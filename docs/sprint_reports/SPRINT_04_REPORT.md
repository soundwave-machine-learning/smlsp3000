# Sprint 04 report — Calibrated MPC reference and path comparison (Track A: provisional, software only)

Contract: docs/sprint_prompts/SPRINT_04.md (planning V1, unchanged), entry gates amended by docs/EXECUTION_PLAN_V2.md (OWN-DEC-001). Owner inputs 2026-10-07: OWN-DEC-005 (R12/R15 TRANSPARENT), OWN-DEC-006 (record level ideal dB trim, 20 dB steps), OWN-DEC-007 (R13 ROUND_NEAREST default, TRUNCATION alternate), OWN-DEC-008 (MAIN_LR only, individual not populated, headphones excluded, normalized converter FS, volts UNSET). Executor: autonomous.

The contract title says "calibrated" and asks for "measured" behaviour; nothing in this sprint is measured or calibrated against hardware. Every artifact is SIMULATION or software and is tagged UNVALIDATED AGAINST HARDWARE. The contract's question "whether an undriven MPC contribution exists" cannot be answered by software; it stays UNKNOWN (MPC3K-CLM-020).

## 1–2. Starting state

Starting commit e3acb86 (Sprint 3 milestone 51b72d5). Branch `claude/autonomous-build`, tree clean. Sprint 1 PASS, Sprint 2 BLOCKED, Sprint 3 PASS WITH EXTERNAL VALIDATION PENDING, G-04 BLOCKED / DEFERRED EXTERNAL VALIDATION — all preserved.

## 3. Scope mapping

| Contract permission | Repository path |
|---|---|
| Offline MPC reference / modules / tests / assets | smlsp3000/reference/mpc3000.py, smlsp3000/reference/assets/mpc3000_provisional_v1.json, research_config_mpc_track_a_v1.json, smlsp3000/reference/kernels.py (TapTable, interpolation_kernel_response), smlsp3000/reference/render.py (machine dispatch), smlsp3000/reference/assets.py (machine selection), tests/test_reference_mpc3000.py |
| research/fit/mpc3000 | NOT CREATED — no fit without hardware (Track B) |
| research/validation/mpc3000 | research/validation/mpc3000/{digital,analog,path_comparison}/ |
| evidence/sprint_04 | evidence/sprint_04/ (provenance.json, commands.json, scope_audit.json, logs incl. sprint3_regression_run.log) |

## 4. Implementation

