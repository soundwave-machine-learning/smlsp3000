"""MPC3000 reference blocks R11–R15 and the true-stereo engine (Track A, provisional, OWN-DEC-005..008).

Signal flow per channel:

    host x[m] ─R1→ proxy v[n] ─R11→ gain ─R12→ TRANSPARENT ADC: ideal band limit at 22.05 kHz, sample at
    q_k = k·P (P = f_proxy/44100, exact Fraction), 18-bit code c18_k (round to nearest, clamp)
    ─R13→ c16_k = rule(c18_k / 4) clamp (ROUND_NEAREST default / TRUNCATION alternate)
    ─R14→ identity (stored = replayed) ─R15→ TRANSPARENT DAC: d18_k = 4·c16_k, ideal band-limited
    reconstruction y(t) = Σ_k d18_k/131072 · w(t/T − k) onto the proxy grid ─route MAIN_LR (identity)─ R16→ host y[m]

Everything that would be the machine's response (AK5328 decimator, SM5841 interpolator, PCM69A, I/V,
analog low-pass, coupling, de-emphasis, overload recovery, volts) is absent by owner decision and is
represented as a replaceable strategy slot. The implementation kernels (R1/R16 low-pass, the R12 band
limitation, the R4-style sampler, the R15 reconstruction) are IMPLEMENTATION/ESTIMATE and their numeric
properties are reported for check bounds. Nothing here is a measurement of an MPC3000.

Implementation delay (exact, integer host samples) = lobes + r12_half + ceil_L(hw_r·P + hw_s)/L + lobes.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from fractions import Fraction

import numpy as np

from .assets import asset_identity, asset_value
from .errors import InvalidConfiguration
from .kernels import TapTable, interpolation_kernel_response, kaiser_sinc_lowpass
from .scheduler import RationalClock
from .streaming import Decimator, PolyphaseUpsampler, StreamingFIR

SUPPORTED_HOST_RATES = (44100, 48000, 88200, 96000, 176400, 192000)
MODEL_IMPLEMENTATION_VERSION = "mpc3000-reference-impl-1.0.2"


# --- R13 reduction strategies (replaceable registry) -------------------------------------

def _reduce_round_nearest(c18: np.ndarray) -> np.ndarray:
    """⌊c18/4 + ½⌋ : nearest 16-bit code, ties toward +∞ (repository convention, OWN-DEC-003/007). OWNER-SET PROVISIONAL DEFAULT."""
    return np.floor(c18 / 4.0 + 0.5)


def _reduce_truncation(c18: np.ndarray) -> np.ndarray:
    """⌊c18/4⌋ : drop the two LSBs of the two's-complement word (truncation toward −∞). Research alternate."""
    return np.floor(c18 / 4.0)


REDUCTION_RULES = {"ROUND_NEAREST": _reduce_round_nearest, "TRUNCATION": _reduce_truncation}

# --- strategy registries (names reserved for future evidence-backed strategies are NOT populated) ---
R12_STRATEGIES = {"TRANSPARENT": "ideal band limitation at the machine Nyquist + ideal sampling + 18-bit code clamp"}
R12_RESERVED_SLOTS = ("ESTIMATE_FIR", "DATASHEET_RESPONSE", "MEASURED_RESPONSE")
R14_STRATEGIES = {"IDENTITY_UNITY": "stored 16-bit code replayed unchanged; x4 re-expansion to the 18-bit DAC word"}
R15_STRATEGIES = {"TRANSPARENT": "unity re-expansion + ideal band-limited reconstruction; no interpolation/I-V/LP/coupling/de-emphasis response"}
R15_RESERVED_SLOTS = ("ESTIMATE_FIR", "DATASHEET_RESPONSE", "MEASURED_RESPONSE")
R15_ROUTES = {"MAIN_LR": "identity"}
DE_EMPHASIS_STATES = ("OFF_UNASSERTED",)


