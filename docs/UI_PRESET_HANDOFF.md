# SML SP-3000 — UI and preset engineering handoff

Date: 2026-10-07. Status: handoff only; UI redesign and preset implementation NOT STARTED. Owner reports the installed plugin now works in FL Studio. Preserve that working baseline.

## 1. Source and authority

Repository: `D:\SML Projects\SML-SP-3000`. Branch: `claude/autonomous-build`. HEAD: `38ff483ed6f75d080bfc5e06e32465e4804294ca`. The tree is intentionally dirty with approved harness/regression changes and documentation. Inspect status, diff and new regression source; do not reset, clean, stash or overwrite them. A fresh checkout at HEAD omits the approved correction. No new branch name or milestone commit is presumed.

Read AGENTS.md, README.md, docs/README.md, WINDOWS_TROUBLESHOOTING_REPORT.md, PROJECT_HANDOFF.md, ARCHITECTURE.md, PARAMETERS.md, USER_CONTROL_GUIDE.md, RATE_GAIN_PLAN.md, VALIDATION_PLAN.md, DECISIONS.md, CONFIDENCE.md, BUILD_COMMANDS.md, the Sprint 7 report/contract and actual source. Historical pending/no-install statements are superseded by the consolidated report; historical failures are not erased.

The user requested this handoff for future UI/preset work. This document does not itself begin implementation, Sprint 8, release, merging or publication. The next task should explicitly scope a UI/preset pass with frozen sound and preserved compatibility.

## 2. Preserve the working installation

Installed: `C:\Program Files\Common Files\VST3\SML SP-3000.vst3`.
Executable: `Contents\x86_64-win\SML SP-3000.vst3` within the bundle.
SHA-256: `E0D0B731698ED7739346D5C00FC9C15532925B04257DF7D9B070385ACB5F04E6`.
Build: `D:\SML Builds\SML-SP-3000\windows-sprint7-release`.
Experimental baseline: `review\sprint7-experimental-20261007-164049` under the build root.
JUCE: source `third_party\JUCE`, version 8.0.9, commit `f72bad64d29715216226685810c5196bd0d79d77`.

Do not overwrite the installed working binary during design. Build/stage a new candidate, then obtain a separate installation decision. The old executable hash identifies the rollback baseline; a UI-modified binary will normally have a different hash.

## 3. Compatibility identity

- Product: SML SP-3000; company: Soundwave Machine Learning.
- Manufacturer `SWML`; plugin code `Sp3K`; bundle ID `com.soundwavemachinelearning.smlsp3000`.
- Version currently 0.7.0. Do not silently change identity or version.
- Stereo in/out only, VST3 category Fx, not a synth, no MIDI input/output.
- Wrapper state root `SMLSP3000_STATE_V1`, schema version 1.
- Native header `smlsp3000-state`, schema 1; exact controls/product/SP/MPC identity-and-hash lines.
- Preset directory identity `SML SP-3000`; no custom preset bank exists yet.
- Preserve exact host parameter IDs, registration order, version hints, bounds/defaults, normalization, enum ordering, gesture behavior and old-session recall.

A label redesign does not authorize a host-ID change. A clean native diff alone is insufficient: identical input and settings must still produce identical audio after UI/preset work.

## 4. Existing controls and mappings

| Order | Host ID | Type / range | Default | Meaning |
|---|---|---|---|---|
| 0 | `sp_input_level_db` | Float -60 to +12 dB | 0 dB | SP input trim; 10 ms ramp |
| 1 | `sp_input_gain` | Choice indexes 0/1/2 | 0 | 0/+20/+40 dB; native field `sp_input_gain_db` is physical 0/20/40 |
| 2 | `interstage_level_db` | Float -60 to +24 dB | 0 dB | Single SP-to-MPC gain; 10 ms ramp |
| 3 | `mpc_input_gain` | Choice indexes 0/1/2 | 0 / LO | LO/MID/HI, relative gain 0/+20/+40 dB |
| 4 | `output_trim_db` | Float -60 to +12 dB | 0 dB | Final processed-output gain, 10 ms ramp; not a limiter or bypass-dry gain |
| 5 | `plugin_bypass` | Boolean | false | Latency-aligned original input; 10 ms linear crossfade; engine keeps running |

