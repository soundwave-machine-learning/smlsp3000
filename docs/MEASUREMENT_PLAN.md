# Hardware campaign, capture validity and provenance

Revision: planning V1 · 2026-10-06

Status: DRAFT PLANNING CONTRACT. Documentation creation authorized; implementation and release not authorized.

## Hardware entry conditions

One identified stock vintage SP-1200 and stock MPC3000, calibrated interface supporting analog192kHz/24-bit plus44.1k S/PDIF source, true-RMS1kHz voltage measurement, documented sample import/export routes and operator access. Unit IDs, serials, board/revision, OS/firmware, repair/mod status must be recorded first. Aftermarket output/amp/clock/filter changes are MODIFIED, excluded from stock fit; repaired/recapped unit noted; replacement supply accepted as stock audio only with verified rails. No unit is assumed available now.

Instrument loopback response/noise/THD+N must be known; source asks20dB better than best measured figure. If that cannot be achieved, record uncertainty/floor and block any conclusion below instrument capability. Calibrate interface input/output volts-per-dBFS at1kHz, preserve loopback at start and end. Record cable/load/TS vs contact breakout and pot photos. Machines free-run, interface internal clock; pilots estimate one ratio per capture. Warm-up threshold is UNKNOWN: establish stability from repeat drift and freeze criterion before accepted takes. Do not open or probe powered hardware without separately authorized operator procedure; documentary tracing and external captures can proceed under their own scope.

## Capture and source schedule

Analog captures192k/24; SP stimuli ≤2.3s **total including pilot/settling/tail**, below2.5s per sound. Original10s sweep must be segmented into independently valid SP sounds; pilot durations/frequencies and segment overlap are fixed during S2 preparation. Verify low-frequency cycles and high-Q settling within the budget; if impossible choose alternate steady-state measurements with documented criterion, not concatenated invalid impulse data. No claim that hardware streams a full mix. MPC standard-memory excerpts stay within documented supported duration/configuration. Three takes per configuration estimate repeatability; not an automatic PASS.

| Signal | Rate / depth | Peak | Duration | Channels |
|---|---|---|---|---|
| Log sweep 10 Hz – 90 kHz | 192 k / 24 | −20, −10, −3 dB re machine FS | 10 s (SP: ≤ 2.3 s segments, see note) | Mono; L-only, R-only for MPC |
| Stepped sine 20 Hz – 20 kHz, 1/6 octave | 192 k / 24 | −60 … +6 dB re FS in 3 dB steps at 100 Hz, 1 kHz, 10 kHz | 1 s per step | Mono / each channel |
| 100 Hz, 1 kHz, 10 kHz sines | 192 k / 24 | −1 dB re FS | 2 s | Mono / stereo |
| SMPTE IMD 60 Hz + 7 kHz 4:1 | 192 k / 24 | −3, −10 dB | 2 s | Mono / stereo |
| CCIF IMD 19 + 20 kHz (MPC); 10 + 11 kHz (SP, in band) | 192 k / 24 | −3, −10 dB | 2 s | Mono / stereo |
| Multitone, 31 tones log-spaced, random phase, seeded | 192 k / 24 | −12 dB crest-normalized | 2 s | Mono / stereo |
| Music-like multitone (pink-weighted) | 192 k / 24 | −12 dB | 2 s | Stereo |
| Impulse, band-limited to 80 kHz | 192 k / 24 | −6 dB | 0.5 s | Mono / each channel |
| Square 100 Hz and 1 kHz; single pulse | 192 k / 24 | −6 dB | 1 s | Mono |
| Silence | — | — | 2 s | — |
| Low-level sine 1 kHz | 192 k / 24 | −60, −70, −80 dB re FS | 2 s | Mono |
| White noise, pink noise (seeded) | 192 k / 24 | −12 dB RMS-normalized | 2 s | Mono; correlated, uncorrelated, anti-phase stereo for MPC |
| Slow ramp across full code range | 192 k / 24 (analog) and synthetic sample data (digital) | Full scale | 2 s | Mono |
| Transient drum loop, bass-heavy mix, bright mix, dense master, dynamic premaster | 192 k / 24 source | As mastered and −12 dB | SP: 2.3 s excerpts; MPC: up to 10 s stereo with standard memory | Mono (SP), stereo (MPC) |

Note: the SP-1200 can only pass audio by recording it, and one sound is limited to 2.5 s. Every SP stimulus is therefore a ≤ 2.3 s segment with pilot tones. A full mix cannot be streamed through the hardware.