- Provisional MPC asset (model mpc3000-provisional-1.0.0): 44.1 kHz (VERIFIED value), 18-bit converter / 16-bit storage code domains (VERIFIED format), converter clamp (PROVISIONAL), ADC code representation ROUND_NEAREST_18BIT (ESTIMATE), reduction default ROUND_NEAREST, R14 IDENTITY_UNITY, input gain steps LO/MID/HI = 0/+20/+40 dB from printed sensitivities (ESTIMATE; sensitivity ≠ FS), record level IDEAL_DB_TRIM (ESTIMATE), R11 clamp/coupling INACTIVE, R12/R15 TRANSPARENT, de-emphasis OFF_UNASSERTED, R15 coupling INACTIVE, routes (MAIN_LR POPULATED; INDIVIDUAL_PAIR NOT POPULATED; HEADPHONES EXCLUDED), DAC FS normalized 1.0 (ESTIMATE), volts UNSET.
- Engine (mpc3000-reference-impl-1.0.1): R1 host→proxy (×8); R11 gain; R12 TRANSPARENT = ideal band limitation at 22.05 kHz (windowed-sinc, 62 host samples per side, β 9; implementation transition ≈ 2.2 kHz at 48 kHz, recorded as an ESTIMATE, not the AK5328's) + ideal sampling on the exact rational 44.1 kHz grid + 18-bit code (round-nearest) + converter clamp with meter; R13 registry ROUND_NEAREST (⌊c/4+½⌋) / TRUNCATION (⌊c/4⌋) with storage clamp and meter; R14 identity (stored = replayed), x4 re-expansion; R15 TRANSPARENT = ideal band-limited reconstruction onto the proxy grid (windowed-sinc, 128 machine samples per side, β 12; exact response recorded: flat to 21 kHz within 1e-5 dB, −0.005 dB at 21.5 kHz); route MAIN_LR identity; R16 proxy→host. True stereo (shared clock, per-channel state). prepare/reset/process/drain/latency/meters/taps; code-domain entry points reduce_codes / expand_codes; physical calibration → INVALID_CONFIGURATION. Reserved strategy slots ESTIMATE_FIR / DATASHEET_RESPONSE / MEASURED_RESPONSE exist by name only and are rejected.
- Latency: integer host samples (302 at 48 kHz, 441 at 96 kHz with the default kernels), documented as software kernel delay, never as converter latency.
- Shared improvement: exact per-residue interpolation tap tables (kernels.TapTable) for the MPC sampler/reconstruction and the SP sampler; SP outputs are bit-identical to Sprint 3 (sp1200-reference-impl-1.0.3; evidence/sprint_04/sprint3_regression_run.log), ≈10× faster.
- Deliberately not implemented: R10 interstage, output trim, cascade, any response of AK5328/SM5841/PCM69A/I-V/analog LP, de-emphasis, coupling, overload recovery, mixer arithmetic, individual/headphone routes, volts.

## 5. Commands (repository root; Python 3.13.16, numpy 2.5.3)

| ID | Command | Exit | Log |
|---|---|---|---|
| CMD-02 | `python3 tools/check_repo_integrity.py` | 0 | evidence/sprint_04/integrity_run.log |
| CMD-10 | `python3 -m smlsp3000.runner validate-sprint4 --out research/validation` | 0 | evidence/sprint_04/validate_sprint4_run.log (≈29 s) |
| CMD-07 (regression) | `python3 -m smlsp3000.runner validate-sprint3 --out <scratch>` + record comparison | 0 | evidence/sprint_04/sprint3_regression_run.log |
| CMD-09 | `python3 -m smlsp3000.runner scope-audit --out evidence/sprint_04/scope_audit.json` | 0 | evidence/sprint_04/scope_audit_run.log |
| CMD-05 | `python3 -m unittest discover -s tests -t . -v` | 0 | evidence/sprint_04/unittest_run.log (45 tests OK, ≈119 s) |
| CMD-04 | `verify-manifest` on the three MPC artifact directories | 0 | all OK |

## 6. Tests and results

| Check | Software (Track A) | Hardware-fit (Track B) | Evidence |
|---|---|---|---|
| VAL-012 / REQ-012 | PASS: ratios exact; 18/16 domains distinct; both rules exact over all 262 144 codes (zero, negatives, extremes); ROUND_NEAREST overflows two top codes → clamped and counted, TRUNCATION none; mean bias −0.125 / +0.375 LSB16; R14 x4 identity; digital-input patterns bit-exact; determinism and partition invariance for both rules; rules differ on program (49 % of stored codes) with identical 18-bit codes | BLOCKED (CHAIN-EXP-008) | research/validation/mpc3000/digital/VAL-012_software.json |
| VAL-013 / REQ-013 | PASS: in-band lines (1/10/15/20 kHz at 48 and 96 kHz) within bound — worst 1.2e-7 vs 4.7e-5; 23 kHz folds to 21.1 kHz with the band-limitation transition applied and ≤ 1e-9 left at 23 kHz; 30 kHz suppressed to 1.5e-13; LO/MID/HI = 1/10/100 and −12 dB trim within 1e-15; positive trim rejected; 18-bit clamp 131071/−131072 with meters; physical mode rejected; reserved strategies and de-emphasis ON rejected; true stereo identities bit-exact; reset reproducible | BLOCKED (CHAIN-EXP-009/010/015/020) | research/validation/mpc3000/analog/VAL-013_software.json |
| VAL-014 / REQ-014 | PASS: MAIN_LR prepares; INDIVIDUAL_PAIR rejected NOT POPULATED; HEADPHONES rejected EXCLUDED | BLOCKED (CHAIN-EXP-011) | research/validation/mpc3000/path_comparison/VAL-014_software.json |
| VAL-018 scope audit | PASS (now covers mpc3000.py) | N/A | evidence/sprint_04/scope_audit.json |
| Regression | Sprint 1 (18) + Sprint 3 (17) + Sprint 4 (10) = 45 tests OK; Sprint 3 validation re-run numerically identical | — | evidence/sprint_04/unittest_run.log, sprint3_regression_run.log |

Tolerance policy: identities bit-exact; line bounds = input amplitude × kernel line_amplitude_bound_relative (4.7e-5 at 0.5) with the exact implementation kernel responses (R1, R12 band limitation, R15 reconstruction, R16) in the expectation; float64 identities 1e-9; quantized-line deviations INFORMATIONAL (16-bit storage quantization, residual ≈ −95 dB re input at 0.5; the 30 kHz quantized case reports an all-zero output as a numerical floor artefact). Nothing was loosened.

Test-integrity notes: (1) the first R15 lookahead omitted the sampler's own lookahead and tripped an invariant assertion — fixed in the delay bookkeeping before any record was written; (2) the first expected-line model omitted the reconstruction kernel's passband response (−0.014 dB at 20 kHz with 32-sample half-width) — the kernel was lengthened to 128 and its exact response added to the expectation; (3) the first model did not predict above-Nyquist fold-back — corrected to |f − round(f/44100)·44100|; (4) the initial validation run exceeded 10 minutes because of per-sample Bessel evaluation — replaced by exact per-residue tap tables (bit-identical values).

## 7. Experiments and measurements

No software experiment is mandated for Sprint 4; CHAIN-EXP-008/009/010/011/015/020 remain NOT EXECUTED (hardware). Measurements above are SIMULATION of the implementation only.

## 8. Artifacts

17 files hashed in evidence/sprint_04/provenance.json; asset sha256 e100bec1…, research config sha256 125f0276…. research/validation/mpc3000 ≈ 100 KB; no audio committed.

## 9. Provisional behaviour (all UNVALIDATED AGAINST HARDWARE)

R11 ideal trim and 20 dB steps; R12 TRANSPARENT with implementation band limitation; 18-bit round-nearest code representation; R13 ROUND_NEAREST / TRUNCATION; R14 identity; R15 TRANSPARENT ideal reconstruction; de-emphasis OFF_UNASSERTED; MAIN_LR only; proxy ×8 and kernel sizes (ESTIMATE pending G-08); volts UNSET.

## 10. Hardware-dependent unresolved items

AK5328 decimation response/latency/FS/overload and recovery (RD-P1-02, AUD-C05); SM5841 response/group delay/rounding/de-emphasis (RD-P1-03); PCM69A/I-V/analog LP/coupling/FS volts and "6 dBm" meaning (RD-P0-06, RD-P1-12); 18→16 rule and mixer arithmetic (RD-P0-05); main vs individual equivalence (RD-P1-08); THD/IMD/noise (RD-P1-07); undriven coloration (MPC3K-CLM-020). G-04/G-05/G-06 unchanged.

## 11. Assumptions

The TRANSPARENT strategies are defined as ideal band limitation / ideal reconstruction with documented implementation kernels; the band limitation is the mathematically transparent choice for a 44.1 kHz sampler (an unfiltered sampler would alias SP images above 22.05 kHz, which no real ADC does and the research expects to be negligible). The 18-bit round-nearest representation and the reconstruction kernel parameters are implementation estimates.

## 12. Deviations

Contract work items 1–5 ("measured" curves, "as measured or documented" decimation, "measured arithmetic", "held-out loaded sounds", "THD/IMD/noise and driven recovery against held-out evidence") are executed only in their provisional software form under OWN-DEC-005..008; their hardware content is BLOCKED. research/fit/mpc3000 not created. No individual-route comparison beyond the route table (no data).

## 13. Documentation updated

ENGINE_SPEC, ARCHITECTURE, PARAMETERS, CONFIDENCE, DECISIONS (OWN-DEC-005/006/007/008, ENG-DEC-018), EXPERIMENT_PLAN, VALIDATION_PLAN, DSP_CHANGELOG, ACCEPTANCE_MATRIX.md/.csv (rows 012/013/014), SPRINT_PLAN, EXECUTION_PLAN_V2 (§9 item 5), BUILD_COMMANDS (CMD-10), docs/README, PROJECT_HANDOFF, this report. Immutable research and contracts untouched (integrity 5/5). Previous sprint reports untouched.

## 14. Confidence / status / acceptance changes

No claim status changed. Acceptance: software cells PASS for REQ-012/013/014; hardware-fit cells BLOCKED.

## 15. Verdict

Software acceptance: PASS (software implementation, numerical validation, deterministic regression, reference model, code-domain conversion). Hardware-fit acceptance: BLOCKED.

Sprint verdict: **PASS WITH EXTERNAL VALIDATION PENDING** (named external gate: G-04, Track B — CHAIN-EXP-008/009/010/011/015/020, G-05/G-06).

## 16. Continuation gate

Sprint 5 (cascade, interstage, G-07S) requires owner inputs that are not hardware: provisional interstage default in normalized units and the G-07S software product decision / listening protocol (EXECUTION_PLAN_V2 §9 item 6). STOP before Sprint 5.

## 17. Ending commit

Milestone commit `e8f66008e635b00969b7944277ba72ed6f7c43c9` on `claude/autonomous-build` (hash back-filled by the follow-up checkpoint commit).