Continuous host ranges are linear in dB without additional interval quantization. Current value displays use two decimals. The host ID `sp_input_gain` is NOT the native state field `sp_input_gain_db`; a choice index is not a dB number. Native text stores MPC gain as LO/MID/HI, not a normalized float. Use existing parameter conversion functions.

The processor uses JUCE parameter objects and SliderParameterAttachment / ComboBoxParameterAttachment / ButtonParameterAttachment; it does not use APVTS. Do not introduce a state/parameter architecture rewrite merely to reskin controls.

Automation is delivered at the next block boundary; sample accuracy is not claimed. Discrete gain changes are steps, not continuously interpolated controls.

## 5. Implementation map

| Files | Responsibility |
|---|---|
| `plugin/src/PluginEditor.h/.cpp` | Primary UI scope: components, layout, attachments, tooltips, 24 Hz meter updates, INIT |
| `plugin/src/PluginProcessor.h/.cpp` | Parameters, stereo buses, latency, adapter bridge, wrapper state; preserve behavior |
| `plugin/src/ProductIdentity.h`, `plugin/product_identity.json` | Identity and truthful product claims |
| `native/include/smlsp3000/host_adapter.hpp` | MeterSnapshot, parameters, state handoff and bypass API |
| `native/src/host_adapter.cpp`, `native/src/engine.cpp` | Frozen adapter/DSP and native state semantics; not UI edit targets |
| `native/generated/track_a_assets_v1.hpp` | Generated authoritative bounds/defaults; never hand-edit |
| `plugin/tools/snapshot_main.cpp` | Actual editor screenshots |
| `plugin/tools/host_harness_main.cpp` | VST3 host validation |
| `plugin/tools/processor_test_main.cpp` | Approved uncommitted oversized regression; preserve |
| `smlsp3000/validation/plugin_track_a.py` | Plugin validation, including corrected host announcement |
| `smlsp3000/validation/production_track_a.py` | Native reference/rate/alias/state checks |

## 6. UI design requirements

Current sizes: default 920×540, minimum 760×440, maximum 1520×880; fixed 920:540 aspect ratio. Current signal hierarchy is SP INPUT → SP ENGINE → INTERSTAGE → MPC ENGINE → OUTPUT. No new visual brief, style reference or mockup is approved yet. Baseline screenshots document implementation, not a required aesthetic.

Five screenshots exist at `windows-validation-agent/safety_ui/screenshots` under the build root: default, before prepare, bypassed, minimum and maximum. Future screenshots must come from the actual built editor. Review DPI, keyboard focus, value readability, contrast, resizing, automation feedback, multiple instances and editor-before-prepare behavior.

Organize detailed engineering/provisional text into an About/Details area if the owner chooses; the main controls need not expose every implementation detail. Preserve accurate model limitations and avoid unsupported “hardware matched” or “exact emulation” claims.

Available telemetry: stereo input sample peaks/holds, MPC-core-input proxy-grid sample peaks, output sample peaks/holds, SP 12-bit clamps, MPC 18-bit clamps and 16-bit storage clamps, output over-range flags, non-finite input/fault counters, bypass weight, host rate/latency and prepared state. MPC input has current peak semantics, not the same historical hold as input/output. Reset-hold is distinct from engine reset.

Do not label these RMS, LUFS, true-peak, analog voltage or analog saturation meters. Do not invent live animation representing unmeasured signals. Poll existing atomic snapshots from the message thread with bounded repaint cost. No allocation, file I/O, locks or logging on the audio thread.

INIT restores all six host defaults using beginChangeGesture / setValueNotifyingHost / endChangeGesture; it does not reset engine history. Unsupported sample rates mute output and show a status; preserve that behavior. Latencies remain 298/310/426/449/682/728 samples at 44.1/48/88.2/96/176.4/192 kHz.

## 7. Presets: existing state and recommended scope

Only INIT exists. `getNumPrograms()` returns 1; current program is 0; program name is INIT; program switching is a no-op. There is no factory bank, preset browser, tags, custom save/load management or curated musical preset collection. Host session persistence exists and passed its recorded tests.

