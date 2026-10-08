# Owner sonic target: drum impact — preset-authoring guide

Revision: V1 · 2026-10-08 · owner target recorded 2026-10-07

Status: AUTHORING GUIDE for the Preset Lab (docs/PRESET_LAB.md, format docs/PRESET_FORMAT.md). Nothing here is a factory preset, a DSP change or a claim about hardware. The plugin reads none of these files.

## The target (creative listening reference only)

The owner's musical reference is the drum impact of 2001-era Dr. Dre productions. This is a **creative listening reference**: a description of what the owner wants finished beats to feel like. It is NOT, and must never be described as, an emulation of that producer's chain, of any album, of specific hardware used on it, hardware-matched behaviour, or verified historical signal-chain accuracy. SML SP-3000's own claim boundary (docs/SML_SP3000_MANUAL.md) stands unchanged.

What the target means for a preset: finished beats feel more authoritative, punchy and weighty in the drum presentation while the finished mix is preserved. Specifically: kick impact, snare authority, transient firmness, drum density, perceived weight, controlled sampler/converter character, enough coloration to feel intentional, preservation of bass definition and of overall mix integrity.

Not acceptable ways to get there: louder output, hidden compression, limiting, normalisation, arbitrary EQ, excessive clipping, destructive high-frequency loss. The plugin contains none of these and the Preset Lab adds none (its audition monitor trim is playback-only and never saved). The result must survive a careful Processed / Bypass comparison at similar perceived loudness.

## Owner-approved foundational directions (presets/candidates/foundations/)

Shared: SP input gain 0 dB, MPC input gain LO, bypass off. Status AUDITIONED (owner found them useful starting points on finished beats); not factory presets; ratings not yet recorded.

| File | Name | SP level | Interstage | Output | Role |
|---|---|---|---|---|---|
| fd_clean_print_r1.json | CLEAN PRINT | -2 dB | 0 dB | +2 dB | restrained reference point |
| fd_dusted_soul_r1.json | DUSTED SOUL | 0 dB | -2 dB | +2 dB | reduced MPC-stage feed, restrained |
| fd_drum_authority_r1.json | DRUM AUTHORITY | +2 dB | -4 dB | +2 dB | primary root of the drum-impact family: SP pushed, MPC feed backed down |
| fd_mpc_pressure_r1.json | MPC PRESSURE | -3 dB | +5 dB | -2 dB | contrasting MPC-forward direction |
| fd_dual_machine_r1.json | DUAL MACHINE | +3 dB | +2 dB | -5 dB | assertive dual-stage reference; stronger processing, NOT light |

The owner's own lab-saved files (presets/candidates/ca_dual_light_r2/r3, ca_mpc_light_r2/r3/r4, cand_46417de5f6cf_r1: "QU DRE PRESET CLEAN", "SOUNDWAVE_1", "SOUNDWAVE_2", "DRE") are preserved exactly as saved. Their description/audition-note text was inherited from the character-audit root files and is stale; the owner edits it in the lab when convenient.

## Calibration finding (owner, 2026-10-07)

The rule-derived character-audit points were too aggressive. `ca_dual_light_r1` (SP +6 / interstage +6 / output -12) was labelled DUAL LIGHT and the owner found it clearly too hot. Gain arithmetic such as +6 +6 -12 says nothing about perceived intensity: the output trim acts after the SP, MPC and storage stages and cannot undo converter/clamp behaviour created upstream. Intensity classes are therefore assigned by **owner audition only**, never from summed gains, and never promoted to LIGHT because the output level is compensated. The eight `character_audit/ca_*_r1.json` files stay as historical DRAFT starting points; their LIGHT/MEDIUM/HARD words are names, not classifications.

## Intensity definitions

| Class | Meaning |
|---|---|
| LIGHT | subtle character; finished mix substantially intact; audible mainly through careful A/B; little or controlled clamp activity; appropriate for routine use on a finished beat |
| MEDIUM | clearly audible machine character; stronger transient/density change; some clamp activity may be musically useful; still appropriate across the whole beat |
| HARD | obvious converter/clamp character; deliberately coloured; use-dependent rather than universally suitable |
| EXTREME | effect / stress-test territory; not representative of normal master-bus use |

