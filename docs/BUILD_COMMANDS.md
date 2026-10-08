# Build, test and analysis command manifest

Revision: execution V8 (manual + Preset Lab, after Sprint 7) + Windows validation addendum · 2026-10-08 · supersedes execution V7

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
| CMD-18 (plugin configure + build, Linux dev container) | `git clone --depth 1 --branch 8.0.9 https://github.com/juce-framework/JUCE third_party/JUCE` (once; pinned, git-ignored) then `CXXFLAGS="-DJUCE_USE_XRANDR=0 -DJUCE_USE_XINERAMA=0 -DJUCE_USE_XCURSOR=0 -DJUCE_USE_CURL=0 -DJUCE_WEB_BROWSER=0 -DJUCE_ALSA=0 -DJUCE_JACK=0" cmake -S plugin -B plugin/build -G Ninja -DCMAKE_BUILD_TYPE=Release && cmake --build plugin/build` | JUCE 8.0.9 wrapper: VST3 + Standalone (`plugin/build/SMLSP3000_artefacts/Release/{VST3,Standalone}`), native core, host harness and editor snapshot tool. The CXXFLAGS environment is a Linux dev-container workaround (missing Xrandr/Xinerama/Xcursor/ALSA headers) that JUCE's juceaide bootstrap needs; it adds only `-D` definitions (no floating-point flags). On Windows no CXXFLAGS are needed (docs/WINDOWS_HANDOFF.md) | 0 = built | evidence/sprint_07/plugin_configure.log, plugin_build.log, build_record.json | 0 |
| CMD-19 / VAL-023..026 (software cells, Linux) | `python3 -m smlsp3000.runner validate-sprint7 --evidence evidence/sprint_07` | plugin wrapper checks through the JUCE VST3 host harness under Xvfb: host matrix (plugin vs adapter vs reference, float32/float64, partitions, offline, automation, state, instances, editor), latency/bypass, real-time/state/numerical safety (allocation counter, ASan/UBSan build, timing), safety/UI (screenshots, indicators, exposed parameters), plus pluginval (CMD-20) | 0 = all PASS | evidence/sprint_07/{host_matrix,latency_bypass,realtime_state,safety_ui,pluginval}/ ; evidence/sprint_07/validate_sprint7_run.log | 0 |
| CMD-20 (pluginval) | `xvfb-run -a tools_external/pluginval/pluginval --strictness-level 8 --validate-in-process --verbose --output-dir evidence/sprint_07/pluginval "plugin/build/SMLSP3000_artefacts/Release/VST3/SML SP-3000.vst3"` (pluginval 1.0.4 Linux binary, sha256 recorded; git-ignored) | external plugin validation, strictness 8 | 0 = pass | evidence/sprint_07/pluginval/ | 0 |
| CMD-21 (Preset Lab build) | part of CMD-18 (`cmake --build plugin/build`), or `cmake --build plugin/build --target smlsp3000_preset_lab smlsp3000_preset_lab_test` | development authoring tool `plugin/build/tools/preset_lab/smlsp3000_preset_lab_artefacts/Release/smlsp3000_preset_lab` and its self-test; separate targets under plugin/tools/preset_lab/ (product targets untouched) | 0 = built | evidence/preset_lab/validation/validation_run.log | 0 |
| CMD-22 (Preset Lab tests) | `ctest --test-dir plugin/build/tools/preset_lab --output-on-failure` then `python3 -m unittest tests.test_preset_lab -v` (both under Xvfb on Linux; the ctest wraps itself) | candidate format/validation/no-partial-application/INIT/determinism/metadata-independence (ctest) and lab render == native HostAdapter render bit-for-bit (unittest) | 0 = all PASS | evidence/preset_lab/validation/validation_run.log | 0 |
| CMD-23 (Preset Lab demo material / screenshots) | `python3 -m smlsp3000.runner preset-lab-demo-source --out reference/preset_lab/sources --rate 48000` then `xvfb-run -a -s "-screen 0 1400x900x24" plugin/build/tools/preset_lab/smlsp3000_preset_lab_artefacts/Release/smlsp3000_preset_lab --snapshot evidence/preset_lab/screenshots reference/preset_lab/sources/demo_beat_48000.wav presets/candidates/demo/*.json` | deterministic synthetic demo beat (hash record committed, audio ignored) and the tool screenshots (INIT, four demo candidates after an audition render, modified/save view) | 0 = written | evidence/preset_lab/screenshots/ ; reference/preset_lab/sources/demo_beat_48000.json | 0 |
| CMD-09 / VAL-018 | `python3 -m smlsp3000.runner scope-audit --out evidence/sprint_03/scope_audit.json` | unity-pitch / non-goal scope audit of the reference code and configuration | 0 = PASS | evidence/sprint_03/scope_audit.json | 0 |
| CMD-06 | `sha256sum -c SHA256SUMS.txt` | planning-V1 byte manifest (historical); living docs revised after planning V1 legitimately differ; immutable set is enforced by CMD-02 | informational | — | 1 (docs/ACCEPTANCE_MATRIX.csv line endings; revised living docs) |