@dataclass(frozen=True)
class MPCProductParameters:
    """ProductParameters subset for the MPC stage (docs/PARAMETERS.md candidate IDs). No defaults."""
    mpc_input_gain: str          # LO / MID / HI
    mpc_record_level_db: float   # ideal dB trim, <= 0 (0 = pot at maximum)
    mpc_output_route: str        # MAIN_LR / INDIVIDUAL_PAIR / HEADPHONES
    calibration_mode: str        # NORMALIZED_RESEARCH | PHYSICAL


@dataclass
class MPCPreparedInfo:
    host_rate_hz: int
    proxy_rate_hz: int
    proxy_oversampling: int
    mpc_rate: str
    mpc_over_host_ratio: str
    latency_host_samples: int
    latency_breakdown_proxy_samples: dict
    latency_note: str
    kernel_properties: dict
    asset_identity: dict
    research_config_sha256: str
    reduction_rule: str
    r12_strategy: str
    r14_strategy: str
    r15_strategy: str
    de_emphasis: str
    route: str
    fidelity: str

    def to_dict(self) -> dict:
        return asdict(self)


class _ChannelState:
    def __init__(self, engine: "MPCReferenceEngine"):
        e = engine
        self.up = PolyphaseUpsampler(e.L, e.h_lp)
        self.bandlimit = StreamingFIR(e.h_r12)
        self.down = Decimator(e.L, e.h_lp)
        self.clock = RationalClock(e.rate_num, e.rate_den, e.proxy_rate)
        self.hw_s = e.hw_s
        self.reset()

    def reset(self):
        self.up.reset(); self.bandlimit.reset(); self.down.reset(); self.clock.reset()
        self.proxy_hist = np.zeros(self.hw_s, dtype=np.float64)   # pre-padded: samples before t=0 are zero
        self.hist_start = -self.hw_s
        self.codes16: dict[int, float] = {}
        self.n_out = 0
        self.clip18_count = 0
        self.clip16_count = 0
        self.peak_in = 0.0
        self.tap_c18: list[float] = []
        self.tap_c16: list[float] = []


