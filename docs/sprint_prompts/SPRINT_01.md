# Sprint 01 — Foundation, capability freeze and targeted source closure

Revision: planning V1 · 2026-10-06

Status: DRAFT PLANNING CONTRACT. Documentation creation authorized; implementation and release not authorized.

Contract revision: V1 · owner execution approval PENDING. Authoritative file: docs/sprint_prompts/SPRINT_01.md.

## Objective

Establish a reproducible analysis/evidence foundation and actual command/target contract before any hardware-fit claims. Attempt targeted documentary closure only for known gaps.

## Prerequisites and starting state

G-01 separate implementation authorization, actual repository/baseline/branch and permitted operations. The planning package exists; no code/commands/unit evidence are assumed. Current planning state: NOT STARTED. Previous milestone/commit UNKNOWN until executed. Before editing resolve previous actual report/implementation commit and exact working SHA; an expected PASS is not a prerequisite. GATE_REGISTER defines blocking evidence and owners.

## Read first

Read root AGENTS.md, README.md, docs/README.md, docs/PROJECT_HANDOFF.md and docs/SPRINT_PLAN.md. Exact additional files: `docs/RESEARCH_AUDIT.md`, `docs/RESEARCH_DEBT.md`, `docs/CONFIDENCE.md`, `docs/DECISIONS.md`, `docs/PROJECT_BRIEF.md`, `docs/EXPERIMENT_PLAN.md`, `docs/VALIDATION_PLAN.md`. Relevant source sections/IDs and assets: RESEARCH_AUDIT, PROJECT_BRIEF, CONFIDENCE, DECISIONS, EXPERIMENT_PLAN, VALIDATION_PLAN, RESEARCH_DEBT; research §§3–5,28–32,38–44; CHAIN-EXP-016/019/020; RD-P1-01..03/09/10. Then reread this entire contract and exact check rows in docs/ACCEPTANCE_MATRIX.md. Required source V1 Markdown governs JSON; source filenames are indexed in docs/README.md. Sprint8 also reads all actual reports, manifests and current documents after execution.

## Allowed scope and non-goals

docs/BUILD_COMMANDS.md, evidence/sprint_01, reference/sources, research/sim/CHAIN-EXP-016, build/test/evidence-schema foundation in the authorized repository. Actual source directories/language are established by Sprint1; no guessed path is an authorization. Before implementation map these subsystem permissions to real repository paths and document mapping in command/preflight record. Historical docs/research inputs immutable. Other sprint features forbidden; no external repository mutation or destructive cleanup. No hidden saturation/noise/jitter/mismatch/sag/tuned playback/SSM filter/reverse-order product/limiter/normalization. Current session remains planning only.

## Work in dependency order

1. Inspect actual repository/status/history/AGENTS and record exact baseline SHA, remotes/read authorization, runtime/tool versions, target proposals, budgets and available hardware/source access. Preserve user changes; no forced cleanup.

2. Select a project-appropriate reference/runtime stack and dependency/license route under G-01. Do not inherit SPZERO constants/framework/platform. Freeze exact command manifest for configure/build/tests/analysis/artifact checks and show smoke commands with actual exit codes.

3. Define immutable experiment/unit/config/asset schemas, artifact labels/hash manifest and independent FIT/VALIDATION identities. Build minimal analysis runner and pilot/alignment/null evaluator; self-test CHAIN-EXP-016 using independent synthetic truth before consuming measurements.

4. Obtain only readable missing source sheets and required datasheets using permitted access; trace nets and source locators; execute CHAIN-EXP-019/020 only for complete circuit sections. Record missing drawings/values/access failures and remaining P0/P1, never guess coefficients.

5. Document source-derived architecture/state interfaces and invalid-config semantics. A normalized digital skeleton is optional research scaffold only when separately authorized in G-01; no production DSP, no calibrated machine claim or fixture defaults disguised as factory settings.

6. Freeze command/version/evidence routes and framework floor, update open debt and measurement preparation tasks. Record target/human gates as OPEN rather than falsely completing later sprints.

## Required build and checks

Run the approved configure/build/inherited regression plus every listed check. Commands are currently UNKNOWN; Sprint1 must establish docs/BUILD_COMMANDS.md with exact tool versions, shell commands/flags, working directory, check IDs and evidence routes. Until commands and required numeric criteria are frozen this is a DRAFT/BLOCKED executable contract. Do not write a speculative build command and call it validated. Structural exact criteria below are planning requirements; hardware G-06 and production G-08 numeric bounds must exist before the dependent check.

