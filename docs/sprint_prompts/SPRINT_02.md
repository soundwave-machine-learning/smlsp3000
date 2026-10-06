# Sprint 02 — Hardware evidence, P0/P1 closure and acceptance freeze

Revision: planning V1 · 2026-10-06

Status: DRAFT PLANNING CONTRACT. Documentation creation authorized; implementation and release not authorized.

Contract revision: V1 · owner execution approval PENDING. Authoritative file: docs/sprint_prompts/SPRINT_02.md.

## Objective

Produce trustworthy stock-unit evidence and close prerequisite debt before calibrated SP/MPC fitting. Freeze thresholds from repeatability, not fitted-model outcomes.

## Prerequisites and starting state

Accepted S1 and G-01/G-02. G-04 valid stock units/routes/interface/operator; G-03 unresolved items must have documentary or measurement resolving plan. Measurement thresholds and listening product judgment are not assumed. Current planning state: NOT STARTED. Previous milestone/commit UNKNOWN until executed. Before editing resolve previous actual report/implementation commit and exact working SHA; an expected PASS is not a prerequisite. GATE_REGISTER defines blocking evidence and owners.

## Read first

Read root AGENTS.md, README.md, docs/README.md, docs/PROJECT_HANDOFF.md and docs/SPRINT_PLAN.md. Exact additional files: `docs/RESEARCH_AUDIT.md`, `docs/RESEARCH_DEBT.md`, `docs/GATE_REGISTER.md`, `docs/EXPERIMENT_PLAN.md`, `docs/MEASUREMENT_PLAN.md`, `docs/VALIDATION_PLAN.md`. Relevant source sections/IDs and assets: MEASUREMENT_PLAN, EXPERIMENT_PLAN, RESEARCH_DEBT, GATE_REGISTER, VALIDATION_PLAN, RESEARCH_AUDIT; research §§23–27,30–32,36,40–42; CHAIN-EXP-001..012/015; AUD-C03/04/05/10. Then reread this entire contract and exact check rows in docs/ACCEPTANCE_MATRIX.md. Required source V1 Markdown governs JSON; source filenames are indexed in docs/README.md. Sprint8 also reads all actual reports, manifests and current documents after execution.

## Allowed scope and non-goals

Measurement/stimulus/export analysis tooling, reference/hardware, research/validation policy/split, evidence/sprint_02 and affected living docs. External hardware capture by authorized operator only. Actual source directories/language are established by Sprint1; no guessed path is an authorization. Before implementation map these subsystem permissions to real repository paths and document mapping in command/preflight record. Historical docs/research inputs immutable. Other sprint features forbidden; no external repository mutation or destructive cleanup. No hidden saturation/noise/jitter/mismatch/sag/tuned playback/SSM filter/reverse-order product/limiter/normalization. Current session remains planning only.

## Work in dependency order

1. Prove import/export sample routes and actual units/revisions/stock status. Calibrate voltage/loopback/load, log pot/photos, instrument floor and warm-up stability; freeze segment/pilot/cycle/settling plan compatible with ≤2.3s SP sound length.

2. Run three captures per selected configuration with provenance/hashes. SP rate/input/quantizer, loaded output/hold/filter contacts/mix topology/levels/noise/skew follow CHAIN-EXP-001..007. Separate captured input offsets from playback slot skew.

3. Measure MPC digital/storage routes CHAIN-EXP-008, each gain/pot input/ADC CHAIN-EXP-009, loaded main outputs CHAIN-EXP-010 and individual comparison CHAIN-EXP-011. Distinguish sensitivity vs FS and 16-bit receiver data vs unidentified 18-bit reduction.

4. After gain measurements capture physical cascade CHAIN-EXP-012 and required IMD/overload-recovery characterization CHAIN-EXP-015. Verify whether residual effects are above measurement floor; no unsupported nonlinear fit.

5. Resolve bandwidth conflict: wideband instrument for208.33k spur if needed, otherwise record NOT OBSERVABLE with scope disposition; in-band noise evidence remains necessary. Complete all P0/P1 closure records with evidence, uncertainty and unresolved remainder.

6. Freeze disjoint FIT/VALIDATION captures before model fitting. Measure hardware-self-null floors; propose and obtain owner acceptance of numeric frequency/phase/delay/harmonic/IMD/image/null/stereo/crest and digital-code criteria by domain/level/material. Record exact metric algorithms and undefined-silence handling.

7. Resolve topology portion of RD-P0-04 from all measured paths without choosing shipping default; final factory decision remains S5/G-07. Stop if any mandatory P0/P1 cannot be supported; restricted-scope disposition requires owner approval and cannot silently waive unknown physics.

## Required build and checks

Run the approved configure/build/inherited regression plus every listed check. Commands are currently UNKNOWN; Sprint1 must establish docs/BUILD_COMMANDS.md with exact tool versions, shell commands/flags, working directory, check IDs and evidence routes. Until commands and required numeric criteria are frozen this is a DRAFT/BLOCKED executable contract. Do not write a speculative build command and call it validated. Structural exact criteria below are planning requirements; hardware G-06 and production G-08 numeric bounds must exist before the dependent check.

