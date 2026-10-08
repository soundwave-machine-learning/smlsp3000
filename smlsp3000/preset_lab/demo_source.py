"""Deterministic synthetic 'demo beat' for Preset Lab screenshots and tests (NOT a musical reference; the owner auditions real beats).

A fixed 8-second pattern at the requested rate: a decaying-pitch kick, a noise+tone snare, closed hats, a sub-bass line and
a short sampled-style chord stab. Peak ≈ −3 dBFS. Everything is analytic and seeded, so the file is regenerable and hashed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from .. import wavio

SECONDS = 8.0
BPM = 92.0


def _env(t: np.ndarray, t0: float, decay: float) -> np.ndarray:
    tt = t - t0
    return np.where(tt >= 0.0, np.exp(-tt / decay), 0.0)


def render_demo_beat(rate: int, seconds: float = SECONDS, seed: int = 20261008) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = int(round(rate * seconds)); t = np.arange(n) / rate
    beat = 60.0 / BPM; step = beat / 4.0
    y = np.zeros((n, 2))
    noise = rng.standard_normal(n)
    hat_noise = np.convolve(noise, np.array([1.0, -1.0, 0.5, -0.25]), mode="same")   # crude bright noise (no claim; stimulus only)
    for k in range(int(seconds / step)):
        t0 = k * step
        if k % 4 == 0:                                                         # kick on every beat
            e = _env(t, t0, 0.18); ph = 2 * np.pi * (45.0 * (t - t0) + 80.0 * 0.03 * (1 - np.exp(-(t - t0) / 0.03)) / 0.03 * (t - t0 >= 0))
            kick = 0.9 * e * np.sin(2 * np.pi * (45.0 + 110.0 * np.exp(-(t - t0) / 0.025)) * np.clip(t - t0, 0, None) * 0 + ph)
            y[:, 0] += kick; y[:, 1] += kick
        if k % 8 == 4:                                                         # snare on 2 and 4
            e = _env(t, t0, 0.12); sn = e * (0.35 * noise + 0.4 * np.sin(2 * np.pi * 185.0 * (t - t0)))
            y[:, 0] += 0.9 * sn; y[:, 1] += 1.0 * sn
        if k % 2 == 0:                                                         # closed hats on eighths
            e = _env(t, t0, 0.025); h = 0.12 * e * hat_noise
            y[:, 0] += 1.0 * h; y[:, 1] += 0.8 * h
        if k % 16 in (0, 6, 10):                                               # sub-bass line
            e = _env(t, t0, 0.35); f = {0: 41.2, 6: 49.0, 10: 36.7}[k % 16]
            b = 0.45 * e * np.sin(2 * np.pi * f * (t - t0)) * (t >= t0)
            y[:, 0] += b; y[:, 1] += b
        if k % 16 == 8:                                                        # chord stab (upper harmonics, decorrelated L/R)
            e = _env(t, t0, 0.4)
            for i, f in enumerate((261.6, 311.1, 392.0, 466.2)):
                y[:, 0] += 0.09 * e * np.sin(2 * np.pi * f * (t - t0) + 0.3 * i) * (t >= t0)
                y[:, 1] += 0.09 * e * np.sin(2 * np.pi * f * 1.002 * (t - t0) + 0.9 * i) * (t >= t0)
    peak = float(np.max(np.abs(y)))
    y *= 10 ** (-3.0 / 20.0) / peak
    return y


def write_demo_source(out_dir: Path, rate: int = 48000, record: bool = True) -> dict:
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    y = render_demo_beat(rate)
    wav = out_dir / f"demo_beat_{rate}.wav"
    wavio.write_wav(wav, y, rate, bit_depth=24)
    rec = {"record": "smlsp3000-preset-lab-demo-source", "schema": 1, "file": wav.name, "rate": rate, "seconds": SECONDS, "bpm": BPM,
           "generator": "smlsp3000.preset_lab.demo_source.render_demo_beat (seed 20261008)", "wav_sha256": hashlib.sha256(wav.read_bytes()).hexdigest(),
           "samples_sha256": hashlib.sha256(np.ascontiguousarray(y, dtype=np.float64).tobytes()).hexdigest(), "peak_dbfs": -3.0,
           "note": "synthetic stimulus for tool demonstration and tests only; not a musical reference; the owner auditions real beats", "regenerate": f"python3 -m smlsp3000.runner preset-lab-demo-source --out {out_dir} --rate {rate}"}
    if record:
        (out_dir / f"demo_beat_{rate}.json").write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")
    return rec
