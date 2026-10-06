# Architecture, replaceable blocks and state

Revision: execution V1 (Sprint 1) · 2026-10-06 · supersedes planning V1

Status: EXECUTION IN PROGRESS. R0–R16 not implemented; Sprint 1 foundation layout recorded below.

## Ownership and dependency direction

Proposed architecture. Sprint 1 implemented only the analysis/evidence foundation (no R-block): package `smlsp3000/` — `hashing` (SHA-256 files/arrays, manifests), `schemas` (frozen artifact-class/dataset-role vocabularies; experiment-result, unit, capture-sidecar, machine-asset and research-configuration records with explicit UNSET), `wavio` (PCM 16/24/32 and float32 WAV), `stimuli` (analytic continuous-time synthetic truth), `nullframework` (pilot/alignment/null evaluator), `environment` (provenance), `runner` (experiments by repository ID), `experiments/exp016`; `tests/` (unittest); `tools/check_repo_integrity.py`. Future reference blocks are intended to live under `smlsp3000/reference/` (R0–R16 as separately replaceable modules consuming MachineAsset records) and the production engine in a separately decided stack (G-08/G-09); neither exists yet. `Configuration and immutable machine assets → shared reference/production engines → tests/offline renderer/plugin adapter → UI`. UI depends on parameter definitions and meters, never the reverse. Research import/fit tools emit reviewed versioned assets; runtime does not fetch sources or fit itself. Do not duplicate DSP in wrapper/GUI or create a second sonic pipeline.

An engine instance owns one logical chain: global shared clocks and per-channel signal state; no global mutable buffers. MachineParameters and provenance are immutable for a prepared run; ProductParameters snapshots update through a bounded lock-free handoff; ResearchConfiguration is present only in research builds. Reference and production engines share units/routing/control semantics while numerical implementations differ only by documented G-08-validated substitution. Offline renderer records input/config/assets/source commit hashes.

## Interface contracts (semantic, not language signatures)

| Interface | Inputs | Outputs / ownership | Failure and lifetime |
|---|---|---|---|
| Prepare | host Hz, maximum block/channels, immutable machine asset/version, product state, explicit research config where permitted | validated prepared engine, preallocated buffers and latency/metadata | non-real-time; missing calibration/strategy/unsupported route returns explicit invalid config; no guessed defaults |
| Reset | documented stream start and common clock phase | cleared FIR/IIR/hold histories, phase/count, meters and deterministic state | bounded; no new memory; preserves immutable settings |
| Process | channel buffers, frames≤prepared maximum, bounded parameter event schedule | audio plus bounded clip/peak meters; existing allocated memory | real-time, no files/locks/allocations; invalid input policy decided G-08 |
| Drain offline | finite input end | tail frames and exact delay metadata | host wrapper does not do offline filesystem work on audio thread |
| Latency query | prepared route, rate and kernel version | integer implementation alignment delay; separate measured group-delay descriptor | no claim to cancel analog phase dispersion |
| Diagnostic tap | reference block output, code grid and timestamp | in-memory bounded buffers copied/written off-thread by harness | disabled in release process; never audio-thread I/O |
| State serialization | versioned ProductParameters and selected immutable calibration identity | portable state record with migration result | non-audio thread; cannot serialize research strategies into factory presets |

## Every replaceable block

