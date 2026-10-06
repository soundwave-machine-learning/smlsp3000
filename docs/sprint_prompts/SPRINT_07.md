# Sprint 07 — Plugin wrapper, host/UI integration and real-time hardening

Revision: planning V1 · 2026-10-06

Status: DRAFT PLANNING CONTRACT. Documentation creation authorized; implementation and release not authorized.

Contract revision: V1 · owner execution approval PENDING. Authoritative file: docs/sprint_prompts/SPRINT_07.md.

## Objective

Integrate the shared engine into approved plugin formats/hosts with correct latency/bypass/state/automation and observable full-mix safety.

## Prerequisites and starting state

Accepted S6/G-08; actual G-09 target matrix, SDK/framework/license and native host access. G-10 final UI/listening protocol available; output/control design already selected. Current planning state: NOT STARTED. Previous milestone/commit UNKNOWN until executed. Before editing resolve previous actual report/implementation commit and exact working SHA; an expected PASS is not a prerequisite. GATE_REGISTER defines blocking evidence and owners.

## Read first

Read root AGENTS.md, README.md, docs/README.md, docs/PROJECT_HANDOFF.md and docs/SPRINT_PLAN.md. Exact additional files: `docs/DECISIONS.md`, `docs/ENGINE_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/RATE_GAIN_PLAN.md`, `docs/PARAMETERS.md`, `docs/VALIDATION_PLAN.md`, `docs/LISTENING_TEST_PLAN.md`. Relevant source sections/IDs and assets: ENGINE_SPEC, ARCHITECTURE, PARAMETERS, VALIDATION_PLAN, RATE_GAIN_PLAN, LISTENING_TEST_PLAN, DECISIONS; target matrix/command manifest; REQ-023..026; §43. Then reread this entire contract and exact check rows in docs/ACCEPTANCE_MATRIX.md. Required source V1 Markdown governs JSON; source filenames are indexed in docs/README.md. Sprint8 also reads all actual reports, manifests and current documents after execution.

## Allowed scope and non-goals

Approved plugin adapters/UI/state bridge/packaging foundation, native host test harness, manuals, evidence/sprint_07. All sound remains shared core; no unrelated brand/UI feature expansion. Actual source directories/language are established by Sprint1; no guessed path is an authorization. Before implementation map these subsystem permissions to real repository paths and document mapping in command/preflight record. Historical docs/research inputs immutable. Other sprint features forbidden; no external repository mutation or destructive cleanup. No hidden saturation/noise/jitter/mismatch/sag/tuned playback/SSM filter/reverse-order product/limiter/normalization. Current session remains planning only.

## Work in dependency order

1. Implement wrapper with approved bus/layout/rate validation, prepare/reset/reprepare policy, bounded parameter-event handoff, native state/preset restore and offline bounce using same engine.

2. Implement measured integer latency reporting/alignment and separate plugin/SP/MPC bypass semantics; test impulse alignment and automation changes, document any fixed alignment strategy without removing analog phase.

3. Build approved UI controls/meters/help from frozen parameter spec; show meaningful source/interstage/output headroom and clip indications, no hidden research/calibration editing or loudness compensation.

4. Instrument audio-thread allocation/locks/I/O, denormals and numerical failures; stress rate/block/automation/state changes, silence/overload/channel isolation and multiple instances. CPU/input policy follows frozen bounds.

5. Run native scan/load/reopen/automation/bounce/session restore in each required format/host, compare offline renders under G-08 platform budget. Cross-build results stay build-only; required native rows cannot be marked external-pending.

6. Conduct owner UI/manual/final listening review with headroom preset documentation and honest abstraction/claim wording; fix local integration defects without altering accepted DSP or thresholds.

## Required build and checks

Run the approved configure/build/inherited regression plus every listed check. Commands are currently UNKNOWN; Sprint1 must establish docs/BUILD_COMMANDS.md with exact tool versions, shell commands/flags, working directory, check IDs and evidence routes. Until commands and required numeric criteria are frozen this is a DRAFT/BLOCKED executable contract. Do not write a speculative build command and call it validated. Structural exact criteria below are planning requirements; hardware G-06 and production G-08 numeric bounds must exist before the dependent check.

