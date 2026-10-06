# Build, test and analysis command manifest

Revision: execution V1 (Sprint 1) · 2026-10-06

Status: FROZEN for the reference/analysis stack (ENG-DEC-011). Every command below was executed in Sprint 1 with the recorded exit code (evidence/sprint_01/smoke_run.json, evidence/sprint_01/unittest_run.log, evidence/sprint_01/exp016_run.log). Native plugin build/host commands do not exist yet: G-09 target matrix UNKNOWN; nothing speculative is listed.

## Environment of record

| Item | Value |
|---|---|
| Working directory | repository root (`/home/user/smlsp3000` in the Sprint 1 container; any clone root is equivalent) |
| Shell | POSIX sh / bash |
| Python | 3.13.16 (CPython), system interpreter `python3`; no virtual environment, no `pip install` |
| numpy | 2.5.3 |
| git | 2.43.0 |
| OS | Linux 6.18.44 x86_64, Ubuntu 24.04 userland, 4 vCPU, 15 GB RAM |
| Optional native toolchain present but unused | gcc 13.3.0, clang, cmake 3.28.3, ninja, make |
| Not installed | scipy, pytest, soundfile, ngspice, plugin SDKs, DAWs |

Reproduction on another machine requires Python ≥ 3.12 and numpy ≥ 2.0; floating-point results of CHAIN-EXP-016 are same-build goldens (validation domain 2) and may differ in low-order digits across platforms/BLAS builds — that is a recorded limitation, not a pass criterion.

## Commands

| Check ID | Command (from repository root) | Purpose | Exit code policy | Evidence route | Sprint 1 result |
|---|---|---|---|---|---|
| CMD-01 | `python3 -c "import numpy, sys; print(sys.version, numpy.__version__)"` | version stamp | 0 | evidence/sprint_NN/preflight.json | 0 |
| CMD-02 / VAL-001 | `python3 tools/check_repo_integrity.py` | research-source SHA-256, 8 contracts, local links, 28 matrix rows, SHA256SUMS (immutable set strict) | 0 = all PASS | stdout log in evidence/sprint_NN/ | 0 (5/5 PASS; CSV CRLF→LF normalization reported) |
| CMD-03 / VAL-003 | `python3 -m smlsp3000.runner run CHAIN-EXP-016 --out research/sim/CHAIN-EXP-016` | execute the null-framework self-test; writes config.json, result.json, residual spectra, manifest.sha256 | 0 = outcome PASS | research/sim/CHAIN-EXP-016/ ; evidence/sprint_01/exp016_run.log | 0 (PASS; ~101 s wall) |
| CMD-04 | `python3 -m smlsp3000.runner verify-manifest research/sim/CHAIN-EXP-016` | verify artifact hashes of an evidence directory | 0 = all OK | stdout | 0 |
| CMD-05 (inherited regression) | `python3 -m unittest discover -s tests -t . -v` | full unit/regression suite incl. VAL-001 integrity, VAL-003 structural checks and CHAIN-EXP-016 same-build reproduction | 0 = all tests pass | evidence/sprint_NN/unittest_run.log | 0 (18 tests OK; ~108 s wall) |
| CMD-06 | `sha256sum -c SHA256SUMS.txt` | planning-V1 byte manifest (historical); living docs revised after planning V1 legitimately differ; immutable set is enforced by CMD-02 | informational | — | 1 (docs/ACCEPTANCE_MATRIX.csv line endings; revised living docs) |

Rules: a command absent from this table is not an approved check. Adding a command requires a new revision of this file and a sprint report entry. Timings are informational. `PYTHONPATH` is not needed because every command runs from the repository root with the package in place.

## Checks that cannot run yet

| Check | Blocking gate | What is needed |
|---|---|---|
| VAL-004 documentary extraction / SPICE | G-03 | source access (archive.org, datasheet hosts) or sheets supplied through an approved route; ngspice or equivalent if AC analysis is to run |
| VAL-005…VAL-016 hardware fits, thresholds, listening | G-04/G-05/G-06/G-07 | stock units, calibrated interface, operator, owner |
| VAL-019…VAL-022 production engine | G-08 | owner numeric/parameter budgets; production stack decision |
| VAL-023…VAL-027 native plugin/host/release | G-09/G-10/G-11 | approved formats/OS/DAW matrix, SDK/licence, native hosts |
