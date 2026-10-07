# Build, test and analysis command manifest

Revision: execution V6 (Sprint 6) · 2026-10-07 · supersedes execution V5

Status: FROZEN for the reference/analysis stack (ENG-DEC-011) and, from Sprint 6, for the native production core (OWN-DEC-014: C++20, CMake, GCC/Clang; no plugin SDK). Every command below was executed in the sprint that introduced it with the recorded exit code. Native plugin build/host commands do not exist yet: G-09 target matrix UNKNOWN; Windows commands are NOT listed because no Windows build was run.

## Environment of record

| Item | Value |
|---|---|
| Working directory | repository root (`/home/user/smlsp3000` in the Sprint 1 container; any clone root is equivalent) |
| Shell | POSIX sh / bash |
| Python | 3.13.16 (CPython), system interpreter `python3`; no virtual environment, no `pip install` |
| numpy | 2.5.3 |
| git | 2.43.0 |
| OS | Linux 6.18.44 x86_64, Ubuntu 24.04 userland, 4 vCPU, 15 GB RAM |
| Native toolchain (used from Sprint 6) | gcc 13.3.0 (g++ -std=c++20), clang 18.1.3 (present, unused), cmake 3.28.3, ninja 1.11, ctest; no Windows cross-compiler |
| Not installed | scipy, pytest, soundfile, ngspice, plugin SDKs, DAWs |

Reproduction on another machine requires Python ≥ 3.12 and numpy ≥ 2.0; floating-point results of CHAIN-EXP-016 are same-build goldens (validation domain 2) and may differ in low-order digits across platforms/BLAS builds — that is a recorded limitation, not a pass criterion.

## Commands

