# Execution plan V2 — owner decision: two tracks, software first, hardware fit deferred

Revision: execution V2 · 2026-10-06 · supersedes the entry-gate wording of docs/sprint_prompts/SPRINT_03.md … SPRINT_08.md where they require accepted Sprint 2 hardware evidence (the contract files themselves stay byte-identical as the planning-V1 record)

Status: OWNER DECISION RECORDED (OWN-DEC-001). The §4 dependency plan was APPROVED by the owner on 2026-10-07 with the Sprint 3 inputs (§9 items 1–4: R3 INACTIVE, quantizer ROUND_NEAREST / FLOOR alternate, NONE_CH7_8 only). Sprint 3 and Sprint 4 executed (software PASS; §9 item 5 received 2026-10-07: R12/R15 TRANSPARENT, R13 ROUND_NEAREST / TRUNCATION, OWN-DEC-005..008). §9 item 6 received 2026-10-07 (interstage 0.0 dB, G-07S path B, OWN-DEC-009..013); Sprint 5 executed (software PASS). §9 item 7: G-08 software budgets and the C++ stack received 2026-10-07 (OWN-DEC-014..023); Sprint 6 executed. G-09 target matrix/framework/licence remains open.

## 1. Owner decision OWN-DEC-001

DECISION: proceed with a provisional software/reference implementation without hardware fit.

Reason: the owner does not currently possess SP-1200 or MPC3000 hardware; the Sprint 2 hardware campaign (G-04) cannot be executed (docs/sprint_reports/SPRINT_02_REPORT.md, BLOCKED, unchanged).

Consequences (binding on every later sprint):

1. Hardware matching is not claimed anywhere — code, docs, UI, manual, metadata, release notes.
2. Hardware-derived coefficients remain unresolved; every value that would normally be fitted is PROVISIONAL / LITERATURE-DERIVED / SIMULATED / ESTIMATE and UNVALIDATED AGAINST HARDWARE.
3. Provisional implementations must remain replaceable behind the block interfaces of docs/ARCHITECTURE.md (R0–R16, MachineAsset records).
4. All hardware confidence states (docs/CONFIDENCE.md claim register, docs/RESEARCH_DEBT.md, G-04/G-05/G-06) remain unchanged; nothing is promoted.
5. Future hardware fitting (Track B) may replace provisional components; the architecture must not make that unnecessarily difficult.
6. Release wording must distinguish modeled/inspired behaviour from measured hardware behaviour (§7 claim boundary).
7. History is preserved: Sprint 1 PASS, Sprint 2 hardware campaign BLOCKED / EXTERNAL HARDWARE REQUIRED, G-04 status preserved. The previous plan was not wrong; it assumed hardware availability the owner does not have.

## 2. Tracks

| Track | Content | May use | Status |
|---|---|---|---|
| A — SOFTWARE / REFERENCE IMPLEMENTATION | reference DSP (R0–R16 as provisional/replaceable blocks), provisional DSP, application architecture, plugin/app wrapper, UI, state/preset system, numerical validation, deterministic regression, simulation experiments, performance work | documented research (docs/research V1), literature-derived behaviour (SRC-04 etc., labelled as sibling-machine literature where applicable), simulation, numerical experiments, owner-approved provisional models, deterministic tests | ELIGIBLE after owner approval of §4 |
| B — HARDWARE FIT / VALIDATION | CHAIN-EXP-001..015, G-04 campaign, G-05 P0/P1 closure by evidence, G-06 hardware thresholds, hardware fitting of every provisional value, hardware-condition listening, hardware-accuracy claims, hardware-fit release | stock units, calibrated interface, operator, owner acceptance | DEFERRED / BLOCKED until hardware exists |

Track B artifacts never share a filename pattern, status word or acceptance row with Track A artifacts (research §43 artifact labels).

## 3. G-04 reclassification — DEFERRED EXTERNAL VALIDATION GATE

G-04 stays BLOCKED — HARDWARE NOT AVAILABLE. It is reclassified from a sprint-entry gate to a DEFERRED EXTERNAL VALIDATION GATE:

