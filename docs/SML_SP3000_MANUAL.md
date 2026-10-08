# SML SP-3000 — Operating Manual

Revision: manual V1 · 2026-10-08 · software build v0.7.0 (native core smlsp3000-native-core-1.0.0, host adapter smlsp3000-host-adapter-1.0.0, state schema v1)

This manual describes how to use SML SP-3000 on finished beats and mixes. It is written for the person at the DAW, not for the research record. Three kinds of statements appear and are labelled where it matters:

* **USER-FACING** — what you hear, what the controls do, how to work with it.
* **IMPLEMENTATION DETAIL** — what the software actually computes (from the source code and its validation records).
* **UNRESOLVED RESEARCH CLAIM** — something documented about the original hardware that this build does *not* model or has not verified.

Claim boundary (applies to every page): SML SP-3000 is a software effect inspired by and informed by documented SP-1200 / MPC3000 architecture and behaviour. It is not an exact emulation, not hardware matched, not component accurate, not measured against hardware and not hardware validated. Nothing in this manual should be read as "it sounds like the machine"; it describes what this software does.

---

## 1. What SML SP-3000 Is

SML SP-3000 is a stereo full-mix processor. It passes your whole beat through two sampler-style conversion stages in series: a 12-bit stage running on a 26.04 kHz clock (the "SP engine"), then an 18-bit-in / 16-bit-store / 44.1 kHz stage (the "MPC engine"). Between them sits one gain (the interstage level), in front of the first sits an input level and a stepped input gain, and after the second sits an output trim and a bypass.

What it adds to a signal comes only from those conversions: quantisation to 12 bits, sample-and-hold at 26.04 kHz with the aliasing and images that implies, a hard code clamp when a converter is overdriven, 18-bit quantisation and clamp, rounding from 18 to 16 bits, and band-limiting to the 44.1 kHz domain. There is deliberately **no** saturation model, no noise generator, no EQ, no jitter, no compressor, no limiter, no normalisation, no "drive" macro, no wet/dry control.

USER-FACING: think of it as a converter chain you can push harder or run cleaner, not as a colour box with a flavour knob.

## 2. Intended Use

* Insert on the master bus or a mix bus of a finished beat, or on a stem bus (drums, bass, samples).
* Set levels so that the two converter stages see the signal you want them to see, listen, and then decide how hard to push each stage.
* Use the bypass to compare against the untouched signal at the same alignment.
* Use the Preset Lab (section 28) to design candidate presets on your own reference beats before anything becomes a factory preset.

Not intended: as a mastering limiter (it never limits), as a loudness tool (nothing is normalised), as a hardware substitute for measurement or archival work (see section 27).

## 3. Signal Flow

```
host input (stereo)
   |
   v
SP INPUT ........ SP input level (-60..+12 dB, smooth)  +  SP input gain (0 / +20 / +40 dB, stepped)
   |
   v
SP ENGINE ....... 12-bit converter with code clamp, sample-and-hold on the 26.04 kHz clock
   |
   v
INTERSTAGE ...... interstage level (-60..+24 dB, smooth)  +  MPC input gain (LO / MID / HI = 0 / +20 / +40 dB, stepped)
   |
   v
MPC ENGINE ...... 18-bit converter with code clamp at 44.1 kHz, 18 -> 16-bit storage rounding (with clamp), reconstruction
   |
   v
OUTPUT .......... output trim (-60..+12 dB, smooth)  ->  bypass selector (latency-aligned original input, 10 ms crossfade)
   |
   v
host output (stereo)
```

IMPLEMENTATION DETAIL: internally the audio is first raised to an 8x "proxy" grid (eight times the host rate) so that both machine clocks can be placed exactly; the SP and MPC stages run on that grid and the output is brought back to the host rate. The two channels are processed as a linked pair (same clock instants, same settings, separate signal state). Everything is computed in 64-bit floating point.

## 4. Control Reference