Recommended first implementation: a small explicit preset manifest using only the six product controls, with a UI selector applying values through existing JUCE parameters and host notification. This is a proposal for the next task, not an implemented feature. Do not change the host program count or native state schema without a compatibility decision. Actual control values must remain sufficient to recall sound from old sessions. Preset name/category metadata should not become a required DSP state field. Show Custom/Modified when controls or automation diverge from a preset.

Each preset should specify stable ID, display name, category, description, exact physical values, intended source/input level, expected gain and clamp behavior, author/revision, audition evidence and acceptance status. Keep physical values distinct from normalized host encodings. Preserve INIT exactly. Sound presets should normally use bypass=false; any bypass utility should be explicit.

Do not hide quantizer rules, oversampling, calibration, routing, reverse order, asset IDs or other research switches inside presets. No hidden auto-gain, normalization, limiter, saturation, wet/dry or new DSP. Reducing output trim does not undo upstream converter clipping. Large SP/MPC gain steps need intentional headroom and listening review; explain designed clamping honestly.

No preset count, names, numeric sound settings, file extension or final UI style is approved in this handoff. Audition owner-provided drum loops, mixes and other relevant material; disclose a single-source limitation. No “safe for all audio”, hardware-accurate or listening-approved labels without evidence. Measurement-based loudness matching may aid auditions but must not become hidden runtime gain compensation.

## 8. State and preset I/O compatibility

Wrapper persistence is JUCE binary XML: SMLSP3000_STATE_V1, schema_version=1, adapter/product-version attributes, and a native child containing validated text. Inputs over 1 MiB, wrong root/schema or rejected native payloads are left unapplied.

Native text requires all six controls and five identity/schema lines. It rejects unknown keys, non-finite values, invalid enums, out-of-range values and mismatched identities. It stores `sp_input_gain_db=0|20|40`, `mpc_input_gain=LO|MID|HI`, and `plugin_bypass=0|1`. Do not insert arbitrary preset metadata keys into this strict schema.

Use existing serializers/validation for full processor state. If a new external preset format is approved, validate its version, types and bounds before applying any controls. File dialogs/read/write stay off the audio thread. A cancelled, malformed or incompatible import must not partially apply a preset.

The current INIT loop performs six notified changes; it is not proof of an atomic multi-parameter transaction. Specify how preset recall interacts with live processing and automation without silently changing smoothing or state-handoff semantics.

## 9. Validation and delivery plan

1. Preserve installed rollback binary and local source diff. Capture initial parameter/state inventory and real UI screenshots.
2. Implement only the approved UI/preset scope; preserve identity, parameter contracts, old-session recall and sound.
3. Build all eight existing Windows targets with VS2022 x64 Release and pinned JUCE. Use exact commands in BUILD_COMMANDS.md and D: for build outputs.
4. Run CTest including the 72-check oversized regression, plugin integration/state/automation/bypass checks and strictness-8 pluginval on the new candidate. When implementing presets, add checks for bounds/enums, full recall, deterministic renders, malformed-load rejection and compatibility with old state.
5. Compare pre/post-change audio at identical settings and schedules. Preserve existing plugin/adapter/reference criteria; no golden regeneration or tolerance changes to bless a mismatch. Unit baseline is 57/59, not 59/59: distinguish known failures from new regressions.
6. Inspect actual screenshots across supported sizes/DPI, bypass, before prepare, fault/unsupported states, keyboard focus, host automation and multiple instances. A screenshot is not owner acceptance.
7. Deliver source/assets, diff, design note, exact preset manifest, audition findings, logs, before/after screenshots and staged hashes. Obtain a separate decision before replacing the installed working VST3.
8. Owner tests FL project save/reopen, automation, bypass, instances and offline bounce with rate, buffer, driver and source material recorded. Existing “plugin works” confirmation does not fill these formal cells automatically.

Do not re-enable the broad D:\Audio scan path: it recursively reaches archived Windows DLLs. Use genuine plugin directories and standard VST3 folders. No plugin database reset is needed.

Known open baseline: CHAIN-EXP-016 exact reproduction; CRLF integrity; p99.9 target with 1,233 recorded overruns; combined Windows sanitizer proof; owner UI/listening, G-10 and DI-001; licensing/distribution and hardware fit. Full native VAL-019/020/021/022 and plugin VAL-023/025/026 passed. Sprint 8 and release readiness are not authorized by this handoff.
