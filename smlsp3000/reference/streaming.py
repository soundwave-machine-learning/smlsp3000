"""Block-streaming FIR primitives with exact partition invariance.

Every output sample is a reduction over its own tap window
(``(W * h).sum(axis=1)`` on a sliding-window view), so the floating-point
accumulation order of a given output sample does not depend on how the input
was partitioned into blocks. State is the last ``len(h) - 1`` inputs. No
allocation policy is claimed (reference implementation).
"""
from __future__ import annotations

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

ROW_CHUNK = 4096


def _windowed_dot(buf: np.ndarray, taps_rev: np.ndarray, start: int, count: int, stride: int = 1) -> np.ndarray:
    """y[i] = sum_j buf[start + i*stride + j] * taps_rev[j] for i in range(count)."""
    M = taps_rev.size
    out = np.empty(count, dtype=np.float64)
    if count == 0:
        return out
    W = sliding_window_view(buf, M)[start::stride][:count]
    for s in range(0, count, ROW_CHUNK):
        e = min(count, s + ROW_CHUNK)
        out[s:e] = (W[s:e] * taps_rev).sum(axis=1)
    return out


class StreamingFIR:
    """Causal FIR y[n] = sum_k h[k] x[n-k]."""

    def __init__(self, h: np.ndarray):
        self.h = np.asarray(h, dtype=np.float64)
        self.taps_rev = self.h[::-1].copy()
        self.reset()

    def reset(self):
        self.state = np.zeros(self.h.size - 1, dtype=np.float64)

    def process(self, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=np.float64)
        buf = np.concatenate([self.state, x])
        y = _windowed_dot(buf, self.taps_rev, 0, x.size)
        if self.state.size:
            self.state = buf[-self.state.size:].copy()
        return y


class PolyphaseUpsampler:
    """Integer upsampling by L: zero-stuff then low-pass ``h`` (gain L applied), computed polyphase.

    y[n*L + p] = sum_k hp[k] x[n-k], hp[k] = L * h[k*L + p]. Delay = (len(h)-1)/2 output samples.
    """

    def __init__(self, L: int, h: np.ndarray):
        self.L = int(L)
        self.h = np.asarray(h, dtype=np.float64)
        n_per_phase = int(np.ceil(self.h.size / self.L))
        hp = np.zeros((self.L, n_per_phase), dtype=np.float64)
        for p in range(self.L):
            taps = self.h[p::self.L] * self.L
            hp[p, :taps.size] = taps
        self.phase_taps_rev = hp[:, ::-1].copy()
        self.n_per_phase = n_per_phase
        self.reset()

    def reset(self):
        self.state = np.zeros(self.n_per_phase - 1, dtype=np.float64)

    def process(self, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=np.float64)
        buf = np.concatenate([self.state, x])
        y = np.empty(x.size * self.L, dtype=np.float64)
        for p in range(self.L):
            y[p::self.L] = _windowed_dot(buf, self.phase_taps_rev[p], 0, x.size)
        if self.state.size:
            self.state = buf[-self.state.size:].copy()
        return y


class Decimator:
    """Low-pass ``h`` then keep every L-th sample. Input length must be a multiple of L.

    Output y[m] = sum_k h[k] v[m*L - k] evaluated at the input index m*L (phase 0).
    Delay = (len(h)-1)/2 input samples.
    """

    def __init__(self, L: int, h: np.ndarray):
        self.L = int(L)
        self.h = np.asarray(h, dtype=np.float64)
        self.taps_rev = self.h[::-1].copy()
        self.reset()

    def reset(self):
        self.state = np.zeros(self.h.size - 1, dtype=np.float64)

    def process(self, v: np.ndarray) -> np.ndarray:
        v = np.asarray(v, dtype=np.float64)
        if v.size % self.L:
            raise ValueError("decimator input length must be a multiple of L")
        buf = np.concatenate([self.state, v])
        y = _windowed_dot(buf, self.taps_rev, 0, v.size // self.L, stride=self.L)
        if self.state.size:
            self.state = buf[-self.state.size:].copy()
        return y
