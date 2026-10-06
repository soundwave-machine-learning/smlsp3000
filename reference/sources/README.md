# reference/sources — documentary extraction (CHAIN-EXP-019 / CHAIN-EXP-020)

Status after Sprint 1 (2026-10-06): **NOT EXECUTED / BLOCKED**. Every source host needed for the targeted documentary closure (archive.org for SRC-01 and SRC-20, analog.com / mirrors for SRC-30, datasheet mirrors for SRC-33) is denied by the execution environment's network egress policy; SRC-32 (AK5328) was not located by search. See `sp1200/ACCESS_RECORD.json` and `mpc3000/ACCESS_RECORD.json` for the exact attempts.

No schematic transcription, refdes/net ledger or SPICE deck exists. No coefficient was guessed. All affected P0/P1 debt (docs/RESEARCH_DEBT.md) remains OPEN. Search-engine snippets encountered during the attempt are recorded as UNVERIFIED and are not promoted to any claim status.

When access exists, the extraction ledger format is: one JSON per circuit section with `sheet`, `refdes`, `value`, `tolerance`, `net_a`, `net_b`, `readability` (READ / AMBIGUOUS / UNKNOWN) and `source_id`; SPICE decks and AC results are labelled SIMULATION with simulator name/version and are never promoted to hardware evidence. Copyrighted scans are never committed.
