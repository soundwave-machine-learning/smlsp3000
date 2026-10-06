# Sprint 01 report — Foundation, capability freeze and targeted source closure

Contract: docs/sprint_prompts/SPRINT_01.md (planning V1, unchanged). Authorization: owner execution instruction 2026-10-06 (evidence/sprint_01/preflight.json). Executor: autonomous (Claude Code cloud session). Date: 2026-10-06.

## 1–2. Starting state

- Repository https://github.com/soundwave-machine-learning/smlsp3000, remote origin.
- Starting commit 3b53a6b1cb6600800cbc3c5eb6929fff8b3b254c (== main), working tree clean, branch at session start `claude/sleepy-hawking-wqdssx` (harness default); owner instruction names `claude/autonomous-build`, created from 3b53a6b and used for all work (ENG-DEC-013).
- Baseline verification: 8/8 contracts; AUTONOMOUS_BUILD_PROMPT paths resolve; acceptance matrix 28 rows; no prior implementation present; both research sources byte-identical to PACKAGE_VALIDATION hashes. One mechanical inconsistency: docs/ACCEPTANCE_MATRIX.csv hash in SHA256SUMS/MANIFEST was computed on CRLF bytes while git holds LF (content identical; CRLF-restored bytes reproduce the manifest hash). Not substantive; recorded, not repaired.
- The owner instruction references docs/sprint_reports/README.md, which did not exist in the planning package; created as a mechanical gap fix (template + verdict vocabulary), not a contract rewrite.

## 3. Scope mapping

| Contract permission | Repository path |
|---|---|
| docs/BUILD_COMMANDS.md | docs/BUILD_COMMANDS.md |
| evidence/sprint_01 | evidence/sprint_01/ |
| reference/sources | reference/sources/README.md, sp1200/ACCESS_RECORD.json, mpc3000/ACCESS_RECORD.json |
| research/sim/CHAIN-EXP-016 | research/sim/CHAIN-EXP-016/ |
| build/test/evidence-schema foundation | pyproject.toml, smlsp3000/, tests/, tools/check_repo_integrity.py, .gitignore |

## 4. Implementation completed

- Stack frozen (ENG-DEC-011): Python 3.13 + numpy + standard library; no installs; native stack undecided (G-09).
- `smlsp3000.hashing`: SHA-256 of files/bytes/arrays (dtype+shape bound), sha256sum-compatible manifests, verification.
- `smlsp3000.schemas`: frozen vocabularies (artifact classes, dataset roles FIT/VALIDATION/SELF_NULL/NONE, evidence statuses, outcomes, debt states), records for experiment results, unit metadata, capture sidecars, machine assets, research configuration; strict validation (unknown fields rejected); explicit `UNSET` (blocked configuration, never 0 dB).
- `smlsp3000.wavio`: PCM 16/24/32 and float32 WAV read/write with explicit clamping on write (no wrap).
- `smlsp3000.stimuli`: analytic continuous-time stimulus (segments/tones, raised-cosine edges); `render_perturbed` evaluates the closed-form signal at perturbed instants — independent truth for the self-test. Self-test layout ≤ 2.3 s: silence, two-tone pilot burst (2000 + 2300 Hz), 1 kHz calibration tone, 31-tone log-spaced seeded multitone 50 Hz–18 kHz, end pilot.
- `smlsp3000.nullframework` (v1.2.1): DC report + identical 5 Hz first-order high-pass; polarity from pilot cross-correlation; clock ratio from pilot frequency scale (phase-slope first guess refined by joint multi-tone least-squares fit; start/end drift in ppm); delay = integer lag (envelope-guided signal cross-correlation) + sub-sample pilot phase; single-pass Kaiser-windowed sinc resampling (96 taps, β = 12, exact at integer positions); scalar gain from the calibration tone; residual metrics (peak, RMS re signal, correlation, per-octave-band, spectrum CSV) with explicit undefined handling on silence. No EQ, dynamic gain or warp exists.
- `smlsp3000.experiments.exp016` + `smlsp3000.runner`: experiment by repository ID, result record conforming to the EXPERIMENT_RESULT_RECORD schema, config/raw-output hashes, manifest.
- `tools/check_repo_integrity.py`: VAL-001 checks (sources, contracts, links, matrix, SHA256SUMS with immutable set strict).
- Deliberately not implemented: any R-block, machine asset, filter coefficient, quantizer, hold, clamp, production code, preset, UI, plugin.

