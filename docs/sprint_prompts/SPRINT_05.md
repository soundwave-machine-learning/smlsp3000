# Sprint 05 — Cascade validation, blind listening and product selection

Revision: planning V1 · 2026-10-06

Status: DRAFT PLANNING CONTRACT. Documentation creation authorized; implementation and release not authorized.

Contract revision: V1 · owner execution approval PENDING. Authoritative file: docs/sprint_prompts/SPRINT_05.md.

## Objective

Integrate physical SP→MPC calibration, validate the reference cascade and choose shipping path/outputs/retained blocks using evidence and owner listening.

## Prerequisites and starting state

Accepted S3/S4, G-05/G-06, CHAIN-EXP-012 calibrated physical cascade. G-07 listening/selection protocol criterion frozen before trials; owner/listeners available. Current planning state: NOT STARTED. Previous milestone/commit UNKNOWN until executed. Before editing resolve previous actual report/implementation commit and exact working SHA; an expected PASS is not a prerequisite. GATE_REGISTER defines blocking evidence and owners.

## Read first

Read root AGENTS.md, README.md, docs/README.md, docs/PROJECT_HANDOFF.md and docs/SPRINT_PLAN.md. Exact additional files: `docs/CONFIDENCE.md`, `docs/DECISIONS.md`, `docs/ENGINE_SPEC.md`, `docs/RATE_GAIN_PLAN.md`, `docs/PARAMETERS.md`, `docs/VALIDATION_PLAN.md`, `docs/LISTENING_TEST_PLAN.md`. Relevant source sections/IDs and assets: DECISIONS, ENGINE_SPEC, RATE_GAIN_PLAN, LISTENING_TEST_PLAN, VALIDATION_PLAN, PARAMETERS, CONFIDENCE; CHAIN-DEC-001/003/005/012/013/014; CHAIN-EXP-012/013/014/018; research §§22–26,31–33,41–43. Then reread this entire contract and exact check rows in docs/ACCEPTANCE_MATRIX.md. Required source V1 Markdown governs JSON; source filenames are indexed in docs/README.md. Sprint8 also reads all actual reports, manifests and current documents after execution.

## Allowed scope and non-goals

Reference cascade/calibration code/tests, research/fit/cascade, research/validation/cascade, research/listening, evidence/sprint_05/product_decision.json and living product scope docs. Actual source directories/language are established by Sprint1; no guessed path is an authorization. Before implementation map these subsystem permissions to real repository paths and document mapping in command/preflight record. Historical docs/research inputs immutable. Other sprint features forbidden; no external repository mutation or destructive cleanup. No hidden saturation/noise/jitter/mismatch/sag/tuned playback/SSM filter/reverse-order product/limiter/normalization. Current session remains planning only.

## Work in dependency order

1. Connect R0/R10/R16 with measured volts/gain at documented SP output and MPC record-level/gain settings; expose taps and compare composed references to physical chain on held-out stimuli.

2. Check image admission, clip boundary/headroom, LF/HF phase/group delay, noise/IMD/crest/stereo across DRY/SP/MPC/SP→MPC at calibrated levels. Keep level-matched listening derivatives separate from fidelity-null data.

3. Run CHAIN-EXP-014 comparative contribution suite; CHAIN-EXP-013 reverse order may be informative only. If source says informational, record nonblocking disposition; do not add reverse shipping switch.

4. Prepare blinded hardware/reference/simplified/bypass listening conditions with logged RMS match and source hashes. Execute approved CHAIN-EXP-018 protocol, retain actual responses, not invented audibility predictions.

5. Propose lowest-complexity candidate consistent with objective metrics/listening. Owner chooses A/B/C, canonical SP output and measured variants, MPC output scope, linked-stereo label, controls/default meanings and whether any abstraction is retained.

6. Freeze selected product brief and module/parameter/claim boundary; note that choosingA may change modeling claim and choosingC requires reduction evidence. Any material scope change revises downstream sprint/matrix before continuation.

## Required build and checks

Run the approved configure/build/inherited regression plus every listed check. Commands are currently UNKNOWN; Sprint1 must establish docs/BUILD_COMMANDS.md with exact tool versions, shell commands/flags, working directory, check IDs and evidence routes. Until commands and required numeric criteria are frozen this is a DRAFT/BLOCKED executable contract. Do not write a speculative build command and call it validated. Structural exact criteria below are planning requirements; hardware G-06 and production G-08 numeric bounds must exist before the dependent check.