| Check / requirement | Stimulus/configuration | Expected / tolerance rationale | Environment | Evidence |
|---|---|---|---|---|
| VAL-023 / REQ-023 | Impulse at each supported rate and routing; toggles and host compensation | Reported integer delay matches implemented alignment; measured frequency group delay separately retained; plugin bypass latency-aligned dry; machine bypass removes entire machine incl quantizer/rate process; no zero-latency claim | Approved host formats/DAWs | evidence/sprint_07/latency_bypass/ |
| VAL-024 / REQ-024 | Allocation/lock instrumentation; denormals, NaN/Inf, silence, extremes, rate/block changes, automation, state load | Zero audio-thread allocations/locks/I/O; finite bounded behavior under frozen input-domain policy; deterministic resets; no cross-channel state leak; CPU within G-08 budget | Actual target runtime + approved sanitizers | evidence/sprint_07/realtime_state/ |
| VAL-025 / REQ-025 | Clip and inter-sample-peak stimuli; quiet/wide mix; parameter automation; UI state restore | Boundary indicators correct to defined semantics; no hidden limiter/normalization/noise/jitter/mismatch; UI cannot alter calibration/research; headroom classes documented | Plugin/DAW + owner UI review | evidence/sprint_07/safety_ui/ |
| VAL-026 / REQ-026 | Same params/audio through offline and each approved format/host; reopen project/offline bounce | Agreement within G-08 platform budget; native host load/reload/automation/session restore passes; cross-build is not native validation | Only approved OS/CPU/format/host matrix | evidence/sprint_07/host_matrix/ |


Capture source/assets/input/config hashes, environment, exact command and exit code, stimulus levels/rates/channels and threshold revision. Same-build exact determinism, cross-rate/platform tolerance, reference agreement and hardware fidelity are separate. Retain failures and compare against held-out data only. Tests cannot be loosened or goldens regenerated merely to fit current implementation. Invalid tests need independent defect rationale, exact diff, preservation of old evidence and rerun. Acceptance-policy changes require named owner decision first.

## Measurements and experiment gates

Native host/runtime and UI evidence; final listening derivative of approved S5 protocol. No new modeled hardware mechanism added. Record planned versus actual execution, limitations/uncertainty and artifact class. SIMULATION never becomes HARDWARE MEASUREMENT. No notebook-only conclusion; scripts/config/raw outputs and hashes persist. Numeric criterion UNKNOWN prevents PASS for that metric. Large raw captures/build artifacts use the approved durable evidence destination; repository retains provenance/hashes/regeneration commands without arbitrary bulky binaries.

## Human work

Owner G-10 accepts UI/control/meter/bypass/headroom/manual/listening behavior. Platform operator supplies native host evidence G-09. Required human/stock-unit/platform evidence cannot be substituted by agent judgment or previous-project history. Independent permitted tasks may continue within this sprint, but dependent tasks stop at their gate.

## Artifacts and documentation updates

Actual native plugin builds under approved formats, host test logs/renders/source hashes, latency matrix, real-time instrumentation, state/automation evidence, manual and owner review record. Update affected ENGINE_SPEC, ARCHITECTURE, PARAMETERS, CONFIDENCE, DECISIONS, RESEARCH_DEBT/GATE_REGISTER, VALIDATION_PLAN/ACCEPTANCE_MATRIX and DSP_CHANGELOG only where actual work/evidence changes them. Preserve original sources unchanged. Update PROJECT_HANDOFF with current source/phase/tests/blockers/next action; no unexecuted future report is created.

## Observable Definition of Done

All selected native rows and real-time/latency/bypass/state/UI checks pass; plugin/offline equivalence demonstrated; owner G-10 acceptance actual; no hypothetical target pass. Required tests have actual execution logs/exit codes/evidence, diff matches scope, valid inherited tests pass and no unsupported source status is promoted. Report must distinguish implementation acceptance from hardware/production/native release readiness. On BLOCKED, record partial artifacts truthfully; do not label milestone complete.

## Automatic continue gate

S8 only after mandatory G-09/G-10 native/human proofs and inherited G-05..08 remain valid. Optional platforms must have prior explicit advisory designation. Continuation is enabled only by a future execution-authorized orchestrator invocation. A manual sprint run stops after its report/permitted checkpoint. No elapsed time, empty answer or generated contract itself counts as approval.

## Stop and escalation

Missing required native host or license, wrapper introduces alternate sonic path, allocation/lock/latency/state regression, mandatory owner judgment unavailable or scope drift. Also stop affected dependency on source/spec conflict, required unknown value/threshold, changed accepted design, unauthorized destructive action/payment/credentials, exceeded budget or unapproved distribution. Record blocker ID, evidence, impact, options and exact next needed action. Never silently declare a mandatory gate nonblocking.

## Review, commit and report

Inspect full diff, test/requirement coverage, scope leakage, authority labels and evidence hashes. Future report: docs/sprint_reports/SPRINT_07_REPORT.md (not created now). Include baseline/branch/working SHA, authorization, work, exact checks/results/metrics, artifacts, decisions, limitations, verdict and continuation gate. Local milestone message if explicitly authorized: `sprint 07: plugin wrapper, host/ui integration and real-time hardening`. Commit only an accepted milestone. A blocker progress checkpoint may be made only if authorized and clearly labeled incomplete, never an accepted milestone. Do not claim an ending hash inside its own report before it exists; print hash after commit or record next-state index. Push/merge/publish/deploy/install permission: NONE by this planning request. Preserve dirty user work, no stash/reset/history rewrite. No delegation/agent launch is implied by this contract.