## 5. Commands executed (repository root)

| ID | Command | Exit | Log |
|---|---|---|---|
| CMD-01 | `python3 -c "import numpy, sys; ..."` | 0 | evidence/sprint_01/preflight.json |
| CMD-02 | `python3 tools/check_repo_integrity.py` | 0 | evidence/sprint_01/integrity_run.log |
| CMD-03 | `python3 -m smlsp3000.runner run CHAIN-EXP-016 --out research/sim/CHAIN-EXP-016` | 0 | evidence/sprint_01/exp016_run.log (≈101 s) |
| CMD-04 | `python3 -m smlsp3000.runner verify-manifest research/sim/CHAIN-EXP-016` | 0 | evidence/sprint_01/verify_manifest_run.log |
| CMD-05 | `python3 -m unittest discover -s tests -t . -v` | 0 | evidence/sprint_01/unittest_run.log (18 tests OK, ≈108 s) |
| CMD-06 | `sha256sum -c SHA256SUMS.txt` | 1 (informational) | CSV line endings + revised living docs; immutable set verified by CMD-02 |

Tool versions: Python 3.13.16, numpy 2.5.3, git 2.43.0. Full table: docs/BUILD_COMMANDS.md.

## 6. Checks

| Check | Result | Evidence |
|---|---|---|
| VAL-001 / REQ-001 | PASS | integrity 5/5; evidence/sprint_01/provenance.json |
| VAL-002 / REQ-002 | PASS for the reference/analysis stack; native target matrix explicitly UNKNOWN (G-09), not invented | docs/BUILD_COMMANDS.md; preflight.json; smoke_run.json |
| VAL-003 / REQ-003 | PASS (SIMULATION) | research/sim/CHAIN-EXP-016/result.json |
| VAL-004 / REQ-004 | BLOCKED | reference/sources/*/ACCESS_RECORD.json |
| VAL-028 / REQ-028 | PASS (executor side; owner review of the dry review pending) | evidence/sprint_01/val028_dry_review.json |

Test-integrity note: one test failed during development (interpolator identity at integer positions was not bit-exact because `np.sinc(n)` returns ~1e-16 for nonzero integers). The implementation, not the test, was corrected (exact integer handling), the algorithm version bumped to 1.2.1, and CHAIN-EXP-016 was re-executed; floor values were unchanged to the printed precision. No tolerance was loosened; no golden was regenerated to fit an implementation — the committed EXP-016 record is the output of the corrected build.

## 7. Measurements (SIMULATION — CHAIN-EXP-016)

| Quantity | Value |
|---|---|
| Identical-array residual (no preprocessing) | exactly 0 (all samples) |
| Residual RMS re signal, unperturbed through pipeline | −149.1 dB |
| Residual RMS re signal, worst perturbation case (combined) | −92.6 dB |
| Clock-ratio recovery error, max over cases | 0.0005 ppm |
| Delay recovery error, max | 1.9e-5 samples @ 192 kHz |
| Gain recovery error, max | 3.1e-8 dB |
| Polarity | correct in 11/11 cases |
| Start/end pilot delay consistency | within the recorded case values |

Cases: none; ratio +37 / −120 ppm; delay 0.37 / 3.30 / 17.25 samples; polarity inverted; gain ±1 dB; DC +0.01; combined (+61 ppm, 7.63 samples, inverted, −2.5 dB, −0.004 DC). Decision rule (source): framework accepted when its own floor is known → floor known → G-02 PASS. These numbers describe the evaluator on synthetic truth; they say nothing about either machine.

## 8. Artifacts

Listed with SHA-256, size and class in evidence/sprint_01/provenance.json (36 files). Classes: research/sim/CHAIN-EXP-016/* SIMULATION (SELF_NULL); reference/sources/*/ACCESS_RECORD.json SOURCE EVIDENCE (access failures only); code/tests IMPLEMENTATION. Total new artifact size ≈ 0.9 MB (residual spectra CSVs); no audio committed.

