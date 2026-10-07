"""Sprint 5 software-track validation (VAL-015 / VAL-016 software cells; Track A, OWN-DEC-009..013).

SIMULATION only: composition identities, chain modes, latency alignment, interstage mapping, product
configuration, and INFORMATIONAL software derivatives of CHAIN-EXP-013/014. No hardware, no listener data.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .. import environment as env
from ..hashing import sha256_array, write_manifest
from ..schemas import VALIDATION_RECORD, validate
from ..reference.cascade import (CHAIN_MODES, PRODUCT_DEFAULT_CHAIN_MODE, RESEARCH_CHAIN_MODES, CascadeProductParameters, CascadeReferenceEngine,
                                 load_cascade_research_config, load_product_config)
from ..reference.errors import InvalidConfiguration
from ..reference.mpc3000 import MPCProductParameters
from ..reference.render import render_offline, with_switches
from ..reference.assets import load_asset, load_research_config
from ..reference.sp1200 import SPProductParameters
from ..reference.streaming import Decimator
from .measure import fit_components

SP = SPProductParameters(0.0, 0, "NONE_CH7_8", "NORMALIZED_RESEARCH")
MPC = MPCProductParameters("LO", 0.0, "MAIN_LR", "NORMALIZED_RESEARCH")
FLOAT_REL_BOUND = 1e-9


def _base(check_id, req, command):
    pc, psha = load_product_config(); cc, csha = load_cascade_research_config()
    sa, ssha = load_asset(machine="SP-1200"); ma, msha = load_asset(machine="MPC3000")
    return {"check_id": check_id, "requirement_id": req, "track": "A", "artifact_class": "SIMULATION", "dataset_role": "NONE",
            "asset_identity": {"asset_id": "cascade(sp1200-track-a-provisional v1 + mpc3000-track-a-provisional v1)", "version": "1", "model_version": "cascade-reference-impl-1.0.0",
                               "sha256": sha256_array(np.frombuffer((ssha + msha + psha + csha).encode(), dtype=np.uint8))},
            "research_config_sha256": csha, "software": env.software_record(), "source_commit": env.git_describe(), "environment": env.environment_record(),
            "command": command, "stimulus": {}, "method": "", "tolerance_policy": {}, "results": {}, "outcome": "NOT EXECUTED",
            "hardware_fit_outcome": "BLOCKED", "limitations": [], "timestamp_utc": env.utc_now()}


def _write(rec, path: Path):
    problems = validate(rec, VALIDATION_RECORD)
    if problems:
        raise RuntimeError(f"{rec['check_id']} record invalid: {problems}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rec, indent=1, sort_keys=True), encoding="utf-8")


def run_cascade(x, fs, mode, g10=0.0, chunks=None, channels=None, cascade_research=None):
    x = np.asarray(x, dtype=np.float64); x = x[:, None] if x.ndim == 1 else x
    e = CascadeReferenceEngine(); info = e.prepare(fs, x.shape[1], CascadeProductParameters(SP, MPC, g10, mode), cascade_research=cascade_research)
    outs = []
    if chunks is None:
        outs.append(e.process(x))
    else:
        i = 0
        for n in chunks:
            outs.append(e.process(x[i:i + n])); i += n
        outs.append(e.process(x[i:]))
    outs.append(e.drain()); y = np.concatenate(outs, 0)
    return y[info.latency_host_samples:info.latency_host_samples + x.shape[0]], info, e


def _tone(fs, f, seconds, amp):
    return amp * np.sin(2 * np.pi * f * np.arange(int(seconds * fs)) / fs)


# ------------------------------------------------------------------ VAL-015
def val_015(out_dir: Path, command: str) -> dict:
    rec = _base("VAL-015", "REQ-015", command)
    rec["method"] = ("Cascade composition on the proxy grid (R1 → SP core → R10 → MPC core → R16). Identities (bit-exact): SP_ONLY == standalone SP engine; "
                     "MPC_ONLY == standalone MPC engine fed the input delayed by the SP-core delay, shifted back by that delay (same sampling phase); CASCADE == explicit manual composition of the "
                     "engines' public cores; same latency for every chain mode; BOTH_MACHINE_BYPASSED == R1/R16 round trip only (no gain, no machine); determinism and "
                     "block-partition invariance; stereo identities. Interstage: exact 10^(dB/20) mapping on a low-level tone (-60, -20, 0, +6 dB), converter clamp at "
                     "+20 dB with meters, out-of-range rejected, 0 dB level-neutral within the kernel bound; no hidden normalization or saturation.")
    fs = 48000
    x = 0.5 * np.sin(2 * np.pi * 1234.5 * np.arange(20000) / fs) + 0.2 * np.sin(2 * np.pi * 7777.0 * np.arange(20000) / fs)
    res: dict = {}
    yc, info_c, e_c = run_cascade(x, fs, "CASCADE")
    ysp, info_sp, _ = run_cascade(x, fs, "SP_ONLY"); ym, info_m, _ = run_cascade(x, fs, "MPC_ONLY"); yb, info_b, _ = run_cascade(x, fs, "BOTH_MACHINE_BYPASSED")
    sp_ref, sp_i, _, _ = render_offline(x, fs, SP)
    d_sp_host = e_c.sp.core_delay_proxy // e_c.L
    x_del = np.concatenate([np.zeros(d_sp_host), x])          # full length + d: no truncation of the tail
    m_ref, m_i, _, _ = render_offline(x_del, fs, MPC)
    # explicit manual composition with the engines' public pieces
    sp_e = e_c.sp; mpc_e = e_c.mpc
    from ..reference.sp1200 import SPReferenceEngine
    from ..reference.mpc3000 import MPCReferenceEngine
    from ..reference.streaming import PolyphaseUpsampler
    sa, ssha = load_asset(machine="SP-1200"); sr, srsha = load_research_config(machine="SP-1200")
    ma, msha = load_asset(machine="MPC3000"); mr, mrsha = load_research_config(machine="MPC3000")
    s2 = SPReferenceEngine(); s2.prepare(fs, 1, sa, ssha, SP, sr, srsha); m2 = MPCReferenceEngine(); m2.prepare(fs, 1, ma, msha, MPC, mr, mrsha)
    up = PolyphaseUpsampler(s2.L, s2.h_lp); down = Decimator(s2.L, s2.h_lp)
    xx = np.concatenate([x, np.zeros(info_c.latency_host_samples)])
    h = m2.core_channel(m2.ch[0], s2.core_channel(s2.ch[0], up.process(xx)) * 1.0)
    manual = down.process(h)[info_c.latency_host_samples:info_c.latency_host_samples + x.size]
    yc2, _, _ = run_cascade(x, fs, "CASCADE", chunks=[1] * 30 + [7, 64, 1000, 3000])
    yc3, _, _ = run_cascade(x, fs, "CASCADE")
    trim = 2000
    res["identities"] = {
        "sp_only_equals_sp_engine": bool(np.array_equal(ysp[:, 0], sp_ref[:, 0])),
        "mpc_only_equals_mpc_engine_on_delayed_input": bool(np.array_equal(ym[:, 0], m_ref[d_sp_host:d_sp_host + x.size, 0])),
        "mpc_only_identity_note": "cascade output aligned by the cascade latency equals the standalone MPC engine output (aligned by its own latency) on the input delayed by the SP-core delay, shifted back by that delay: same 44.1 kHz sampling phase",
        "cascade_equals_manual_composition": bool(np.array_equal(yc[:, 0], manual)),
        "partition_identical": bool(np.array_equal(yc, yc2)), "repeat_identical": bool(np.array_equal(yc, yc3)),
        "latency_all_modes": {"CASCADE": info_c.latency_host_samples, "SP_ONLY": info_sp.latency_host_samples, "MPC_ONLY": info_m.latency_host_samples, "BOTH_MACHINE_BYPASSED": info_b.latency_host_samples},
        "latency_equal_all_modes": bool(len({info_c.latency_host_samples, info_sp.latency_host_samples, info_m.latency_host_samples, info_b.latency_host_samples}) == 1),
        "latency_equals_sp_plus_mpc_core_delays_plus_r1_r16": bool(info_c.latency_host_samples == (sp_i.latency_host_samples + m_i.latency_host_samples - 2 * ((e_c.sp.h_lp.size - 1) // 2) // e_c.L)),
        "bypass_round_trip_max_abs_diff_trimmed": float(np.max(np.abs(yb[trim:-trim, 0] - x[trim:-trim]))),
        "bypass_round_trip_bound": float(0.7 * info_c.sp_info["kernel_properties"]["line_amplitude_bound_relative"] * 4),
        "cascade_differs_from_sp_only": bool(not np.array_equal(yc, ysp)), "cascade_differs_from_mpc_only": bool(not np.array_equal(yc, ym)),
    }
    res["identities"]["bypass_within_bound"] = bool(res["identities"]["bypass_round_trip_max_abs_diff_trimmed"] <= res["identities"]["bypass_round_trip_bound"])
    # stereo
    n = 16000; a = 0.5 * np.sin(2 * np.pi * 1000.0 * np.arange(n) / fs) + 0.1 * np.sin(2 * np.pi * 6100.0 * np.arange(n) / fs); b = 0.4 * np.sin(2 * np.pi * 440.0 * np.arange(n) / fs + 1.0)
    y_eq, _, _ = run_cascade(np.stack([a, a], 1), fs, "CASCADE"); y_ab, _, _ = run_cascade(np.stack([a, b], 1), fs, "CASCADE")
    y_a, _, _ = run_cascade(a, fs, "CASCADE"); y_b, _, _ = run_cascade(b, fs, "CASCADE"); y_l, _, _ = run_cascade(np.stack([a, np.zeros(n)], 1), fs, "CASCADE")
    e = CascadeReferenceEngine(); e.prepare(fs, 2, CascadeProductParameters(SP, MPC, 0.0, "CASCADE"))
    first = np.concatenate([e.process(np.stack([a, a], 1)), e.drain()]); e.reset(); second = np.concatenate([e.process(np.stack([a, a], 1)), e.drain()])
    res["stereo"] = {"equal_input_identical": bool(np.array_equal(y_eq[:, 0], y_eq[:, 1])), "stereo_equals_independent_mono": bool(np.array_equal(y_ab[:, 0], y_a[:, 0]) and np.array_equal(y_ab[:, 1], y_b[:, 0])),
                     "silent_channel_exactly_zero": bool(np.all(y_l[:, 1] == 0.0)), "left_unaffected": bool(np.array_equal(y_l[:, 0], y_a[:, 0])), "reset_reproduces": bool(np.array_equal(first, second)),
                     "label": "SP stage linked dual mono (PRODUCT ABSTRACTION) → MPC true stereo; parameters linked"}
    # interstage mapping: low-level tone so no clamp up to +6 dB; compare to 0 dB render scaled (quantization makes this inexact → use quantization bypass on both machines)
    sr_b = with_switches(sr, quantizer_bypass_diagnostic=True); mr_b = with_switches(mr, converter_quantization_bypass_diagnostic=True)
    xt = _tone(fs, 1000.0, 0.2, 0.001)
    def run_lin(g):
        e = CascadeReferenceEngine(); info = e.prepare(fs, 1, CascadeProductParameters(SP, MPC, g, "CASCADE"), sp_research=(sr_b, "diag"), mpc_research=(mr_b, "diag"))
        y = np.concatenate([e.process(xt[:, None]), e.drain()])[info.latency_host_samples:info.latency_host_samples + xt.size, 0]
        return y[3000:-3000]
    y0 = run_lin(0.0)
    inter = {}
    for g in (-60.0, -20.0, 6.0):
        yg = run_lin(g); expect = 10 ** (g / 20)
        rel = float(np.max(np.abs(yg - expect * y0)) / np.max(np.abs(expect * y0)))
        inter[f"{g:+.0f}dB"] = {"expected_linear": expect, "max_rel_deviation": rel, "within_float_bound": bool(rel <= FLOAT_REL_BOUND)}
    # 0 dB level neutrality (linear): output tone amplitude vs input amplitude within kernel bound (R1,R12 band limit, K, R16 all ≈ 1 at 1 kHz)
    amps, _ = fit_components(y0, fs, [1000.0]); bound = 0.001 * (info_c.sp_info["kernel_properties"]["line_amplitude_bound_relative"] + info_c.mpc_info["kernel_properties"]["line_amplitude_bound_relative"])
    # level-neutral "subject to the already implemented behaviour": the SP full-period hold droop sinc(f/fsp) (SP12-CLM-020) and the
    # implementation kernels (≈1 at 1 kHz) are part of the expected amplitude; R10 itself adds no gain at 0 dB
    from .measure import zoh_magnitude
    from ..reference.kernels import frequency_response, interpolation_kernel_response
    fp = fs * e_c.L
    expected = 0.001 * zoh_magnitude(1000.0, 20_000_000 / 768) * abs(frequency_response(e_c.sp.h_lp, 1000.0 / fp)[0]) ** 2 * abs(frequency_response(e_c.mpc.h_r12, 1000.0 / fp)[0]) * float(interpolation_kernel_response(e_c.mpc.hw_r, e_c.mpc.interp_beta, 1000.0 / 44100)[0])
    inter["0dB_level_neutral"] = {"input_amplitude": 0.001, "expected_amplitude_with_implemented_behaviour": expected, "sp_hold_droop_db_at_1k": float(20 * np.log10(zoh_magnitude(1000.0, 20_000_000 / 768))),
                                  "output_amplitude": amps[1000.0], "abs_error": abs(amps[1000.0] - expected), "bound": bound, "within_bound": bool(abs(amps[1000.0] - expected) <= bound),
                                  "r10_gain_at_0dB": 1.0}
    # clamp at +20 dB on a 0.5 tone (quantizers active)
    yclamp, info_cl, e_cl = run_cascade(_tone(fs, 1000.0, 0.2, 0.5), fs, "CASCADE", g10=20.0)
    inter["+20dB_clamp"] = {"mpc_meters": e_cl.meters()["mpc"][0], "sp_meters": e_cl.meters()["sp"][0], "max_output_abs": float(np.max(np.abs(yclamp))),
                            "converter_clamp_reached": bool(e_cl.meters()["mpc"][0]["converter_clip_count_18bit"] > 0), "sp_not_clipped": bool(e_cl.meters()["sp"][0]["converter_clip_count"] == 0),
                            "overload_model": "18-bit converter code clamp only; no recovery, no saturation"}
    yq, _, e_q = run_cascade(_tone(fs, 1000.0, 0.2, 0.5), fs, "CASCADE", g10=6.0)
    inter["+6dB_clamp_on_0p5_tone"] = {"converter_clamp_reached": bool(e_q.meters()["mpc"][0]["converter_clip_count_18bit"] > 0), "note": "0.5 x 2.0 = 1.0 reaches full scale → clamp events expected"}
    for g in (-61.0, 25.0):
        try:
            run_cascade(x[:100], fs, "CASCADE", g10=g); inter[f"range_{g:+.0f}dB"] = "ACCEPTED (unexpected)"
        except InvalidConfiguration as ex:
            inter[f"range_{g:+.0f}dB"] = f"REJECTED {ex.code}"
    inter["default"] = {"interstage_level_db": 0.0, "status": info_c.interstage_status, "volts": "UNSET", "hidden_normalization": "none", "hidden_saturation": "none"}
    res["interstage"] = inter
    rec["stimulus"] = {"program": "1234.5 Hz (0.5) + 7777 Hz (0.2), 20000 samples at 48 kHz", "interstage_tone": "1 kHz 0.001 (linear diagnostics) and 0.5 (clamp)", "stereo": "a = 1 kHz + 6.1 kHz, b = 440 Hz"}
    rec["tolerance_policy"] = {"identities": "bit-exact", "interstage_gain": f"max relative deviation <= {FLOAT_REL_BOUND} (float64; linear diagnostics)", "0 dB neutrality": "abs error <= amp x (SP + MPC kernel line bounds)",
                               "bypass round trip": "trimmed max abs diff <= 4 x peak x SP kernel line bound (R1/R16 transition products; informational bound derived from the kernel)"}
    rec["results"] = res
    idn = res["identities"]
    ok = (idn["sp_only_equals_sp_engine"] and idn["mpc_only_equals_mpc_engine_on_delayed_input"] and idn["cascade_equals_manual_composition"] and idn["partition_identical"] and idn["repeat_identical"]
          and idn["latency_equal_all_modes"] and idn["latency_equals_sp_plus_mpc_core_delays_plus_r1_r16"] and idn["bypass_within_bound"] and idn["cascade_differs_from_sp_only"]
          and all(res["stereo"][k] for k in ("equal_input_identical", "stereo_equals_independent_mono", "silent_channel_exactly_zero", "left_unaffected", "reset_reproduces"))
          and all(v["within_float_bound"] for k, v in inter.items() if k.endswith("dB") and isinstance(v, dict) and "within_float_bound" in v)
          and inter["0dB_level_neutral"]["within_bound"] and inter["+20dB_clamp"]["converter_clamp_reached"] and inter["+20dB_clamp"]["sp_not_clipped"]
          and inter["range_-61dB"].startswith("REJECTED") and inter["range_+25dB"].startswith("REJECTED"))
    rec["outcome"] = "PASS" if ok else "FAIL"
    rec["limitations"] = ["Interstage 0 dB is an owner-set provisional software default (OWN-DEC-009), NON-HISTORICAL: SP output volts and MPC volts per full scale are UNKNOWN (RD-P0-02/03/06; CHAIN-EXP-005/009/012 NOT EXECUTED). Hardware-fit cell BLOCKED."]
    _write(rec, out_dir / "cascade" / "VAL-015_software.json")
    return rec


# ------------------------------------------------------------------ VAL-016
def val_016(out_dir: Path, command: str) -> dict:
    rec = _base("VAL-016", "REQ-016", command)
    rec["method"] = ("Software product decision (G-07S, OWNER-APPROVED): path B, routes NONE_CH7_8 / MAIN_LR, linked dual mono labelled PRODUCT ABSTRACTION, chain-mode default "
                     "CASCADE with research modes, no drive/wet-dry; verified structurally against the product configuration record and the engines. INFORMATIONAL software "
                     "derivatives of CHAIN-EXP-014 (DRY/SP/MPC/SP→MPC metrics) and CHAIN-EXP-013 (reverse order) on a bright multitone; listening kit prepared (CHAIN-EXP-018 "
                     "software arm), human listening NOT EXECUTED; G-07H BLOCKED.")
    pc, psha = load_product_config()
    fs = 48000
    res: dict = {"product_config_sha256": psha, "product_path": pc["product_path"]["selected"], "routes": pc["routes"], "stereo": pc["stereo"],
                 "chain_modes": pc["chain_modes"], "controls": pc["controls"], "cascade_order": pc["cascade_order"]}
    # structural: product default chain mode, research modes present, reverse order off by default, non-product routes rejected by the cascade
    cc, _ = load_cascade_research_config()
    res["structural"] = {"product_default_chain_mode": PRODUCT_DEFAULT_CHAIN_MODE, "research_modes": list(RESEARCH_CHAIN_MODES), "all_modes": list(CHAIN_MODES),
                         "reverse_order_default_off": bool(not cc["switches"]["reverse_order_research"]), "drive_macro": "NONE", "wet_dry": "NONE"}
    try:
        run_cascade(np.zeros(100), fs, "CASCADE"); res["structural"]["product_routes_prepare"] = "OK"
    except InvalidConfiguration as ex:
        res["structural"]["product_routes_prepare"] = f"REJECTED {ex.code}"
    try:
        e = CascadeReferenceEngine(); e.prepare(fs, 1, CascadeProductParameters(SPProductParameters(0.0, 0, "FIXED_CH5_6", "NORMALIZED_RESEARCH"), MPC, 0.0, "CASCADE"))
        res["structural"]["non_product_route"] = "ACCEPTED (unexpected)"
    except InvalidConfiguration as ex:
        res["structural"]["non_product_route"] = f"REJECTED {ex.code}"
    # CHAIN-EXP-014 software derivative (INFORMATIONAL)
    from ..stimuli import multitone
    n = int(1.0 * fs); t = np.arange(n) / fs
    tones = multitone(31, 60.0, 18000.0, 101, 0.5)
    x = sum(tn.amplitude * np.sin(2 * np.pi * tn.freq_hz * t + tn.phase_rad) for tn in tones)
    freqs = [tn.freq_hz for tn in tones]
    def metrics(y, label):
        seg = y[3000:-3000]; amps, resid = fit_components(seg, fs, freqs)
        return {"label": label, "rms_db": float(20 * np.log10(np.sqrt(np.mean(seg ** 2)))), "peak_db": float(20 * np.log10(np.max(np.abs(seg)))),
                "crest_db": float(20 * np.log10(np.max(np.abs(seg)) / np.sqrt(np.mean(seg ** 2)))),
                "tone_levels_db_re_input": {f"{f:.1f}": float(20 * np.log10(max(amps[f], 1e-12) / tn.amplitude)) for f, tn in zip(freqs, tones)},
                "residual_rms_db_re_input_rms": float(20 * np.log10(max(resid, 1e-12) / np.sqrt(np.mean(x[3000:-3000] ** 2))))}
    cmp = {}
    for mode, label in (("BOTH_MACHINE_BYPASSED", "DRY"), ("SP_ONLY", "SP"), ("MPC_ONLY", "MPC"), ("CASCADE", "SP_TO_MPC")):
        y, _, _ = run_cascade(x, fs, mode); cmp[label] = metrics(y[:, 0], label)
    yr, _, _ = run_cascade(x, fs, "CASCADE", cascade_research=({"config_id": "cascade-track-a-research-config", "version": "1", "switches": {"reverse_order_research": True}}, "informational-reverse"))
    cmp["MPC_TO_SP_informational"] = metrics(yr[:, 0], "MPC_TO_SP (CHAIN-DEC-013 research only)")
    res["chain_exp_014_software_derivative"] = {"status": "INFORMATIONAL SIMULATION (hardware CHAIN-EXP-014 NOT EXECUTED)", "stimulus": "31-tone log multitone 60 Hz–18 kHz, seed 101, peak 0.5, 1 s at 48 kHz", "conditions": cmp,
                                                "reading": "SP-dominated: tones above 13.02 kHz fold back (R3 INACTIVE) and hold droop shapes the top; MPC stage adds only 16-bit quantization and the 22.05 kHz band limit at 0 dB interstage; no hardware meaning"}
    res["chain_exp_013_software_derivative"] = {"status": "INFORMATIONAL SIMULATION (hardware CHAIN-EXP-013 NOT EXECUTED); reverse order is research-only, never product",
                                                "sp_to_mpc_vs_mpc_to_sp_rms_db": [cmp["SP_TO_MPC"]["rms_db"], cmp["MPC_TO_SP_informational"]["rms_db"]]}
    # listening kit reference
    kit = Path("research/listening/CHAIN-EXP-018/generation_record.json")
    res["listening_kit"] = {"prepared": kit.exists(), "record": str(kit) if kit.exists() else "NOT GENERATED", "human_listening": "NOT EXECUTED", "criterion": "NONE DEFINED (owner/validation lead)", "hardware_arm": "G-07H BLOCKED (slot reserved)"}
    if kit.exists():
        kr = json.loads(kit.read_text(encoding="utf-8")); res["listening_kit"].update({"files": len(kr["entries"]), "kit_version": kr["kit_version"], "status": kr["status"]})
    rec["stimulus"] = {"multitone": "31 tones 60 Hz–18 kHz seed 101"}
    rec["tolerance_policy"] = {"structural": "accept/reject", "derivatives": "INFORMATIONAL (no criterion defined; none invented)"}
    rec["results"] = res
    ok = (res["product_path"] == "B" and res["structural"]["reverse_order_default_off"] and res["structural"]["product_routes_prepare"] == "OK" and res["structural"]["non_product_route"].startswith("REJECTED")
          and res["listening_kit"]["prepared"])
    rec["outcome"] = "PASS" if ok else "FAIL"
    rec["limitations"] = ["Software product decision only (OWN-DEC-010); hardware-informed confirmation G-07H BLOCKED; no human listening occurred; CHAIN-EXP-013/014/018 hardware arms NOT EXECUTED."]
    _write(rec, out_dir / "cascade" / "VAL-016_software.json")
    return rec


def run_all(out_root, command: str) -> dict:
    out = Path(out_root); results = {}
    for fn in (val_015, val_016):
        r = fn(out, command); results[r["check_id"]] = r["outcome"]
    d = out / "cascade"; write_manifest(d, [p.name for p in d.iterdir() if p.is_file() and p.name != "manifest.sha256"])
    return results
