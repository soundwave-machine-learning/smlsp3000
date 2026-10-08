# SML SP-3000 Preset Lab — development authoring tool

Revision: V1 · 2026-10-08 · tool version smlsp3000-preset-lab-0.1.0

Status: DEVELOPMENT TOOL. Not the shipped plugin, not installed, not part of any release. It exists to design, audition, document and validate candidate presets before the owner decides on a factory bank. No factory preset exists; the files under presets/candidates/demo/ are tool demonstrations only.

## What it is

A JUCE desktop application (`smlsp3000_preset_lab`) that owns **the product processor itself** — `SMLProcessor` → `HostAdapter` → the unchanged native core — and puts an authoring workflow around it: reference beats, the six product controls, A/B and processed-vs-bypass comparison, candidate metadata, deterministic audition renders with clamp reports, telemetry, candidate files and a manifest.

It adds **no** DSP. There is no second audition engine, no simplified model, no alternative gain mapping, no hidden switch, no limiter, no auto-gain, no normalisation. The one thing it adds to what you hear is an explicitly labelled audition monitor trim applied to the playback *after* the processor; it is never saved and never part of a preset. Proof: tests/test_preset_lab.py renders through the lab and through the native host-adapter path and requires the two to be bit-identical (and the ctest `preset_lab_test` checks determinism and that metadata never changes the output).

Sources: plugin/tools/preset_lab/ (`PresetCandidate.*` format, `LabEngine.*` offline render, `LabApp.cpp` GUI + headless modes, `lab_test_main.cpp` self-test, `CMakeLists.txt`). Build: docs/BUILD_COMMANDS.md CMD-21 (built with the plugin project; separate targets; the product targets are untouched).

## The window

