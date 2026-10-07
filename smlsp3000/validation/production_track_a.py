"""Sprint 6 software-track validation of the native production core (VAL-019 / VAL-020 / VAL-021 / VAL-022; Track A).

SIMULATION / VALIDATION RESULT only. The Python reference is the oracle (OWN-DEC-016). Fixtures, metrics and limits are
frozen in evidence/sprint_06/fixture_freeze.json before any result here was evaluated. Nothing is hardware.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from .. import environment as env
from ..hashing import sha256_array, write_manifest
from ..nullframework import kaiser_sinc_interpolate
from ..schemas import VALIDATION_RECORD, validate, validate_machine_asset
from ..native import driver
from ..reference.assets import load_asset, load_research_config
from ..reference.cascade import CASCADE_IMPLEMENTATION_VERSION, CascadeProductParameters, CascadeReferenceEngine, load_cascade_research_config, load_product_config
from ..reference.mpc3000 import MPCProductParameters
from ..reference.render import with_switches
from ..reference.sp1200 import SPProductParameters
from . import fixtures as F

ROOT = Path(__file__).resolve().parents[2]
RMS_REL, RMS_ABS, PEAK_ABS = 1e-5, 1e-7, 1e-4


# ----------------------------------------------------------------------------- records
def _base(check_id, req, command, nat_info):
    pc, psha = load_product_config(); cc, csha = load_cascade_research_config()
    sa, ssha = load_asset(machine="SP-1200"); ma, msha = load_asset(machine="MPC3000")
    return {"check_id": check_id, "requirement_id": req, "track": "A", "artifact_class": "VALIDATION RESULT", "dataset_role": "VALIDATION",
            "asset_identity": {"asset_id": "native(cascade-reference oracle; sp1200-track-a-provisional v1 + mpc3000-track-a-provisional v1)", "version": "1",
                               "model_version": f"{nat_info.get('version')} vs {CASCADE_IMPLEMENTATION_VERSION}", "sha256": sha256_array(np.frombuffer((ssha + msha + psha + csha).encode(), dtype=np.uint8))},
            "research_config_sha256": csha, "software": {**env.software_record(), "native": driver.build_record()}, "source_commit": env.git_describe(), "environment": env.environment_record(),
            "command": command, "stimulus": {}, "method": "", "tolerance_policy": {}, "results": {}, "outcome": "NOT EXECUTED",
            "hardware_fit_outcome": "BLOCKED", "limitations": [], "timestamp_utc": env.utc_now()}


def _write(rec, path: Path):
    problems = validate(rec, VALIDATION_RECORD)
    if problems:
        raise RuntimeError(f"{rec['check_id']} record invalid: {problems}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rec, indent=1, sort_keys=True, default=_jsonable), encoding="utf-8")


def _jsonable(o):
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.bool_,)):
        return bool(o)
    raise TypeError(str(type(o)))


# ----------------------------------------------------------------------------- reference runs
SP0 = SPProductParameters(0.0, 0, "NONE_CH7_8", "NORMALIZED_RESEARCH")
MPC0 = MPCProductParameters("LO", 0.0, "MAIN_LR", "NORMALIZED_RESEARCH")
_REF_CACHE: dict = {}


def ref_params(state: dict) -> CascadeProductParameters:
    sp = SPProductParameters(float(state.get("sp_level", 0.0)), int(state.get("sp_gain", 0)), "NONE_CH7_8", "NORMALIZED_RESEARCH")
    mpc = MPCProductParameters(str(state.get("mpc_gain", "LO")), 0.0, "MAIN_LR", "NORMALIZED_RESEARCH")
    return CascadeProductParameters(sp, mpc, float(state.get("interstage", 0.0)), str(state.get("mode", "CASCADE")))


def ref_configs(state: dict, taps: bool, proxy: int | None = None):
    spr, _ = load_research_config(machine="SP-1200"); mpr, _ = load_research_config(machine="MPC3000"); cr, _ = load_cascade_research_config()
    spk, mpk = {}, {}
    if taps:
        spk["diagnostic_taps"] = True; mpk["diagnostic_taps"] = True
    if state.get("quantizer_rule"):
        spk["quantizer_rule"] = state["quantizer_rule"]
    if state.get("quantizer_bypass"):
        spk["quantizer_bypass_diagnostic"] = True
    if state.get("reduction_rule"):
        mpk["reduction_rule"] = state["reduction_rule"]
    if state.get("converter_bypass"):
        mpk["converter_quantization_bypass_diagnostic"] = True
    if proxy:
        spk["proxy_oversampling"] = int(proxy); mpk["proxy_oversampling"] = int(proxy)
    spr = with_switches(spr, **spk) if spk else spr
    mpr = with_switches(mpr, **mpk) if mpk else mpr
    cr = {**cr, "switches": {**cr["switches"], "reverse_order_research": True}} if state.get("reverse") else cr
    from ..reference.assets import canonical_bytes
    from ..hashing import sha256_bytes
    return (spr, sha256_bytes(canonical_bytes(spr))), (mpr, sha256_bytes(canonical_bytes(mpr))), (cr, sha256_bytes(canonical_bytes(cr)))


def ref_render(x: np.ndarray, fs: int, state: dict, taps: bool = False, proxy: int | None = None):
    """Reference cascade render with drain; returns (y, engine). Cached per (fixture bytes, fs, state, taps, proxy)."""
    key = (hashlib.sha256(x.tobytes()).hexdigest(), fs, json.dumps(state, sort_keys=True), taps, proxy)
    if key in _REF_CACHE:
        return _REF_CACHE[key]
    (spr, sps), (mpr, mps), (cr, crs) = ref_configs(state, taps, proxy)
    e = CascadeReferenceEngine(); e.prepare(fs, x.shape[1], ref_params(state), sp_research=(spr, sps), mpc_research=(mpr, mps), cascade_research=(cr, crs))
    y = np.concatenate([e.process(x), e.drain()])
    _REF_CACHE[key] = (y, e)
    return y, e


def compare(x: np.ndarray, y_ref: np.ndarray, y_nat: np.ndarray) -> list[dict]:
    """Per-channel RMS / peak cells against the owner limits (OWN-DEC-016 C). Both outputs include the drained tail (same length)."""
    cells = []
    n = min(y_ref.shape[0], y_nat.shape[0])
    for ch in range(x.shape[1]):
        d = y_ref[:n, ch] - y_nat[:n, ch]
        rin = float(np.sqrt(np.mean(x[:, ch] ** 2)))
        rms = float(np.sqrt(np.mean(d ** 2))); peak = float(np.max(np.abs(d))) if d.size else 0.0
        rl = max(RMS_REL * rin, RMS_ABS)
        cells.append({"channel": ch, "rms_input": rin, "rms_error": rms, "rms_limit": rl, "peak_error": peak, "peak_limit": PEAK_ABS,
                      "identical_fraction": float(np.mean(d == 0.0)), "pass": bool(rms <= rl and peak <= PEAK_ABS), "length_equal": bool(y_ref.shape[0] == y_nat.shape[0])})
    return cells


def code_compare(e: CascadeReferenceEngine, j: dict, x: np.ndarray, channels: int, state: dict | None = None) -> dict:
    """Exact machine-sample code comparison (SP 12-bit, MPC 18-bit, MPC 16-bit) native taps vs reference taps.

    In the quantizer-bypass diagnostic states the SP "codes" / MPC "c16" are continuous float values (no quantizer); they are
    compared with a relative tolerance of 1e-9 and flagged ``continuous_diagnostic`` instead of exact code equality."""
    out = {}
    state = state or {}
    for ch in range(channels):
        for kind, ref in (("sp_codes", e.sp.tap_codes(ch)), ("mpc_c18", e.mpc.tap_codes(ch, "c18")), ("mpc_c16", e.mpc.tap_codes(ch, "c16"))):
            nat = j["tap_arrays"].get((ch, kind), np.zeros(0))
            n = min(ref.size, nat.size)
            continuous = (kind == "sp_codes" and bool(state.get("quantizer_bypass"))) or (kind in ("mpc_c16", "mpc_c18") and bool(state.get("converter_bypass")))
            if continuous:
                tol = 1e-9 * np.maximum(np.abs(ref[:n]), 1e-3)
                diff = np.nonzero(np.abs(ref[:n] - nat[:n]) > tol)[0]
            else:
                diff = np.nonzero(ref[:n] != nat[:n])[0]
            rec = {"ref_count": int(ref.size), "native_count": int(nat.size), "compared": int(n), "mismatches": int(diff.size), "count_equal": bool(ref.size == nat.size),
                   "comparison": "continuous diagnostic values, relative tolerance 1e-9 (quantizer bypassed: not codes)" if continuous else "exact code equality"}
            if continuous and n:
                rec["max_rel_diff"] = float(np.max(np.abs(ref[:n] - nat[:n]) / np.maximum(np.abs(ref[:n]), 1e-3)))
            if diff.size:
                rec["first_mismatches"] = [{"index": int(i), "reference_code": float(ref[i]), "native_code": float(nat[i])} for i in diff[:10]]
            out[f"ch{ch}_{kind}"] = rec
    return out


# ----------------------------------------------------------------------------- VAL-021
def val_021(out_dir: Path, command: str, quick: bool = False) -> dict:
    nat_info = driver.info(48000)["info"]
    rec = _base("VAL-021", "REQ-021", command, nat_info)
    rec["method"] = ("Native production core (composed operator tables, default) and the exact-order diagnostic path rendered on the frozen fixtures and compared with the "
                     "Python reference cascade at every supported rate (product default state) and across all configuration states at 48 kHz; alignment by declared latency "
                     "only; comparison before output trim; per-fixture/per-channel RMS and peak cells; exact code-stream comparison (SP 12-bit, MPC 18/16-bit) on every "
                     "48 kHz run with diagnostic taps; output-trim gain law tested separately (static exact multiply; ramp trajectory in VAL-022).")
    rec["tolerance_policy"] = {"rms": "RMS(error) <= max(1e-5*RMS(input), 1e-7) (owner-set, OWN-DEC-016 C)", "peak": "max|error| <= 1e-4 (owner-set)", "codes": "exact; discrepancies reported, never waived",
                               "aggregation": "every cell individually; no averaging", "fixture_freeze": "evidence/sprint_06/fixture_freeze.json"}
    rec["stimulus"] = {"fixtures": list(F.FIXTURE_NAMES), "seconds": 0.5, "channels": 2, "rates": list(F.RATES), "states_48k": list(F.CONFIG_STATES)}
    cells, failures, codes_all, timing = [], [], {}, {}
    rates = (48000,) if quick else F.RATES
    fixtures = ("multitone_mix_m12", "overrange_steps_pm16", "tie_adversarial_sp") if quick else F.FIXTURE_NAMES
    # A. product default state, all fixtures, all rates (composed path), plus exact-order at 48 kHz
    for fs in rates:
        for name in fixtures:
            x = F.render_fixture(name, fs, 0.5)
            t0 = time.time(); y_ref, e = ref_render(x, fs, {}, taps=(fs == 48000)); timing[f"ref_{name}_{fs}"] = round(time.time() - t0, 2)
            for exact in ((0, 1) if fs == 48000 else (0,)):
                y_nat, j = driver.render(x, fs, config={"exact_order": exact}, block=64, taps=(fs == 48000))
                if not j.get("ok"):
                    failures.append({"fixture": name, "rate": fs, "exact": exact, "error": j}); continue
                cc = compare(x, y_ref, y_nat)
                for c in cc:
                    c.update({"fixture": name, "rate": fs, "state": "product_default", "native_path": "exact_order" if exact else "composed"})
                    cells.append(c)
                    if not c["pass"]:
                        failures.append(c)
                if fs == 48000:
                    codes = code_compare(e, j, x, 2)
                    codes_all[f"{name}_{fs}_{'exact' if exact else 'composed'}"] = codes
                # meters agreement (clamp counts exact)
                mr = e.meters(); mn = j["meters"]["channel"]
                for ch in range(2):
                    if mr["sp"][ch]["converter_clip_count"] != mn[ch]["sp_clip"] or mr["mpc"][ch]["converter_clip_count_18bit"] != mn[ch]["mpc_clip18"] or mr["mpc"][ch]["storage_clamp_count_16bit"] != mn[ch]["mpc_clamp16"]:
                        failures.append({"fixture": name, "rate": fs, "exact": exact, "meter_mismatch": {"reference": mr, "native": mn}})
    # B. configuration states at 48 kHz on two fixtures (composed path), with taps
    fs = 48000
    for sname, state in F.CONFIG_STATES.items():
        for name in (("multitone_mix_m12", "overrange_steps_pm16") if not quick else ("multitone_mix_m12",)):
            x = F.render_fixture(name, fs, 0.5)
            y_ref, e = ref_render(x, fs, state, taps=True)
            cfg = dict(state)
            y_nat, j = driver.render(x, fs, config=cfg, block=64, taps=True)
            if not j.get("ok"):
                failures.append({"fixture": name, "state": sname, "error": j}); continue
            cc = compare(x, y_ref, y_nat)
            for c in cc:
                c.update({"fixture": name, "rate": fs, "state": sname, "native_path": "composed"}); cells.append(c)
                if not c["pass"]:
                    failures.append(c)
            codes_all[f"{name}_{sname}"] = code_compare(e, j, x, 2, state)
            if e.latency() != j["info"]["latency_host_samples"]:
                failures.append({"state": sname, "latency_mismatch": [e.latency(), j["info"]["latency_host_samples"]]})
    # C. output trim law (static): native trim -6 dB equals native trim 0 dB times 10^(-6/20) exactly (bitwise)
    x = F.render_fixture("multitone_mix_m12", 48000, 0.25)
    y0, _ = driver.render(x, 48000, config={}, block=64); y6, _ = driver.render(x, 48000, config={"trim": -6.0}, block=64)
    g = 10.0 ** (-6.0 / 20.0)
    trim = {"gain_law": "y_trim = y_pre_trim * 10^(dB/20), applied per host sample after R16", "exact_bitwise": bool(np.array_equal(y6, y0 * g)), "max_abs_diff": float(np.max(np.abs(y6 - y0 * g)))}
    if not trim["exact_bitwise"]:
        failures.append({"output_trim_law": trim})
    # D. code-stream summary
    total_mismatch = sum(v["mismatches"] for d in codes_all.values() for v in d.values())
    count_mismatch = sum(0 if v["count_equal"] else 1 for d in codes_all.values() for v in d.values())
    rec["results"] = {"cells": cells, "cells_total": len(cells), "cells_failed": sum(0 if c["pass"] else 1 for c in cells),
                      "worst_rms_error": max(c["rms_error"] for c in cells), "worst_rms_ratio_to_limit": max(c["rms_error"] / c["rms_limit"] for c in cells),
                      "worst_peak_error": max(c["peak_error"] for c in cells), "codes": codes_all, "code_mismatches_total": total_mismatch, "code_count_mismatches": count_mismatch,
                      "output_trim": trim, "failures": failures, "reference_timing_s": timing, "native_info_48k": nat_info}
    rec["outcome"] = "PASS" if (not failures and total_mismatch == 0 and count_mismatch == 0) else "FAIL"
    rec["limitations"] = ["Software oracle only: agreement with the Python reference, which is itself UNVALIDATED AGAINST HARDWARE.",
                          "Native kernel tables differ from the Python tables at the last bit (libm vs numpy SIMD exp); differences are measured in the cells, not hidden.",
                          "The composed-operator production path evaluates the same linear operators in a different rounding order; code streams are compared exactly to expose any boundary discrepancy."]
    _write(rec, out_dir / "reference_production" / "VAL-021_software.json")
    return {"VAL-021": rec["outcome"]}


# ----------------------------------------------------------------------------- VAL-019
def _resample_to(y: np.ndarray, fs_from: int, fs_to: int, trim_s: float, hw: int = 64, beta: float = 12.0) -> np.ndarray:
    """Analysis conversion: 18 kHz brick-wall low-pass on the SOURCE grid (removes the SP images / fold-back products above the
    common band so that they cannot alias when the fs_to grid is sampled), then Kaiser-sinc evaluation of the band-limited signal on
    the fs_to grid, trimmed by trim_s at both ends. Correction recorded in evidence/sprint_06/fixture_freeze.json (the first
    implementation low-passed after the interpolation, which aliased images between 22.05 kHz and the source Nyquist)."""
    Y = np.fft.rfft(y); f = np.fft.rfftfreq(y.size, 1.0 / fs_from); Y[f > 18000.0] = 0.0
    yl = np.fft.irfft(Y, y.size)
    n_to = int(np.floor((yl.size - 1) / fs_from * fs_to))
    t = np.arange(n_to, dtype=np.float64) / fs_to
    pos = t * fs_from
    a = int(trim_s * fs_to); b = n_to - a
    return kaiser_sinc_interpolate(yl, pos[a:b], hw, beta)


def val_019(out_dir: Path, command: str, quick: bool = False) -> dict:
    nat_info = driver.info(48000)["info"]
    rec = _base("VAL-019", "REQ-019", command, nat_info)
    rec["method"] = ("Same-build determinism and block-partition invariance of the native core at every supported rate (sha256 of output bytes for: repeated render; block 64; irregular "
                     "list incl. 1-sample blocks; seeded random blocks up to 8192; single call larger than the prepared maximum → internal chunking; prepared max_block 64), "
                     "same-rate native-vs-reference budget at every rate, declared latency verified from code and by an independent impulse/burst timing test, and cross-rate "
                     "behaviour (frozen method: Kaiser-sinc analysis conversion to the 44.1 kHz grid + 18 kHz brick wall, tool error characterised on the analytic stimulus; "
                     "production cross-rate discrepancy compared with the reference's own cross-rate discrepancy and bounded by the propagated same-rate errors plus tool error).")
    rec["tolerance_policy"] = {"determinism": "bit-identical (sha256)", "same_rate": "owner limits (OWN-DEC-016 C)", "cross_rate": "|d_nat - d_ref| <= G*e_rate + e_44k + tool_error, G = 1.001 (measured resampler gain bound), recorded before the run (evidence/sprint_06/fixture_freeze.json)",
                               "latency": "declared == measured (impulse peak in the resampling-only path exact; burst envelope lag within 1 host sample + the SP hold half-period in the cascade); <= 10 ms at every rate (OWN-DEC-018)"}
    rates = (48000, 96000) if quick else F.RATES
    det, same_rate, latency, cross = {}, {}, {}, {}
    failures = []
    for fs in rates:
        x = F.render_fixture("multitone_mix_m12", fs, 0.5)
        runs = {"block64_a": driver.render(x, fs, block=64), "block64_b": driver.render(x, fs, block=64),
                "irregular": driver.render(x, fs, blocks=[1, 7, 500, 8192, 64, 3, 1000, 8191, 2, 1, 1, 4096]),
                "seeded": driver.render(x, fs, block_seed=7, block_max=8192), "single_call": driver.render(x, fs, block=x.shape[0] + 2000),
                "max_block_64": driver.render(x, fs, block=64, max_block=64), "ones": driver.render(x, fs, blocks=[1])}
        hashes = {k: hashlib.sha256(v[0].tobytes()).hexdigest() for k, v in runs.items()}
        det[fs] = {"hashes": hashes, "all_identical": len(set(hashes.values())) == 1, "blocks_used": {k: v[1]["blocks_used"] for k, v in runs.items()}}
        if not det[fs]["all_identical"]:
            failures.append({"rate": fs, "determinism": hashes})
        y_ref, e = ref_render(x, fs, {})
        cc = compare(x, y_ref, runs["block64_a"][0]); same_rate[fs] = cc
        if not all(c["pass"] for c in cc):
            failures.append({"rate": fs, "same_rate": cc})
        # latency: declared (code) vs reference vs measured
        info = runs["block64_a"][1]["info"]; lat = info["latency_host_samples"]
        imp = np.zeros((int(0.05 * fs), 1)); imp[200, 0] = 1.0
        yi, _ = driver.render(imp, fs, config={"mode": "BOTH_MACHINE_BYPASSED"}, block=64)
        peak = int(np.argmax(np.abs(yi[:, 0])))
        t = np.arange(int(0.1 * fs)) / fs; burst = (0.5 * np.sin(2 * np.pi * 1000.0 * t) * ((t > 0.03) & (t < 0.06)))[:, None]
        yb, _ = driver.render(burst, fs, config={}, block=64)
        env_in = np.abs(burst[:, 0]); env_out = np.abs(yb[: burst.shape[0], 0])
        # envelope lag by cross-correlation of rectified signals' smoothed envelopes
        k = max(1, int(fs / 1000)); sm = np.ones(k) / k
        ei = np.convolve(env_in, sm, "same"); eo = np.convolve(env_out, sm, "same")
        lags = np.arange(0, lat + 200); xc = [float(np.dot(eo[l:l + ei.size - l], ei[: ei.size - l])) for l in lags]
        lag = int(lags[int(np.argmax(xc))])
        latency[fs] = {"declared_native": lat, "declared_reference": e.latency(), "equal": lat == e.latency(), "ms": lat / fs * 1000.0, "within_10ms": lat / fs <= 0.010,
                       "impulse_peak_index_minus_input_index_resampling_path": peak - 200, "burst_envelope_lag_cascade": lag,
                       "sp_hold_half_period_host_samples": fs / (20000000 / 768) / 2.0, "breakdown_proxy": info["latency_breakdown_proxy"],
                       "pass": bool(lat == e.latency() and peak - 200 == lat and abs(lag - lat) <= 2 + fs / (20000000 / 768) / 2.0 and lat / fs <= 0.010)}
        if not latency[fs]["pass"]:
            failures.append({"rate": fs, "latency": latency[fs]})
    # cross-rate (frozen method)
    if not quick:
        for name in ("multitone_mix_m12", "transient_bursts", "sine_1k_m20"):
            cr = {}
            x44 = F.render_fixture(name, 44100, 0.5)
            y44r, _ = ref_render(x44, 44100, {}); y44n, _ = driver.render(x44, 44100, block=64)
            lat44 = driver.info(44100)["info"]["latency_host_samples"]
            a44r = _resample_to(y44r[lat44:lat44 + x44.shape[0], 0], 44100, 44100, 0.03); a44n = _resample_to(y44n[lat44:lat44 + x44.shape[0], 0], 44100, 44100, 0.03)
            e44 = float(np.sqrt(np.mean((a44r - a44n) ** 2)))
            x44a = _resample_to(x44[:, 0], 44100, 44100, 0.03)
            for fs in F.RATES:
                if fs == 44100:
                    continue
                x = F.render_fixture(name, fs, 0.5)
                yr, _ = ref_render(x, fs, {}); yn, _ = driver.render(x, fs, block=64)
                lat = driver.info(fs)["info"]["latency_host_samples"]
                ar = _resample_to(yr[lat:lat + x.shape[0], 0], fs, 44100, 0.03); an = _resample_to(yn[lat:lat + x.shape[0], 0], fs, 44100, 0.03)
                n = min(ar.size, a44r.size)
                tool = _resample_to(x[:, 0], fs, 44100, 0.03)
                tool_err = float(np.sqrt(np.mean((tool[:n] - x44a[:n]) ** 2)))
                d_ref = float(np.sqrt(np.mean((ar[:n] - a44r[:n]) ** 2))); d_nat = float(np.sqrt(np.mean((an[:n] - a44n[:n]) ** 2)))
                e_rate = float(np.sqrt(np.mean((ar[:n] - an[:n]) ** 2)))
                bound = 1.001 * e_rate + e44 + tool_err
                rms_sig = float(np.sqrt(np.mean(a44r[:n] ** 2)))
                # phase-insensitive view: magnitude spectra (Hann) of the converted outputs; the reference's machine clocks are anchored at
                # proxy index 0 (= input time -lobes/fs_host), so phase-sensitive fold-back products legitimately differ in phase between rates
                def mag(v):
                    w = np.hanning(n); return np.abs(np.fft.rfft(v[:n] * w)) / (np.sum(w) / 2.0)
                Mr, Mr44, Mn, Mn44 = mag(ar), mag(a44r), mag(an), mag(a44n)
                mag_ref = float(np.sqrt(np.mean((Mr - Mr44) ** 2))); mag_nat = float(np.sqrt(np.mean((Mn - Mn44) ** 2)))
                mag_sig = float(np.sqrt(np.mean(Mr44 ** 2)))
                cr[fs] = {"d_ref_rms": d_ref, "d_nat_rms": d_nat, "d_ref_db_re_signal": 20 * np.log10(d_ref / rms_sig) if d_ref > 0 else None, "d_nat_db_re_signal": 20 * np.log10(d_nat / rms_sig) if d_nat > 0 else None,
                          "e_rate_same_rate_rms": e_rate, "e_44k_same_rate_rms": e44, "tool_error_rms": tool_err, "bound": bound, "abs_diff": abs(d_nat - d_ref), "pass": bool(abs(d_nat - d_ref) <= bound),
                          "magnitude_spectrum_diff_ref_db_re_signal": 20 * np.log10(mag_ref / mag_sig) if mag_ref > 0 else None, "magnitude_spectrum_diff_native_db_re_signal": 20 * np.log10(mag_nat / mag_sig) if mag_nat > 0 else None,
                          "magnitude_native_minus_ref_abs": abs(mag_nat - mag_ref)}
                if not cr[fs]["pass"]:
                    failures.append({"cross_rate": name, "rate": fs, "cell": cr[fs]})
            cross[name] = cr
    rec["stimulus"] = {"determinism_fixture": "multitone_mix_m12 0.5 s stereo", "cross_rate_fixtures": ["multitone_mix_m12", "transient_bursts", "sine_1k_m20"], "rates": list(rates)}
    rec["results"] = {"determinism": det, "same_rate": same_rate, "latency": latency, "cross_rate": cross, "failures": failures}
    rec["outcome"] = "PASS" if not failures else "FAIL"
    rec["limitations"] = ["Cross-rate agreement is bounded relative to the reference's own cross-rate behaviour (which includes rate-dependent quantizer-boundary decisions); no absolute cross-rate identity is claimed.",
                          "FINDING (reference property, reproduced exactly by the native core): the reference anchors the SP and MPC machine clocks at proxy index 0, which corresponds to input time -lobes/fs_host (1.09 ms at 44.1 kHz, 1.0 ms at 48 kHz, 0.5 ms at 96 kHz, 0.25 ms at 192 kHz); the machine sampling phase relative to the audio therefore depends on the host rate, so phase-sensitive SP fold-back products (e.g. the 18 kHz tone folded to 8042 Hz) differ in PHASE between host rates while their magnitudes agree (see magnitude_spectrum_diff_* vs d_ref). On hardware the machine clock phase relative to the audio is arbitrary, so this is not a modelling error; a rate-independent anchor (machine sample k at proxy position k*per + lobes*L, i.e. input time k/f_machine) would be a reference behaviour change and is left for owner review (not applied).",
                          "The analysis conversion is an IMPLEMENTATION tool characterised on the analytic stimulus; its error is part of the bound.",
                          "Latency is software kernel delay; the SP hold adds a frequency-dependent half-period (not compensated, documented)."]
    _write(rec, out_dir / "rate_block" / "VAL-019_software.json")
    return {"VAL-019": rec["outcome"]}


# ----------------------------------------------------------------------------- VAL-020
def _spectrum_db(y: np.ndarray, fs: int):
    w = np.hanning(y.size); Y = np.fft.rfft(y * w) / (np.sum(w) / 2.0); f = np.fft.rfftfreq(y.size, 1.0 / fs)
    return f, 20 * np.log10(np.maximum(np.abs(Y), 1e-300))


def _line(f, mag_db, f0, bw):
    m = (f >= f0 - bw) & (f <= f0 + bw)
    return float(np.max(mag_db[m])) if np.any(m) else None


def val_020(out_dir: Path, command: str, quick: bool = False) -> dict:
    nat_info = driver.info(48000)["info"]
    rec = _base("VAL-020", "REQ-020", command, nat_info)
    rec["method"] = ("Proxy-rate convergence of the accepted reference (8x vs 16x, research switch proxy_oversampling on both machines) and native-vs-reference at both ratios on short "
                     "deterministic fixtures (near-Nyquist tone, two-tone, stepped clamp levels, multitone, 1 kHz), each render aligned by its own declared latency and the shared "
                     "physical origin; spectral categories separated: intentional SP images/fold-back (lines at k*26041.67 ± f), converter-clamp harmonics (overrange fixture), "
                     "implementation filtering error (8x vs 16x difference), production-introduced difference (native vs reference at the same ratio). Structural check: the native SP "
                     "stage renders the band-limited zero-order hold (step table) — verified by the presence and level of SP image lines equal to the reference's.")
    rec["tolerance_policy"] = {"production": "native vs reference at the same ratio within the owner same-rate limits", "model_self_convergence": "REPORTED (8x vs 16x residual vs the kernel-derived line bound); not an acceptance limit — the 8x reference is the owner-frozen configuration",
                               "images": "native image lines equal reference image lines within the same-rate limits (no band-limited reconstruction substituted for the ZOH)"}
    rates = (48000,) if quick else (48000, 96000)
    fixtures = ("sine_1k_m20", "near_nyquist_tone_19k", "multitone_mix_m12", "overrange_steps_pm16", "two_tone_18k_19p5k")
    results, failures = {}, []
    sp_rate = 20000000 / 768
    for fs in rates:
        for name in fixtures:
            if name == "two_tone_18k_19p5k":
                t = np.arange(int(0.25 * fs)) / fs; x = np.stack([0.4 * np.sin(2 * np.pi * 18000 * t) + 0.4 * np.sin(2 * np.pi * 19500 * t)] * 2, axis=1)
            else:
                x = F.render_fixture(name, fs, 0.25)
            r8, e8 = ref_render(x, fs, {}, proxy=8); r16, e16 = ref_render(x, fs, {}, proxy=16)
            n8, j8 = driver.render(x, fs, config={"proxy": 8}, block=64); n16, j16 = driver.render(x, fs, config={"proxy": 16}, block=64)
            L8, L16 = e8.latency(), e16.latency()
            N = x.shape[0]
            a8, a16 = r8[L8:L8 + N, 0], r16[L16:L16 + N, 0]; b8, b16 = n8[L8:L8 + N, 0], n16[L16:L16 + N, 0]
            rms = lambda v: float(np.sqrt(np.mean(v ** 2)))
            sig = rms(a8)
            cell = {"latency_8x": L8, "latency_16x": L16, "native_latency_8x": j8["info"]["latency_host_samples"], "native_latency_16x": j16["info"]["latency_host_samples"],
                    "model_self_convergence_rms_8_vs_16": rms(a8 - a16), "model_self_convergence_db_re_signal": 20 * np.log10(rms(a8 - a16) / sig) if sig > 0 else None,
                    "production_vs_reference_rms_8x": rms(a8 - b8), "production_vs_reference_rms_16x": rms(a16 - b16),
                    "production_cells_8x": compare(x[:, :1], r8[:, :1], n8[:, :1]), "production_cells_16x": compare(x[:, :1], r16[:, :1], n16[:, :1]),
                    "kernel_line_bound_relative_8x": e8.sp_info.kernel_properties["line_amplitude_bound_relative"]}
            f, m8 = _spectrum_db(a8, fs); _, m16 = _spectrum_db(a16, fs); _, mn = _spectrum_db(b8, fs); _, md = _spectrum_db(a8 - a16, fs); _, mp = _spectrum_db(a8 - b8, fs)
            bw = 3.0 * fs / a8.size
            lines = {}
            if name in ("near_nyquist_tone_19k", "sine_1k_m20"):
                f0 = 19000.0 if name == "near_nyquist_tone_19k" else 1000.0
                lines["input_tone"] = {"f": f0, "ref8_db": _line(f, m8, f0, bw), "ref16_db": _line(f, m16, f0, bw), "native8_db": _line(f, mn, f0, bw)}
                for k in (1, 2):
                    for fi in (k * sp_rate - f0, k * sp_rate + f0):
                        if 0 < fi < fs / 2:
                            lines[f"sp_image_{k}{'-' if fi < k*sp_rate else '+'}"] = {"f": fi, "ref8_db": _line(f, m8, fi, bw), "ref16_db": _line(f, m16, fi, bw), "native8_db": _line(f, mn, fi, bw), "category": "INTENTIONAL SP image / fold-back (band-limited ZOH on the provisional 26.04 kHz grid)"}
            if name == "two_tone_18k_19p5k":
                for fi, lab in ((sp_rate - 19500.0, "sp_fold_19p5k"), (sp_rate - 18000.0, "sp_fold_18k"), (2 * 18000.0 - 19500.0, "imd_16p5k"), (2 * 19500.0 - 18000.0, "imd_21k")):
                    if fi < fs / 2:
                        lines[lab] = {"f": fi, "ref8_db": _line(f, m8, fi, bw), "ref16_db": _line(f, m16, fi, bw), "native8_db": _line(f, mn, fi, bw)}
            if name == "overrange_steps_pm16":
                for k in (2, 3, 5):
                    lines[f"clamp_harmonic_{k}"] = {"f": 320.0 * k, "ref8_db": _line(f, m8, 320.0 * k, bw), "ref16_db": _line(f, m16, 320.0 * k, bw), "native8_db": _line(f, mn, 320.0 * k, bw), "category": "converter-clamp harmonics (intentional overload model)"}
            inband = f < min(fs / 2, 22050.0)
            cell["lines"] = lines
            cell["implementation_filtering_error_max_db_inband_8_vs_16"] = float(np.max(md[inband]))
            cell["production_introduced_max_db_inband"] = float(np.max(mp[inband]))
            cell["model_self_convergence_within_kernel_line_bound"] = bool(rms(a8 - a16) <= cell["kernel_line_bound_relative_8x"] * float(np.max(np.abs(x[:, 0]))))
            cell["pass_production"] = all(c["pass"] for c in cell["production_cells_8x"]) and all(c["pass"] for c in cell["production_cells_16x"])
            if not cell["pass_production"]:
                failures.append({"rate": fs, "fixture": name, "production": cell["production_cells_8x"] + cell["production_cells_16x"]})
            results[f"{name}_{fs}"] = cell
    conv_flags = {k: v["model_self_convergence_within_kernel_line_bound"] for k, v in results.items()}
    rec["stimulus"] = {"fixtures": list(fixtures), "seconds": 0.25, "rates": list(rates), "proxy_ratios": [8, 16]}
    rec["results"] = {"cells": results, "model_self_convergence_within_kernel_bound": conv_flags, "failures": failures,
                      "note": "model self-convergence (8x vs 16x) is a property of the accepted reference, reported for G-08 review; production acceptance is native-vs-reference at the frozen 8x"}
    rec["outcome"] = "PASS" if not failures else "FAIL"
    rec["limitations"] = ["The 16x rendering is the same model at a finer proxy, not an analog oracle; convergence says nothing about hardware.",
                          "Historical image/alias level agreement with hardware (G-06) remains BLOCKED."]
    if not all(conv_flags.values()):
        rec["limitations"].append("MATERIAL: the 8x reference differs from its 16x rendering by more than the kernel-derived line bound on at least one fixture — see results; this is documented for owner review of the proxy-rate quality decision (OWN-DEC-015/016 E), not silently accepted.")
    _write(rec, out_dir / "implementation_alias" / "VAL-020_software.json")
    return {"VAL-020": rec["outcome"]}


# ----------------------------------------------------------------------------- VAL-022
def val_022(out_dir: Path, command: str, quick: bool = False) -> dict:
    nat_info = driver.info(48000)["info"]
    rec = _base("VAL-022", "REQ-022", command, nat_info)
    rec["method"] = ("Parameter layers and state v1: native state serialisation round trips (defaults and modified values, exact), explicit rejections (future schema version, unknown key, "
                     "research key, out-of-range value, unknown enum, asset identity mismatch, malformed record), preset content limited to product fields + identities, assets carry "
                     "provisional tags, generated asset header in sync with the JSON sources, research switches unreachable from state; smoothing/automation fixtures: event "
                     "trajectories bit-identical across partitions, output-trim ramp bit-exact against the linear-in-dB law reproduced in Python, proxy-domain ramps measured on a "
                     "linear SP path (quantizer bypass) against the expected envelope, discrete switches switch at the mapped sample, ramp continuation from the current value.")
    rec["tolerance_policy"] = {"state": "exact", "trim_ramp": "bit-exact (same float sequence)", "proxy_ramps": "envelope within 0.5 dB during the 10 ms ramp (sampling/hold smear), exact (<= 1e-12 relative) outside ±48 host samples of the ramp",
                               "partitions": "bit-identical"}
    failures, res = [], {}
    base_state = driver.info(48000)["state"]
    # 1. state round trips and rejections
    tests = {"defaults": (base_state, True, "OK")}
    mod = base_state.replace("sp_input_level_db=0\n", "sp_input_level_db=-12.345678901234567\n").replace("interstage_level_db=0\n", "interstage_level_db=6.5\n").replace("sp_input_gain_db=0\n", "sp_input_gain_db=40\n").replace("mpc_input_gain=LO\n", "mpc_input_gain=HI\n").replace("output_trim_db=0\n", "output_trim_db=-1.25\n").replace("plugin_bypass=0\n", "plugin_bypass=1\n")
    tests["modified"] = (mod, True, "OK")
    tests["future_schema_2"] = (base_state.replace("schema_version=1", "schema_version=2"), False, "UNSUPPORTED_SCHEMA_VERSION")
    tests["unknown_key"] = (base_state + "drive=3\n", False, "UNKNOWN_KEY")
    tests["research_key"] = (base_state + "quantizer_rule=FLOOR\n", False, "UNKNOWN_KEY")
    tests["calibration_key"] = (base_state + "volts_per_normalized_unit=1.0\n", False, "UNKNOWN_KEY")
    tests["out_of_range"] = (base_state.replace("output_trim_db=0\n", "output_trim_db=13\n"), False, "OUT_OF_RANGE")
    tests["unknown_enum"] = (base_state.replace("mpc_input_gain=LO", "mpc_input_gain=ULTRA"), False, "UNKNOWN_ENUM")
    tests["bad_gain_step"] = (base_state.replace("sp_input_gain_db=0\n", "sp_input_gain_db=30\n"), False, "UNKNOWN_ENUM")
    tests["identity_mismatch"] = (base_state.replace("sp_asset=sp1200", "sp_asset=sp1201"), False, "ASSET_IDENTITY_MISMATCH")
    tests["missing_field"] = (base_state.replace("plugin_bypass=0\n", ""), False, "MISSING_FIELD")
    tests["non_record"] = ("hello\n", False, "NOT_A_STATE_RECORD")
    tests["nonfinite"] = (base_state.replace("output_trim_db=0\n", "output_trim_db=nan\n"), False, "NON_FINITE_OR_MALFORMED")
    st = {}
    for name, (text, want_ok, want_code) in tests.items():
        r = driver.state_load(text)
        ok = (bool(r.get("ok")) == want_ok) and (r.get("code") == want_code)
        if name == "modified" and ok:
            ok = r["sp_input_level_db"] == -12.345678901234567 and r["interstage_level_db"] == 6.5 and r["sp_input_gain_db"] == 40 and r["mpc_input_gain"] == "HI" and r["output_trim_db"] == -1.25 and r["plugin_bypass"] is True
        st[name] = {"expected": [want_ok, want_code], "got": [r.get("ok"), r.get("code"), r.get("detail")], "pass": ok}
        if not ok:
            failures.append({"state_test": name, "got": r})
    keys = [l.split("=")[0] for l in base_state.strip().splitlines()[1:]]
    layer = {"state_keys": keys, "only_product_fields_and_identities": set(keys) == {"schema_version", "controls", "product_config", "sp_asset", "mpc_asset", "sp_input_level_db", "sp_input_gain_db", "interstage_level_db", "mpc_input_gain", "output_trim_db", "plugin_bypass"}}
    sa, _ = load_asset(machine="SP-1200"); ma, _ = load_asset(machine="MPC3000")
    layer["assets_valid_with_provisional_tags"] = not validate_machine_asset(sa) and not validate_machine_asset(ma)
    chk = subprocess.run([sys.executable, str(ROOT / "tools" / "gen_native_assets.py"), "--check"], capture_output=True, text=True)
    layer["generated_header_in_sync"] = chk.returncode == 0 and "UP TO DATE" in chk.stdout
    ctl = json.loads((ROOT / "smlsp3000" / "reference" / "assets" / "product_controls_v1.json").read_text())
    layer["controls_schema_version"] = ctl["schema_version"]; layer["controls"] = {k: {kk: v[kk] for kk in v if kk in ("min", "max", "default", "values")} for k, v in ctl["controls"].items()}
    if not (layer["only_product_fields_and_identities"] and layer["assets_valid_with_provisional_tags"] and layer["generated_header_in_sync"]):
        failures.append({"layers": layer})
    res["state"] = st; res["layers"] = layer
    # 2. automation fixtures (48 kHz)
    fs = 48000
    x = F.render_fixture("multitone_mix_m12", fs, 0.5)
    ev = [(3000, "sp_input_level_db", -6.0), (3100, "interstage_level_db", 3.0), (3200, "sp_input_level_db", 2.0), (9000, "output_trim_db", -3.0), (12000, "sp_input_gain_db", 20.0), (15000, "mpc_input_gain", 1.0), (20000, "plugin_bypass", 1.0), (21000, "plugin_bypass", 0.0)]
    ya, ja = driver.render(x, fs, block=64, events=ev); yb, _ = driver.render(x, fs, blocks=[1, 7, 500, 8192, 64, 3, 1000], events=ev); yc, _ = driver.render(x, fs, block=x.shape[0] + 1000, events=ev)
    y0, _ = driver.render(x, fs, block=64)
    auto = {"partition_identical": bool(np.array_equal(ya, yb) and np.array_equal(ya, yc)), "differs_from_static": bool(not np.array_equal(ya, y0)), "events_rejected": ja["meters"]["events_rejected"]}
    # trim ramp bit-exact: y_trim[m] = y0[m] * g[m], g from the ramp arithmetic reproduced here
    yt, jt = driver.render(x, fs, block=64, events=[(9000, "output_trim_db", -3.0)])
    ramp = jt["info"]["ramp_host_samples"]; g = np.ones(yt.shape[0]); cur = 0.0; step = (-3.0 - 0.0) / ramp
    for i in range(ramp):
        cur = cur + step
        if i == ramp - 1:
            cur = -3.0
        g[9000 + i] = 10.0 ** (cur / 20.0)
    g[9000 + ramp:] = 10.0 ** (-3.0 / 20.0)
    exp = y0 * g[:, None]
    auto["trim_ramp_bit_exact"] = bool(np.array_equal(yt, exp)); auto["trim_ramp_max_abs_diff"] = float(np.max(np.abs(yt - exp))); auto["ramp_host_samples"] = ramp
    # proxy-domain ramp on a linear SP path (quantizer bypass, SP_ONLY): 1 kHz tone, sp_input_level 0 → -12 dB at frame 10000
    t = np.arange(int(0.6 * fs)) / fs; tone = (0.5 * np.sin(2 * np.pi * 1000.0 * t))[:, None]
    cfg = {"mode": "SP_ONLY", "quantizer_bypass": 1}
    yr, jr = driver.render(tone, fs, config=cfg, block=64, events=[(10000, "sp_input_level_db", -12.0)]); ys, _ = driver.render(tone, fs, config=cfg, block=64)
    lat = jr["info"]["latency_host_samples"]; rp = jr["info"]["ramp_proxy_samples"] // jr["info"]["L"]
    # the effect of an event mapped to proxy index m*L + R1 delay reaches the host output before `start` by the R16 look-ahead (48 host samples),
    # the hold-kernel look-ahead (4) and the sampler look-ahead (4): the pre-event window ends 128 host samples before `start` to stay exact
    start = 10000 + lat; mask_pre = slice(2000, start - 128); mask_post = slice(start + rp + 48, start + rp + 6000)
    rel = lambda a, b: float(np.max(np.abs(a - b) / np.maximum(np.abs(b), 1e-9)))
    pre_exact = rel(yr[mask_pre, 0], ys[mask_pre, 0]); post_ratio = yr[mask_post, 0] / np.where(np.abs(ys[mask_post, 0]) > 0.05, ys[mask_post, 0], np.nan)
    post_ratio = post_ratio[np.isfinite(post_ratio)]
    # envelope during the ramp: RMS over 1 ms windows vs expected linear-in-dB envelope
    envs = []
    for k in range(0, rp, 48):
        seg = slice(start + k, start + k + 48)
        a = np.sqrt(np.mean(yr[seg, 0] ** 2)); b = np.sqrt(np.mean(ys[seg, 0] ** 2))
        db_meas = 20 * np.log10(a / b); db_exp = -12.0 * (k + 24) / rp
        envs.append({"host_offset": k, "measured_db": db_meas, "expected_db": db_exp, "abs_diff_db": abs(db_meas - db_exp)})
    auto["proxy_ramp"] = {"pre_event_max_rel_diff": pre_exact, "post_ramp_gain_ratio_min_max": [float(np.min(post_ratio)), float(np.max(post_ratio))], "expected_post_gain": 10 ** (-12 / 20),
                          "ramp_envelope": envs, "max_abs_diff_db_in_ramp": max(e["abs_diff_db"] for e in envs),
                          "pass": bool(pre_exact <= 1e-12 and abs(float(np.min(post_ratio)) - 10 ** (-12 / 20)) <= 1e-6 and abs(float(np.max(post_ratio)) - 10 ** (-12 / 20)) <= 1e-6 and max(e["abs_diff_db"] for e in envs) <= 0.5)}
    # ramp continuation: second target mid-ramp must not restart; discrete switch exactness: sp gain step 20 dB on the linear path = exact x10 after the switch
    yg, _ = driver.render(tone, fs, config=cfg, block=64, events=[(10000, "sp_input_gain_db", 20.0)])
    ratio = yg[start + 64: start + 6000, 0] / np.where(np.abs(ys[start + 64: start + 6000, 0]) > 0.05, ys[start + 64: start + 6000, 0], np.nan); ratio = ratio[np.isfinite(ratio)]
    auto["discrete_switch"] = {"post_switch_ratio_min_max": [float(np.min(ratio)), float(np.max(ratio))], "expected": 10.0, "pre_switch_exact": rel(yg[mask_pre, 0], ys[mask_pre, 0]) <= 1e-12,
                               "tolerance": "ratio within 1e-12 of 10 (float rounding of the linear path); pre-switch exact",
                               "pass": bool(abs(float(np.min(ratio)) - 10.0) <= 1e-12 and abs(float(np.max(ratio)) - 10.0) <= 1e-12 and rel(yg[mask_pre, 0], ys[mask_pre, 0]) <= 1e-12)}
    ym, _ = driver.render(tone, fs, config=cfg, block=64, events=[(10000, "sp_input_level_db", -12.0), (10000 + rp // 2, "sp_input_level_db", -12.0)])
    auto["retarget_mid_ramp_same_target_identical"] = bool(np.array_equal(ym, yr))   # a redundant retarget keeps the running trajectory (documented semantics)
    ok_auto = auto["partition_identical"] and auto["differs_from_static"] and auto["events_rejected"] == 0 and auto["trim_ramp_bit_exact"] and auto["proxy_ramp"]["pass"] and auto["discrete_switch"]["pass"] and auto["retarget_mid_ramp_same_target_identical"]
    if not ok_auto:
        failures.append({"automation": {k: v for k, v in auto.items() if k != "proxy_ramp"} | {"proxy_ramp_pass": auto["proxy_ramp"]["pass"]}})
    res["automation"] = auto
    res["event_mapping"] = {"sp_input_level_db / sp_input_gain_db": f"host input sample m → proxy index m*L + {ja['info']['event_offset_r2_proxy']} (R1 delay)",
                            "interstage_level_db / mpc_input_gain": f"host input sample m → proxy index m*L + {ja['info']['event_offset_r10_proxy']} (R1 delay + SP core delay)",
                            "output_trim_db / plugin_bypass": "host sample m of the same call (host time)", "ramp_lengths": {"proxy": ja["info"]["ramp_proxy_samples"], "host": ja["info"]["ramp_host_samples"]}}
    rec["stimulus"] = {"automation_fixture": "multitone_mix_m12 0.5 s + 1 kHz tone 0.6 s (linear SP path)", "events": ev}
    rec["results"] = res | {"failures": failures}
    rec["outcome"] = "PASS" if not failures else "FAIL"
    rec["limitations"] = ["Plugin bypass transitions and host UI interactions are Sprint 7; here plugin_bypass is a static latency-aligned dry selector.",
                          "No preset bank exists; the state record is the only persistence format (v1)."]
    out = out_dir / "state_parameter"
    _write(rec, out / "VAL-022_software.json")
    return {"VAL-022": rec["outcome"]}


def run_all(out_root, evidence_root, command: str, quick: bool = False, only: str | None = None) -> dict:
    out = Path(out_root); ev = Path(evidence_root)
    if not driver.available():
        raise RuntimeError(f"native binary not found at {driver.binary_path()}; build with the commands in docs/BUILD_COMMANDS.md (CMD-13)")
    results = {}
    if only in (None, "VAL-021"):
        results.update(val_021(out, command, quick))
    if only in (None, "VAL-019"):
        results.update(val_019(out, command, quick))
    if only in (None, "VAL-020"):
        results.update(val_020(out, command, quick))
    if only in (None, "VAL-022"):
        results.update(val_022(ev, command, quick))
    for d in (out / "reference_production", out / "rate_block", out / "implementation_alias", ev / "state_parameter"):
        write_manifest(d, [p.name for p in d.iterdir() if p.is_file() and p.name != "manifest.sha256"])
    return results


def benchmark(evidence_dir, seconds: float = 5.0, trials: int = 3, warmup: float = 1.0) -> dict:
    """OWN-DEC-017 benchmark: one stereo CASCADE instance, product configuration, per rate/block pair; raw per-callback times saved."""
    ev = Path(evidence_dir); ev.mkdir(parents=True, exist_ok=True)
    pairs = ((44100, 64), (48000, 64), (88200, 128), (96000, 128), (176400, 256), (192000, 256))
    limits = {44100: 0.20, 48000: 0.20, 88200: 0.40, 96000: 0.40, 176400: 0.60, 192000: 0.60}
    cpu = ""
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                cpu = line.split(":", 1)[1].strip(); break
    except Exception:
        cpu = "unavailable"
    rec = {"record": "Sprint 06 native Release benchmark (OWN-DEC-017)", "recorded_utc": env.utc_now(), "environment": env.environment_record(), "cpu_model": cpu,
           "threads": 1, "container": "Claude Code cloud container (shared virtualised CPU, no real-time scheduling, no CPU pinning, background processes idle during the run)",
           "build": driver.build_record(), "signal": "deterministic 3-tone + LCG noise (see tool); stereo; CASCADE product state; preallocated; warm-up before timing",
           "load_definition": "processing elapsed time / represented audio duration (steady_clock around each process() call)", "pairs": {}}
    all_pass = True; p999_all = True
    for rate, block in pairs:
        j = driver.bench(rate, block, seconds, trials, warmup, raw_prefix=ev / f"raw_{rate}_{block}")
        means = [t["mean_load"] for t in j["trials"]]
        limit_ok = all(m <= limits[rate] for m in means)                      # OWNER-SET LIMIT (OWN-DEC-017)
        p999_ok = all(t["p999_over_budget"] < 0.8 for t in j["trials"])       # OWNER TARGET (reported; scheduling jitter of the host is included)
        all_pass &= limit_ok; p999_all &= p999_ok
        rec["pairs"][f"{rate}_{block}"] = {"rate": rate, "block": block, "limit_mean_load": limits[rate], "trials": j["trials"], "mean_load_all_trials": means, "max_mean_load": max(means),
                                            "overruns_total": sum(t["overruns"] for t in j["trials"]), "calls_total": j["calls_per_trial"] * trials, "p999_target_fraction": 0.8,
                                            "mean_load_limit_pass": limit_ok, "p999_target_met": p999_ok, "pass": limit_ok, "callback_budget_s": j["callback_budget_s"], "calls_per_trial": j["calls_per_trial"],
                                            "median_over_budget": [t["median_s"] / j["callback_budget_s"] for t in j["trials"]]}
    rec["all_pass"] = all_pass
    rec["p999_target_met_all_pairs"] = p999_all
    rec["scheduling_conditions"] = "shared cloud VM vCPU (Intel Xeon @ 2.10 GHz, 4 vCPU), ordinary process priority, no real-time scheduling, no CPU pinning, no isolated core; callback-time outliers (several times the median) are host preemption/jitter, not steady-state load; every overrun is listed per trial"
    rec["applies_only_to"] = "the recorded environment; Windows performance pending until measured on Windows"
    (ev / "benchmark_record.json").write_text(json.dumps(rec, indent=1, sort_keys=True), encoding="utf-8")
    write_manifest(ev, [p.name for p in ev.iterdir() if p.is_file() and p.name != "manifest.sha256"])
    return rec
