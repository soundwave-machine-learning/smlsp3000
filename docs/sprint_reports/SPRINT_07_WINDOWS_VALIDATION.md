> CURRENT STATUS: Owner reports the installed plugin works in FL Studio; full native matrix passed. Earlier blocked/pending/no-install entries below are chronological snapshots. Open validation gates remain. See [consolidated report](../WINDOWS_TROUBLESHOOTING_REPORT.md) and [UI/preset handoff](../UI_PRESET_HANDOFF.md).

# Sprint 7 Windows validation addendum — BLOCKED

Date: 2026-10-07. Baseline: `38ff483ed6f75d080bfc5e06e32465e4804294ca`, branch `claude/autonomous-build`. This is Windows validation of Sprint 7, not Sprint 8 or a release. Changes are local and uncommitted.

## Approved correction

The owner approved correcting the VST3 test host's announced maximum and adding a direct processor oversized regression. VAL-026 previously prepared a maximum of 512 samples but delivered callbacks up to 9000 samples. JUCE's VST3 wrapper allocated its channel scratch buffers for the announced maximum; the Windows harness crashed with `0xC0000005` during irregular callbacks. The corrected validation announces 9000 samples and keeps the exact schedule and numerical comparisons. `processor_oversized_test` separately prepares `SMLProcessor` for 512 samples and delivers the original irregular schedule, including a complete 9000-sample callback, in float32 and float64 at all six rates. This preserves direct processor oversized-call coverage. Malformed VST3 hosts exceeding the negotiated maximum remain outside the corrected hosted test's proof.

No native core, DSP, product processor/editor, JUCE, golden, or tolerance changes were made. The VST3 executable remains byte-identical to the pre-correction build (SHA-256 `E0D0B731698ED7739346D5C00FC9C15532925B04257DF7D9B070385ACB5F04E6`).

## Executed results

- Windows 10 Pro 10.0.19045 x64; AMD Ryzen 5 1600X, 6 cores/12 threads.
- Visual Studio 2022 Community 17.14.37; MSVC 19.44.35228.0; SDK 10.0.26100.0; CMake 4.4.0; Visual Studio 17 2022 generator, x64 Release.
- JUCE 8.0.9 at `f72bad64d29715216226685810c5196bd0d79d77`, unchanged.
- CMD-W01 configure PASS. CMD-W02 build of all eight targets PASS.
- CMD-W03: 3/3 tests PASS, exit 0, 12.95 seconds. Direct processor: 72 named checks. Native core: 32 named checks. Adapter: 26 named checks. Total: 130, zero failures. Both process-allocation checks passed.
- Earlier VST3 host loading/lifecycle matrix: 12/12 rate/precision configurations PASS in 24.965 seconds; all reported latencies match the Sprint 7 expectations.
- Generated native asset header: UP TO DATE.
- Full unit suite: 59 tests, 57 PASS, 2 FAIL, no skips; 311.481 seconds test time, 312.0247501 seconds wall time, exit 1. Failures are the two retained gates below.
- Corrected full VAL-026: PASS, 197.3354602 seconds. All six sample rates, float32/float64, plugin-to-adapter bit identity, reference limits, irregular partitions, automation, state mutations, instance/reprepare/editor checks passed.
- VAL-023: PASS, 10.2599452 seconds. Latencies 298/310/426/449/682/728 samples at 44.1/48/88.2/96/176.4/192 kHz. Latency-aligned bypass and 10 ms crossfade checks passed.
- VAL-025 software checks: PASS, 12.5680821 seconds. Five Windows screenshots, indicators, exposed parameters and bounded Standalone smoke completed. These do not constitute owner UI or listening acceptance.
- pluginval 1.0.4 Windows, strictness 8, in-process verbose: PASS, exit 0, 25 groups, 24.249149 seconds. Portable dependency stored only under the build directory. Executable SHA-256: `f4ac5c31c5544a434f73e686b816861d92c22ae849d69ad693681cbc9522fcd8`.
- VAL-024 Windows portable sections 3–5: PASS under the unchanged existing failure criteria, 54.2760534 seconds. Invalid/edge input remained finite, silence was zero, plugin matched adapter, and 47 rapid automation events passed. All 36 performance trials retained; all mean-load limits passed. Full VAL-024 is INCOMPLETE because combined ASan/UBSan validation was not run on Windows.

## Unresolved gates

