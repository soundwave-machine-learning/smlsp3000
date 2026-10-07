"""Numerical kernels shared by the reference blocks (IMPLEMENTATION, not machine behaviour).

* ``kaiser_sinc_lowpass`` — odd-length windowed-sinc low-pass, DC gain 1 within DC_GAIN_BOUND (float64).
* ``kaiser_window_fn`` / ``windowed_sinc_taps`` — fractional interpolation taps.
* ``BandlimitedStepTable`` — S(d) = ∫_{-∞}^{d} w(x)·sinc(x) dx, the response of an
  ideal band-limited acquisition (cutoff = Nyquist of the grid) to a unit step at
  fractional offset d. Used by the zero-order-hold block to render the
  continuous-time staircase band-limited to the proxy Nyquist instead of
  sampling hard edges (which would alias). It keeps every image below the
  proxy Nyquist; it is not a reconstruction filter of either machine.

All kernels are parameterised by the research configuration and their numeric
properties (truncation residual, passband deviation) are reported, so that any
tolerance used in a software check is derived from the kernel, not invented.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

#: |sum(h) - 1| bound after normalisation (float64; 4 ulp of 1.0). Documented numeric contract, not a tuning.
DC_GAIN_BOUND = 4.0 * np.finfo(np.float64).eps


def kaiser_window_fn(d: np.ndarray, half_width: float, beta: float) -> np.ndarray:
    arg = np.clip(1.0 - (d / half_width) ** 2, 0.0, 1.0)
    return np.i0(beta * np.sqrt(arg)) / np.i0(beta)


def exact_sinc(d: np.ndarray) -> np.ndarray:
    """np.sinc with exact 1/0 at integer arguments (np.sinc(n) is ~1e-16, not 0)."""
    s = np.sinc(d)
    integer = d == np.round(d)
    return np.where(integer, np.where(d == 0.0, 1.0, 0.0), s)


def kaiser_sinc_lowpass(num_taps: int, cutoff: float, beta: float) -> np.ndarray:
    """Windowed-sinc low-pass; ``cutoff`` in cycles/sample (0 < cutoff < 0.5); odd ``num_taps``; |sum(h) - 1| <= DC_GAIN_BOUND."""
    if num_taps % 2 == 0:
        raise ValueError("num_taps must be odd")
    m = (num_taps - 1) // 2
    n = np.arange(-m, m + 1, dtype=np.float64)
    h = 2.0 * cutoff * exact_sinc(2.0 * cutoff * n) * kaiser_window_fn(n, m + 1, beta)
    h = h / np.sum(h)
    # fold the float64 normalisation residual into the centre tap (two passes); |sum(h) - 1| <= DC_GAIN_BOUND afterwards
    for _ in range(2):
        h[m] -= (np.sum(h) - 1.0)
    if abs(float(np.sum(h)) - 1.0) > DC_GAIN_BOUND:
        raise ArithmeticError("low-pass DC gain not within float64 bound")
    return h


def frequency_response(h: np.ndarray, f_cycles_per_sample: np.ndarray | float) -> np.ndarray:
    """Complex response of a linear-phase FIR (centre tap = zero delay) at the given frequencies."""
    f = np.atleast_1d(np.asarray(f_cycles_per_sample, dtype=np.float64))
    m = (h.size - 1) // 2
    n = np.arange(-m, m + 1, dtype=np.float64)
    return np.array([np.sum(h * np.exp(-2j * np.pi * fi * n)) for fi in f])


def windowed_sinc_taps(frac: np.ndarray, half_width: int, beta: float) -> tuple[np.ndarray, np.ndarray]:
    """Taps for evaluating a band-limited interpolant at base+frac. Returns (k, taps[len(frac), 2*half_width])."""
    k = np.arange(-half_width + 1, half_width + 1, dtype=np.float64)
    d = k[None, :] - np.asarray(frac, dtype=np.float64)[:, None]
    return k, exact_sinc(d) * kaiser_window_fn(d, half_width, beta)


@dataclass
class BandlimitedStepTable:
    """Tabulated S(d) for |d| <= half_width at resolution 1/res; S(d<-hw)=0, S(d>=hw)=1.

    Built by cumulative trapezoidal integration of the windowed sinc over a fine
    grid; the table is normalised so S(+hw) == 1 exactly (the truncation residual
    before normalisation is reported as ``truncation_residual``).
    """

    half_width: int
    beta: float
    res: int = 1024

    def __post_init__(self):
        hw = self.half_width
        x = np.arange(-hw * self.res, hw * self.res + 1, dtype=np.float64) / self.res
        w = exact_sinc(x) * kaiser_window_fn(x, hw, self.beta)
        cum = np.concatenate([[0.0], np.cumsum(0.5 * (w[1:] + w[:-1]) / self.res)])
        self.truncation_residual = float(abs(cum[-1] - 1.0))
        self.table = cum / cum[-1]
        self.x0 = -hw

    def __call__(self, d: np.ndarray) -> np.ndarray:
        d = np.asarray(d, dtype=np.float64)
        out = np.where(d >= self.half_width, 1.0, 0.0)
        inside = (d > -self.half_width) & (d < self.half_width)
        pos = (d[inside] - self.x0) * self.res
        i = np.floor(pos).astype(np.int64)
        f = pos - i
        i = np.clip(i, 0, self.table.size - 2)
        out[inside] = self.table[i] * (1.0 - f) + self.table[i + 1] * f
        return out
