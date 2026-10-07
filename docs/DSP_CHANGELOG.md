# DSP changelog

Revision: execution V3 (Sprint 3) · 2026-10-07 · supersedes execution V1

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
