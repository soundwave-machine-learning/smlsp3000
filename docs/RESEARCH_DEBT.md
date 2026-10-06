# Research debt register

Revision: execution V1 (Sprint 1) · 2026-10-06 · supersedes planning V1

Status: EXECUTION IN PROGRESS. All 6 P0 + 12 P1 items remain OPEN after Sprint 1.

## Priority semantics

Source P0 blocks a defensible calibrated reference; it does not prohibit independent documentation, numerical skeleton or self-test work. Source P1 is mandatory before dependent production modeling. Source P2/P3 remain deferred, with AUD-C05 driven-overload exception. All source debt remains OPEN; generating this register closes none.

S1 attempted documentary closure on 2026-10-06 and was BLOCKED: SRC-01, SRC-20, SRC-30 and SRC-33 hosts are denied by the execution environment network policy and SRC-32 was not located (reference/sources/sp1200/ACCESS_RECORD.json, reference/sources/mpc3000/ACCESS_RECORD.json). No item changed state; no coefficient was guessed. S2 supplies unit evidence and freezes acceptance before S3/S4 fitting. S5 makes final product choices after comparison/listening. S2 can measure every output without selecting a shipping default; RD-P0-04 closes the physical topology before S3, while factory default stays G-07. Source priority labels are preserved. Any restriction/nonapplicability needs a written evidence-backed owner decision before dependent work, never an autonomous waiver.

## All P0 and P1 items
| ID / priority | Exact question | Evidence / resolving test | Affected block/decision | First closure owner / dependency |
|---|---|---|---|---|
| RD-P0-01 P0 | SP analog transfer functions: AA filter, ch 3–4 and 5–6 filters, mix path | Schematic values or measurement; CHAIN-EXP-019, CHAIN-EXP-002, CHAIN-EXP-004 | R3, R8, R9 are placeholders until closed | S1 documentary / S2 evidence; Readable SRC-01 or unit |
| RD-P0-02 P0 | SP gain structure: input sensitivity per gain, ADC full-scale volts, output volts for full scale, clip points | Measurement or schematic; CHAIN-EXP-005, CHAIN-EXP-019 | R0, R2, R5, R9 calibration | S1 documentary / S2 evidence; Unit |
| RD-P0-03 P0 | SP → MPC interstage calibration | RD-P0-02 + MPC full-scale volts; CHAIN-EXP-009, CHAIN-EXP-012 | R10 default | S1 documentary / S2 evidence; RD-P0-02, -06 |
| RD-P0-04 P0 | SP canonical output path and MIX OUT topology (what is summed, pre or post filter, contact mapping) | Schematic or measurement; CHAIN-EXP-004, CHAIN-EXP-019 | R8 selection; mono-sum mode | S1 documentary / S2 evidence; Unit or SRC-01 |
| RD-P0-05 P0 | MPC machine-domain behavior at unity: bit transparency, 18 → 16-bit rule, mixer scaling | Bit-level tests; CHAIN-EXP-008, CHAIN-EXP-010 | R13, R14 | S1 documentary / S2 evidence; Unit, S/PDIF source |
| RD-P0-06 P0 | MPC analog responses and levels: input chain, clip location, I/V gain, output filter, full-scale volts | Schematic extraction or measurement; CHAIN-EXP-020, CHAIN-EXP-009, CHAIN-EXP-010 | R11, R12, R15 | S1 documentary / S2 evidence; SRC-20 scan or unit |
| RD-P1-01 P1 | AD7541 datasheet figures, grade fitted, SAR timing and sample-and-hold aperture | Datasheet; EXP-019, -002; CHAIN-EXP-019, CHAIN-EXP-002 | Converter strategy | S1 documentary / S2 evidence; — |
| RD-P1-02 P1 | AK5328 datasheet: decimation response, group delay, full-scale input, overload behavior | Datasheet; EXP-009; CHAIN-EXP-009 | R12 | S1 documentary / S2 evidence; — |
| RD-P1-03 P1 | SM5841 datasheet: response, group delay, rounding, de-emphasis logic | Datasheet; EXP-010; CHAIN-EXP-010 | R15 | S1 documentary / S2 evidence; — |
| RD-P1-04 P1 | SP level-DAC: is maximum level unity; effect on resolution | EXP-003; CHAIN-EXP-003 | R6 | S1 documentary / S2 evidence; — |
| RD-P1-05 P1 | SP quantizer: encoding, rounding rule, offset, dither-like behavior | EXP-002; CHAIN-EXP-002 | R5 | S1 documentary / S2 evidence; Export route |
| RD-P1-06 P1 | SP noise and spur spectrum | EXP-006; CHAIN-EXP-006 | DEC-007 | S1 documentary / S2 evidence; — |
| RD-P1-07 P1 | MPC noise, THD, IMD vs level | EXP-010, -015; CHAIN-EXP-010, CHAIN-EXP-015 | DEC-006 | S1 documentary / S2 evidence; — |
| RD-P1-08 P1 | MPC main vs individual outputs | EXP-011; CHAIN-EXP-011 | R15 variants | S1 documentary / S2 evidence; — |
| RD-P1-09 P1 | Equivalence of SP-12 and SP-1200 analog and playback circuits | Schematic comparison; Schematic comparison | Confidence of CLM-008, -009 | S1 documentary / S2 evidence; SRC-01, -02 |
| RD-P1-10 P1 | Audio-relevant differences across SP-1200 revisions (1987, 1993, 1997, Rossum 2020/2021) | Service notes, ECOs, measurements; Service notes, ECOs, measurements | Revision table | S1 documentary / S2 evidence; — |
| RD-P1-11 P1 | SP multiplex slot skew and hold fraction | EXP-003, -007; CHAIN-EXP-003, CHAIN-EXP-007 | R7; DEC-005 | S1 documentary / S2 evidence; — |
| RD-P1-12 P1 | MPC output level meaning ("6 dBm"), full-scale volts, coupling poles | EXP-010, -020; CHAIN-EXP-010, CHAIN-EXP-020 | R15 | S1 documentary / S2 evidence; — |