* **SOURCE MATERIAL** — load one or more stereo WAV/AIFF files (mono is duplicated), select one, Play / Stop / Loop. The file analysis line shows rate, length, sample peak and RMS of the file (offline analysis of the whole file; not a plugin meter, not LUFS, not true peak) and the first characters of its SHA-256. "Audio settings…" picks the output device. The audition monitor trim is the only playback-only gain; the label says so. "Help (manual)" opens docs/SML_SP3000_MANUAL.md; "About" shows versions and the claim boundary.
* **CANDIDATE** — the six product controls, bound to the live processor's own host parameters (same normalised mapping a DAW uses, same 10 ms ramps, same stepped switches). Status line: `INIT (unsaved)`, `CUSTOM (unsaved)`, `SAVED <name> r<rev>` or `MODIFIED <name> r<rev>`. Buttons: Reset to INIT (sets the six values to the defaults; does not clear the engine history, exactly like the plugin's own button), Processed / Bypass (toggles the plugin's bypass parameter: latency-aligned original with the 10 ms crossfade), A / B (two parameter sets; switching applies the other set through the host parameters), B = INIT, Copy A → B, Compare A/B (offline renders both over the selected source and prints both clamp reports, peaks and RMS side by side with the RMS level difference for manual level matching), Render audition…
* **CANDIDATE METADATA** — name, author, category (authoring categories: UTILITY, CLEAN, SP CHARACTER, MPC CHARACTER, DUAL STAGE, DRUMS, BASS, SAMPLE / DENSE, HEAVY, EXPERIMENTAL), acceptance status (DRAFT, AUDITIONED, CANDIDATE, REJECTED, TOOL_DEMO), description, audition notes, clamp observations, source material used, engineering note. New / Open… / Save (new revision) / Overwrite / Export manifest.
* **TELEMETRY** — the live processor's meters (input peak + hold, MPC-core-input proxy peak, output peak + hold with the amber over-range indication), the three cumulative clamp counters, over-range flag, non-finite/fault counters, host rate, latency, bypass weight, prepared flag, block count, playback position. These are the plugin's existing meters, nothing new. When no audio device is open, an audition render also pushes the same source through the live processor so the panel shows an offline pass (the counters then exclude the 310-sample drained tail that the render file includes). The right-hand text box shows the last render report, the last A/B comparison or the manifest result.

## Audition workflow

1. Load several beats (drum-heavy, bass-heavy, dense/sample-based, bright digital, already loud, dynamic). Do not judge from one loop.
2. Play, loop, set the six controls. Watch the clamp counters while the loudest section plays.
3. Compare: Processed / Bypass for "is it doing what I want"; A / B against INIT or an alternative set for "which of two"; use the monitor trim to level-match by ear and by the output peak — nothing is normalised for you, and the trim never ends up in a preset.
4. Render audition… writes `reference/preset_lab/renders/<id>_r<rev>/<source>_<rate>.wav` (32-bit float) and `<source>_<rate>.render.json`, prints the clamp report and fills "clamp observations" / "source material" / input & output peaks if they were empty.
5. Name it, pick a category and status, write what you heard and on what. Save (new revision) writes `presets/candidates/<id>_r<rev>.json`. A loaded candidate that you changed can only be saved as a new revision or by the explicit Overwrite button; the original file is never silently replaced.
6. Export manifest writes `presets/candidates/MANIFEST.json` listing every candidate file with its validity, identity and SHA-256.

## Clamp report

For every audition render:

```
SP 12-bit clamps: L n  R n
MPC 18-bit clamps: L n  R n
16-bit storage clamps: L n  R n
Output over-range: YES / NO
```

plus source and output sample peak and RMS. The report classifies nothing as good or bad; it is design information. Counts are per sample per channel over the whole rendered file (including the drained latency tail).

## INIT and engine history

INIT is exactly the six frozen defaults (0 dB / 0 dB / 0 dB / LO / 0 dB / bypass off). "Reset to INIT" and "B = INIT" set values; they do not reset the audio engine's history — the same as the plugin's own Reset to INIT. The engine history is cleared only where the plugin clears it: when playback is (re)prepared by the host (here: when the device starts, the transport is restarted, or an offline render begins, which always starts from a clean engine). `--init-state` prints the native state text INIT corresponds to; the self-test checks that it parses back to the core's defaults.

## Headless modes (tests, screenshots, scripting)

```
smlsp3000_preset_lab --validate <candidate.json>                        # JSON {ok, code, detail}; exit 0/1
smlsp3000_preset_lab --roundtrip <in.json> <out.json>                     # load, save; prints the native state text
smlsp3000_preset_lab --init-state                                         # native schema-v1 state text of INIT
smlsp3000_preset_lab --render <candidate.json|INIT> <source.wav> <out_dir> [--block N]
                                                                          # writes <id>_r<rev>_<source>_<rate>.wav/.render.json/.f64; prints the record
smlsp3000_preset_lab --snapshot <out_dir> <source.wav> [candidate.json ...]  # PNG screenshots (INIT, each candidate after a render, a modified/save view)
```
On Linux run them under `xvfb-run -a` (the tool is a GUI application). On Windows they run directly.

Render record fields: tool/core/adapter versions and the build commit, candidate id and revision, source path and SHA-256, output file SHA-256 and float64 sample SHA-256, rate, block size, frames, latency, the stored (physical) parameters, the effective host-mapped values the adapter actually held (float32 normalised mapping, as a DAW delivers them), the clamp report, and offline peak/RMS of source and output.

## Determinism and regeneration

Renders are deterministic for a given build, source and candidate (same float64 SHA-256 every time; checked by the tests). Audio under reference/preset_lab/ is git-ignored; the JSON records are kept. Regenerate the demo source with `python3 -m smlsp3000.runner preset-lab-demo-source --out reference/preset_lab/sources --rate 48000` (hash record reference/preset_lab/sources/demo_beat_48000.json) and any render with the `--render` mode above.

## Validation

* ctest `preset_lab_test` (plugin/build/tools/preset_lab): candidate round trip, file save/load, INIT equivalence, 25 rejection cases (malformed, non-object, future schema, wrong format, unknown keys incl. hidden/research parameters, bad id/revision/category/status, out-of-range values through the core's own range policy, enum index instead of physical value, non-bool bypass, oversized), no partial application, deterministic render, metadata independence, different parameters differ, two engine instances agree, bypassed render = latency-aligned input, clamp report on a driven render, refusal of out-of-range parameters and unsupported rates, effective-value mapping.
* tests/test_preset_lab.py (unittest, skipped if the lab is not built): demo candidates validate and are TOOL_DEMO, round trip and bounds, malformed/future/unknown rejection, INIT state, deterministic render, **lab render == native HostAdapter render bit-for-bit** for a driven candidate and for INIT, metadata independence, render record fields.
* Product equivalence after adding the lab: evidence/preset_lab/validation/ (native ctest, VAL-026/VAL-023 re-run, pluginval, unit suite, integrity, scope audit) — the product sources are byte-identical to the Sprint 7 checkpoint (`git diff 38ff483 -- native plugin/src` is empty).

## What it must never do (and does not)

Change `getNumPrograms()`, the VST3 program behaviour, the native state schema, VST3 state compatibility, old-session recall, host automation or the plugin identity; store preset metadata inside SMLSP3000_STATE_V1; expose research controls; normalise or limit; claim hardware authenticity for any category.

## Screenshots

evidence/preset_lab/screenshots/ (Linux build under Xvfb, 1280×820): `preset_lab_01_init.png`, `02_demo_light_sp_drive_r1`, `03_demo_light_mpc_drive_r1`, `04_demo_dual_stage_r1`, `05_demo_heavy_r1`, `06_metadata_modified_save_view`. Each candidate screenshot is taken after an audition render of the demo beat, so the status reads MODIFIED (the render filled in observations) and the telemetry shows the offline pass. The demo settings are demonstrations of the tool, not factory presets and not recommendations.
