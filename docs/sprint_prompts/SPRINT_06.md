# Sprint 06 — Production shared engine, parameter freeze and optimization

Revision: planning V1 · 2026-10-06

Status: DRAFT PLANNING CONTRACT. Documentation creation authorized; implementation and release not authorized.

Contract revision: V1 · owner execution approval PENDING. Authoritative file: docs/sprint_prompts/SPRINT_06.md.

## Objective

Build the selected real-time-capable shared engine and product state/controls, proving reference agreement without introducing new coloration.

## Prerequisites and starting state

Accepted S5/G-07; G-08 numeric and parameter policy approved before changes: proxy/rate kernel, precision, cross-platform and reference tolerances, maximum inputs/blocks, CPU/latency budget, IDs/ranges/defaults/smoothing/version. Current planning state: NOT STARTED. Previous milestone/commit UNKNOWN until executed. Before editing resolve previous actual report/implementation commit and exact working SHA; an expected PASS is not a prerequisite. GATE_REGISTER defines blocking evidence and owners.

## Read first

Read root AGENTS.md, README.md, docs/README.md, docs/PROJECT_HANDOFF.md and docs/SPRINT_PLAN.md. Exact additional files: `docs/CONFIDENCE.md`, `docs/DECISIONS.md`, `docs/ENGINE_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/RATE_GAIN_PLAN.md`, `docs/PARAMETERS.md`, `docs/VALIDATION_PLAN.md`. Relevant source sections/IDs and assets: ENGINE_SPEC, ARCHITECTURE, PARAMETERS, RATE_GAIN_PLAN, VALIDATION_PLAN, DECISIONS, CONFIDENCE; selected asset versions/product decision; research §43 real-time/parameter/bypass; REQ-019..022. Then reread this entire contract and exact check rows in docs/ACCEPTANCE_MATRIX.md. Required source V1 Markdown governs JSON; source filenames are indexed in docs/README.md. Sprint8 also reads all actual reports, manifests and current documents after execution.

## Allowed scope and non-goals

Shared production engine/config/state/offline renderer/tests/benchmarks, immutable reviewed assets, research/validation rate/alias/reference comparisons, evidence/sprint_06. No plugin-specific alternate sound or production research switches. Actual source directories/language are established by Sprint1; no guessed path is an authorization. Before implementation map these subsystem permissions to real repository paths and document mapping in command/preflight record. Historical docs/research inputs immutable. Other sprint features forbidden; no external repository mutation or destructive cleanup. No hidden saturation/noise/jitter/mismatch/sag/tuned playback/SSM filter/reverse-order product/limiter/normalization. Current session remains planning only.

## Work in dependency order

1. Implement selected retained modules/route using shared calibrated asset contracts. Reference remains comparison oracle; optimize only with measurable substitution budget and stable units.

2. Freeze ProductParameter IDs/types/units/ranges/defaults/normalized automation/smoothing, immutable Machine assets and research-only hypotheses. Define schema migration/rejection and versioned calibration identity.

3. Establish proxy/kernel/precision convergence and near-Nyquist/clamp alias tests; keep SP historical images/fold-back. Select numerical implementation only if G-08 limits and CPU/latency tradeoff pass.

4. Verify persistent machine timing on all candidate supported rates/common-band fixtures and irregular chunks; compare same-build bounce/reset/block partitions exactly. Cross-host rate quantizer-boundary error follows frozen policy, not an impossible absolute claim.

5. Prove optimized reference agreement on held-out stimuli and all selected parameters/routings; measure headroom/DC/clip and serialized state. Presets, if requested by approved product selection, store product fields only and document headroom without hidden normalization.

6. Benchmark prepared processing for bounded state/memory/CPU and publish actual metrics/environments. Keep commands/source/assets/config/input hashes attached and update current behavior docs only.

## Required build and checks

Run the approved configure/build/inherited regression plus every listed check. Commands are currently UNKNOWN; Sprint1 must establish docs/BUILD_COMMANDS.md with exact tool versions, shell commands/flags, working directory, check IDs and evidence routes. Until commands and required numeric criteria are frozen this is a DRAFT/BLOCKED executable contract. Do not write a speculative build command and call it validated. Structural exact criteria below are planning requirements; hardware G-06 and production G-08 numeric bounds must exist before the dependent check.