1. CHAIN-EXP-016 exact committed-reference reproduction FAIL at `tests/test_exp016_reproduction.py:21`; 1 test, 1 failure, 241.864 seconds. Current Python 3.11.15/NumPy 2.4.3 differs from the original Python 3.13.16/NumPy 2.5.3. Thirty-three generated configuration values differ, with observed amplitude delta `3.4694469519536142e-17` and frequency delta `4.5474735088646412e-13 Hz`. Original float64 arrays are not committed, so sample-level max/RMS error is unavailable. No reference regeneration or acceptance waiver.
2. Integrity checker FAIL for immutable working-tree files because system `core.autocrlf=true` produces CRLF. All ten committed Git blobs match the recorded hashes, and in-memory LF normalization matches. Raw checkout hashes still fail. Documents were not modified. The owner explicitly authorized continuation with this failure unresolved.
3. Callback timing target NOT MET: p99.9 below 80% of callback budget was not achieved across all trials for any of the six rate/buffer pairs. There were 1,233 deadline overruns over the complete recorded run. This metric is reported separately from the enforced mean-load criterion by existing code (`plugin_track_a.py:327–329`). No target was changed and no outliers were discarded. Ordinary process priority and concurrent user applications were possible; scheduling interference is plausible but not established as the cause. No DSP modification is justified by these measurements. A controlled performance follow-up needs owner agreement before proceeding after this newly identified concern.
4. Combined ASan/UBSan proof is NOT RUN: the existing command uses GCC/Clang flags, not the prescribed MSVC toolchain. No equivalent sanitizer PASS is claimed. The optional complete Sprint 6 validation driver (VAL-019/020/021/022) has not been rerun as a separate full Windows matrix; Windows plugin reference agreement is proved only within VAL-026's recorded fixtures.
5. Owner UI/listening, G-10, DI-001 decision, distribution licensing and hardware fit remain unresolved. FL Studio 2025 `25.1.5.4976` is present but not scanned or reviewed. Installation and Sprint 8 are not authorized.

## Evidence

Local build/evidence root: `D:/SML Builds/SML-SP-3000/windows-sprint7-release`.
Logs: `approved-fix-configure.log`, `approved-fix-build.log`, `approved-fix-ctest.log`, `approved-fix-validation.log`. Corrected validation reports: `windows-validation-agent/`. Existing failure records and crash dumps are preserved. This report records a blocked validation attempt; no fully validated review artifact has been staged or installed.

## Callback performance detail

These are measured results for this machine and session, not a hardware-fit or DAW guarantee. The pair suffix is callback block size, not processing precision; each pair includes three trials each in float32 and float64.

| Rate / block | Highest mean load | Limit | Deadline overruns | p99.9 target |
|---|---:|---:|---:|---|
| 44100 / 64 | 13.2053% | 20% | 14 | NOT MET |
| 48000 / 64 | 18.4765% | 20% | 61 | NOT MET |
| 88200 / 128 | 14.9391% | 40% | 14 | NOT MET |
| 96000 / 128 | 33.9009% | 40% | 251 | NOT MET |
| 176400 / 256 | 23.1718% | 60% | 42 | NOT MET |
| 192000 / 256 | 53.2339% | 60% | 851 | NOT MET |

## Artifact inventory and installation handoff

Build root: `D:/SML Builds/SML-SP-3000/windows-sprint7-release`.

- VST3 bundle: `SMLSP3000_artefacts/Release/VST3/SML SP-3000.vst3`.
- Executable within bundle: `Contents/x86_64-win/SML SP-3000.vst3`, 6,938,624 bytes; SHA-256 `E0D0B731698ED7739346D5C00FC9C15532925B04257DF7D9B070385ACB5F04E6`.
- Standalone: `SMLSP3000_artefacts/Release/Standalone/SML SP-3000.exe`, 8,014,336 bytes; SHA-256 `3746D29C74B48FD449E69F98550AC36A74084245585733C4CAB0125336B32A02`.
- Module metadata: automatic VST3 manifest generation is disabled by the existing CMake configuration; no moduleinfo hash claimed.
- Review artifact: NOT CREATED, because validation gates remain open.
- FL Studio: `C:/Program Files/Image-Line/FL Studio 2025/FL64.exe`, version 25.1.5.4976. No scan or plugin database changes performed.
- Existing SML SP-3000 installation: none detected in the standard `C:/Program Files/Common Files/VST3` destination. Recheck immediately before any eventual authorized installation. If one appears, hash it and preserve the complete bundle in a timestamped backup before replacement.
- Future owner action after validation and installation approval: FL Studio Options > Manage plugins > Find installed plugins; confirm one SML SP-3000 stereo effect by Soundwave Machine Learning, then execute the checklist in docs/WINDOWS_HANDOFF.md. Do not scan/install now.

## Final status

