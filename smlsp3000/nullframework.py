"""Pilot/alignment/null evaluator (docs/VALIDATION_PLAN.md “Hardware null protocol”).

Pipeline (one constant clock ratio, one fixed sub-sample delay, one scalar
gain from the calibration tone, fixed polarity, documented DC treatment):

1. DC: report the mean of the leading silence window of each signal; remove
   with an identical first-order high-pass (``dc_highpass_hz``) on both.
2. Polarity: sign of the cross-correlation peak of the start pilot burst.
3. Clock ratio: pilot frequency scale measured on reference and capture at
   start and end (phase-slope demodulation for a first guess, then a joint
   multi-tone least-squares scale fit); ratio = mean(r_cap/r_ref). The
   start/end disagreement is reported in ppm as a drift-consistency metric.
4. Delay: coarse integer lag from the envelope cross-correlation of the start
   pilot burst on the ratio-corrected capture; fine sub-sample part from the
   pilot phase difference; the end pilot repeats the estimate as a check.
5. Resample the raw capture once onto the reference grid with a Kaiser-windowed
   sinc interpolator (single pass; ratio and delay applied together).
6. Gain: amplitude ratio of the 1 kHz calibration tone (demodulated magnitude).
7. Residual metrics over the program window.

Prohibited by policy and absent here: EQ, dynamic gain, time-varying warp,
fitted filters. Nonzero *acceptance* thresholds are not defined in this module;
hardware fit thresholds are G-06 (docs/GATE_REGISTER.md).
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np

from .stimuli import Stimulus

ALGORITHM_VERSION = "nullframework-1.2.1"
PREPROCESSING_VERSION = "dc-hp1-5Hz/two-tone-pilot-lsfit+xcorr+phase/kaiser-sinc-96tap-b12"


@dataclass
class EvaluatorConfig:
    dc_highpass_hz: float = 5.0
    dc_window_s: float = 0.040
    pilot_trim_s: float = 0.020          # drop this much at each pilot edge before phase-slope fit
    demod_average_s: float = 0.010       # moving-average length for demodulation (nulls 2f and the second pilot tone; 10 ms = 1/100 Hz)
    coarse_envelope_s: float = 0.010     # heavy envelope smoothing for the coarse (±1/2 pilot-recurrence) search
    sinc_half_width: int = 48            # taps each side
    kaiser_beta: float = 12.0
    envelope_smooth_s: float = 0.002     # (unused by the coarse search; kept for diagnostics)
    analysis_trim_s: float = 0.020       # trimmed from each end of the program window for metrics
    band_edges_hz: tuple = (22.0, 44.0, 88.0, 177.0, 355.0, 710.0, 1420.0, 2840.0, 5680.0, 11360.0, 22720.0)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AlignmentEstimate:
    dc_reference: float
    dc_capture: float
    polarity: int
    pilot_freq_ref_start_hz: float
    pilot_freq_ref_end_hz: float
    pilot_freq_cap_start_hz: float
    pilot_freq_cap_end_hz: float
    clock_ratio: float
    clock_ratio_drift_ppm: float
    delay_coarse_samples: int
    delay_samples: float
    delay_seconds: float
    delay_end_check_samples: float
    gain: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class NullMetrics:
    n_samples: int
    signal_rms: float
    residual_peak_abs: float
    residual_peak_dbfs: float | None
    residual_rms: float
    residual_rms_db_re_signal: float | None
    correlation: float | None
    per_band_residual_db: dict
    max_abs_residual_exact_zero: bool

    def to_dict(self) -> dict:
        return asdict(self)


# --- helpers -----------------------------------------------------------------

def _db(x: float) -> float | None:
    return None if x <= 0.0 or not np.isfinite(x) else float(20.0 * np.log10(x))


def null_identical(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Residual of two arrays with NO preprocessing. Identical arrays must give an all-zero residual."""
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    if a.shape != b.shape:
        raise ValueError("shape mismatch")
    return a - b


def dc_highpass(x: np.ndarray, fs: float, fc_hz: float, initial_dc: float) -> np.ndarray:
    """First-order DC blocker y[n] = x[n] - x[n-1] + a*y[n-1], a = exp(-2*pi*fc/fs); initial state at ``initial_dc``."""
    a = float(np.exp(-2.0 * np.pi * fc_hz / fs))
    x = np.asarray(x, dtype=np.float64)
    y = np.empty_like(x)
    prev_x = initial_dc
    prev_y = 0.0
    for n in range(x.size):
        y[n] = x[n] - prev_x + a * prev_y
        prev_x = x[n]
        prev_y = y[n]
    return y


