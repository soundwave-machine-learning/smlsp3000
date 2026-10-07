# Project handoff and honest current state

Revision: execution V3 (after Sprint 3) · 2026-10-07 · supersedes execution V2

Status: EXECUTION IN PROGRESS. Sprint 1 ACCEPTED (PASS, fbd1fac). Sprint 2 hardware campaign BLOCKED / EXTERNAL HARDWARE REQUIRED (1c0fe89, preserved). Governance V2 (8257c2d) approved by the owner 2026-10-07 (OWN-DEC-001..004). Sprint 3 Track A ACCEPTED — PASS WITH EXTERNAL VALIDATION PENDING (G-04); milestone commit recorded below. Sprint 4 NOT started: owner inputs required (R12 state, R15 state, R13 default). Release NOT authorized.

## Current verified state

Project: SP-1200 → MPC3000 Full-Mix Processor (repository name smlsp3000). Phase: autonomous build, Sprint 1 complete. Authorization: owner execution instruction 2026-10-06 (recorded in evidence/sprint_01/preflight.json) — implement autonomously through later sprints only where contracts/stop conditions permit; never merge to main; branch `claude/autonomous-build`; push allowed; publish/install/payment/signing not allowed.

Repository: https://github.com/soundwave-machine-learning/smlsp3000 · remote origin · baseline commit 3b53a6b1cb6600800cbc3c5eb6929fff8b3b254c ("Import SML SP-3000 engineering baseline", == main). Working branch `claude/autonomous-build` created from the baseline. Sprint 1 milestone commit: `fbd1facffb84ffd132c17eca8c60a390f7df5d6e`.

Execution environment: Claude Code cloud container, Linux x86_64, Python 3.13.16, numpy 2.5.3, gcc 13.3/cmake 3.28 present but unused; no scipy/pytest (not needed, not installed); network egress allow-listed (PyPI reachable; archive.org and all datasheet hosts DENIED); no hardware, no audio interface, no plugin SDK, no DAW. Stack decision ENG-DEC-011; commands docs/BUILD_COMMANDS.md.

