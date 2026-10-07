# SML SP-3000 — Windows build and test handoff (Sprint 7)

Revision: execution V7 (Sprint 7) · 2026-10-07

Purpose: everything needed to build, validate and review the Windows x86_64 VST3 and Standalone on the owner's machine. Nothing in this document was executed on Windows by the executor; the status table at the end says exactly what occurred.

## Source

* Repository: https://github.com/soundwave-machine-learning/smlsp3000, branch `claude/autonomous-build`.
* Source commit: `e333dc3a678a32ed52d382ed4fc8d4f03fd5206d` (Sprint 7 implementation/review checkpoint on `claude/autonomous-build`; see docs/sprint_reports/SPRINT_07_REPORT.md §17).
* Product identity (plugin/product_identity.json): display name "SML SP-3000", company "Soundwave Machine Learning", manufacturer code `SWML`, plugin code `Sp3K`, bundle id `com.soundwavemachinelearning.smlsp3000`, version 0.7.0, VST3 category Fx, stereo in/out. Never install over or next to an SPZERO / SML SP-06 build; the identities differ by design.

## Required components (owner's Windows machine)

1. Windows 10/11 x86_64.
2. Visual Studio 2022 with the "Desktop development with C++" workload (MSVC v143, Windows 10/11 SDK). Community edition is sufficient for personal use (its licence is the owner's to accept).
3. CMake ≥ 3.22 (the VS installer component or cmake.org) and optionally Ninja.
4. Git.
5. JUCE 8.0.9, exactly the pinned commit `f72bad64d29715216226685810c5196bd0d79d77` (plugin/JUCE_PIN.json): `git clone --depth 1 --branch 8.0.9 https://github.com/juce-framework/JUCE third_party\JUCE` from the repository root. The configure step refuses any other commit.
6. pluginval for Windows (Tracktion, GitHub release v1.0.4 `pluginval_Windows.zip`), unpacked anywhere; record its SHA-256.
7. Python ≥ 3.12 with numpy ≥ 2.0 only if the Python validation (`validate-sprint6/7`) is to be re-run on Windows (optional; the native ctest and pluginval do not need Python).

Licensing prerequisites (owner decision, not performed by the executor): the Linux build uses the JUCE AGPLv3 route and the Steinberg VST3 SDK GPLv3 option, suitable for private personal use without distribution. If the owner prefers the JUCE EULA (Personal/Indie/Pro) or the proprietary Steinberg VST3 licence, the owner must accept those terms personally before building; no purchase or acceptance was made.

## Clean Release configure / build (x64 Native Tools Command Prompt for VS 2022, repository root)

```
rmdir /s /q plugin\build
cmake -S plugin -B plugin\build -G "Visual Studio 17 2022" -A x64
cmake --build plugin\build --config Release --target SMLSP3000_VST3 SMLSP3000_Standalone smlsp3000_host_harness smlsp3000_editor_snapshot smlsp3000_selftest smlsp3000_adapter_test smlsp3000_native
```
No CXXFLAGS workaround is needed on Windows (that is a Linux-container-only measure). The native core keeps `/fp:precise` (no contraction, no fast-math) from native/CMakeLists.txt; JUCE adds no fast-math.

## Tests and pluginval

```
ctest --test-dir plugin\build\native -C Release --output-on-failure
plugin\build\native\Release\smlsp3000_native.exe info --rate 48000 --channels 2
pluginval.exe --strictness-level 8 --validate-in-process --verbose --output-dir evidence\sprint_07\pluginval_windows "plugin\build\SMLSP3000_artefacts\Release\VST3\SML SP-3000.vst3"
```
Optional (needs Python): `python -m smlsp3000.runner validate-sprint6 --out research\validation --evidence evidence\sprint_06` and `python -m smlsp3000.runner validate-sprint7 --evidence evidence\sprint_07_windows` (the Sprint 7 driver expects the Linux artefact layout; adjust the `PB`/`VST3` paths in smlsp3000/validation/plugin_track_a.py to the `Release` configuration directory on Windows before running).

## Expected artefact locations

* VST3 bundle: `plugin\build\SMLSP3000_artefacts\Release\VST3\SML SP-3000.vst3` (folder bundle; the DLL is `Contents\x86_64-win\SML SP-3000.vst3`).
* Standalone: `plugin\build\SMLSP3000_artefacts\Release\Standalone\SML SP-3000.exe`.
* Native tools: `plugin\build\native\Release\smlsp3000_native.exe`, `smlsp3000_selftest.exe`, `smlsp3000_adapter_test.exe`; harness/snapshot under their `*_artefacts\Release` folders.
* Installation (NOT performed, owner action): copy the `.vst3` folder bundle to `C:\Program Files\Common Files\VST3\` (or FL Studio's configured VST3 search path); never into an SPZERO folder.

## Local DAW review checklist (FL Studio, owner's installed version — record the exact version, OS build and CPU)

1. Rescan plugins; "SML SP-3000" appears once under Effects (Soundwave Machine Learning), stereo.
2. Insert on a stereo mixer track; reported latency compensated automatically (expect 310 samples at 48 kHz, 298 at 44.1 kHz; see the status strip).
3. Open/close the editor repeatedly; resize; keyboard navigation; tooltips.
4. Move each of the six controls; automate SP input level and interstage level (expect smooth 10 ms ramps, block-boundary application); switch SP/MPC gains (instant steps).
5. Toggle bypass from the editor and from the mixer slot (same behaviour: latency-aligned dry, 10 ms crossfade); rapid toggles.
6. Save the project, close FL Studio, reopen: all six values restored; INIT program recall.
7. Render (bounce) the project offline and compare with the real-time pass of the same material (expect identical audio for the same block schedule; small differences only from automation block boundaries).
8. Multiple instances on different tracks; different sample rates (44.1/48/96 kHz) in the audio settings.
9. Standalone: start, open audio settings, choose a device, enable input monitoring explicitly; confirm no feedback path exists until enabled.
10. Report problems with: FL Studio version, build, sample rate, buffer size, steps to reproduce.

## Status (only what actually occurred)

| Step | Status |
|---|---|
| Source prepared (CMake project, pinned JUCE, identity, tests, this procedure) | DONE (Linux, commit per report §17) |
| Windows build performed | NOT RUN |
| Windows artefact produced | NOT RUN |
| Plugin validated on Windows (pluginval / ctest) | NOT RUN |
| FL Studio session / automation / bounce checks | NOT RUN |
| Plugin installed on the owner's computer | NOT PERFORMED (owner action; not done by the executor) |
