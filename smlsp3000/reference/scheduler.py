"""Exact rational machine clock on a proxy grid (docs/ARCHITECTURE.md “Scheduler and stereo state”).

The machine rate is a rational ``num/den`` Hz (SP: 20 000 000/768, PROVISIONAL)
and the proxy rate an integer. Machine sample k occurs at continuous time
t_k = k·den/num seconds, i.e. at proxy position p_k = k·den·f_proxy/num, kept as
an exact ``Fraction``. Positions never drift and never depend on block
boundaries; conversion to float happens only at the interpolation step.
"""
from __future__ import annotations

from fractions import Fraction


class RationalClock:
    def __init__(self, rate_num: int, rate_den: int, proxy_rate_hz: int,
                 capture_offset_seconds: Fraction = Fraction(0), hold_offset_seconds: Fraction = Fraction(0)):
        self.rate = Fraction(int(rate_num), int(rate_den))
        self.proxy_rate = int(proxy_rate_hz)
        self.period_proxy = Fraction(self.proxy_rate) / self.rate     # proxy samples per machine sample
        # research-only offsets (docs/ARCHITECTURE.md: "source capture offset and DAC multiplex playback
        # skew are separate terms"): sampling instants use capture_offset, hold edges use hold_offset.
        self.capture_offset_proxy = Fraction(capture_offset_seconds) * self.proxy_rate
        self.hold_offset_proxy = Fraction(hold_offset_seconds) * self.proxy_rate
        if self.hold_offset_proxy < self.capture_offset_proxy:
            raise ValueError("hold offset must be >= capture offset (causality of the hold)")
        self.reset()

    def reset(self):
        self.next_k = 0  # next machine sample index not yet produced

    def position(self, k: int) -> Fraction:
        """Sampling instant of machine sample k (proxy position)."""
        return k * self.period_proxy + self.capture_offset_proxy

    def hold_position(self, k: int) -> Fraction:
        """Instant at which the hold output switches to code k (playback edge)."""
        return k * self.period_proxy + self.hold_offset_proxy

    def take_samples_up_to(self, max_position: Fraction) -> list[tuple[int, Fraction]]:
        """Return (k, position) for every not-yet-produced sample with position <= max_position; advances next_k."""
        out = []
        while True:
            pos = self.position(self.next_k)
            if pos > max_position:
                break
            out.append((self.next_k, pos))
            self.next_k += 1
        return out

    def latest_samples_at(self, proxy_positions) -> "np.ndarray":
        """Vectorised latest_sample_at for integer proxy positions (exact integer arithmetic, int64)."""
        import numpy as np
        t = np.asarray(proxy_positions, dtype=np.int64)
        per = self.period_proxy
        off = self.hold_offset_proxy
        # k = floor((t - off) / per) = floor(((t*off.den - off.num) * per.den) / (off.den * per.num))
        num = (t * int(off.denominator) - int(off.numerator)) * int(per.denominator)
        den = int(off.denominator) * int(per.numerator)
        if t.size and (abs(num).max() > 2**62 // 4):
            raise OverflowError("scheduler position arithmetic exceeds int64 range")
        return np.floor_divide(num, den).astype(np.int64)

    def latest_sample_at(self, proxy_position: Fraction) -> int:
        """Largest k whose hold edge hold_position(k) <= proxy_position (may be -1 before the first sample)."""
        q = (Fraction(proxy_position) - self.hold_offset_proxy) / self.period_proxy
        k = q.numerator // q.denominator
        return int(k)
