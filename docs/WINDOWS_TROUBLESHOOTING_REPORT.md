# SML SP-3000 — Windows troubleshooting and delivery report

Date: 2026-10-07. Product: 0.7.0. This is the consolidated current report. Earlier running reports and package snapshots retain their historical statuses.

## 1. Current outcome

**The owner now reports that the plugin works in FL Studio.** An earlier owner screenshot independently showed SML SP-3000 as `ok`, VST3, 64-bit, Effect. The agent installed and hashed the bundle, validated the installed copy, and corrected the scanner search-path problem. DAW operation is owner-reported; a complete musical listening, project-reopen, offline-bounce or automation acceptance session was not recorded.

Windows build, native reference matrix, CTest, plugin state/bypass/equivalence and pluginval passed. Full validation is not all green: two unit tests remain failed, a callback timing target was missed and combined Windows sanitizer proof is missing. Experimental use does not erase those results.

DSP, native core, product processor/editor and pinned JUCE source were not changed. No reference outputs or acceptance tolerances were changed. No commit, merge, push, publication or Sprint 8 execution occurred.

## 2. Exact baseline and machine

| Item | Value |
|---|---|
| Repository | `D:\SML Projects\SML-SP-3000` |
| Remote | `https://github.com/soundwave-machine-learning/smlsp3000` |
| Branch | `claude/autonomous-build` |
| HEAD | `38ff483ed6f75d080bfc5e06e32465e4804294ca` |
| Working tree | DIRTY: approved harness/regression changes and documentation |
| Build | `D:\SML Builds\SML-SP-3000\windows-sprint7-release` |
| Windows / CPU | Windows 10 Pro 10.0.19045 x64; AMD Ryzen 5 1600X, 6 cores / 12 threads |
| Visual Studio | 2022 Community 17.14.37; MSVC 19.44.35228.0, v143 14.44.35207 |
| Windows SDK | 10.0.26100.0 |
| CMake / generator | 4.4.0; Visual Studio 17 2022; x64 Release |
| Python / NumPy | 3.11.15 / 2.4.3; existing Hermes venv, not upgraded |
| JUCE | 8.0.9, `f72bad64d29715216226685810c5196bd0d79d77`, intentional detached HEAD |
| JUCE path | `D:\SML Projects\SML-SP-3000\third_party\JUCE` |
| FL Studio | 2025, 25.1.5.4976; Plugin Manager 1.8.1.4976 |

## 3. Troubleshooting chronology

### Local setup, dependency and permissions

The owner fixed GitHub authentication, cloned the repository and supplied the pinned JUCE checkout. Required branch/HEAD and clean source/JUCE state were verified initially. Authentication and cloning were not repeated after those local inputs existed.

C: free space was constrained, so repository, dependency and build outputs stayed on D:. Early D: write denial persisted even in a manually created directory. Work switched to manual Administrator PowerShell orchestration. Later scoped tool permission approvals allowed direct execution. This was an execution-permission issue, not a source defect; UAC/security controls were not bypassed.

The default Ninja command was inaccessible under the sandbox; Visual Studio's bundled Ninja was callable. The successful build used the documented Visual Studio generator, so Ninja was unnecessary. No compiler-flag workaround or DSP source change was made to compensate for permissions/tools.

### Configure/build

Pinned JUCE's juceaide bootstrap completed; CMake configured and generated successfully. All seven original targets and the subsequently approved processor-regression target built in Release.

Recorded warnings included unused local `hw` in native/src/mpc_core.cpp, a constant conditional in native/src/engine.cpp, shadowed locals in native/tests/selftest.cpp, JUCE's obsolete splash-screen define notice, and later MSB8029 concerning the TEMP/build arrangement. Warnings were not globally suppressed and DSP was not changed to remove them.

### PowerShell test logging

Under Windows PowerShell 5.1 with `$ErrorActionPreference='Stop'`, native stderr redirected with `*>` produced `NativeCommandError` and interrupted the intended summary. Logging moved to Python subprocess with stdout/stderr combined into a file and explicit exit-code capture. Tests were unchanged.

### CHAIN-EXP-016 exact-reference failure — OPEN

`tests/test_exp016_reproduction.py:21` failed exact raw-output SHA-256 equality. The isolated diagnostic ran one test, one failure, in 241.864 seconds. The original record identifies Python 3.13.16 / NumPy 2.5.3; this Windows run used 3.11.15 / 2.4.3.

