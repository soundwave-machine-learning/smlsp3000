"""Sprint 3 software-track validation (VAL-008/009/010/011/017 software cells; Track A).

Every check is a SIMULATION against the implementation's own documented equations
and closed-form expectations. Nothing here compares to hardware; every record
carries hardware_fit_outcome = BLOCKED. Nonzero bounds are derived from the
kernel design (PreparedInfo.kernel_properties) or from float64 arithmetic, and
are written into the record's tolerance_policy.
"""
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

import numpy as np

from .. import environment as env
from ..hashing import sha256_array, write_manifest
from ..schemas import VALIDATION_RECORD, validate
from ..reference.assets import load_asset, load_research_config
from ..reference.errors import InvalidConfiguration
from ..reference.kernels import frequency_response
from ..reference.render import render_offline, with_switches
from ..reference.sp1200 import QUANTIZER_RULES, SPProductParameters, SPReferenceEngine
from .measure import fit_components, image_frequencies, zoh_magnitude

SP_NUM, SP_DEN = 20_000_000, 768
RATE_TABLE = {44100: "3125/5292", 48000: "625/1152", 88200: "3125/10584", 96000: "625/2304", 176400: "3125/21168", 192000: "625/4608"}
PRODUCT = SPProductParameters(sp_input_level_db=0.0, sp_input_gain=0, sp_output_path="NONE_CH7_8", calibration_mode="NORMALIZED_RESEARCH")
FLOAT_REL_BOUND = 1e-9  # float64 arithmetic bound for linear-gain identities (documented, not tuned)


def _base_record(check_id: str, req: str, command: str) -> dict:
    asset, asha = load_asset()
    _, rsha = load_research_config()
    return {
        "check_id": check_id, "requirement_id": req, "track": "A", "artifact_class": "SIMULATION", "dataset_role": "NONE",
        "asset_identity": {"asset_id": asset["asset_id"], "version": asset["version"], "model_version": asset["model_version"], "sha256": asha},
        "research_config_sha256": rsha, "software": env.software_record(), "source_commit": env.git_describe(),
        "environment": env.environment_record(), "command": command, "stimulus": {}, "method": "", "tolerance_policy": {},
        "results": {}, "outcome": "NOT EXECUTED", "hardware_fit_outcome": "BLOCKED", "limitations": [], "timestamp_utc": env.utc_now(),
    }


