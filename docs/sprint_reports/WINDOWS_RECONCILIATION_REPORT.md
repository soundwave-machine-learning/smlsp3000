# Windows reconciliation report — stabilization commit, Preset Lab merge and Windows validation

Date: 2026-10-07 (local Windows time). Repository: `D:\SML Projects\SML-SP-3000`. Machine: Windows 10 Pro 10.0.19045 x64, Visual Studio 17 2022 (MSVC 19.44), CMake 4.4.0, pinned JUCE 8.0.9 (`f72bad64`), Python 3.11, pluginval 1.0.4. Build directory: `D:\SML Builds\SML-SP-3000\windows-sprint7-release` (CMD-W01 configuration, Release x64).

This is non-sonic engineering reconciliation. It is not owner listening acceptance, not a factory preset decision, not a UI pass and not Sprint 8.

## Commits

| Step | Branch | Commit |
|---|---|---|
| Historical base | `claude/autonomous-build` | `38ff483ed6f75d080bfc5e06e32465e4804294ca` |
| Windows stabilization (pushed to origin) | `claude/autonomous-build` | `768d57aca1da270133a75f9bb60b2aefac849c5e` |
| Manual + Preset Lab HEAD before merge | `claude/manual-preset-lab` | `f574615` (contains `9969cc0`, `a02785b`, `7aa93c8`) |
| Merge of the stabilized branch (local) | `claude/manual-preset-lab` | `e5276d79bcf52cd1236708a1da476225609bcfb0` |
| Windows Preset Lab validation + this report | `claude/manual-preset-lab` | recorded in docs/PROJECT_HANDOFF.md |

Worktree audit before the stabilization commit (`git status`, `git diff`, `git diff --cached`, `git ls-files --others --exclude-standard`, and the read-only classifier `tools/audit_worktree.py` taken from the remote branch): 10 dirty paths, classes VALIDATION (plugin/CMakeLists.txt, smlsp3000/validation/plugin_track_a.py, plugin/tools/processor_test_main.cpp) and DOCS-EVIDENCE (seven documents); 0 FROZEN-DSP / IMMUTABLE paths. `git diff 38ff483 -- native plugin/src smlsp3000/reference docs/research docs/sprint_prompts plugin/product_identity.json plugin/JUCE_PIN.json docs/ACCEPTANCE_MATRIX.*` is empty on the merged tree.

Merge conflicts and resolution: `plugin/CMakeLists.txt` (both the `smlsp3000_processor_test` / `processor_oversized_test` block and `add_subdirectory(tools/preset_lab)` kept), `docs/BUILD_COMMANDS.md` (one combined revision line), `docs/PROJECT_HANDOFF.md` (Preset Lab resume paragraph followed by the Windows sections). No conflict touched DSP, native state, parameter semantics or reference outputs.

One Windows build repair on the merged branch: `plugin/tools/preset_lab/lab_test_main.cpp` used `M_PI`, which MSVC does not define; replaced by `juce::MathConstants<double>::pi` (same double value) in the self-test synthetic stimulus only. No product source changed.

## Results — stabilization commit (before commit, Windows build of 38ff483 + approved corrections)

| Check | Result | Log (build directory) |
|---|---|---|
| CTest: processor_oversized_test (72 checks), native_selftest, host_adapter_test | 3/3 PASS | reconcile-ctest.log |
| VAL-026 host matrix (host announces 9000, irregular schedule unchanged) | PASS, 188 s | reconcile-validation.log, windows-validation-agent/host_matrix |
| VAL-023 latency/bypass | PASS | reconcile-validation.log |
| VAL-025 safety/UI | PASS | reconcile-ui-safety.log |
| pluginval strictness 8, in-process | PASS, exit 0, 23 s | reconcile-pluginval/ |
| Unit suite (59 tests) | 57 pass, 2 retained baseline failures (CHAIN-EXP-016 reproduction, CRLF repo integrity) | reconcile-unittest.log |

## Results — reconciled branch (merge e5276d7 + lab_test_main.cpp repair)