Thirty-three generated configuration values differed before native plugin processing. Observed tone-amplitude delta: `3.4694469519536142e-17`; frequency delta: `4.5474735088646412e-13 Hz`. This establishes reference-generation/environment differences, not their sole cause. Python, NumPy, platform math and SIMD effects were not individually isolated.

Original float64 waveform arrays are not committed. Original-waveform maximum/RMS error cannot be recovered from hashes alone. References, tolerances and acceptance hashes were not changed. This remains FAIL, even though native-to-current-Python comparisons passed later.

### VST3 harness crash and approved fix

VAL-026 announced maximum block size 512 but sent irregular callbacks up to 9000. JUCE's VST3 wrapper scratch allocation followed the announced maximum. Windows exposed access violation `0xC0000005`. This violated the hosting contract; it did not justify changing JUCE or DSP and was not proven Windows-only.

Owner-approved correction:

- `smlsp3000/validation/plugin_track_a.py` now announces 9000 for the unchanged irregular schedule. Comparisons and thresholds remain unchanged.
- New `plugin/tools/processor_test_main.cpp`, wired through `plugin/CMakeLists.txt`, directly prepares SMLProcessor for 512 and tests callbacks including a complete 9000 block, at all six rates in float32 and float64. This preserves oversized-processor coverage.

Schedule: `[1,7,500,2048,64,3,1000,4096,2,1,513,8192,9000]`. New regression: 72 named checks passed. A malformed VST3 host exceeding its negotiated maximum remains outside the corrected hosted test's proof.

The product VST3 binary SHA-256 was unchanged by this correction. External Windows runners used the proper .exe/Release paths and corrected platform metadata. An unsupported extra metadata field was rejected by the strict report schema; context was instead recorded in existing supported fields. Validation logic was not replaced.

### CRLF integrity failure — OPEN

Ten immutable checkout documents failed byte hashes due to system `core.autocrlf=true`: two research documents and eight sprint prompts. Their committed Git blobs matched the manifests, and in-memory CRLF-to-LF normalization matched. Raw checkout bytes still fail. No immutable file, manifest or acceptance threshold was rewritten.

### Safety, performance and sanitizers

Existing portable VAL-024 sections 3–5 passed unchanged: finite edge/invalid input, zero silence, denormal handling and 47 rapid automation events. All 36 benchmark trials met mean-load limits. Separately reported p99.9 targets were missed at all six rate/buffer pairs, with 1,233 overruns retained. Ordinary priority and concurrent applications were possible; scheduling interference is plausible, not a proven sole cause. No hardware-fit or guaranteed real-time claim follows.

Combined ASan/UBSan was NOT RUN on Windows: the existing command uses GCC/Clang flags, not the prescribed MSVC configuration. Portable subset PASS is not full VAL-024 PASS.

### Experimental staging and installation

The owner first required every gate to pass before staging/installing. Later explicit instructions approved an experimental owner-test copy with unresolved gates, then installation for DAW use. These permissions did not convert failures to PASS or authorize DSP, golden, distribution or Sprint 8 changes.

The complete bundle was installed in the standard VST3 folder. No prior SML SP-3000 bundle existed there, so no replacement/old-install backup was necessary. Every installed file matched its staged source. Installed-copy pluginval strictness 8 passed again.

### Plugin Manager crashes and UI automation

Computer Use screenshot capture failed with `SetIsBorderRequired failed: No such interface supported (0x80004002)`. Accessibility exposed mostly unlabeled panes, preventing safe automatic clicks.

The agent opened a separate Plugin Manager; the owner later opened one through FL Studio. The agent closed its extra instance gracefully. The FL-owned scanner remained trapped in nested errors: PluginManager.exe offset `49BA1B`, read of `0xF4`. Acknowledging the dialog did not recover it. Only the verified stuck scanner child was terminated; FL Studio stayed open and responsive. No project was closed and no database/cache reset occurred. Duplicate instances were a possible contributor, not an established cause of that exception.

Scanner `auto start` and `rescan previous` were backed up and changed from 1 to 0. `verify plugins` remained 1. Backup: `FL_SCANNER_SETTINGS_BEFORE.json` in the build directory.

