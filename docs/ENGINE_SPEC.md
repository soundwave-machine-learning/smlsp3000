# Engine specification and requirements

Revision: execution V4 (Sprint 4) · 2026-10-07 · supersedes execution V3

Status: EXECUTION IN PROGRESS. Requirements unchanged; REQ-001/002/003/028 have Sprint 1 evidence (ACCEPTANCE_MATRIX); REQ-004 BLOCKED; no R-block implemented.

## Product behavior and scope

Input: full-mix program from an approved host. Intended output: calibrated coloration through selected SP-1200-derived path then selected MPC3000-derived path. Shipping path and default outputs remain G-07 decisions. B reference is the structurally evidence-backed comparison superset. The product is a continuous mix processor, not a sampler; no hardware 2.5s memory limit is imposed on software. The limit instead constrains measurement stimuli.

At unity pitch the SP effects are AA/bandwidth, sampling fold-back, 12-bit quantization/clamp, ZOH droop/images and selected output response. The famous pitched drop-sample sound is absent at unity and must not be promised. MPC18-bit converters/16-bit storage and linear/filter/clip response are distinct; undriven audible contribution is UNKNOWN. Both machines may need calibration, not generic added warmth.

## Functional requirements and ownership

| Requirement | Behavior | Source/design basis | Modules | Primary sprint | Validation | Gate |
|---|---|---|---|---|---|---|
| REQ-001 | Preserve provenance and four authority lanes | §§3–5, 34, 44; user planning-only | Docs/evidence registry | S01 | VAL-001 | G-01 |
| REQ-002 | Freeze actual toolchain, commands and target matrix before executable work | User scope; workflow capability rules | Build/test harness | S01 | VAL-002 | G-01 |
| REQ-003 | Self-test alignment/null framework without hardware claims | CHAIN-EXP-016; §§31–32 | Validation harness | S01 | VAL-003 | G-02 |
| REQ-004 | Extract circuits and constrain source use without guesses | CHAIN-EXP-019/020; RD-P0-01/06; RD-P1-01..03/09/10 | R2/R3/R8/R9/R11/R12/R15 | S01 | VAL-004 | G-03 |
| REQ-005 | Measure stock units with trustworthy artifacts | §30; all hardware experiments | Hardware campaign | S02 | VAL-005 | G-04 |
| REQ-006 | Close all P0/P1 debt or explicitly limit scope with owner approval | §§40–42 | Evidence/gate registry | S02 | VAL-006 | G-05 |
| REQ-007 | Freeze quantitative validation thresholds before fitting | §32; source thresholds UNKNOWN | Validation policy | S02 | VAL-007 | G-06 |
| REQ-008 | Maintain SP sample grid, encoding and quantizer behavior | SP12-CLM-001..004/024; CHAIN-DEC-002/015 | R4/R5 | S03 | VAL-008 | G-05 |
| REQ-009 | Model SP AA response and retain historical fold-back | SP12-CLM-008/009; RD-P0-01; CHAIN-EXP-002/019 | R2/R3/R4 | S03 | VAL-009 | G-05/G-06 |
| REQ-010 | Preserve SP hold images and distinct output variants | SP12-CLM-012..016/020; CHAIN-DEC-003 | R6/R7/R8/R9 | S03 | VAL-010 | G-05/G-06 |
| REQ-011 | Calibrate SP physical gains and clip boundaries | RD-P0-02; CHAIN-EXP-005; §26 | R0/R2/R5/R9 | S03 | VAL-011 | G-05/G-06 |
| REQ-012 | Keep MPC conversion, storage and arithmetic separate | MPC3K-CLM-001..004/010/016/017; RD-P0-05 | R12/R13/R14/R15 | S04 | VAL-012 | G-05/G-06 |
| REQ-013 | Fit MPC input/output response, gain and overload only to evidence | MPC3K-CLM-007/018..020; RD-P0-06/P1-02/03/07/12 | R11/R12/R15 | S04 | VAL-013 | G-05/G-06 |
| REQ-014 | Separate main, individual and headphone MPC paths | §20; RD-P1-08; CHAIN-EXP-011 | R15 variants | S04 | VAL-014 | G-05 |
| REQ-015 | Use calibrated analog SP→MPC interstage | CHAIN-DEC-014; RD-P0-03; CHAIN-EXP-012 | R0/R9/R10/R11/R16 | S05 | VAL-015 | G-05/G-06 |
| REQ-016 | Freeze product path and output defaults using fit/listening | CHAIN-DEC-001/003; §33; CHAIN-EXP-018 | Product model configuration | S05 | VAL-016 | G-07 |
| REQ-017 | Preserve linked dual-mono SP and true-stereo MPC semantics | CHAIN-DEC-005/010; §24; CHAIN-EXP-007 | Stereo scheduler; all per-channel blocks | S03 | VAL-017 | G-05/G-08 |
| REQ-018 | Keep unity pitch and sampler non-goals | CHAIN-DEC-004/013/016 | R6/R14; product scope | S03 | VAL-018 | G-07 |
| REQ-019 | Respect four rate domains and block-size invariance | §25; §43 | R1/R4/R7/R12/R15/R16 scheduler | S06 | VAL-019 | G-08 |
| REQ-020 | Keep implementation aliasing below approved floor while retaining authentic images | §29; CHAIN-EXP-016/017 | Resamplers/analog-proxy/clamps | S06 | VAL-020 | G-08 |
| REQ-021 | Validate production engine against reference | §43 reference/product separation | Shared engine + offline renderer | S06 | VAL-021 | G-07/G-08 |
| REQ-022 | Keep Product/Machine/Research parameter layers distinct | §43; CHAIN-DEC-012/014 | Configuration/state/presets | S06 | VAL-022 | G-07/G-08 |
| REQ-023 | Define latency and three bypass states | CHAIN-CLM-007; §43 bypass/latency | Engine/wrapper/bypass | S07 | VAL-023 | G-09 |
| REQ-024 | Meet real-time/state/numerical safety | §43 real-time/full-mix safety | Engine/wrapper/state bridge | S07 | VAL-024 | G-08/G-09 |
| REQ-025 | Expose full-mix headroom and honest UI behavior | §26/43; CHAIN-DEC-007..012 | Meters/controls/manual/presets | S07 | VAL-025 | G-09/G-10 |
| REQ-026 | Demonstrate plugin/offline equivalence and platform compatibility | §43; project-specific proposed delivery gate | Wrapper/build/package | S07 | VAL-026 | G-09 |
| REQ-027 | Reproduce and review release candidate without publishing | User planning-only; §§42–43 | Packaging/provenance/manual | S08 | VAL-027 | G-11 |
| REQ-028 | Preserve valid tests and bounded autonomous continuation | Workflow execution policy; user scope | Orchestrator/handoff | S01 | VAL-028 | G-01 |

