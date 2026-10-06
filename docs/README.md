# Engineering documentation index

Revision: planning V1 · 2026-10-06

Status: DRAFT PLANNING CONTRACT. Documentation creation authorized; implementation and release not authorized.

## Authority and exact read order

Read root AGENTS.md/README.md, PROJECT_HANDOFF and PROJECT_BRIEF; then RESEARCH_AUDIT, immutable sourceV1 Markdown/JSON, CONFIDENCE, RESEARCH_DEBT, GATE_REGISTER and DECISIONS; then ENGINE_SPEC, ARCHITECTURE, RATE_GAIN_PLAN, PARAMETERS, EXPERIMENT_PLAN, MEASUREMENT_PLAN, VALIDATION_PLAN, LISTENING_TEST_PLAN, ACCEPTANCE_MATRIX and DSP_CHANGELOG; finally SPRINT_PLAN, all eight exact contracts and AUTONOMOUS_BUILD_PROMPT. Read DELIVERY_SUMMARY/PACKAGE_VALIDATION/manifests for delivery review. Commands, target matrices, threshold policies and execution reports are future artifacts; not missing promised files in this planning package.

Version: all generated documents planningV1 dated2026-10-06; supplied sourceV1 dated2026-10-05. Research Markdown governs JSON summary; research originals immutable. New engineering proposals do not supersede source evidence. Owner authorization is planning-only; execution/design/release approvals unknown. Vocabulary and authority lanes are in CONFIDENCE and AGENTS.

## Document map

| Path | Role | Update trigger | Owner |
|---|---|---|---|
| [docs/RESEARCH_AUDIT.md](RESEARCH_AUDIT.md) | Evidence/conflict audit | Evidence, approved scope, or contract revision changes | Cross-sprint |
| [docs/RESEARCH_DEBT.md](RESEARCH_DEBT.md) | All 28 debt items with closure policy | Evidence, approved scope, or contract revision changes | S1/S2, decisions S5 |
| [docs/GATE_REGISTER.md](GATE_REGISTER.md) | Dependency/measurement/approval gates | Evidence, approved scope, or contract revision changes | S1–S8 |
| [docs/CONFIDENCE.md](CONFIDENCE.md) | Full 54-claim register and 27-source inventory | Evidence, approved scope, or contract revision changes | Cross-sprint |
| [docs/DECISIONS.md](DECISIONS.md) | 16 original decisions and engineering proposals | Evidence, approved scope, or contract revision changes | Cross-sprint |
| [docs/ENGINE_SPEC.md](ENGINE_SPEC.md) | 28 traceable requirements; behavior and interfaces | Evidence, approved scope, or contract revision changes | Cross-sprint |
| [docs/PROJECT_BRIEF.md](PROJECT_BRIEF.md) | Project goal, targets, authorization and non-goals | Evidence, approved scope, or contract revision changes | Cross-sprint |
| [docs/ARCHITECTURE.md](ARCHITECTURE.md) | All R0–R16 boundaries, ownership and runtime semantics | Evidence, approved scope, or contract revision changes | Cross-sprint |
| [docs/RATE_GAIN_PLAN.md](RATE_GAIN_PLAN.md) | Rate ratios, calibration units and explicit clipping | Evidence, approved scope, or contract revision changes | Cross-sprint |
| [docs/PARAMETERS.md](PARAMETERS.md) | Product/Machine/Research separation; no invented defaults | Evidence, approved scope, or contract revision changes | Cross-sprint |
| [docs/EXPERIMENT_PLAN.md](EXPERIMENT_PLAN.md) | Full experiment register and dependency methods | Evidence, approved scope, or contract revision changes | S1/S2/S3/S4/S5 |
| [docs/MEASUREMENT_PLAN.md](MEASUREMENT_PLAN.md) | Hardware setup/stimuli/calibration/split protocol | Evidence, approved scope, or contract revision changes | S2 |
| [docs/VALIDATION_PLAN.md](VALIDATION_PLAN.md) | Acceptance/check policy; honest command/target status | Evidence, approved scope, or contract revision changes | Cross-sprint |
| [docs/LISTENING_TEST_PLAN.md](LISTENING_TEST_PLAN.md) | Mandatory human test method and decision records | Evidence, approved scope, or contract revision changes | S5/S7 |
| [docs/ACCEPTANCE_MATRIX.md](ACCEPTANCE_MATRIX.md) | Complete 28-row requirement-to-check/evidence mapping | Evidence, approved scope, or contract revision changes | Cross-sprint |
| [docs/ACCEPTANCE_MATRIX.csv](ACCEPTANCE_MATRIX.csv) | Machine-readable acceptance matrix | Acceptance requirement or gate revision | Cross-sprint |
| [docs/SPRINT_PLAN.md](SPRINT_PLAN.md) | Exact count, dependencies, gate and requirement map | Evidence, approved scope, or contract revision changes | Cross-sprint |
| [docs/AUTONOMOUS_BUILD_PROMPT.md](AUTONOMOUS_BUILD_PROMPT.md) | Eight-file read/execute/resume prompt; not launched | Evidence, approved scope, or contract revision changes | Cross-sprint |
| [docs/PROJECT_HANDOFF.md](PROJECT_HANDOFF.md) | Single durable continuity/state file | Evidence, approved scope, or contract revision changes | Cross-sprint |
| [docs/DSP_CHANGELOG.md](DSP_CHANGELOG.md) | Planned DSP baseline; execution-only future entries | Evidence, approved scope, or contract revision changes | Cross-sprint |
| [AGENTS.md](../AGENTS.md) | Read order, authority and repository/autonomy policy | Evidence, approved scope, or contract revision changes | Cross-sprint |
| [README.md](../README.md) | Entry point and honest readiness | Evidence, approved scope, or contract revision changes | Cross-sprint |
| [docs/DELIVERY_SUMMARY.md](DELIVERY_SUMMARY.md) | Self-contained requested final deliverable summary | Evidence, approved scope, or contract revision changes | Cross-sprint |

