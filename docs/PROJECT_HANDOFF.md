# Project handoff and honest current state

Revision: execution V6 (after Sprint 6) · 2026-10-07 · supersedes execution V5

Status: EXECUTION IN PROGRESS. Sprint 1 ACCEPTED (PASS, fbd1fac). Sprint 2 hardware campaign BLOCKED / EXTERNAL HARDWARE REQUIRED (1c0fe89, preserved). Governance V2 (8257c2d) approved by the owner 2026-10-07 (OWN-DEC-001..004). Sprint 3 Track A ACCEPTED — PASS WITH EXTERNAL VALIDATION PENDING (G-04); milestone `51b72d5`. Sprint 4 Track A ACCEPTED — PASS WITH EXTERNAL VALIDATION PENDING (G-04); milestone commit `e8f66008e635b00969b7944277ba72ed6f7c43c9` (OWN-DEC-005..008 applied). Sprint 5 Track A ACCEPTED — PASS WITH EXTERNAL VALIDATION PENDING (human listening, G-07H, G-04); milestone commit `69d64a02ba206a085bfd7b018decdba9e70183f1` (OWN-DEC-009..013 applied). Sprint 6 Track A ACCEPTED — PASS WITH EXTERNAL VALIDATION PENDING (Windows native validation NOT RUN; human listening; G-07H; G-04); implementation milestone commit recorded below (OWN-DEC-014..023 applied). Sprint 7 NOT started: G-09 owner inputs required. Release NOT authorized.

## Current verified state

Project: SP-1200 → MPC3000 Full-Mix Processor (repository name smlsp3000). Phase: autonomous build, Sprint 1 complete. Authorization: owner execution instruction 2026-10-06 (recorded in evidence/sprint_01/preflight.json) — implement autonomously through later sprints only where contracts/stop conditions permit; never merge to main; branch `claude/autonomous-build`; push allowed; publish/install/payment/signing not allowed.

Repository: https://github.com/soundwave-machine-learning/smlsp3000 · remote origin · baseline commit 3b53a6b1cb6600800cbc3c5eb6929fff8b3b254c ("Import SML SP-3000 engineering baseline", == main). Working branch `claude/autonomous-build` created from the baseline. Sprint 1 milestone commit: `fbd1facffb84ffd132c17eca8c60a390f7df5d6e`.

Execution environment: Claude Code cloud container, Linux x86_64, Python 3.13.16, numpy 2.5.3, gcc 13.3/cmake 3.28 present but unused; no scipy/pytest (not needed, not installed); network egress allow-listed (PyPI reachable; archive.org and all datasheet hosts DENIED); no hardware, no audio interface, no plugin SDK, no DAW. Stack decision ENG-DEC-011; commands docs/BUILD_COMMANDS.md.

