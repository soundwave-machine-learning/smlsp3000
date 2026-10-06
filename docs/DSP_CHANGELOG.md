# DSP changelog

Revision: execution V1 (Sprint 1) · 2026-10-06 · supersedes planning V1

Status: EXECUTION IN PROGRESS.

## Planning baseline — PLANNED, NOT IMPLEMENTED

2026-10-06: documented B reference superset R0–R16, four rate domains, physical gains/clamps, linked-dual-mono abstraction, unity pitch and replaceable uncertainties from researchV1. No DSP was written or executed. No audible behavior, code change, preset or binary is claimed.

Future executed entries must record date/implementation commit, changed block/parameter/asset versions, source/decision/requirement IDs, before/after actual behavior, metrics/regression impact, evidence paths and limitations. New calibration/hardware evidence updates confidence/decisions before product behavior changes. Do not rewrite historical research or create fake entries for planned sprints. Artifact labels and claim lanes remain separate.

## Sprint 1 — 2026-10-06 — NO DSP BEHAVIOUR

Implementation commit: recorded in docs/PROJECT_HANDOFF.md after the milestone commit. Changed blocks/parameters/assets: NONE. R0–R16 remain unimplemented; no machine asset exists; no quantizer, filter, hold, clamp or resampler of either machine was written. What was added is analysis tooling only (smlsp3000/: hashing, schemas, WAV I/O, analytic self-test stimuli, pilot/alignment/null evaluator; CHAIN-EXP-016 SIMULATION record). The evaluator's Kaiser-sinc interpolator and DC high-pass are measurement-side preprocessing with a recorded floor; they are not part of any machine model and carry no sonic claim. Audible behaviour: none claimed.