| Still blocked by G-04 (and G-05/G-06 behind it) | Explicitly NOT blocked by G-04 |
|---|---|
| any statement "hardware accurate", "matched to SP-1200", "matched to MPC3000", "hardware validated", "production hardware-fit complete", "measured SP-1200/MPC3000", "component accurate", "exact emulation" | reference DSP implementation (Track A) |
| every HARDWARE-FIT ACCEPTANCE cell in docs/ACCEPTANCE_MATRIX.md | provisional DSP implementation |
| closing any RD-P0/RD-P1 item (they stay OPEN) | application architecture, plugin/app wrapper, UI, state/preset system |
| promoting any claim in docs/CONFIDENCE.md | numerical validation, deterministic regression, simulation experiments, performance work |
| hardware-condition listening (CHAIN-EXP-018 hardware arm; CHAIN-EXP-013/014) | software-only comparisons labelled SIMULATION / LISTENING STIMULUS (software conditions only) |
| hardware-fit release (G-11 "hardware" wording) | a software release candidate under the §7 claim boundary |

## 4. Sprint 3–8 dependency audit (SUBMITTED FOR OWNER APPROVAL)

Classification: A = HARD DEPENDENCY (cannot proceed without actual hardware); B = PROVISIONAL SUBSTITUTE ALLOWED (clearly labelled provisional/reference implementation); C = NO TRUE HARDWARE DEPENDENCY. "Owner" in the replacement column means an owner decision that is not a hardware measurement.

