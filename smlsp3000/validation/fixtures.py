"""Frozen Sprint 6 validation fixtures (OWN-DEC-016; frozen before any native result was evaluated).

Every fixture is an analytic continuous-time definition rendered at a host rate from a common time origin t = 0,
so the same fixture exists at every supported rate. Nothing here is music or hardware; all SIMULATION.
"""
from __future__ import annotations

import numpy as np

RATES = (44100, 48000, 88200, 96000, 176400, 192000)
SEED = 20261007
RAMP = 0.005   # raised-cosine edge seconds for gated material


def _edge(t: np.ndarray, t0: float, t1: float, edge: float) -> np.ndarray:
    w = np.ones_like(t)
    a = (t - t0) / edge
    w = np.where(a < 1.0, 0.5 - 0.5 * np.cos(np.pi * np.clip(a, 0.0, 1.0)), w)
    b = (t1 - t) / edge
    w = np.where(b < 1.0, 0.5 - 0.5 * np.cos(np.pi * np.clip(b, 0.0, 1.0)), w)
    return np.where((t >= t0) & (t <= t1), w, 0.0)


def multitone_components(n_tones: int, f_lo: float, f_hi: float, seed: int) -> list[tuple[float, float, float]]:
    """(frequency, amplitude, phase) with log spacing and deterministic phases; common band only (< 20 kHz)."""
    rng = np.random.default_rng(seed)
    f = np.exp(np.linspace(np.log(f_lo), np.log(f_hi), n_tones))
    ph = rng.uniform(0, 2 * np.pi, n_tones)
    return [(float(fi), 1.0 / n_tones, float(p)) for fi, p in zip(f, ph)]