Record the class in the audition log (`intensity_class_owner`) and in the candidate's audition notes once the owner has rated it.

## 2001 DRUM AUTHORITY family (presets/candidates/drum_authority_2001/)

Working name only; final naming is an owner decision. The older "2001 Drum Authority" candidate's exact settings were not recovered and are NOT inferred. The family starts from the verified DRUM AUTHORITY foundation and changes one control at a time (SP input gain 0 dB and MPC input gain LO throughout; the +20/+40 dB SP steps and MID/HI MPC gain are left for a separately requested aggressive branch).

| File | Direction | SP level | Interstage | Output | Status |
|---|---|---|---|---|---|
| da2001_root_r1.json | root (= DRUM AUTHORITY) | +2 | -4 | +2 | DRAFT |
| da2001_a_sp_less_r1.json | A slightly less SP drive | +1 | -4 | +2 | DRAFT |
| da2001_b_sp_more_r1.json | B slightly more SP drive | +3 | -4 | +2 | DRAFT |
| da2001_c_mpc_less_r1.json | C less MPC feed | +2 | -6 | +2 | DRAFT |
| da2001_d_mpc_more_r1.json | D slightly more MPC feed | +2 | -2 | +2 | DRAFT |
| da2001_e_trim_0_r1.json | E output-trim variation | +2 | -4 | 0 | DRAFT |
| da2001_e_trim_p4_r1.json | E output-trim variation | +2 | -4 | +4 | DRAFT |

E exists for fair, level-matched listening: the trim is after all processing, so E renders are identical to the root up to the trim gain (same clamp counts); they help the owner compare at similar perceived loudness without touching the monitor trim. With +4 dB the output sample peak can exceed 1.0 (float) on loud material; watch the host's headroom.

### Preparation telemetry (synthetic, not owner material)

evidence/preset_lab/drum_authority_2001_windows_demo_telemetry.json holds Windows Release-build renders (`smlsp3000_preset_lab.exe --render`) of every foundation, family member and owner-saved file on the synthetic demo beat at its committed -3 dBFS peak and on the same beat scaled to -0.5 dBFS peak. On that sparse stimulus (RMS about -19 dBFS) the foundations and the whole family show zero clamps at -3 dBFS and only single- to double-digit SP clamps at -0.5 dBFS (DUAL MACHINE: about 1000 MPC clamps; MPC PRESSURE: a few dozen); `ca_dual_light_r1` shows about 14 000 MPC and 7 000 storage clamps per channel at -3 dBFS, which the owner heard as clearly too hot. Finished beats are denser and louder, so these numbers are not predictions; the owner re-observes the counters on real material and records them in the log.

## Authoring method (per candidate)

1. Start from a verified foundational preset (or the current family root).
2. Change ONE control at a time.
3. Audition on several finished owner beats (drum-heavy, bass-heavy, dense, bright, already loud, dynamic).
4. Compare against: bypass, INIT, DRUM AUTHORITY, and the owner's current favourite candidate.
5. Control playback loudness manually (audition monitor trim or the output-trim E variants); never judge the louder one as better.
6. Record in presets/candidates/drum_authority_2001/AUDITION_LOG.csv: exact parameter values, source beat, SP / MPC / storage clamp counts, input peak, output peak, owner notes.
7. Owner ratings, 0–5 each: drum impact, kick authority, snare authority, bass preservation, mix preservation, character; plus Too hot YES/NO and Would use on a finished beat YES/NO.
8. Save only successful settings as new candidate revisions (Save (new revision) in the lab); set `acceptance_status` AUDITIONED or CANDIDATE and the intensity class in the notes. Unsuccessful settings are logged, not saved.

## Success criterion and stop rule

The goal is not maximum clipping or the loudest setting. It is a clearly audible sampler/converter imprint that gives the owner the drum authority and impact of their creative reference while remaining usable on an already-finished stereo beat.

STOP preset development and report if the desired impact cannot be reached without jumping directly from subtle to ugly/destructive behaviour: that outcome means the DSP character range may need a separate review (owner product gate B). No DSP change is made during preset authoring without explicit owner authorisation.
