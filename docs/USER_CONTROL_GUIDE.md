# SML SP-3000 — user and control guide (software build v0.7.0, Sprint 7 prototype)

Revision: execution V7 (Sprint 7) · 2026-10-07

Status: PROTOTYPE pending owner G-10 review. SML SP-3000 is a software effect inspired by and informed by documented SP-1200 / MPC3000 architecture and behaviour. It is not an exact emulation, not hardware matched, not component accurate, not measured and not hardware validated (docs/EXECUTION_PLAN_V2.md §7). Every modelled value is UNVALIDATED AGAINST HARDWARE.

## What it does

A stereo-in / stereo-out effect: the signal passes an SP-style 12-bit sampler stage on a provisional 26.04 kHz clock (band-limited sample-and-hold, images and fold-back retained), an interstage gain, and an MPC-style stage (transparent 18-bit converter with code clamp, 18→16-bit storage reduction, transparent reconstruction at 44.1 kHz). Path B (full sample path), cascade order SP → MPC. There is no saturation, noise, EQ, jitter, limiter, normalisation, drive macro or wet/dry control.

## Controls (the six frozen product controls; docs/PARAMETERS.md)

| Control | Range / values | Default | What it does |
|---|---|---|---|
| SP input level | −60 … +12 dB, continuous | 0 dB | trim before the SP stage (R2); ramped over 10 ms |
| SP input gain | 0 / +20 / +40 dB | 0 dB | discrete SP input gain switch; switches at the next block |
| Interstage level | −60 … +24 dB, continuous | 0 dB | the single gain between SP output and MPC input (R10); 0 dB = SP normalised full scale → MPC normalised full scale (owner-set software default, non-historical). Positive values can reach the MPC 18-bit converter clamp, the only overload mechanism |
| MPC input gain | LO / MID / HI | LO | discrete MPC input gain position (0 / +20 / +40 dB relative); sensitivity labels are not full-scale calibration |
| Output trim | −60 … +12 dB, continuous | 0 dB | final output gain only; not a limiter; not applied while bypassed |
| Bypass | off / on | off | latency-aligned original input (before every gain and both machines) with a 10 ms linear crossfade; host bypass uses the same parameter |

Host automation: parameter changes are applied at block boundaries (JUCE/VST3 delivery); the engine's own 10 ms ramps smooth continuous controls. Reset to INIT sets the six controls to their defaults without resetting the audio engine.

## Meters and status

* Input peak, MPC input peak (proxy-grid peak at the MPC core input, after the interstage gain) and output peak are sample-peak meters per block with a hold line; they are not RMS, LUFS or true-peak meters.
* SP 12-bit converter clamps and MPC 18-bit / 16-bit clamps count modelled code clamps. Analog clipping, overload and recovery are not modelled (no measurement) and are shown as such.
* The output meter turns amber when the finite output exceeds ±1.0 (over-range). Nothing is clamped or limited by the plugin; the host decides.
* Non-finite input samples (NaN/Inf) are replaced by zero and counted. An internal fault (non-finite output) silences that block, clears the signal state and is shown until the engine is reset.
* Reported latency is the integer alignment delay the host compensates (e.g. 310 samples at 48 kHz, 449 at 96 kHz; below 10 ms at every supported rate). The SP hold adds a frequency-dependent half period that is not compensated. No zero-latency claim.
* "unavailable" means a meter has no data (editor opened before audio preparation, or unsupported rate). It is never a silent zero.

## Supported rates and hosts

44.1, 48, 88.2, 96, 176.4 and 192 kHz. Float32 and float64 host buffers. Any block size (internal chunking). Intended deployment: Windows x86_64 VST3 + Standalone (FL Studio primary). Linux builds are development/testing builds.

## Standalone application

Same processor as the VST3. The standalone window mutes the audio input by default (JUCE standalone behaviour): enable monitoring explicitly in the audio settings to hear a live input. The Linux development build is compiled without an ALSA backend (no audio device in the container); the Windows build uses the system audio devices.

## State and presets

Sessions store the six controls plus the model/asset identity (schema version 1). Research switches, filter coefficients, calibration data, unpopulated routes and the research reverse order are never stored. Unsupported or corrupted state is rejected and the current settings remain. No factory preset bank exists in this build; INIT is the only program.