| Check | Result | Log |
|---|---|---|
| Configure + build Release x64: SMLSP3000_VST3, SMLSP3000_Standalone, smlsp3000_processor_test, smlsp3000_preset_lab, smlsp3000_preset_lab_test, host harness, editor snapshot, selftest, adapter test, native | PASS | reconcile-configure.log, reconcile-build-3.log |
| Product VST3 executable SHA-256 after rebuild | `E0D0B731698ED7739346D5C00FC9C15532925B04257DF7D9B070385ACB5F04E6` (unchanged; equals the installed rollback baseline) | — |
| CTest: processor_oversized_test, native_selftest, host_adapter_test, preset_lab_test (46 checks) | 4/4 PASS | reconcile-ctest-2.log |
| tests/test_preset_lab.py via run_windows_preset_lab_tests.py (paths only): demo candidates validate, INIT state = core defaults, malformed/future/unknown rejected, round trip + bounds, deterministic render, lab render == native HostAdapter render bit-for-bit (driven candidate and INIT), metadata independence, record fields | 7/7 PASS | reconcile-preset-lab-unittest.log |
| VAL-026 / VAL-023 re-run | PASS / PASS | reconcile-validation-2.log |
| pluginval strictness 8 re-run | PASS, exit 0, 24 s | reconcile-pluginval-2/ |
| VAL-018 scope audit | PASS | reconcile-scope-audit.json |
| Eight character-audit candidates `--validate` | all OK, acceptance_status DRAFT | — |
| Preset Lab GUI `--snapshot` on Windows (loads demo_beat_48000.wav, renders INIT + eight candidates through the live processor, metadata/save view) | exit 0, 10 PNG 1280×820; audio device detected: "Output 1/2 (SSL 2 USB Audio Device)" | reconcile-preset-lab-gui/ |

Preset Lab test mapping to the requested criteria: candidate load/save, round trip, INIT equivalence, bounds, enum validation, malformed manifest rejection, future schema rejection, no partial application on invalid load, deterministic render, metadata has no DSP effect — all in `preset_lab_test` (ctest) PASS; Preset Lab render == validated product/core processing for identical settings — `test_render_deterministic_and_equals_native_adapter_path` and `test_metadata_does_not_alter_output_and_init_render_matches_native` PASS (bit-for-bit against the native host-adapter path on this build).

Interactive device test (play, stop, loop, processed/bypass A/B through the SSL 2 output) was NOT executed by the agent: desktop control is not available in this session. The headless GUI mode exercised window creation, file load, live-processor rendering and telemetry. The owner performs the interactive check as the first step of the audition.

## Observations (not defects)

- Windows render records for the eight character-audit points show identical clamp counts, peaks, RMS, latency and effective host-mapped values to the committed Linux records; only `output_f64_sha256` differs (MSVC vs GCC build of the same source; last-ulp platform differences are already recorded in docs/WINDOWS_TROUBLESHOOTING_REPORT.md). Cross-platform bit identity is not claimed anywhere; on-platform equivalence is what the tests prove. Windows records are kept in the build directory, not in the repository.
- Regenerating the demo source on Windows gives a byte-identical WAV (`be35b5b4…`) but a different pre-quantisation `samples_sha256`; the committed record was left unchanged.
- The demo beat is a synthetic stimulus. Telemetry on it is preparation only; the owner re-observes on real material.

## Known baseline failures (unchanged, still open)

CHAIN-EXP-016 exact reproduction; CRLF checkout integrity (core.autocrlf=true working copy); p99.9 callback timing target; combined Windows sanitizer proof; owner UI/listening acceptance; G-10; DI-001; licensing/distribution; hardware fit.

## State after this task

Installed `C:\Program Files\Common Files\VST3\SML SP-3000.vst3` not touched (hash verified before and after). No factory presets, no production UI change, no DSP change, no Sprint 8. Next product gate: owner character audition in the Preset Lab on real finished beats (A: enough character when driven; B: separate DSP-character review).
