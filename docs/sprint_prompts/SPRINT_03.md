# Sprint 03 — Calibrated SP reference and stereo skeleton validation

Revision: planning V1 · 2026-10-06

Status: DRAFT PLANNING CONTRACT. Documentation creation authorized; implementation and release not authorized.

Contract revision: V1 · owner execution approval PENDING. Authoritative file: docs/sprint_prompts/SPRINT_03.md.

## Objective

Build offline SP R2–R9 plus physical calibration with measured AA/output/quantizer/hold behavior, preserving historical imaging and unity pitch.

## Prerequisites and starting state

Accepted S2 with G-04/G-05/G-06 closed for all dependent items; actual SP asset candidates and held-out data. No production optimization or factory output default selected yet. Current planning state: NOT STARTED. Previous milestone/commit UNKNOWN until executed. Before editing resolve previous actual report/implementation commit and exact working SHA; an expected PASS is not a prerequisite. GATE_REGISTER defines blocking evidence and owners.

## Read first

Read root AGENTS.md, README.md, docs/README.md, docs/PROJECT_HANDOFF.md and docs/SPRINT_PLAN.md. Exact additional files: `docs/CONFIDENCE.md`, `docs/ENGINE_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/RATE_GAIN_PLAN.md`, `docs/PARAMETERS.md`, `docs/VALIDATION_PLAN.md`. Relevant source sections/IDs and assets: ENGINE_SPEC, ARCHITECTURE, RATE_GAIN_PLAN, CONFIDENCE, VALIDATION_PLAN, PARAMETERS; SP12-CLM-001..026; CHAIN-DEC-002..005/015/016; R0/R2–R9; research §§6–13,24–29,31–33. Then reread this entire contract and exact check rows in docs/ACCEPTANCE_MATRIX.md. Required source V1 Markdown governs JSON; source filenames are indexed in docs/README.md. Sprint8 also reads all actual reports, manifests and current documents after execution.

## Allowed scope and non-goals

Offline reference core/SP modules/tests, machine asset candidates with provenance, research/fit/sp1200, research/validation/sp1200/stereo, evidence/sprint_03. No production wrapper/UI/presets. Actual source directories/language are established by Sprint1; no guessed path is an authorization. Before implementation map these subsystem permissions to real repository paths and document mapping in command/preflight record. Historical docs/research inputs immutable. Other sprint features forbidden; no external repository mutation or destructive cleanup. No hidden saturation/noise/jitter/mismatch/sag/tuned playback/SSM filter/reverse-order product/limiter/normalization. Current session remains planning only.

## Work in dependency order

1. Implement measured/provisional clock version and persistent phase schedule, imported raw-code handling and selected measured quantizer encoding/offset/rounding/clamp. Code thresholds remain physically calibrated; static ADC/DAC error cancellation is not presumed.

2. Populate R2/R3 with evidence-constrained gains, AA complex response and measured clip boundaries. Fit only FIT data; verify AA phase/group delay and13–15k fold-back with held-out stimuli.

3. Implement unity R6 and measured R7 hold/reconstruction, retaining images. Populate separate R8/R9 ch7 unfiltered/ch5/ch3 responses and coupling/gain. No guessed transfer or perfect bandlimited SP reconstruction. MIX OUT only as approved/known separate mono diagnostic.

4. Ensure linked dual-mono uses shared instants/coefficients with independent per-channel history. Research skew setting uses measured interpretation and stays outside product. Run equal/anti-phase/channel-isolation, reset and chunk partition diagnostics.

5. Run CHAIN-EXP-017 qualitative published SP-12 skeleton sanity without treating it as owned SP-1200 validation. Use threshold policy for each held-out quantitative check; preserve failures and provenance.

6. Write reference asset version/hash/units/source IDs and measured limitations; update confidence and changelog with real implemented behavior only. Keep output default undecided for G-07.

## Required build and checks

Run the approved configure/build/inherited regression plus every listed check. Commands are currently UNKNOWN; Sprint1 must establish docs/BUILD_COMMANDS.md with exact tool versions, shell commands/flags, working directory, check IDs and evidence routes. Until commands and required numeric criteria are frozen this is a DRAFT/BLOCKED executable contract. Do not write a speculative build command and call it validated. Structural exact criteria below are planning requirements; hardware G-06 and production G-08 numeric bounds must exist before the dependent check.

