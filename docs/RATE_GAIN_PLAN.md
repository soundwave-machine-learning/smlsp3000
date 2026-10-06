# Rate, gain, converter and delay plan

Revision: planning V1 · 2026-10-06

Status: DRAFT PLANNING CONTRACT. Documentation creation authorized; implementation and release not authorized.

## Four rate domains

| Host Hz | SP / host (on provisional clock) | MPC / host |
|---|---|---|
| 44100 | 3125/5292 | 1 |
| 48000 | 625/1152 | 147/160 |
| 88200 | 3125/10584 | 1/2 |
| 96000 | 625/2304 | 147/320 |
| 176400 | 3125/21168 | 1/4 |
| 192000 | 625/4608 | 147/640 |

SP nominal26.04k is documentary VERIFIED; exact20MHz/768=26041.666… Hz is PROVISIONAL. Candidate mux208333.333… Hz and slot4.8µs are arithmetic on that premise, not measured. MPC44100 is VERIFIED;64fs ADC modulator and8fs DAC interpolation are internal converter architecture, not independent product controls. Host rates listed are research candidate support; actual native target support is G-09. Proxy rate/oversampling is UNSET and selected by convergence/alias budget G-08. Proxy must carry SP images that reach the MPC path; resampling directly from SP through a perfect reconstruction filter would invalidate this goal.

## Calibration units and formulas

Use V_peak internally for analog amplitudes; report V_rms for sine measurements. Digital full-scale normalization and code endpoints must be documented for each converter. For a calibrated interface `V_peak = normalized_sample × volts_peak_per_normalized_unit`. `V_rms = V_peak / sqrt(2)` only for a sine. Product trim `G = 10^(dB/20)` multiplies physical voltage at its named boundary. Machine FS volts and code transfer (offset/encoding/asymmetry) are measured assets; null gains come from calibration tone, never per-program fitting.

SP input source calibration → selected0/+20/+40dB preamp → measured analog boundaries → converter code limit → hold/output path volts. R10 scales those volts through the chosen analog connection/MPC record-level setting; there is no historically meaningful unity digital link. MPC LO/MID/HI sensitivity at max pot is printed−18/−38/−58dBs,0dBs=0.775Vrms; the computed97.6/9.76/0.976mVrms sensitivity is **not** ADC full-scale voltage. Record reference level, pot law/position and FS relationship remain measured unknowns. Output `6dBm/600Ω` sign/meaning is unresolved; provisional+6 interpretation cannot be a factory calibration. Input/output FS variables and interstage default remain UNSET.

## Clip boundary inventory

| Boundary | Domain | Current knowledge | Required resolution |
|---|---|---|---|
| SP preamp/AA | volts at proxy | Gain steps supported; clip voltage, symmetry/recovery unknown | CHAIN-EXP-002/005/019 |
| SP ADC | 12-bit code range | Hard code limit candidate; physical input FS/offset/encoding unknown | CHAIN-EXP-002/005 |
| SP DAC/output | hold/output volts | Full-scale code not proof of amplifier rail behavior | CHAIN-EXP-003/004/005 |
| MPC input amp | volts at proxy | Sensitivity known; location before/after pot and overload unknown | CHAIN-EXP-009/020 |
| MPC ADC | converter FS/code | 18-bit architecture; modulator overload/recovery unknown | CHAIN-EXP-009; AUD-C05 |
| MPC digital arithmetic | stored/mix code | Reduction/mix scaling unknown; no wrap/saturate guess | CHAIN-EXP-008/010 |
| MPC DAC/output | calibrated volts | 18-bit architecture; gain/poles/ceiling unknown | CHAIN-EXP-010/020 |

Do not use floating-point overflow as clipping. Analog, converter and digital boundaries remain separate. Clamp oversampling is implementation and must preserve intended physical boundary; overload recovery is measured before driven product modes. Clip meter semantics and inter-sample-peak policy are chosen G-08. Final host output trim alone is not a limiter. Quantization error is inherent, not added noise; no deliberate SP dither unless measured evidence/decision changes CHAIN-DEC-015.

## Delay accounting

Track algorithmic delay from host/proxy SRC, scheduling, hold/interpolation and any clamp oversampling; report integer host alignment exactly for implemented route. Analog AA/output LF/HF group delay is frequency-dependent response, not a scalar zero-latency promise. Source estimates (SP sampling/hold ≤1.5 samples; converter delays UNKNOWN) are not final latency values. No lookahead is supported by the mechanisms. G-08 freezes allowed latency/CPU tradeoff after reference fidelity; G-09 tests host reporting and bypass alignment.