**Measurement categories:** LINEAR (frequency, phase, group delay, channel matching, crosstalk); LEVEL (gain curve, clip onset, output ceiling, overload recovery); DISTORTION (THD vs level and frequency, harmonic balance, SMPTE, CCIF, multitone); NOISE (idle spectrum, loaded noise, DC, hum, spurs); DIGITAL (quantizer transfer, low-level behavior, images, aliasing, truncation vs rounding); TRANSIENT (impulse, square, recovery); STEREO (L-only, R-only, dual mono, correlated, anti-phase).

## Differential isolation and output coverage

SP input path: record each stimulus/gain then export12-bit words, verify file encoding/checksum. SP output: load synthetic words, play unity/max-level setting as measured and capture ch3, ch5, ch7 with confirmed contacts, plus MIX OUT; compare same sample to obtain filter ratios with calibration and source lineage. Jack contact mapping C-03 is resolved by schematic/external verification before treating a tap as filtered/unfiltered. Capture paired channels for slot skew separately from capture-time offsets.

MPC input: sample analog L/R per gain/pot then save16-bit data. S/PDIF receiver/storage: compare known44.1k16-bit patterns exactly. It does not expose internal18-bit ADC thresholds. DAC/output: load synthetic16-bit sounds to mainL/R and one individual pair, capture complex response/levels. Main/individual and phones are not interchangeable. Test de-emphasis state under normal selected route; emphasized S/PDIF use is P2 unless included. Record analog input/full roundtrip to test composition with outputs.

Cascade: SP output→MPC input at recorded calibration/record-level settings after CHAIN-EXP-005/009; measure volts/node, overload and image admission. Actual physical capture is staged recording/playback; software continuity is an abstraction outside sampler memory behavior. DRY/SP/MPC/SP→MPC comparisons are necessary for contribution decisions; reverse order is optional informational. Analog audio fullscale never comes solely from sensitivity or nominaldBm.

## Bandwidth and identifiability limits

192kHz captures contain frequencies below96kHz. A predicted208.33kHz mux spur cannot be directly observed there; a >416.67kHz sample rate with adequate analog bandwidth or appropriate wideband spectral instrument is required for direct study. This calculation is a sampling-limit clarification, not new hardware evidence. Otherwise label out-of-band spur NOT OBSERVABLE and keep question scoped/open; do not claim no spur. Near96k capture edges carry uncertainty; choose valid analysis band from instrument characterization. In-band spur/noise study remains mandatory.

SP12-bit raw-code comparisons can target exact agreement for identifiable transfer rules. MPC analog input exported16-bit data may not uniquely identify18-bit internal reduction; report identifiable composite response and unresolved mechanism. No ambiguous distinction between analog noise, dither and truncation is promoted to fact without an isolating measurement. Driven overload recovery must be observed before approving driven product modes; deeper P2 model only if evidence requires it.

## Fit versus validation split and artifact contract

Freeze separate capture IDs before fitting: sweep/multitone/ramp/stepped levels as FIT; alternate-frequency levels, impulses/noise/held-out low-level sines/music as VALIDATION, maintaining required stimulus coverage. Do not put repeated takes of one source condition in both sets without documenting leakage risk. Hardware-self-null repeats establish threshold basis, separate from fit optimization.

Naming preserves source pattern `{machine}_{unit}_{category}_{signal}_{path}_{level}_{take}.wav` with sidecar; add artifact-class prefix where needed to enforce §43 labels. Sidecar includes unit/session, revision/mod/OS, warm-up/temp, interface calibration/uncertainty, cables/load, contact/path/pot photo, source input hash, sample rate/depth/channels, gain/level, pilots/clock estimate, capture/raw hash, repeat ID, FIT/VALIDATION/self-null purpose and evidence class. Manifest SHA-256 contains each stimulus/capture/sidecar. Raw captures never overwritten by aligned or level-matched derivatives.

Planned repository-relative directories: reference/hardware/sp1200/unit_001 and mpc3000/unit_001 with metadata/calibration/linear/nonlinear/noise/digital/stereo/transient; reference/hardware/cascade; reference/sources; research/sim/fit/validation/listening. These directories do not contain measurements yet. Store large artifacts in the future approved durable evidence route, with hashes and regeneration instructions; do not commit copyrighted manual scans or large audio blindly. Production unit can be renamed from unit_001 only with consistent manifest/state updates.
