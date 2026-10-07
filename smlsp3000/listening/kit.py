"""CHAIN-EXP-018 software-only listening kit generator (docs/LISTENING_TEST_PLAN.md).

Produces deterministic, RMS-matched, blinded LISTENING STIMULUS files for the conditions supported by the
software track: BYPASS (BOTH_MACHINE_BYPASSED, i.e. the resampling-only path), REFERENCE_B (CASCADE, product
path B), SIMPLIFIED_SP_ONLY and SIMPLIFIED_MPC_ONLY. No hardware condition exists (G-07H BLOCKED); the
protocol reserves the condition slot ``HARDWARE`` so a hardware arm can be added later without redesign.

Material: the repository contains no approved music excerpts, so deterministic synthetic analytic excerpts
(≤ 2.3 s, matching the SP sound-length limit) stand in for the material classes of the listening plan.
This is an explicit coverage limit recorded in the manifest. No listener responses, counts, scores or
criteria are produced; those are external/owner/human.

Audio files are written to the output directory and are NOT committed (repository policy: hashes and
regeneration commands only); the manifest, blinding map, result form and generation record are committed.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .. import environment as env
from ..hashing import sha256_array, sha256_file, write_manifest
from ..reference.cascade import CASCADE_IMPLEMENTATION_VERSION, CascadeProductParameters, CascadeReferenceEngine
from ..reference.mpc3000 import MPCProductParameters
from ..reference.sp1200 import SPProductParameters
from ..stimuli import multitone
from ..wavio import write_wav

KIT_VERSION = "listening-kit-1.0.0"
HOST_RATE = 48000
EXCERPT_SECONDS = 2.2
CONDITIONS = {"BYPASS": "BOTH_MACHINE_BYPASSED", "REFERENCE_B": "CASCADE", "SIMPLIFIED_SP_ONLY": "SP_ONLY", "SIMPLIFIED_MPC_ONLY": "MPC_ONLY"}
RESERVED_CONDITIONS = {"HARDWARE": "G-07H BLOCKED — slot reserved for a future hardware capture arm"}


def _env(t: np.ndarray, t0: float, t1: float, edge: float = 0.01) -> np.ndarray:
    w = np.zeros_like(t)
    m = (t >= t0) & (t < t1); w[m] = 1.0
    up = (t >= t0) & (t < t0 + edge); w[up] = 0.5 - 0.5 * np.cos(np.pi * (t[up] - t0) / edge)
    dn = (t >= t1 - edge) & (t < t1); w[dn] = 0.5 - 0.5 * np.cos(np.pi * (t1 - t[dn]) / edge)
    return w


def synthetic_excerpts(fs: int = HOST_RATE, seconds: float = EXCERPT_SECONDS) -> dict[str, np.ndarray]:
    """Deterministic synthetic stereo excerpts (peak 0.5) standing in for the listening-plan material classes."""
    n = int(seconds * fs); t = np.arange(n) / fs
    out = {}
    # bright: 31-tone log multitone to 18 kHz, decorrelated phases per channel
    tl = multitone(31, 60.0, 18000.0, 101, 0.5); tr = multitone(31, 60.0, 18000.0, 102, 0.5)
    L = sum(tn.amplitude * np.sin(2 * np.pi * tn.freq_hz * t + tn.phase_rad) for tn in tl)
    R = sum(tn.amplitude * np.sin(2 * np.pi * tn.freq_hz * t + tn.phase_rad) for tn in tr)
    out["bright_multitone"] = np.stack([L, R], 1) * _env(t, 0, seconds)[:, None]
    # dense: pink-weighted multitone (amplitude ∝ 1/sqrt(f)), 61 tones, identical L/R (mono-compatible)
    f = np.geomspace(40.0, 16000.0, 61); ph = np.random.default_rng(7).uniform(0, 2 * np.pi, 61)
    a = (1 / np.sqrt(f)); s = sum(ai * np.sin(2 * np.pi * fi * t + pi) for ai, fi, pi in zip(a, f, ph)); s *= 0.5 / np.max(np.abs(s))
    out["dense_pink_multitone"] = np.stack([s, s], 1) * _env(t, 0, seconds)[:, None]
    # transient: seeded exponentially decaying band-limited noise bursts (drum-like envelope), slight L/R difference
    rng = np.random.default_rng(11)
    def bursts(seed):
        r = np.random.default_rng(seed); y = np.zeros(n)
        for k, t0 in enumerate(np.arange(0.05, seconds - 0.3, 0.25)):
            i0 = int(t0 * fs); ln = int(0.18 * fs)
            burst = r.standard_normal(ln) * np.exp(-np.arange(ln) / (0.03 * fs))
            kern = np.ones(4) / 4 if k % 2 else np.ones(1)  # alternate darker/brighter hits
            y[i0:i0 + ln] += np.convolve(burst, kern, mode="same")
        return y
    L = bursts(21); R = 0.8 * L + 0.2 * bursts(22); m = max(np.max(np.abs(L)), np.max(np.abs(R)))
    out["transient_bursts"] = np.stack([L, R], 1) * (0.5 / m)
    # sub-heavy: 45 Hz + 90 Hz + 2.5 kHz click train, quiet tail at the end
    s = 0.6 * np.sin(2 * np.pi * 45 * t) + 0.3 * np.sin(2 * np.pi * 90 * t) + 0.1 * np.sign(np.sin(2 * np.pi * 2500 * t)) * (np.sin(2 * np.pi * 2 * t) > 0.9)
    s = s * (_env(t, 0, seconds * 0.7) + 0.05 * _env(t, seconds * 0.7, seconds)); s *= 0.5 / np.max(np.abs(s))
    out["sub_heavy_quiet_tail"] = np.stack([s, s], 1)
    return out


def generate(out_dir: str | Path, seed: int = 20261007, command: str = "") -> dict:
    out = Path(out_dir); stim_dir = out / "stimuli"; stim_dir.mkdir(parents=True, exist_ok=True)
    sp = SPProductParameters(0.0, 0, "NONE_CH7_8", "NORMALIZED_RESEARCH")
    mpc = MPCProductParameters("LO", 0.0, "MAIN_LR", "NORMALIZED_RESEARCH")
    excerpts = synthetic_excerpts()
    rng = np.random.default_rng(seed)
    entries, blind_map, trials = [], {}, []
    for ex_name, x in excerpts.items():
        src_hash = sha256_array(x)
        renders = {}
        for cond, mode in CONDITIONS.items():
            eng = CascadeReferenceEngine()
            info = eng.prepare(HOST_RATE, 2, CascadeProductParameters(sp, mpc, 0.0, mode))
            y = np.concatenate([eng.process(x), eng.drain()], 0)[info.latency_host_samples:info.latency_host_samples + x.shape[0]]
            renders[cond] = (y, info)
        # RMS match every condition to the BYPASS excerpt RMS (listening-only derivative; logged scalar)
        ref_rms = float(np.sqrt(np.mean(renders["BYPASS"][0] ** 2)))
        for cond, (y, info) in renders.items():
            rms = float(np.sqrt(np.mean(y ** 2))); scalar = ref_rms / rms if rms > 0 else 1.0
            ym = y * scalar
            peak = float(np.max(np.abs(ym)))
            if peak > 0.999:
                raise RuntimeError("level-matched stimulus would clip; adjust excerpt headroom")
            blind = f"stim_{rng.integers(10**6, 10**7)}.wav"
            while blind in blind_map:
                blind = f"stim_{rng.integers(10**6, 10**7)}.wav"
            write_wav(stim_dir / blind, ym, HOST_RATE, 24)
            blind_map[blind] = {"excerpt": ex_name, "condition": cond, "chain_mode": info.chain_mode}
            entries.append({"blind_file": blind, "excerpt": ex_name, "condition": cond, "chain_mode": info.chain_mode, "artifact_class": "LISTENING STIMULUS",
                            "source_excerpt_sha256": src_hash, "render_sha256_before_match": sha256_array(y), "file_sha256": sha256_file(stim_dir / blind),
                            "rms_match_scalar": scalar, "rms_match_scalar_db": float(20 * np.log10(scalar)), "peak_after_match": peak, "rms_after_match": float(np.sqrt(np.mean(ym ** 2))),
                            "latency_host_samples": info.latency_host_samples, "interstage_level_db": 0.0, "sp_asset": info.sp_info["asset_identity"], "mpc_asset": info.mpc_info["asset_identity"]})
        order = list(CONDITIONS); rng.shuffle(order)
        trials.append({"excerpt": ex_name, "presentation_order_blind": [next(b for b, m in blind_map.items() if m["excerpt"] == ex_name and m["condition"] == c) for c in order],
                       "hidden_reference_condition": "REFERENCE_B", "protocol_options": ["ABX (REFERENCE_B vs each candidate, BYPASS anchor)", "MUSHRA-style (all conditions, hidden reference REFERENCE_B)"]})
    # files for the public (blind) side and the keyed side kept separate
    (out / "blind_manifest.json").write_text(json.dumps({"kit_version": KIT_VERSION, "host_rate_hz": HOST_RATE, "bit_depth": 24, "artifact_class": "LISTENING STIMULUS",
        "files": sorted(e["blind_file"] for e in entries), "trials_blind": [{"excerpt_index": i, "presentation_order": t["presentation_order_blind"]} for i, t in enumerate(trials)],
        "note": "blinded presentation; the key is in key_DO_NOT_OPEN_BEFORE_SCORING.json"}, indent=1), encoding="utf-8")
    (out / "key_DO_NOT_OPEN_BEFORE_SCORING.json").write_text(json.dumps({"blind_map": blind_map, "trials": trials, "seed": seed}, indent=1), encoding="utf-8")
    (out / "result_form_template.json").write_text(json.dumps({
        "protocol": "FILL: ABX or MUSHRA-style (one, logged)", "listener_id": "FILL (as permitted)", "playback_chain": "FILL", "level_calibration": "FILL",
        "trials": [{"excerpt_index": i, "responses": [{"blind_file": b, "rating_or_choice": None, "notes": ""} for b in t["presentation_order_blind"]]} for i, t in enumerate(trials)],
        "criterion": "NONE DEFINED IN REPOSITORY EVIDENCE — the owner/validation lead freezes a criterion before scoring; the executor does not invent one",
        "status": "NOT EXECUTED (no human listening has occurred)"}, indent=1), encoding="utf-8")
    record = {
        "experiment_id": "CHAIN-EXP-018", "arm": "SOFTWARE-ONLY (hardware arm G-07H BLOCKED; reserved condition slots: " + json.dumps(RESERVED_CONDITIONS) + ")",
        "status": "PREPARED — NOT EXECUTED (no listener data)", "artifact_class": "LISTENING STIMULUS", "kit_version": KIT_VERSION,
        "cascade_implementation_version": CASCADE_IMPLEMENTATION_VERSION, "conditions": CONDITIONS, "excerpts": {k: {"frames": int(v.shape[0]), "channels": 2, "seconds": EXCERPT_SECONDS, "source_sha256": sha256_array(v), "kind": "SYNTHETIC ANALYTIC (coverage limit: no approved music material in the repository)"} for k, v in excerpts.items()},
        "level_match": "RMS over each excerpt matched to the BYPASS render; scalar logged per file; peaks preserved in metadata; no normalization inside the model",
        "entries": entries, "seed": seed, "command": command or "python3 -m smlsp3000.runner listening-kit --out research/listening/CHAIN-EXP-018",
        "software": env.software_record(), "source_commit": env.git_describe(), "environment": env.environment_record(), "timestamp_utc": env.utc_now(),
        "audio_files_committed": False, "regeneration": "run the command above at the recorded commit; file hashes must match this record",
        "limitations": ["Synthetic material only; SP excerpt limit 2.3 s; software conditions only; no hardware condition; no listener responses; no criterion defined."],
    }
    (out / "generation_record.json").write_text(json.dumps(record, indent=1, sort_keys=True), encoding="utf-8")
    write_manifest(out, ["blind_manifest.json", "key_DO_NOT_OPEN_BEFORE_SCORING.json", "result_form_template.json", "generation_record.json"])
    return record
