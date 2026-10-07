# DSP changelog

Revision: execution V7 (Sprint 7) · 2026-10-07 · supersedes execution V6

Status: EXECUTION IN PROGRESS.

## Planning baseline — PLANNED, NOT IMPLEMENTED

2026-10-06: documented B reference superset R0–R16, four rate domains, physical gains/clamps, linked-dual-mono abstraction, unity pitch and replaceable uncertainties from researchV1. No DSP was written or executed. No audible behavior, code change, preset or binary is claimed.

Future executed entries must record date/implementation commit, changed block/parameter/asset versions, source/decision/requirement IDs, before/after actual behavior, metrics/regression impact, evidence paths and limitations. New calibration/hardware evidence updates confidence/decisions before product behavior changes. Do not rewrite historical research or create fake entries for planned sprints. Artifact labels and claim lanes remain separate.

## Sprint 1 — 2026-10-06 — NO DSP BEHAVIOUR

Implementation commit: recorded in docs/PROJECT_HANDOFF.md after the milestone commit. Changed blocks/parameters/assets: NONE. R0–R16 remain unimplemented; no machine asset exists; no quantizer, filter, hold, clamp or resampler of either machine was written. What was added is analysis tooling only (smlsp3000/: hashing, schemas, WAV I/O, analytic self-test stimuli, pilot/alignment/null evaluator; CHAIN-EXP-016 SIMULATION record). The evaluator's Kaiser-sinc interpolator and DC high-pass are measurement-side preprocessing with a recorded floor; they are not part of any machine model and carry no sonic claim. Audible behaviour: none claimed.

## Sprint 3 — 2026-10-07 — PROVISIONAL SP REFERENCE PATH (Track A, OWN-DEC-001..004)

Implementation commit: recorded in docs/PROJECT_HANDOFF.md after the milestone commit. Subsystem: `smlsp3000/reference/` (R1, R2, R3, R4, R5, R6, R7, R8, R9, R16 of the SP stage); asset `sp1200-track-a-provisional` v1 (model sp1200-provisional-1.0.0), research configuration `sp-track-a-research-config` v1, implementation sp1200-reference-impl-1.0.1.

| Block | Behaviour introduced | Reason / evidence | Status | Audible / behavioural consequence | Test coverage | Hardware-fit replacement point |
|---|---|---|---|---|---|---|
| R1/R16 | host ↔ proxy (×8) windowed-sinc resampling, cutoff at host Nyquist | IMPLEMENTATION (ENG-DEC-016) | ESTIMATE pending G-08 | none intended; images above host Nyquist removed as a recording interface would | VAL-010 line model includes |H(g)| | G-08 convergence (S6) |
| R2 | gain 0/+20/+40 dB as exact ratios × product trim; analog clamp INACTIVE | SP12-CLM-018 STRONGLY SUPPORTED; clip UNKNOWN | PROVISIONAL / UNVALIDATED AGAINST HARDWARE | level only; no preamp clipping | VAL-011 | CHAIN-EXP-002/005 |
| R3 | INACTIVE (identity) | OWN-DEC-002; coefficients UNKNOWN (RD-P0-01) | INACTIVE — does not represent the hardware | content above 13.02 kHz folds back unattenuated | VAL-009, CHAIN-EXP-017 | CHAIN-EXP-002/019 |
| R4 | ideal sampling at exact rational instants k·768/20e6 s | SP12-CLM-001/002 | PROVISIONAL clock | 26.04 kHz band limit and fold-back | VAL-008 (ratios), VAL-009 | CHAIN-EXP-001 |
| R5 | 12-bit code, ROUND_NEAREST default / FLOOR alternate, offset 0, clamp −2048..2047 | SP12-CLM-003 VERIFIED format; rule UNRESOLVED (OWN-DEC-003) | PROVISIONAL SOFTWARE DEFAULT | quantization error ≈ −72 dB re FS; hard clamp when driven | VAL-008, VAL-011, unit tests for both rules | CHAIN-EXP-002 |
| R6 | identity at unity pitch | CHAIN-DEC-004 | PROVISIONAL | none | VAL-018 | CHAIN-EXP-003 |
| R7 | full-period zero-order hold rendered band-limited to the proxy Nyquist (images preserved) | SP12-CLM-020 closed form; hold fraction UNKNOWN | PROVISIONAL | droop −2.22 dB at 10 kHz, images at k·fsp ± f (e.g. 16.04 kHz at −6.3 dB for 10 kHz) | VAL-010, CHAIN-EXP-017 | CHAIN-EXP-003 |
| R8 | route NONE_CH7_8 = identity; other routes NOT POPULATED (prepare rejects) | SP12-CLM-012 VERIFIED no filter; OWN-DEC-004 | PROVISIONAL; not the canonical output | unfiltered images | VAL-010 | CHAIN-EXP-004/019; G-07S |
| R9 | output gain 1.0 normalized; coupling INACTIVE; volts UNSET | SP12-CLM-023 UNKNOWN | ESTIMATE / UNSET | none | VAL-011 | CHAIN-EXP-004/005 |
| Stereo | linked dual mono (shared instants, per-channel state); research-only playback slot skew and capture offset, both off | CHAIN-DEC-005 PRODUCT ABSTRACTION | PROVISIONAL | no mismatch, no bleed | VAL-017 | CHAIN-EXP-007 |