def _avg_len(fs: float, f_hz: float, average_s: float | None) -> int:
    if average_s is None:
        return max(2, int(round(fs / f_hz)))
    return max(2, int(round(average_s * fs)))


def estimate_tone_frequency(x: np.ndarray, fs: float, f_nominal: float, average_s: float | None = None) -> float:
    """Phase-slope frequency estimate of a near-``f_nominal`` tone.

    Demodulate, moving-average over ``average_s`` (default one nominal period;
    nulls the 2f image and any tone whose offset is a multiple of 1/average_s),
    unwrap phase, least-squares slope. Returns Hz.
    """
    n = np.arange(x.size, dtype=np.float64)
    z = x * np.exp(-1j * 2.0 * np.pi * f_nominal * n / fs)
    L = _avg_len(fs, f_nominal, average_s)
    kernel = np.ones(L) / L
    zf = np.convolve(z, kernel, mode="valid")
    ph = np.unwrap(np.angle(zf))
    m = np.arange(ph.size, dtype=np.float64)
    slope = np.polyfit(m, ph, 1)[0]              # rad/sample
    return float(f_nominal + slope * fs / (2.0 * np.pi))


def tone_amplitude(x: np.ndarray, fs: float, f_hz: float, average_s: float | None = None) -> float:
    """Amplitude of a tone at f_hz via demodulation (averaged |z|*2)."""
    n = np.arange(x.size, dtype=np.float64)
    z = x * np.exp(-1j * 2.0 * np.pi * f_hz * n / fs)
    L = _avg_len(fs, f_hz, average_s)
    zf = np.convolve(z, np.ones(L) / L, mode="valid")
    return float(2.0 * np.mean(np.abs(zf)))


def tone_phase(x: np.ndarray, fs: float, f_hz: float, average_s: float | None = None) -> float:
    n = np.arange(x.size, dtype=np.float64)
    z = x * np.exp(-1j * 2.0 * np.pi * f_hz * n / fs)
    L = _avg_len(fs, f_hz, average_s)
    zf = np.convolve(z, np.ones(L) / L, mode="valid")
    return float(np.angle(np.mean(zf)))


def envelope(x: np.ndarray, fs: float, smooth_s: float) -> np.ndarray:
    L = max(1, int(round(smooth_s * fs)))
    return np.convolve(np.abs(x), np.ones(L) / L, mode="same")


def xcorr_peak_lag(a: np.ndarray, b: np.ndarray, max_lag: int, center: int = 0) -> tuple[int, float]:
    """Lag k maximizing |sum a[n]*b[n+k]| over |k-center|<=max_lag; returns (k, value). FFT based."""
    n = a.size + b.size
    if n < 2:
        raise ValueError("empty correlation input")
    nfft = 1 << (int(np.ceil(np.log2(n))))
    A = np.fft.rfft(a, nfft)
    B = np.fft.rfft(b, nfft)
    c = np.fft.irfft(np.conj(A) * B, nfft)      # c[k] = sum a[n] b[n+k]
    lags = np.arange(center - max_lag, center + max_lag + 1)
    vals = c[lags % nfft]
    i = int(np.argmax(np.abs(vals)))
    return int(lags[i]), float(vals[i])


def kaiser_sinc_interpolate(y: np.ndarray, positions: np.ndarray, half_width: int, beta: float) -> np.ndarray:
    """Evaluate the band-limited interpolant of y at fractional sample ``positions``.

    Out-of-range taps read as zero. Exact at integer positions (sinc(0)=1,
    others 0), so a unit ratio with zero delay is the identity.
    """
    y = np.asarray(y, dtype=np.float64)
    pos = np.asarray(positions, dtype=np.float64)
    base = np.floor(pos).astype(np.int64)
    frac = pos - base
    out = np.zeros(pos.size, dtype=np.float64)
    pad = half_width + 2
    ypad = np.concatenate([np.zeros(pad), y, np.zeros(pad)])
    offset = pad
    valid_lo, valid_hi = 0, ypad.size - 1
    # Kaiser window as a function of continuous distance d in samples (|d| <= half_width).
    i0_beta = np.i0(beta)
    chunk = 4096
    k = np.arange(-half_width + 1, half_width + 1, dtype=np.float64)  # taps base-hw+1 .. base+hw
    for s in range(0, pos.size, chunk):
        e = min(pos.size, s + chunk)
        b = base[s:e]
        f = frac[s:e]
        d = k[None, :] - f[:, None]                       # distance from tap to position
        sinc = np.sinc(d)
        # Exact identity at integer positions: np.sinc(n) for integer n != 0 is ~1e-16, not 0.
        integer = d == np.round(d)
        sinc = np.where(integer, np.where(d == 0.0, 1.0, 0.0), sinc)
        arg = np.clip(1.0 - (d / half_width) ** 2, 0.0, 1.0)
        w = np.i0(beta * np.sqrt(arg)) / i0_beta
        idx = b[:, None] + k[None, :].astype(np.int64) + offset
        inside = (idx >= valid_lo) & (idx <= valid_hi)
        idx = np.clip(idx, valid_lo, valid_hi)
        out[s:e] = np.sum(np.where(inside, ypad[idx], 0.0) * sinc * w, axis=1)
    return out