| Check / requirement | Stimulus/configuration | Expected / tolerance rationale | Environment | Evidence |
|---|---|---|---|---|
| VAL-001 / REQ-001 | Compare originals, decision/debt IDs, all planned files | Source SHA-256 identical; exactly 8 contracts; zero fabricated implementation/results | Planner; then execution workspace | docs/PACKAGE_VALIDATION.md; evidence/sprint_01/provenance.json |
| VAL-002 / REQ-002 | Inventory execution OS, SDKs, repo, licenses, budgets and fresh smoke run | Known commands/versions/exit codes; missing target access explicitly blocked, no invented commands | Actual authorized repository | docs/BUILD_COMMANDS.md; evidence/sprint_01/preflight.json |
| VAL-003 / REQ-003 | Identical data; known scalar, fixed fractional delay, constant clock ratio, polarity and DC perturbations | Identical-array residual exactly zero; recovery errors measured against independently generated truth; nonzero tolerances frozen before real fits | Chosen numerical environment | research/sim/CHAIN-EXP-016/ |
| VAL-004 / REQ-004 | Readable sheets, net tracing, relevant component datasheets, AC simulations | Every used value tied to sheet/refdes/net; ambiguous values UNKNOWN; simulation explicitly labeled; no manual redistribution | Research workstation; source access | reference/sources/sp1200/; reference/sources/mpc3000/ |
| VAL-028 / REQ-028 | Dry review of ordering, dirty-tree case, missing gates, restart and report rules | Exactly 8 ordered contracts; blocked mandatory gate stops dependency; no reset/stash/push/merge/deploy; only accepted milestones resumed | Planning validator; later executor | docs/PACKAGE_VALIDATION.md; docs/PROJECT_HANDOFF.md |


Capture source/assets/input/config hashes, environment, exact command and exit code, stimulus levels/rates/channels and threshold revision. Same-build exact determinism, cross-rate/platform tolerance, reference agreement and hardware fidelity are separate. Retain failures and compare against held-out data only. Tests cannot be loosened or goldens regenerated merely to fit current implementation. Invalid tests need independent defect rationale, exact diff, preservation of old evidence and rerun. Acceptance-policy changes require named owner decision first.

## Measurements and experiment gates

CHAIN-EXP-016 mandatory framework. CHAIN-EXP-019/020 and datasheet extraction are targeted closure attempts; unavailable inputs remain OPEN. No simulation of guessed analog hardware. Record planned versus actual execution, limitations/uncertainty and artifact class. SIMULATION never becomes HARDWARE MEASUREMENT. No notebook-only conclusion; scripts/config/raw outputs and hashes persist. Numeric criterion UNKNOWN prevents PASS for that metric. Large raw captures/build artifacts use the approved durable evidence destination; repository retains provenance/hashes/regeneration commands without arbitrary bulky binaries.

## Human work

Owner approves execution repository/targets/stack/budgets under G-01; source reviewer inspects net extraction. Mandatory unavailable framework prerequisite blocks hardware comparison; documentary gaps can pass to S2 only when measurement can resolve them. Required human/stock-unit/platform evidence cannot be substituted by agent judgment or previous-project history. Independent permitted tasks may continue within this sprint, but dependent tasks stop at their gate.

## Artifacts and documentation updates

Command manifest, preflight/source hashes, simulator inputs/logs/transcriptions with rights notes, null self-test results/floor, schemas and updated debt. No manual scans redistributed. Update affected ENGINE_SPEC, ARCHITECTURE, PARAMETERS, CONFIDENCE, DECISIONS, RESEARCH_DEBT/GATE_REGISTER, VALIDATION_PLAN/ACCEPTANCE_MATRIX and DSP_CHANGELOG only where actual work/evidence changes them. Preserve original sources unchanged. Update PROJECT_HANDOFF with current source/phase/tests/blockers/next action; no unexecuted future report is created.

## Observable Definition of Done

Actual commands and smoke results are recorded; source integrity/count checks pass; null framework verifies independent truth; ambiguous source values remain UNKNOWN; G-01/G-02 resolved and G-03 disposition precise. Required tests have actual execution logs/exit codes/evidence, diff matches scope, valid inherited tests pass and no unsupported source status is promoted. Report must distinguish implementation acceptance from hardware/production/native release readiness. On BLOCKED, record partial artifacts truthfully; do not label milestone complete.

## Automatic continue gate

S2 capture preparation can continue only if G-01/G-02 pass and required units/calibration/routes/operator are actually available; missing documents stay explicit measurement prerequisites. Continuation is enabled only by a future execution-authorized orchestrator invocation. A manual sprint run stops after its report/permitted checkpoint. No elapsed time, empty answer or generated contract itself counts as approval.

## Stop and escalation

Unknown toolchain/commands, unauthorized repository work, invalid/null self-test, inaccessible necessary source with no valid measurement alternative, or material source/spec conflict. Also stop affected dependency on source/spec conflict, required unknown value/threshold, changed accepted design, unauthorized destructive action/payment/credentials, exceeded budget or unapproved distribution. Record blocker ID, evidence, impact, options and exact next needed action. Never silently declare a mandatory gate nonblocking.

## Review, commit and report

Inspect full diff, test/requirement coverage, scope leakage, authority labels and evidence hashes. Future report: docs/sprint_reports/SPRINT_01_REPORT.md (not created now). Include baseline/branch/working SHA, authorization, work, exact checks/results/metrics, artifacts, decisions, limitations, verdict and continuation gate. Local milestone message if explicitly authorized: `sprint 01: foundation, capability freeze and targeted source closure`. Commit only an accepted milestone. A blocker progress checkpoint may be made only if authorized and clearly labeled incomplete, never an accepted milestone. Do not claim an ending hash inside its own report before it exists; print hash after commit or record next-state index. Push/merge/publish/deploy/install permission: NONE by this planning request. Preserve dirty user work, no stash/reset/history rewrite. No delegation/agent launch is implied by this contract.