Not introduced: any MPC block, noise, jitter, mismatch, sag, saturation, limiter, normalization, SSM filter, tuned playback, reverse order, MIX OUT. No hardware behaviour is claimed; the whole path is UNVALIDATED AGAINST HARDWARE.

## Sprint 4 — 2026-10-07 — PROVISIONAL MPC REFERENCE PATH (Track A, OWN-DEC-005..008)

Implementation commit: recorded in docs/PROJECT_HANDOFF.md after the milestone commit. Subsystem: `smlsp3000/reference/mpc3000.py` (R11, R12, R13, R14, R15 of the MPC stage with R1/R16); asset `mpc3000-track-a-provisional` v1 (model mpc3000-provisional-1.0.0), research configuration `mpc-track-a-research-config` v1, implementation mpc3000-reference-impl-1.0.1. SP implementation 1.0.3: exact per-residue tap tables (outputs bit-identical to 1.0.2).

| Block | Behaviour introduced | Reason / evidence | Status | Audible / behavioural consequence | Test coverage | Hardware-fit replacement point |
|---|---|---|---|---|---|---|
| R11 | switch gain LO/MID/HI = 1/10/100 from printed sensitivities; ideal dB trim ≤ 0 dB; analog clamp and coupling INACTIVE | MPC3K-CLM-007 VERIFIED text; FS/clip/pot law UNKNOWN | ESTIMATE / UNVALIDATED AGAINST HARDWARE | level only; no preamp clipping, no LF pole | VAL-013 | CHAIN-EXP-009/020 |
| R12 | TRANSPARENT: ideal band limitation at 22.05 kHz (implementation kernel, transition ≈ 2.2 kHz ESTIMATE) + ideal sampling at 44.1 kHz + 18-bit code (round-nearest representation) + converter clamp | OWN-DEC-005; AK5328 response UNKNOWN | PROVISIONAL SOFTWARE DEFAULT | content above 22.05 kHz removed (SP images above 22.05 kHz do not reach storage); nothing else; no overload recovery | VAL-013 lines/fold-back/stopband/clamp | CHAIN-EXP-009 / SRC-32 |
| R13 | 18→16 reduction ROUND_NEAREST default (⌊c/4+½⌋), TRUNCATION alternate (⌊c/4⌋), storage clamp | OWN-DEC-007; rule UNRESOLVED | PROVISIONAL SOFTWARE DEFAULT | 16-bit quantization ≈ −98 dB re FS; ROUND_NEAREST bias −0.125 LSB16, TRUNCATION +0.375 LSB16 (mean over codes) | VAL-012 (all 262144 codes), unit tests | CHAIN-EXP-008 |
| R14 | IDENTITY_UNITY: stored code replayed unchanged, x4 re-expansion | EXECUTION_PLAN_V2 §4; arithmetic UNKNOWN | PROVISIONAL | none | VAL-012 | CHAIN-EXP-008/010 |
| R15 | TRANSPARENT: ideal band-limited reconstruction (implementation kernel, flat to 21 kHz within 1e-5 dB, −0.005 dB at 21.5 kHz, exact response recorded); de-emphasis OFF_UNASSERTED; coupling INACTIVE; normalized FS | OWN-DEC-005; SM5841/PCM69A/I-V/LP UNKNOWN | PROVISIONAL SOFTWARE DEFAULT | no interpolation images, no ringing, no LF pole; not a hardware reconstruction | VAL-013 | CHAIN-EXP-010/020 / SRC-33 |
| Routes | MAIN_LR identity; INDIVIDUAL_PAIR represented, NOT POPULATED; HEADPHONES EXCLUDED | OWN-DEC-008 | PROVISIONAL | none | VAL-014 | CHAIN-EXP-011 |
| Stereo | true phase-locked stereo: shared clock, per-channel state, no offsets | MPC3K-CLM-012 | PROVISIONAL | no mismatch, no bleed | VAL-013 stereo | — |
| Calibration | normalized converter full scale; volts UNSET (physical mode INVALID_CONFIGURATION) | CHAIN-DEC-014 | UNSET | none | VAL-013 | CHAIN-EXP-009/010 |

Not introduced: interstage R10, output trim, cascade, noise, jitter, mismatch, saturation, overload recovery, limiter, normalization, mixer arithmetic, pitch interpolation, reverse order. No hardware fidelity is implied anywhere; the MPC path is UNVALIDATED AGAINST HARDWARE.

