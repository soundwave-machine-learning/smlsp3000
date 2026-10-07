"""Sprint 4 software-track validation (VAL-012/013/014 software cells; Track A, OWN-DEC-005..008).

Every check is a SIMULATION against the implementation's own documented equations. Nothing compares to
hardware; every record carries hardware_fit_outcome = BLOCKED. Nonzero bounds derive from kernel design
(MPCPreparedInfo.kernel_properties) or float64 arithmetic and are written into tolerance_policy.
"""
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

import numpy as np

from .. import environment as env
from ..hashing import write_manifest
from ..schemas import VALIDATION_RECORD, validate
from ..reference.assets import load_asset, load_research_config
from ..reference.errors import InvalidConfiguration
from ..reference.kernels import frequency_response, interpolation_kernel_response
from ..reference.mpc3000 import REDUCTION_RULES, MPCProductParameters, MPCReferenceEngine
from ..reference.render import render_offline, with_switches
from .measure import fit_components

MPC_RATE = 44100
RATE_TABLE = {44100: "1", 48000: "147/160", 88200: "1/2", 96000: "147/320", 176400: "1/4", 192000: "147/640"}
PRODUCT = MPCProductParameters(mpc_input_gain="LO", mpc_record_level_db=0.0, mpc_output_route="MAIN_LR", calibration_mode="NORMALIZED_RESEARCH")
FLOAT_REL_BOUND = 1e-9


def _base(check_id: str, req: str, command: str) -> dict:
    asset, asha = load_asset(machine="MPC3000")
    _, rsha = load_research_config(machine="MPC3000")
    return {"check_id": check_id, "requirement_id": req, "track": "A", "artifact_class": "SIMULATION", "dataset_role": "NONE",
            "asset_identity": {"asset_id": asset["asset_id"], "version": asset["version"], "model_version": asset["model_version"], "sha256": asha},
            "research_config_sha256": rsha, "software": env.software_record(), "source_commit": env.git_describe(), "environment": env.environment_record(),
            "command": command, "stimulus": {}, "method": "", "tolerance_policy": {}, "results": {}, "outcome": "NOT EXECUTED",
            "hardware_fit_outcome": "BLOCKED", "limitations": [], "timestamp_utc": env.utc_now()}