| Check ID | Command (from repository root) | Purpose | Exit code policy | Evidence route | Sprint 1 result |
|---|---|---|---|---|---|
| CMD-01 | `python3 -c "import numpy, sys; print(sys.version, numpy.__version__)"` | version stamp | 0 | evidence/sprint_NN/preflight.json | 0 |
| CMD-02 / VAL-001 | `python3 tools/check_repo_integrity.py` | research-source SHA-256, 8 contracts, local links, 28 matrix rows, SHA256SUMS (immutable set strict) | 0 = all PASS | stdout log in evidence/sprint_NN/ | 0 (5/5 PASS; CSV CRLF→LF normalization reported) |
| CMD-03 / VAL-003 | `python3 -m smlsp3000.runner run CHAIN-EXP-016 --out research/sim/CHAIN-EXP-016` | execute the null-framework self-test; writes config.json, result.json, residual spectra, manifest.sha256 | 0 = outcome PASS | research/sim/CHAIN-EXP-016/ ; evidence/sprint_01/exp016_run.log | 0 (PASS; ~101 s wall) |
| CMD-04 | `python3 -m smlsp3000.runner verify-manifest research/sim/CHAIN-EXP-016` | verify artifact hashes of an evidence directory | 0 = all OK | stdout | 0 |
| CMD-05 (inherited regression) | `python3 -m unittest discover -s tests -t . -v` | full unit/regression suite incl. VAL-001 integrity, VAL-003 structural checks, CHAIN-EXP-016 same-build reproduction and the Sprint 3 reference tests (assets, kernels, scheduler, quantizer rules, engine) | 0 = all tests pass | evidence/sprint_NN/unittest_run.log | 0 (Sprint 1: 18 tests; Sprint 3: see evidence/sprint_03/unittest_run.log) |
| CMD-07 / VAL-008..011, VAL-017 (software cells) | `python3 -m smlsp3000.runner validate-sprint3 --out research/validation` | Sprint 3 Track A checks: rate ratios, quantizer rules, ramp coverage, determinism/partition, fold-back lines, hold droop/images vs closed form, gain/clamp/physical rejection, linked dual-mono properties, research slot skew | 0 = all PASS | research/validation/sp1200/{digital,input,output,calibration}/, research/validation/stereo/ ; evidence/sprint_03/validate_sprint3_run.log | 0 (5/5 PASS; ~21 s) |
| CMD-08 / CHAIN-EXP-017 | `python3 -m smlsp3000.runner run CHAIN-EXP-017 --out research/sim/CHAIN-EXP-017` | qualitative SP-12 pattern sanity (SIMULATION, INFORMATIONAL) | 0 = record written | research/sim/CHAIN-EXP-017/ ; evidence/sprint_03/exp017_run.log | 0 (pattern consistent; ~4 s) |
| CMD-10 / VAL-012..014 (software cells) | `python3 -m smlsp3000.runner validate-sprint4 --out research/validation` | Sprint 4 Track A checks: rate ratios, 18/16 code domains, R13 rules over all 262144 codes, R14 identity, determinism/partition, TRANSPARENT R12/R15 line transparency and fold-back, R11 gains/trim, 18-bit clamp, physical rejection, true stereo, route table | 0 = all PASS | research/validation/mpc3000/{digital,analog,path_comparison}/ ; evidence/sprint_04/validate_sprint4_run.log | 0 (3/3 PASS; ~29 s) |
| CMD-11 / VAL-015, VAL-016 (software cells) | `python3 -m smlsp3000.runner validate-sprint5 --out research/validation` | cascade composition identities, chain modes, latency alignment, interstage mapping/clamp/range, stereo linkage, product configuration, INFORMATIONAL CHAIN-EXP-013/014 software derivatives, listening-kit presence | 0 = all PASS | research/validation/cascade/ ; evidence/sprint_05/validate_sprint5_run.log | 0 (2/2 PASS; ~32 s) |
| CMD-12 / CHAIN-EXP-018 software arm | `python3 -m smlsp3000.runner listening-kit --out research/listening/CHAIN-EXP-018` | deterministic RMS-matched blinded LISTENING STIMULUS kit (audio to an ignored `stimuli/` directory; hashes, blind manifest, key, result form and generation record committed) | 0 = kit written | research/listening/CHAIN-EXP-018/ ; evidence/sprint_05/listening_kit_run.log | 0 (16 files; ~96 s) |
| CMD-13 (native configure + build) | `cmake -S native -B native/build -G Ninja -DCMAKE_BUILD_TYPE=Release && cmake --build native/build` | build the native production core (static library), the offline tool `native/build/smlsp3000_native` and the self-test `native/build/smlsp3000_selftest`; options `-O2 -ffp-contract=off -fno-fast-math -fexcess-precision=standard`, generic x86-64 (`SMLSP3000_NATIVE_ARCH=OFF`) | 0 = built | evidence/sprint_06/build_record.json ; evidence/sprint_06/native_build.log | 0 |
| CMD-14 (native self-test) | `cd native/build && ctest --output-on-failure` (equivalently `native/build/smlsp3000_selftest`) | runtime safety: determinism, partition invariance, internal chunking, zero/one-sample calls, non-finite input, over-range, bypass alignment, latency, automation across partitions, trim law, state v1 round trips/rejections, prepare rejections, reset | 0 = all PASS | evidence/sprint_06/native_selftest.log | 0 |
| CMD-15 / VAL-019..022 (software cells) | `python3 -m smlsp3000.runner validate-sprint6 --out research/validation --evidence evidence/sprint_06` | native production core vs the Python reference oracle: same-rate agreement at every rate and state, exact code streams, determinism/partitions, latency, cross-rate (frozen method), proxy convergence 8x/16x, state/parameter layers and automation fixtures (`--quick` for a reduced smoke pass) | 0 = all PASS | research/validation/{reference_production,rate_block,implementation_alias}/ ; evidence/sprint_06/state_parameter/ ; evidence/sprint_06/validate_sprint6_run.log | 0 |
| CMD-16 (native benchmark) | `python3 -m smlsp3000.runner native-bench --out evidence/sprint_06/benchmark --seconds 5 --trials 3 --warmup 1` | OWN-DEC-017 load/percentile benchmark of the Release core at 44.1/48 @64, 88.2/96 @128, 176.4/192 @256; raw per-callback times saved | 0 = every pair within budget | evidence/sprint_06/benchmark/ | 0 |
| CMD-17 (asset header sync) | `python3 tools/gen_native_assets.py --check` (regenerate without `--check`) | the generated `native/generated/track_a_assets_v1.hpp` must match the JSON assets/configurations/controls | 0 = UP TO DATE | tests/test_native_assets.py | 0 |
| CMD-09 / VAL-018 | `python3 -m smlsp3000.runner scope-audit --out evidence/sprint_03/scope_audit.json` | unity-pitch / non-goal scope audit of the reference code and configuration | 0 = PASS | evidence/sprint_03/scope_audit.json | 0 |
| CMD-06 | `sha256sum -c SHA256SUMS.txt` | planning-V1 byte manifest (historical); living docs revised after planning V1 legitimately differ; immutable set is enforced by CMD-02 | informational | — | 1 (docs/ACCEPTANCE_MATRIX.csv line endings; revised living docs) |

Rules: a command absent from this table is not an approved check. Adding a command requires a new revision of this file and a sprint report entry. Timings are informational. `PYTHONPATH` is not needed because every command runs from the repository root with the package in place.

## Checks that cannot run yet

| Check | Blocking gate | What is needed |
|---|---|---|
| VAL-004 documentary extraction / SPICE | G-03 | source access (archive.org, datasheet hosts) or sheets supplied through an approved route; ngspice or equivalent if AC analysis is to run |
| VAL-005…VAL-016 HARDWARE-FIT cells, thresholds, hardware-arm listening | G-04/G-05/G-06/G-07H | stock units, calibrated interface, operator, owner (Track B, deferred) |
| VAL-023…VAL-027 native plugin/host/release | G-09/G-10/G-11 | approved formats/OS/DAW matrix, SDK/licence, native hosts |
| Windows native build/validation of the Sprint 6 core | G-09 (platform) | a Windows x86_64 toolchain (MSVC or MinGW) or a Windows machine; nothing in this container can produce it |
