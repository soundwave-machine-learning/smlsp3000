# Sprint 04 — Calibrated MPC reference and path comparison

Revision: planning V1 · 2026-10-06

Status: DRAFT PLANNING CONTRACT. Documentation creation authorized; implementation and release not authorized.

Contract revision: V1 · owner execution approval PENDING. Authoritative file: docs/sprint_prompts/SPRINT_04.md.

## Objective

Implement R11–R15 offline with measured linear/converter/storage/level behavior and honestly characterize whether an undriven MPC contribution exists.

## Prerequisites and starting state

Accepted S3; G-05/G-06 MPC data/rules/levels and de-emphasis disposition closed. Measured main/individual paths and digital observations, not assumed converter imperfections. Current planning state: NOT STARTED. Previous milestone/commit UNKNOWN until executed. Before editing resolve previous actual report/implementation commit and exact working SHA; an expected PASS is not a prerequisite. GATE_REGISTER defines blocking evidence and owners.

## Read first

Read root AGENTS.md, README.md, docs/README.md, docs/PROJECT_HANDOFF.md and docs/SPRINT_PLAN.md. Exact additional files: `docs/CONFIDENCE.md`, `docs/ENGINE_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/RATE_GAIN_PLAN.md`, `docs/PARAMETERS.md`, `docs/VALIDATION_PLAN.md`. Relevant source sections/IDs and assets: ENGINE_SPEC, ARCHITECTURE, RATE_GAIN_PLAN, CONFIDENCE, PARAMETERS, VALIDATION_PLAN; MPC3K-CLM-001..020; CHAIN-DEC-006/011; research §§14–21,28–32; R11–R15; AUD-C04/05. Then reread this entire contract and exact check rows in docs/ACCEPTANCE_MATRIX.md. Required source V1 Markdown governs JSON; source filenames are indexed in docs/README.md. Sprint8 also reads all actual reports, manifests and current documents after execution.

## Allowed scope and non-goals

Offline MPC reference/modules/tests/assets, research/fit/mpc3000, research/validation/mpc3000, evidence/sprint_04. No generic saturation/voice sampler/UI/reverse product route. Actual source directories/language are established by Sprint1; no guessed path is an authorization. Before implementation map these subsystem permissions to real repository paths and document mapping in command/preflight record. Historical docs/research inputs immutable. Other sprint features forbidden; no external repository mutation or destructive cleanup. No hidden saturation/noise/jitter/mismatch/sag/tuned playback/SSM filter/reverse-order product/limiter/normalization. Current session remains planning only.

## Work in dependency order

1. Preserve44100 machine domain, measured input switch/pot curves and FS volts, explicit analog vs ADC boundaries and validated recovery behavior. Sensitivity values do not substitute for converter FS.

2. Implement ADC linear decimation/latency as measured or documented;18-bit converter candidate and R13 storage16-bit behavior distinct. Use only identifiable reduction/arithmetic under approved closure; no unsupported rounding/dither claim from S/PDIF.

3. Populate R14 unity and R15 separate main reconstruction/I-V/LP/coupling/gain. Architecture contains8× interpolation; response/de-emphasis configuration comes from evidence, not an arbitrary oversampling kernel presented as authentic.

4. Compare individual pair to main with held-out loaded sounds; keep paths isolated and phones excluded. If measured equivalence permits shared coefficients, document evidence and allowed tolerance.

5. Quantify low-level, THD/IMD/noise and driven recovery against held-out evidence. A transparent MPC result is acceptable; unexplained residual opens investigation/decision rather than invented warmth.

6. Preserve stereo independent signal histories/shared sample clock; emit reference assets/provenance and update implemented confidence/changelog. Product MPC output recommendation stays pending owner G-07.

## Required build and checks

Run the approved configure/build/inherited regression plus every listed check. Commands are currently UNKNOWN; Sprint1 must establish docs/BUILD_COMMANDS.md with exact tool versions, shell commands/flags, working directory, check IDs and evidence routes. Until commands and required numeric criteria are frozen this is a DRAFT/BLOCKED executable contract. Do not write a speculative build command and call it validated. Structural exact criteria below are planning requirements; hardware G-06 and production G-08 numeric bounds must exist before the dependent check.