def _write(rec: dict, path: Path):
    problems = validate(rec, VALIDATION_RECORD)
    if problems:
        raise RuntimeError(f"{rec['check_id']} record invalid: {problems}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rec, indent=1, sort_keys=True), encoding="utf-8")


def _tone(fs: int, f: float, seconds: float, amp: float) -> np.ndarray:
    t = np.arange(int(round(seconds * fs))) / fs
    return amp * np.sin(2 * np.pi * f * t)


def _line_model(f: float, amp: float, fs: int, info, h_lp) -> dict[float, float]:
    """Expected amplitude of every host-band line for an input tone: images k*fsp±f below proxy Nyquist,
    aliased by decimation into the host band; amp*|H1(f)|*|ZOH(g)|*|H16(g)|. Lines that coincide are summed."""
    fsp = SP_NUM / SP_DEN
    fp = fs * info.proxy_oversampling
    h1 = abs(frequency_response(h_lp, f / fp)[0])
    lines: dict[float, float] = {}
    for g in image_frequencies(f, fsp, fp / 2, max_order=400):
        ga = abs(g - round(g / fs) * fs)
        if ga <= 0.0 or ga >= fs / 2:
            continue
        exp = amp * h1 * zoh_magnitude(g, fsp) * abs(frequency_response(h_lp, g / fp)[0])
        key = round(ga, 6)
        lines[key] = lines.get(key, 0.0) + exp
    return lines


def _lines_check(f: float, amp: float, fs: int, bypass: bool, seconds: float = 0.25, trim: int = 4000) -> dict:
    cfg, _ = load_research_config()
    x = _tone(fs, f, seconds, amp)
    y, info, rec, eng = render_offline(x, fs, PRODUCT, with_switches(cfg, quantizer_bypass_diagnostic=bypass))
    seg = y[trim:-trim, 0]
    model = _line_model(f, amp, fs, info, eng.h_lp)
    freqs = sorted(model)
    amps, res = fit_components(seg, fs, freqs)
    bound = amp * info.kernel_properties["line_amplitude_bound_relative"]
    errs = {str(g): {"expected": model[g], "measured": amps[g], "abs_error": abs(amps[g] - model[g])} for g in freqs}
    worst = max(e["abs_error"] for e in errs.values())
    # structural (independent of the LS fit): the strongest host-band line other than the fundamental must sit,
    # by FFT peak search, within one bin of the model's predicted strongest non-fundamental line (fsp ± f family).
    fsp = SP_NUM / SP_DEN
    nfft = 8 * seg.size                      # 8x zero padding: scalloping < 0.03 dB so near-equal lines rank correctly
    spec = np.abs(np.fft.rfft(seg * np.hanning(seg.size), nfft))
    fr = np.fft.rfftfreq(nfft, 1 / fs)
    bin_hz = fs / seg.size                   # resolution of the window (not of the padded grid)
    key_f = round(f, 6)
    others = {g: a for g, a in model.items() if g != key_f}
    predicted_first_image = max(others, key=others.get) if others else None
    mask = (np.abs(fr - f) > 4 * bin_hz) & (fr > 2 * bin_hz) & (fr < fs / 2 - bin_hz)
    peak_f = float(fr[mask][np.argmax(spec[mask])]) if mask.any() else None
    return {
        "input_hz": f, "input_amplitude": amp, "host_rate_hz": fs, "quantizer_bypass_diagnostic": bypass,
        "lines": errs, "n_lines": len(freqs), "worst_abs_error": worst, "bound_abs": bound, "within_bound": bool(worst <= bound),
        "residual_rms_db_re_input": float(20 * np.log10(res / amp)),
        "fft_peak_above_fundamental_hz": peak_f, "predicted_first_image_hz": predicted_first_image, "fft_bin_hz": bin_hz,
        "first_image_position_ok": (peak_f is not None and predicted_first_image is not None and abs(peak_f - predicted_first_image) <= 1.5 * bin_hz),
        "render_record": rec, "latency_host_samples": info.latency_host_samples,
    }


# ------------------------------------------------------------------ VAL-008
def val_008(out_dir: Path, command: str) -> dict:
    rec = _base_record("VAL-008", "REQ-008", command)
    rec["method"] = ("(a) exact rational SP/host ratios vs docs/RATE_GAIN_PLAN.md; (b) quantizer strategies vs their definitions at every code boundary; "
                     "(c) slow ramp through the engine covers all 4096 codes monotonically with clamp; (d) same-build determinism; (e) exact block-partition invariance")
    results: dict = {}
    # (a)
    sp = Fraction(SP_NUM, SP_DEN)
    ratios = {str(h): str(sp / h) for h in RATE_TABLE}
    expected = {str(h): v for h, v in RATE_TABLE.items()}
    results["rate_ratios"] = {"computed": ratios, "expected": expected, "all_exact": ratios == expected, "sp_rate_hz_exact": str(sp)}
    # (b)
    codes = np.arange(-2048, 2048, dtype=np.float64)
    eps = 1e-9
    rb = {}
    for name, rule in QUANTIZER_RULES.items():
        if name == "ROUND_NEAREST":
            below, above = codes - 0.5 - eps, codes - 0.5 + eps
            exp_below, exp_above = codes - 1, codes
        else:  # FLOOR
            below, above = codes - eps, codes + eps
            exp_below, exp_above = codes - 1, codes
        ok = bool(np.array_equal(rule(below), exp_below) and np.array_equal(rule(above), exp_above))
        ties = {"ROUND_NEAREST": "r = c - 0.5 maps to c (ties toward +inf)", "FLOOR": "r = c maps to c"}[name]
        ok_tie = bool(np.array_equal(rule(codes - 0.5), codes)) if name == "ROUND_NEAREST" else bool(np.array_equal(rule(codes), codes))
        rb[name] = {"boundary_definition_exact": ok, "tie_rule": ties, "tie_exact": ok_tie}
    results["quantizer_rule_definitions"] = rb
    # (c)
    cfg, _ = load_research_config()
    fs = 48000
    n = int(0.5 * fs)
    ramp = np.linspace(-1.1, 1.1, n)
    cov = {}
    for name in QUANTIZER_RULES:
        y, info, r, eng = render_offline(ramp, fs, PRODUCT, with_switches(cfg, quantizer_rule=name, diagnostic_taps=True))
        c = eng.tap_codes(0)
        c_mid = c[200:-200]  # exclude transient edges of the low-pass at the record boundaries
        cov[name] = {
            "codes_seen": int(np.unique(c_mid).size), "all_4096": bool(np.unique(c_mid).size == 4096),
            "min_code": int(c_mid.min()), "max_code": int(c_mid.max()),
            "monotone_non_decreasing": bool(np.all(np.diff(c_mid) >= 0)),
            "clip_count": eng.meters()[0]["converter_clip_count"],
            "clamped_at_limits": bool(c_mid.min() == -2048 and c_mid.max() == 2047),
        }
    results["ramp_coverage"] = cov
    # (d)(e)
    x = 0.5 * np.sin(2 * np.pi * 1234.5 * np.arange(20000) / fs) + 0.2 * np.sin(2 * np.pi * 7777.0 * np.arange(20000) / fs)
    det = {}
    for name in QUANTIZER_RULES:
        rc = with_switches(cfg, quantizer_rule=name)
        y1, _, r1, _ = render_offline(x, fs, PRODUCT, rc)
        y2, _, r2, _ = render_offline(x, fs, PRODUCT, rc)
        y3, _, r3, _ = render_offline(x, fs, PRODUCT, rc, block_sizes=[1] * 50 + [7, 64, 1000, 3000])
        det[name] = {"repeat_identical": bool(np.array_equal(y1, y2)), "partition_identical": bool(np.array_equal(y1, y3)),
                     "output_sha256": r1["output_sha256"], "partition_max_abs_diff": float(np.max(np.abs(y1 - y3)))}
    results["determinism_and_partition"] = det
    rec["stimulus"] = {"ramp": "linear -1.1..1.1 over 0.5 s at 48 kHz", "tone_pair": "1234.5 Hz (0.5) + 7777 Hz (0.2), 20000 samples at 48 kHz", "blocks": "[1]*50, 7, 64, 1000, 3000, remainder"}
    rec["tolerance_policy"] = {"rate_ratios": "exact rational equality", "rule_definitions": "exact equality at boundaries ± 1e-9 LSB", "coverage": "exact set/order properties", "determinism/partition": "bit-exact equality (validation domain 2)"}
    rec["results"] = results
    allok = (results["rate_ratios"]["all_exact"] and all(v["boundary_definition_exact"] and v["tie_exact"] for v in rb.values())
             and all(v["all_4096"] and v["monotone_non_decreasing"] and v["clamped_at_limits"] for v in cov.values())
             and all(v["repeat_identical"] and v["partition_identical"] for v in det.values()))
    rec["outcome"] = "PASS" if allok else "FAIL"
    rec["limitations"] = ["Software behaviour only: the exact SP rate (CHAIN-EXP-001) and the historical rounding/offset/encoding rule (CHAIN-EXP-002) remain UNRESOLVED; ROUND_NEAREST is an owner-set provisional software default (OWN-DEC-003)."]
    _write(rec, out_dir / "sp1200" / "digital" / "VAL-008_software.json")
    return rec


# ------------------------------------------------------------------ VAL-009
def val_009(out_dir: Path, command: str) -> dict:
    rec = _base_record("VAL-009", "REQ-009", command)
    rec["method"] = ("R3 = INACTIVE (OWN-DEC-002): no anti-alias attenuation is applied. Structural fold-back check: a 15 kHz and a 14 kHz tone at a 48 kHz host "
                     "must appear in the SP code sequence and the host output at fsp - f (11041.67 / 12041.67 Hz) with the hold response, and the full line model "
                     "(all images aliased into the host band) must match within the kernel-derived bound (quantizer bypass diagnostic). Quantizer-active runs are informational.")
    fs = 48000
    cfg, _ = load_research_config()
    res = {"r3_strategy": "INACTIVE", "aa_response_applied": False, "cases": {}}
    for f in (15000.0, 14000.0):
        case = {"linear": _lines_check(f, 0.5, fs, True), "quantizer_active_informational": _lines_check(f, 0.5, fs, False)}
        # SP-domain check on tap codes (bypass): folded line amplitude in codes
        x = _tone(fs, f, 0.25, 0.5)
        y, info, r, eng = render_offline(x, fs, PRODUCT, with_switches(cfg, quantizer_bypass_diagnostic=True, diagnostic_taps=True))
        codes = eng.tap_codes(0)[500:-500]
        fsp = SP_NUM / SP_DEN
        fold = fsp - f
        amps, resid = fit_components(codes, fsp, [fold])
        h1 = abs(frequency_response(eng.h_lp, f / (fs * info.proxy_oversampling))[0])
        expected = 0.5 * h1 * 2048.0
        case["sp_domain_fold_back"] = {"fold_hz": fold, "expected_codes_amplitude": expected, "measured_codes_amplitude": amps[fold],
                                       "abs_error_codes": abs(amps[fold] - expected), "bound_codes": 2048.0 * 0.5 * info.kernel_properties["line_amplitude_bound_relative"],
                                       "within_bound": bool(abs(amps[fold] - expected) <= 2048.0 * 0.5 * info.kernel_properties["line_amplitude_bound_relative"]),
                                       "residual_rms_codes": resid}
        res["cases"][str(f)] = case
    rec["stimulus"] = {"tones": [15000.0, 14000.0], "amplitude": 0.5, "host_rate_hz": fs, "duration_s": 0.25}
    rec["tolerance_policy"] = {"line_amplitudes": "abs error <= input amplitude x kernel line_amplitude_bound_relative (derived from Kaiser design attenuation + hold-step truncation; see PreparedInfo.kernel_properties)",
                               "first_image_position": "FFT peak (excluding ±4 bins around the fundamental) within 1.5 bins of the model's strongest non-fundamental line", "quantizer_active": "INFORMATIONAL (12-bit quantization distortion products are expected and not bounded here)"}
    rec["results"] = res
    ok = all(c["linear"]["within_bound"] and c["linear"]["first_image_position_ok"] and c["sp_domain_fold_back"]["within_bound"] for c in res["cases"].values())
    rec["outcome"] = "PASS" if ok else "FAIL"
    rec["limitations"] = ["The SP-1200 anti-alias response (RD-P0-01) is not modelled: R3 is INACTIVE and does not represent the hardware; measured fold-back levels of the machine are UNKNOWN. Hardware-fit cell BLOCKED (CHAIN-EXP-002/019)."]
    _write(rec, out_dir / "sp1200" / "input" / "VAL-009_software.json")
    return rec


# ------------------------------------------------------------------ VAL-010
def val_010(out_dir: Path, command: str) -> dict:
    rec = _base_record("VAL-010", "REQ-010", command)
    rec["method"] = ("Route NONE_CH7_8 (identity, VERIFIED no filter) with the provisional full-period hold: tones at a 96 kHz host; joint LS fit of every "
                     "host-band line (fundamental, hold images k*fsp±f, decimation aliases) against amp*|H1(f)|*sinc(g/fsp)*|H16(g)| within the kernel bound; "
                     "hold droop vs the closed-form SP12-CLM-020 table; first image position within an FFT bin of fsp - f; non-populated routes rejected at prepare().")
    fs = 96000
    fsp = SP_NUM / SP_DEN
    cases = {}
    for f in (1000.0, 5000.0, 10000.0, 12000.0):
        cases[str(f)] = {"linear": _lines_check(f, 0.5, fs, True), "quantizer_active_informational": _lines_check(f, 0.5, fs, False)}
    droop_table = {"5000": -0.53, "10000": -2.22, "12000": -3.28}  # research §11 (SIMULATED closed form, 2 decimals)
    droop = {}
    for fk, v in droop_table.items():
        f = float(fk)
        lin = cases[str(f)]["linear"]["lines"][str(round(f, 6))]
        # remove the implementation low-pass responses to compare the hold alone
        cfg, _ = load_research_config()
        _, info, _, eng = render_offline(np.zeros(64), fs, PRODUCT, cfg)
        fp = fs * info.proxy_oversampling
        hh = abs(frequency_response(eng.h_lp, f / fp)[0]) ** 2
        measured_db = 20 * np.log10(lin["measured"] / (0.5 * hh))
        droop[fk] = {"closed_form_db": float(20 * np.log10(zoh_magnitude(f, fsp))), "research_table_db": v, "measured_hold_only_db": float(measured_db),
                     "abs_diff_vs_closed_form_db": float(abs(measured_db - 20 * np.log10(zoh_magnitude(f, fsp)))),
                     "bound_db": float(20 * np.log10(1 + info.kernel_properties["line_amplitude_bound_relative"] / zoh_magnitude(f, fsp)))}
        droop[fk]["within_bound"] = bool(droop[fk]["abs_diff_vs_closed_form_db"] <= droop[fk]["bound_db"])
        droop[fk]["matches_research_table_to_2dp"] = bool(round(droop[fk]["measured_hold_only_db"], 2) == v)
    # routes
    asset, asha = load_asset()
    cfg, rsha = load_research_config()
    routes = {}
    for name in asset["values"]["output_routes"]["value"]:
        p = SPProductParameters(0.0, 0, name, "NORMALIZED_RESEARCH")
        try:
            SPReferenceEngine().prepare(fs, 1, asset, asha, p, cfg, rsha)
            routes[name] = "PREPARED (populated)"
        except InvalidConfiguration as e:
            routes[name] = f"REJECTED {e.code}"
    rec["stimulus"] = {"tones_hz": [1000, 5000, 10000, 12000], "amplitude": 0.5, "host_rate_hz": fs, "duration_s": 0.25}
    rec["tolerance_policy"] = {"line_amplitudes": "abs error <= 0.5 x kernel line_amplitude_bound_relative (design-derived)", "droop": "same bound expressed in dB at each frequency",
                               "image_position": "FFT peak (excluding ±4 bins around the fundamental) within 1.5 bins of the model's strongest non-fundamental line", "quantizer_active": "INFORMATIONAL"}
    rec["results"] = {"route": "NONE_CH7_8 — THE ONLY CURRENTLY POPULATED SOFTWARE-REFERENCE ROUTE; NOT the canonical historical output", "routes_prepare": routes,
                      "hold_fraction": 1.0, "line_checks": cases, "hold_droop": droop}
    ok = (all(c["linear"]["within_bound"] and c["linear"]["first_image_position_ok"] for c in cases.values()) and all(d["within_bound"] for d in droop.values())
          and routes["NONE_CH7_8"].startswith("PREPARED") and all(v.startswith("REJECTED ROUTE_NOT_POPULATED") for k, v in routes.items() if k != "NONE_CH7_8"))
    rec["outcome"] = "PASS" if ok else "FAIL"
    rec["limitations"] = ["Hold fraction, ch 3-4 / 5-6 responses, contact mapping and MIX OUT topology are UNKNOWN (CHAIN-EXP-003/004); images are those of the provisional full-period hold on the provisional clock. Hardware-fit cell BLOCKED."]
    _write(rec, out_dir / "sp1200" / "output" / "VAL-010_software.json")
    return rec


# ------------------------------------------------------------------ VAL-011
def val_011(out_dir: Path, command: str) -> dict:
    rec = _base_record("VAL-011", "REQ-011", command)
    rec["method"] = ("Normalized research calibration only: gain steps 0/+20/+40 dB as exact ratios on a -60 dBFS tone (quantizer bypass, linear identity within float64); "
                     "converter clamp at code limits on a 1.5x full-scale tone with clip meter; physical calibration mode must be rejected (volts UNSET).")
    fs = 48000
    cfg, _ = load_research_config()
    x = _tone(fs, 1000.0, 0.2, 0.001)
    outs = {}
    for g in (0, 20, 40):
        p = SPProductParameters(0.0, g, "NONE_CH7_8", "NORMALIZED_RESEARCH")
        y, info, r, eng = render_offline(x, fs, p, with_switches(cfg, quantizer_bypass_diagnostic=True))
        outs[g] = y[2000:-2000, 0]
    ratios = {}
    for g, expect in ((20, 10.0), (40, 100.0)):
        rel = float(np.max(np.abs(outs[g] - expect * outs[0])) / np.max(np.abs(expect * outs[0])))
        ratios[str(g)] = {"expected_ratio": expect, "max_rel_deviation": rel, "within_float_bound": bool(rel <= FLOAT_REL_BOUND)}
    # trim parameter
    p = SPProductParameters(-6.0, 0, "NONE_CH7_8", "NORMALIZED_RESEARCH")
    y, info, r, eng = render_offline(x, fs, p, with_switches(cfg, quantizer_bypass_diagnostic=True))
    rel = float(np.max(np.abs(y[2000:-2000, 0] - 10 ** (-6 / 20) * outs[0])) / np.max(np.abs(outs[0])))
    ratios["trim_-6dB"] = {"expected_ratio": 10 ** (-6 / 20), "max_rel_deviation": rel, "within_float_bound": bool(rel <= FLOAT_REL_BOUND)}
    # clamp
    xc = _tone(fs, 1000.0, 0.2, 1.5)
    y, info, r, eng = render_offline(xc, fs, PRODUCT, with_switches(cfg, diagnostic_taps=True))
    codes = eng.tap_codes(0)
    clamp = {"max_code": int(codes.max()), "min_code": int(codes.min()), "clip_count": eng.meters()[0]["converter_clip_count"],
             "max_output_abs": float(np.max(np.abs(y))), "dac_full_scale_normalized": 1.0,
             "codes_within_range": bool(codes.max() <= 2047 and codes.min() >= -2048), "clamped": bool(codes.max() == 2047 and codes.min() == -2048 and eng.meters()[0]["converter_clip_count"] > 0)}
    # physical mode
    asset, asha = load_asset()
    cfg2, rsha = load_research_config()
    try:
        SPReferenceEngine().prepare(fs, 1, asset, asha, SPProductParameters(0.0, 0, "NONE_CH7_8", "PHYSICAL"), cfg2, rsha)
        physical = "PREPARED (unexpected)"
    except InvalidConfiguration as e:
        physical = f"REJECTED {e.code}: {e.detail}"
    rec["stimulus"] = {"gain_tone": "1 kHz, 0.001 (-60 dBFS), 0.2 s at 48 kHz", "clamp_tone": "1 kHz, 1.5 x full scale"}
    rec["tolerance_policy"] = {"gain_ratios": f"max relative deviation <= {FLOAT_REL_BOUND} (float64 arithmetic; linear pipeline)", "clamp": "exact code limits and clip meter > 0", "physical": "must raise INVALID_CONFIGURATION"}
    rec["results"] = {"gain_ratios": ratios, "clamp": clamp, "physical_calibration": physical, "analog_clamp": "INACTIVE (no rail model)", "volts_per_normalized_unit": "UNSET", "fidelity": info.fidelity}
    ok = all(v["within_float_bound"] for v in ratios.values()) and clamp["clamped"] and clamp["codes_within_range"] and physical.startswith("REJECTED ASSET_VALUE_UNSET")
    rec["outcome"] = "PASS" if ok else "FAIL"
    rec["limitations"] = ["No volts: input FS, output volts, preamp/AA clip (RD-P0-02, CHAIN-EXP-005) are UNKNOWN; the gain steps are nominal menu values; the converter clamp is presumed. Hardware-fit cell BLOCKED."]
    _write(rec, out_dir / "sp1200" / "calibration" / "VAL-011_software.json")
    return rec


# ------------------------------------------------------------------ VAL-017
def val_017(out_dir: Path, command: str) -> dict:
    rec = _base_record("VAL-017", "REQ-017", command)
    rec["method"] = ("Linked dual mono (PRODUCT ABSTRACTION): L=R gives bit-identical channels; a stereo render equals the two mono renders (independent state); "
                     "a silent channel stays exactly zero; reset() reproduces a fresh engine; the research-only playback slot-skew switch delays channel 1's hold edges by the "
                     "provisional 4.8 µs (a pure delay of the staircase, measured by 1 kHz tone phase; codes/sampling instants shared) and is disabled in the product "
                     "configuration; the separate research capture-offset switch is also disabled.")
    fs = 48000
    cfg, _ = load_research_config()
    n = 24000
    t = np.arange(n) / fs
    a = 0.5 * np.sin(2 * np.pi * 1000.0 * t) + 0.1 * np.sin(2 * np.pi * 6100.0 * t)
    b = 0.4 * np.sin(2 * np.pi * 440.0 * t + 1.0)
    st = np.stack([a, a], axis=1)
    y_eq, _, r_eq, _ = render_offline(st, fs, PRODUCT, cfg)
    y_ab, _, _, _ = render_offline(np.stack([a, b], axis=1), fs, PRODUCT, cfg)
    y_a, _, _, _ = render_offline(a, fs, PRODUCT, cfg)
    y_b, _, _, _ = render_offline(b, fs, PRODUCT, cfg)
    y_minus, _, _, _ = render_offline(np.stack([a, -a], axis=1), fs, PRODUCT, cfg)
    y_ma, _, _, _ = render_offline(-a, fs, PRODUCT, cfg)
    y_lonly, _, _, _ = render_offline(np.stack([a, np.zeros(n)], axis=1), fs, PRODUCT, cfg)
    # reset
    asset, asha = load_asset()
    cfg2, rsha = load_research_config()
    eng = SPReferenceEngine(); eng.prepare(fs, 2, asset, asha, PRODUCT, cfg2, rsha)
    first = np.concatenate([eng.process(st), eng.drain()])
    eng.reset()
    second = np.concatenate([eng.process(st), eng.drain()])
    # slot skew (research only)
    skew_cfg = with_switches(cfg, slot_skew_enabled=True, quantizer_bypass_diagnostic=True)
    y_sk, info_sk, _, _ = render_offline(st, fs, PRODUCT, skew_cfg)
    seg0, seg1 = y_sk[3000:-3000, 0], y_sk[3000:-3000, 1]
    from .measure import fit_components as _fc
    def phase(seg):
        nn = np.arange(seg.size) / fs
        A = np.stack([np.cos(2 * np.pi * 1000 * nn), np.sin(2 * np.pi * 1000 * nn)], axis=1)
        c, *_ = np.linalg.lstsq(A, seg, rcond=None)
        return float(np.arctan2(c[1], c[0]))
    dphi = phase(seg1) - phase(seg0)
    dphi = float(np.angle(np.exp(1j * dphi)))
    # basis [cos, sin], phase = atan2(B, A): x = cos(wt - phi) → A = cos(phi), B = sin(phi); a delay d gives phi = w*d → d = dphi/w
    delay_meas = dphi / (2 * np.pi * 1000.0)
    skew_expected = 4.8e-6
    skew_bound = info_sk.kernel_properties["line_amplitude_bound_relative"] / (2 * np.pi * 1000.0)  # amplitude-bound → phase-bound (small-angle)
    res = {
        "equal_input_identical": bool(np.array_equal(y_eq[:, 0], y_eq[:, 1])),
        "stereo_equals_independent_mono": bool(np.array_equal(y_ab[:, 0], y_a[:, 0]) and np.array_equal(y_ab[:, 1], y_b[:, 0])),
        "anti_phase_equals_mono_of_negated": bool(np.array_equal(y_minus[:, 1], y_ma[:, 0])),
        "silent_channel_exactly_zero": bool(np.all(y_lonly[:, 1] == 0.0)),
        "left_unaffected_by_silent_right": bool(np.array_equal(y_lonly[:, 0], y_a[:, 0])),
        "reset_reproduces_fresh": bool(np.array_equal(first, second)),
        "product_config_slot_skew_enabled": bool(cfg["switches"]["slot_skew_enabled"]),
        "product_config_capture_offset_enabled": bool(cfg["switches"]["capture_offset_enabled"]),
        "research_slot_skew": {"expected_delay_s": skew_expected, "measured_delay_s": delay_meas, "abs_error_s": abs(delay_meas - skew_expected),
                               "bound_s": skew_bound, "within_bound": bool(abs(delay_meas - skew_expected) <= skew_bound),
                               "channels_differ_when_enabled": bool(not np.array_equal(y_sk[:, 0], y_sk[:, 1])),
                               "label": "RESEARCH CONFIGURATION ONLY — DAC multiplex playback skew, arithmetic on the provisional clock (CHAIN-EXP-007 NOT EXECUTED); capture offset is a separate research term (0 here)"},
        "no_random_mismatch": True,
        "output_sha256_equal_input_render": r_eq["output_sha256"],
    }
    rec["stimulus"] = {"a": "1 kHz (0.5) + 6.1 kHz (0.1)", "b": "440 Hz (0.4, phase 1 rad)", "frames": n, "host_rate_hz": fs}
    rec["tolerance_policy"] = {"identity checks": "bit-exact equality", "slot_skew": "|measured - 4.8 µs| <= kernel line_amplitude_bound_relative / (2π·1 kHz) (small-angle phase bound derived from the kernel)"}
    rec["results"] = res
    ok = all(res[k] for k in ("equal_input_identical", "stereo_equals_independent_mono", "anti_phase_equals_mono_of_negated", "silent_channel_exactly_zero",
                              "left_unaffected_by_silent_right", "reset_reproduces_fresh")) and not res["product_config_slot_skew_enabled"] and not res["product_config_capture_offset_enabled"] and res["research_slot_skew"]["within_bound"] and res["research_slot_skew"]["channels_differ_when_enabled"]
    rec["outcome"] = "PASS" if ok else "FAIL"
    rec["limitations"] = ["Linked dual mono is a PRODUCT ABSTRACTION (CHAIN-DEC-005), not a historical stereo path; measured slot skew/hold fraction (CHAIN-EXP-007) NOT EXECUTED. Hardware-fit cell BLOCKED."]
    _write(rec, out_dir / "stereo" / "VAL-017_software.json")
    return rec


def run_all(out_root: str | Path, command: str) -> dict:
    out = Path(out_root)
    results = {}
    for fn in (val_008, val_009, val_010, val_011, val_017):
        r = fn(out, command)
        results[r["check_id"]] = r["outcome"]
    for sub in ("sp1200/digital", "sp1200/input", "sp1200/output", "sp1200/calibration", "stereo"):
        d = out / sub
        write_manifest(d, [p.name for p in d.iterdir() if p.is_file() and p.name != "manifest.sha256"])
    return results
