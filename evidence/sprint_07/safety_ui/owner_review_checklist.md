# SML SP-3000 — owner UI / G-10 review checklist (prototype, Sprint 7)

Status: NOT EXECUTED by the owner. Screenshots: evidence/sprint_07/safety_ui/screenshots/ (Linux build under Xvfb). Nothing here scores preference.

1. Signal path reads correctly: SP INPUT → SP ENGINE → INTERSTAGE → MPC ENGINE → OUTPUT.
2. Six controls present with exact units (dB, discrete 0/+20/+40, LO/MID/HI, bypass); defaults 0 / 0 / 0 / LO / 0 / off; Reset to INIT restores them.
3. Meter labels say what they measure (sample peak per block, hold line) and never claim RMS/LUFS/true peak; "unavailable" shown before audio preparation.
4. Converter clamp counters read "modelled code clamp"; analog clipping/recovery shown as not modelled.
5. Over-range (amber) output indicator appears for finite output above ±1.0 without changing the audio.
6. Bypass button: latency-aligned dry, 10 ms crossfade; host bypass behaves the same.
7. Status strip: reported latency and rate; non-finite/fault messages; model and claim-boundary wording acceptable.
8. Readability at default size (920×540) and at the minimum (760×440); resizing keeps the layout usable; keyboard focus moves through controls; tooltips describe implemented behaviour only.
9. No fake animation, no copied hardware panels/logos.
10. Musical/listening judgement: NOT part of this checklist (CHAIN-EXP-018 remains NOT EXECUTED).