Repository: `D:/SML Projects/SML-SP-3000`; remote: `https://github.com/soundwave-machine-learning/smlsp3000`; branch: `claude/autonomous-build`; HEAD: `38ff483ed6f75d080bfc5e06e32465e4804294ca`.
Working tree: DIRTY, limited to the approved harness/regression correction and its documentation. No commit, merge, push or main modification performed.
Configure: PASS. Windows Release build: PASS. CTest: PASS (3 tests, 130 named checks). Unit suite: FAIL (57/59 pass). Plugin VAL-023/025/026: PASS. Native reference agreement via VAL-026: PASS for its fixtures, not the complete separate Sprint 6 matrix. Goldens/references: FAIL (CHAIN-EXP-016). Raw checkout integrity: FAIL. pluginval: PASS. Full VAL-024: INCOMPLETE. Performance mean limits: PASS; p99.9 target: NOT MET.
Installation performed: NO. Owner UI/listening: NOT EXECUTED. DSP changed: NO. Ready for fully validated owner-review artifact: NO. Ready for installation: NO. Ready for Sprint 8: NO.

Exact blockers: CHAIN-EXP-016 reference reproduction; CRLF checkout integrity; callback p99.9 timing target unmet; incomplete Windows sanitizer proof. Owner UI/listening, G-10, DI-001, licensing/distribution and hardware-fit decisions remain unresolved.

## Experimental owner-test package authorization (2026-10-07)

The owner explicitly approved preparing an experimental owner-test copy while the recorded validation gates remain unresolved. This approval changes the staging restriction only; it does not convert any failing or pending check to PASS and does not authorize installation, distribution, DSP changes or Sprint 8.

Package: D:\SML Builds\SML-SP-3000\windows-sprint7-release\review\sprint7-experimental-20261007-164049
Complete VST3 bundle and Standalone copy verified against the built originals. SHA256SUMS.txt verified for all 38 packaged files. BUILD_INFO.txt, WINDOWS_VALIDATION.txt, OWNER_TEST_PLAN.txt, evidence, provenance patch and a read-only manifest verifier are included. Ready for experimental owner UI/listening exploration: YES, under this explicit approval. Fully validated: NO. Installed: NO. The additional full native matrix remains in progress at packaging; its result is not assumed. Avoid performance judgments while that job is active.

## Experimental DAW installation authorized and performed (2026-10-07)

The owner explicitly requested the VST3 working in their DAW and authorized necessary installation despite documentary staging restrictions. The complete experimental bundle was installed at C:/Program Files/Common Files/VST3/SML SP-3000.vst3. No previous SML SP-3000 bundle existed at that path; no replacement or backup was needed. Every installed file was compared with the staged bundle. Installed executable SHA-256 remains E0D0B731698ED7739346D5C00FC9C15532925B04257DF7D9B070385ACB5F04E6.

Installed-copy pluginval strictness 8: PASS, exit 0, 23.9848951 seconds. Logs: D:/SML Builds/SML-SP-3000/windows-sprint7-release/installed-pluginval. Installation record: WINDOWS_INSTALLATION.json in the build root.

FL Studio Plugin Manager v1.8.1.4976 was opened. Its scan has NOT been executed by the agent: Computer Use screenshot capture failed with SetIsBorderRequired failed: No such interface supported (0x80004002); accessibility inspection returned unlabeled panes. User next action: Find installed plugins, then choose SML SP-3000 in a mixer effect slot. No plugin database reset, cache deletion or DAW project modification was performed. DAW loading and listening remain unverified. Experimental testing is authorized; full validation and release acceptance remain unresolved. No DSP, reference or tolerance changes and no Sprint 8.

## FL Studio archive scan diagnosis (2026-10-07)

Owner screenshot showed SML SP-3000 status ok, VST3, 64-bit, Effect, followed by a stalled scan under D:/Audio/12_ARCHIVE/QUARANTINE/C_TEMP_2026-09-22/178AC34E-9DF9-4E53-BF59-1F307C598E3B. Inspection found Windows DISM servicing modules in that directory, including DismCore.dll and AppxProvider.dll; the screenshot did not expose the complete currently scanned filename. No archived executable was run or archive file changed.

Root configuration finding: HKCU/Software/Image-Line/Shared/Plugin search paths/List/16 had path D:/Audio/ and selected=1. The broad path includes archive and installer material. After closing Plugin Manager gracefully, that entry alone was disabled (selected=0), with its original values preserved in FL_AUDIO_SCAN_PATH_BEFORE.json in the Windows build root. Standard C:/Program Files/Common Files/VST3 scanning remains enabled; verification remains enabled. No database or caches were deleted. Genuine plugins stored elsewhere under D:/Audio will need their dedicated plugin directories added if future scans are needed; the broad archive-containing root should remain excluded.

SML did not appear in the checked user plugin database after cancellation. Cancellation preventing persistence is consistent with the observation but not proven. Next action: reopen Manage plugins from FL Studio and complete one verified scan with the broad archive path disabled; then confirm SML can load in an effect slot. DAW loading remains unverified.

Additional native matrix completed: VAL-021, VAL-019, VAL-020 and VAL-022 PASS using the original full checks. Evidence under windows-native-full-matrix in the build root. This does not waive CHAIN-EXP-016, raw-checkout integrity or the other recorded open gates.
