# Sprint 05 report — Provisional SP→MPC software cascade, G-07S software product decision, listening-asset preparation (Track A: provisional, software only)

Contract: docs/sprint_prompts/SPRINT_05.md (planning V1, unchanged), entry gates amended by docs/EXECUTION_PLAN_V2.md (OWN-DEC-001). Owner inputs 2026-10-07 (EXECUTION_PLAN_V2 §9 item 6): OWN-DEC-009 (R10 interstage_level_db default 0.0 dB, OWNER-SET PROVISIONAL, NON-HISTORICAL), OWN-DEC-010 (G-07S software product path B), OWN-DEC-011 (cascade order SP → MPC; reverse research-only), OWN-DEC-012 (routes NONE_CH7_8 / MAIN_LR, linked dual mono PRODUCT ABSTRACTION, chain modes CASCADE default / SP_ONLY / MPC_ONLY / BOTH_MACHINE_BYPASSED latency-aligned, no drive macro, no wet/dry), OWN-DEC-013 (software-only listening preparation; hardware listening deferred). Executor: autonomous.

This report separates five things that the contract treats as one: SOFTWARE IMPLEMENTATION (§4, §6), SOFTWARE PRODUCT SELECTION (§4b), LISTENING-ASSET PREPARATION (§7), HUMAN LISTENING (§7b — NOT EXECUTED) and HARDWARE FIT (§10 — BLOCKED). Nothing here is measured, calibrated or validated against hardware. The interstage default is a software convention, not a historical level relationship.

## 1–2. Starting state

Starting commit eefdf8d (Sprint 4 milestone e8f6600 + hash back-fill). Branch `claude/autonomous-build`, tree clean. Sprint 1 PASS, Sprint 2 BLOCKED, Sprint 3 and 4 PASS WITH EXTERNAL VALIDATION PENDING, G-04 BLOCKED / DEFERRED EXTERNAL VALIDATION — all preserved. Immutable research and the eight contracts unchanged (integrity 5/5 before and after).

## 3. Scope mapping

| Contract permission | Repository path |
|---|---|
| Cascade composition / interstage / chain modes / product configuration | smlsp3000/reference/cascade.py, smlsp3000/reference/assets/product_config_track_a_v1.json, research_config_cascade_track_a_v1.json, smlsp3000/reference/assets.py (loaders); core entry points exposed in sp1200.py (1.0.4) and mpc3000.py (1.0.2), outputs bit-identical |
| Validation | smlsp3000/validation/cascade_track_a.py → research/validation/cascade/{VAL-015,VAL-016}_software.json; tests/test_reference_cascade.py |
| Listening protocol assets | smlsp3000/listening/kit.py → research/listening/CHAIN-EXP-018/ (records committed; audio in `stimuli/` git-ignored, regenerable) |
| research/fit/cascade | NOT CREATED — no fit without hardware (Track B) |
| evidence/sprint_05 | product_decision.json, provenance.json, commands.json, scope_audit.json, logs |

## 4. Implementation (SOFTWARE IMPLEMENTATION)

- Composition (cascade-reference-impl-1.0.0): R1 host→proxy (×8) → SP core R2–R9 → R10 → MPC core R11–R15 → R16 proxy→host, all on one proxy grid through the engines' public `core_channel` entry points (no DSP duplicated, no second R1/R16 pair). The cascade owns a host-input peak meter; machine meters are reported per stage.
- R10: `interstage_level_db` → exact linear gain 10^(dB/20); owner default 0.0 dB; research range −60 … +24 dB (outside → INVALID_CONFIGURATION INTERSTAGE_RANGE). No normalization, no saturation; the MPC 18-bit converter clamp is the only overload mechanism.
- Chain modes: CASCADE (product default), SP_ONLY, MPC_ONLY, BOTH_MACHINE_BYPASSED. A bypassed machine is replaced by an exact integer delay equal to its core delay, so every mode reports the same host latency (310 host samples at 48 kHz with the default kernels: R1 384 + SP core 64 + MPC core 1648 + R16 384 proxy samples = 2480 / 8). R10 is not applied in single-machine modes. Reverse order (MPC → SP) exists only behind the research switch `reverse_order_research` (default off; CHAIN-DEC-013 informational).
- Stereo: SP stage linked dual mono (PRODUCT ABSTRACTION) → MPC true stereo; parameters linked across channels.
- Parameters: `CascadeProductParameters(sp, mpc, interstage_level_db, chain_mode)`; `CascadePreparedInfo` (latency, delay breakdown, versions); prepare/reset/process/drain/latency/meters.
- Deliberately not implemented: R0 volts, R16 output trim, plugin bypass, drive macro, wet/dry, any hardware response, overload recovery, individual/headphone routes, production engine.

