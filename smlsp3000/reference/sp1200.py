"""SP-1200 reference blocks R2–R9 and the linked dual-mono engine (Track A, provisional).

Signal flow per channel (docs/ENGINE_SPEC.md candidate reference flow):

    host x[m] ─R1→ proxy v[n] ─R2→ gain ─R3→ (INACTIVE) ─R4→ sample at p_k ─R5→ code c_k
    ─R6→ identity ─R7→ band-limited zero-order hold on the proxy grid ─R8→ route (NONE_CH7_8 = identity)
    ─R9→ output gain (normalized) ─R16→ host y[m]

Equations (normalized research calibration, 1.0 = converter full scale):

* R1  v = upsample_L(x) with a windowed-sinc low-pass at the host Nyquist (gain L).
* R2  v2 = g_step · g_trim · v, g_step ∈ {1, 10, 100} (0/+20/+40 dB), g_trim = 10^(sp_input_level_db/20).
* R3  v3 = v2 (INACTIVE strategy; owner decision OWN-DEC-002).
* R4  s_k = Σ_j v3[⌊p_k⌋ + j] · w(j − frac(p_k)), p_k = k · f_proxy · den/num (exact Fraction).
* R5  c_k = clamp(rule(s_k · 2048 + offset), −2048, 2047); rule ∈ {ROUND_NEAREST: ⌊r + ½⌋, FLOOR: ⌊r⌋}.
* R6  identity at unity pitch.
* R7  h[n] = c_{k(n)}/2048 + Σ_{edges e near n} Δc_e/2048 · (S(n − q_e) − u(n − q_e)),
      q_e = hold edge of code e (= p_e unless the research playback slot skew is enabled),
      k(n) = max{k : q_k ≤ n}; S = band-limited unit step of the proxy grid; this is the
      continuous-time staircase band-limited to the proxy Nyquist (no hard-edge aliasing).
* R8  identity for NONE_CH7_8; every other route is NOT POPULATED → INVALID_CONFIGURATION.
* R9  y9 = g_out · h (coupling pole INACTIVE).
* R16 y = decimate_L(y9) with the same windowed-sinc low-pass.

Implementation delay (exact, integer host samples) = 2·lobes + sampler_hw + hold_hw.
Linked dual mono: all channels share the clock (sample instants) and the asset;
each channel owns its own filter/sampler/hold state. Nothing bleeds.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from fractions import Fraction

import numpy as np

from ..schemas import UNSET
from .assets import asset_identity, asset_value
from .errors import InvalidConfiguration
from .kernels import BandlimitedStepTable, TapTable, kaiser_sinc_lowpass
from .scheduler import RationalClock
from .streaming import Decimator, PolyphaseUpsampler

SUPPORTED_HOST_RATES = (44100, 48000, 88200, 96000, 176400, 192000)
MODEL_IMPLEMENTATION_VERSION = "sp1200-reference-impl-1.0.3"

# --- R5 quantizer strategies (replaceable registry) -------------------------------------

def _rule_round_nearest(r: np.ndarray) -> np.ndarray:
    """⌊r + 0.5⌋ : nearest code, ties toward +∞. OWNER-SET PROVISIONAL SOFTWARE DEFAULT (OWN-DEC-003)."""
    return np.floor(r + 0.5)


def _rule_floor(r: np.ndarray) -> np.ndarray:
    """⌊r⌋ : SAR-style 'largest code not exceeding the input' hypothesis (research §8). Research alternate."""
    return np.floor(r)


QUANTIZER_RULES = {"ROUND_NEAREST": _rule_round_nearest, "FLOOR": _rule_floor}

# --- R3 strategies (replaceable registry) -----------------------------------------------

class R3Inactive:
    """Anti-alias block placeholder: identity. Does NOT represent the hardware (OWN-DEC-002)."""
    name = "INACTIVE"

    def reset(self):
        pass

    def process(self, v: np.ndarray) -> np.ndarray:
        return v


R3_STRATEGIES = {"INACTIVE": R3Inactive}
R3_RESERVED_SLOTS = ("LITERATURE_DERIVED_LOWPASS", "MEASURED_RESPONSE")  # names reserved, not populated

# --- R8 routes (replaceable registry) ---------------------------------------------------

class RouteIdentity:
    name = "NONE_CH7_8"

    def reset(self):
        pass

    def process(self, h: np.ndarray) -> np.ndarray:
        return h


R8_ROUTES = {"NONE_CH7_8": RouteIdentity}


@dataclass(frozen=True)
class SPProductParameters:
    """ProductParameters subset relevant to the SP stage (docs/PARAMETERS.md candidate IDs). No defaults."""
    sp_input_level_db: float
    sp_input_gain: int          # 0 / 20 / 40
    sp_output_path: str         # NONE_CH7_8 / FIXED_CH5_6 / FIXED_CH3_4 / MIX_OUT
    calibration_mode: str       # "NORMALIZED_RESEARCH" | "PHYSICAL"


@dataclass
class PreparedInfo:
    host_rate_hz: int
    proxy_rate_hz: int
    proxy_oversampling: int
    sp_rate: str
    sp_over_host_ratio: str
    latency_host_samples: int
    latency_breakdown_proxy_samples: dict
    hold_group_delay_descriptor: str
    kernel_properties: dict
    asset_identity: dict
    research_config_sha256: str
    quantizer_rule: str
    r3_strategy: str
    route: str
    fidelity: str

    def to_dict(self) -> dict:
        return asdict(self)


class _ChannelState:
    def __init__(self, engine: "SPReferenceEngine", channel_index: int):
        e = engine
        self.hw_s_pad = e.hw_s
        self.up = PolyphaseUpsampler(e.L, e.h_lp)
        self.r3 = e.r3_factory()
        self.route = e.route_factory()
        self.down = Decimator(e.L, e.h_lp)
        cap = e.capture_offset_seconds * channel_index if e.capture_offset_enabled else Fraction(0)
        skew = e.slot_skew_seconds * channel_index if e.slot_skew_enabled else Fraction(0)
        self.clock = RationalClock(e.rate_num, e.rate_den, e.proxy_rate, capture_offset_seconds=cap, hold_offset_seconds=cap + skew)
        self.reset()

    def reset(self):
        self.up.reset(); self.r3.reset(); self.route.reset(); self.down.reset(); self.clock.reset()
        # proxy history: absolute indices [hist_start, hist_start+len). Samples before stream start (index < 0)
        # are zero by definition, so the history is pre-padded with hw_s zeros (hist_start = -hw_s) and no
        # interpolation window can ever index before the buffer (fix 1.0.1: negative indices wrapped).
        self.proxy_hist = np.zeros(self.hw_s_pad, dtype=np.float64)
        self.hist_start = -self.hw_s_pad
        self.codes: dict[int, int] = {}                    # k -> code (bounded window, pruned)
        self.n_out = 0                                     # next absolute proxy output index
        self.clip_count = 0
        self.peak_in = 0.0
        self.tap_codes: list[int] = []


class SPReferenceEngine:
    """Offline reference for R1–R9 + R16 of the SP stage. prepare() → reset() → process()* → drain()."""

    def __init__(self):
        self.prepared = False

    # ---------------------------------------------------------------- prepare
    def prepare(self, host_rate_hz: int, channels: int, asset: dict, asset_sha256: str,
                product: SPProductParameters, research: dict, research_sha256: str) -> PreparedInfo:
        if host_rate_hz not in SUPPORTED_HOST_RATES:
            raise InvalidConfiguration("UNSUPPORTED_HOST_RATE", f"{host_rate_hz} not in {SUPPORTED_HOST_RATES}")
        if channels < 1:
            raise InvalidConfiguration("CHANNELS", "need >= 1 channel")
        if asset.get("track") != "A":
            raise InvalidConfiguration("ASSET_TRACK", "only Track A assets exist; a Track B asset needs hardware")
        sw = research["switches"]
        # physical vs normalized calibration
        if product.calibration_mode == "PHYSICAL":
            # any physically scaled run must have volts; the provisional asset has UNSET → blocked
            asset_value(asset, "volts_per_normalized_unit")
            raise InvalidConfiguration("CALIBRATION_UNAVAILABLE", "physical calibration requires Track B evidence")
        if product.calibration_mode != "NORMALIZED_RESEARCH" or not asset.get("normalized_research_calibration"):
            raise InvalidConfiguration("CALIBRATION_MODE", "unknown calibration mode")
        # rate
        rate = asset_value(asset, "sp_rate_hz")
        self.rate_num, self.rate_den = int(rate["numerator"]), int(rate["denominator"])
        # quantizer
        rule = sw["quantizer_rule"]
        if rule not in QUANTIZER_RULES:
            raise InvalidConfiguration("QUANTIZER_RULE", f"unknown rule {rule!r}; known {sorted(QUANTIZER_RULES)}")
        self.rule_name, self.rule = rule, QUANTIZER_RULES[rule]
        self.offset_codes = float(sw["quantizer_offset_codes"])
        self.quantizer_bypass = bool(sw["quantizer_bypass_diagnostic"])
        bits = int(asset_value(asset, "word_bits"))
        cr = asset_value(asset, "code_range")
        self.code_min, self.code_max = int(cr["min"]), int(cr["max"])
        if self.code_max - self.code_min + 1 != 2 ** bits:
            raise InvalidConfiguration("CODE_RANGE", "code range inconsistent with word_bits")
        self.full_scale_codes = float(2 ** (bits - 1))
        self.dac_fs = float(asset_value(asset, "dac_full_scale_normalized"))
        # gain
        steps = asset_value(asset, "input_gain_steps_db")
        if product.sp_input_gain not in steps:
            raise InvalidConfiguration("SP_INPUT_GAIN", f"{product.sp_input_gain} not in {steps}")
        self.gain = (10.0 ** (product.sp_input_gain / 20.0)) * (10.0 ** (product.sp_input_level_db / 20.0))
        if asset_value(asset, "r2_analog_clamp") != "INACTIVE":
            raise InvalidConfiguration("R2_CLAMP", "only INACTIVE analog clamp exists (no rail model)")
        # R3
        r3 = sw["r3_strategy"]
        if r3 != asset_value(asset, "r3_strategy"):
            raise InvalidConfiguration("R3_STRATEGY", "research config and asset disagree on R3 strategy")
        if r3 not in R3_STRATEGIES:
            raise InvalidConfiguration("R3_NOT_POPULATED", f"R3 strategy {r3!r} is reserved/not populated")
        self.r3_factory = R3_STRATEGIES[r3]
        # hold
        hf = float(sw["hold_fraction"])
        if hf != float(asset_value(asset, "hold_fraction")) or hf != 1.0:
            raise InvalidConfiguration("HOLD_FRACTION", "only the full-period hold (1.0) is implemented; others are blocked")
        # route
        routes = asset_value(asset, "output_routes")
        if product.sp_output_path not in routes:
            raise InvalidConfiguration("ROUTE_UNKNOWN", f"route {product.sp_output_path!r} not in asset")
        if routes[product.sp_output_path]["status"] != "POPULATED" or product.sp_output_path not in R8_ROUTES:
            raise InvalidConfiguration("ROUTE_NOT_POPULATED", f"route {product.sp_output_path!r} is NOT POPULATED (no guessed response)")
        self.route_name = product.sp_output_path
        self.route_factory = R8_ROUTES[self.route_name]
        self.out_gain = float(asset_value(asset, "r9_output_gain_normalized"))
        if asset_value(asset, "r9_coupling_pole") != "INACTIVE":
            raise InvalidConfiguration("R9_COUPLING", "only INACTIVE coupling exists")
        # proxy / kernels (IMPLEMENTATION)
        self.L = int(sw["proxy_oversampling"])
        if self.L < 1:
            raise InvalidConfiguration("PROXY", "proxy_oversampling must be >= 1")
        self.host_rate = int(host_rate_hz)
        self.proxy_rate = self.host_rate * self.L
        kp = sw["r1_r16_kernel"]
        lobes, beta = int(kp["lobes_per_side"]), float(kp["kaiser_beta"])
        self.h_lp = kaiser_sinc_lowpass(2 * lobes * self.L + 1, 0.5 / self.L, beta)
        self.hw_s = int(sw["sampler_half_width_host_samples"]) * self.L
        self.hw_z = int(sw["hold_kernel_half_width_host_samples"]) * self.L
        self.interp_beta = float(sw["interpolation_kaiser_beta"])
        self.step = BandlimitedStepTable(self.hw_z, self.interp_beta)
        period = Fraction(self.proxy_rate) * self.rate_den / self.rate_num     # proxy samples per SP sample
        self.sampler_taps = TapTable(self.hw_s, self.interp_beta, period.denominator)
        self.delay_proxy = lobes * self.L + self.hw_s + self.hw_z + lobes * self.L
        assert self.delay_proxy % self.L == 0
        self.latency_host = self.delay_proxy // self.L
        self.D = self.hw_s + self.hw_z  # internal continuous-time delay of the SP path on the proxy grid
        # research-only offsets: playback slot skew (hold edges) and capture offset (sampling instants), per channel index
        self.slot_skew_enabled = bool(sw["slot_skew_enabled"])
        self.slot_skew_seconds = Fraction(asset_value(asset, "slot_skew_seconds_research")).limit_denominator(10**12) if self.slot_skew_enabled else Fraction(0)
        self.capture_offset_enabled = bool(sw["capture_offset_enabled"])
        self.capture_offset_seconds = Fraction(sw["capture_offset_seconds_per_channel"]).limit_denominator(10**12) if self.capture_offset_enabled else Fraction(0)
        self.taps_enabled = bool(sw["diagnostic_taps"])
        self.channels = int(channels)
        self.asset_id = asset_identity(asset, asset_sha256)
        self.research_sha = research_sha256
        self.ch = [_ChannelState(self, c) for c in range(self.channels)]
        self.prepared = True
        sp_rate = Fraction(self.rate_num, self.rate_den)
        self.info = PreparedInfo(
            host_rate_hz=self.host_rate, proxy_rate_hz=self.proxy_rate, proxy_oversampling=self.L,
            sp_rate=f"{sp_rate.numerator}/{sp_rate.denominator} Hz", sp_over_host_ratio=str(sp_rate / self.host_rate),
            latency_host_samples=self.latency_host,
            latency_breakdown_proxy_samples={"R1": lobes * self.L, "R4_sampler_lookahead": self.hw_s, "R7_hold_kernel_lookahead": self.hw_z, "R16": lobes * self.L},
            hold_group_delay_descriptor="zero-order hold adds a frequency-dependent delay of one half machine period (19.2 µs on the provisional clock) plus the sampling phase (0..1 period), not compensated; not a hardware claim",
            kernel_properties=self._kernel_properties(lobes, beta),
            asset_identity=self.asset_id, research_config_sha256=self.research_sha, quantizer_rule=self.rule_name,
            r3_strategy=r3, route=self.route_name,
            fidelity="NORMALIZED RESEARCH SKELETON — NOT A MODEL OF A MEASURED SP-1200; UNVALIDATED AGAINST HARDWARE",
        )
        return self.info

    def _kernel_properties(self, lobes: int, beta: float) -> dict:
        """Design-derived numeric properties (Kaiser window formulas, Oppenheim & Schafer): used to derive check bounds."""
        A_lp = beta / 0.1102 + 8.7 if beta > 0 else 21.0           # stopband attenuation estimate, dB
        N = self.h_lp.size - 1
        dw = (A_lp - 8.0) / (2.285 * N)                              # transition width, rad/proxy sample
        A_interp = self.interp_beta / 0.1102 + 8.7
        return {
            "lowpass_taps": int(self.h_lp.size), "lowpass_cutoff_hz": self.host_rate / 2, "lowpass_kaiser_beta": beta,
            "lowpass_design_attenuation_db": A_lp, "lowpass_transition_width_hz": dw / (2 * np.pi) * self.proxy_rate,
            "interp_half_width_proxy": self.hw_s, "hold_kernel_half_width_proxy": self.hw_z, "interp_kaiser_beta": self.interp_beta,
            "interp_design_attenuation_db": A_interp, "hold_step_truncation_residual": self.step.truncation_residual,
            "line_amplitude_bound_relative": 2.0 * 10 ** (-A_lp / 20) + 10 ** (-A_interp / 20) + self.step.truncation_residual,
            "line_amplitude_bound_note": "absolute amplitude error bound for any spectral line = input amplitude x this value (leakage of out-of-band images through the low-pass stopband, interpolation kernel sidelobes, hold-step truncation); derived from kernel design, not tuned",
        }

    # ---------------------------------------------------------------- reset
    def reset(self):
        self._require()
        for c in self.ch:
            c.reset()

    def latency(self) -> int:
        self._require()
        return self.latency_host

    def _require(self):
        if not self.prepared:
            raise InvalidConfiguration("NOT_PREPARED", "call prepare() first")

    # ---------------------------------------------------------------- process
    def process(self, x: np.ndarray) -> np.ndarray:
        """x: (frames, channels) float64 host samples → y same shape, delayed by latency()."""
        self._require()
        x = np.asarray(x, dtype=np.float64)
        if x.ndim == 1:
            x = x[:, None]
        if x.shape[1] != self.channels:
            raise InvalidConfiguration("CHANNELS", "channel count differs from prepare()")
        y = np.empty_like(x)
        for c in range(self.channels):
            y[:, c] = self._process_channel(self.ch[c], x[:, c])
        return y

    def drain(self) -> np.ndarray:
        """Flush the implementation delay: returns latency() host frames (tail)."""
        self._require()
        return self.process(np.zeros((self.latency_host, self.channels)))

    # ---------------------------------------------------------------- per channel
    def _process_channel(self, st: _ChannelState, x: np.ndarray) -> np.ndarray:
        st.peak_in = max(st.peak_in, float(np.max(np.abs(x))) if x.size else 0.0)
        v = st.up.process(x)                       # R1
        v = v * self.gain                          # R2 (analog clamp INACTIVE)
        v = st.r3.process(v)                       # R3 (INACTIVE)
        # append to proxy history
        st.proxy_hist = np.concatenate([st.proxy_hist, v])
        avail_end = st.hist_start + st.proxy_hist.size      # absolute index one past last available
        # R4/R5: produce every machine sample whose interpolation window is available
        max_pos = Fraction(avail_end - 1 - self.hw_s)
        new = st.clock.take_samples_up_to(max_pos)
        if new:
            ks = np.array([k for k, _ in new], dtype=np.int64)
            pos = [p for _, p in new]
            base = np.array([p.numerator // p.denominator for p in pos], dtype=np.int64)
            den = self.sampler_taps.den
            residues = [(p - (p.numerator // p.denominator)) * den for p in pos]
            if any(r.denominator != 1 for r in residues):
                raise RuntimeError("internal invariant violated: sampling residue not on the tap-table grid")
            residues = np.array([int(r) for r in residues], dtype=np.int64)
            kk = self.sampler_taps.k
            taps = self.sampler_taps.taps(residues)
            idx = base[:, None] + kk[None, :].astype(np.int64) - st.hist_start
            if idx.min() < 0 or idx.max() >= st.proxy_hist.size:
                raise RuntimeError("internal invariant violated: sampler window outside proxy history")
            samples = np.sum(st.proxy_hist[idx] * taps, axis=1)
            if self.quantizer_bypass:
                codes = samples * self.full_scale_codes
            else:
                raw = self.rule(samples * self.full_scale_codes + self.offset_codes)
                codes = np.clip(raw, self.code_min, self.code_max)
                st.clip_count += int(np.sum(raw != codes))
            for k, cval in zip(ks.tolist(), codes.tolist()):
                st.codes[k] = cval
                if self.taps_enabled:
                    st.tap_codes.append(cval)
        # R7: band-limited hold for output proxy indices [st.n_out, avail_end): output n ↔ time n - D
        n0, n1 = st.n_out, avail_end
        n = np.arange(n0, n1, dtype=np.int64)
        t = n - self.D                                                   # continuous-time proxy position
        k_held = st.clock.latest_samples_at(t)                           # exact integer arithmetic, vectorised
        if k_held.size:
            kmin, kmax = int(k_held.min()), int(k_held.max())
            missing = [k for k in range(max(kmin, 0), kmax + 1) if k not in st.codes]
            if missing:
                raise RuntimeError(f"internal invariant violated: held codes not yet produced: {missing[:3]}")
            lut = np.array([st.codes[k] if k >= 0 else 0.0 for k in range(kmin, kmax + 1)], dtype=np.float64)
            held = lut[k_held - kmin]
        else:
            held = np.zeros(0, dtype=np.float64)
        h = held.copy()
        # edge corrections: edges e with |t - p_e| < hw_z ; e ranges over samples with p_e in (t0 - hw_z, t1 + hw_z)
        e_lo = st.clock.latest_sample_at(Fraction(int(t[0]) - self.hw_z)) + 1 if n.size else 0
        e_hi = st.clock.latest_sample_at(Fraction(int(t[-1]) + self.hw_z)) if n.size else -1
        for e in range(max(e_lo, 0), e_hi + 1):
            pe = st.clock.hold_position(e)
            pef = float(pe)
            delta = st.codes.get(e, 0.0) - (st.codes.get(e - 1, 0.0) if e > 0 else 0.0)
            if delta == 0.0:
                continue
            lo = int(np.floor(pef)) - self.hw_z + 1
            hi = int(np.floor(pef)) + self.hw_z
            a = max(lo, int(t[0])); b = min(hi, int(t[-1]))
            if a > b:
                continue
            tt = np.arange(a, b + 1, dtype=np.float64)
            d = tt - pef
            corr = self.step(d) - (d >= 0.0).astype(np.float64)   # S(d) - u(d); u(0)=1 matches k(n)=floor
            h[a - int(t[0]):b - int(t[0]) + 1] += delta * corr
        h = h * (self.dac_fs / self.full_scale_codes)
        st.n_out = n1
        # prune: codes older than needed, proxy history older than needed
        keep_from_k = st.clock.latest_sample_at(Fraction(int(t[-1]) - self.hw_z)) - 2 if n.size else 0
        for k in [k for k in st.codes if k < keep_from_k]:
            del st.codes[k]
        oldest_needed = (st.clock.position(st.clock.next_k).numerator // st.clock.position(st.clock.next_k).denominator) - self.hw_s - 1
        drop = max(0, oldest_needed - st.hist_start)
        if drop > 0:
            st.proxy_hist = st.proxy_hist[drop:]
            st.hist_start += drop
        # R8, R9, R16
        h = st.route.process(h)
        h = h * self.out_gain
        return st.down.process(h)

    # ---------------------------------------------------------------- meters / taps
    def meters(self) -> list[dict]:
        self._require()
        return [{"converter_clip_count": c.clip_count, "peak_input_normalized": c.peak_in} for c in self.ch]

    def tap_codes(self, channel: int) -> np.ndarray:
        self._require()
        return np.array(self.ch[channel].tap_codes, dtype=np.float64)