| Control | Host parameter ID | Range / values | Default (INIT) | Behaviour on change |
|---|---|---|---|---|
| SP input level | `sp_input_level_db` | -60.00 … +12.00 dB, continuous | 0.00 dB | 10 ms linear-in-dB ramp |
| SP input gain | `sp_input_gain` | 0 dB / +20 dB / +40 dB | 0 dB | instant step at the next block |
| Interstage level | `interstage_level_db` | -60.00 … +24.00 dB, continuous | 0.00 dB | 10 ms linear-in-dB ramp |
| MPC input gain | `mpc_input_gain` | LO / MID / HI (relative 0 / +20 / +40 dB) | LO | instant step at the next block |
| Output trim | `output_trim_db` | -60.00 … +12.00 dB, continuous | 0.00 dB | 10 ms linear-in-dB ramp |
| Bypass | `plugin_bypass` | off / on | off | 10 ms linear crossfade to the latency-aligned original |

These six are the only controls. There are no hidden parameters, no page two, no research switches reachable from the plugin. "Reset to INIT" in the editor sets all six back to the defaults above (it does not clear the audio engine's history; see section 22 of the Preset Lab guide for the distinction).

USER-FACING: the ranges are software ranges chosen for this product; they are not the travel of a hardware pot and the dB numbers are not calibrated voltages.

## 5. SP Input Stage

Two controls set the level that reaches the 12-bit converter, and they simply add up:

* **SP input level** is a continuous trim. Use it for fine level decisions and for automation.
* **SP input gain** is a three-position step (0 / +20 / +40). Use it for coarse decisions. Switching it is an immediate step at the next processing block; it is not ramped, so switch it while listening, not in the middle of an exposed sustained note if you want to avoid a click-like jump.

IMPLEMENTATION DETAIL: with everything at 0 dB, a host sample at full scale (±1.0) lands exactly at the converter's full-scale code. Any total gain above 0 dB means peaks above −(total gain) dBFS reach the clamp. Example: +6 dB total means every input peak above −6 dBFS is clamped.

UNRESOLVED RESEARCH CLAIM: the hardware has an input amplifier and an anti-alias filter in front of its converter. Neither is modelled here (the amplifier's clipping behaviour is unmeasured; the filter is a placeholder marked INACTIVE). The consequence is spelled out in section 6.

## 6. SP Engine Behaviour

What the SP engine does to the signal, in order:

1. **12-bit quantisation.** Every sample is rounded to the nearest of 4096 codes (−2048 … +2047). Quiet material uses fewer codes; the rounding error becomes a larger fraction of the signal. Loud material uses more codes. This is the ordinary behaviour of a 12-bit converter: level matters.
2. **Code clamp.** Anything above the top code or below the bottom code is held at that code. This is a hard, flat clamp, not a soft saturation. It is counted and shown as "SP 12-bit converter clamps".
3. **Sample-and-hold at 26.04 kHz.** The signal is sampled on the SP clock and held for a full clock period. Two audible consequences:
   * Frequencies above half the SP clock (about 13.0 kHz) fold back below it. A 16 kHz hat component appears at roughly 10 kHz; an 18 kHz component near 8 kHz. This is aliasing and it is kept on purpose: it is part of what a 26 kHz sampler does.
   * The hold produces copies ("images") of the whole spectrum above 13 kHz and a gentle high-frequency roll-off below it (an ideal full-period hold is about 4 dB down at 13 kHz). The images that survive into the MPC stage are then band-limited by it (section 8).

IMPLEMENTATION DETAIL: the clock is the exact rational 20 MHz / 768 = 26 041.666… Hz (a documented, provisional value); the quantiser rounds half-way values toward +∞; the hold is an ideal band-limited zero-order hold of the full period. The SP route in this build is the "no output filter" channel pair, so there is no SP output filtering.

UNRESOLVED RESEARCH CLAIM: because no anti-alias filter is modelled, this build folds **more** high-frequency content than a filtered hardware input would. The exact hold fraction, the output filters of the other channel pairs, and any analog overload behaviour are unmeasured and not modelled.

## 7. Interstage Gain

The interstage level is the one gain between the SP output and the MPC input. At 0 dB, SP full scale maps onto MPC full scale: a signal that just reached the SP converter's top code also just reaches the MPC converter's top code.

* Raise it to push the MPC 18-bit converter into its clamp **without** changing what the SP stage did.
* Lower it to give the MPC stage headroom so that nothing the SP stage produced (including clamp flat-tops and alias products) can clamp again.

The range extends to +24 dB, which is enough to clamp the MPC converter hard on almost any material.

IMPLEMENTATION DETAIL: the 0 dB mapping is a software convention set for this product (OWN-DEC-012); it is explicitly non-historical. There is no second, hidden record-level control; the internal MPC record level is fixed at 0 dB because it would be mathematically identical to the interstage level.

## 8. MPC Engine Behaviour

In order:

1. **MPC input gain** (LO / MID / HI) adds 0 / +20 / +40 dB on top of the interstage level. It is a step, not a ramp.
2. **Band-limiting and sampling at 44.1 kHz.** Content above 22.05 kHz, including most of the SP stage's images, is removed; the signal is sampled on the MPC clock.
3. **18-bit quantisation with code clamp.** Peaks above full scale are clamped at the top 18-bit code (counted as "MPC 18-bit converter clamps"). This is the second hard clamp in the chain.
4. **18 → 16-bit storage rounding.** The 18-bit code is divided by four and rounded to the nearest 16-bit code. A rounded value that falls outside the 16-bit range is clamped (counted as "16-bit storage clamps"; this only happens at the extreme codes).
5. **Reconstruction.** The 16-bit stream is re-expanded and reconstructed with a transparent (ideal) interpolation filter back onto the proxy grid, then resampled to the host rate.

USER-FACING: the MPC stage sounds "clean" by itself at moderate levels; its character in this build comes from how hard you drive its converter (clamp) and from what it does to the SP stage's aliases and images (it keeps those below 22.05 kHz and removes the rest).

IMPLEMENTATION DETAIL: the converter is modelled as transparent band-limiting plus quantisation (ROUND_NEAREST_18BIT), the storage reduction as ⌊c/4 + ½⌋, the DAC as transparent reconstruction. The LO/MID/HI labels are relative gain steps; the printed hardware sensitivities are not used as full-scale calibration.

UNRESOLVED RESEARCH CLAIM: the hardware converter responses, analog input/output stages, overload recovery, de-emphasis and any non-identity arithmetic are not modelled. The rounding rule for 18 → 16 bits on the hardware is unknown; round-to-nearest is the chosen software rule (truncation exists only as a research switch, not reachable in the product).

## 9. Output Stage

The output trim is a plain gain after both engines. It is the last thing before the bypass selector.

* It changes level and nothing else. It cannot undo a clamp that happened upstream (section 11).
* It is **not** applied to the bypassed signal: in bypass you hear the original input at its original level.
* It is never a limiter. If the processed signal exceeds ±1.0 (full scale), it leaves the plugin above full scale and the host decides what happens next. The output meter turns amber to tell you.

## 10. Bypass

Bypass replaces the processed signal with the **original input**, delayed by exactly the plugin's reported latency so the host's delay compensation keeps everything aligned, with a 10 ms linear crossfade in each direction. While bypassed:

* No gain, no trim, no machine stage touches the signal.
* The engines keep running in the background, so coming out of bypass does not restart anything and does not click.
* Rapid toggles continue from wherever the crossfade currently is.

The host's own bypass button (where the DAW offers one) and the editor's Bypass control are the same parameter. Starting playback already in bypass gives the fully dry signal from the first sample.

IMPLEMENTATION DETAIL: the crossfade weights are complementary (w and 1−w), so the sum is exactly the processed signal at one end and exactly the dry signal at the other.

## 11. Gain Staging

The chain has two places where a hard clamp can happen and three gains that decide whether it does. Everything else is linear. So gain staging *is* the sound design of this processor.

| You raise … | What it changes | What it does not change |
|---|---|---|
| SP input level / SP input gain | level into the 12-bit converter: more codes used, then clamp when peaks pass full scale; aliasing products get louder in proportion | nothing downstream is "re-driven" unless the SP output rises past MPC full scale |
| Interstage level / MPC input gain | level into the 18-bit converter: clamp when the SP output (already quantised, possibly clamped, with aliases) passes MPC full scale | the SP stage's result is already fixed; the MPC stage can only clamp it further and band-limit it |
| Output trim | the level you hand to the host | nothing about either converter; **a clamp that already happened stays in the audio** |

Four ways to run it:

* **Driving the SP stage** — raise SP input level (and/or step the SP input gain) until the SP clamp counter starts moving on the peaks you want flattened. Lower the interstage level so the MPC stage does not clamp again. Bring the level back with the output trim.
* **Driving the MPC stage** — keep the SP stage below its clamp (counter stays at 0) and raise the interstage level (and/or MPC input gain) until the 18-bit clamp counter moves. Trim down afterwards.
* **Driving both** — raise both. Expect the MPC clamp to act on the already flat-topped SP output; the two clamps are at different places in the chain and after different processing (12-bit quantisation and the 26 kHz sample-and-hold sit between them).
* **Reducing output trim** — only changes the listening level. It is the right tool for level-matching an A/B comparison and the wrong tool for "fixing" clamps.

Workflow starting points (describe intent, not numbers — the numbers come from auditioning in the Preset Lab):

* **Clean** — all gains at or below 0 dB; no clamp counter moves; you hear 12-bit quantisation, 26 kHz aliasing/images and the 44.1 kHz band limit only.
* **Light coloration** — SP level slightly up so quiet material uses more codes, clamps only on the very loudest peaks.
* **SP-forward** — SP stage driven into clamp, MPC stage kept clean.
* **MPC-forward** — SP stage clean, interstage pushed so only the 18-bit converter clamps.
* **Dual-stage drive** — both clamp; order matters (SP first, then MPC).
* **Heavy clamp** — large gains at both stages; the 16-bit storage clamp counter may also move; expect over-range output unless the trim is pulled well down.

The owner has not approved any numeric "best settings" and none are given here. Use the Preset Lab to find them on your own material.

## 12. How the Two Machine Stages Interact

* The SP stage comes first. Whatever it produces — quantisation error, flat-topped clamps, fold-back products, hold images — is the MPC stage's input.
* The MPC stage band-limits at 22.05 kHz. SP images between 13 kHz and 22.05 kHz pass; images above 22.05 kHz are removed. Fold-back products (which are below 13 kHz) always pass.
* Clamping at the MPC stage flattens an already quantised signal. Two clamps in series do not "add" in a simple way; the second one only acts where the first stage's output (times the interstage gain) still exceeds full scale.
* The interstage level is the only thing that decides how the SP result meets the MPC converter. At 0 dB a clean, unclamped SP output cannot clamp the MPC stage; with positive interstage gain it can.

## 13. Clamp / Converter Behaviour

Three counters report what the converters did. All are **modelled code clamps** — the converter reached its top or bottom code — counted per sample per channel, cumulative since the engine was last reset (play start / re-prepare).

| Counter | Where | Meaning |
|---|---|---|
| SP 12-bit converter clamps | after SP input level + SP input gain, at the 12-bit converter | the SP converter was overdriven on that many samples (on the SP clock) |
| MPC 18-bit converter clamps | after interstage level + MPC input gain, at the 18-bit converter | the MPC converter was overdriven on that many samples (on the 44.1 kHz clock) |
| 16-bit storage clamps | at the 18 → 16-bit rounding | rounding produced a value outside the 16-bit range (extreme codes only) |

What a clamp is here: the signal is held flat at the code limit for as long as it exceeds it. It is abrupt. There is no analog softening, no recovery time, no asymmetry, no DC shift — because none of those have been measured (UNRESOLVED RESEARCH CLAIM; the editor says "Analog clip: not modelled").

The counters are information, not a verdict. Zero clamps is not "correct" and many clamps is not "wrong"; it is the number of samples you flattened.

Over-range output (amber output meter) is a separate thing: the finite output signal exceeded ±1.0. It can happen from a positive output trim, and it can happen with the trim at 0 dB because the reconstruction after a clamped, flat-topped signal overshoots (ringing on the flat top edges). The plugin never clamps or limits its output.

## 14. Metering

Every meter is a **sample-peak** meter: the largest absolute sample value in each processing block, in dBFS. None of them is RMS, LUFS, VU, true-peak (inter-sample) or an analog level. A hold line shows the largest value since the engine was last reset.

| Meter | Measures | Does not mean |
|---|---|---|
| Input peak (L/R) + hold | the host input, per block, before any gain | not the level inside either converter |
| MPC input peak (L/R) | the signal at the MPC converter input on the proxy grid, after the interstage level and MPC input gain, per block | no hold line; not an output level; not a loudness |
| Output peak (L/R) + hold | the final output after trim and bypass, per block; amber when a finite sample exceeded ±1.0 | not a true-peak reading: peaks between samples are not measured |
| Clamp counters | see section 13 | not "distortion amount" |
| Status strip | "ready", "not prepared", "unsupported sample rate: output muted", "BYPASSED" / "bypass crossfade" | — |
| Reported latency | the integer delay the host compensates, in samples and ms, at the current rate | not zero latency; the SP hold adds a frequency-dependent half period that is not compensated |
| Fault line | non-finite input samples replaced by zero (count); internal fault (chunk silenced, signal state cleared, latched until reset) | — |

"unavailable" means the meter genuinely has no data (editor opened before the host prepared audio, or an unsupported rate). It is never a silent zero.

## 15. Sample Rates

Supported host rates: 44.1, 48, 88.2, 96, 176.4 and 192 kHz. The machine clocks (26.04 kHz and 44.1 kHz) are placed exactly at every one of these rates; the processing does not change meaning with the host rate, but the result is not bit-identical across rates (different host grids, different phase of the machine clocks relative to the audio — tracked as design issue DI-001).

Any other host rate: the plugin reports "unsupported sample rate: output muted" and outputs silence rather than guessing. Float32 and float64 host processing are both supported; the float32 path is the float64 engine with the host buffers promoted on the way in and cast on the way out.

## 16. Latency

| Host rate | Reported latency (samples) | ms |
|---|---|---|
| 44.1 kHz | 298 | 6.76 |
| 48 kHz | 310 | 6.46 |
| 88.2 kHz | 426 | 4.83 |
| 96 kHz | 449 | 4.68 |
| 176.4 kHz | 682 | 3.87 |
| 192 kHz | 728 | 3.79 |

The latency is fixed for a given rate, identical in bypass and when processing, and reported to the host for automatic compensation. It does not depend on any control. Not included: the SP sample-and-hold adds a frequency-dependent delay of half an SP clock period (about 19 µs), which is part of the processing, not latency.

## 17. Automation

* All six parameters are automatable from the host.
* The host hands parameter changes to the plugin once per processing block; a change requested in the middle of a block takes effect at the start of the next block (BLOCK-BOUNDARY delivery, typically well under a millisecond late at ordinary buffer sizes). Sample-accurate automation is **not** claimed.
* Continuous controls (SP input level, interstage level, output trim) then ramp over 10 ms, linearly in dB, inside the engine. Automation moves are therefore smooth without any extra smoothing in the host.
* Stepped controls (SP input gain, MPC input gain) switch immediately at that block boundary. Bypass crossfades over 10 ms.
* The host sees the parameters normalised linearly in dB over their ranges; the editor and the host display the same dB value. Values are not quantised to display steps.

Offline rendering ("bounce") goes through the same path and gives the same result as real-time playback for the same block schedule.

## 18. Session Recall

The plugin stores the six control values plus the identity of the model it was built with (schema version 1). It never stores filter coefficients, research switches, calibration data or anything else.

* Reopening a project restores the six values exactly.
* State from a damaged project, from a future version with a different schema, from a build with different model assets, or with out-of-range values is **rejected as a whole**; the current settings stay and nothing is partially applied.
* There is one program, INIT. The plugin has no factory preset bank in this build; presets are being designed with the Preset Lab (section 28) and will be added as a separate, later step.

## 19. Recommended Workflow

1. Insert SML SP-3000 on the bus you want to treat. Confirm the status strip says "ready" and shows the latency for your rate.
2. Play the loudest section. Watch the input peak and the SP clamp counter: at INIT, the SP stage clamps only if the input itself exceeds full scale.
3. Decide which stage you want to hear working first. Raise that stage's level until its clamp counter starts moving on the peaks you care about; stop where it sounds right, not at a number.
4. Set the other stage: either keep it clean (counter stays at 0) or drive it too.
5. Pull the output trim down until the output peak sits where the untouched signal sat. Toggle bypass to compare at matched level. Remember that the trim does not touch the bypassed signal, so match by ear and by the output meter.
6. Automate SP input level or interstage level across sections if you want the treatment to change with the arrangement; use the stepped gains for section-sized jumps.
7. Save the project. If a setting works on several beats, record it as a Preset Lab candidate with notes (section 28).

## 20. Using It on Drum-Heavy Beats

* Transients are where the SP clamp acts first. Driving the SP stage flattens kick and snare peaks; the body of the hit passes with 12-bit resolution; hat and cymbal content above 13 kHz folds down into the upper mids. Listen to whether the folded hats sit where you want them.
* The MPC stage then band-limits at 22.05 kHz and, if driven, flattens whatever the SP stage left above full scale. On drums the difference between SP-forward and MPC-forward is mostly *where* the flat top happens: before or after the 26 kHz hold.
* Watch the output over-range indicator: clamped drums reconstruct with overshoot, so a trim of 0 dB can still leave the output above full scale.

## 21. Using It on Bass-Heavy Beats

* Low frequencies are far below both clock rates; they alias nothing and pass the hold almost untouched. What changes is resolution (12 bits) and level: sustained bass at a high level uses many codes and clamps evenly across a whole cycle when driven — that is a flat-topped sine, which adds odd harmonics abruptly.
* Driving the MPC stage on bass gives the same kind of flat top but after the SP stage's quantisation; the two sound different only in what sits on top of the bass (hats, air) that the SP stage already folded.
* The interstage level is the useful control here: lower it so the bass does not clamp twice.

## 22. Using It on Dense / Sample-Based Beats

* Dense material has many peaks near full scale; even +2 or +3 dB of SP input level produces frequent, short clamps. The counters rise quickly. Decide by ear whether that density of clamps is what you want.
* Sample-based material often already contains aliasing or band-limited content; the SP stage's fold-back then lands on top of it. Compare against bypass to be sure the change is the one you want.
* On already-loud mixes, start by lowering the SP input level (negative values) to see what the chain does *without* clamps, then raise it.

## 23. Subtle Processing

* Keep all gains at or below 0 dB so neither clamp counter moves.
* What remains is 12-bit quantisation (most audible on quiet passages and decays), the 26 kHz hold's high-frequency roll-off and fold-back of anything above 13 kHz, and the 44.1 kHz band limit.
* Lowering the SP input level makes the quantisation coarser (fewer codes); raising the interstage level does nothing audible until the MPC converter clamps. Use the output trim to compensate the level.

## 24. Heavy Processing

* Large positive gains at both stages; both clamp counters move constantly; the 16-bit storage clamp counter may move as well.
* The output will be over range unless the trim is far down. Pull the trim down first, then raise the input gains, to protect your monitoring.
* Expect a hard, square-edged result; there is no softening stage. If that is too harsh, the fix is less gain at one stage, not more trim.

## 25. Troubleshooting

| Symptom | Cause | What to do |
|---|---|---|
| Silence, status says "unsupported sample rate" | host rate is not one of the six supported rates | change the project rate (section 15) |
| Meters say "unavailable" | editor opened before the host started audio | start playback; the host prepares the plugin |
| Clamp counters never move | total gain into that converter is ≤ 0 dB and the input does not reach full scale | raise that stage's level |
| Bypass sounds louder/quieter than processed | output trim is applied to the processed signal only | match with the trim while watching the output meter |
| Audible jump when switching SP/MPC input gain | stepped gains switch immediately | switch between sections, or automate the continuous levels instead |
| Output meter amber, host clips | finite over-range output (section 13) | lower the output trim; the plugin never limits |
| Settings came back as INIT after reopening | the saved state was rejected (schema/identity/range) | re-set the controls; the rejection is deliberate |
| Standalone app is silent | the standalone mutes its input until monitoring is enabled | enable input monitoring in its audio settings |
| "FAULT" shown in the status | an internal non-finite value occurred; that block was silenced and the signal state cleared | restart playback; report the material and settings |

## 26. Known Limitations

* No anti-alias filter in front of the SP converter (placeholder INACTIVE): more fold-back than a filtered hardware input.
* No SP output filter channels (only the unfiltered route is populated), no analog input/output stages, no overload recovery, no de-emphasis, no noise, no jitter.
* Automation is applied at block boundaries, not sample-accurately.
* Output can exceed full scale; the plugin does not limit.
* Across host rates the output is not bit-identical (DI-001).
* Only stereo in / stereo out; no sidechain, no multichannel.
* Validated on Linux by automated tests; the Windows build was validated by the owner in FL Studio on one machine; no other DAW has been checked.

## 27. Accuracy / Modeling Claims

What is claimed: the plugin reproduces its own accepted software reference to floating-point rounding (validated at all six rates, float32 and float64, offline and real-time), is deterministic, reports its latency correctly and applies its controls as documented.

What is **not** claimed: any measured agreement with an SP-1200 or an MPC3000. No hardware was measured for this build; every converter rate, word length, rounding rule, clamp and gain step comes from documentation and documented engineering decisions, and each is tagged "UNVALIDATED AGAINST HARDWARE" in the project's confidence register. The words "emulation", "hardware matched", "authentic" and "component accurate" do not apply to this build and are not used in its interface.

## 28. Preset-Creation Workflow

Presets are designed outside the plugin, in the **SML SP-3000 Preset Lab**, a development tool that drives the exact same processor (see docs/PRESET_LAB.md and docs/PRESET_FORMAT.md). The workflow:

1. Load several reference beats into the Preset Lab (drum-heavy, bass-heavy, dense, bright, already loud, dynamic).
2. Set the six controls, listen in a loop, compare A against B (another candidate or INIT) and processed against bypass. Level-match manually with the audition monitor trim; nothing is normalised for you.
3. Render an audition file; read the clamp report (SP 12-bit / MPC 18-bit / 16-bit storage counts, over-range yes/no) and the file's peak and RMS.
4. Name the candidate, give it an authoring category, write what you heard and on which material, and save it. A changed candidate is saved as a new revision unless you explicitly overwrite.
5. Export the candidate manifest for review.

Candidates are JSON files with physical values (dB, step dB, LO/MID/HI); they are not plugin state and do not become factory presets by being saved. The factory bank is a later, separate step that the owner approves.

## 29. Technical Reference Table

| Item | Value | Status |
|---|---|---|
| Channels | 2 in / 2 out, linked pair | implemented |
| Host rates | 44.1 / 48 / 88.2 / 96 / 176.4 / 192 kHz | implemented; others muted |
| Internal precision | 64-bit float, 8x proxy grid | implemented |
| SP clock | 20 MHz / 768 = 26 041.67 Hz | documented value, PROVISIONAL |
| SP word length / codes | 12 bit, −2048 … +2047, round to nearest | documented word length; rounding rule chosen |
| SP hold | full-period band-limited zero-order hold | PROVISIONAL (hold fraction unmeasured) |
| SP anti-alias / output filter | not modelled (INACTIVE) / none (route NONE_CH7_8) | UNRESOLVED |
| Interstage 0 dB meaning | SP full scale → MPC full scale | software convention, NON-HISTORICAL |
| MPC clock | 44 100 Hz | documented |
| MPC converter | transparent band-limit, 18-bit round to nearest, code clamp | architecture documented; response not modelled |
| MPC storage | 18 → 16 bit, ⌊c/4 + ½⌋, clamp | rule chosen (hardware rule unknown) |
| MPC reconstruction | transparent interpolation, re-expansion ×4 | architecture documented; response not modelled |
| Ramps | 10 ms linear in dB (continuous controls); 10 ms linear crossfade (bypass) | implemented |
| Automation delivery | block boundary | implemented (host path) |
| Latency | 298 / 310 / 426 / 449 / 682 / 728 samples | implemented, verified |
| Max host block | any (internal chunking at 8192) | implemented |
| Non-finite input | replaced by 0 and counted | implemented |
| Output limiting | none | by design |
| State | schema v1: six controls + model identity; strict rejection | implemented |
| Programs | INIT only | this build |

## 30. Version / Identity

| Field | Value |
|---|---|
| Product | SML SP-3000 v0.7.0 |
| Company | Soundwave Machine Learning |
| Formats | VST3 (stereo effect), Standalone |
| Manufacturer / plugin code | SWML / Sp3K |
| Bundle id | com.soundwavemachinelearning.smlsp3000 |
| Native core | smlsp3000-native-core-1.0.0 |
| Host adapter | smlsp3000-host-adapter-1.0.0 |
| Model assets | sp1200-track-a-provisional v1, mpc3000-track-a-provisional v1 (cascade path B) |
| State root | SMLSP3000_STATE_V1 (schema 1) |
| Framework | JUCE 8.0.9 (pinned) |
| Source | https://github.com/soundwave-machine-learning/smlsp3000 |

Related documents: docs/USER_CONTROL_GUIDE.md (short control guide), docs/PARAMETERS.md (parameter layers and state policy), docs/PRESET_LAB.md (authoring tool), docs/PRESET_FORMAT.md (candidate file format), docs/WINDOWS_HANDOFF.md (build and install on Windows), docs/CONFIDENCE.md (claim register).