## 4b. Software product selection (SOFTWARE PRODUCT SELECTION — G-07S)

evidence/sprint_05/product_decision.json records the OWNER-APPROVED SOFTWARE PRODUCT DECISION: path B (full implemented sample path); SP route NONE_CH7_8; MPC route MAIN_LR; linked dual mono as PRODUCT ABSTRACTION; cascade order SP → MPC; chain-mode default CASCADE with the three research modes; no drive macro; no wet/dry; candidate controls only from docs/PARAMETERS.md. This is a software decision made without listening data or hardware; G-07H (hardware-informed confirmation) is BLOCKED / DEFERRED. The product configuration record `sml-sp3000-product-config-track-a` v1 (sha256 a2656d0f…) carries the claim boundary text of OWN-DEC-001.

## 5. Commands (repository root; Python 3.13.16, numpy 2.5.3)

| ID | Command | Exit | Log |
|---|---|---|---|
| CMD-02 | `python3 tools/check_repo_integrity.py` | 0 | evidence/sprint_05/integrity_run.log |
| CMD-11 | `python3 -m smlsp3000.runner validate-sprint5 --out research/validation` | 0 | evidence/sprint_05/validate_sprint5_run.log (≈32 s; VAL-015 PASS, VAL-016 PASS) |
| CMD-12 | `python3 -m smlsp3000.runner listening-kit --out research/listening/CHAIN-EXP-018` | 0 | evidence/sprint_05/listening_kit_run.log (16 stimulus files; ≈96 s) |
| CMD-07/CMD-10 (regression) | validate-sprint3 and validate-sprint4 into scratch, compared with committed records | 0 | evidence/sprint_05/prior_sprints_regression_run.log (ALL_IDENTICAL True) |
| CMD-09 | `python3 -m smlsp3000.runner scope-audit --out evidence/sprint_05/scope_audit.json` | 0 | evidence/sprint_05/scope_audit_run.log |
| CMD-05 | `python3 -m unittest discover -s tests -t . -v` | 0 | evidence/sprint_05/unittest_run.log (52 tests OK) |
| CMD-04 | `verify-manifest` on research/validation/cascade and research/listening/CHAIN-EXP-018 | 0 | all OK |

## 6. Tests and results (SOFTWARE IMPLEMENTATION)

