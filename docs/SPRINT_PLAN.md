# Eight-sprint dependency and ownership index

Revision: execution V4 (Sprint 4) · 2026-10-07 · supersedes execution V3

Status: EXECUTION IN PROGRESS. Sprint 1 PASS (fbd1fac). Sprint 2 hardware campaign BLOCKED / EXTERNAL HARDWARE REQUIRED (1c0fe89), preserved. Owner approved EXECUTION_PLAN_V2 §4 on 2026-10-07. Sprint 3 Track A PASS (software cells); its hardware-fit cells BLOCKED. Sprint 4 Track A PASS (software cells, 2026-10-07); hardware-fit cells BLOCKED. Sprint 5 awaits owner inputs (interstage default, G-07S). Track B (hardware fit) deferred.

## Exactly eight substantive milestones

Eight is explicitly requested by the owner. Boundaries follow evidence dependencies: research/framework → hardware/thresholds → two references → cascade/product decision → production → native integration → candidate. Every individual contract is authoritative for scope and checks; under OWN-DEC-001 the entry-gate wording "accepted S2 / G-04/G-05/G-06 closed" of contracts 03–08 is amended by docs/EXECUTION_PLAN_V2.md: the software (Track A) parts of each sprint proceed with labelled provisional substitutes, the hardware-fit (Track B) parts stay BLOCKED. Executed: Sprint 1 PASS; Sprint 2 BLOCKED at preflight (docs/sprint_reports/).

| Sprint | Authoritative contract | Milestone | Entry gate / exit condition |
|---|---|---|---|
| 01 | [SPRINT_01.md](sprint_prompts/SPRINT_01.md) | Foundation, capability freeze and targeted source closure | G-01 separate implementation authorization, actual repository/baseline/branch and permitted operations. The planning package exists; no code/commands/unit evidence are assumed. → Actual commands and smoke results are recorded; source integrity/count checks pass; null framework verifies independent truth; ambiguous source values remain UNKNOWN; G-01/G-02 resolved and G-03 disposition precise. |
| 02 | [SPRINT_02.md](sprint_prompts/SPRINT_02.md) | Hardware evidence, P0/P1 closure and acceptance freeze | Accepted S1 and G-01/G-02. G-04 valid stock units/routes/interface/operator; G-03 unresolved items must have documentary or measurement resolving plan. Measurement thresholds and listening product judgment are not assumed. → G-04/G-05/G-06 PASS with actual evidence; all18 prerequisite debt items have valid scoped resolutions; split frozen and numeric acceptance owner-approved. A missing hardware campaign is BLOCKED, never completed. |
| 03 | [SPRINT_03.md](sprint_prompts/SPRINT_03.md) | Calibrated SP reference and stereo skeleton validation | Accepted S2 with G-04/G-05/G-06 closed for all dependent items; actual SP asset candidates and held-out data. No production optimization or factory output default selected yet. → All SP checks satisfy frozen limits; linked-stereo/scope assertions pass; complex response and images match held-out evidence; calibrated assets carry exact source/experiment identity; no shipping/default/fidelity overclaim. |
| 04 | [SPRINT_04.md](sprint_prompts/SPRINT_04.md) | Calibrated MPC reference and path comparison | Accepted S3; G-05/G-06 MPC data/rules/levels and de-emphasis disposition closed. Measured main/individual paths and digital observations, not assumed converter imperfections. → Frozen digital and analog checks pass on held-out data;18/16 distinction documented; path comparison and unity arithmetic rationale explicit; no generic nonlinear or noise behavior added. |
| 05 | [SPRINT_05.md](sprint_prompts/SPRINT_05.md) | Cascade validation, blind listening and product selection | Accepted S3/S4, G-05/G-06, CHAIN-EXP-012 calibrated physical cascade. G-07 listening/selection protocol criterion frozen before trials; owner/listeners available. → Cascade passes frozen hardware criteria; human listening recorded; G-07 resolves A/B/C/SP/MPC defaults/retained mechanisms. No undecided default remains hidden in downstream product tasks. |
| 06 | [SPRINT_06.md](sprint_prompts/SPRINT_06.md) | Production shared engine, parameter freeze and optimization | Accepted S5/G-07; G-08 numeric and parameter policy approved before changes: proxy/rate kernel, precision, cross-platform and reference tolerances, maximum inputs/blocks, CPU/latency budget, IDs/ranges/defaults/smoothing/version. → All exact/numeric checks pass under G-08; production matches accepted reference; parameter layers and persistence rules tested; no unknown release default or research switch; budgets met on chosen evaluation target. |
| 07 | [SPRINT_07.md](sprint_prompts/SPRINT_07.md) | Plugin wrapper, host/UI integration and real-time hardening | Accepted S6/G-08; actual G-09 target matrix, SDK/framework/license and native host access. G-10 final UI/listening protocol available; output/control design already selected. → All selected native rows and real-time/latency/bypass/state/UI checks pass; plugin/offline equivalence demonstrated; owner G-10 acceptance actual; no hypothetical target pass. |
| 08 | [SPRINT_08.md](sprint_prompts/SPRINT_08.md) | Reproducible release candidate, provenance and final review | Accepted S1–S7; all mandatory evidence/numeric/product/native/human gates closed; G-11 rights/package/signing/install scope resolved as applicable; approved clean-build environment and artifact destination. → Clean rebuild/regression/package/mandatory native and human gates pass; exact hashes/source provenance; every requirement covered; RELEASE READY YES only if G-11 valid. If blocked, precise NO verdict and blocker report instead of fabricated completion. |