| Sprint | Requirement | Original dependency | Class | Replacement / provisional path (Track A) | Future hardware-fit impact (Track B) |
|---|---|---|---|---|---|
| S3 | REQ-008 SP sample grid, encoding, quantizer | CHAIN-EXP-001 (exact rate), CHAIN-EXP-002 (encoding/rounding/offset/clamp) | B | Rate = versioned asset 20 000 000/768 Hz, PROVISIONAL (SP12-CLM-002, SRC-10), nominal 26.04 kHz VERIFIED; 12-bit linear VERIFIED; encoding/rounding/offset = ResearchConfiguration switch with the explicit candidate set {FLOOR (SAR hypothesis, research §8), ROUND_NEAREST}; default candidate chosen by owner and tagged PROVISIONAL + UNVALIDATED AGAINST HARDWARE; code clamp 0…4095 PROVISIONAL; no dither (CHAIN-DEC-015) | measured rate/rule replace the asset; VAL-008 hardware-fit cell (exact code agreement with exported data) stays BLOCKED |
| S3 | REQ-009 SP AA response and fold-back | CHAIN-EXP-019 / -002; RD-P0-01 | B (constrained) | R3 stays a replaceable block. Two owner-selectable provisional states: (i) INACTIVE placeholder (skeleton explicitly "not a valid SP model", research §41); (ii) PROVISIONAL LITERATURE-DERIVED low-pass of the documented class (multi-section active low-pass, attenuation onset ≈15 kHz on the SP-12 sibling, SRC-04) with order/corner/Q recorded as ESTIMATE in a versioned asset, approved by owner in the S3 report before use. Fold-back of 13.02–15 kHz content is structural (sampling) and needs no hardware. No order-11 digital fit is transplanted as analog order. | SPICE/measured response replaces coefficients; VAL-009 hardware-fit cell BLOCKED |
| S3 | REQ-010 SP hold images and output variants | CHAIN-EXP-003 / -004 | B (hold, ch 7–8) + A (ch 3–4 / 5–6 responses, MIX OUT topology) | R7 full-period zero-order hold PROVISIONAL (hold fraction UNKNOWN); R8 route NONE_CH7_8 fully supported (VERIFIED no filter; images structural, checked against closed form SP12-CLM-020); routes FIXED_CH5_6 / FIXED_CH3_4 present in the interface but NOT POPULATED (no arbitrary low-pass; research §39) unless the owner later approves an explicit ESTIMATE; MIX_OUT not implemented (summing topology UNKNOWN) | hold fraction and ch 3–6 coefficients from hardware/SPICE; VAL-010 hardware-fit cell BLOCKED |
| S3 | REQ-011 SP physical gains and clip | CHAIN-EXP-005; RD-P0-02 | B (normalized) | NORMALIZED RESEARCH CALIBRATION (already permitted by docs/ENGINE_SPEC.md): digital full scale ↔ converter full scale; gain steps 0/+20/+40 dB as exact ratios (STRONGLY SUPPORTED); analog clamp INACTIVE (UNSET), converter clamp at code range only; volts-per-dBFS UNSET so any physically scaled run still returns INVALID_CONFIGURATION | FS volts/clip from hardware; VAL-011 hardware-fit cell BLOCKED |
| S3 | REQ-017 linked dual-mono SP / true-stereo MPC | CHAIN-EXP-007 (slot skew) | C (product) / B (research skew) | abstraction implemented as designed (CHAIN-DEC-005, labelled PRODUCT ABSTRACTION); research-only slot-skew switch with PROVISIONAL arithmetic value 4.8 µs; equal/anti-phase/isolation/reset/chunk tests are software tests | measured skew/hold fraction; no product impact unless EXP-007 reopens CHAIN-DEC-005 |
| S3 | REQ-018 unity pitch, sampler non-goals | none | C | scope audit as written | none |
| S3 | CHAIN-EXP-017 qualitative SP-12 sanity | simulation only | C | run as SIMULATION; never evidence about the SP-1200 | none |
| S4 | REQ-012 MPC conversion / storage / arithmetic separation | CHAIN-EXP-008; RD-P0-05 | B | 44.1 kHz VERIFIED; 16-bit storage VERIFIED; 18-bit converter architecture VERIFIED; R13 reduction = ResearchConfiguration {TRUNCATION, ROUND_NEAREST} PROVISIONAL, owner-chosen default; R14 identity PLACEHOLDER | identifiable rule from the hardware low-level test; VAL-012 hardware-fit cell BLOCKED |
| S4 | REQ-013 MPC input/output response, gain, overload | CHAIN-EXP-009 / -010 / -020; RD-P0-06, RD-P1-02/03/07/12 | B (constrained) | R11: switch gains as 20 dB steps from the printed sensitivities (VERIFIED text; sensitivity ≠ FS), record-level pot as an ideal dB trim (ESTIMATE), coupling pole and analog clamp INACTIVE/UNSET; R12/R15: owner-selectable provisional states (i) TRANSPARENT (identity decimation/interpolation; the research's own expectation for undriven program) or (ii) ESTIMATE linear-phase FIR of generic converter class with recorded design spec; FS volts UNSET (normalized); overload = converter clamp only; no recovery model; no saturation, no noise, no de-emphasis (UNKNOWN use) | datasheet/measured responses replace kernels; VAL-013 hardware-fit cell BLOCKED; driven product modes stay unapproved until recovery is measured (AUD-C05) |
| S4 | REQ-014 main / individual / headphone paths | CHAIN-EXP-011 | B | main L/R implemented (recommended route, ENG-DEC-003); individual route present in the interface, NOT POPULATED; headphones excluded | hardware decides equivalence; VAL-014 hardware-fit cell BLOCKED |
| S5 | REQ-015 calibrated SP→MPC interstage | CHAIN-EXP-012; RD-P0-03 | B (owner-set) | interstage_level_db as the single explicit parameter in normalized units (dB re MPC converter full scale); default requires an OWNER decision, labelled non-historical and PROVISIONAL; composed cascade validated against its own composition (software consistency), not against hardware | measured volts/record-level mapping replaces default; VAL-015 hardware-fit cell BLOCKED |
| S5 | REQ-016 product path / output defaults | CHAIN-EXP-013 / -014 / -018 + G-07 | A (hardware conditions) / B (software-only product decision) | owner selects A/B/C, SP route (only NONE_CH7_8 is populated), MPC route, controls and claim limits on documentary and software evidence; CHAIN-EXP-013/014 run only as SIMULATION derivatives (informational); CHAIN-EXP-018 may run with software conditions only (reference / simplified / bypass; no hardware arm), labelled LISTENING STIMULUS, informational for product choice | hardware-arm listening and hardware-fit metrics may revise the selection later; G-07 is split into G-07S (software product decision) and G-07H (hardware-informed confirmation, deferred) |
| S6 | REQ-019 rate domains, block-size invariance | §25; G-08 | C | as written; same-build exact checks; cross-rate tolerance frozen by owner at G-08 | none |
| S6 | REQ-020 implementation aliasing floor vs authentic images | G-06 agreement + G-08 budget | C (implementation residual, G-08 owner budget) / A (hardware image-level agreement) | proxy-rate convergence, near-Nyquist and clamp tests against the model's own higher-rate rendering; "retains G-06 agreement" cell deferred | hardware image/alias levels; VAL-020 hardware-fit cell BLOCKED |
| S6 | REQ-021 production vs reference | §43; G-08 | C | as written (reference is the oracle) | none |
| S6 | REQ-022 parameter layers / persistence | G-07/G-08 | C (needs G-07S/G-08 owner decisions, not hardware) | as written; every MachineAsset carries provisional tags (§5) | asset version bump when fitted |
| S7 | REQ-023 latency and bypass states | G-09 | C | as written | none |
| S7 | REQ-024 real-time / state / numerical safety | G-08/G-09 | C | as written | none |
| S7 | REQ-025 headroom and honest UI | G-09/G-10 | C (claim boundary §7 governs wording) | as written; UI/manual text must use §7 wording; clip meters mark converter-code boundaries, analog clamps shown as "not modelled" | analog clip indication once measured |
| S7 | REQ-026 plugin/offline equivalence, platform | G-09 | C (platform/SDK/licence/native-host are owner/platform inputs, not hardware) | as written once G-09 inputs exist | none |
| S8 | REQ-027 reproducible release candidate | G-11 | C (software candidate) / A (hardware-fit release) | candidate may be built and reviewed under the §7 claim boundary; RELEASE READY YES only for a release described as inspired/informed, never as hardware-validated | hardware-fit release stays BLOCKED |

Summary: no sprint is entirely hardware-blocked after Sprint 2; the hardware-blocked parts are the HARDWARE-FIT ACCEPTANCE cells (VAL-005..007 wholly; VAL-008..016 and VAL-020 in part) and hardware-condition listening.

## 5. Provisional implementation policy (Track A)

1. Every behaviour that would normally be fitted from hardware lives behind the replaceable block interface (R0–R16) and consumes a versioned MachineAsset or ResearchConfiguration record; no provisional number is hard-coded in DSP code.
2. Every provisional value carries, in its asset record: `value`, `unit`, `evidence_status` (VERIFIED / STRONGLY SUPPORTED / LITERATURE-DERIVED / SIMULATED / PROVISIONAL / SPECULATIVE / UNKNOWN per docs/CONFIDENCE.md), `substitute_kind` (PROVISIONAL / LITERATURE-DERIVED / SIMULATED / ESTIMATE), `hardware_validation` = `UNVALIDATED AGAINST HARDWARE`, `source_ids` / `claim_ids` / `decision_id`, `replaced_by` (the Track B experiment that would replace it), `model_version`.
3. No magic values: a value without source/status fails asset validation and prepare() returns INVALID_CONFIGURATION.
4. Model version is recorded in every render record and in serialized state (asset ID + version + hash).
5. Tests target software behaviour (closed-form expectations, determinism, invariances, documented equations), never historical hardware truth; any nonzero tolerance is derived from the design specification and recorded, not tuned to pass.
6. Hardware-fit parameters remain swappable: a fitted asset is a new asset version with the same interface; switching assets must not require code changes.
7. Nothing prohibited by research §39 / AGENTS.md becomes allowed by this decision: no generic saturation, noise, jitter, mismatch, sag, hidden limiter/normalization, SSM filter, tuned playback or reverse-order product.
8. Priorities in the reference model: deterministic behaviour, clear equations, traceability, numerical stability, testability, replaceability; no premature optimization.

Repository status vocabulary applies (docs/CONFIDENCE.md); the additional implementation tags ESTIMATE and UNVALIDATED AGAINST HARDWARE are defined here and will be added to smlsp3000/schemas.py when Sprint 3 starts.

## 6. Software-track acceptance

docs/ACCEPTANCE_MATRIX.md now carries two acceptance columns per row: SOFTWARE ACCEPTANCE (Track A: software implementation, numerical regression, plugin/app validation — PASS possible) and HARDWARE-FIT ACCEPTANCE (Track B: hardware correlation, hardware-fit release — BLOCKED until G-04). Software numeric policies (exactness, cross-rate tolerance, reference/production budget, CPU/latency) are owner decisions at G-08 and are not hardware thresholds; G-06 hardware thresholds stay UNKNOWN.

## 7. Claim boundary (release / marketing)

Until G-04 (and the dependent G-05/G-06 fits) are actually completed, the product may be described as:

> SML SP-3000 — a software instrument/effect inspired by and informed by documented SP-1200 / MPC3000 architecture and behaviour.

It may NOT be described as: exact emulation, hardware matched, component accurate, measured SP-1200, measured MPC3000, hardware validated. Existing repository wording continues to apply: linked SP stereo is a PRODUCT ABSTRACTION; the ch 7–8 unfiltered route is a research fixture, not a factory default until G-07; unity pitch only; the famous pitched sound is absent at unity and must not be promised; the MPC undriven contribution is UNKNOWN. Every UI/manual/preset/metadata string referencing either machine must pass a claim-boundary review item in the S7 (G-10) and S8 (G-11) reports.

## 8. Revised autonomous continuation

Claude may continue past the Sprint 2 hardware block into Sprint N (3…8) when all hold: (a) the owner has approved this §4 plan; (b) the sprint's §4 rows have an approved provisional path (class B or C) for every requirement; (c) hardware-derived claims remain explicitly unresolved in every artifact; (d) replaceable architecture (§5) is preserved; (e) the sprint's automated software gates pass. Claude must still STOP when a sprint requires hardware data for an implementation decision that cannot be safely deferred (a class-A item on the critical path, an undefined provisional candidate set, or an owner choice listed as "Owner" in §4 that has not been made), when an artifact would need a hardware-accuracy claim, or for any stop condition already in docs/AUTONOMOUS_BUILD_PROMPT.md.

## 9. Owner inputs still needed before Sprint 3 code

1. Approval of this §4 dependency plan. — RECEIVED 2026-10-07.
2. R3 state for S3. — RECEIVED: INACTIVE (OWN-DEC-002).
3. Default SP quantizer rule candidate. — RECEIVED: ROUND_NEAREST default, FLOOR research alternate (OWN-DEC-003).
4. Confirmation that NONE_CH7_8 is the only populated SP output route in Track A. — RECEIVED (OWN-DEC-004).
5. (Before S4) R12/R15 state; R13 default candidate. — RECEIVED: TRANSPARENT / TRANSPARENT; ROUND_NEAREST default, TRUNCATION alternate (OWN-DEC-005..008).
6. (Before S5) provisional interstage default; G-07S product selection. — RECEIVED: 0.0 dB (OWN-DEC-009); path B, SP→MPC, routes, abstraction, chain modes, listening preparation (OWN-DEC-010..013).
7. (Before S6/S7) G-08 software numeric/CPU/latency/parameter budgets; G-09 target matrix, framework, licence. — G-08 PART RECEIVED 2026-10-07 (OWN-DEC-014..023: C++20/CMake stack, float64/8x freeze, numerical limits, CPU/latency budgets, 8192-sample blocks, controls v1, 10 ms ramps); G-09 (plugin formats, OS/DAW matrix, framework/SDK/licence, Windows toolchain) STILL OPEN.