| Check | Software (Track A) | Hardware-fit (Track B) | Evidence |
|---|---|---|---|
| VAL-015 / REQ-015 identities | PASS: SP_ONLY bit-identical to the standalone SP engine; MPC_ONLY bit-identical to the standalone MPC engine fed the input delayed by the SP-core delay (same 44.1 kHz sampling phase); CASCADE bit-identical to the explicit manual composition; CASCADE differs from both single-machine modes; latency 310 in all four modes and equal to SP + MPC core delays + R1/R16; BOTH_MACHINE_BYPASSED round trip within the kernel bound (4.8e-6 vs 1.7e-4); determinism and block-partition invariance | BLOCKED (CHAIN-EXP-012) | research/validation/cascade/VAL-015_software.json |
| VAL-015 interstage | PASS: −60 / −20 / +6 dB exact 10^(dB/20) within 1.1e-15 relative (quantization-bypass diagnostic); 0 dB level-neutral on a 0.001 tone — output 0.00099757 vs expected 0.00099757 with the implemented SP hold droop (−0.021 dB at 1 kHz) and kernel responses, error 3.9e-10 vs bound 1.6e-7; +20 dB reaches the 18-bit converter clamp (7 680 clip events, 3 840 storage clamps; SP not clipped; max output 1.074 = clamped code through reconstruction overshoot); −61 / +25 dB rejected INTERSTAGE_RANGE; no hidden normalization or saturation | BLOCKED (CHAIN-EXP-005/009/012) | same record |
| VAL-015 stereo | PASS: stereo equals independent mono per channel; silent channel exactly zero; left unaffected by right; equal inputs identical; reset reproduces | BLOCKED | same record |
| VAL-016 / REQ-016 | PASS (software): product configuration verified structurally against the record and the engines (path B, routes populated, reserved routes rejected, chain-mode default CASCADE, reverse order off by default, no drive/wet-dry); listening kit present with manifest; CHAIN-EXP-013/014 software derivatives INFORMATIONAL | BLOCKED (G-07H) | research/validation/cascade/VAL-016_software.json |
| VAL-018 scope audit | PASS (covers cascade.py, listening/kit.py) | N/A | evidence/sprint_05/scope_audit.json |
| Regression | Sprint 1 (18) + Sprint 3 (17) + Sprint 4 (10) + Sprint 5 (7) = 52 tests OK; Sprint 3 and Sprint 4 validation re-runs numerically identical (render-record `machine` key added in Sprint 4 ignored by design) | — | evidence/sprint_05/unittest_run.log, prior_sprints_regression_run.log |

Tolerance policy: identities bit-exact; float64 gain identities 1e-9; line bounds from the kernel design (`line_amplitude_bound_relative` × input amplitude, with the exact implemented R1/SP hold/R12/R15/R16 responses in the expectation); quantized-line deviations INFORMATIONAL. Nothing was loosened; no threshold was invented.

Test-integrity notes: (1) the first MPC_ONLY identity check compared outputs with mismatched alignment (the cascade alignment removes the SP-core delay) and then truncated the tail of the delayed comparison input — both were check-design errors, corrected before any record was written; (2) moving the host-input peak meter into the SP/MPC `core_channel` changed the Sprint 3/4 render-record meters — reverted: the standalone engines keep host-input metering, the cascade tracks its own `host_input_peak`; (3) the first 0 dB neutrality expectation omitted the implemented SP zero-order-hold droop — the expectation now includes sinc(f/fsp) and the kernels. Known reporting gap: inside the cascade the machine-level `peak_input_normalized` meters read 0 (the host peak is reported at the cascade level); recorded, not hidden.

## 7. Listening-asset preparation (LISTENING-ASSET PREPARATION — CHAIN-EXP-018 software arm)

research/listening/CHAIN-EXP-018: four synthetic analytic excerpts (bright multitone, dense pink multitone, transient bursts, sub-heavy quiet tail; 2.2 s, 48 kHz stereo, 24-bit) × four conditions (BYPASS, REFERENCE_B = cascade path B, SIMPLIFIED_SP_ONLY, SIMPLIFIED_MPC_ONLY) = 16 LISTENING STIMULUS files, RMS-matched to BYPASS, blinded filenames, blind manifest, sealed key, result-form template (criterion field "NONE DEFINED"), generation record with per-file sha256, manifest.sha256. Seed 20261007; deterministic. Audio (9.7 MB) is not committed (`.gitignore` `research/listening/**/stimuli/`) and regenerates bit-exactly from CMD-12; hashes are the record. A HARDWARE condition slot is reserved and empty. Coverage limit: no approved music material exists in the repository; synthetic material does not stand in for programme material.

## 7b. Human listening (NOT EXECUTED)

No listener, score, count, threshold or pass criterion exists. The result form is empty. Human listening is EXTERNAL / OWNER PENDING; the owner defines the criterion before any score is recorded. Hardware listening (G-07H) is BLOCKED.

## 8. Artifacts

19 files hashed in evidence/sprint_05/provenance.json; product config sha256 a2656d0f…, cascade research config sha256 81871c8b…. research/validation/cascade ≈ 32 KB; research/listening/CHAIN-EXP-018 records ≈ 44 KB; no audio committed.

## 9. Provisional behaviour (all UNVALIDATED AGAINST HARDWARE)