## Track A / Track B dependency revision (OWN-DEC-001)

| Sprint | Track A (software/reference, provisional) | Track B (hardware fit) | Entry under V2 |
|---|---|---|---|
| 02 | — | whole sprint (CHAIN-EXP-001..012/015, G-04/G-05/G-06) | BLOCKED / EXTERNAL HARDWARE REQUIRED |
| 03 | REQ-008/009/010/011 provisional SP reference (class B), REQ-017/018 and CHAIN-EXP-017 (class C); ch 3–6 responses and MIX OUT not populated (class A) | VAL-008..011 hardware-fit cells | EXECUTED 2026-10-07 — software PASS (docs/sprint_reports/SPRINT_03_REPORT.md); hardware-fit BLOCKED |
| 04 | REQ-012/013/014 provisional MPC reference (class B) | VAL-012..014 hardware-fit cells | EXECUTED 2026-10-07 — software PASS (docs/sprint_reports/SPRINT_04_REPORT.md); hardware-fit BLOCKED |
| 05 | REQ-015 provisional interstage (B, owner-set), REQ-016 G-07S software product decision with software-only listening (B); CHAIN-EXP-013/014/018 hardware arms (A) | VAL-015 hardware-fit cell; G-07H | Accepted S4 + §9 input 6 |
| 06 | REQ-019..022 (class C; G-08 owner budgets) | VAL-020 hardware image agreement cell | Accepted S5 + G-07S + G-08 |
| 07 | REQ-023..026 (class C; G-09 owner/platform inputs; claim boundary) | — | Accepted S6 + G-09 + G-10 protocol |
| 08 | REQ-027 software candidate under the claim boundary (C) | hardware-fit release (A) | Accepted S7; G-11 for software candidate |

Full per-requirement table: docs/EXECUTION_PLAN_V2.md §4.

## Dependency order

S1 before S2 (framework/commands); S2 before S3/S4 for Track B only (valid evidence/thresholds) — Track A S3/S4 proceed on provisional substitutes (OWN-DEC-001); S3 then S4 form reference acceptance sequence; S3+S4+physical cascade before S5; G-07 after S5 before S6; G-08 frozen before S6 numerical work; S6 plus native capabilities G-09 before S7; G-10 human/native acceptance before S8; G-11 before release-ready verdict. Documentary source attempts cannot replace mandatory hardware evidence. No sprints are launched in parallel or delegated by this plan.

## Gate and requirement ownership

| Gate | First owner sprint | Blocks |
|---|---|---|
| G-01 | S01 | G-01A blocks S1 mutations; G-01B blocks dependent executable work |
| G-02 | S01 | Trusting fitted residuals or hardware comparison |
| G-03 | S01 | Using extracted/guessed coefficients; dependent P0/P1 closure |
| G-04 | S02 (deferred external validation) | All hardware-fit conclusions and claims; not Track A implementation |
| G-05 | S02 | Calibrated machine references (S3/S4), cascade/product (S5+) |
| G-06 | S02 | PASS for hardware fits in S3/S4/S5 |
| G-07 | S05 | Production optimization, UI/defaults/presets |
| G-08 | S06 | Executable S6 numeric optimization and S7 runtime criteria |
| G-09 | S07 | Format delivery and final release verdict |
| G-10 | S07 | Product acceptance and S8 candidate completion |
| G-11 | S08 | Declaring RELEASE READY YES; any install/distribution |

| Sprint | Primary requirements / checks | Inherited prerequisites |
|---|---|---|
| S01 | REQ-001/VAL-001, REQ-002/VAL-002, REQ-003/VAL-003, REQ-004/VAL-004, REQ-028/VAL-028 | All prior accepted requirements and affected regression; contract-specific hardware/human/target gates |
| S02 | REQ-005/VAL-005, REQ-006/VAL-006, REQ-007/VAL-007 | All prior accepted requirements and affected regression; contract-specific hardware/human/target gates |
| S03 | REQ-008/VAL-008, REQ-009/VAL-009, REQ-010/VAL-010, REQ-011/VAL-011, REQ-017/VAL-017, REQ-018/VAL-018 | All prior accepted requirements and affected regression; contract-specific hardware/human/target gates |
| S04 | REQ-012/VAL-012, REQ-013/VAL-013, REQ-014/VAL-014 | All prior accepted requirements and affected regression; contract-specific hardware/human/target gates |
| S05 | REQ-015/VAL-015, REQ-016/VAL-016 | All prior accepted requirements and affected regression; contract-specific hardware/human/target gates |
| S06 | REQ-019/VAL-019, REQ-020/VAL-020, REQ-021/VAL-021, REQ-022/VAL-022 | All prior accepted requirements and affected regression; contract-specific hardware/human/target gates |
| S07 | REQ-023/VAL-023, REQ-024/VAL-024, REQ-025/VAL-025, REQ-026/VAL-026 | All prior accepted requirements and affected regression; contract-specific hardware/human/target gates |
| S08 | REQ-027/VAL-027 | All prior accepted requirements and affected regression; contract-specific hardware/human/target gates |

## Readiness and resumption

Repository/baseline/branch/stack/commands are known (Sprint 1); targets/budgets (G-08/G-09) and hardware thresholds (G-06) remain UNKNOWN. Track A readiness is gated by owner approval of EXECUTION_PLAN_V2 §4; release readiness remains NO. Subsequent required owner/hardware gates pause only the affected dependent work. ResearchConfiguration cannot be changed to quietly bypass a failed gate. PROJECT_HANDOFF is the durable actual state; accepted milestones are inspected before resuming, never rerun merely because a new chat starts.