## Sprint 5 — 2026-10-07 — PROVISIONAL SP→MPC SOFTWARE CASCADE (Track A, OWN-DEC-009..013)

Implementation commit: `69d64a02ba206a085bfd7b018decdba9e70183f1`. Subsystem: `smlsp3000/reference/cascade.py` (cascade-reference-impl-1.0.0), product configuration `sml-sp3000-product-config-track-a` v1, cascade research configuration v1; SP 1.0.4 / MPC 1.0.2 (core entry points exposed; outputs bit-identical to Sprint 3/4 records).

| Item | Behaviour introduced | Reason / evidence | Status | Audible / behavioural consequence | Test coverage | Replacement point |
|---|---|---|---|---|---|---|
| Composition | R1 → SP core (R2–R9) → R10 → MPC core (R11–R15) → R16 on the proxy grid; no duplicated blocks | docs/ARCHITECTURE.md | PROVISIONAL / UNVALIDATED AGAINST HARDWARE | the 12-bit SP path (band limit, fold-back, hold droop/images, quantization) feeds the 18-bit TRANSPARENT ADC, 18→16 storage and TRANSPARENT DAC: the MPC stage adds only 16-bit quantization (≈ −98 dB re FS) and the 22.05 kHz band limitation on top of the SP result; SP images above 22.05 kHz do not reach storage | VAL-015 identities | CHAIN-EXP-012 |
| R10 | interstage_level_db, owner default 0.0 dB (SP normalized FS → MPC normalized FS); research range −60…+24 dB | OWN-DEC-009; RD-P0-03 UNKNOWN | OWNER-SET PROVISIONAL SOFTWARE DEFAULT; NON-HISTORICAL; volts UNSET | at 0 dB level-neutral apart from implemented droop/quantization; negative values lower MPC storage level (more relative quantization error); positive values reach the 18-bit converter clamp (hard clamp, no recovery, no saturation) | VAL-015 interstage (−60/−20/0/+6/+20 dB) | CHAIN-EXP-005/009/012 |
| Chain modes | CASCADE (product default), SP_ONLY, MPC_ONLY, BOTH_MACHINE_BYPASSED; all with the cascade's integer latency (310 host samples at 48 kHz, default kernels); bypassed machine = exact delay of its core delay | OWN-DEC-012 | research/diagnostic except CASCADE | mode switches keep alignment; a bypassed machine contributes nothing (no grid, no quantizer) | VAL-015 | — |
| Product path | B selected (G-07S software decision); routes NONE_CH7_8 / MAIN_LR; linked dual mono PRODUCT ABSTRACTION; no drive macro / wet-dry | OWN-DEC-010/011/012 | OWNER-APPROVED SOFTWARE PRODUCT DECISION; G-07H BLOCKED | none beyond the implemented path | VAL-016 | G-07H |
| Reverse order | MPC → SP behind research switch (default off) | CHAIN-DEC-013 | INFORMATIONAL only | never a product mode | VAL-016 derivative | CHAIN-EXP-013 |
| Listening kit | software-only CHAIN-EXP-018 stimuli (synthetic material), RMS-matched, blinded | OWN-DEC-013 | PREPARED; human listening NOT EXECUTED | none (outside the model) | kit record + manifest | human listening; G-07H |

Not introduced: soft clipping, saturation, recovery, transformer/level-dependent analog behaviour, normalization, drive/wet-dry, volts, output trim, plugin bypass. No hardware fidelity is implied.

## Sprint 6 — 2026-10-07 — NATIVE PRODUCTION CORE, PARAMETER FREEZE, OPTIMISATION (Track A, OWN-DEC-014..023)

Implementation commit: `1a3ecafd98209f1b637b8aa2ba187d6003941c8a`. Subsystem: `native/` (smlsp3000-native-core-1.0.0); reference instrumentation sp1200 1.0.5 / mpc3000 1.0.3 / cascade 1.0.1 (audio unchanged, evidence/sprint_06/instrumentation_regression_run.log).