| Check / requirement | Stimulus/configuration | Expected / tolerance rationale | Environment | Evidence |
|---|---|---|---|---|
| VAL-005 / REQ-005 | Calibrated loopbacks; three takes per configuration; pilots and metadata | Calibration uncertainty/repeatability documented; hashes exact; valid route and no capture clipping; unsupported bandwidth claims rejected | Stock SP and MPC; calibrated interface | reference/hardware/; evidence/sprint_02/capture_manifest.json |
| VAL-006 / REQ-006 | Item-by-item 6 P0 + 12 P1 review against measurements/extraction | No OPEN blocking item treated as closed; scoped nonapplicability needs evidence and recorded owner acceptance; no blanket waiver | Evidence reviewer + owner | evidence/sprint_02/debt_closure.json |
| VAL-007 / REQ-007 | Hardware self-null repeats and instrument floor; held-out split IDs | Signed threshold policy with numeric bounds, rationale, uncertainty and domains before model fitting; held-out capture IDs disjoint | Measurement/review environment | research/validation/threshold_policy.json; research/validation/dataset_split.json |


Capture source/assets/input/config hashes, environment, exact command and exit code, stimulus levels/rates/channels and threshold revision. Same-build exact determinism, cross-rate/platform tolerance, reference agreement and hardware fidelity are separate. Retain failures and compare against held-out data only. Tests cannot be loosened or goldens regenerated merely to fit current implementation. Invalid tests need independent defect rationale, exact diff, preservation of old evidence and rerun. Acceptance-policy changes require named owner decision first.

## Measurements and experiment gates

CHAIN-EXP-001..012 and015 prerequisite evidence; no results assumed. CHAIN-EXP-013 reverse order and014 comparative listening derivatives are S5, informational vs mandatory as defined. Record planned versus actual execution, limitations/uncertainty and artifact class. SIMULATION never becomes HARDWARE MEASUREMENT. No notebook-only conclusion; scripts/config/raw outputs and hashes persist. Numeric criterion UNKNOWN prevents PASS for that metric. Large raw captures/build artifacts use the approved durable evidence destination; repository retains provenance/hashes/regeneration commands without arbitrary bulky binaries.

## Human work

Hardware operator captures real data. Evidence reviewer/owner accepts closure records and G-06 thresholds before fitting. No software agent manufactures unavailable measurement. Required human/stock-unit/platform evidence cannot be substituted by agent judgment or previous-project history. Independent permitted tasks may continue within this sprint, but dependent tasks stop at their gate.

## Artifacts and documentation updates

Raw captures/exports/stimuli and sidecars, calibration/uncertainty/pot photos, hash manifests, debt_closure.json, threshold_policy.json, dataset_split.json and gate decisions. Update affected ENGINE_SPEC, ARCHITECTURE, PARAMETERS, CONFIDENCE, DECISIONS, RESEARCH_DEBT/GATE_REGISTER, VALIDATION_PLAN/ACCEPTANCE_MATRIX and DSP_CHANGELOG only where actual work/evidence changes them. Preserve original sources unchanged. Update PROJECT_HANDOFF with current source/phase/tests/blockers/next action; no unexecuted future report is created.

## Observable Definition of Done

G-04/G-05/G-06 PASS with actual evidence; all18 prerequisite debt items have valid scoped resolutions; split frozen and numeric acceptance owner-approved. A missing hardware campaign is BLOCKED, never completed. Required tests have actual execution logs/exit codes/evidence, diff matches scope, valid inherited tests pass and no unsupported source status is promoted. Report must distinguish implementation acceptance from hardware/production/native release readiness. On BLOCKED, record partial artifacts truthfully; do not label milestone complete.

## Automatic continue gate

S3 begins only after its required SP data/calibration/coefficients and global acceptance/closure gates pass. MPC-dependent closures cannot be assumed for later S4. Continuation is enabled only by a future execution-authorized orchestrator invocation. A manual sprint run stops after its report/permitted checkpoint. No elapsed time, empty answer or generated contract itself counts as approval.

## Stop and escalation

Missing/modified units without approved scope, invalid capture/pilot/overload data, floor too high, ambiguous code mechanism, unavailable mandatory thresholds or any unresolved dependent P0/P1. Also stop affected dependency on source/spec conflict, required unknown value/threshold, changed accepted design, unauthorized destructive action/payment/credentials, exceeded budget or unapproved distribution. Record blocker ID, evidence, impact, options and exact next needed action. Never silently declare a mandatory gate nonblocking.

## Review, commit and report

Inspect full diff, test/requirement coverage, scope leakage, authority labels and evidence hashes. Future report: docs/sprint_reports/SPRINT_02_REPORT.md (not created now). Include baseline/branch/working SHA, authorization, work, exact checks/results/metrics, artifacts, decisions, limitations, verdict and continuation gate. Local milestone message if explicitly authorized: `sprint 02: hardware evidence, p0/p1 closure and acceptance freeze`. Commit only an accepted milestone. A blocker progress checkpoint may be made only if authorized and clearly labeled incomplete, never an accepted milestone. Do not claim an ending hash inside its own report before it exists; print hash after commit or record next-state index. Push/merge/publish/deploy/install permission: NONE by this planning request. Preserve dirty user work, no stash/reset/history rewrite. No delegation/agent launch is implied by this contract.
