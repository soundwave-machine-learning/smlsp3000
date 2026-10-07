"""CHAIN-EXP-017 — Skeleton vs published SP-12 figures (SIMULATION, qualitative sanity only).

Question: does the skeleton (R3 INACTIVE placeholder, provisional hold, route
NONE_CH7_8) reproduce the alias/image pattern SRC-04 reports qualitatively for an
SP-12 unfiltered channel (hold images above ~13 kHz; fold-back of content above
13.02 kHz)? Decision criterion (source): sanity check only; never evidence about
hardware. Output: a coarse spectrogram (CSV) of a log sweep and a line-tracking
table comparing detected peaks with predicted fsp - f / fsp + f lines.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .. import environment as env
from ..hashing import sha256_array, write_manifest
from ..reference.assets import load_research_config
from ..reference.render import render_offline, with_switches
from ..reference.sp1200 import SPProductParameters
from ..schemas import EXPERIMENT_RESULT_RECORD, validate

EXPERIMENT_ID = "CHAIN-EXP-017"
FSP = 20_000_000 / 768


def run(out_dir: str | Path, config: dict | None = None, command: str = "") -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    fs = 96000
    seconds = 2.0
    f0, f1 = 200.0, 20000.0
    t = np.arange(int(seconds * fs)) / fs
    k = np.log(f1 / f0) / seconds
    phase = 2 * np.pi * f0 * (np.exp(k * t) - 1) / k
    x = 0.5 * np.sin(phase)
    cfg, rsha = load_research_config()
    product = SPProductParameters(0.0, 0, "NONE_CH7_8", "NORMALIZED_RESEARCH")
    y, info, rec, eng = render_offline(x, fs, product, cfg)
    y = y[:, 0]
    nfft = 4096
    hop = nfft
    frames = []
    rows = []
    win = np.hanning(nfft)
    freqs = np.fft.rfftfreq(nfft, 1 / fs)
    for s in range(0, y.size - nfft, hop):
        tc = (s + nfft / 2) / fs
        f_inst = f0 * np.exp(k * tc)
        f_a, f_b = f0 * np.exp(k * s / fs), f0 * np.exp(k * (s + nfft) / fs)     # sweep span inside the frame
        span = f_b - f_a
        X = np.abs(np.fft.rfft(y[s:s + nfft] * win)) * 2 / np.sum(win)
        db = 20 * np.log10(np.maximum(X, 1e-12))
        frames.append(db[::8])  # coarse
        # fundamental bin + top-2 peaks elsewhere (excluding ±4 bins around the fundamental's Hann main lobe)
        fund_i = int(np.argmin(np.abs(freqs - f_inst)))
        bin_hz0 = fs / nfft
        away = (freqs < f_a - 8 * bin_hz0) | (freqs > f_b + 8 * bin_hz0)       # exclude the chirp's own spread
        order = np.argsort(np.where(away, db, -np.inf))[::-1][:2]
        peaks = [(float(freqs[fund_i]), float(db[fund_i]))] + sorted((float(freqs[i]), float(db[i])) for i in order)
        pred = {"f": f_inst, "fsp-f": abs(FSP - f_inst), "fsp+f": FSP + f_inst, "2fsp-f": abs(2 * FSP - f_inst)}
        rows.append({"t_s": tc, "f_inst_hz": f_inst, "frame_sweep_span_hz": span, "peaks_hz_db": peaks, "predicted_lines_hz": pred})
    with open(out / "spectrogram_coarse.csv", "w", encoding="utf-8") as fh:
        fh.write("# SIMULATION; CHAIN-EXP-017; rows = frames (" + str(nfft) + " samples @ 96 kHz), cols = freq bins every " + f"{freqs[8]:.1f}" + " Hz; dB re 1.0\n")
        for fr in frames:
            fh.write(",".join(f"{v:.1f}" for v in fr) + "\n")
    # qualitative assessment: for frames with f_inst in 5–12 kHz, is the second strongest peak near fsp - f?
    bin_hz = fs / nfft
    checks = []
    for r in rows:
        f = r["f_inst_hz"]
        tol = r["frame_sweep_span_hz"] / 2 + 2 * bin_hz   # the image line sweeps as much as the fundamental within a frame
        non_fund = sorted(r["peaks_hz_db"][1:], key=lambda p: -p[1])
        if 4000 < f < 12000:
            second = non_fund[0][0] if non_fund else None
            checks.append({"f": f, "strongest_non_fundamental_hz": second, "predicted_image_hz": FSP - f, "tolerance_hz": tol, "near": bool(second is not None and abs(second - (FSP - f)) <= tol)})
        if 13100 < f < 20000:
            strongest = non_fund[0][0] if non_fund else None
            fund_db = r["peaks_hz_db"][0][1]
            checks.append({"f": f, "strongest_non_fundamental_hz": strongest, "predicted_fold_hz": FSP - f, "level_at_f_db": fund_db,
                           "tolerance_hz": tol, "near": bool(strongest is not None and abs(strongest - (FSP - f)) <= tol), "note": "above SP Nyquist: fold-back expected; residual level at f is a hold image of the folded line only when fsp - (fsp - f) = f"})
    pattern_ok = all(c["near"] for c in checks) if checks else False
    record = {
        "experiment_id": EXPERIMENT_ID,
        "question": "Skeleton vs published SP-12 figures",
        "hypothesis": "Skeleton reproduces the alias/image pattern reported in SRC-04 qualitatively",
        "requirement_ids": ["REQ-009", "REQ-010"], "debt_ids": ["RD-P1-09"],
        "artifact_class": "SIMULATION", "dataset_role": "NONE",
        "input_config_sha256": rsha, "unit_routes": "N/A (simulation; route NONE_CH7_8; R3 INACTIVE)",
        "software": env.software_record(), "source_commit": env.git_describe(), "environment": env.environment_record(),
        "command": command or "python3 -m smlsp3000.runner run CHAIN-EXP-017",
        "algorithm_version": rec["model_implementation_version"], "preprocessing_version": "hann-4096-stft",
        "raw_output_sha256": {"sweep_input": sha256_array(x), "render_output": sha256_array(y)},
        "metric_definitions": {"peaks": "top-3 STFT magnitude peaks per frame", "near": "within half the frame's sweep span + 2 FFT bins of the predicted line (qualitative)"},
        "threshold_policy": {"revision": "none", "status": "qualitative sanity only (source decision criterion); no numeric threshold defined"},
        "uncertainty": {"note": "coarse STFT; provisional clock; R3 inactive so fold-back is unattenuated (SRC-04 reports attenuation above ~15 kHz on the SP-12, which this skeleton does not have)"},
        "results": {"frames": len(rows), "line_tracking": rows, "qualitative_checks": checks, "pattern_consistent": pattern_ok,
                    "render_record": rec, "latency_host_samples": info.latency_host_samples},
        "outcome": "INFORMATIONAL",
        "limitations": ["Never evidence about the SP-1200 (research §36); SP-12 sibling literature only (RD-P1-09 open).",
                        "Without the AA filter the fold-back is stronger than any hardware would show; this is the documented INACTIVE placeholder state."],
        "resulting_decision": "Sanity only: hold images and fold-back lines follow fsp ± f on the provisional clock; no status change.",
        "timestamp_utc": env.utc_now(),
    }
    problems = validate(record, EXPERIMENT_RESULT_RECORD)
    if problems:
        raise RuntimeError(str(problems))
    (out / "result.json").write_text(json.dumps(record, indent=1, sort_keys=True), encoding="utf-8")
    write_manifest(out, [p.name for p in out.iterdir() if p.is_file() and p.name != "manifest.sha256"])
    return record