### Quarantine archive scan freeze — confirmed search-path defect

The owner's screenshot showed SML already scanned as `ok`, followed by scanning under:

`D:\Audio\12_ARCHIVE\QUARANTINE\C_TEMP_2026-09-22\178AC34E-9DF9-4E53-BF59-1F307C598E3B`

That directory contains archived Windows DISM components, including DismCore.dll, AppxProvider.dll and DismHost.exe. Inspected DismCore.dll had a valid Microsoft Windows signature. These are not audio plugins. The screenshot truncated the current filename, so a specific crashing DLL was not conclusively identified. QUARANTINE was a folder name, not an antivirus alert about SML.

Confirmed cause of unwanted scanning: enabled root `D:\Audio\` at `HKCU\Software\Image-Line\Shared\Plugin search paths\List\16`. It includes projects, samples, installers and archives. After closing Plugin Manager, only this entry's `selected` value changed from 1 to 0, with backup `FL_AUDIO_SCAN_PATH_BEFORE.json`. Standard VST3 scanning stayed enabled. No archive file was executed by the agent, moved, deleted or released from security quarantine; no security settings changed.

Genuine plugins elsewhere under D:\Audio may need dedicated format-specific scan directories later; do not re-enable the broad archive-containing root.

Cancelling did not leave SML visible to the owner; no SML file was found in the checked user database folder. Cancellation preventing persistence is consistent with the observations, not fully traced internal FL behavior. Earlier advice that cancellation would preserve the entry was too strong. After the search-path correction and retry, the owner reports the plugin works.

## 4. Executed validation results

| Check | Result | Timing |
|---|---|---:|
| Release configure/build | PASS; eight targets | Build logs |
| Original native CTest | PASS, 2/2 | 8.65 s |
| Post-fix CTest | PASS, 3/3; 32 core + 26 adapter + 72 processor = 130 named checks | 12.95 s |
| Unit discovery | FAIL; 57/59 pass, 2 fail, 0 skips, exit 1 | 311.481 s test / 312.0247501 s wall |
| Host smoke | PASS; six rates × two precisions, 12/12 | 24.965 s |
| VAL-021 native/reference | PASS; 216/216 cells; zero converter-code/count mismatches | 1089.8568175 s |
| VAL-019 rate/block | PASS | 106.1930164 s |
| VAL-020 implementation/alias | PASS | 185.0028243 s |
| VAL-022 state/parameters | PASS | 3.0704492 s |
| VAL-026 plugin equivalence/state/automation | PASS; full six-rate run | 197.3354602 s |
| VAL-023 latency/bypass | PASS | 10.2599452 s |
| VAL-025 software UI/safety/Standalone | PASS; five screenshots; no owner acceptance implied | 12.5680821 s |
| VAL-024 portable subset | PASS under unchanged enforced criteria; full sanitizer proof missing | 54.2760534 s |
| pluginval build copy | PASS; strictness 8, 25 groups, exit 0 | 24.249149 s |
| pluginval installed copy | PASS; strictness 8, exit 0 | 23.9848951 s |
| Generated native assets | UP TO DATE | Not separately recorded |
| FL scan | Screenshot: ok / VST3 / 64-bit / Effect | Owner supplied |
| FL operation | Owner reports plugin works | Rate/buffer/audio-session details not supplied |

VAL-021 worst per-cell RMS error: `6.127461550614579e-16`; worst peak error: `3.3306690738754696e-15`. These are Windows native versus current Python oracle comparisons, not original CHAIN-EXP-016 waveform errors or hardware errors. Counts not emitted by individual tools are not invented as a suite-wide assertion total.

| Sample rate | Latency samples |
|---|---:|
| 44.1 kHz | 298 |
| 48 kHz | 310 |
| 88.2 kHz | 426 |
| 96 kHz | 449 |
| 176.4 kHz | 682 |
| 192 kHz | 728 |

| Rate / buffer | Worst trial mean load | Limit | Overruns | p99.9 target |
|---|---:|---:|---:|---|
| 44100 / 64 | 13.2053% | 20% | 14 | NOT MET |
| 48000 / 64 | 18.4765% | 20% | 61 | NOT MET |
| 88200 / 128 | 14.9391% | 40% | 14 | NOT MET |
| 96000 / 128 | 33.9009% | 40% | 251 | NOT MET |
| 176400 / 256 | 23.1718% | 60% | 42 | NOT MET |
| 192000 / 256 | 53.2339% | 60% | 851 | NOT MET |

## 5. Artifact inventory

Installed bundle: `C:\Program Files\Common Files\VST3\SML SP-3000.vst3`.
Installed executable: `Contents\x86_64-win\SML SP-3000.vst3` inside that bundle.
VST3 executable size: 6,938,624 bytes.
SHA-256: `E0D0B731698ED7739346D5C00FC9C15532925B04257DF7D9B070385ACB5F04E6`.

Build-relative VST3: `SMLSP3000_artefacts\Release\VST3\SML SP-3000.vst3`.
Build-relative Standalone: `SMLSP3000_artefacts\Release\Standalone\SML SP-3000.exe`.
Standalone size: 8,014,336 bytes; SHA-256 `3746D29C74B48FD449E69F98550AC36A74084245585733C4CAB0125336B32A02`.
No signing performed; Standalone inspected as NotSigned. Existing CMake disables automatic moduleinfo generation (`VST3_AUTO_MANIFEST FALSE`); no module metadata hash claimed.

Experimental package: `D:\SML Builds\SML-SP-3000\windows-sprint7-release\review\sprint7-experimental-20261007-164049`. Complete bundle and all 38 manifest-covered files verified. This historical package predates completed native-matrix results, installation and owner DAW confirmation. Its old pending statuses must not be mistaken for current status; do not rewrite it to erase chronology.

## 6. Commands, evidence and local changes

Exact commands CMD-W01..W09: `docs/BUILD_COMMANDS.md`. All paths below are relative to the external build directory.

- `approved-fix-configure.log`, `approved-fix-build.log`, `approved-fix-ctest.log`, `approved-fix-validation.log`.
- `windows-full-unittest.log`, `windows-full-unittest-status.json` and original reference-failure diagnostic logs.
- `windows-validation-agent/host_matrix/VAL-026_software.json`, `latency_bypass/VAL-023_software.json`, `safety_ui/VAL-025_software.json`, screenshots and timing records.
- `windows-validation-agent/VAL-024_windows_portable.json`, exact source `VAL-024_executed_source.txt`, all benchmark trials.
- `windows-native-full-matrix/` with VAL-019/020/021/022 results/timings; `windows-native-full-matrix.log`; exit 0.
- `windows-validation-agent/pluginval/` and `installed-pluginval/`: exact commands, hashes, logs, exit codes.
- External orchestration: `run_windows_checks.py`, `run_windows_safety.py`, `run_windows_native_matrix.py`.
- `WINDOWS_INSTALLATION.json`, `FL_SCANNER_FAILURE.json`, settings backups and `FL_ARCHIVE_SCAN_DIAGNOSIS.txt`.
- Portable pluginval 1.0.4: `tools/pluginval-1.0.4/pluginval.exe`, hash `F4AC5C31C5544A434F73E686B816861D92C22AE849D69AD693681CBC9522FCD8`. Official ZIP hash: `C08E61CE3B96DB41636F8EC7E76F4C7E2C13EBDAC7FA1B5A1F52B4F32EC715AB`.

Approved code changes are limited to `plugin/CMakeLists.txt`, new `plugin/tools/processor_test_main.cpp`, and the host max-block announcement in `smlsp3000/validation/plugin_track_a.py`. Documentation changed in BUILD_COMMANDS, PROJECT_HANDOFF and reports/handoff. No commit was created. Checking out HEAD alone loses the uncommitted test correction; preserve the patch and new test source included in the handoff bundle.

## 7. Remaining gates and next work

Still open: CHAIN-EXP-016 exact reproduction; raw CRLF checkout integrity; p99.9 timing target; combined Windows sanitizer proof; formal owner UI/listening acceptance; G-10; DI-001 owner decision; distribution licensing and hardware fit. DAW loading success does not automatically close these.

UI/preset work has not started. The owner requested this handoff so a new task can design the UI and presets while preserving the working DSP and compatibility. This is not execution of Sprint 8 or permission to publish. Read [UI/preset handoff](UI_PRESET_HANDOFF.md) and [next-task prompt](NEXT_UI_PRESET_TASK.md).