R10 0.0 dB default (NON-HISTORICAL); converter clamp as the only overload; proxy ×8 and kernel sizes (ESTIMATE pending G-08); latency-aligned research modes (software choice); path B; routes NONE_CH7_8 / MAIN_LR; linked dual mono abstraction; volts UNSET.

INFORMATIONAL software derivatives (31-tone multitone at 48 kHz; SIMULATION of the implementation only, no hardware meaning): DRY rms −18.34 dB / crest 12.07 dB; MPC alone identical rms and crest, residual −82.8 dB re input (16-bit storage quantization); SP alone rms −18.52 dB / crest 12.27 dB; SP→MPC rms −18.53 dB / crest 12.21 dB, 16 kHz tone −8.4 dB (SP fold-back/hold droop); MPC→SP (research only) rms −18.52 dB / crest 12.63 dB.

## 10. Hardware-dependent unresolved items (HARDWARE FIT — BLOCKED)

Interstage level in volts (RD-P0-02/03/06; CHAIN-EXP-005/009/012); MPC input stage behaviour above the converter clamp (overload recovery; AUD-C05); whether SP output coloration drives the MPC differently from a clean source (CHAIN-EXP-012); order asymmetry on hardware (CHAIN-EXP-013); path A/B/C audibility on hardware (CHAIN-EXP-014); G-07H; everything listed in SPRINT_03/04 reports §10. G-04/G-05/G-06 unchanged.

## 11. Assumptions

0 dB maps SP normalized full scale to MPC normalized full scale because no measured relationship exists and no other number is defensible (OWN-DEC-009). Constant-delay compensation in research modes is a software convenience with no hardware counterpart. Synthetic listening material is a coverage decision of the executor under OWN-DEC-013, not a claim of representativeness.

## 12. Deviations

Contract items that require hardware (interstage calibration in volts, hardware listening, hardware-informed product selection, CHAIN-EXP-012/013/014/018 hardware arms) are executed only in their provisional software form under OWN-DEC-009..013. research/fit/cascade not created. No listener data. The suggested commit title "Sprint 5: Integrate provisional SP→MPC software cascade" is applied in the repository's lowercase convention.

## 13. Documentation updated

ENGINE_SPEC, ARCHITECTURE, PARAMETERS, CONFIDENCE, DECISIONS (OWN-DEC-009..013, ENG-DEC-019), EXPERIMENT_PLAN, VALIDATION_PLAN, DSP_CHANGELOG, ACCEPTANCE_MATRIX.md/.csv (rows 015/016), SPRINT_PLAN, EXECUTION_PLAN_V2 (§9 item 6 RECEIVED), GATE_REGISTER (G-07S), LISTENING_TEST_PLAN (software arm PREPARED), BUILD_COMMANDS (CMD-11, CMD-12), docs/README, PROJECT_HANDOFF, this report. Immutable research and contracts untouched. Previous sprint reports untouched.

## 14. Confidence / status / acceptance changes

No claim status changed. Acceptance: software cells PASS for REQ-015/016; human listening PENDING; hardware-fit cells BLOCKED.

## 15. Verdict

Software acceptance: PASS (composition, interstage, chain modes, stereo, product configuration, listening assets, regression). Human listening: NOT EXECUTED. Hardware-fit acceptance: BLOCKED.

Sprint verdict: **PASS WITH EXTERNAL VALIDATION PENDING** (named external gates: human listening under an owner-defined criterion; G-07H; G-04, Track B — CHAIN-EXP-012/013/014/018 hardware arms, G-05/G-06).

## 16. Continuation gate

Sprint 6 (production engine, numerical optimization) requires G-08 owner budgets that the repository does not contain: proxy oversampling / kernel convergence budget, cross-rate and precision tolerances, reference-vs-production numerical budget, block size and input domain, CPU and latency budgets, parameter IDs/ranges/defaults/smoothing and state schema version, non-finite input policy, production stack. STOP before Sprint 6 (EXECUTION_PLAN_V2 §8/§9 item 7).

## 17. Ending commit

Milestone commit: recorded by the follow-up hash back-fill commit.