## Sprint and original source index

Exactly eight separate files docs/sprint_prompts/SPRINT_01.md throughSPRINT_08.md; links and dependencies in SPRINT_PLAN. Original [research package](research/SP1200_MPC3000_MIX_PROCESSOR_RESEARCH_PACKAGE_V1.md) and [JSON handoff](research/SP1200_MPC3000_HANDOFF_V1.json) are exact provided bytes renamed only to canonical package filenames. Their original attachment names included(1); source checksums in manifest/validation. No copyrighted manual/datasheet bytes redistributed. Referenced27 external source IDs remain REPORTED access; original materials not retrieved here.

## Chosen document set and omissions

All relevant audio engineering roles are substantive. Added RESEARCH_AUDIT/RESEARCH_DEBT/GATE_REGISTER separate evidence/dependencies from spec; RATE_GAIN_PLAN consolidates rate/converter/calibration/delay policy; LISTENING_TEST_PLAN has a mandatory human gate; ACCEPTANCE_MATRIX Markdown/CSV is one logical matrix for navigation and machine use. No separate REQUIREMENTS.md because ENGINE_SPEC plus acceptance mapping owns those IDs. No extra SOURCE_REGISTER because CONFIDENCE owns source access. No standalone rejected-ideas file because original§39 and spec/AGENTS preserve exclusions. No separate execution-status file beyond PROJECT_HANDOFF. No generated completed sprint_reports directory or final build report. No BUILD_COMMANDS/target/threshold placeholder presented as executable; these are named future Sprint1/2/6 deliverables.

## Update dependencies and conflicts

Evidence change updates CONFIDENCE/debt/gates; material design change records DECISIONS and affected spec/architecture/parameters/matrix/contracts. Numeric threshold changes revise signed policy and check rows before dependent reruns. Runtime result updates changelog/actual report/handoff, not historical source. Cross-document consistency is recorded PASS/FAIL/UNRESOLVED in PACKAGE_VALIDATION; material decision conflicts remain OPEN until named owner gate, even when files consistently mark them unknown.
