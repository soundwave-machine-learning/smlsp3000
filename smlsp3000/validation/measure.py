"""Measurement helpers for software checks: joint least-squares tone/image amplitude estimation.

For a signal known to consist of a set of sinusoids at given frequencies, a linear
least-squares fit of cos/sin pairs separates every component exactly (no window
leakage between the fitted lines); the residual RMS reports everything else
(quantization error, kernel error, aliasing). Used instead of single-tone
demodulation because hold images sit only a few kHz from the fundamental.
"""
from __future__ import annotations

import numpy as np


def fit_components(y: np.ndarray, fs: float, freqs: list[float]) -> tuple[dict[float, float], float]:
    """Return ({freq: amplitude}, residual_rms) from a joint LS fit of cos/sin at each freq (plus DC)."""
    y = np.asarray(y, dtype=np.float64)
    n = np.arange(y.size, dtype=np.float64) / fs
    cols = [np.ones_like(n)]
    for f in freqs:
        w = 2.0 * np.pi * f * n
        cols.append(np.cos(w)); cols.append(np.sin(w))
    A = np.stack(cols, axis=1)
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    amps = {}
    for i, f in enumerate(freqs):
        c, s = coef[1 + 2 * i], coef[2 + 2 * i]
        amps[f] = float(np.hypot(c, s))
    res = y - A @ coef
    return amps, float(np.sqrt(np.mean(res * res)))


def image_frequencies(f: float, machine_rate: float, limit: float, max_order: int = 40) -> list[float]:
    """f and all k*machine_rate ± f below ``limit`` (hold images / fold-back lines), sorted, unique."""
    out = {f}
    for k in range(1, max_order + 1):
        for g in (k * machine_rate - f, k * machine_rate + f):
            if 0.0 < g < limit:
                out.add(g)
    return sorted(out)


def zoh_magnitude(f: float, machine_rate: float) -> float:
    """|sin(pi f/fs)/(pi f/fs)| — ideal full-period hold (research §11 formula)."""
    x = f / machine_rate
    return float(abs(np.sinc(x)))