class MPCReferenceEngine:
    """Offline reference for R1 + R11–R15 + R16 of the MPC stage. prepare() → reset() → process()* → drain()."""

    def __init__(self):
        self.prepared = False

    # ---------------------------------------------------------------- prepare
    def prepare(self, host_rate_hz: int, channels: int, asset: dict, asset_sha256: str,
                product: MPCProductParameters, research: dict, research_sha256: str) -> MPCPreparedInfo:
        if host_rate_hz not in SUPPORTED_HOST_RATES:
            raise InvalidConfiguration("UNSUPPORTED_HOST_RATE", f"{host_rate_hz} not in {SUPPORTED_HOST_RATES}")
        if channels < 1:
            raise InvalidConfiguration("CHANNELS", "need >= 1 channel")
        if asset.get("track") != "A" or asset.get("machine") != "MPC3000":
            raise InvalidConfiguration("ASSET_TRACK", "expected a Track A MPC3000 asset")
        sw = research["switches"]
        if product.calibration_mode == "PHYSICAL":
            asset_value(asset, "volts_per_normalized_unit")   # UNSET → raises ASSET_VALUE_UNSET
            raise InvalidConfiguration("CALIBRATION_UNAVAILABLE", "physical calibration requires Track B evidence")
        if product.calibration_mode != "NORMALIZED_RESEARCH" or not asset.get("normalized_research_calibration"):
            raise InvalidConfiguration("CALIBRATION_MODE", "unknown calibration mode")
        rate = asset_value(asset, "mpc_rate_hz")
        self.rate_num, self.rate_den = int(rate["numerator"]), int(rate["denominator"])
        # converter / storage code domains
        cbits = int(asset_value(asset, "converter_bits")); sbits = int(asset_value(asset, "storage_bits"))
        cr = asset_value(asset, "converter_code_range"); sr = asset_value(asset, "storage_code_range")
        self.c18_min, self.c18_max = int(cr["min"]), int(cr["max"])
        self.c16_min, self.c16_max = int(sr["min"]), int(sr["max"])
        if self.c18_max - self.c18_min + 1 != 2 ** cbits or self.c16_max - self.c16_min + 1 != 2 ** sbits:
            raise InvalidConfiguration("CODE_RANGE", "code ranges inconsistent with bit widths")
        self.c18_fs = float(2 ** (cbits - 1))
        self.expand = 2 ** (cbits - sbits)   # exact x4
        if asset_value(asset, "adc_code_representation") != "ROUND_NEAREST_18BIT":
            raise InvalidConfiguration("ADC_CODE_RULE", "only ROUND_NEAREST_18BIT code representation exists")
        self.quant_bypass = bool(sw["converter_quantization_bypass_diagnostic"])
        # R13
        rule = sw["reduction_rule"]
        if rule not in REDUCTION_RULES:
            raise InvalidConfiguration("REDUCTION_RULE", f"unknown rule {rule!r}; known {sorted(REDUCTION_RULES)}")
        self.rule_name, self.rule = rule, REDUCTION_RULES[rule]
        # R12 / R14 / R15 strategies
        for key, reg, slots in (("r12_strategy", R12_STRATEGIES, R12_RESERVED_SLOTS), ("r14_strategy", R14_STRATEGIES, ()), ("r15_strategy", R15_STRATEGIES, R15_RESERVED_SLOTS)):
            name = sw[key]
            akey = key if key != "r14_strategy" else "r14_arithmetic"
            if name != asset_value(asset, akey):
                raise InvalidConfiguration(key.upper(), "research config and asset disagree")
            if name not in reg:
                raise InvalidConfiguration(key.upper() + "_NOT_POPULATED", f"{name!r} is reserved/not populated (slots {slots})")
        self.r12_name, self.r14_name, self.r15_name = sw["r12_strategy"], sw["r14_strategy"], sw["r15_strategy"]
        de = sw["de_emphasis"]
        if de != asset_value(asset, "de_emphasis") or de not in DE_EMPHASIS_STATES:
            raise InvalidConfiguration("DE_EMPHASIS", "only OFF_UNASSERTED exists (use UNKNOWN)")
        self.de_emphasis = de
        for key in ("r11_analog_clamp", "r11_coupling_pole", "r15_coupling_pole"):
            if asset_value(asset, key) != "INACTIVE":
                raise InvalidConfiguration(key.upper(), "only INACTIVE exists")
        # R11 gain
        steps = asset_value(asset, "input_gain_steps")
        if product.mpc_input_gain not in steps:
            raise InvalidConfiguration("MPC_INPUT_GAIN", f"{product.mpc_input_gain!r} not in {sorted(steps)}")
        if asset_value(asset, "record_level_law") != "IDEAL_DB_TRIM":
            raise InvalidConfiguration("RECORD_LEVEL_LAW", "only IDEAL_DB_TRIM exists")
        if product.mpc_record_level_db > 0.0:
            raise InvalidConfiguration("RECORD_LEVEL", "ideal trim is <= 0 dB (0 dB = pot maximum)")
        self.gain = (10.0 ** (steps[product.mpc_input_gain]["relative_gain_db"] / 20.0)) * (10.0 ** (product.mpc_record_level_db / 20.0))
        # route
        routes = asset_value(asset, "output_routes")
        if product.mpc_output_route not in routes:
            raise InvalidConfiguration("ROUTE_UNKNOWN", f"route {product.mpc_output_route!r} not in asset")
        st = routes[product.mpc_output_route]["status"]
        if st == "EXCLUDED":
            raise InvalidConfiguration("ROUTE_EXCLUDED", f"route {product.mpc_output_route!r} is EXCLUDED")
        if st != "POPULATED" or product.mpc_output_route not in R15_ROUTES:
            raise InvalidConfiguration("ROUTE_NOT_POPULATED", f"route {product.mpc_output_route!r} is NOT POPULATED")
        self.route_name = product.mpc_output_route
        self.dac_fs = float(asset_value(asset, "dac_full_scale_normalized"))
        # proxy / kernels (IMPLEMENTATION)
        self.L = int(sw["proxy_oversampling"]); self.host_rate = int(host_rate_hz); self.proxy_rate = self.host_rate * self.L
        kp = sw["r1_r16_kernel"]; lobes, beta = int(kp["lobes_per_side"]), float(kp["kaiser_beta"])
        self.h_lp = kaiser_sinc_lowpass(2 * lobes * self.L + 1, 0.5 / self.L, beta)
        r12_half = int(sw["r12_lowpass_half_width_host_samples"]) * self.L
        self.h_r12 = kaiser_sinc_lowpass(2 * r12_half + 1, (self.rate_num / self.rate_den / 2.0) / self.proxy_rate, float(sw["r12_lowpass_kaiser_beta"]))
        self.hw_s = int(sw["sampler_half_width_host_samples"]) * self.L
        self.hw_r = int(sw["reconstruction_half_width_machine_samples"])
        self.interp_beta = float(sw["interpolation_kaiser_beta"])
        self.P = Fraction(self.proxy_rate) * self.rate_den / self.rate_num      # proxy samples per machine sample
        self.sampler_taps = TapTable(self.hw_s, self.interp_beta, self.P.denominator)
        self.recon_taps = TapTable(self.hw_r, self.interp_beta, self.P.numerator)   # u = tq/P has denominator P.numerator
        # R15 reads codes up to hw_r machine samples ahead of the output time; each code needs hw_s proxy samples
        # of sampler lookahead → total SP-side lookahead D15 >= hw_r*P + hw_s, rounded up to a multiple of L.
        lookahead = self.hw_r * self.P + self.hw_s
        self.D15 = int(self.L * (-(-lookahead // self.L)))
        self.delay_proxy = lobes * self.L + r12_half + self.D15 + lobes * self.L
        self.core_delay_proxy = r12_half + self.D15   # delay of core_channel() on the proxy grid (multiple of L)
        assert self.delay_proxy % self.L == 0
        self.latency_host = self.delay_proxy // self.L
        self.taps_enabled = bool(sw["diagnostic_taps"])
        self.channels = int(channels)
        self.asset_id = asset_identity(asset, asset_sha256); self.research_sha = research_sha256
        self.ch = [_ChannelState(self) for _ in range(self.channels)]
        self.prepared = True
        mrate = Fraction(self.rate_num, self.rate_den)
        A_lp = beta / 0.1102 + 8.7; A_12 = float(sw["r12_lowpass_kaiser_beta"]) / 0.1102 + 8.7; A_i = self.interp_beta / 0.1102 + 8.7
        dw12 = (A_12 - 8.0) / (2.285 * (self.h_r12.size - 1))
        self.kernel_properties = {
            "lowpass_taps": int(self.h_lp.size), "lowpass_design_attenuation_db": A_lp,
            "lowpass_transition_width_hz": (A_lp - 8.0) / (2.285 * (self.h_lp.size - 1)) / (2 * np.pi) * self.proxy_rate,
            "r12_bandlimit_taps": int(self.h_r12.size), "r12_bandlimit_cutoff_hz": float(mrate) / 2.0, "r12_design_attenuation_db": A_12,
            "r12_transition_width_hz_ESTIMATE_not_AK5328": dw12 / (2 * np.pi) * self.proxy_rate,
            "sampler_half_width_proxy": self.hw_s, "reconstruction_half_width_machine_samples": self.hw_r, "interp_design_attenuation_db": A_i,
            "reconstruction_response_db_at_20k_21k_21p5k": [float(20 * np.log10(v)) for v in interpolation_kernel_response(self.hw_r, self.interp_beta, np.array([20000.0, 21000.0, 21500.0]) / float(mrate))],
            "reconstruction_note": "exact response of the IMPLEMENTATION reconstruction kernel; NOT the SM5841/PCM69A/analog response (UNKNOWN)",
            "line_amplitude_bound_relative": 2.0 * 10 ** (-A_lp / 20) + 10 ** (-A_12 / 20) + 2.0 * 10 ** (-A_i / 20),
            "line_amplitude_bound_note": "absolute amplitude error bound for any in-band spectral line = input amplitude x this value (kernel stopband leakage and interpolation/reconstruction sidelobes); derived from kernel design, not tuned",
        }
        self.info = MPCPreparedInfo(
            host_rate_hz=self.host_rate, proxy_rate_hz=self.proxy_rate, proxy_oversampling=self.L,
            mpc_rate=f"{mrate.numerator}/{mrate.denominator} Hz", mpc_over_host_ratio=str(mrate / self.host_rate),
            latency_host_samples=self.latency_host,
            latency_breakdown_proxy_samples={"R1": lobes * self.L, "R12_bandlimit": r12_half, "R12_sampler_plus_R15_reconstruction_lookahead": self.D15, "R16": lobes * self.L},
            latency_note="software implementation delay of the TRANSPARENT strategies' kernels; NOT a measured AK5328/SM5841 latency (UNKNOWN, RD-P1-02/03)",
            kernel_properties=self.kernel_properties, asset_identity=self.asset_id, research_config_sha256=self.research_sha,
            reduction_rule=self.rule_name, r12_strategy=self.r12_name, r14_strategy=self.r14_name, r15_strategy=self.r15_name,
            de_emphasis=self.de_emphasis, route=self.route_name,
            fidelity="NORMALIZED RESEARCH SKELETON — TRANSPARENT ADC/DAC STRATEGIES; NOT A MODEL OF A MEASURED MPC3000; UNVALIDATED AGAINST HARDWARE",
        )
        return self.info

    def _require(self):
        if not self.prepared:
            raise InvalidConfiguration("NOT_PREPARED", "call prepare() first")

    def reset(self):
        self._require()
        for c in self.ch:
            c.reset()

    def latency(self) -> int:
        self._require()
        return self.latency_host

    # ---------------------------------------------------------------- process
    def process(self, x: np.ndarray) -> np.ndarray:
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
        self._require()
        return self.process(np.zeros((self.latency_host, self.channels)))

    def reduce_codes(self, c18: np.ndarray) -> tuple[np.ndarray, int]:
        """R13 on integer-valued 18-bit codes → (16-bit codes, clamp count). Exposed for code-domain tests."""
        self._require()
        raw = self.rule(np.asarray(c18, dtype=np.float64))
        c16 = np.clip(raw, self.c16_min, self.c16_max)
        return c16, int(np.sum(raw != c16))

    def expand_codes(self, c16: np.ndarray) -> np.ndarray:
        """R14/R15 unity re-expansion of stored codes to the 18-bit DAC word (exact x4)."""
        self._require()
        return np.asarray(c16, dtype=np.float64) * self.expand

    # ---------------------------------------------------------------- per channel
    def _process_channel(self, st: _ChannelState, x: np.ndarray) -> np.ndarray:
        st.peak_in = max(st.peak_in, float(np.max(np.abs(x))) if x.size else 0.0)   # host-input peak meter (unchanged semantics)
        return st.down.process(self.core_channel(st, st.up.process(x)))   # R1 → core (R11–R15) → R16

    def core_channel(self, st: _ChannelState, v: np.ndarray) -> np.ndarray:
        """R11–R15 on the proxy grid: proxy input v (len N) → proxy output h (len N), delayed by core_delay_proxy.

        Exposed for the cascade engine (composition on the proxy grid); standalone use goes through process()."""
        v = v * self.gain                    # R11 (switch step x ideal trim; clamp/coupling INACTIVE)
        v = st.bandlimit.process(v)          # R12 TRANSPARENT: ideal band limitation at the machine Nyquist
        st.proxy_hist = np.concatenate([st.proxy_hist, v])
        avail_end = st.hist_start + st.proxy_hist.size
        # R12 sampling at q_k = k*P (lookahead hw_s) → 18-bit code
        new = st.clock.take_samples_up_to(Fraction(avail_end - 1 - self.hw_s))
        if new:
            pos = [p for _, p in new]
            base = np.array([p.numerator // p.denominator for p in pos], dtype=np.int64)
            den = self.sampler_taps.den
            residues = np.array([int((p - (p.numerator // p.denominator)) * den) for p in pos], dtype=np.int64)
            kk = self.sampler_taps.k
            taps = self.sampler_taps.taps(residues)
            idx = base[:, None] + kk[None, :].astype(np.int64) - st.hist_start
            if idx.min() < 0 or idx.max() >= st.proxy_hist.size:
                raise RuntimeError("internal invariant violated: sampler window outside proxy history")
            s = np.sum(st.proxy_hist[idx] * taps, axis=1)
            if self.quant_bypass:
                c16 = s * (self.c18_fs / self.expand)       # continuous "codes" for linear-response diagnostics
            else:
                raw18 = np.floor(s * self.c18_fs + 0.5)     # ROUND_NEAREST_18BIT representation (ESTIMATE)
                c18 = np.clip(raw18, self.c18_min, self.c18_max)
                st.clip18_count += int(np.sum(raw18 != c18))
                raw16 = self.rule(c18)                     # R13
                c16 = np.clip(raw16, self.c16_min, self.c16_max)
                st.clip16_count += int(np.sum(raw16 != c16))
                if self.taps_enabled:
                    st.tap_c18.extend(c18.tolist())
            if self.taps_enabled:
                st.tap_c16.extend(c16.tolist())
            for (k, _), cv in zip(new, c16.tolist()):
                st.codes16[k] = cv                          # R14: stored = replayed (identity)
        # R15 TRANSPARENT: ideal reconstruction onto proxy output indices [n_out, avail_end); output n ↔ time n - D15
        n0, n1 = st.n_out, avail_end
        n = np.arange(n0, n1, dtype=np.int64)
        if n.size:
            h = np.empty(n.size, dtype=np.float64)
            CH = 8192
            for s0 in range(0, n.size, CH):
                nn = n[s0:s0 + CH]
                tq = nn - self.D15                                        # proxy position of the output sample's time
                u_num = tq * self.P.denominator                          # machine-sample coordinate u = tq / P = u_num / u_den
                u_den = self.P.numerator
                kc = np.floor_divide(u_num, u_den)                        # floor(u)
                residues = u_num - kc * u_den                             # (u - floor(u)) * u_den, exact integers
                kk = self.recon_taps.k
                taps = self.recon_taps.taps(residues)
                kidx = kc[:, None] + kk[None, :].astype(np.int64)
                kmin, kmax = int(kidx.min()), int(kidx.max())
                lut = np.empty(kmax - kmin + 1, dtype=np.float64)
                for k in range(kmin, kmax + 1):
                    if k < 0:
                        lut[k - kmin] = 0.0
                    elif k in st.codes16:
                        lut[k - kmin] = st.codes16[k]
                    else:
                        raise RuntimeError(f"internal invariant violated: code {k} not yet produced for reconstruction")
                d18 = lut[kidx - kmin] * self.expand                     # R14/R15 unity re-expansion
                h[s0:s0 + nn.size] = np.sum(d18 * taps, axis=1) * (self.dac_fs / self.c18_fs)
        else:
            h = np.zeros(0, dtype=np.float64)
        st.n_out = n1
        # prune
        if n.size:
            keep_k = int(np.floor_divide((int(n[-1]) - self.D15) * self.P.denominator, self.P.numerator)) - self.hw_r - 2
            for k in [k for k in st.codes16 if k < keep_k]:
                del st.codes16[k]
        nxt = st.clock.position(st.clock.next_k)
        oldest_needed = (nxt.numerator // nxt.denominator) - self.hw_s - 1
        drop = max(0, oldest_needed - st.hist_start)
        if drop > 0:
            st.proxy_hist = st.proxy_hist[drop:]; st.hist_start += drop
        return h                               # route MAIN_LR identity (R16 applied by the caller)

    def meters(self) -> list[dict]:
        self._require()
        return [{"converter_clip_count_18bit": c.clip18_count, "storage_clamp_count_16bit": c.clip16_count, "peak_input_normalized": c.peak_in} for c in self.ch]

    def tap_codes(self, channel: int, which: str = "c16") -> np.ndarray:
        self._require()
        src = self.ch[channel].tap_c16 if which == "c16" else self.ch[channel].tap_c18
        return np.array(src, dtype=np.float64)
