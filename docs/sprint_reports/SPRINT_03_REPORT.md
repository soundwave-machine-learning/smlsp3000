# Sprint 03 report — Calibrated SP reference and stereo skeleton validation (Track A: provisional, software only)

Contract: docs/sprint_prompts/SPRINT_03.md (planning V1, unchanged), entry gates amended by docs/EXECUTION_PLAN_V2.md (OWN-DEC-001, owner-approved 2026-10-07). Owner inputs: OWN-DEC-002 (R3 INACTIVE), OWN-DEC-003 (quantizer ROUND_NEAREST default / FLOOR alternate), OWN-DEC-004 (route NONE_CH7_8 only). Date: 2026-10-07. Executor: autonomous.

The contract title says "calibrated"; nothing in this sprint is calibrated against hardware. Every artifact is SIMULATION or software and is tagged UNVALIDATED AGAINST HARDWARE.

## 1–2. Starting state

Starting commit 8257c2d (governance V2). Branch `claude/autonomous-build`, tree clean. Sprint 1 PASS (fbd1fac) and Sprint 2 BLOCKED (1c0fe89) preserved; G-04 BLOCKED / DEFERRED EXTERNAL VALIDATION unchanged.

## 3. Scope mapping

| Contract permission | Repository path |
|---|---|
| Offline reference core / SP modules / tests | smlsp3000/reference/{kernels,streaming,scheduler,assets,sp1200,render}.py, smlsp3000/validation/{measure,sp1200_track_a,scope_audit}.py, tests/test_reference_sp1200.py |
| Machine asset candidates with provenance | smlsp3000/reference/assets/sp1200_provisional_v1.json (asset sp1200-track-a-provisional v1, model sp1200-provisional-1.0.0), research_config_sp_track_a_v1.json |
| research/fit/sp1200 | NOT CREATED — no fit without hardware (Track B) |
| research/validation/sp1200, research/validation/stereo | research/validation/sp1200/{digital,input,output,calibration}/, research/validation/stereo/ |
| evidence/sprint_03 | evidence/sprint_03/ (scope_audit.json, provenance.json, commands.json, logs) |
| CHAIN-EXP-017 | research/sim/CHAIN-EXP-017/ |

## 4. Implementation completed

- Schemas: ASSET_VALUE (value, unit, evidence_status, substitute_kind, hardware_validation, sources, claims, decision, replaced_by), MACHINE_ASSET with model_version/track, VALIDATION_RECORD; `validate_machine_asset` rejects any untagged "magic" value.
- Provisional SP asset: rate 20 000 000/768 Hz (PROVISIONAL), 12-bit linear (VERIFIED format), code range −2048..2047 with presumed clamp, ROUND_NEAREST default (owner), offset 0 (ESTIMATE), gain steps 0/+20/+40 dB (STRONGLY SUPPORTED), R2 analog clamp INACTIVE, R3 INACTIVE, hold fraction 1.0 (PROVISIONAL), route table (NONE_CH7_8 POPULATED; FIXED_CH5_6 / FIXED_CH3_4 / MIX_OUT / unfiltered contacts NOT POPULATED), R9 gain 1.0 normalized, coupling INACTIVE, volts UNSET, slot skew 4.8 µs research-only.
- Reference engine (R1–R9, R16): polyphase host→proxy (×8) and decimation with windowed-sinc low-pass; exact rational scheduler; Kaiser-sinc sampling; quantizer rule registry (ROUND_NEAREST = ⌊r+½⌋, FLOOR = ⌊r⌋) with clamp and clip meter; R6 identity; full-period hold rendered band-limited to the proxy Nyquist (hold images preserved, no hard-edge aliasing); route registry; prepare/reset/process/drain/latency/meters/taps; linked dual mono with shared instants and per-channel state; research-only playback slot skew and capture offset switches (both off). Integer latency 104 host samples at the default kernels. Physical calibration mode returns INVALID_CONFIGURATION (volts UNSET).
- Offline renderer with provenance record (asset identity, research-config hash, input/output hashes, software, commit, model implementation version 1.0.2).
- Validation runner for the software cells of VAL-008/009/010/011/017; VAL-018 scope audit; CHAIN-EXP-017 runner; runner CLI entries.
- Deliberately not implemented: R0 volts, R3 response, R8 ch 3–6 / MIX OUT responses, R9 coupling, any MPC block (R10–R15), production engine, UI, presets, hold fractions other than 1.0.

## 5. Commands run (repository root; Python 3.13.16, numpy 2.5.3)