| Check / requirement | Stimulus/configuration | Expected / tolerance rationale | Environment | Evidence |
|---|---|---|---|---|
| VAL-019 / REQ-019 | Common-band analytic input at 44.1/48/88.2/96/176.4/192 kHz; irregular/one-sample/max blocks | Same-build repeated bounce and block partitions exactly agree; cross-rate/precision thresholds frozen at G-08; only shared representable continuous-input band compared | Reference and production runtime | research/validation/rate_block/ |
| VAL-020 / REQ-020 | Proxy-rate convergence, near-Nyquist tones, two-tone/stepped clamp levels | No band-limited reconstruction used instead of SP ZOH; implementation residual below G-08 budget; historical image/alias levels retain G-06 agreement | Offline + optimized engine | research/validation/implementation_alias/ |
| VAL-021 / REQ-021 | Held-out sines/transients/mixes; all selected paths, trims and gain states | Reference-production quantitative agreement within G-08 limits; no new independent plugin processing | Actual target builds | research/validation/reference_production/ |
| VAL-022 / REQ-022 | Parameter/state round trips, old-version load, factory preset diff, invalid config | Presets only product fields; calibration immutable/versioned; research inaccessible in release; stable IDs, units/defaults frozen after G-07; unknown never silently substituted | Product engine tests | evidence/sprint_06/state_parameter/ |


Capture source/assets/input/config hashes, environment, exact command and exit code, stimulus levels/rates/channels and threshold revision. Same-build exact determinism, cross-rate/platform tolerance, reference agreement and hardware fidelity are separate. Retain failures and compare against held-out data only. Tests cannot be loosened or goldens regenerated merely to fit current implementation. Invalid tests need independent defect rationale, exact diff, preservation of old evidence and rerun. Acceptance-policy changes require named owner decision first.

## Measurements and experiment gates

Proxy/precision convergence and cross-rate numerical experiments labeled SIMULATION/VALIDATION, not hardware measurement. Original hardware agreement G-06 still inherited. Record planned versus actual execution, limitations/uncertainty and artifact class. SIMULATION never becomes HARDWARE MEASUREMENT. No notebook-only conclusion; scripts/config/raw outputs and hashes persist. Numeric criterion UNKNOWN prevents PASS for that metric. Large raw captures/build artifacts use the approved durable evidence destination; repository retains provenance/hashes/regeneration commands without arbitrary bulky binaries.

## Human work

Owner/engineering lead freezes G-08 thresholds/controls/headroom before optimization; parameter or CPU/latency policy changes need a decision. Actual measured presets may need later G-10 listening. Required human/stock-unit/platform evidence cannot be substituted by agent judgment or previous-project history. Independent permitted tasks may continue within this sprint, but dependent tasks stop at their gate.

## Artifacts and documentation updates

Shared engine/offline tool/state schemas, asset version manifests, rate/chunk/alias/reference metrics and benchmarks, parameter freeze record; no completed plugin binary assumed. Update affected ENGINE_SPEC, ARCHITECTURE, PARAMETERS, CONFIDENCE, DECISIONS, RESEARCH_DEBT/GATE_REGISTER, VALIDATION_PLAN/ACCEPTANCE_MATRIX and DSP_CHANGELOG only where actual work/evidence changes them. Preserve original sources unchanged. Update PROJECT_HANDOFF with current source/phase/tests/blockers/next action; no unexecuted future report is created.

## Observable Definition of Done

All exact/numeric checks pass under G-08; production matches accepted reference; parameter layers and persistence rules tested; no unknown release default or research switch; budgets met on chosen evaluation target. Required tests have actual execution logs/exit codes/evidence, diff matches scope, valid inherited tests pass and no unsupported source status is promoted. Report must distinguish implementation acceptance from hardware/production/native release readiness. On BLOCKED, record partial artifacts truthfully; do not label milestone complete.

## Automatic continue gate

S7 requires accepted engine plus actual approved native formats/SDK/hosts and G-09 execution capabilities. Missing native target blocks affected wrapper validation. Continuation is enabled only by a future execution-authorized orchestrator invocation. A manual sprint run stops after its report/permitted checkpoint. No elapsed time, empty answer or generated contract itself counts as approval.

## Stop and escalation

Unknown numeric/control criterion, CPU/latency tradeoff requiring unapproved fidelity loss, invalid golden relaxation, inaccessible real-time target or product/reference residual outside budget. Also stop affected dependency on source/spec conflict, required unknown value/threshold, changed accepted design, unauthorized destructive action/payment/credentials, exceeded budget or unapproved distribution. Record blocker ID, evidence, impact, options and exact next needed action. Never silently declare a mandatory gate nonblocking.

## Review, commit and report

Inspect full diff, test/requirement coverage, scope leakage, authority labels and evidence hashes. Future report: docs/sprint_reports/SPRINT_06_REPORT.md (not created now). Include baseline/branch/working SHA, authorization, work, exact checks/results/metrics, artifacts, decisions, limitations, verdict and continuation gate. Local milestone message if explicitly authorized: `sprint 06: production shared engine, parameter freeze and optimization`. Commit only an accepted milestone. A blocker progress checkpoint may be made only if authorized and clearly labeled incomplete, never an accepted milestone. Do not claim an ending hash inside its own report before it exists; print hash after commit or record next-state index. Push/merge/publish/deploy/install permission: NONE by this planning request. Preserve dirty user work, no stash/reset/history rewrite. No delegation/agent launch is implied by this contract.