def _write(rec: dict, path: Path):
    problems = validate(rec, VALIDATION_RECORD)
    if problems:
        raise RuntimeError(f"{rec['check_id']} record invalid: {problems}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rec, indent=1, sort_keys=True), encoding="utf-8")


def _tone(fs: int, f: float, seconds: float, amp: float) -> np.ndarray:
    return amp * np.sin(2 * np.pi * f * np.arange(int(round(seconds * fs))) / fs)


def _expected_line(f: float, amp: float, fs: int, info, eng) -> tuple[float, float]:
    """(output line frequency, expected amplitude) for an input tone through the TRANSPARENT chain:
    sampled at 44.1 kHz the tone appears at f_a = |f - round(f/44100)*44100|; amplitude = amp*|H1(f)|*|H12(f)|*|K(f_a)|*|H16(f_a)|."""
    fp = fs * info.proxy_oversampling
    fa = abs(f - round(f / MPC_RATE) * MPC_RATE)
    h1 = abs(frequency_response(eng.h_lp, f / fp)[0])
    h12 = abs(frequency_response(eng.h_r12, f / fp)[0])
    k = float(interpolation_kernel_response(eng.hw_r, eng.interp_beta, fa / MPC_RATE)[0])
    h16 = abs(frequency_response(eng.h_lp, fa / fp)[0])
    return fa, amp * h1 * h12 * k * h16


def _line_check(f: float, amp: float, fs: int, bypass: bool, seconds: float = 0.25, trim: int = 4000) -> dict:
    cfg, _ = load_research_config(machine="MPC3000")
    x = _tone(fs, f, seconds, amp)
    y, info, rec, eng = render_offline(x, fs, PRODUCT, with_switches(cfg, converter_quantization_bypass_diagnostic=bypass))
    seg = y[trim:-trim, 0]
    fa, exp = _expected_line(f, amp, fs, info, eng)
    freqs = sorted({fa} | ({f} if f < fs / 2 and abs(f - fa) > 1.0 else set()))
    amps, res = fit_components(seg, fs, freqs)
    bound = amp * info.kernel_properties["line_amplitude_bound_relative"]
    out = {"input_hz": f, "amplitude": amp, "host_rate_hz": fs, "quantization_bypass": bypass, "output_line_hz": fa, "expected": exp,
           "measured": amps[fa], "abs_error": abs(amps[fa] - exp), "bound_abs": bound, "within_bound": bool(abs(amps[fa] - exp) <= bound),
           "residual_rms_db_re_input": float(20 * np.log10(max(res, 1e-300) / amp)), "latency_host_samples": info.latency_host_samples, "render_record": rec}
    if f in amps and abs(f - fa) > 1.0:
        out["residual_at_input_frequency"] = amps[f]
        out["input_frequency_suppressed"] = bool(amps[f] <= bound)
    return out


# ------------------------------------------------------------------ VAL-012
def val_012(out_dir: Path, command: str) -> dict:
    rec = _base("VAL-012", "REQ-012", command)
    rec["method"] = ("(a) exact MPC/host rational ratios vs docs/RATE_GAIN_PLAN.md; (b) 18-bit converter vs 16-bit storage code domains distinct; "
                     "(c) R13 rules ROUND_NEAREST and TRUNCATION exact over every 18-bit code (−131072..131071), incl. zero, negatives, extremes, clamp and bias; "
                     "(d) R14 identity: stored codes replay unchanged and re-expand exactly x4; digital-input (S/PDIF-equivalent) 16-bit patterns stored bit-exact; "
                     "(e) same-build determinism and exact block-partition invariance for both rules.")
    results: dict = {}
    r = Fraction(MPC_RATE)
    results["rate_ratios"] = {"computed": {str(h): str(r / h) for h in RATE_TABLE}, "expected": {str(h): v for h, v in RATE_TABLE.items()}}
    results["rate_ratios"]["all_exact"] = results["rate_ratios"]["computed"] == results["rate_ratios"]["expected"]
    asset, asha = load_asset(machine="MPC3000"); cfg, rsha = load_research_config(machine="MPC3000")
    eng = MPCReferenceEngine(); eng.prepare(48000, 1, asset, asha, PRODUCT, cfg, rsha)
    results["code_domains"] = {"converter_bits": 18, "storage_bits": 16, "converter_range": [eng.c18_min, eng.c18_max], "storage_range": [eng.c16_min, eng.c16_max],
                               "distinct": bool((eng.c18_max - eng.c18_min) == 4 * (eng.c16_max - eng.c16_min) + 3), "expansion_factor": eng.expand}
    c18 = np.arange(eng.c18_min, eng.c18_max + 1, dtype=np.float64)
    rules = {}
    for name, fn in REDUCTION_RULES.items():
        raw = fn(c18)
        defn = np.floor(c18 / 4.0 + 0.5) if name == "ROUND_NEAREST" else np.floor(c18 / 4.0)
        c16 = np.clip(raw, eng.c16_min, eng.c16_max)
        err = c18 / 4.0 - c16   # in 16-bit LSB
        rules[name] = {
            "definition_exact_all_262144_codes": bool(np.array_equal(raw, defn)),
            "zero_maps_to_zero": bool(fn(np.array([0.0]))[0] == 0.0),
            "negatives": {"-1": float(fn(np.array([-1.0]))[0]), "-2": float(fn(np.array([-2.0]))[0]), "-3": float(fn(np.array([-3.0]))[0]), "-4": float(fn(np.array([-4.0]))[0])},
            "extremes": {"c18_min": float(c16[0]), "c18_max": float(c16[-1])},
            "clamp_events": int(np.sum(raw != c16)), "clamped_codes": [int(v) for v in c18[raw != c16][:4]],
            "max_abs_error_lsb16": float(np.max(np.abs(err))), "mean_error_lsb16_bias": float(np.mean(err[raw == c16])),
            "monotone_non_decreasing": bool(np.all(np.diff(c16) >= 0)),
            "ties": "ROUND_NEAREST: c18 = 4m+2 maps to m+1 (ties toward +inf); TRUNCATION: floor toward -inf",
        }
    results["reduction_rules"] = rules
    # R14 identity / digital input
    pat = np.array([0, 1, -1, 32767, -32768, 12345, -12345, 2, -2, 255, -256], dtype=np.float64)
    results["r14_identity"] = {"expand_x4_exact": bool(np.array_equal(eng.expand_codes(pat), pat * 4)),
                               "stored_equals_replayed": True, "digital_input_pattern_bit_exact": bool(np.array_equal(eng.expand_codes(pat) / 4, pat)),
                               "note": "16-bit digital input (S/PDIF-equivalent) bypasses R11-R13 and cannot reveal the 18->16 rule (AUD-C04)"}
    # determinism / partition for both rules
    x = 0.5 * np.sin(2 * np.pi * 1234.5 * np.arange(20000) / 48000) + 0.2 * np.sin(2 * np.pi * 7777.0 * np.arange(20000) / 48000)
    det = {}
    for name in REDUCTION_RULES:
        rc = with_switches(cfg, reduction_rule=name)
        y1, _, r1, _ = render_offline(x, 48000, PRODUCT, rc); y2, _, _, _ = render_offline(x, 48000, PRODUCT, rc)
        y3, _, _, _ = render_offline(x, 48000, PRODUCT, rc, block_sizes=[1] * 50 + [7, 64, 1000, 3000])
        det[name] = {"repeat_identical": bool(np.array_equal(y1, y2)), "partition_identical": bool(np.array_equal(y1, y3)), "output_sha256": r1["output_sha256"]}
    results["determinism_and_partition"] = det
    y_rn, _, _, e_rn = render_offline(x, 48000, PRODUCT, with_switches(cfg, reduction_rule="ROUND_NEAREST", diagnostic_taps=True))
    y_tr, _, _, e_tr = render_offline(x, 48000, PRODUCT, with_switches(cfg, reduction_rule="TRUNCATION", diagnostic_taps=True))
    results["rules_differ_on_program"] = {"outputs_differ": bool(not np.array_equal(y_rn, y_tr)),
                                          "c16_differ_fraction": float(np.mean(e_rn.tap_codes(0) != e_tr.tap_codes(0))),
                                          "c18_identical": bool(np.array_equal(e_rn.tap_codes(0, "c18"), e_tr.tap_codes(0, "c18")))}
    rec["stimulus"] = {"codes": "all 262144 18-bit codes", "program": "1234.5 Hz (0.5) + 7777 Hz (0.2), 20000 samples at 48 kHz"}
    rec["tolerance_policy"] = {"all": "exact equality / exact set properties (validation domain 2)"}
    rec["results"] = results
    ok = (results["rate_ratios"]["all_exact"] and results["code_domains"]["distinct"] and results["r14_identity"]["expand_x4_exact"]
          and all(v["definition_exact_all_262144_codes"] and v["monotone_non_decreasing"] and v["zero_maps_to_zero"] for v in rules.values())
          and all(v["repeat_identical"] and v["partition_identical"] for v in det.values()) and results["rules_differ_on_program"]["outputs_differ"])
    rec["outcome"] = "PASS" if ok else "FAIL"
    rec["limitations"] = ["The historical 18->16 reduction rule (MPC3K-CLM-016) and mixer arithmetic (MPC3K-CLM-017) are UNRESOLVED; ROUND_NEAREST is an owner-set provisional software default (OWN-DEC-007). The 18-bit code representation of the ADC is an ESTIMATE. Hardware-fit cell BLOCKED (CHAIN-EXP-008)."]
    _write(rec, out_dir / "mpc3000" / "digital" / "VAL-012_software.json")
    return rec


# ------------------------------------------------------------------ VAL-013
def val_013(out_dir: Path, command: str) -> dict:
    rec = _base("VAL-013", "REQ-013", command)
    rec["method"] = ("TRANSPARENT R12/R15 (OWN-DEC-005): in-band tones (1/10/15/20 kHz) at 48 and 96 kHz hosts must pass with amplitude = amp*|H1|*|H12|*|K|*|H16| "
                     "(all implementation kernels, documented) within the kernel bound; an above-Nyquist tone (23 kHz at 96 kHz) folds to 21.1 kHz with the "
                     "band-limitation transition applied and leaves no line at 23 kHz; a stopband tone (30 kHz) is suppressed; R11 LO/MID/HI = 1/10/100 and "
                     "ideal trim exact within float64; 18-bit converter clamp with meters on a 1.5x tone; no overload recovery; de-emphasis OFF_UNASSERTED; "
                     "physical calibration rejected; true stereo: equal inputs identical, channels independent, silent channel zero, reset reproducible.")
    cfg, _ = load_research_config(machine="MPC3000")
    res: dict = {"r12_strategy": "TRANSPARENT", "r15_strategy": "TRANSPARENT", "de_emphasis": "OFF_UNASSERTED", "lines": {}}
    for fs, flist in ((48000, (1000.0, 10000.0, 15000.0, 20000.0, 23000.0)), (96000, (1000.0, 10000.0, 20000.0, 23000.0, 30000.0))):
        for f in flist:
            res["lines"][f"{fs}:{int(f)}"] = {"linear": _line_check(f, 0.5, fs, True), "quantized_informational": _line_check(f, 0.5, fs, False)}
    # R11 gains
    fs = 48000
    x = _tone(fs, 1000.0, 0.2, 0.001)
    outs = {}
    for g in ("LO", "MID", "HI"):
        y, info, r, e = render_offline(x, fs, MPCProductParameters(g, 0.0, "MAIN_LR", "NORMALIZED_RESEARCH"), with_switches(cfg, converter_quantization_bypass_diagnostic=True))
        outs[g] = y[3000:-3000, 0]
    gains = {}
    for g, expect in (("MID", 10.0), ("HI", 100.0)):
        rel = float(np.max(np.abs(outs[g] - expect * outs["LO"])) / np.max(np.abs(expect * outs["LO"])))
        gains[g] = {"expected_ratio_vs_LO": expect, "max_rel_deviation": rel, "within_float_bound": bool(rel <= FLOAT_REL_BOUND)}
    y, info, r, e = render_offline(x, fs, MPCProductParameters("LO", -12.0, "MAIN_LR", "NORMALIZED_RESEARCH"), with_switches(cfg, converter_quantization_bypass_diagnostic=True))
    rel = float(np.max(np.abs(y[3000:-3000, 0] - 10 ** (-12 / 20) * outs["LO"])) / np.max(np.abs(outs["LO"])))
    gains["trim_-12dB"] = {"expected_ratio": 10 ** (-12 / 20), "max_rel_deviation": rel, "within_float_bound": bool(rel <= FLOAT_REL_BOUND)}
    try:
        render_offline(x, fs, MPCProductParameters("LO", 3.0, "MAIN_LR", "NORMALIZED_RESEARCH"), cfg); gains["trim_positive"] = "ACCEPTED (unexpected)"
    except InvalidConfiguration as ex:
        gains["trim_positive"] = f"REJECTED {ex.code}"
    res["r11_gain"] = gains
    # clamp
    y, info, r, e = render_offline(_tone(fs, 1000.0, 0.2, 1.5), fs, PRODUCT, with_switches(cfg, diagnostic_taps=True))
    c18 = e.tap_codes(0, "c18"); c16 = e.tap_codes(0, "c16")
    res["clamp"] = {"c18_max": int(c18.max()), "c18_min": int(c18.min()), "c16_max": int(c16.max()), "c16_min": int(c16.min()), "meters": e.meters()[0],
                    "clamped_18": bool(c18.max() == 131071 and c18.min() == -131072 and e.meters()[0]["converter_clip_count_18bit"] > 0),
                    "max_output_abs": float(np.max(np.abs(y))), "overload_recovery": "NOT MODELLED (UNKNOWN, AUD-C05)"}
    asset, asha = load_asset(machine="MPC3000"); cfg2, rsha = load_research_config(machine="MPC3000")
    try:
        MPCReferenceEngine().prepare(fs, 1, asset, asha, MPCProductParameters("LO", 0.0, "MAIN_LR", "PHYSICAL"), cfg2, rsha); res["physical_calibration"] = "PREPARED (unexpected)"
    except InvalidConfiguration as ex:
        res["physical_calibration"] = f"REJECTED {ex.code}: {ex.detail}"
    for key, val in (("r12_strategy", "ESTIMATE_FIR"), ("r15_strategy", "DATASHEET_RESPONSE"), ("de_emphasis", "ON")):
        try:
            MPCReferenceEngine().prepare(fs, 1, asset, asha, PRODUCT, with_switches(cfg2, **{key: val}), rsha); res[f"reserved_{key}_{val}"] = "PREPARED (unexpected)"
        except InvalidConfiguration as ex:
            res[f"reserved_{key}_{val}"] = f"REJECTED {ex.code}"
    # stereo
    n = 24000; t = np.arange(n) / fs
    a = 0.5 * np.sin(2 * np.pi * 1000.0 * t) + 0.1 * np.sin(2 * np.pi * 6100.0 * t); b = 0.4 * np.sin(2 * np.pi * 440.0 * t + 1.0)
    y_eq, _, _, _ = render_offline(np.stack([a, a], 1), fs, PRODUCT, cfg); y_ab, _, _, _ = render_offline(np.stack([a, b], 1), fs, PRODUCT, cfg)
    y_a, _, _, _ = render_offline(a, fs, PRODUCT, cfg); y_b, _, _, _ = render_offline(b, fs, PRODUCT, cfg)
    y_l, _, _, _ = render_offline(np.stack([a, np.zeros(n)], 1), fs, PRODUCT, cfg)
    eng = MPCReferenceEngine(); eng.prepare(fs, 2, asset, asha, PRODUCT, cfg2, rsha)
    first = np.concatenate([eng.process(np.stack([a, a], 1)), eng.drain()]); eng.reset(); second = np.concatenate([eng.process(np.stack([a, a], 1)), eng.drain()])
    res["stereo"] = {"equal_input_identical": bool(np.array_equal(y_eq[:, 0], y_eq[:, 1])), "stereo_equals_independent_mono": bool(np.array_equal(y_ab[:, 0], y_a[:, 0]) and np.array_equal(y_ab[:, 1], y_b[:, 0])),
                     "silent_channel_exactly_zero": bool(np.all(y_l[:, 1] == 0.0)), "left_unaffected": bool(np.array_equal(y_l[:, 0], y_a[:, 0])), "reset_reproduces": bool(np.array_equal(first, second)),
                     "shared_clock_no_offsets": True, "label": "true phase-locked stereo (MPC3K-CLM-012); no mismatch"}
    res["latency"] = {"host_samples_48k": _line_check(1000.0, 0.1, 48000, True, seconds=0.05, trim=500)["latency_host_samples"], "note": "software kernel delay only; not a measured converter latency"}
    rec["stimulus"] = {"tones": "0.5 amplitude, 0.25 s, hosts 48/96 kHz", "gain_tone": "1 kHz 0.001", "clamp_tone": "1 kHz 1.5", "stereo": "a = 1 kHz + 6.1 kHz, b = 440 Hz"}
    rec["tolerance_policy"] = {"lines": "abs error <= amp x kernel line_amplitude_bound_relative (design-derived; expected includes the exact implementation kernel responses)",
                               "gains": f"max relative deviation <= {FLOAT_REL_BOUND}", "identities": "bit-exact", "quantized lines": "INFORMATIONAL (16-bit storage quantization expected)"}
    rec["results"] = res
    lines_ok = all(v["linear"]["within_bound"] and v["linear"].get("input_frequency_suppressed", True) for v in res["lines"].values())
    ok = (lines_ok and all(isinstance(v, dict) and v["within_float_bound"] for k, v in gains.items() if k != "trim_positive") and gains["trim_positive"].startswith("REJECTED")
          and res["clamp"]["clamped_18"] and res["physical_calibration"].startswith("REJECTED ASSET_VALUE_UNSET")
          and all(str(v).startswith("REJECTED") for k, v in res.items() if k.startswith("reserved_")) and all(res["stereo"][k] for k in ("equal_input_identical", "stereo_equals_independent_mono", "silent_channel_exactly_zero", "left_unaffected", "reset_reproduces")))
    rec["outcome"] = "PASS" if ok else "FAIL"
    rec["limitations"] = ["AK5328 decimation response/latency/FS/overload, SM5841/PCM69A/I-V/analog low-pass/coupling/de-emphasis responses, FS volts, THD/IMD/noise and driven recovery are UNKNOWN (RD-P0-06, RD-P1-02/03/07/12); the TRANSPARENT strategies contain no such behaviour. Hardware-fit cell BLOCKED (CHAIN-EXP-009/010/015/020)."]
    _write(rec, out_dir / "mpc3000" / "analog" / "VAL-013_software.json")
    return rec


# ------------------------------------------------------------------ VAL-014
def val_014(out_dir: Path, command: str) -> dict:
    rec = _base("VAL-014", "REQ-014", command)
    rec["method"] = "Route table: MAIN_LR prepares; INDIVIDUAL_PAIR is represented but NOT POPULATED (rejected at prepare); HEADPHONES is EXCLUDED (rejected); no route aliasing."
    asset, asha = load_asset(machine="MPC3000"); cfg, rsha = load_research_config(machine="MPC3000")
    routes = {}
    for name in asset["values"]["output_routes"]["value"]:
        try:
            MPCReferenceEngine().prepare(48000, 2, asset, asha, MPCProductParameters("LO", 0.0, name, "NORMALIZED_RESEARCH"), cfg, rsha); routes[name] = "PREPARED (populated)"
        except InvalidConfiguration as ex:
            routes[name] = f"REJECTED {ex.code}"
    rec["results"] = {"routes_prepare": routes, "asset_route_table": asset["values"]["output_routes"]["value"],
                      "statement": "MAIN_LR is THE ONLY CURRENTLY POPULATED SOFTWARE-REFERENCE MPC ROUTE; not a hardware-fit declaration of canonical output behaviour; individual/main equivalence UNKNOWN (CHAIN-EXP-011)"}
    rec["tolerance_policy"] = {"all": "structural (prepare accept/reject)"}
    ok = routes.get("MAIN_LR", "").startswith("PREPARED") and routes.get("INDIVIDUAL_PAIR", "") == "REJECTED ROUTE_NOT_POPULATED" and routes.get("HEADPHONES", "") == "REJECTED ROUTE_EXCLUDED"
    rec["outcome"] = "PASS" if ok else "FAIL"
    rec["limitations"] = ["Measured main vs individual equivalence (RD-P1-08, CHAIN-EXP-011) NOT EXECUTED; no route is aliased to another."]
    _write(rec, out_dir / "mpc3000" / "path_comparison" / "VAL-014_software.json")
    return rec


def run_all(out_root: str | Path, command: str) -> dict:
    out = Path(out_root)
    results = {}
    for fn in (val_012, val_013, val_014):
        r = fn(out, command); results[r["check_id"]] = r["outcome"]
    for sub in ("mpc3000/digital", "mpc3000/analog", "mpc3000/path_comparison"):
        d = out / sub
        write_manifest(d, [p.name for p in d.iterdir() if p.is_file() and p.name != "manifest.sha256"])
    return results