Rules: a command absent from this table is not an approved check. Adding a command requires a new revision of this file and a sprint report entry. Timings are informational. `PYTHONPATH` is not needed because every command runs from the repository root with the package in place.

## Checks that cannot run yet

| Check | Blocking gate | What is needed |
|---|---|---|
| VAL-004 documentary extraction / SPICE | G-03 | source access (archive.org, datasheet hosts) or sheets supplied through an approved route; ngspice or equivalent if AC analysis is to run |
| VAL-005…VAL-016 HARDWARE-FIT cells, thresholds, hardware-arm listening | G-04/G-05/G-06/G-07H | stock units, calibrated interface, operator, owner (Track B, deferred) |
| VAL-023…VAL-027 native plugin/host/release | G-09/G-10/G-11 | approved formats/OS/DAW matrix, SDK/licence, native hosts |
| Windows native build/validation of the core, VST3 and Standalone; FL Studio session/automation/bounce checks | G-09 (platform) | a Windows x86_64 machine with Visual Studio 2022 (MSVC v143), CMake ≥ 3.22, Ninja or the VS generator, the pinned JUCE checkout and FL Studio; procedure: docs/WINDOWS_HANDOFF.md |


## Windows validation addendum (owner-approved harness correction, 2026-10-07)

The Windows continuation starts from `38ff483ed6f75d080bfc5e06e32465e4804294ca` and retains all prior numerical criteria. The approved correction changes the VAL-026 VST3 host announcement to 9000 samples for the unchanged irregular schedule. Calls larger than the processor's prepared maximum remain covered directly by the new `processor_oversized_test`. No DSP or JUCE changes are part of this correction. See [Windows validation addendum](sprint_reports/SPRINT_07_WINDOWS_VALIDATION.md) for executed results and unresolved gates.

| Check ID | Windows command | Purpose | Exit policy |
|---|---|---|---|
| CMD-W01 | `cmake -S plugin -B "D:/SML Builds/SML-SP-3000/windows-sprint7-release" -G "Visual Studio 17 2022" -A x64 -DCMAKE_BUILD_TYPE=Release -DSMLSP3000_JUCE_DIR="D:/SML Projects/SML-SP-3000/third_party/JUCE"` | Configure the existing approved out-of-tree Windows build | 0 = configured |
| CMD-W02 | `cmake --build "D:/SML Builds/SML-SP-3000/windows-sprint7-release" --config Release --target smlsp3000_processor_test SMLSP3000_VST3 SMLSP3000_Standalone smlsp3000_host_harness smlsp3000_editor_snapshot smlsp3000_selftest smlsp3000_adapter_test smlsp3000_native` | Build the direct regression and original seven targets | 0 = built |
| CMD-W03 | `ctest --test-dir "D:/SML Builds/SML-SP-3000/windows-sprint7-release" -C Release --verbose --no-tests=error --stop-on-failure --output-log "D:/SML Builds/SML-SP-3000/windows-sprint7-release/approved-fix-ctest.log"` | All three native/direct-processor CTest tests | 0 = all three pass |

Windows VAL-026/VAL-023 use the existing functions with runtime paths pointing to `.exe` binaries in the external build directory. Reports and scratch files stay in that directory. Runtime report labels identify Windows/MSVC without changing checks or thresholds. The local orchestration script and logs are retained alongside the build; it is not a source-code or acceptance-policy replacement.

### Executed Windows continuation commands