## Candidate reference flow

R0 host dBFS→volts → R1 host→proxy → R2 SP input gain → R3 SP AA → R4 sample onto SP grid → R5 12-bit code/clamp → R6 unity machine state → R7 SP DAC/ZOH onto proxy → R8 selected SP channel response → R9 SP output volts/coupling → R10 calibrated interstage → R11 MPC input gain/coupling/analog clip → R12 ADC linear decimation/clamp/18-bit candidate → R13 16-bit storage reduction → R14 unity arithmetic candidate → R15 8× reconstruction/I-V/analog output → R16 host reconstruction/output trim.

Unknown analog clamp is inactive/UNSET in research skeleton, not a guessed rail model. Quantizer normalized code endpoints are permitted only for explicit research configuration; volts-based runs reject missing calibration. Supported word widths do not establish rounding, offset or FS voltage. R7 must preserve ZOH images; a conventional perfect bandlimited SP upsampler would remove a target mechanism and fail REQ-010. Diagnostic taps after all R0–R16 are reference-only; they never cause audio-thread I/O.

## State, error and compatibility contract

ARCHITECTURE owns interface/state/thread design; RATE_GAIN_PLAN owns units/rates/calibration; PARAMETERS owns stable candidate IDs and unresolved mappings. prepare validates complete selected calibration/kernel assets and target/routing support before process. Missing physical calibration yields a structured BLOCKED/INVALID_CONFIGURATION error in offline operation; a future plugin must fail initialization or use its documented latency-aligned error/bypass policy, decided at G-08, rather than substitute fake values. Nonfinite input/state handling and unsupported-rate behavior are frozen before S6. No unbounded solver, allocation, lock or disk access in real-time processing. Reported host delay and measured frequency-dependent phase are separate.

Machine asset replacement requires provenance/hash, unchanged units/interface, updated confidence, rerun of affected validation and explicit scope decision if behavior changes. ProductParameters cannot modify ResearchConfiguration; release assets fix hypothesis choices. Unity pitch only. SP/MPC bypasses remove complete respective machine blocks. Plugin bypass means aligned dry passthrough, not a hidden alternate model. No wet/dry control or level macro is added without G-07 approval and explicit latency semantics.

## Claim boundary (OWN-DEC-001)

Until G-04 is actually completed the product is "a software instrument/effect inspired by and informed by documented SP-1200 / MPC3000 architecture and behaviour"; the words exact emulation, hardware matched, component accurate, measured SP-1200, measured MPC3000 and hardware validated are prohibited in code, UI, manual, metadata and release notes. Existing wording rules (PRODUCT ABSTRACTION for linked SP stereo, research fixture for ch 7–8, unity pitch only, MPC undriven contribution UNKNOWN) stand. Full text docs/EXECUTION_PLAN_V2.md §7.

## Readiness and acceptance

Acceptance is the 28-row ACCEPTANCE_MATRIX, split per OWN-DEC-001 into SOFTWARE ACCEPTANCE (Track A) and HARDWARE-FIT ACCEPTANCE (Track B, BLOCKED until G-04); G-06 hardware tolerance, G-08 production tolerance and G-09 target tests are deliberately unresolved. No quantitative hardware PASS can be asserted yet. Unknown criteria keep dependent contracts DRAFT/BLOCKED. Sprint 3 (2026-10-07, Track A) implemented the provisional SP reference R1–R9/R16 in `smlsp3000/reference/` under OWN-DEC-001..004: R3 INACTIVE, quantizer ROUND_NEAREST default / FLOOR alternate, route NONE_CH7_8 only, normalized research calibration (volts UNSET → physical runs return INVALID_CONFIGURATION), full-period hold rendered band-limited to the proxy Nyquist (images preserved), exact rational scheduler, integer latency 104 host samples at the default kernels. Sprint 4 (2026-10-07, Track A) implemented the provisional MPC reference R11–R15 under OWN-DEC-005..008: R11 ideal dB trim with 20 dB switch steps (clamp/coupling INACTIVE), R12 TRANSPARENT (ideal band limitation at 22.05 kHz + ideal sampling + 18-bit clamp), R13 ROUND_NEAREST default / TRUNCATION alternate, R14 identity, R15 TRANSPARENT (unity re-expansion + ideal reconstruction; de-emphasis OFF_UNASSERTED), route MAIN_LR only, true stereo, volts UNSET. Both machines are NORMALIZED RESEARCH SKELETONS, UNVALIDATED AGAINST HARDWARE; R0/R10/R16 trims, the cascade and the production engine are not implemented (docs/sprint_reports/SPRINT_03_REPORT.md, SPRINT_04_REPORT.md).