| ID | Command | Exit | Log |
|---|---|---|---|
| CMD-02 | `python3 tools/check_repo_integrity.py` | 0 | evidence/sprint_03/integrity_run.log |
| CMD-07 | `python3 -m smlsp3000.runner validate-sprint3 --out research/validation` | 0 | evidence/sprint_03/validate_sprint3_run.log (≈21 s) |
| CMD-08 | `python3 -m smlsp3000.runner run CHAIN-EXP-017 --out research/sim/CHAIN-EXP-017` | 0 | evidence/sprint_03/exp017_run.log |
| CMD-09 | `python3 -m smlsp3000.runner scope-audit --out evidence/sprint_03/scope_audit.json` | 0 | evidence/sprint_03/scope_audit_run.log |
| CMD-05 | `python3 -m unittest discover -s tests -t . -v` | 0 | evidence/sprint_03/unittest_run.log (35 tests OK, ≈111 s) |
| CMD-04 | `python3 -m smlsp3000.runner verify-manifest <dir>` for the six artifact directories | 0 | all OK |

## 6. Tests and results

| Check | Software (Track A) | Hardware-fit (Track B) | Evidence |
|---|---|---|---|
| VAL-008 / REQ-008 | PASS: rate ratios exact for 6 hosts; both rules exact at every code boundary and tie; ramp covers 4096 codes monotonically with clamp (both rules); bit-exact repeat and block-partition invariance (both rules) | BLOCKED | research/validation/sp1200/digital/VAL-008_software.json |
| VAL-009 / REQ-009 | PASS (R3 INACTIVE): 15 kHz / 14 kHz at 48 kHz fold to 11041.67 / 12041.67 Hz; all host-band lines within bound; SP-domain fold-back amplitude within bound | BLOCKED | research/validation/sp1200/input/VAL-009_software.json |
| VAL-010 / REQ-010 | PASS (NONE_CH7_8): every host-band line within the kernel bound for 1/5/10/12 kHz at 96 kHz; first image at fsp − f; droop vs closed form within bound; non-populated routes rejected | BLOCKED | research/validation/sp1200/output/VAL-010_software.json |
| VAL-011 / REQ-011 | PASS (normalized): +20/+40 dB ratios within 1e-9; −6 dB trim exact; clamp 2047/−2048 with clip count; physical mode rejected (ASSET_VALUE_UNSET) | BLOCKED | research/validation/sp1200/calibration/VAL-011_software.json |
| VAL-017 / REQ-017 | PASS: L=R identical, stereo = independent mono, anti-phase, silent channel exactly zero, reset reproduces; research slot skew measured 4.80006 µs (error 6e-10 s, bound 9.9e-9 s); both research offsets off in product config | BLOCKED (CHAIN-EXP-007) | research/validation/stereo/VAL-017_software.json |
| VAL-018 / REQ-018 | PASS: no pitch/tuning parameter; registries contain only INACTIVE / NONE_CH7_8 / two quantizer rules; no forbidden tokens in reference code | N/A | evidence/sprint_03/scope_audit.json |
| Unit/regression | 35 tests OK (18 inherited + 17 new) | — | evidence/sprint_03/unittest_run.log |

Tolerance policy: identities are bit-exact; spectral-line bounds are `input amplitude × kernel_properties.line_amplitude_bound_relative` (3.1e-5 for 0.5 amplitude; from the Kaiser design attenuations and the hold-step truncation residual); float64 identities use 1e-9 relative. Quantizer-active line deviations (up to 3.6e-5, i.e. 12-bit quantization distortion) are recorded INFORMATIONAL, not bounded, and no bound was loosened.

Test-integrity notes (defects found and fixed in the implementation or in check design, never by loosening): (1) machine samples near stream start indexed proxy history at negative offsets, which numpy wrapped — exposed as a 1-code partition difference under ROUND_NEAREST at a tie; fixed by zero-padding history before t = 0 (impl 1.0.1) and adding invariant assertions. (2) The low-pass docstring claimed sum(h) == 1 exactly; corrected to a stated float64 bound with centre-tap residual folding (impl 1.0.2). (3) The research slot-skew switch originally shifted sampling and hold together (a capture offset); split into playback slot skew (hold edges) and capture offset per docs/ARCHITECTURE.md (ENG-DEC-017). Check-design defects: dict key types in the rate-ratio comparison; an ill-posed "strongest line above the fundamental" search (replaced by model-argmax with 8× zero-padded FFT); the chirp's own spread in CHAIN-EXP-017 frames; docstring tokens in the scope regex; the phase sign convention in the skew measurement.

## 7. Experiments and measurements (SIMULATION)

CHAIN-EXP-017: INFORMATIONAL, pattern consistent in 15/15 frames (4–12 kHz: strongest non-fundamental line at fsp − f; 13.1–20 kHz: strongest line at the fold fsp − f). Never evidence about the SP-1200.

