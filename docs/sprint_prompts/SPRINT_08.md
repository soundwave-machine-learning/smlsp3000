# Sprint 08 — Reproducible release candidate, provenance and final review

Revision: planning V1 · 2026-10-06

Status: DRAFT PLANNING CONTRACT. Documentation creation authorized; implementation and release not authorized.

Contract revision: V1 · owner execution approval PENDING. Authoritative file: docs/sprint_prompts/SPRINT_08.md.

## Objective

Produce a concrete reviewable release candidate with exact evidence/provenance and honest readiness, stopping before unauthorized install/publication/merge.

## Prerequisites and starting state

Accepted S1–S7; all mandatory evidence/numeric/product/native/human gates closed; G-11 rights/package/signing/install scope resolved as applicable; approved clean-build environment and artifact destination. Current planning state: NOT STARTED. Previous milestone/commit UNKNOWN until executed. Before editing resolve previous actual report/implementation commit and exact working SHA; an expected PASS is not a prerequisite. GATE_REGISTER defines blocking evidence and owners.

## Read first

Read root AGENTS.md, README.md, docs/README.md, docs/PROJECT_HANDOFF.md and docs/SPRINT_PLAN.md. Exact additional files: . Relevant source sections/IDs and assets: All current living docs, source evidence index, eight contracts and seven actual reports, target/license/command/asset/parameter manifests; REQ-027; release rows §§42–43. Then reread this entire contract and exact check rows in docs/ACCEPTANCE_MATRIX.md. Required source V1 Markdown governs JSON; source filenames are indexed in docs/README.md. Sprint8 also reads all actual reports, manifests and current documents after execution.

## Allowed scope and non-goals

Release candidate build/package metadata/manual/checksum/evidence, necessary local packaging fixes within accepted behavior, docs/AUTONOMOUS_BUILD_FINAL_REPORT.md, docs/PROJECT_HANDOFF.md. No push/merge/publish/deploy/install by default. Actual source directories/language are established by Sprint1; no guessed path is an authorization. Before implementation map these subsystem permissions to real repository paths and document mapping in command/preflight record. Historical docs/research inputs immutable. Other sprint features forbidden; no external repository mutation or destructive cleanup. No hidden saturation/noise/jitter/mismatch/sag/tuned playback/SSM filter/reverse-order product/limiter/normalization. Current session remains planning only.

## Work in dependency order

1. Inspect accepted milestone commits, exact source/dependencies/assets and actual workspace. Use clean isolated authorized checkout for reproducible configure/build without resetting user work.

2. Run approved full regression and mandatory native matrix/owner release checks; inherit accepted hardware/listening evidence only when source/assets/configuration are unchanged and provenance valid, rerun affected checks for any packaging change affecting behavior.

3. Create packages only for validated targets, verify contents/version/schema/manual/calibration asset/licenses/source provenance; preserve restricted manual scans outside distribution. Signing/payment/install actions occur only if separately authorized and required; otherwise affected delivery remains blocked.

4. Generate exact source commit/tool/version/build config/dependency/asset/input/evidence/binary SHA manifests and reproducibility record. Claim binary bit identity only if measured; timestamp/tool variation otherwise explicit.

5. Audit final claims/abstraction/noise/latency/bypass/headroom and all28 requirement rows/gates. No completed hardware claim from software tests or release-ready verdict with mandatory unresolved gate.

6. Write complete final report and handoff: commits/checks/commands/environments/results/artifacts/hashes/limitations/blockers/next owner action. Stop at reviewable candidate; no remote publication/merge/installation implied.

## Required build and checks

Run the approved configure/build/inherited regression plus every listed check. Commands are currently UNKNOWN; Sprint1 must establish docs/BUILD_COMMANDS.md with exact tool versions, shell commands/flags, working directory, check IDs and evidence routes. Until commands and required numeric criteria are frozen this is a DRAFT/BLOCKED executable contract. Do not write a speculative build command and call it validated. Structural exact criteria below are planning requirements; hardware G-06 and production G-08 numeric bounds must exist before the dependent check.

| Check / requirement | Stimulus/configuration | Expected / tolerance rationale | Environment | Evidence |
|---|---|---|---|---|
| VAL-027 / REQ-027 | Clean authorized checkout configure/build/regression, package content/hash inspection, native install test if authorized | All mandatory gates closed; source/tool/license manifest and actual hashes; reproducible behavior within frozen budgets; no fabricated target pass or distribution | Approved native targets + artifact route | evidence/sprint_08/release_manifest.json; docs/AUTONOMOUS_BUILD_FINAL_REPORT.md |


