"""Sprint 7 software-track validation of the plugin wrapper (VAL-023 / VAL-024 / VAL-025 / VAL-026; Track A, Linux build).

Instruments: the JUCE VST3 host harness (plugin/tools/host_harness_main.cpp), the native offline tool in adapter mode,
the Python reference (oracle), pluginval 1.0.4, the editor snapshot tool under a virtual display. Everything here is
IMPLEMENTATION / AUTOMATED VALIDATION on Linux; Windows native, DAW and owner UI/listening acceptance are separate.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import numpy as np

from .. import environment as env
from ..hashing import sha256_array, write_manifest
from ..native import driver
from ..schemas import VALIDATION_RECORD, validate
from . import fixtures as F
from .production_track_a import compare, ref_render, _jsonable

ROOT = Path(__file__).resolve().parents[2]
PB = ROOT / "plugin" / "build"
VST3 = PB / "SMLSP3000_artefacts" / "Release" / "VST3" / "SML SP-3000.vst3"
HARNESS = PB / "smlsp3000_host_harness_artefacts" / "Release" / "smlsp3000_host_harness"
SNAPSHOT = PB / "smlsp3000_editor_snapshot_artefacts" / "Release" / "smlsp3000_editor_snapshot"
STANDALONE = PB / "SMLSP3000_artefacts" / "Release" / "Standalone" / "SML SP-3000"
PLUGINVAL = ROOT / "tools_external" / "pluginval" / "pluginval"
SCRATCH = Path(os.environ.get("SMLSP3000_SCRATCH", "/tmp/smlsp3000_sprint7"))
RATES = (44100, 48000, 88200, 96000, 176400, 192000)


def _xvfb(cmd: list[str]) -> list[str]:
    return (["xvfb-run", "-a", "-s", "-screen 0 1600x1000x24"] if shutil.which("xvfb-run") else []) + cmd


def harness(args: dict, timeout: int = 1200) -> dict:
    cmd = _xvfb([str(HARNESS), f"plugin={VST3}"] + [f"{k}={v}" for k, v in args.items()])
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    line = [l for l in r.stdout.splitlines() if l.startswith("{")]
    j = json.loads(line[-1]) if line else {"ok": False, "error": (r.stdout + r.stderr)[-800:]}
    j["_exit"] = r.returncode
    return j


def _base(check_id, req, command):
    from ..reference.assets import load_asset
    from ..reference.cascade import load_product_config
    sa, ssha = load_asset(machine="SP-1200"); ma, msha = load_asset(machine="MPC3000"); pc, psha = load_product_config()
    ident = json.loads((ROOT / "plugin" / "product_identity.json").read_text()); pin = json.loads((ROOT / "plugin" / "JUCE_PIN.json").read_text())
    return {"check_id": check_id, "requirement_id": req, "track": "A", "artifact_class": "VALIDATION RESULT", "dataset_role": "VALIDATION",
            "asset_identity": {"asset_id": "plugin(SML SP-3000 VST3 Linux dev build) vs native adapter vs reference", "version": ident["version"], "model_version": f"JUCE {pin['pinned_release']} ({pin['pinned_commit'][:12]}); native core + host adapter", "sha256": sha256_array(np.frombuffer((ssha + msha + psha).encode(), dtype=np.uint8))},
            "research_config_sha256": "n/a (product state only)", "software": {**env.software_record(), "native": driver.build_record(), "plugin_build": "plugin/build (Linux, GCC 13.3, -O2, -ffp-contract=off on the core)"},
            "source_commit": env.git_describe(), "environment": env.environment_record(), "command": command, "stimulus": {}, "method": "", "tolerance_policy": {}, "results": {}, "outcome": "NOT EXECUTED",
            "hardware_fit_outcome": "BLOCKED", "limitations": [], "timestamp_utc": env.utc_now()}


def _write(rec, path: Path):
    problems = validate(rec, VALIDATION_RECORD)
    if problems:
        raise RuntimeError(f"{rec['check_id']} record invalid: {problems}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rec, indent=1, sort_keys=True, default=_jsonable), encoding="utf-8")


def _f64(path: Path, x: np.ndarray):
    np.ascontiguousarray(x, dtype=np.float64).tofile(path)


def _render_plugin(x, rate, precision, extra: dict | None = None, name="r", blocks=None, events=None):
    wd = SCRATCH / name; wd.mkdir(parents=True, exist_ok=True)
    fin, fout = wd / "in.f64", wd / f"out_{precision}.f64"; _f64(fin, x)
    args = {"rate": rate, "block": 512, "precision": precision, "in": str(fin), "out": str(fout)}
    if blocks:
        args["blocks"] = ",".join(str(b) for b in blocks)
    if events:
        fe = wd / "events.txt"; fe.write_text("".join(f"{int(o)} {n} {float(v)!r}\n" for o, n, v in events)); args["events"] = str(fe)
    args.update(extra or {})
    j = harness(args)
    y = np.fromfile(fout, dtype=np.float64).reshape(-1, 2) if j.get("ok") else np.zeros((0, 2))
    return y, j


# Host parameter values travel through JUCE's float32 normalised mapping (NormalisableRange without skew: start + (end-start)*norm in
# float32). The adapter/native oracle must receive exactly the value the plugin ended up with, so the mapping is replicated here.
_PMAP = {"sp_input_level_db": (-60.0, 12.0), "interstage_level_db": (-60.0, 24.0), "output_trim_db": (-60.0, 12.0)}
_NATIVE_NAME = {"sp_input_gain": "sp_input_gain_db"}


def mapped(name: str, v: float) -> float:
    if name in _PMAP:
        lo, hi = _PMAP[name]
        norm = np.float32((v - lo) / (hi - lo))                       # harness: static_cast<float>((v - lo) / (hi - lo))
        return float(np.float32(lo) + np.float32(np.float32(hi) - np.float32(lo)) * norm)   # JUCE convertFrom0to1 in float32
    if name == "sp_input_gain":
        return float(20 if v >= 10 else 0) if v < 30 else 40.0
    return float(v)


def _adapter_cfg_from_params(params: dict | None) -> dict:
    cfg = {}
    for k, v in (params or {}).items():
        name = k[6:] if k.startswith("param.") else k
        mv = mapped(name, float(v))
        if name == "sp_input_level_db": cfg["sp_level"] = repr(mv)
        elif name == "sp_input_gain": cfg["sp_gain"] = int(mv)
        elif name == "interstage_level_db": cfg["interstage"] = repr(mv)
        elif name == "mpc_input_gain": cfg["mpc_gain"] = ["LO", "MID", "HI"][int(mv)]
        elif name == "output_trim_db": cfg["trim"] = repr(mv)
        elif name == "plugin_bypass": cfg["bypass"] = int(mv != 0.0)
    return cfg


def _render_adapter(x, rate, precision, events=None, blocks=None, extra=None, params=None):
    cfg = {"adapter": 1, "precision": precision}; cfg.update(_adapter_cfg_from_params(params)); cfg.update(extra or {})
    ev = None
    if events:
        ev = [(o, _NATIVE_NAME.get(n, n), mapped(n, v)) for o, n, v in events]
    y, j = driver.render(x, rate, config=cfg, blocks=blocks, block=None if blocks else 512, events=ev)
    return y, j


def _cells(x, a, b):
    return compare(x, a, b)


def _bitwise(a, b):
    n = min(a.shape[0], b.shape[0])
    return {"length_equal": bool(a.shape == b.shape), "identical": bool(np.array_equal(a[:n], b[:n])), "max_abs_diff": float(np.max(np.abs(a[:n] - b[:n]))) if n else 0.0}


# ----------------------------------------------------------------------------- VAL-026 host matrix (Linux VST3 via harness)
def val_026(out: Path, command: str, quick=False) -> dict:
    rec = _base("VAL-026", "REQ-026", command)
    rec["method"] = ("The built VST3 (Linux dev build) is loaded by the JUCE host harness and rendered on the frozen fixtures at every supported rate in float64 and float32; "
                     "compared bit-for-bit with the native adapter path (same block schedule) and against the Python reference under the G-08 limits; the float32 oracle is the reference "
                     "run on the same float32 input promoted to double with the same final float32 cast; partition invariance (irregular block lists incl. 1-sample blocks and blocks larger than the "
                     "prepared size), offline mode, automation (block-boundary delivery, delivered schedule recorded), state round trip / fresh-instance restore / restore during processing, "
                     "multiple instances, reprepare, editor open/close under a virtual display. Linux only: not Windows, not a DAW.")
    rec["tolerance_policy"] = {"plugin_vs_adapter": "bit-identical (same code path through the wrapper)", "plugin_vs_reference": "G-08 limits (OWN-DEC-016 C) on the same precision oracle", "automation": "plugin == adapter with the delivered (block-boundary) schedule, bit-identical; requested vs delivered offsets recorded"}
    rates = (48000, 96000) if quick else RATES
    res = {"per_rate": {}, "failures": []}
    for fs in rates:
        x = F.render_fixture("multitone_mix_m12", fs, 0.5)
        cell = {}
        y64, j64 = _render_plugin(x, fs, 64, name=f"m_{fs}")
        if not j64.get("ok"):
            res["failures"].append({"rate": fs, "harness": j64}); continue
        a64, ja = _render_adapter(x, fs, 64)
        cell["latency_plugin"] = j64["latency"]; cell["latency_native"] = ja["latency"]; cell["double_supported"] = j64["double_supported"]
        cell["plugin64_vs_adapter64"] = _bitwise(y64, a64)
        yref, e = ref_render(x, fs, {})
        cell["plugin64_vs_reference"] = _cells(x, yref, y64)
        y32, j32 = _render_plugin(x, fs, 32, name=f"m32_{fs}")
        a32, _ = _render_adapter(x, fs, 32)
        cell["plugin32_vs_adapter32"] = _bitwise(y32, a32)
        x32 = x.astype(np.float32).astype(np.float64)
        yref32, _ = ref_render(x32, fs, {})
        oracle32 = yref32.astype(np.float32).astype(np.float64)
        cell["plugin32_vs_reference_same_float32_input_and_cast"] = _cells(x32, oracle32, y32)
        cell["float32_interface_rounding_rms"] = float(np.sqrt(np.mean((yref32 - oracle32) ** 2)))
        # The VST3 host must announce its largest callback before processing (JUCE allocates bus buffers then).
        # Direct SMLProcessor calls larger than prepareToPlay(512) remain covered by processor_oversized_test.
        yi, _ = _render_plugin(x, fs, 64, name=f"mi_{fs}", extra={"block": 9000}, blocks=[1, 7, 500, 2048, 64, 3, 1000, 4096, 2, 1, 513, 8192, 9000])
        cell["plugin64_irregular_vs_block512"] = _bitwise(yi, y64)
        yo, _ = _render_plugin(x, fs, 64, name=f"mo_{fs}", extra={"offline": 1})
        cell["offline_vs_realtime"] = _bitwise(yo, y64)
        ok = (cell["plugin64_vs_adapter64"]["identical"] and cell["plugin32_vs_adapter32"]["identical"] and cell["plugin64_irregular_vs_block512"]["identical"] and cell["offline_vs_realtime"]["identical"]
              and all(c["pass"] for c in cell["plugin64_vs_reference"]) and all(c["pass"] for c in cell["plugin32_vs_reference_same_float32_input_and_cast"]) and cell["latency_plugin"] == cell["latency_native"])
        cell["pass"] = ok
        if not ok:
            res["failures"].append({"rate": fs, "cell": {k: v for k, v in cell.items() if k != "plugin64_vs_reference"}})
        res["per_rate"][fs] = cell
    # automation (48 kHz): requested frames vs delivered block boundaries
    fs = 48000; x = F.render_fixture("multitone_mix_m12", fs, 0.5)
    req = [(3000, "sp_input_level_db", -6.0), (9100, "interstage_level_db", 3.0), (12000, "sp_input_gain", 20.0), (15050, "mpc_input_gain", 1.0), (18000, "output_trim_db", -3.0), (20500, "plugin_bypass", 1.0), (22000, "plugin_bypass", 0.0)]
    delivered = [((f + 511) // 512 * 512, n, v) for f, n, v in req]
    ya, ja = _render_plugin(x, fs, 64, name="auto", events=req)
    aa, _ = _render_adapter(x, fs, 64, events=delivered)
    y0, _ = _render_plugin(x, fs, 64, name="auto0")
    res["automation"] = {"requested": req, "delivered_block_boundary": delivered, "delivery": "BLOCK-BOUNDARY (JUCE AudioProcessor parameter path: host changes are applied before processBlock; the VST3 wrapper does not pass sample offsets to the processor)",
                         "plugin_vs_adapter_same_delivered_schedule": _bitwise(ya, aa), "differs_from_static": bool(not np.array_equal(ya, y0))}
    if not (res["automation"]["plugin_vs_adapter_same_delivered_schedule"]["identical"] and res["automation"]["differs_from_static"]):
        res["failures"].append({"automation": res["automation"]})
    # state: round trip, fresh-instance restore, restore during processing, invalid states
    st = SCRATCH / "state"; st.mkdir(parents=True, exist_ok=True)
    ys, js = _render_plugin(x, fs, 64, name="st1", extra={"param.sp_input_level_db": -12.5, "param.sp_input_gain": 20, "param.interstage_level_db": 6.25, "param.mpc_input_gain": 2, "param.output_trim_db": -1.5, "state_out": str(st / "s1.bin")})
    yr, jr = _render_plugin(x, fs, 64, name="st2", extra={"state_in": str(st / "s1.bin"), "state_out": str(st / "s2.bin")})
    as1, _ = _render_adapter(x, fs, 64, params={"sp_input_level_db": -12.5, "sp_input_gain": 20, "interstage_level_db": 6.25, "mpc_input_gain": 2, "output_trim_db": -1.5})
    sm = {"plugin_with_params_vs_adapter_mapped_values": _bitwise(ys, as1), "params_after_set": js.get("params"), "params_after_restore": jr.get("params"), "params_equal": js.get("params") == jr.get("params"), "fresh_instance_render_identical": _bitwise(ys, yr),
          "state_bytes": js.get("state_out_bytes"), "state_hash_round_trip_equal": hashlib.sha256((st / "s1.bin").read_bytes()).hexdigest() == hashlib.sha256((st / "s2.bin").read_bytes()).hexdigest()}
    for mut in ("garbage", "truncate", "oversize", "future_schema", "identity", "research_key", "out_of_range"):
        jm = harness({"rate": fs, "block": 512, "state_in": str(st / "s1.bin"), "state_mutate": mut})
        sm[f"mutated_{mut}"] = {"ok": jm.get("ok"), "params_unchanged_from_restored": jm.get("params") == js.get("params"), "mutation": jm.get("state_mutation")}
        if not sm[f"mutated_{mut}"]["params_unchanged_from_restored"]:
            res["failures"].append({"state_mutation": mut, "got": jm})
    # restore during processing at frame 8192: equals adapter with the equivalent parameter events at that block
    yd, jd = _render_plugin(x, fs, 64, name="st3", extra={"state_at": 8192, "state_file": str(st / "s1.bin")})
    ad, _ = _render_adapter(x, fs, 64, events=[(8192, "sp_input_level_db", -12.5), (8192, "sp_input_gain", 20), (8192, "interstage_level_db", 6.25), (8192, "mpc_input_gain", 2), (8192, "output_trim_db", -1.5)])
    sm["restore_during_processing_vs_adapter_events"] = _bitwise(yd, ad); sm["restore_during_processing_applied_at"] = jd.get("state_applied_at_frame")
    sm["pass"] = bool(sm["plugin_with_params_vs_adapter_mapped_values"]["identical"] and sm["params_equal"] and sm["fresh_instance_render_identical"]["identical"] and sm["state_hash_round_trip_equal"] and sm["restore_during_processing_vs_adapter_events"]["identical"])
    if not sm["pass"]:
        res["failures"].append({"state": {k: v for k, v in sm.items() if not k.startswith("params_after")}})
    res["state"] = sm
    jm = harness({"rate": fs, "block": 512, "instances": 4, "reprepare": 1, "editor": 5})
    res["instances_reprepare_editor"] = {k: jm.get(k) for k in ("instances", "instances_identical", "reprepare_latency", "editor_open_close", "latency")}
    if not (jm.get("instances_identical") and jm.get("reprepare_latency") == jm.get("latency") and jm.get("editor_open_close") == 5):
        res["failures"].append({"instances_reprepare_editor": res["instances_reprepare_editor"]})
    rec["stimulus"] = {"fixture": "multitone_mix_m12 0.5 s stereo at each rate", "rates": list(rates)}
    rec["results"] = res; rec["outcome"] = "PASS" if not res["failures"] else "FAIL"
    rec["limitations"] = ["Linux VST3 development build hosted by a JUCE harness: this is plugin/offline equivalence on Linux, NOT Windows native validation and NOT a DAW session test (FL Studio rows NOT RUN).",
                          "Automation is delivered at block boundaries (wrapper limitation); the native sample-timestamped event contract is unchanged."]
    _write(rec, out / "host_matrix" / "VAL-026_software.json")
    return {"VAL-026": rec["outcome"]}


# ----------------------------------------------------------------------------- VAL-023 latency / bypass
def val_023(out: Path, command: str, quick=False) -> dict:
    rec = _base("VAL-023", "REQ-023", command)
    rec["method"] = ("Reported plugin latency vs native at every rate; impulse alignment through the bypass path (parameter bypass and host processBlockBypassed route through the same "
                     "mechanism); full dry endpoint (latency-aligned input, no trim/gain), full processed endpoint (equals the un-bypassed render), 10 ms linear crossfade with complementary "
                     "weights, rapid toggles continuing from the current weight, startup in bypass, reset in bypass (reprepare), automation of the bypass parameter; float32 and float64 paths; "
                     "plugin vs adapter bit-identical for the same delivered schedule. Machine bypass (chain modes) stays a research configuration of the native core (VAL-015).")
    rec["tolerance_policy"] = {"latency": "plugin == native == reference integer latency; <= 10 ms", "impulse": "exact index", "endpoints": "bit-exact", "crossfade": "|y - (w*processed + (1-w)*dry)| <= 1e-12 with linear w over 10 ms", "plugin_vs_adapter": "bit-identical"}
    rates = (48000, 96000) if quick else RATES
    res = {"latency": {}, "bypass": {}, "failures": []}
    for fs in rates:
        imp = np.zeros((int(0.05 * fs), 2)); imp[200, 0] = 1.0; imp[300, 1] = -0.5
        yb, jb = _render_plugin(imp, fs, 64, name=f"imp_{fs}", extra={"param.plugin_bypass": 1, "param.output_trim_db": -6.0, "param.sp_input_level_db": 6.0})
        yh, jh = _render_plugin(imp, fs, 64, name=f"imph_{fs}", extra={"host_bypass": 1, "param.output_trim_db": -6.0})
        # JUCE's hosted processBlockBypassed sets the plugin's bypass PARAMETER at the first bypassed block (VST3PluginInstance::updateBypass):
        # the equivalent parameter render has the bypass event at frame 0 (crossfade from the processed state), not bypass-at-prepare
        yp0, _ = _render_plugin(imp, fs, 64, name=f"imp0_{fs}", extra={"param.output_trim_db": -6.0}, events=[(0, "plugin_bypass", 1.0)])
        lat = jb.get("latency"); nat = driver.info(fs)["info"]["latency_host_samples"]
        pk0 = int(np.argmax(np.abs(yb[:, 0]))) if yb.size else -1; pk1 = int(np.argmax(np.abs(yb[:, 1]))) if yb.size else -1
        c = {"plugin_latency": lat, "native_latency": nat, "ms": lat / fs * 1000.0 if lat else None, "impulse_index_ch0": pk0 - 200, "impulse_index_ch1": pk1 - 300,
             "dry_exact_amplitude": bool(yb.size and yb[pk0, 0] == 1.0 and yb[pk1, 1] == -0.5), "host_bypass_same_output_as_parameter_bypass_event_at_frame0": _bitwise(yp0, yh)["identical"] if (yh.size and yp0.size) else False,
             "host_bypass_mechanism": "hosted processBlockBypassed → plugin bypass parameter (one mechanism); differs from bypass-at-prepare only by the initial 10 ms crossfade",
             "pass": bool(lat == nat and pk0 - 200 == lat and pk1 - 300 == lat and yb.size and yb[pk0, 0] == 1.0 and lat / fs <= 0.010 and yh.size and yp0.size and _bitwise(yp0, yh)["identical"])}
        if not c["pass"]:
            res["failures"].append({"rate": fs, "latency": c})
        res["latency"][fs] = c
    fs = 48000; x = F.render_fixture("multitone_mix_m12", fs, 0.5); L = driver.info(fs)["info"]["latency_host_samples"]
    for prec in (64, 32):
        yon, _ = _render_plugin(x, fs, prec, name=f"byp_on_{prec}", extra={"param.plugin_bypass": 1}); yoff, _ = _render_plugin(x, fs, prec, name=f"byp_off_{prec}")
        xin = x if prec == 64 else x.astype(np.float32).astype(np.float64)
        dry = np.zeros_like(yon); dry[L:L + xin.shape[0]] = xin
        if prec == 32:
            dry = dry.astype(np.float32).astype(np.float64)
        ev = [(6144, "plugin_bypass", 0.0), (12288, "plugin_bypass", 1.0), (12800, "plugin_bypass", 0.0), (13312, "plugin_bypass", 1.0), (20480, "plugin_bypass", 0.0)]
        yt, _ = _render_plugin(x, fs, prec, name=f"byp_t_{prec}", extra={"param.plugin_bypass": 1}, events=ev)
        at, _ = _render_adapter(x, fs, prec, events=ev, extra={"bypass": 1})
        ramp = int(0.010 * fs)
        fade_ok = True
        for m in range(6144, 6144 + ramp):
            w = (m - 6144 + 1) / ramp
            exp = w * yoff[m] + (1 - w) * dry[m]
            fade_ok &= bool(np.all(np.abs(yt[m] - exp) <= (1e-12 if prec == 64 else 2e-7)))
        post = slice(6144 + ramp + 1, 12288); pre = slice(L, 6144)
        res["bypass"][prec] = {"startup_in_bypass_fully_dry": _bitwise(yon, dry), "full_processed_after_fade": _bitwise(yt[post], yoff[post]), "dry_before_unbypass": _bitwise(yt[pre], dry[pre]),
                               "crossfade_linear_10ms": fade_ok, "plugin_toggles_vs_adapter_toggles": _bitwise(yt, at), "events": ev, "toggle_bounded": bool(np.all(yt[12288:14500] <= np.maximum(yoff[12288:14500], dry[12288:14500]) + 1e-9) and np.all(yt[12288:14500] >= np.minimum(yoff[12288:14500], dry[12288:14500]) - 1e-9))}
        b = res["bypass"][prec]; b["pass"] = bool(b["startup_in_bypass_fully_dry"]["identical"] and b["full_processed_after_fade"]["identical"] and b["dry_before_unbypass"]["identical"] and fade_ok and b["plugin_toggles_vs_adapter_toggles"]["identical"] and b["toggle_bounded"])
        if not b["pass"]:
            res["failures"].append({"bypass_precision": prec, "cell": {k: v for k, v in b.items() if k != "events"}})
    rec["stimulus"] = {"impulse": "unit impulse ch0 @200, -0.5 ch1 @300, 50 ms", "toggles_fixture": "multitone_mix_m12 0.5 s @48 kHz", "rates": list(rates)}
    rec["results"] = res; rec["outcome"] = "PASS" if not res["failures"] else "FAIL"
    rec["limitations"] = ["Host suspension: the plugin cannot process callbacks the host does not deliver; state continues from the last delivered block (documented, not testable here).",
                          "Linux harness only; host compensation of the reported latency is the DAW's responsibility (FL Studio NOT RUN)."]
    _write(rec, out / "latency_bypass" / "VAL-023_software.json")
    return {"VAL-023": rec["outcome"]}


# ----------------------------------------------------------------------------- VAL-024 real-time / state / numerical safety
def val_024(out: Path, command: str, quick=False) -> dict:
    rec = _base("VAL-024", "REQ-024", command)
    rec["method"] = ("Adapter allocation instrumentation (global operator new/delete counted inside process(); ctest host_adapter_test), ASan+UBSan build of the native core running the core "
                     "self-test and the adapter test (stream start, pre-padding, ring/history boundaries), NaN/Inf/over-range/silence through the plugin (finite output, equals the adapter path), "
                     "rapid automation, state handoff during processing, multiple instances, and callback timing of the complete plugin (wrapper + conversion + bypass + metering) through the "
                     "harness at the owner's rate/block pairs in float32 and float64 (all trials retained, including outliers).")
    rec["tolerance_policy"] = {"allocations": "0 inside process()", "sanitizers": "no report", "numerics": "finite output; plugin == adapter bit-identical", "cpu": "OWN-DEC-017 mean-load limits (20/40/60 %); p99.9 < 80 % target reported", "trials": "all retained"}
    res = {"failures": []}
    # 1. ctest (adapter allocation test + core self-test) on the plugin build tree's native core
    r = subprocess.run(["ctest", "--output-on-failure"], cwd=PB / "native", capture_output=True, text=True)
    res["ctest"] = {"exit": r.returncode, "tail": r.stdout[-600:]}
    if r.returncode != 0:
        res["failures"].append({"ctest": r.stdout[-2000:]})
    # 2. sanitizer build of the native core
    san = ROOT / "native" / "build-asan"
    r1 = subprocess.run(["cmake", "-S", str(ROOT / "native"), "-B", str(san), "-G", "Ninja", "-DCMAKE_BUILD_TYPE=Debug", "-DCMAKE_CXX_FLAGS=-fsanitize=address,undefined -fno-omit-frame-pointer -O1"], capture_output=True, text=True)
    r2 = subprocess.run(["cmake", "--build", str(san)], capture_output=True, text=True) if r1.returncode == 0 else r1
    r3 = subprocess.run(["ctest", "--output-on-failure"], cwd=san, capture_output=True, text=True, env={**os.environ, "ASAN_OPTIONS": "detect_leaks=0", "UBSAN_OPTIONS": "print_stacktrace=1"}) if r2.returncode == 0 else r2
    res["sanitizers"] = {"configure_exit": r1.returncode, "build_exit": r2.returncode, "ctest_exit": r3.returncode, "report_lines": [l for l in (r3.stdout + r3.stderr).splitlines() if "runtime error" in l or "AddressSanitizer" in l][:20], "tail": r3.stdout[-400:]}
    if r3.returncode != 0 or res["sanitizers"]["report_lines"]:
        res["failures"].append({"sanitizers": res["sanitizers"]})
    # 3. numerics through the plugin
    fs = 48000; x = F.render_fixture("multitone_mix_m12", fs, 0.5); bad = x.copy(); bad[100, 0] = np.nan; bad[200, 1] = np.inf; bad[:, 1] *= 16.0
    yb, jb = _render_plugin(bad, fs, 64, name="bad"); ab, ja = _render_adapter(bad, fs, 64)
    sil = np.zeros((24000, 2)); ysil, _ = _render_plugin(sil, fs, 64, name="sil"); tiny = sil + 1e-300; ytiny, _ = _render_plugin(tiny, fs, 64, name="tiny")
    res["numerics"] = {"nan_inf_overrange_plugin_finite": bool(np.all(np.isfinite(yb))), "plugin_vs_adapter_identical": _bitwise(yb, ab)["identical"], "adapter_meters": ja.get("meters"), "silence_output_all_zero": bool(np.all(ysil == 0.0)), "denormal_input_finite": bool(np.all(np.isfinite(ytiny)))}
    if not (res["numerics"]["nan_inf_overrange_plugin_finite"] and res["numerics"]["plugin_vs_adapter_identical"] and res["numerics"]["silence_output_all_zero"] and res["numerics"]["denormal_input_finite"]):
        res["failures"].append({"numerics": res["numerics"]})
    # 4. rapid automation + state handoff during processing (every block changes a parameter)
    ev = [(f, ["sp_input_level_db", "interstage_level_db", "output_trim_db"][i % 3], float(-6 + (i % 5))) for i, f in enumerate(range(0, 24000, 512))]
    yr, jr = _render_plugin(x, fs, 64, name="rapid", events=ev); ar, _ = _render_adapter(x, fs, 64, events=ev)
    res["rapid_automation"] = {"events": len(ev), "plugin_vs_adapter_identical": _bitwise(yr, ar)["identical"], "finite": bool(np.all(np.isfinite(yr)))}
    if not (res["rapid_automation"]["plugin_vs_adapter_identical"] and res["rapid_automation"]["finite"]):
        res["failures"].append({"rapid_automation": res["rapid_automation"]})
    # 5. callback timing of the complete plugin
    pairs = ((44100, 64), (48000, 64), (88200, 128), (96000, 128), (176400, 256), (192000, 256)); limits = {44100: 0.2, 48000: 0.2, 88200: 0.4, 96000: 0.4, 176400: 0.6, 192000: 0.6}
    bench = {}
    bdir = out / "realtime_state" / "bench_raw"; bdir.mkdir(parents=True, exist_ok=True)
    for rate, block in pairs:
        t = np.arange(int((2.0 if quick else 5.0) * rate)) / rate; sigx = np.stack([0.0837 * (np.sin(2 * np.pi * 97 * t) + np.sin(2 * np.pi * 1003 * t) + np.sin(2 * np.pi * 7919 * t)), -0.5 * 0.0837 * (np.sin(2 * np.pi * 97 * t) + np.sin(2 * np.pi * 1003 * t) + np.sin(2 * np.pi * 7919 * t))], axis=1)
        trials = []
        for prec in (32, 64):
            for trial in range(1 if quick else 3):
                wd = SCRATCH / f"bench_{rate}_{prec}_{trial}"; wd.mkdir(parents=True, exist_ok=True); fin = wd / "in.f64"; _f64(fin, sigx)
                evb = [(f, "plugin_bypass", float((f // (block * 40)) % 2)) for f in range(0, sigx.shape[0], block * 40)]   # periodic bypass toggles: the bypass path is part of the measurement
                fe = wd / "ev.txt"; fe.write_text("".join(f"{f} {n} {v!r}\n" for f, n, v in evb))
                j = harness({"rate": rate, "block": block, "precision": prec, "in": str(fin), "out": str(wd / "out.f64"), "bench": 1, "bench_raw": str(bdir / f"raw_{rate}_{block}_f{prec}_t{trial}.f64"), "events": str(fe), "drain": 0})
                b = j.get("bench", {}); b.update({"precision": prec, "trial": trial, "p999_over_budget": (b.get("p999_s", 0) / b["budget_s"]) if b.get("budget_s") else None}); trials.append(b)
        means = [b.get("mean_load", 9) for b in trials]
        bench[f"{rate}_{block}"] = {"limit": limits[rate], "trials": trials, "max_mean_load": max(means), "mean_limit_pass": all(m <= limits[rate] for m in means), "p999_target_met": all((b.get("p999_over_budget") or 9) < 0.8 for b in trials), "overruns_total": sum(b.get("overruns", 0) for b in trials)}
        if not bench[f"{rate}_{block}"]["mean_limit_pass"]:
            res["failures"].append({"bench": f"{rate}_{block}", "means": means})
    res["bench"] = bench
    res["bench_conditions"] = "complete VST3 through the JUCE harness (wrapper, float conversion where precision=32, bypass toggles every 40 blocks, metering); shared cloud VM, no RT priority; all trials retained"
    rec["stimulus"] = {"numerics": "multitone with NaN/Inf samples and x16 over-range channel; silence; 1e-300 input", "bench": "3-tone + stereo inverse at the six rate/block pairs"}
    rec["results"] = res; rec["outcome"] = "PASS" if not res["failures"] else "FAIL"
    rec["limitations"] = ["Lock/I-O freedom in the audio path is established by construction and code review of the adapter/processor (no locks, no I/O, no logging) plus the allocation counter; no OS-level syscall tracer was run.",
                          "Timing applies only to this Linux container; Windows timing pending."]
    _write(rec, out / "realtime_state" / "VAL-024_software.json")
    return {"VAL-024": rec["outcome"]}


# ----------------------------------------------------------------------------- VAL-025 safety / UI
def val_025(out: Path, command: str, quick=False) -> dict:
    rec = _base("VAL-025", "REQ-025", command)
    rec["method"] = ("Editor rendered under a virtual display (screenshots at default/min/max/bypassed sizes and before audio preparation); clip/over-range meter semantics on clip and inter-sample-peak "
                     "stimuli through the adapter path (modelled converter clamps counted; finite over-range output indicated and never clamped); exposed parameter list limited to the six product controls; "
                     "state contains no research/calibration fields; standalone binary smoke test (headless, no audio device). Owner UI/listening acceptance NOT EXECUTED (G-10).")
    rec["tolerance_policy"] = {"indicators": "exact semantics (counts from the core; over-range = |out| > 1.0 finite)", "ui": "structural checks only; owner review pending"}
    res = {"failures": []}
    shots = out / "safety_ui" / "screenshots"; shots.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(_xvfb([str(SNAPSHOT), str(shots)]), capture_output=True, text=True, timeout=600)
    files = sorted(p.name for p in shots.glob("*.png"))
    res["screenshots"] = {"exit": r.returncode, "files": files, "stdout": r.stdout[-600:]}
    if r.returncode != 0 or len(files) < 5:
        res["failures"].append({"screenshots": res["screenshots"]})
    fs = 48000; x = F.render_fixture("overrange_steps_pm16", fs, 0.5)
    y, j = _render_adapter(x, fs, 64); m = j.get("meters", {})
    isp = np.stack([0.98 * np.sin(2 * np.pi * 11025.0 * np.arange(24000) / fs + 0.7)] * 2, axis=1)   # inter-sample peaks above 1.0 between samples
    yi, ji = _render_adapter(isp, fs, 64, extra={"trim": 3.0}); mi = ji.get("meters", {})
    # adapter JSON meters are last-block values (the editor shows per-block peaks + hold); the clamp/over-range semantics are checked on the render itself
    res["indicators"] = {"overrange_fixture": {"sp_clip_total": m.get("sp_clip"), "mpc_clip18_total": m.get("mpc_clip18"), "render_max_abs": float(np.max(np.abs(y))), "output_not_clamped_by_plugin": bool(np.max(np.abs(y)) > 1.0),
                                               "note": "converter clamps bound the machine CODES (counted); reconstruction/trim can exceed ±1.0 and the plugin leaves it (no limiter)"},
                         "isp_trim_plus3": {"last_block_output_peak": mi.get("output_peak"), "last_block_over_range_flag": mi.get("over_range"), "render_max_abs": float(np.max(np.abs(yi))), "note": "sample-peak meter only; inter-sample peaks between samples are not measured (no true-peak claim)"}}
    ind_ok = res["indicators"]["overrange_fixture"]["output_not_clamped_by_plugin"] and all(mi.get("over_range", [False])) and float(np.max(np.abs(yi))) > 1.0 and (m.get("sp_clip", [0])[0] > 0) and (m.get("mpc_clip18", [0])[0] > 0)
    if not ind_ok:
        res["failures"].append({"indicators": res["indicators"]})
    jp = harness({"rate": fs, "block": 512})
    res["exposed_parameters"] = sorted(jp.get("params", {}).keys())
    if res["exposed_parameters"] != sorted(["sp_input_level_db", "sp_input_gain", "interstage_level_db", "mpc_input_gain", "output_trim_db", "plugin_bypass"]):
        res["failures"].append({"exposed_parameters": res["exposed_parameters"]})
    res["state_fields"] = [l.split("=")[0] for l in j.get("state", "").strip().splitlines()[1:]]
    if any(k in res["state_fields"] for k in ("quantizer_rule", "reduction_rule", "volts_per_normalized_unit", "reverse_order_research", "chain_mode")):
        res["failures"].append({"state_fields": res["state_fields"]})
    # standalone smoke: launch under Xvfb for a bounded time; a clean run (still alive after 8 s, no crash) is the smoke result, then it is terminated
    smoke = {"binary_exists": STANDALONE.exists(), "size_bytes": STANDALONE.stat().st_size if STANDALONE.exists() else 0, "note": "Linux standalone built without an audio backend (no ALSA headers in the container); launched headless under Xvfb for 8 s; monitoring requires explicit activation (JUCE standalone mutes input by default)"}
    if STANDALONE.exists():
        pr = subprocess.Popen(_xvfb([str(STANDALONE)]), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            pr.wait(timeout=8); smoke["exited_early"] = True; smoke["exit"] = pr.returncode; smoke["stderr"] = (pr.stderr.read() or "")[-400:]
        except subprocess.TimeoutExpired:
            smoke["exited_early"] = False; pr.terminate()
            try: pr.wait(timeout=10)
            except subprocess.TimeoutExpired: pr.kill()
            smoke["exit"] = "terminated after 8 s (alive, no crash)"
        smoke["pass"] = (not smoke["exited_early"]) or smoke.get("exit") == 0
        if not smoke["pass"]:
            res["failures"].append({"standalone_smoke": smoke})
    res["standalone_smoke"] = smoke
    res["review_checklist"] = str(out / "safety_ui" / "owner_review_checklist.md")
    (out / "safety_ui" / "owner_review_checklist.md").write_text(OWNER_CHECKLIST, encoding="utf-8")
    rec["stimulus"] = {"overrange": "overrange_steps_pm16", "isp": "11.025 kHz sine 0.98 with +3 dB trim"}
    rec["results"] = res; rec["outcome"] = "PASS" if not res["failures"] else "FAIL"
    rec["limitations"] = ["Owner G-10 visual/musical acceptance NOT EXECUTED; screenshots are from the Linux build under Xvfb (software rendering), Windows look not captured.", "No LUFS/RMS/true-peak metering exists; sample-peak only."]
    _write(rec, out / "safety_ui" / "VAL-025_software.json")
    return {"VAL-025": rec["outcome"]}


OWNER_CHECKLIST = """# SML SP-3000 — owner UI / G-10 review checklist (prototype, Sprint 7)