| Check / requirement | Stimulus/configuration | Expected / tolerance rationale | Environment | Evidence |
|---|---|---|---|---|
| VAL-012 / REQ-012 | 44.1 kHz S/PDIF known 16-bit patterns, analog low-level exports, loaded synthetic sounds | 44.1 kHz domain; 18-bit converter architecture and 16-bit storage preserved; rule/arithmetic only as identifiable; S/PDIF cannot alone prove 18→16 rule | Offline reference + MPC routes | research/validation/mpc3000/digital/ |
| VAL-013 / REQ-013 | Main L/R sweep, impulse, stepped sines, overload recovery, low-level and IMD | Complex responses, FS volts and residuals within G-06 limits; no default saturation; observed recovery escalated as required | Offline + stock MPC analog data | research/validation/mpc3000/analog/ |
| VAL-014 / REQ-014 | Same synthetic sound to main L/R and one individual pair | Measured equivalence/difference documented; no silent substitution; headphones excluded; main path is recommendation pending product decision | MPC + offline reference | research/validation/mpc3000/path_comparison/ |


Capture source/assets/input/config hashes, environment, exact command and exit code, stimulus levels/rates/channels and threshold revision. Same-build exact determinism, cross-rate/platform tolerance, reference agreement and hardware fidelity are separate. Retain failures and compare against held-out data only. Tests cannot be loosened or goldens regenerated merely to fit current implementation. Invalid tests need independent defect rationale, exact diff, preservation of old evidence and rerun. Acceptance-policy changes require named owner decision first.

## Measurements and experiment gates

Consume CHAIN-EXP-008..011/015/020. Additional targeted residual study only if existing closure/fit blocks; record NOT EXECUTED for missing data. Record planned versus actual execution, limitations/uncertainty and artifact class. SIMULATION never becomes HARDWARE MEASUREMENT. No notebook-only conclusion; scripts/config/raw outputs and hashes persist. Numeric criterion UNKNOWN prevents PASS for that metric. Large raw captures/build artifacts use the approved durable evidence destination; repository retains provenance/hashes/regeneration commands without arbitrary bulky binaries.

## Human work

Evidence reviewer accepts output/input fits and limits, including unknown internal mechanism if restricted identifiable model is owner-approved. No folklore authenticity verdict. Required human/stock-unit/platform evidence cannot be substituted by agent judgment or previous-project history. Independent permitted tasks may continue within this sprint, but dependent tasks stop at their gate.

## Artifacts and documentation updates

MPC reference/assets/tests, main/individual metrics, digital bit comparisons/identifiability note, THD/IMD/recovery/complex-response reports with hashes. Update affected ENGINE_SPEC, ARCHITECTURE, PARAMETERS, CONFIDENCE, DECISIONS, RESEARCH_DEBT/GATE_REGISTER, VALIDATION_PLAN/ACCEPTANCE_MATRIX and DSP_CHANGELOG only where actual work/evidence changes them. Preserve original sources unchanged. Update PROJECT_HANDOFF with current source/phase/tests/blockers/next action; no unexecuted future report is created.

## Observable Definition of Done

Frozen digital and analog checks pass on held-out data;18/16 distinction documented; path comparison and unity arithmetic rationale explicit; no generic nonlinear or noise behavior added. Required tests have actual execution logs/exit codes/evidence, diff matches scope, valid inherited tests pass and no unsupported source status is promoted. Report must distinguish implementation acceptance from hardware/production/native release readiness. On BLOCKED, record partial artifacts truthfully; do not label milestone complete.

## Automatic continue gate

S5 begins only with both accepted references and physical cascade/interstage S2 evidence plus available listening protocol/owner. Continuation is enabled only by a future execution-authorized orchestrator invocation. A manual sprint run stops after its report/permitted checkpoint. No elapsed time, empty answer or generated contract itself counts as approval.

## Stop and escalation

Non-identifiable required rule, unmodeled overload dynamics, active unexpected de-emphasis, analog response/level mismatch or attempt to force undriven coloration. Also stop affected dependency on source/spec conflict, required unknown value/threshold, changed accepted design, unauthorized destructive action/payment/credentials, exceeded budget or unapproved distribution. Record blocker ID, evidence, impact, options and exact next needed action. Never silently declare a mandatory gate nonblocking.

## Review, commit and report

Inspect full diff, test/requirement coverage, scope leakage, authority labels and evidence hashes. Future report: docs/sprint_reports/SPRINT_04_REPORT.md (not created now). Include baseline/branch/working SHA, authorization, work, exact checks/results/metrics, artifacts, decisions, limitations, verdict and continuation gate. Local milestone message if explicitly authorized: `sprint 04: calibrated mpc reference and path comparison`. Commit only an accepted milestone. A blocker progress checkpoint may be made only if authorized and clearly labeled incomplete, never an accepted milestone. Do not claim an ending hash inside its own report before it exists; print hash after commit or record next-state index. Push/merge/publish/deploy/install permission: NONE by this planning request. Preserve dirty user work, no stash/reset/history rewrite. No delegation/agent launch is implied by this contract.