Capture source/assets/input/config hashes, environment, exact command and exit code, stimulus levels/rates/channels and threshold revision. Same-build exact determinism, cross-rate/platform tolerance, reference agreement and hardware fidelity are separate. Retain failures and compare against held-out data only. Tests cannot be loosened or goldens regenerated merely to fit current implementation. Invalid tests need independent defect rationale, exact diff, preservation of old evidence and rerun. Acceptance-policy changes require named owner decision first.

## Measurements and experiment gates

Final clean-build/regression/package proof; reuse validated hardware captures with exact source/asset lineage, do not falsely claim rerun. Record planned versus actual execution, limitations/uncertainty and artifact class. SIMULATION never becomes HARDWARE MEASUREMENT. No notebook-only conclusion; scripts/config/raw outputs and hashes persist. Numeric criterion UNKNOWN prevents PASS for that metric. Large raw captures/build artifacts use the approved durable evidence destination; repository retains provenance/hashes/regeneration commands without arbitrary bulky binaries.

## Human work

Owner reviews candidate/delivery scope and rights/signing decision where required. Separate later instruction authorizes actual distribution/install/merge; not part of current planning. Required human/stock-unit/platform evidence cannot be substituted by agent judgment or previous-project history. Independent permitted tasks may continue within this sprint, but dependent tasks stop at their gate.

## Artifacts and documentation updates

Actual candidate packages, release manifest/checksums/manual/licenses/source mapping, native regression evidence, final report and durable handoff. No production artifacts generated during this planning task. Update affected ENGINE_SPEC, ARCHITECTURE, PARAMETERS, CONFIDENCE, DECISIONS, RESEARCH_DEBT/GATE_REGISTER, VALIDATION_PLAN/ACCEPTANCE_MATRIX and DSP_CHANGELOG only where actual work/evidence changes them. Preserve original sources unchanged. Update PROJECT_HANDOFF with current source/phase/tests/blockers/next action; no unexecuted future report is created.

## Observable Definition of Done

Clean rebuild/regression/package/mandatory native and human gates pass; exact hashes/source provenance; every requirement covered; RELEASE READY YES only if G-11 valid. If blocked, precise NO verdict and blocker report instead of fabricated completion. Required tests have actual execution logs/exit codes/evidence, diff matches scope, valid inherited tests pass and no unsupported source status is promoted. Report must distinguish implementation acceptance from hardware/production/native release readiness. On BLOCKED, record partial artifacts truthfully; do not label milestone complete.

## Automatic continue gate

No Sprint9. Stop after candidate report and permitted local milestone. Await separately authorized concrete distribution/install/merge action. Continuation is enabled only by a future execution-authorized orchestrator invocation. A manual sprint run stops after its report/permitted checkpoint. No elapsed time, empty answer or generated contract itself counts as approval.

## Stop and escalation

Any mandatory open debt/gate, unproven target, missing source rights, package regression, nonreproducible unsupported claim, or required payment/signing/install permission not supplied. Also stop affected dependency on source/spec conflict, required unknown value/threshold, changed accepted design, unauthorized destructive action/payment/credentials, exceeded budget or unapproved distribution. Record blocker ID, evidence, impact, options and exact next needed action. Never silently declare a mandatory gate nonblocking.

## Review, commit and report

Inspect full diff, test/requirement coverage, scope leakage, authority labels and evidence hashes. Future report: docs/sprint_reports/SPRINT_08_REPORT.md (not created now). Include baseline/branch/working SHA, authorization, work, exact checks/results/metrics, artifacts, decisions, limitations, verdict and continuation gate. Local milestone message if explicitly authorized: `sprint 08: reproducible release candidate, provenance and final review`. Commit only an accepted milestone. A blocker progress checkpoint may be made only if authorized and clearly labeled incomplete, never an accepted milestone. Do not claim an ending hash inside its own report before it exists; print hash after commit or record next-state index. Push/merge/publish/deploy/install permission: NONE by this planning request. Preserve dirty user work, no stash/reset/history rewrite. No delegation/agent launch is implied by this contract.