Run from the project root with `SMLSP3000_NATIVE` pointing to the Release native executable, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUTF8=1`, and TEMP/TMP under the external build directory. The retained scripts provide exact path overrides and metadata corrections; reference acceptance logic is unchanged.

- CMD-W04: `python "D:/SML Builds/SML-SP-3000/windows-sprint7-release/run_windows_checks.py"` — full VAL-026 and VAL-023; exit 0. Log: `approved-fix-validation.log`.
- CMD-W05: `python "D:/SML Builds/SML-SP-3000/windows-sprint7-release/run_windows_checks.py" VAL-025` — software UI/safety checks; exit 0. Log: `windows-ui-safety.log`.
- CMD-W06: `python -m unittest discover -s tests -t . -v` — all 59 unit tests; exit 1, 57 pass and two retained failures. Native stderr captured with Python subprocess to avoid Windows PowerShell 5.1 NativeCommandError termination. Log: `windows-full-unittest.log`.
- CMD-W07: `python "D:/SML Builds/SML-SP-3000/windows-sprint7-release/run_windows_safety.py"` — unchanged VAL-024 sections 3–5, quick=False; exit 0 for the portable subset only. Exact extracted source and all trials retained. Combined sanitizers NOT RUN, p99.9 target NOT MET. Log: `windows-safety-benchmark.log`.
- CMD-W08: `"D:/SML Builds/SML-SP-3000/windows-sprint7-release/tools/pluginval-1.0.4/pluginval.exe" --strictness-level 8 --validate-in-process --verbose --output-dir "D:/SML Builds/SML-SP-3000/windows-sprint7-release/windows-validation-agent/pluginval" "D:/SML Builds/SML-SP-3000/windows-sprint7-release/SMLSP3000_artefacts/Release/VST3/SML SP-3000.vst3"` — executable invoked with PowerShell call operator or Python subprocess; exit 0. Exact invocation and hashes retained in pluginval_record.json.

- CMD-W09: `python "D:/SML Builds/SML-SP-3000/windows-sprint7-release/run_windows_native_matrix.py"` — full existing VAL-021, VAL-019, VAL-020 and VAL-022 in sequence with quick=False. Only runtime executable/output paths and report platform metadata differ. Stops after any non-PASS result; outputs under `windows-native-full-matrix`, log `windows-native-full-matrix.log`. This continuation was authorized on 2026-10-07; execution completed with VAL-021, VAL-019, VAL-020 and VAL-022 PASS, exit 0. See the consolidated Windows troubleshooting report for timings and numerical results.

### Windows reconciliation commands (claude/manual-preset-lab, 2026-10-07)

Same build directory and environment as CMD-W01..W09. Results: [Windows reconciliation report](sprint_reports/WINDOWS_RECONCILIATION_REPORT.md).

- CMD-W10: CMD-W01 configure, then `cmake --build "D:/SML Builds/SML-SP-3000/windows-sprint7-release" --config Release --target smlsp3000_preset_lab smlsp3000_preset_lab_test smlsp3000_processor_test SMLSP3000_VST3 SMLSP3000_Standalone smlsp3000_host_harness smlsp3000_editor_snapshot smlsp3000_selftest smlsp3000_adapter_test smlsp3000_native` - exit 0. Preset Lab executable: `D:/SML Builds/SML-SP-3000/windows-sprint7-release/tools/preset_lab/smlsp3000_preset_lab_artefacts/Release/smlsp3000_preset_lab.exe`.
- CMD-W11: CMD-W03 ctest - four tests (processor_oversized_test, native_selftest, host_adapter_test, preset_lab_test), exit 0.
- CMD-W12: `python "D:/SML Builds/SML-SP-3000/windows-sprint7-release/run_windows_preset_lab_tests.py"` - tests/test_preset_lab.py with the lab `.exe` and native Release paths substituted (test logic unchanged); 7/7, exit 0.
- CMD-W13: CMD-W04 (VAL-026, VAL-023) and CMD-W08 (pluginval 8) re-run on the reconciled build - exit 0; `python -m smlsp3000.runner scope-audit --out <build>/reconcile-scope-audit.json` - PASS.
- CMD-W14: `smlsp3000_preset_lab.exe --validate presets/candidates/character_audit/<file>.json` for the eight starting points - all OK; `smlsp3000_preset_lab.exe --snapshot <build>/reconcile-preset-lab-gui/screenshots reference/preset_lab/sources/demo_beat_48000.wav presets/candidates/character_audit/*.json` - exit 0, 10 PNG (run from the project root after `python -m smlsp3000.runner preset-lab-demo-source --out reference/preset_lab/sources --rate 48000`).