Status: NOT EXECUTED by the owner. Screenshots: evidence/sprint_07/safety_ui/screenshots/ (Linux build under Xvfb). Nothing here scores preference.

1. Signal path reads correctly: SP INPUT → SP ENGINE → INTERSTAGE → MPC ENGINE → OUTPUT.
2. Six controls present with exact units (dB, discrete 0/+20/+40, LO/MID/HI, bypass); defaults 0 / 0 / 0 / LO / 0 / off; Reset to INIT restores them.
3. Meter labels say what they measure (sample peak per block, hold line) and never claim RMS/LUFS/true peak; "unavailable" shown before audio preparation.
4. Converter clamp counters read "modelled code clamp"; analog clipping/recovery shown as not modelled.
5. Over-range (amber) output indicator appears for finite output above ±1.0 without changing the audio.
6. Bypass button: latency-aligned dry, 10 ms crossfade; host bypass behaves the same.
7. Status strip: reported latency and rate; non-finite/fault messages; model and claim-boundary wording acceptable.
8. Readability at default size (920×540) and at the minimum (760×440); resizing keeps the layout usable; keyboard focus moves through controls; tooltips describe implemented behaviour only.
9. No fake animation, no copied hardware panels/logos.
10. Musical/listening judgement: NOT part of this checklist (CHAIN-EXP-018 remains NOT EXECUTED).
"""


def pluginval(out: Path) -> dict:
    d = out / "pluginval"; d.mkdir(parents=True, exist_ok=True)
    cmd = _xvfb([str(PLUGINVAL), "--strictness-level", "8", "--validate-in-process", "--verbose", "--output-dir", str(d), str(VST3)])
    t0 = time.time(); r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600); dt = time.time() - t0
    (d / "pluginval_stdout.log").write_text(r.stdout + "\n--- stderr ---\n" + r.stderr, encoding="utf-8")
    ver = subprocess.run([str(PLUGINVAL), "--version"], capture_output=True, text=True).stdout.strip()
    rec = {"tool": "pluginval", "version": ver, "command": " ".join(cmd), "exit_code": r.returncode, "seconds": round(dt, 1), "strictness": 8, "platform": env.environment_record(), "binary_sha256": hashlib.sha256(PLUGINVAL.read_bytes()).hexdigest(),
           "zip_sha256": hashlib.sha256((PLUGINVAL.parent / "pluginval_Linux.zip").read_bytes()).hexdigest() if (PLUGINVAL.parent / "pluginval_Linux.zip").exists() else None, "log": str(d / "pluginval_stdout.log"), "result": "PASS" if r.returncode == 0 else "FAIL"}
    (d / "pluginval_record.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
    return rec


def run_all(evidence_root, command: str, quick=False, only=None) -> dict:
    out = Path(evidence_root)
    for p in (VST3, HARNESS, SNAPSHOT):
        if not p.exists():
            raise RuntimeError(f"missing build artefact {p}; build with CMD-18")
    SCRATCH.mkdir(parents=True, exist_ok=True)
    results = {}
    if only in (None, "VAL-026"): results.update(val_026(out, command, quick))
    if only in (None, "VAL-023"): results.update(val_023(out, command, quick))
    if only in (None, "VAL-024"): results.update(val_024(out, command, quick))
    if only in (None, "VAL-025"): results.update(val_025(out, command, quick))
    if only in (None, "pluginval"):
        pv = pluginval(out); results["pluginval"] = pv["result"]
    for d in ("host_matrix", "latency_bypass", "realtime_state", "safety_ui"):
        dd = out / d
        if dd.exists():
            write_manifest(dd, [str(p.relative_to(dd)) for p in dd.rglob("*") if p.is_file() and p.name != "manifest.sha256"])
    return results
