# Design decisions and unresolved selections

Revision: planning V1 · 2026-10-06

Status: DRAFT PLANNING CONTRACT. Documentation creation authorized; implementation and release not authorized.

## Source decisions retained; no hidden approval

| ID | Question | Research current decision | Status in engineering package | Reopen trigger |
|---|---|---|---|---|
| CHAIN-DEC-001 | Which product path (A, B, C)? | NOT CHOSEN. Reference model implements B as a superset with replaceable, bypassable blocks | SOURCE RESEARCH CHOICE; product approval not implied | Measurements complete |
| CHAIN-DEC-002 | SP machine-rate constant | 26 041.6667 Hz, provisional | SOURCE RESEARCH CHOICE; product approval not implied | Schematic or EXP-001 disagrees |
| CHAIN-DEC-003 | SP output path in the model | Output filter is a selected replaceable block; ch 1–2 excluded from MVP; canonical default UNDECIDED | SOURCE RESEARCH CHOICE; product approval not implied | Response data available |
| CHAIN-DEC-004 | SP pitch | Unity only in MVP; tuned round trip deferred as labeled extreme mode | SOURCE RESEARCH CHOICE; product approval not implied | Product direction |
| CHAIN-DEC-005 | SP stereo abstraction | Linked dual mono, shared sampling instants, identical coefficients; labeled PRODUCT ABSTRACTION | SOURCE RESEARCH CHOICE; product approval not implied | EXP-007 shows material skew worth offering |
| CHAIN-DEC-006 | MPC modeling level | Linear responses + 16-bit quantizer + explicit clamps, all placeholders | SOURCE RESEARCH CHOICE; product approval not implied | EXP-009/-010 show level-dependent residual |
| CHAIN-DEC-007 | Noise | OMITTED for both machines | SOURCE RESEARCH CHOICE; product approval not implied | EXP-006 shows audible, characteristic noise |
| CHAIN-DEC-008 | Jitter | REJECT | SOURCE RESEARCH CHOICE; product approval not implied | Measured sidebands attributable to clock |
| CHAIN-DEC-009 | Power supply | REJECT | SOURCE RESEARCH CHOICE; product approval not implied | Measured supply-correlated modulation |
| CHAIN-DEC-010 | Tolerance / channel randomization | Product REJECT; research DEFER | SOURCE RESEARCH CHOICE; product approval not implied | Second unit measured |
| CHAIN-DEC-011 | Converter strategy | SP: A + C. MPC: C. INL/DNL/glitch: F | SOURCE RESEARCH CHOICE; product approval not implied | Transfer measurements |
| CHAIN-DEC-012 | Meaning of a future drive control | No drive control defined. Only physically mapped candidates are SP input level and MPC record level | SOURCE RESEARCH CHOICE; product approval not implied | Product design phase |
| CHAIN-DEC-013 | Reverse order MPC→SP | Experiment only | SOURCE RESEARCH CHOICE; product approval not implied | EXP-013 result and product decision |
| CHAIN-DEC-014 | Interstage trim | Explicit calibrated variable; default UNSET | SOURCE RESEARCH CHOICE; product approval not implied | RD-P0-03 closed |
| CHAIN-DEC-015 | Dither in SP quantizer | None added | SOURCE RESEARCH CHOICE; product approval not implied | EXP-002 low-level test shows dither-like behavior |
| CHAIN-DEC-016 | Sampler workflow mechanisms | Exclude (memory limits, truncation, loops, envelopes, velocity, sequencer) | SOURCE RESEARCH CHOICE; product approval not implied | — |

## Engineering proposal decisions

| ID | Proposed decision | Authority / gate | Status |
|---|---|---|---|
| ENG-DEC-001 | Use the B reference superset for comparison; do not preselect shipping A/B/C | CHAIN-DEC-001; G-07 | PLANNED |
| ENG-DEC-002 | Explicit unfiltered ch7–8 research fixture when needed; no canonical factory route | CHAIN-DEC-003; RD-P0-04 | PLANNED; factory default UNKNOWN |
| ENG-DEC-003 | MPC main L/R as proposed shipping target; measure individual pair separately | §20; G-07 | PROPOSED, NOT OWNER SELECTED |
| ENG-DEC-004 | S1 framework/documentary work; S2 evidence/threshold gates before S3/S4 fitted references | §§40–43; G-04/05/06 | PLANNED |
| ENG-DEC-005 | Core shared by tests/offline/plugin; separate reference and production implementations sharing configuration meanings | §43; G-08 | PLANNED |
| ENG-DEC-006 | No stack/platform inherited from another project; freeze actual toolchain/target commands in S1 | G-01/G-09 | UNKNOWN until future execution |
| ENG-DEC-007 | Implement scheduler phase/history despite ideal sampler's physical-state notation | AUD-C08; REQ-019 | PLANNED interface clarification |
| ENG-DEC-008 | Same-build determinism and block invariance exact; cross-rate/platform and fit tolerances separate | §25/32/43; AUD-C09; G-06/G-08 | PLANNED; numeric tolerances UNKNOWN |
| ENG-DEC-009 | Hardware fidelity uses calibration scalar, listening uses logged excerpt RMS; preserve raw captures | AUD-C11; G-02/G-06 | PLANNED clarification |
| ENG-DEC-010 | Candidate delivery only in S8; no remote repository write, publishing, merging or installation authorized now | User planning-only | ACTIVE SCOPE CONSTRAINT |

## Open owner decisions

No formal selected product path, SP route, MPC route, stack/framework/license, OS/CPU/format/DAW matrix, executable repository/baseline, budget, proxy rate/kernel, parameter defaults/ranges, CPU/latency ceilings, fidelity/numeric tolerance, listening success criterion or release signing/distribution scope exists in these inputs. No value is manufactured to fill a template. G-01/G-06/G-07/G-08/G-09/G-10/G-11 place decisions before their dependent work.

When recording a decision, include exact options, supporting claims, rejected options, owner/date/authorization, affected requirement/parameter/module IDs, gate, superseded decision version, validation consequences and reopening rule. New evidence may revise confidence; it does not silently authorize material product change. Original source research stays historical. Native Windows/macOS/AU/VST3 support is not promised merely because this is an audio plugin.