| Item | Behaviour introduced | Reason / evidence | Status | Audible / behavioural consequence | Test coverage | Replacement point |
|---|---|---|---|---|---|---|
| Native core | C++20 port of R1–R16 as composed on the proxy grid; float64; 8x proxy; checkpoint kernels; same quantizer/clamp semantics; no I/O; no allocation in process() | OWN-DEC-014/015 | VALIDATED AGAINST THE SOFTWARE REFERENCE (VAL-021: all cells within 1e-9 of the limits; codes identical); UNVALIDATED AGAINST HARDWARE | none intended: agreement with the reference to ≈1e-16 | VAL-019..022, ctest | reference stays the oracle |
| Composed operator tables | sampler∘R12 band limitation per residue; R16∘R15 per host phase class (ENG-DEC-021); exact-order path retained for diagnostics | OWN-DEC-017 budgets (29 % → 10 % at 48 kHz; 115 % → 19 % at 192 kHz) | ACTIVE | none beyond float rounding order (VAL-020 production-introduced ≤ −321 dB) | VAL-021 both paths; VAL-020 | — |
| Output trim (R16 trim) | output_trim_db −60…+12 dB, final host gain, 10 ms linear-in-dB ramp on the host clock | OWN-DEC-020/021 | ACTIVE | plain gain; not a limiter | VAL-021 (static law bit-exact), VAL-022 (ramp bit-exact) | — |
| Smoothing | 10 ms linear-in-dB ramps for sp_input_level_db and interstage_level_db on the proxy clock, sample-indexed events, no restart, continuation from the current value | OWN-DEC-021 | ACTIVE | no zipper steps on continuous controls; constant parameters identical to the static reference | VAL-022 | — |
| Discrete switches | sp_input_gain / mpc_input_gain switch at the mapped sample, no interpolation | OWN-DEC-021 | ACTIVE | instantaneous gain step (as the machines' switches) | VAL-022 | — |
| plugin_bypass | static latency-aligned dry passthrough (no gains, no trim), chain keeps running | OWN-DEC-020 | ACTIVE (transitions Sprint 7) | dry audio delayed by the reported latency | ctest | Sprint 7 transition policy |
| Input safety | NaN/Inf → 0 + counter; over-range passes to the converter clamps; internal non-finite → silenced chunk, latched fault, cleared signal state | OWN-DEC-019 | ACTIVE | no NaN reaches the host; no hidden limiter | ctest, VAL-022 | — |
| Meters | host input peak, SP/MPC core-input proxy peaks, SP clip, MPC 18-bit clip, 16-bit clamp, output peak; reference cascade machine peak marked UNAVAILABLE_IN_CASCADE | OWN-DEC-022 | ACTIVE | — | VAL-021 (clamp counters identical) | — |
| State v1 | schema 1; six controls + identities; explicit rejections; no migrations | OWN-DEC-020 | ACTIVE | — | VAL-022 | — |

Not introduced: any model change (kernels, proxy, precision, Path A/C, ideal SP reconstruction), soft clipping, saturation, noise, limiter, normalization, drive/wet-dry, volts, bypass transitions, plugin wrapper. No hardware fidelity is implied.

## Sprint 7 — 2026-10-07 — WRAPPER TRANSITIONS ONLY (no DSP change; OWN-DEC-028/030)

Implementation/review checkpoint commit: `e333dc3a678a32ed52d382ed4fc8d4f03fd5206d`. Subsystem: `native/include/smlsp3000/host_adapter.hpp` (smlsp3000-host-adapter-1.0.0), `plugin/` (JUCE 8.0.9 wrapper). The native core's audio behaviour is unchanged (VAL-026: plugin == adapter == core bit-for-bit; VAL-021 limits still met against the Python reference); the two core additions (`serialize_state_with_bypass`, `update_product_targets`) are non-sonic API.

| Item | Behaviour introduced | Reason / evidence | Status | Audible / behavioural consequence | Test coverage | Replacement point |
|---|---|---|---|---|---|---|
| Plugin bypass crossfade | host-facing plugin_bypass selects the latency-aligned ORIGINAL input (before every product gain and both machines, no output trim) with a 10 ms linear crossfade of complementary weights; the core and the dry delay keep running; rapid toggles continue from the current weight; reset/startup in bypass snap to fully dry | OWN-DEC-030 | ACTIVE (adapter, not core) | a 10 ms blend between processed and dry during toggles; nothing else | adapter ctest; VAL-023 | Sprint 7 only; no wet/dry feature |
| Input sanitisation at the adapter boundary | NaN/Inf host samples → 0 (counted) before BOTH the core and the dry path | ENG-DEC-026 | ACTIVE | no NaN can enter the crossfade sum | adapter ctest; VAL-024 | — |
| Block-boundary parameter delivery | host parameter changes become native events at offset 0 of the next block; the core's 10 ms ramps and discrete switches are unchanged | OWN-DEC-031 (JUCE/VST3 path) | ACTIVE | automation steps land on block boundaries (≤ one block late); no wrapper smoothing | VAL-026 automation | sample-offset delivery if a future wrapper provides it |
| Float32 host path | promotion to float64, unchanged core, final float32 cast with preallocated buffers | OWN-DEC-029 | ACTIVE | float32 interface rounding only | VAL-026 (same-input/same-cast oracle) | — |

Not introduced: any sonic processing, denormal guard, limiter, normalisation, extra rate conversion, wet/dry, drive, routes. Clock anchor unchanged (OWN-DEC-027, DI-001).