## 9. Assumptions

- The owner execution instruction in this session constitutes G-01A (repository, baseline, branch, operations). Budgets were not stated; none were assumed exceeded.
- Pilot design (2000 + 2300 Hz burst, 1 kHz calibration tone, 5 Hz DC high-pass) is an evaluator configuration for the self-test, recorded in config.json (ENG-DEC-012); hardware pilot design is frozen in Sprint 2 and the self-test is re-run if it changes.

## 10. Deviations

- Branch name differs from the harness default and from the orchestrator's proposed name; the owner instruction governs (ENG-DEC-013).
- docs/sprint_reports/README.md created (referenced by the owner instruction, absent from the package).
- Living docs received an "execution V1" revision line; MANIFEST.json/MANIFEST.md/SHA256SUMS.txt were left as the historical planning-V1 record (regenerating them would erase the baseline inventory); immutable items remain enforced by tools/check_repo_integrity.py.
- No dependency installation (AGENTS.md no-install posture kept); scipy/pytest reachable on PyPI if a later sprint justifies them.

## 11. Unresolved issues and blockers

| Blocker | Gate | Evidence | Impact | Options | Next action |
|---|---|---|---|---|---|
| Source hosts denied by execution-environment network policy (archive.org, analog.com, renesas.com, farnell.com, alldatasheet.com); AK5328 not located | G-03 | reference/sources/*/ACCESS_RECORD.json | CHAIN-EXP-019/020, RD-P1-01/02/03 documentary closure impossible here; all P0/P1 stay OPEN | (a) owner widens network access or supplies sheets via approved route; (b) rely on S2 hardware measurement | owner decision; no coefficient guessed meanwhile |
| No hardware / interface / operator | G-04 | preflight.json | Sprint 2 cannot start | arrange campaign per docs/MEASUREMENT_PLAN.md | owner |
| Native target matrix / SDK / licence unknown | G-09 | preflight.json | VAL-002 complete only for the analysis stack | owner decision before S7 | owner |

## 12. Documentation updates

AGENTS.md, README.md, docs/README.md, GATE_REGISTER, RESEARCH_DEBT, DECISIONS (ENG-DEC-011/012/013; ENG-DEC-006/010 status), DSP_CHANGELOG (no-DSP entry), VALIDATION_PLAN, EXPERIMENT_PLAN, CONFIDENCE (lane statement), ARCHITECTURE (foundation layout), ENGINE_SPEC, PARAMETERS (status lines), ACCEPTANCE_MATRIX.md/.csv (rows 001/002/003/004/028), PROJECT_HANDOFF, new BUILD_COMMANDS, sprint_reports/README. Immutable research and the eight contracts untouched.

## 13. Confidence / status changes

No claim status changed (no new evidence). Gate states: G-01 RESOLVED, G-02 PASS (simulation), G-03 OPEN (attempted, blocked). Experiments: EXP-016 EXECUTED/PASS; EXP-019/020 ATTEMPTED/BLOCKED.

## 14. Human and hardware gates

Owner: review of the VAL-028 dry review; G-03 source-access decision; G-04 campaign; later G-06..G-11. Hardware: none measured; nothing simulated is promoted.

## 15. Final verdict

**PASS** — Sprint 1 definition of done met on its own terms: actual commands and smoke results recorded; source integrity/count checks pass; null framework verified against independent truth with its floor known; ambiguous source values remain UNKNOWN; G-01 and G-02 resolved; G-03 disposition precise (attempted, blocked, nothing guessed). Implementation acceptance only — no hardware, production or native readiness is implied.

## 16. Continuation gate

Sprint 2 requires G-04 (stock units, calibrated interface, operator, routes) which is absent in this environment → Sprint 2 BLOCKED at preflight (docs/sprint_reports/SPRINT_02_REPORT.md). No later sprint may start.

## 17. Ending commit

Recorded in docs/PROJECT_HANDOFF.md / `git log claude/autonomous-build` after the milestone commit; not written here before it exists.