| Block | Function / domain | Signal-state ownership | Provisional boundary / replacement | Evidence / test |
|---|---|---|---|---|
| R0 | Input calibration (dBFS → volts); Host | None per signal channel; scheduler histories separate | Decision → Measured calibration | CHAIN-EXP-005 |
| R1 | Host → analog-proxy resampler; Host → proxy | FIR per signal channel; scheduler histories separate | Implementation → — | CHAIN-EXP-016 |
| R2 | SP input gain (0/+20/+40 dB) with explicit analog clamp; Proxy | None per signal channel; scheduler histories separate | Gain STRONGLY SUPPORTED; clamp UNKNOWN → Measured gain curve | CHAIN-EXP-002, CHAIN-EXP-005 |
| R3 | SP anti-alias filter; Proxy | IIR per signal channel; scheduler histories separate | PLACEHOLDER coefficients → SPICE-derived or measured response | CHAIN-EXP-019, CHAIN-EXP-002 |
| R4 | SP sampler (ideal sample-and-hold); Proxy → 26 041.67 Hz | None per signal channel; scheduler histories separate | STRONGLY SUPPORTED → Aperture model if measured | CHAIN-EXP-001, CHAIN-EXP-002 |
| R5 | SP 12-bit quantizer with code clamp; SP | None per signal channel; scheduler histories separate | VERIFIED word length; rounding rule PLACEHOLDER → Measured transfer | CHAIN-EXP-002 |
| R6 | SP machine domain; SP | None at unity per signal channel; scheduler histories separate | Identity at unity PROVISIONAL → Tuned-playback block (extreme mode) | CHAIN-EXP-003 |
| R7 | SP DAC + zero-order hold; SP → proxy | Hold per signal channel; scheduler histories separate | VERIFIED hold; full-period PROVISIONAL → Measured hold fraction | CHAIN-EXP-003 |
| R8 | SP output filter, selected: none / ch 5–6 / ch 3–4; Proxy | IIR per signal channel; scheduler histories separate | PLACEHOLDER coefficients → SPICE or measurement | CHAIN-EXP-019, CHAIN-EXP-004 |
| R9 | SP output stage (gain, coupling pole); Proxy | 1 pole per signal channel; scheduler histories separate | PLACEHOLDER → Measurement | CHAIN-EXP-004, CHAIN-EXP-005 |
| R10 | Interstage calibrated gain; Proxy | None per signal channel; scheduler histories separate | UNSET (P0) → Measured levels | CHAIN-EXP-005, CHAIN-EXP-009, CHAIN-EXP-012 |
| R11 | MPC input stage (switch, record level, coupling pole) with explicit clamp; Proxy | 1 pole per signal channel; scheduler histories separate | Sensitivity VERIFIED; rest PLACEHOLDER → Extraction or measurement | CHAIN-EXP-009, CHAIN-EXP-020 |
| R12 | MPC ADC: decimation to 44.1 kHz, full-scale clamp, 18-bit; Proxy → 44.1 kHz | FIR per signal channel; scheduler histories separate | Architecture VERIFIED; response PLACEHOLDER → Datasheet response, measured overload | CHAIN-EXP-009 |
| R13 | MPC word-length reduction 18 → 16 bit; 44.1 kHz | None per signal channel; scheduler histories separate | Method UNKNOWN; research switch truncation / rounding → Result of low-level test | CHAIN-EXP-008 |
| R14 | MPC machine domain; 44.1 kHz | None per signal channel; scheduler histories separate | Identity PLACEHOLDER → Measured arithmetic | CHAIN-EXP-008, CHAIN-EXP-010 |
| R15 | MPC DAC: 8× interpolation, 18-bit, I/V, analog low-pass, coupling pole; 44.1 kHz → proxy | FIR + IIR per signal channel; scheduler histories separate | Architecture VERIFIED; responses PLACEHOLDER → Datasheet, extraction, measurement | CHAIN-EXP-010, CHAIN-EXP-020 |
| R16 | Analog-proxy → host resampler, output trim; Proxy → host | FIR per signal channel; scheduler histories separate | Implementation → — | CHAIN-EXP-016 |

## Scheduler and stereo state

A shared rational/high-precision scheduler owns absolute input time, SP and MPC next-event phase/counters and proxy resampler history. Exact SP constant is a versioned provisional rational20MHz/768 until CHAIN-EXP-001/019 closure, not literal truncated26041.6667 accumulated forever. MPC clock44100 is distinct. Processing chunks never restart clock/hold at block boundaries. R4's source `None` describes ideal physical signal memory, not implementation scheduler state (AUD-C08). R7 stores held code per channel. Each filter delay line, coupling state and meter accumulator is per-channel; L/R share sample instants and nominal coefficient assets in linked mode, never each other's input/state. Equal input with equal state gives identical output. Different channels do not bleed unless measured/approved coupling is added.

For research slot skew, source capture offset and DAC multiplex playback skew are separate terms; they are not arbitrary random phase or independent clocks. Slot experiment is not included in release. Literal MIX OUT is mono and cannot be renamed a stereo path. Unknown summing topology blocks its implementation. Synthetic continuous-time fixtures define cross-rate input; input reconstruction error/quantizer-boundary divergence is budgeted separately, never solved by removing the machine quantizer.

## Numerical and real-time policy

Reference prioritizes traceability and offline precision; float format/order/kernel/proxy rate is an S1/S6 decision, not specified hardware behavior. Product may optimize to lower precision only after G-08 bounds. Historical SP aliases/images remain; numerical SRC or low-rate analog clamps must not add uncontrolled aliasing. Real-time code uses prepared bounded buffers, safe coefficients/denormal policy and no asynchronous sonic state. State reload prepares a replacement snapshot outside process; the approved transition policy defines reset/crossfade/routing behavior and latency, with no hidden mix normalization.

Reset and host-rate changes: prepare/reprepare off-thread, validate new kernel latency, reset all time/history coherently, preserve product settings only when valid for new asset/rate. Continuous automation vs initialization-only parameters are frozen in PARAMETERS before S6. DSP recovery on bad state/nonfinite input is bounded and observable under G-08 policy. No production null threshold is silently shared with hardware-fit or cross-platform criteria.

## Bypass, latency and errors

Plugin bypass preserves documented fixed alignment delay and otherwise passes dry data. SP bypass removes R2–R9 machine behavior including its quantizer/grid; MPC bypass removes R11–R15 behavior including storage reduction. Surrounding calibration/routing must be defined for each case at G-07; no double conversion. Reference block bypasses are diagnostic. Constant-delay compensation may be retained for switches only if explicitly documented; analog group-delay curves remain part of coloration. Unknown calibration fails physically scaled configuration; explicit normalized research skeleton is marked non-fidelity and cannot export a release asset. No hidden limiter or auto loudness matching is an error policy.