| Check / requirement | Stimulus/configuration | Expected / tolerance rationale | Environment | Evidence |
|---|---|---|---|---|
| VAL-008 / REQ-008 | Analytic tones; ramps across 4096 codes; exported recorded data; low-level sines | Nominal 26.04 kHz; provisional exact 20e6/768 replaced only by evidence; code/threshold behavior per measured rule, exact digital agreement where identifiable | Offline reference + SP data | research/validation/sp1200/digital/ |
| VAL-009 / REQ-009 | Sweep incl 13–15 kHz, impulse, seeded multitone; held-out data | Complex response and fold-back within G-06 limits; schematic constrained; no arbitrary low-pass and no cleaning away historical aliases | Offline reference + SP input exports | research/validation/sp1200/input/ |
| VAL-010 / REQ-010 | Synthetic sample impulses/tones on measured ch3/ch5/ch7 and actual contacts | Hold fraction and complex response within G-06 limits; image positions follow measured rate; no blending circuits; ch1–2 excluded; MIX OUT not presumed | Offline + measured SP output paths | research/validation/sp1200/output/ |
| VAL-011 / REQ-011 | Stepped 100 Hz/1 kHz/10 kHz, alternate-frequency validation, full-scale codes | Volts/code mapping and each gain state traceable; converter clamp separate from measured analog clip; no guessed rail thresholds | Reference + measured volts | research/validation/sp1200/calibration/ |
| VAL-017 / REQ-017 | L=R, anti-phase, L-only/R-only, measured slot-delay research config | Identical-input channels identical in linked mode with identical states; no random skew; independent signal/filter state; slot skew research-only; label abstraction | Offline; later plugin | research/validation/stereo/ |
| VAL-018 / REQ-018 | Config inspection and unity sample sequence tests | No tuned playback, reverse-order product, note-driven filters, memory/loop/voice workflow in MVP; future additions require scope decision | Reference; later product UI | evidence/sprint_03/scope_audit.json |


Capture source/assets/input/config hashes, environment, exact command and exit code, stimulus levels/rates/channels and threshold revision. Same-build exact determinism, cross-rate/platform tolerance, reference agreement and hardware fidelity are separate. Retain failures and compare against held-out data only. Tests cannot be loosened or goldens regenerated merely to fit current implementation. Invalid tests need independent defect rationale, exact diff, preservation of old evidence and rerun. Acceptance-policy changes require named owner decision first.

## Measurements and experiment gates

Use S2 results CHAIN-EXP-001..007 and019; CHAIN-EXP-017 simulation sanity now. New residuals reopen evidence before expanding model. Record planned versus actual execution, limitations/uncertainty and artifact class. SIMULATION never becomes HARDWARE MEASUREMENT. No notebook-only conclusion; scripts/config/raw outputs and hashes persist. Numeric criterion UNKNOWN prevents PASS for that metric. Large raw captures/build artifacts use the approved durable evidence destination; repository retains provenance/hashes/regeneration commands without arbitrary bulky binaries.

## Human work

Reviewer accepts calibrated SP asset fit and limitations. Owner is not asked to invent missing coefficients or approve arbitrary saturation. Product path decision is deferred to S5. Required human/stock-unit/platform evidence cannot be substituted by agent judgment or previous-project history. Independent permitted tasks may continue within this sprint, but dependent tasks stop at their gate.

## Artifacts and documentation updates

SP reference code/tests, calibrated asset candidate, held-out plots/metrics/audio/code comparisons, stimulus/config hashes and qualitative simulation with labels. Update affected ENGINE_SPEC, ARCHITECTURE, PARAMETERS, CONFIDENCE, DECISIONS, RESEARCH_DEBT/GATE_REGISTER, VALIDATION_PLAN/ACCEPTANCE_MATRIX and DSP_CHANGELOG only where actual work/evidence changes them. Preserve original sources unchanged. Update PROJECT_HANDOFF with current source/phase/tests/blockers/next action; no unexecuted future report is created.

## Observable Definition of Done

All SP checks satisfy frozen limits; linked-stereo/scope assertions pass; complex response and images match held-out evidence; calibrated assets carry exact source/experiment identity; no shipping/default/fidelity overclaim. Required tests have actual execution logs/exit codes/evidence, diff matches scope, valid inherited tests pass and no unsupported source status is promoted. Report must distinguish implementation acceptance from hardware/production/native release readiness. On BLOCKED, record partial artifacts truthfully; do not label milestone complete.

## Automatic continue gate

S4 requires accepted S3 plus valid MPC S2 data/criteria. A SP failure blocks accepted milestone; independent permitted analysis cannot bypass reference acceptance. Continuation is enabled only by a future execution-authorized orchestrator invocation. A manual sprint run stops after its report/permitted checkpoint. No elapsed time, empty answer or generated contract itself counts as approval.

## Stop and escalation

Unexplained nonlinearity/code/hold/filter residual, unknown SP clip/gain, a need to retune valid threshold or add excluded tuned/SSM/mismatch behavior. Also stop affected dependency on source/spec conflict, required unknown value/threshold, changed accepted design, unauthorized destructive action/payment/credentials, exceeded budget or unapproved distribution. Record blocker ID, evidence, impact, options and exact next needed action. Never silently declare a mandatory gate nonblocking.

## Review, commit and report

Inspect full diff, test/requirement coverage, scope leakage, authority labels and evidence hashes. Future report: docs/sprint_reports/SPRINT_03_REPORT.md (not created now). Include baseline/branch/working SHA, authorization, work, exact checks/results/metrics, artifacts, decisions, limitations, verdict and continuation gate. Local milestone message if explicitly authorized: `sprint 03: calibrated sp reference and stereo skeleton validation`. Commit only an accepted milestone. A blocker progress checkpoint may be made only if authorized and clearly labeled incomplete, never an accepted milestone. Do not claim an ending hash inside its own report before it exists; print hash after commit or record next-state index. Push/merge/publish/deploy/install permission: NONE by this planning request. Preserve dirty user work, no stash/reset/history rewrite. No delegation/agent launch is implied by this contract.