Inputs unchanged: docs/research/*.md/.json byte-identical to PACKAGE_VALIDATION hashes; eight contracts unchanged. Known baseline quirk: docs/ACCEPTANCE_MATRIX.csv was hashed as CRLF in SHA256SUMS/MANIFEST but committed as LF (content identical).

## What exists after Sprint 3 (Track A)

- `smlsp3000/reference/`: provisional SP reference R1–R9/R16 (kernels, partition-invariant streaming FIRs, exact rational scheduler, asset/config loader, SP blocks with replaceable registries, linked dual-mono engine, offline renderer with provenance). Asset `sp1200-track-a-provisional` v1 (model sp1200-provisional-1.0.0), research config v1, implementation 1.0.2. R3 INACTIVE; quantizer ROUND_NEAREST default / FLOOR alternate; route NONE_CH7_8 only; normalized calibration (volts UNSET); every value UNVALIDATED AGAINST HARDWARE.
- Software validation records (all PASS, hardware-fit BLOCKED): research/validation/sp1200/{digital,input,output,calibration}/, research/validation/stereo/; scope audit evidence/sprint_03/scope_audit.json; CHAIN-EXP-017 SIMULATION (INFORMATIONAL) research/sim/CHAIN-EXP-017/. 35 tests pass.
- Not implemented: R0 volts, R3 response, ch 3–6 / MIX OUT routes, R10–R15 (MPC), production engine, wrapper, UI, presets.

## What exists after Sprint 1

- `smlsp3000/` analysis/evidence foundation: hashing + manifests, frozen schema vocabularies and records (experiment result, unit metadata, capture sidecar, machine asset, research configuration, UNSET semantics), WAV I/O, analytic synthetic truth, pilot/alignment/null evaluator, experiment runner by repository ID.
- `research/sim/CHAIN-EXP-016/` — executed self-test, SIMULATION, outcome PASS: identical arrays exactly zero; floor ≤ −92.6 dB RMS re signal across perturbation cases (−149 dB unperturbed); ratio error ≤ 0.0005 ppm; delay error ≤ 2e-5 samples; gain error ≤ 3e-8 dB; polarity always correct.
- `tests/` 18 unit/regression tests (all pass), including VAL-001 integrity and exact same-build reproduction of the EXP-016 record.
- `reference/sources/{sp1200,mpc3000}/ACCESS_RECORD.json` — CHAIN-EXP-019/020 and datasheet retrieval ATTEMPTED and BLOCKED (network policy); nothing transcribed, nothing guessed.
- `evidence/sprint_01/` preflight, provenance, smoke run, dry review, logs. `docs/BUILD_COMMANDS.md`, `docs/sprint_reports/README.md`, `docs/sprint_reports/SPRINT_01_REPORT.md`.
- No DSP. No R-block. No machine asset. No preset. No binary.

## Owner decision OWN-DEC-001 (2026-10-06)

Proceed with provisional software/reference implementation without hardware fit, because the owner does not possess SP-1200/MPC3000 hardware. Hardware matching is not claimed; hardware-derived coefficients remain unresolved; provisional implementations stay replaceable; hardware confidence states unchanged; future hardware fitting may replace provisional components; release wording distinguishes modeled/inspired from measured (claim boundary: "a software instrument/effect inspired by and informed by documented SP-1200 / MPC3000 architecture and behaviour"; never exact emulation / hardware matched / component accurate / measured / hardware validated). G-04 reclassified DEFERRED EXTERNAL VALIDATION GATE (still BLOCKED). Full text, Sprint 3–8 dependency table, provisional policy and revised continuation rules: docs/EXECUTION_PLAN_V2.md.

## Gates and blockers

G-01 RESOLVED (A: owner instruction; B: command manifest for the analysis stack; native target matrix stays G-09). G-02 PASS (simulation floor known). G-03 OPEN/BLOCKED (source access; not a Track A prerequisite). G-04 BLOCKED — HARDWARE NOT AVAILABLE, DEFERRED EXTERNAL VALIDATION GATE: blocks Track B and all hardware claims, does not block Track A. G-07 split into G-07S (software product decision) / G-07H (deferred). G-05/G-06/G-07/G-08/G-09/G-10/G-11 OPEN. All 6 P0 + 12 P1 debt items OPEN. 17 of 20 experiments NOT EXECUTED; EXP-016 executed; EXP-019/020 blocked.

Shipping A/B/C NOT CHOSEN; SP canonical output UNDECIDED; MPC main L/R recommended only; calibration/interstage UNSET; proxy rate UNSET; unity pitch only.

## Last accepted milestone and next action

Last accepted milestone: Sprint 1 — commit `fbd1facffb84ffd132c17eca8c60a390f7df5d6e`. Follow-up checkpoint commit (Sprint 2 BLOCKED preflight report, hash back-fill): the commit after it on the branch. Last activity: Sprint 3 Track A execution (provisional SP reference, software validation, CHAIN-EXP-017, docs, report).

Next authorized action: NONE autonomously. Sprint 4 (Track A MPC reference, REQ-012/013/014 software cells) starts only after the owner supplies EXECUTION_PLAN_V2 §9 item 5: R12 ADC state (TRANSPARENT or ESTIMATE FIR with approved spec), R15 DAC state (TRANSPARENT or ESTIMATE FIR), R13 default 18→16 reduction rule (TRUNCATION or ROUND_NEAREST) — see docs/sprint_reports/SPRINT_03_REPORT.md §16 and the executor's Sprint 4 owner-input request. For Track B the owner must (a) arrange the stock SP-1200 / MPC3000 campaign per docs/MEASUREMENT_PLAN.md with a calibrated 192 k/24 interface, S/PDIF 44.1 k source, operator and a durable raw-capture route (G-04); (b) optionally grant source access (archive.org, analog.com or an approved copy route) for a CHAIN-EXP-019/020 re-attempt; (c) later: G-06 threshold acceptance, G-07 product selection, G-08 budgets, G-09 target matrix/SDK/licence.

On resume: inspect `git status`, `git log claude/autonomous-build`, this file and docs/sprint_reports/; run `python3 tools/check_repo_integrity.py` and `python3 -m unittest discover -s tests -t . -v`; do not rerun accepted Sprint 1 work without a new reason; do not transfer state from other projects.