| Quantity | Value |
|---|---|
| Hold droop 5 / 10 / 12 kHz (hold only, closed form −0.533 / −2.220 / −3.279 dB) | −0.5332 / −2.2196 / −3.2793 dB (diff ≤ 6.5e-6 dB; bound ≈ 7e-4 dB) |
| Worst host-band line error, linear (quantizer bypass) | 7.8e-7 (bound 3.1e-5) |
| Linear residual after removing all modelled lines | ≈ −140 dB re input |
| Quantizer-active residual (12-bit) | ≈ −71 dB re input (0.5 amplitude) |
| Research playback slot skew | 4.80006 µs measured vs 4.8 µs configured |
| Implementation latency | 104 host samples (exact integer) |

## 8. Generated artifacts

32 files hashed in evidence/sprint_03/provenance.json (classes SIMULATION / IMPLEMENTATION); asset sha256 73b75aad…, research config sha256 4771a2e2…. research/validation ≈ 136 KB; research/sim/CHAIN-EXP-017 ≈ 120 KB. No audio committed.

## 9. Provisional behaviour (all UNVALIDATED AGAINST HARDWARE)

SP rate 20e6/768; ROUND_NEAREST default (FLOOR alternate); offset 0; code clamp; R3 INACTIVE; full-period hold; NONE_CH7_8 identity route; normalized gains with analog clamp INACTIVE; volts UNSET; proxy ×8 and kernel sizes (IMPLEMENTATION, ESTIMATE pending G-08); research slot skew 4.8 µs.

## 10. Hardware-dependent unresolved items

Exact SP rate (CHAIN-EXP-001); encoding/rounding/offset/clamp (CHAIN-EXP-002); hold fraction/droop (CHAIN-EXP-003); ch 3–6 responses, contacts, MIX OUT (CHAIN-EXP-004/019); FS volts, gain curve, clip (CHAIN-EXP-005); noise/spurs (CHAIN-EXP-006); slot skew (CHAIN-EXP-007); AA response (RD-P0-01). All P0/P1 OPEN. G-04/G-05/G-06 unchanged.

## 11. Assumptions

Proxy ×8 and kernel parameters are implementation estimates to be converged at G-08; the band-limited hold rendering is an exact acquisition model of the proxy grid, not a reconstruction filter of the machine. Check bounds derive from kernel design formulas (Kaiser attenuation ≈ β/0.1102 + 8.7 dB).

## 12. Deviations

None from the contract's software scope under EXECUTION_PLAN_V2. research/fit/sp1200 not created (no fit possible). Contract work items 2 and 3 ("populate R2/R3 with evidence-constrained gains, AA complex response, measured clip boundaries"; "measured R7 hold"; "ch5/ch3 responses") are executed only in their provisional/placeholder form per OWN-DEC-002/004; their hardware-fit content is BLOCKED.

## 13. Documentation updated

ENGINE_SPEC, ARCHITECTURE, PARAMETERS, CONFIDENCE, DECISIONS (OWN-DEC-002/003/004, ENG-DEC-016/017), EXPERIMENT_PLAN, VALIDATION_PLAN, DSP_CHANGELOG, ACCEPTANCE_MATRIX.md/.csv (rows 008/009/010/011/017/018 software cells and state), SPRINT_PLAN, EXECUTION_PLAN_V2 (§9 inputs received), BUILD_COMMANDS (CMD-07/08/09), docs/README, PROJECT_HANDOFF, this report. Immutable research and contracts untouched (integrity 5/5).

## 14. Confidence / status changes

No claim status changed. Experiments: CHAIN-EXP-017 EXECUTED (INFORMATIONAL). Acceptance: software cells PASS for REQ-008/009/010/011/017/018; hardware-fit cells BLOCKED.

## 15. Verdict

Software acceptance: PASS (software implementation, numerical validation, deterministic regression, reference model). Hardware-fit acceptance: BLOCKED.

Sprint verdict: **PASS WITH EXTERNAL VALIDATION PENDING** — all Track A gates of the sprint pass with evidence; the specifically named external gate that remains is G-04 (Track B hardware fit: CHAIN-EXP-001..007/019 and G-05/G-06), which the owner's execution policy places outside the software track.

## 16. Continuation gate

Sprint 4 (MPC reference) requires owner inputs that are not hardware: R12 state, R15 state, R13 default reduction rule (EXECUTION_PLAN_V2 §9 item 5). STOP before Sprint 4 until supplied. Sprint 5 not started.

## 17. Ending commit

Recorded after the milestone commit exists (docs/PROJECT_HANDOFF.md; `git log claude/autonomous-build`).