| Check / requirement | Stimulus/configuration | Expected / tolerance rationale | Environment | Evidence |
|---|---|---|---|---|
| VAL-015 / REQ-015 | Physical SP→MPC captures at recorded gain/pot settings; held-out excerpts | Interstage volts and trim default from measured setting, not unity digital assumption; cascade within G-06 limits | Both units + reference | research/validation/cascade/ |
| VAL-016 / REQ-016 | B reference versus A/C candidates; blind hardware/reference/simplified/bypass trials | Owner selects A/B/C, SP route, MPC route and controls with reason; no automatic promotion of B; logged listening and retained validation limits | Owner/listeners + fitted offline models | research/listening/CHAIN-EXP-018/; evidence/sprint_05/product_decision.json |


Capture source/assets/input/config hashes, environment, exact command and exit code, stimulus levels/rates/channels and threshold revision. Same-build exact determinism, cross-rate/platform tolerance, reference agreement and hardware fidelity are separate. Retain failures and compare against held-out data only. Tests cannot be loosened or goldens regenerated merely to fit current implementation. Invalid tests need independent defect rationale, exact diff, preservation of old evidence and rerun. Acceptance-policy changes require named owner decision first.

## Measurements and experiment gates

CHAIN-EXP-012 validation,014 contribution and018 human trial mandatory for selection;013 informational only. Fitted models and accepted protocol prerequisite. Record planned versus actual execution, limitations/uncertainty and artifact class. SIMULATION never becomes HARDWARE MEASUREMENT. No notebook-only conclusion; scripts/config/raw outputs and hashes persist. Numeric criterion UNKNOWN prevents PASS for that metric. Large raw captures/build artifacts use the approved durable evidence destination; repository retains provenance/hashes/regeneration commands without arbitrary bulky binaries.

## Human work

Owner/product lead listens and records G-07 selection/claim limits. Missing owner judgment blocks S6; automatic continuation cannot select shipping defaults. Required human/stock-unit/platform evidence cannot be substituted by agent judgment or previous-project history. Independent permitted tasks may continue within this sprint, but dependent tasks stop at their gate.

## Artifacts and documentation updates

Cascade reference/taps, calibrated interstage asset, validation metrics, listening stimuli/randomization/logs, signed product_decision with paths/control intent and retained/removed block reasoning. Update affected ENGINE_SPEC, ARCHITECTURE, PARAMETERS, CONFIDENCE, DECISIONS, RESEARCH_DEBT/GATE_REGISTER, VALIDATION_PLAN/ACCEPTANCE_MATRIX and DSP_CHANGELOG only where actual work/evidence changes them. Preserve original sources unchanged. Update PROJECT_HANDOFF with current source/phase/tests/blockers/next action; no unexecuted future report is created.

## Observable Definition of Done

Cascade passes frozen hardware criteria; human listening recorded; G-07 resolves A/B/C/SP/MPC defaults/retained mechanisms. No undecided default remains hidden in downstream product tasks. Required tests have actual execution logs/exit codes/evidence, diff matches scope, valid inherited tests pass and no unsupported source status is promoted. Report must distinguish implementation acceptance from hardware/production/native release readiness. On BLOCKED, record partial artifacts truthfully; do not label milestone complete.

## Automatic continue gate

S6 requires G-07 decision and G-08 production numeric/CPU/latency/parameter budgets fixed before optimization. Evidence never silently grants new scope. Continuation is enabled only by a future execution-authorized orchestrator invocation. A manual sprint run stops after its report/permitted checkpoint. No elapsed time, empty answer or generated contract itself counts as approval.

## Stop and escalation

No calibrated chain, failed held-out cascade, no actual listening, unknown owner choice, inability to justify block reduction, or new unsupported product mode. Also stop affected dependency on source/spec conflict, required unknown value/threshold, changed accepted design, unauthorized destructive action/payment/credentials, exceeded budget or unapproved distribution. Record blocker ID, evidence, impact, options and exact next needed action. Never silently declare a mandatory gate nonblocking.

## Review, commit and report

Inspect full diff, test/requirement coverage, scope leakage, authority labels and evidence hashes. Future report: docs/sprint_reports/SPRINT_05_REPORT.md (not created now). Include baseline/branch/working SHA, authorization, work, exact checks/results/metrics, artifacts, decisions, limitations, verdict and continuation gate. Local milestone message if explicitly authorized: `sprint 05: cascade validation, blind listening and product selection`. Commit only an accepted milestone. A blocker progress checkpoint may be made only if authorized and clearly labeled incomplete, never an accepted milestone. Do not claim an ending hash inside its own report before it exists; print hash after commit or record next-state index. Push/merge/publish/deploy/install permission: NONE by this planning request. Preserve dirty user work, no stash/reset/history rewrite. No delegation/agent launch is implied by this contract.