Inputs unchanged: docs/research/*.md/.json byte-identical to PACKAGE_VALIDATION hashes; eight contracts unchanged. Known baseline quirk: docs/ACCEPTANCE_MATRIX.csv was hashed as CRLF in SHA256SUMS/MANIFEST but committed as LF (content identical).

## What exists after Sprint 6 (Track A)

- `native/`: C++20 production core (smlsp3000-native-core-1.0.0; CMake; no dependencies; no I/O; no allocation/locks in process()) — numerics (numpy-ordered pairwise dot, i0/sinc/Kaiser ports), kernels, partition-invariant streaming FIRs, exact rational scheduler, SP core R2–R9, MPC core R11–R15 with composed operator tables (sampler∘R12, R16∘R15; exact-order diagnostic path retained), cascade engine with chain modes, R10, 10 ms linear-in-dB ramps with sample-indexed events, discrete switches, output trim, static latency-aligned plugin bypass, meters, NaN/Inf policy, fail-safe, state v1; generated hashed asset header (tools/gen_native_assets.py); offline tool `smlsp3000_native` (render/info/dump-kernels/bench/state-load); `smlsp3000_selftest` (ctest, 31 cases). Linux x86_64 only compiled and tested; Windows NOT RUN.
- Frozen product controls v1 (`smlsp3000/reference/assets/product_controls_v1.json`, OWN-DEC-020) and the G-08 SOFTWARE policy (evidence/sprint_06/owner_decisions_g08.json, fixture_freeze.json, parameter_resolution.json).
- Validation (research/validation/{reference_production,rate_block,implementation_alias}/, evidence/sprint_06/state_parameter/): VAL-019/020/021/022 PASS — 216 agreement cells within 1e-9 of the owner limits, code streams identical, bit-identical determinism/partitions at six rates, latency verified (298/310/426/449/682/728 host samples at 44.1/48/88.2/96/176.4/192 kHz, all < 7 ms), cross-rate bounded, 8x/16x convergence within the kernel bound, state/automation fixtures. Benchmark evidence/sprint_06/benchmark/ (Release core within OWN-DEC-017 budgets on the recorded Linux machine). Instrumentation-only reference change (cascade machine peak meter marked UNAVAILABLE_IN_CASCADE, core-input peaks added) with audio unchanged (evidence/sprint_06/instrumentation_regression_run.log).
- Not implemented: plugin wrapper/host integration, bypass transitions, GUI, presets, installation, Windows build, R0 volts, any hardware response.

## What exists after Sprint 5 (Track A)

- `smlsp3000/reference/cascade.py`: provisional cascade R1 → SP core → R10 → MPC core → R16 on the proxy grid; interstage_level_db owner default 0.0 dB (NON-HISTORICAL, research range −60…+24 dB); chain modes CASCADE (product default) / SP_ONLY / MPC_ONLY / BOTH_MACHINE_BYPASSED, all latency-aligned (310 host samples at 48 kHz); reverse order research switch; product configuration `sml-sp3000-product-config-track-a` v1 (path B, NONE_CH7_8 / MAIN_LR, linked dual mono PRODUCT ABSTRACTION, no drive/wet-dry); cascade research config v1; implementation cascade-reference-impl-1.0.0 (SP 1.0.4 / MPC 1.0.2 core split, outputs bit-identical). Software validation VAL-015/016 PASS (hardware-fit BLOCKED); 52 tests pass; Sprint 3/4 regression numerically identical.
- G-07S OWNER-APPROVED SOFTWARE PRODUCT DECISION recorded in evidence/sprint_05/product_decision.json; G-07H BLOCKED.
- `smlsp3000/listening/kit.py` + research/listening/CHAIN-EXP-018: software-only listening kit PREPARED (16 blinded RMS-matched synthetic stimuli; audio git-ignored and regenerable from CMD-12; hashes committed). Human listening NOT EXECUTED; no criterion, scores or counts exist.
- Not implemented: R0 volts, output trim, plugin bypass, production engine, wrapper, UI, presets, any hardware response.

## What exists after Sprint 4 (Track A)

- `smlsp3000/reference/mpc3000.py`: provisional MPC reference R11–R15 with R1/R16 (TRANSPARENT R12/R15, ROUND_NEAREST default / TRUNCATION alternate R13, R14 identity, ideal dB trim with 20 dB steps, MAIN_LR only, true stereo, volts UNSET); asset `mpc3000-track-a-provisional` v1, research config v1, implementation 1.0.1. Software validation VAL-012/013/014 PASS (hardware-fit BLOCKED); 45 tests pass; Sprint 3 regression numerically identical.
- Not implemented: R10 interstage, output trim, cascade (SP→MPC composition), any machine response, overload recovery, individual/headphone routes, production engine, wrapper, UI, presets.

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

G-01 RESOLVED (A: owner instruction; B: command manifest for the analysis stack; native target matrix stays G-09). G-02 PASS (simulation floor known). G-03 OPEN/BLOCKED (source access; not a Track A prerequisite). G-04 BLOCKED — HARDWARE NOT AVAILABLE, DEFERRED EXTERNAL VALIDATION GATE: blocks Track B and all hardware claims, does not block Track A. G-07 split into G-07S (DECIDED 2026-10-07, software) / G-07H (BLOCKED, deferred). G-08 SOFTWARE criteria set and executed (OWN-DEC-015..021; VAL-019..022 PASS; hardware-related budgets stay with G-06). G-05/G-06/G-09/G-10/G-11 OPEN. All 6 P0 + 12 P1 debt items OPEN. 17 of 20 experiments NOT EXECUTED; EXP-016 executed; EXP-019/020 blocked.

Shipping path B CHOSEN in software (G-07S, OWN-DEC-010; G-07H BLOCKED); SP route NONE_CH7_8 and MPC route MAIN_LR populated; interstage 0.0 dB provisional (volts UNSET); proxy rate ×8 ESTIMATE (G-08 pending); unity pitch only.

## Last accepted milestone and next action

Last accepted milestone: Sprint 6 — implementation milestone commit hash recorded by the follow-up checkpoint commit (see docs/sprint_reports/SPRINT_06_REPORT.md §17). Earlier milestones: Sprint 1 `fbd1fac`, Sprint 3 `51b72d5`, Sprint 4 `e8f6600`, Sprint 5 `69d64a0`. Last activity: Sprint 6 Track A execution (native production core, G-08 software acceptance, parameter freeze, benchmark, docs, report).

Next authorized action: NONE autonomously. Sprint 7 (plugin wrapper, host integration, bypass transitions, meters/UI behaviour, REQ-023..025) starts only after the owner supplies G-09: plugin formats, OS/DAW matrix, framework/SDK and licence (no paid/proprietary dependency is accepted autonomously), a Windows x86_64 toolchain or machine for the deployment target, the bypass transition policy, and the host automation mapping conventions — see docs/sprint_reports/SPRINT_06_REPORT.md §16. Human listening under CHAIN-EXP-018 needs an owner-defined criterion before any score is recorded. For Track B the owner must (a) arrange the stock SP-1200 / MPC3000 campaign per docs/MEASUREMENT_PLAN.md with a calibrated 192 k/24 interface, S/PDIF 44.1 k source, operator and a durable raw-capture route (G-04); (b) optionally grant source access (archive.org, analog.com or an approved copy route) for a CHAIN-EXP-019/020 re-attempt; (c) later: G-06 threshold acceptance, G-07 product selection, G-08 budgets, G-09 target matrix/SDK/licence.

On resume: inspect `git status`, `git log claude/autonomous-build`, this file and docs/sprint_reports/; run `python3 tools/check_repo_integrity.py`, build the native core (docs/BUILD_COMMANDS.md CMD-13/14) and run `python3 -m unittest discover -s tests -t . -v` (native tests skip with an explicit reason when the core is not built); do not rerun accepted work without a new reason; do not transfer state from other projects.
