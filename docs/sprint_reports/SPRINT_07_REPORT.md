# Sprint 07 report — Plugin wrapper, host/UI integration and real-time hardening (Track A: JUCE VST3 + Standalone, Linux implementation/review checkpoint)

Contract: docs/sprint_prompts/SPRINT_07.md (planning V1, unchanged), entry gates amended by docs/EXECUTION_PLAN_V2.md (OWN-DEC-001). Owner inputs 2026-10-07 (G-09 target matrix, framework/licence route, identity, clock anchor, DSP preservation, adapter/bypass/parameter/state/UI/standalone/safety/validation/platform/handoff policies): OWN-DEC-024..038, recorded in evidence/sprint_07/owner_decisions_sprint7.json before any wrapper code. Engineering decisions ENG-DEC-025..028. Executor: autonomous.

**Verdict class: IMPLEMENTATION / REVIEW CHECKPOINT, not a PASS.** This report separates (A) IMPLEMENTATION (what exists), (B) AUTOMATED VALIDATION ON LINUX (executed, all PASS), (C) WINDOWS NATIVE VALIDATION (NOT RUN — the required deployment target; no Windows toolchain or machine exists in this container), (D) DAW VALIDATION (FL Studio NOT RUN), (E) OWNER UI / LISTENING ACCEPTANCE (G-10 NOT EXECUTED) and (F) HARDWARE FIT (BLOCKED). Nothing here is measured, calibrated or validated against hardware; every rendered value remains UNVALIDATED AGAINST HARDWARE. Nothing was installed on the owner's computer and nothing was published.

## 1–2. Starting state

Starting commit `4b8d24e15a07d8aea78b65310a1f4cc927d14f78` (Sprint 6 milestone `1a3ecaf` + its checkpoint). Branch `claude/autonomous-build`, tree clean, no intervening commits, `origin/main` untouched at `3b53a6b`. Sprint 1 PASS, Sprint 2 BLOCKED, Sprints 3–6 PASS WITH EXTERNAL VALIDATION PENDING, G-04/G-07H BLOCKED — all preserved. Inherited regression before any Sprint 7 change (evidence/sprint_07/inherited_regression_run.log): integrity 5/5, native build + ctest OK, 59 unit tests OK, Sprint 6 quick validation PASS ×4, Sprint 3/4/5 re-runs numerically identical to the committed records (two SP records differ only by the Sprint 6 instrumentation meter key that the committed goldens predate; no audio difference).

## 3. Scope mapping

| Contract permission / owner input | Repository path |
|---|---|
| Host adapter (framework-independent) | native/include/smlsp3000/host_adapter.hpp, native/src/host_adapter.cpp (smlsp3000-host-adapter-1.0.0); native/tests/adapter_test.cpp (ctest `host_adapter_test`) |
| Non-sonic core API | native/include/smlsp3000/engine.hpp, native/src/engine.cpp: `serialize_state_with_bypass`, `update_product_targets` (no audio-path change); native/CMakeLists.txt (PIC, adapter sources, test target) |
| Plugin wrapper (JUCE 8.0.9 pinned) | plugin/CMakeLists.txt, plugin/JUCE_PIN.json, plugin/product_identity.json, plugin/src/{ProductIdentity.h, PluginProcessor.h/.cpp, PluginEditor.h/.cpp} |
| Development tools (not product) | plugin/tools/host_harness_main.cpp (JUCE VST3 host harness), plugin/tools/snapshot_main.cpp (editor screenshots under Xvfb) |
| Validation | smlsp3000/validation/plugin_track_a.py (VAL-023..026, pluginval) → evidence/sprint_07/{host_matrix, latency_bypass, realtime_state, safety_ui, pluginval}/; runner `validate-sprint7` |
| Documentation | docs/USER_CONTROL_GUIDE.md, docs/WINDOWS_HANDOFF.md, docs/design_issues/DI-001_clock_anchor.md, updated living docs (§12) |
| Dependencies (git-ignored, local only) | third_party/JUCE (depth-1 clone of tag 8.0.9, commit verified at configure), tools_external/pluginval (1.0.4 Linux release, zip sha256 recorded) |

## 4. Implementation (A)