def _pilot_delay(ref_hp, cap_hp, stim, role, ratio, cfg, guard, polarity=None):
    """Return (polarity, coarse_lag, delay_samples) for one pilot burst.

    Coarse search: heavily smoothed envelope cross-correlation (±guard*3) gives a
    centre within a few ms; the signal cross-correlation then picks the integer
    lag within ±half the two-tone recurrence (1/gcd of the pilot tones) around
    that centre; the first pilot tone's phase difference gives the sub-sample
    part. Delay is positive when the capture lags the reference.
    """
    fs = float(stim.sample_rate_hz)
    seg = stim.segment(role)
    tones = [t.freq_hz for t in seg.tones]
    f1 = tones[0]
    if len(tones) > 1:
        g = np.gcd.reduce([int(round(f)) for f in tones])
        recurrence = int(round(fs / g))
    else:
        recurrence = int(round(fs / f1))
    ps = _window(stim, role, cfg.pilot_trim_s)
    m0 = max(0, ps[0] - guard * 4)
    m1 = min(ref_hp.size, ps[1] + guard * 4)
    positions = np.arange(m0, m1, dtype=np.float64) / ratio
    cap_r = kaiser_sinc_interpolate(cap_hp, positions, cfg.sinc_half_width, cfg.kaiser_beta)
    ref_seg = ref_hp[m0:m1]
    env_ref = envelope(ref_seg, fs, cfg.coarse_envelope_s)
    env_cap = envelope(cap_r, fs, cfg.coarse_envelope_s)
    centre, _ = xcorr_peak_lag(env_ref - env_ref.mean(), env_cap - env_cap.mean(), guard * 3)
    lag, val = xcorr_peak_lag(ref_seg, cap_r, recurrence // 2, center=centre)
    if polarity is None:
        polarity = 1 if val >= 0 else -1
    a, b = ps[0] - m0, ps[1] - m0
    ph_ref = tone_phase(ref_seg[a:b], fs, f1, cfg.demod_average_s)
    ph_cap = tone_phase(float(polarity) * cap_r[a + lag:b + lag], fs, f1, cfg.demod_average_s)
    period = fs / f1
    dphi = float(np.angle(np.exp(1j * (ph_cap - ph_ref))))   # wrapped to (-pi, pi]
    fine = -dphi / (2.0 * np.pi) * period                      # a lagging capture has lower phase
    return polarity, int(lag), float(lag + fine)



def fit_tone_scale(x: np.ndarray, fs: float, freqs: list[float], r0: float, span: float = 50e-6, iters: int = 60) -> float:
    """Maximum-likelihood style estimate of a common frequency scale ``r`` for a multi-tone burst.

    For a candidate r the tone amplitudes/phases are solved by linear least
    squares (columns cos/sin(2*pi*f*r*n/fs) for every f); the residual energy is
    minimised over r by golden-section search in [r0*(1-span), r0*(1+span)].
    Because every tone is in the model there is no leakage bias between tones
    (the weakness of single-tone demodulation with a boxcar average).
    """
    x = np.asarray(x, dtype=np.float64)
    n = np.arange(x.size, dtype=np.float64) / fs

    def cost(r: float) -> float:
        cols = []
        for f in freqs:
            w = 2.0 * np.pi * f * r * n
            cols.append(np.cos(w))
            cols.append(np.sin(w))
        A = np.stack(cols, axis=1)
        coef, *_ = np.linalg.lstsq(A, x, rcond=None)
        e = x - A @ coef
        return float(e @ e)

    a, b = r0 * (1.0 - span), r0 * (1.0 + span)
    gr = (np.sqrt(5.0) - 1.0) / 2.0
    c = b - gr * (b - a)
    d = a + gr * (b - a)
    fc, fd = cost(c), cost(d)
    for _ in range(iters):
        if fc < fd:
            b, d, fd = d, c, fc
            c = b - gr * (b - a)
            fc = cost(c)
        else:
            a, c, fc = c, d, fd
            d = a + gr * (b - a)
            fd = cost(d)
    return float(0.5 * (a + b))


# --- main pipeline ------------------------------------------------------------

def _window(stim: Stimulus, role: str, trim_s: float) -> tuple[int, int]:
    seg = stim.segment(role)
    fs = stim.sample_rate_hz
    a = int(round((seg.start_s + trim_s) * fs))
    b = int(round((seg.end_s - trim_s) * fs))
    return a, b


def align(reference: np.ndarray, capture: np.ndarray, stim: Stimulus, cfg: EvaluatorConfig | None = None):
    """Estimate alignment parameters and return (estimate, corrected_capture, reference_hp)."""
    cfg = cfg or EvaluatorConfig()
    fs = float(stim.sample_rate_hz)
    ref = np.asarray(reference, dtype=np.float64)
    cap = np.asarray(capture, dtype=np.float64)
    pilot_hz = stim.segment("pilot_start").tones[0].freq_hz
    cal_hz = stim.segment("calibration").tones[0].freq_hz

    # 1. DC report + identical high-pass
    w = int(round(cfg.dc_window_s * fs))
    dc_ref = float(np.mean(ref[:w]))
    dc_cap = float(np.mean(cap[:w]))
    ref_hp = dc_highpass(ref, fs, cfg.dc_highpass_hz, dc_ref)
    cap_hp = dc_highpass(cap, fs, cfg.dc_highpass_hz, dc_cap)

    # 3. Clock ratio from pilots (estimate on both so estimator bias cancels)
    ps = _window(stim, "pilot_start", cfg.pilot_trim_s)
    pe = _window(stim, "pilot_end", cfg.pilot_trim_s)
    f_ref_s = estimate_tone_frequency(ref_hp[ps[0]:ps[1]], fs, pilot_hz, cfg.demod_average_s)
    f_ref_e = estimate_tone_frequency(ref_hp[pe[0]:pe[1]], fs, pilot_hz, cfg.demod_average_s)
    # capture pilot windows: widen search region because of unknown delay/ratio (use ±max 1% of window)
    guard = int(round(0.030 * fs))
    f_cap_s = estimate_tone_frequency(cap_hp[ps[0] + guard:ps[1] - guard], fs, pilot_hz, cfg.demod_average_s)
    f_cap_e = estimate_tone_frequency(cap_hp[pe[0] + guard:pe[1] - guard], fs, pilot_hz, cfg.demod_average_s)
    # refine with a joint multi-tone least-squares scale fit (no inter-tone leakage bias)
    pilot_freqs = [t.freq_hz for t in stim.segment("pilot_start").tones]
    rr_s = fit_tone_scale(ref_hp[ps[0]:ps[1]], fs, pilot_freqs, 1.0)
    rr_e = fit_tone_scale(ref_hp[pe[0]:pe[1]], fs, pilot_freqs, 1.0)
    rc_s = fit_tone_scale(cap_hp[ps[0] + guard:ps[1] - guard], fs, pilot_freqs, f_cap_s / f_ref_s)
    rc_e = fit_tone_scale(cap_hp[pe[0] + guard:pe[1] - guard], fs, pilot_freqs, f_cap_e / f_ref_e)
    r_s = rc_s / rr_s
    r_e = rc_e / rr_e
    f_cap_s, f_cap_e = pilot_hz * rc_s, pilot_hz * rc_e
    f_ref_s, f_ref_e = pilot_hz * rr_s, pilot_hz * rr_e
    ratio = 0.5 * (r_s + r_e)
    drift_ppm = float((r_e - r_s) * 1e6)

    # 2./4. polarity and delay from the start pilot on the ratio-only corrected capture; end pilot as check
    polarity, coarse, delay_samples = _pilot_delay(ref_hp, cap_hp, stim, "pilot_start", ratio, cfg, guard)
    _, _, delay_end = _pilot_delay(ref_hp, cap_hp, stim, "pilot_end", ratio, cfg, guard, polarity=polarity)

    # 5. single-pass resample of raw (hp) capture onto the reference grid
    m = np.arange(ref.size, dtype=np.float64)
    corrected = kaiser_sinc_interpolate(cap_hp, (m + delay_samples) / ratio, cfg.sinc_half_width, cfg.kaiser_beta)
    corrected *= float(polarity)

    # 6. gain from calibration tone
    cs = _window(stim, "calibration", cfg.pilot_trim_s)
    g = tone_amplitude(corrected[cs[0]:cs[1]], fs, cal_hz, cfg.demod_average_s) / tone_amplitude(ref_hp[cs[0]:cs[1]], fs, cal_hz, cfg.demod_average_s)
    corrected = corrected / g

    est = AlignmentEstimate(
        dc_reference=dc_ref, dc_capture=dc_cap, polarity=polarity,
        pilot_freq_ref_start_hz=f_ref_s, pilot_freq_ref_end_hz=f_ref_e,
        pilot_freq_cap_start_hz=f_cap_s, pilot_freq_cap_end_hz=f_cap_e,
        clock_ratio=float(ratio), clock_ratio_drift_ppm=drift_ppm,
        delay_coarse_samples=coarse, delay_samples=float(delay_samples), delay_seconds=float(delay_samples / fs),
        delay_end_check_samples=delay_end, gain=float(g),
    )
    return est, corrected, ref_hp


def null_metrics(reference: np.ndarray, candidate: np.ndarray, fs: float, cfg: EvaluatorConfig | None = None) -> NullMetrics:
    cfg = cfg or EvaluatorConfig()
    r = np.asarray(reference, dtype=np.float64)
    c = np.asarray(candidate, dtype=np.float64)
    res = r - c
    sig_rms = float(np.sqrt(np.mean(r * r)))
    res_rms = float(np.sqrt(np.mean(res * res)))
    peak = float(np.max(np.abs(res))) if res.size else 0.0
    if sig_rms > 0 and float(np.std(c)) > 0:
        corr = float(np.corrcoef(r, c)[0, 1])
    else:
        corr = None
    # per-band residual relative to signal in band
    R = np.fft.rfft(r * np.hanning(r.size))
    E = np.fft.rfft(res * np.hanning(res.size))
    freqs = np.fft.rfftfreq(r.size, 1.0 / fs)
    bands: dict[str, float | None] = {}
    edges = cfg.band_edges_hz
    for lo, hi in zip(edges[:-1], edges[1:]):
        sel = (freqs >= lo) & (freqs < hi)
        pr = float(np.sum(np.abs(R[sel]) ** 2))
        pe = float(np.sum(np.abs(E[sel]) ** 2))
        key = f"{lo:g}-{hi:g}Hz"
        bands[key] = None if pr <= 0 or pe <= 0 else float(10.0 * np.log10(pe / pr))
    return NullMetrics(
        n_samples=int(r.size), signal_rms=sig_rms, residual_peak_abs=peak, residual_peak_dbfs=_db(peak),
        residual_rms=res_rms, residual_rms_db_re_signal=(None if sig_rms <= 0 else _db(res_rms / sig_rms)),
        correlation=corr, per_band_residual_db=bands, max_abs_residual_exact_zero=bool(peak == 0.0),
    )


def residual_spectrum(reference: np.ndarray, candidate: np.ndarray, fs: float, nfft: int = 8192) -> tuple[np.ndarray, np.ndarray]:
    """Welch-style averaged residual spectrum (dB re 1.0 peak-sine) for CSV export."""
    res = np.asarray(reference, dtype=np.float64) - np.asarray(candidate, dtype=np.float64)
    win = np.hanning(nfft)
    hop = nfft // 2
    acc = np.zeros(nfft // 2 + 1)
    cnt = 0
    for s in range(0, res.size - nfft + 1, hop):
        X = np.fft.rfft(res[s:s + nfft] * win)
        acc += np.abs(X) ** 2
        cnt += 1
    if cnt == 0:
        return np.fft.rfftfreq(nfft, 1.0 / fs), np.full(nfft // 2 + 1, -np.inf)
    mag = np.sqrt(acc / cnt) * (2.0 / np.sum(win))
    with np.errstate(divide="ignore"):
        db = 20.0 * np.log10(np.maximum(mag, 1e-300))
    return np.fft.rfftfreq(nfft, 1.0 / fs), db