## P2/P3 preserved

| ID | Question | Disposition |
|---|---|---|
| RD-P2-01 | SP tuning table and accumulator precision (extreme mode only) | DEFERRED; no corresponding product feature authorized |
| RD-P2-02 | Unit-to-unit tolerance | DEFERRED; no corresponding product feature authorized |
| RD-P2-03 | SSM2044 channel behavior with continuous program | DEFERRED; no corresponding product feature authorized |
| RD-P2-04 | AK5328 overload recovery dynamics | DEFERRED; no corresponding product feature authorized |
| RD-P2-05 | MPC de-emphasis line behavior with emphasized S/PDIF sources | DEFERRED; no corresponding product feature authorized |
| RD-P2-06 | Low-level linearity of both converter systems | DEFERRED; no corresponding product feature authorized |
| RD-P3-01 | Origin of the 27.5 kHz SP-12 specification figure | DEFERRED; no corresponding product feature authorized |
| RD-P3-02 | MPC3000 operating-system versions and limited-edition hardware differences | DEFERRED; no corresponding product feature authorized |
| RD-P3-03 | Documentary evidence for SP → MPC3000 resampling as period practice | DEFERRED; no corresponding product feature authorized |
| RD-P3-04 | MPC3000 pitch-interpolation algorithm | DEFERRED; no corresponding product feature authorized |

## Closure evidence schema

For each item retain ID/priority, exact question, OPEN/PARTIAL/CLOSED/NOT APPLICABLE WITH APPROVED SCOPE, unit/revision/route, source sheet/capture/hash, measurement uncertainty, unresolved remainder, affected requirements, decision and reviewer/date. Documentary filter extraction can close a documentary subclaim but cannot claim hardware validation. A complete source P0 question includes all its subparts; do not close a whole row with one convenient result. List all residual blockers in PROJECT_HANDOFF.