- **Host adapter** (ENG-DEC-025/026/027; OWN-DEC-029/030/031/032/035): stereo float32 or float64 planar host buffers, any block size (zero, odd, oversized > prepared maximum with internal chunking), six rates; float32 promoted to float64 into preallocated buffers, core unchanged, final cast; parameter targets are atomics turned into native events at offset 0 of the next block (BLOCK-BOUNDARY delivery, no wrapper smoothing — the core's own 10 ms linear-in-dB ramps and discrete switches apply); state is parsed/validated off the audio thread and published through a lock-free slot; NaN/Inf host samples are replaced by 0 (counted) before BOTH the core and the dry path; `plugin_bypass` selects the latency-aligned ORIGINAL input (before every product gain and both machines, no output trim) with a 10 ms linear crossfade of complementary weights while the core and dry delay keep running (rapid toggles continue from the current weight; startup/reset in bypass snap to fully dry); atomic meters (host input peak, SP/MPC core-input proxy peaks, converter clamp counters, output peak, over-range flag, non-finite count, faults, bypass weight). No allocation, lock or I/O in `process()` (global operator new/delete counter in the ctest: 0 allocations for float32 and float64 paths).
- **JUCE processor** (`SMLProcessor`): six `AudioProcessorParameter`s with the frozen identifiers (sp_input_level_db −60…+12 dB, sp_input_gain {0, +20, +40}, interstage_level_db −60…+24 dB, mpc_input_gain LO/MID/HI, output_trim_db −60…+12 dB, plugin_bypass), normalized mapping linear in dB / ordered enums / bool; `getBypassParameter()` returns plugin_bypass so host bypass and editor bypass are ONE mechanism; `prepareToPlay` re-prepares the adapter only when rate or maximum block changes, otherwise resets (stream start, ENG-DEC-027); reported latency = native latency; float and double `processBlock`; state XML root `SMLSP3000_STATE_V1` wrapping the native schema-v1 text (rejects wrong root, schema ≠ 1, > 1 MiB, and everything the native parser rejects: research keys, out-of-range, identity mismatch, truncation, garbage); no `ScopedNoDenormals` (floating-point policy unchanged).
- **Editor** (`SMLEditor`, prototype for G-10): signal path line, five sections, six controls with units and tooltips, Reset to INIT, honest meters (sample peak per block with hold; "unavailable" before preparation; amber over-range indication for finite output > ±1.0 without clamping; converter clamp counters labelled as modelled code clamps, analog clipping labelled not modelled), status/latency/fault/model strip, resizable 760×440 … 1520×880 (default 920×540), 24 Hz timer, no fake animation, no copied panels.
- **Standalone**: same processor; Linux build has no audio backend (no ALSA headers in the container); JUCE's standalone mutes input by default — no automatic live monitoring (OWN-DEC-034).
- **Product identity** (OWN-DEC-026): "SML SP-3000", manufacturer "Soundwave Machine Learning", codes SWML / Sp3K, bundle id com.soundwavemachinelearning.smlsp3000, version 0.7.0, state root SMLSP3000_STATE_V1; nothing reused from SPZERO / SML SP-06.
- **Clock anchor**: UNCHANGED (OWN-DEC-027); tracked as docs/design_issues/DI-001_clock_anchor.md.
- **Not implemented / not done**: Windows build, FL Studio or any DAW session, installation, release, presets bank, Sprint 8, any DSP addition (no saturation/noise/EQ/jitter/normalization/limiter/wet-dry/drive/new routes).

## 5. Commands (repository root; Python 3.13.16, numpy 2.5.3, GCC 13.3.0, CMake 3.28.3, Ninja, Xvfb; exit codes in evidence/sprint_07/commands.json)

| ID | Command | Exit | Log |
|---|---|---|---|
| CMD-02 | `python3 tools/check_repo_integrity.py` | 0 | evidence/sprint_07/integrity_run.log |
| CMD-13/14/05/15 | inherited regression before any change (native build + ctest, unit suite, validate-sprint6 --quick, sprint 3/4/5 re-runs) | 0 | evidence/sprint_07/inherited_regression_run.log |
| JUCE pin | `git clone --depth 1 --branch 8.0.9 https://github.com/juce-framework/JUCE third_party/JUCE` (commit f72bad64d29715216226685810c5196bd0d79d77 verified by plugin/CMakeLists.txt) | 0 | plugin/JUCE_PIN.json |
| pluginval | `curl -sSL -o tools_external/pluginval/pluginval_Linux.zip https://github.com/Tracktion/pluginval/releases/download/v1.0.4/pluginval_Linux.zip` (zip sha256 c01c49d8…b55352; `pluginval --version` = 1.0.4) | 0 | evidence/sprint_07/pluginval/pluginval_record.json |
| CMD-18 | `CXXFLAGS="-DJUCE_USE_XRANDR=0 -DJUCE_USE_XINERAMA=0 -DJUCE_USE_XCURSOR=0 -DJUCE_USE_CURL=0 -DJUCE_WEB_BROWSER=0 -DJUCE_ALSA=0 -DJUCE_JACK=0" cmake -S plugin -B plugin/build -G Ninja -DCMAKE_BUILD_TYPE=Release && cmake --build plugin/build` | 0 | evidence/sprint_07/plugin_configure.log, plugin_build.log, build_record.json |
| CMD-14 | `ctest` in native/build (native_selftest 31 cases + host_adapter_test) | 0 | evidence/sprint_07/native_ctest.log |
| CMD-19 | `python3 -m smlsp3000.runner validate-sprint7 --evidence evidence/sprint_07` (+ `--only VAL-023` and `--only VAL-025` re-runs after check-design corrections and the screenshot-tool defect, §11) | 0 | evidence/sprint_07/validate_sprint7_run.log, validate_sprint7_val023_rerun.log, validate_sprint7_val025_rerun.log |
| CMD-20 | `xvfb-run -a -s "-screen 0 1600x1000x24" tools_external/pluginval/pluginval --strictness-level 8 --validate-in-process --verbose --output-dir evidence/sprint_07/pluginval "plugin/build/SMLSP3000_artefacts/Release/VST3/SML SP-3000.vst3"` (inside CMD-19) | 0 | evidence/sprint_07/pluginval/pluginval_stdout.log, pluginval_record.json |
| CMD-09 | `python3 -m smlsp3000.runner scope-audit --out evidence/sprint_07/scope_audit.json` | 0 | evidence/sprint_07/scope_audit_run.log |
| CMD-05 | `python3 -m unittest discover -s tests -t . -v` | 0 | evidence/sprint_07/unittest_run.log |

## 6. Automated validation on Linux (B) — all executed, all PASS

Frozen before evaluation: identity (plugin/product_identity.json), the G-08 limits inherited unchanged (RMS ≤ max(1e-5·RMS(in), 1e-7), peak ≤ 1e-4 before trim, per fixture, never averaged), the float32 oracle (reference fed the same float32-cast input, compared after the same final cast), the JUCE normalized-mapping replica used to compute the host-delivered values.

| Check | Software (Track A, Linux) | Windows / DAW | Owner G-10 | Evidence |
|---|---|---|---|---|
| VAL-026 / REQ-026 plugin–offline equivalence, platform compatibility | PASS: at six rates the complete VST3 (JUCE host harness) equals the adapter bit-for-bit in float64 and float32; float64 plugin vs the Python reference within the G-08 limits (worst RMS 7.7e-11 of its limit; worst peak 8.3e-16); float32 plugin vs the same-input/same-cast oracle identical to 1 ulp (worst RMS 6.4e-14 of its limit; interface rounding ≈ 2.2e-9 RMS, reported separately, not an engine error); offline (one call) vs real-time partitions identical; automation delivered BLOCK-BOUNDARY (delivered schedule recorded; plugin == adapter for the delivered schedule, differs from the static render as it must); state round trip exact (same hash, same render from a fresh instance); seven mutations (garbage, truncation, oversize, future schema, identity mismatch, research key, out of range) rejected with parameters unchanged; restore during processing applied at a block boundary == adapter events; 4 instances identical; re-prepare and 5× editor open/close OK | NOT RUN | — | evidence/sprint_07/host_matrix/VAL-026_software.json |
| VAL-023 / REQ-023 latency and bypass | PASS: reported plugin latency = native = reference at six rates (table below) and confirmed by impulse alignment through the bypass path; dry endpoint = latency-aligned input with exact amplitude (no trim, no gain); processed endpoint = un-bypassed render; crossfade linear over 10 ms with complementary weights; rapid toggles bounded and continuing from the current weight; startup in bypass fully dry; reset in bypass; host `processBlockBypassed` produces the same output as a plugin_bypass parameter event at frame 0 (one mechanism); float32 and float64; plugin toggles == adapter toggles bit-for-bit | NOT RUN | — | evidence/sprint_07/latency_bypass/VAL-023_software.json |
| VAL-024 / REQ-024 real-time, state and numerical safety | PASS: ctest 2/2 (allocation counter 0 in process()); ASan/UBSan build (native/build-asan, `-fsanitize=address,undefined -O1`) ctest 2/2 with no sanitizer report; NaN/Inf/over-range/denormal/silence inputs finite, plugin == adapter; rapid automation (47 events) finite and identical; complete-plugin timing within the OWN-DEC-017 mean-load limits at all six pairs with the p99.9 < 80 % target met, 0 overruns, all 36 trials retained (§7) | NOT RUN (Windows timing pending) | — | evidence/sprint_07/realtime_state/VAL-024_software.json, bench_raw/ |
| VAL-025 / REQ-025 headroom and honest UI | PASS (software part): converter clamps counted on the over-range fixture while the plugin output exceeds ±1.0 unclamped (no limiter); inter-sample-peak stimulus at +3 dB trim flags over-range on the sample-peak meter (no true-peak claim); exposed parameters = exactly the six product controls; state contains no research/calibration fields; standalone launches headless for a bounded 8 s without crash; five screenshots written under Xvfb; owner review checklist written | NOT RUN | NOT EXECUTED | evidence/sprint_07/safety_ui/VAL-025_software.json, screenshots/, owner_review_checklist.md |
| pluginval | PASS: pluginval 1.0.4 (Linux release, binary sha256 d3d342ea…), strictness 8, in-process, 25 test groups, exit 0, 17 s — a generic host-conformance tool, not a DAW check and not owner review | — | — | evidence/sprint_07/pluginval/ |
| VAL-018 scope audit | PASS (reference, native and plugin/validation sources) | — | — | evidence/sprint_07/scope_audit.json |
| Inherited | integrity PASS; 59 unit tests OK; Sprint 3/4/5/6 records numerically identical | — | — | regression / unittest logs |

Latency and agreement per host rate (VAL-023 / VAL-026; latency unchanged from Sprint 6 and ≤ 10 ms):

| Host rate | Reported plugin latency (= native = reference) | ms | Impulse index via bypass | Host bypass == parameter bypass | Plugin f64 vs reference: worst RMS / limit | worst peak error | Plugin f32 vs float32 oracle: worst RMS / limit | Float32 interface rounding (RMS) |
|---|---|---|---|---|---|---|---|---|
| 44100 | 298 | 6.76 | 298 | yes | 1.8e-11 | 1.7e-16 | 0.0e+00 | 2.2e-09 |
| 48000 | 310 | 6.46 | 310 | yes | 7.3e-11 | 7.8e-16 | 0.0e+00 | 2.2e-09 |
| 88200 | 426 | 4.83 | 426 | yes | 7.7e-11 | 5.0e-16 | 6.4e-14 | 2.2e-09 |
| 96000 | 449 | 4.68 | 449 | yes | 7.5e-11 | 8.3e-16 | 0.0e+00 | 2.2e-09 |
| 176400 | 682 | 3.87 | 682 | yes | 4.5e-11 | 3.3e-16 | 3.5e-16 | 2.2e-09 |
| 192000 | 728 | 3.79 | 728 | yes | 7.4e-11 | 7.2e-16 | 0.0e+00 | 2.2e-09 |

Automation delivery (OWN-DEC-031): host parameter changes are applied by JUCE before `processBlock`; the VST3 wrapper hands no sample offsets to the processor, so a change requested at host sample n takes effect at the first sample of the block that starts at or after n (requested 3000 → delivered 3072 at block 512, etc., recorded in the VAL-026 record). Sample-accurate automation is NOT claimed. The core's 10 ms ramps then run from the delivered sample.

## 7. Complete-plugin timing (OWN-DEC-017/035; VST3 through the JUCE harness incl. wrapper, float conversion where precision = 32, bypass toggles every 40 blocks, metering; 3 trials × ~5 s per precision; all trials retained in bench_raw/)

Machine: Intel(R) Xeon(R) Processor @ 2.10GHz, 4 vCPU shared cloud VM (Ubuntu 24.04, Linux 6.18.44), single thread, ordinary priority, no real-time scheduling, no CPU pinning; GCC 13.3.0, core `-O2 -ffp-contract=off -fno-fast-math -fexcess-precision=standard`, wrapper -O3 (JUCE recommended flags, no fast-math, no LTO). Applies only to this environment; Windows performance is pending until measured on Windows.

| Rate | Block | Limit (mean) | Mean load float32 (3 trials) | Mean load float64 (3 trials) | max p99.9 / budget | Max callback (ms) | Budget (ms) | Overruns |
|---|---|---|---|---|---|---|---|---|
| 44100 | 64 | 20 % | 7.3 / 6.9 / 7.1 % | 7.9 / 7.2 / 7.0 % | 0.23 | 0.54 | 1.45 | 0 |
| 48000 | 64 | 20 % | 10.8 / 9.8 / 10.6 % | 10.6 / 10.7 / 11.0 % | 0.28 | 0.95 | 1.33 | 0 |
| 88200 | 128 | 40 % | 12.2 / 14.0 / 11.3 % | 10.7 / 10.9 / 11.0 % | 0.25 | 0.50 | 1.45 | 0 |
| 96000 | 128 | 40 % | 14.8 / 13.9 / 13.9 % | 13.7 / 14.0 / 14.4 % | 0.39 | 0.92 | 1.33 | 0 |
| 176400 | 256 | 60 % | 16.8 / 16.2 / 16.9 % | 15.7 / 15.3 / 15.8 % | 0.32 | 0.83 | 1.45 | 0 |
| 192000 | 256 | 60 % | 20.0 / 21.4 / 21.5 % | 21.4 / 21.1 / 22.2 % | 0.41 | 0.66 | 1.33 | 0 |

All six pairs meet the owner mean-load limits with margin in every trial; the p99.9 < 80 % target is met in every trial (worst 0.41 at 192 kHz / 256); no overruns occurred. Callback maxima of several times the median (e.g. 0.95 ms at 48 kHz / 64) are shared-VM preemption and are reported as observed.

## 8. Windows native validation (C) — NOT RUN

The required deployment target is Windows x86_64 (OWN-DEC-024). No Windows toolchain, SDK, machine or cross-compiler exists in this container, so no Windows build was performed, no Windows artefact was produced, nothing was validated on Windows and nothing was installed. The exact owner procedure is docs/WINDOWS_HANDOFF.md (components, clean configure/build commands, ctest/pluginval, artefact locations, identity, DAW checklist, and a status table distinguishing source prepared / build performed / artefact produced / validated / installed — only the first row is DONE). The MSVC options in native/CMakeLists.txt (`/fp:precise`) are untested. No Windows screenshot or Windows validation is claimed; no Linux path is claimed to be on the owner's desktop.

## 9. DAW validation (D) — NOT RUN

FL Studio (primary; owner's installed version not recorded) and Cubase/Nuendo (advisory) were not run. pluginval strictness 8 on Linux is a generic host-conformance check and does not substitute for FL Studio session, automation, bypass, latency-compensation or bounce checks (docs/WINDOWS_HANDOFF.md §"Local DAW review checklist").

## 10. Owner UI / listening acceptance (E) — NOT EXECUTED

G-10 remains NOT EXECUTED. The UI is a prototype; the owner's review uses evidence/sprint_07/safety_ui/screenshots/ (Linux build under Xvfb: editor_before_prepare / default / min / max / bypassed) and evidence/sprint_07/safety_ui/owner_review_checklist.md. No preference, listening score or counts exist. Human listening (CHAIN-EXP-018) NOT EXECUTED.

## 11. Hardware fit (F) — BLOCKED

G-04 / G-06 / G-07H unchanged. The plugin reproduces the accepted software reference; the reference is unvalidated against hardware; therefore the plugin is too. No hardware accuracy, "emulation" or measured behaviour is claimed anywhere in the product text (the editor says so).

## 12. Artifacts

Sources listed in §3; evidence/sprint_07/* (records with manifests, 36 raw timing files ≈ 0.4 MB, five PNG screenshots, pluginval log, build/configure logs, decision and command records, provenance.json with hashes). No audio committed; scratch renders under /tmp are not kept; third_party/ and tools_external/ are git-ignored (dependency identities and hashes recorded instead).

## 13. Assumptions and licensing status

- JUCE is used under the GNU AGPLv3 open-source option for this unpublished personal-use build; the bundled Steinberg VST3 SDK under its GPLv3 option. No JUCE licence was purchased, no JUCE 8 EULA or Steinberg proprietary licence was accepted on the owner's behalf, the repository was not published or relicensed. If the owner ever distributes a binary, the AGPLv3 obligations (licence text, corresponding source, JUCE and Steinberg notices, "VST is a trademark of Steinberg Media Technologies GmbH") or a different licence route decided by the owner apply — an unresolved owner action, not an executor decision.
- "Any block size" is implemented as internal chunking against the prepared maximum, including zero-length and oversized calls; hosts that call with blocks larger than `prepareToPlay` promised are tolerated, not endorsed.
- Mean load as defined by the owner is the limit; p99.9 is a target reported with scheduling conditions.

## 14. Deviations and defects found during execution

- Contract items needing Windows, a DAW, the owner or hardware are NOT RUN / NOT EXECUTED / BLOCKED (§8–§11); this is why the sprint is a checkpoint, not a PASS.
- Adapter design corrections before the final records: NaN/Inf sanitisation moved before the dry path (a raw NaN reached the crossfade sum), reset after a parameter change synchronised through `update_product_targets` (ramps started from stale values); both are in the final code and tests, no limit was loosened.
- Check-design corrections (recorded in the re-run logs): bypass toggle frames placed on block boundaries for the plugin/adapter comparison; host-bypass comparison defined against a parameter-bypass event at frame 0 (JUCE's `processBlockBypassed` sets the bypass parameter, so a bypass-at-prepare render differs only by the initial 10 ms crossfade); VAL-025 indicator check performed on the render rather than the last-block meter value; standalone smoke bounded to 8 s.
- Screenshot-tool defect (development tool, not product): `juce::FileOutputStream` appends to an existing file, so repeated VAL-025 runs into the same evidence directory produced PNG files containing several concatenated images whose first (stale) image was displayed, giving the false appearance of a text-encoding problem in the path label. The tool now deletes the target before writing (plugin/tools/snapshot_main.cpp); the stale files were removed and VAL-025 re-run; each committed PNG contains exactly one image rendered by the current binary (ASCII "->" path label). No product code or validation limit changed.
- Editor text uses ASCII arrows in the path label after the Xvfb/Liberation Sans rendering of "→" was inspected; the committed screenshots show the current text.

## 15. Documentation updated

docs/README (rows for this report, USER_CONTROL_GUIDE, WINDOWS_HANDOFF, DI-001), PROJECT_HANDOFF (V7), ARCHITECTURE, PARAMETERS, CONFIDENCE, DECISIONS (OWN-DEC-024..038, ENG-DEC-025..028), GATE_REGISTER (G-09 matrix set / Linux done / Windows NOT RUN; G-10 NOT EXECUTED), VALIDATION_PLAN, ACCEPTANCE_MATRIX.md/.csv (rows 023..026 LINUX SOFTWARE PASS, Windows/DAW NOT RUN, G-10 NOT EXECUTED), BUILD_COMMANDS (V7, CMD-18..20), SPRINT_PLAN (Sprint 7 CHECKPOINT), DSP_CHANGELOG (Sprint 7 wrapper transitions only), new docs/USER_CONTROL_GUIDE.md, docs/WINDOWS_HANDOFF.md, docs/design_issues/DI-001_clock_anchor.md, this report. Immutable research and the eight contracts untouched (integrity PASS). Previous sprint reports untouched.

## 16. Confidence / status / acceptance changes and continuation gate

No claim status changed; no golden, tolerance or discrete semantic was loosened; the native core's audio behaviour is unchanged (VAL-026 plugin == adapter == core bit-for-bit; VAL-021 limits still met). Acceptance: REQ-023..026 software cells LINUX PASS; Windows/DAW NOT RUN; G-10 NOT EXECUTED; hardware-fit cells BLOCKED.

Sprint verdict: **IMPLEMENTATION / REVIEW CHECKPOINT — BLOCKED on mandatory gates** (Linux implementation and automated validation PASS; Windows native validation NOT RUN; FL Studio NOT RUN; owner G-10 UI/listening NOT EXECUTED; hardware fit BLOCKED). Ready for owner review: YES. Ready for Sprint 8: NO — Sprint 8 requires the Windows build/validation outcome, the FL Studio review, the owner's G-10 decision on the UI prototype, the owner's licensing route for any distribution, and the owner's decision on DI-001. STOP before Sprint 8. Nothing installed, nothing published, main untouched.

## 17. Ending commit

Implementation/review checkpoint commit: `<back-filled by the follow-up commit>` on `claude/autonomous-build` (this report does not claim its own hash).