def render_fixture(name: str, rate: int, seconds: float = 0.5, channels: int = 2) -> np.ndarray:
    """Render a frozen fixture at `rate`; (frames, channels) float64. Channel 1 is a decorrelated/scaled variant."""
    n = int(round(seconds * rate))
    t = np.arange(n, dtype=np.float64) / rate
    rng = np.random.default_rng(SEED + sum(ord(c) for c in name))
    if name == "sine_1k_m20":
        x = 10 ** (-20 / 20) * np.sin(2 * np.pi * 1000.0 * t)
    elif name == "sine_1k_m60":
        x = 10 ** (-60 / 20) * np.sin(2 * np.pi * 1000.0 * t)
    elif name == "sine_1k_0dbfs_boundary":
        x = 0.999 * np.sin(2 * np.pi * 997.0 * t)              # just below full scale: exercises code endpoints
    elif name == "multitone_mix_m12":
        comps = multitone_components(24, 40.0, 18000.0, SEED)
        x = sum(a * np.sin(2 * np.pi * f * t + p) for f, a, p in comps) * 10 ** (-12 / 20) / 0.35
    elif name == "near_nyquist_tone_19k":
        x = 0.5 * np.sin(2 * np.pi * 19000.0 * t)                # common band edge; SP fold-back (26.04 kHz grid) intentional
    elif name == "transient_bursts":
        x = np.zeros(n)
        for k, (f, t0) in enumerate(((180.0, 0.05), (2400.0, 0.17), (7000.0, 0.29), (12000.0, 0.41))):
            x += 0.8 * np.sin(2 * np.pi * f * t) * _edge(t, t0, t0 + 0.03, 0.002)
        x += 0.9 * ((t >= 0.10) & (t < 0.10 + 1.0 / 48000.0 * 2))  # two-sample-at-48k rectangular click (band-wide)
    elif name == "noise_pink_m18":
        w = rng.standard_normal(n)
        # deterministic pink-ish shaping by cumulative smoothing (analytic recipe, same at every rate in continuous time)
        X = np.fft.rfft(w); f = np.fft.rfftfreq(n, 1.0 / rate); X[1:] /= np.sqrt(f[1:] / 20.0); X[0] = 0.0; X[f > 18000.0] = 0.0
        x = np.fft.irfft(X, n); x = x / np.max(np.abs(x)) * 10 ** (-18 / 20) * 4.0
        x = np.clip(x, -0.95, 0.95)
    elif name == "overrange_steps_pm16":
        x = np.zeros(n)
        for k, lvl in enumerate((1.5, -1.5, 4.0, -4.0, 16.0, -16.0, 0.5)):
            x += lvl * np.sin(2 * np.pi * 320.0 * t) * _edge(t, 0.02 + 0.065 * k, 0.07 + 0.065 * k, 0.004)
    elif name == "dc_step_and_silence":
        x = 0.25 * ((t >= 0.1) & (t < 0.3)) - 0.25 * ((t >= 0.3) & (t < 0.35))
    elif name == "tie_adversarial_sp":
        # a slow ramp whose SP-grid samples land close to 12-bit code midpoints (ties toward +inf exercised)
        x = (np.floor(t * 6000.0) + 0.5) / 2048.0 * 0.9
        x = np.clip(x, -1.0, 1.0)
    else:
        raise KeyError(name)
    x2 = np.roll(x, n // 3) * 0.7 if channels == 2 else None
    out = np.stack([x, x2], axis=1) if channels == 2 else x[:, None]
    return out.astype(np.float64)


FIXTURE_NAMES = ("sine_1k_m20", "sine_1k_m60", "sine_1k_0dbfs_boundary", "multitone_mix_m12", "near_nyquist_tone_19k", "transient_bursts", "noise_pink_m18",
                 "overrange_steps_pm16", "dc_step_and_silence", "tie_adversarial_sp")

# configuration states for VAL-021 (all at 48 kHz unless noted); keys are native tool flags; reference built from the same values
CONFIG_STATES = {
    "product_default": {},
    "sp_gain_20": {"sp_gain": 20}, "sp_gain_40_level_m30": {"sp_gain": 40, "sp_level": -30.0},
    "sp_level_p12": {"sp_level": 12.0}, "sp_level_m60": {"sp_level": -60.0},
    "mpc_mid": {"mpc_gain": "MID", "sp_level": -24.0}, "mpc_hi": {"mpc_gain": "HI", "sp_level": -46.0},
    "interstage_m20": {"interstage": -20.0}, "interstage_p6": {"interstage": 6.0}, "interstage_p24_clamp": {"interstage": 24.0}, "interstage_m60": {"interstage": -60.0},
    "mode_sp_only": {"mode": "SP_ONLY"}, "mode_mpc_only": {"mode": "MPC_ONLY"}, "mode_both_bypassed": {"mode": "BOTH_MACHINE_BYPASSED"},
    "research_quantizer_floor": {"quantizer_rule": "FLOOR"}, "research_reduction_truncation": {"reduction_rule": "TRUNCATION"},
    "research_quantizer_bypass": {"quantizer_bypass": 1}, "research_converter_bypass": {"converter_bypass": 1},
    "research_reverse_order": {"reverse": 1},
}

METRICS = {
    "alignment": "declared integer latency only (native and reference report the same value; verified); no fitted gain/DC/clock/delay",
    "comparison_point": "native output before output trim (trim 0 dB in every fixture; trim law tested separately) vs reference cascade output",
    "rms_limit": "RMS(error) <= max(1e-5 * RMS(input), 1e-7) per channel, RMS(input) over the fixture frames",
    "peak_limit": "max |error| <= 1e-4 per channel",
    "per_fixture": "each (fixture, rate, state, channel) cell PASS/FAIL individually; never averaged",
    "discrete_rules": "SP 12-bit codes, MPC 18-bit codes and 16-bit codes compared exactly per machine sample (native taps vs reference taps); any difference reported with index, native/reference code, the sampler value and the output consequence",
    "determinism": "two native renders bit-identical (sha256 of the output bytes); block partitions (64 / irregular / seeded / single-call) bit-identical",
}
