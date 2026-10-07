# Sprint 06 report — Production shared engine, parameter freeze and optimization (Track A: native production core, software only)

Contract: docs/sprint_prompts/SPRINT_06.md (planning V1, unchanged), entry gates amended by docs/EXECUTION_PLAN_V2.md (OWN-DEC-001). Owner inputs 2026-10-07 (EXECUTION_PLAN_V2 §9 item 7, G-08 software part): OWN-DEC-014 (C++20/CMake production stack), OWN-DEC-015 (float64 / 8x / checkpoint kernels frozen; optimise computation, not the model), OWN-DEC-016 (G-08 software numerical acceptance), OWN-DEC-017 (performance budget), OWN-DEC-018 (latency), OWN-DEC-019 (buffer/input safety), OWN-DEC-020 (parameters/state v1), OWN-DEC-021 (smoothing), OWN-DEC-022 (meter gap), OWN-DEC-023 (governance). Executor: autonomous. Recorded in evidence/sprint_06/owner_decisions_g08.json before any code.

This report separates IMPLEMENTATION ACCEPTANCE (the native core agrees with the accepted Python reference under owner-set limits; §6–§9) from PRODUCTION / NATIVE RELEASE READINESS (Windows NOT RUN; no wrapper; §10, §16) and from HARDWARE FIT (BLOCKED). Nothing here is measured, calibrated or validated against hardware; the reference remains UNVALIDATED AGAINST HARDWARE and so is everything that agrees with it.

## 1–2. Starting state

Starting commit 4f4679ac1f24f24855390a37530956697fabb396 (Sprint 5 milestone 69d64a0 + checkpoint). Branch `claude/autonomous-build`, tree clean, no intervening commits, `origin/main` untouched at 3b53a6b. Sprint 1 PASS, Sprint 2 BLOCKED, Sprints 3–5 PASS WITH EXTERNAL VALIDATION PENDING, G-04/G-07H BLOCKED — all preserved. Inherited regression before native work: integrity 5/5, 52 tests OK, Sprint 3/4/5 validation re-runs numerically identical (evidence/sprint_06/inherited_regression_run.log; only `model_implementation_version` label strings differed from the committed records).

## 3. Scope mapping

| Contract permission | Repository path |
|---|---|
| Shared production engine | native/include/smlsp3000/*.hpp, native/src/*.cpp (numerics, kernels, streaming, scheduler, sp_core, mpc_core, engine); generated native/generated/track_a_assets_v1.hpp from tools/gen_native_assets.py |
| Offline renderer / test executable / benchmarks | native/tools/smlsp3000_native.cpp (render, info, dump-kernels, bench, state-load); native/tests/selftest.cpp (ctest); smlsp3000/native/driver.py |
| Config/state | smlsp3000/reference/assets/product_controls_v1.json (controls v1); native state v1 (engine.cpp) |
| research/validation rate/alias/reference comparisons | smlsp3000/validation/{fixtures,production_track_a}.py → research/validation/rate_block/ (VAL-019), implementation_alias/ (VAL-020), reference_production/ (VAL-021); evidence/sprint_06/state_parameter/ (VAL-022) |
| evidence/sprint_06 | preflight, owner_decisions_g08, parameter_resolution, fixture_freeze, build_record, native_build/selftest logs, inherited/instrumentation regression logs, validate_sprint6 logs, benchmark/, scope_audit, provenance, commands |
| Reference instrumentation (audio unchanged) | smlsp3000/reference/{sp1200 1.0.5, mpc3000 1.0.3, cascade 1.0.1}: core-input peak meters; cascade machine `peak_input_normalized` marked UNAVAILABLE_IN_CASCADE |

## 4. Implementation

- **Native core** (smlsp3000-native-core-1.0.0; C++20; no dependencies; no I/O; no allocation/locks/logging in process()): the reference composition R1 → SP core (R2–R9) → R10 → MPC core (R11–R15) → R16 on the 8x proxy grid with the checkpoint kernels (R1/R16 48 lobes β 9; SP sampler/hold 4 host samples β 12; R12 62 host samples β 9; R15 reconstruction 128 machine samples β 12), the exact rational schedulers (SP 20 MHz/768, MPC 44.1 kHz), the implemented quantizer rules (⌊r+½⌋ ties toward +∞; FLOOR; R13 ⌊c/4+½⌋ / ⌊c/4⌋), code endpoints and clamps, x4 re-expansion, chain modes with aligned delays, R10. Arithmetic contract (ENG-DEC-020): products and sums rounded separately (`-ffp-contract=off`, no fast-math), FIR accumulation in numpy's pairwise order, kernels generated from the numpy formulas (i0 Chebyshev port, sinc, Kaiser).
- **Composed operator tables** (ENG-DEC-021, production path): (sampler ∘ R12 band limitation) per residue and (R16 decimation ∘ R15 reconstruction) per host phase class — the same linear operators, a different rounding order, ≈ 8× fewer multiply-adds. The straightforward reference-order evaluation is retained (`exact_reference_order`) and validated too.
- **Controls v1 / smoothing / events** (OWN-DEC-020/021, ENG-DEC-023): six frozen controls; 10 ms linear-in-dB ramps advanced per sample of their own clock (proxy or host); sample-indexed events mapped to the stage where the host sample arrives (R2: m·L + R1 delay; R10/R11: + SP core delay; trim/bypass: host sample m); discrete switches at the mapped sample; redundant retarget keeps the trajectory; reset snaps.
- **Output trim**, static **plugin_bypass** (latency-aligned dry selector; chain keeps running), **meters** (host input peak, SP/MPC core-input proxy peaks, SP clip, MPC 18-bit clip, 16-bit clamp, output peak, non-finite count, faults, rejected events), **safety** (NaN/Inf → 0 + counter; over-range passes to the converter clamps; internal non-finite → silenced chunk, latched fault, cleared signal state), **state v1** (schema 1; controls + identities; explicit rejections; no migrations).
- **Parameter resolution** (evidence/sprint_06/parameter_resolution.json): existing identifiers kept; `output_trim_db` and `plugin_bypass` new; `mpc_record_level_db` mathematically redundant with `interstage_level_db` in the implemented model → kept internal at 0 dB (no second control for the same gain). Research-only SP offsets (slot skew, capture offset) not ported (prepare rejects them).
- **Not implemented**: plugin wrapper/host integration, bypass transitions, GUI, presets, installation, Windows build, R0 volts, any hardware response.

## 5. Commands (repository root; Python 3.13.16, numpy 2.5.3, GCC 13.3.0, CMake 3.28.3, Ninja)

| ID | Command | Exit | Log |
|---|---|---|---|
| CMD-02 | `python3 tools/check_repo_integrity.py` | 0 | evidence/sprint_06/integrity_run.log |
| CMD-13 | `cmake -S native -B native/build -G Ninja -DCMAKE_BUILD_TYPE=Release && cmake --build native/build` | 0 | evidence/sprint_06/native_build.log; build_record.json (`-O2 -DNDEBUG -ffp-contract=off -fno-fast-math -fexcess-precision=standard`, generic x86-64) |
| CMD-14 | `ctest` in native/build | 0 | evidence/sprint_06/native_selftest.log (31 cases PASS; detail log) |
| CMD-15 | `python3 -m smlsp3000.runner validate-sprint6 --out research/validation --evidence evidence/sprint_06` (+ `--only VAL-019` re-run after the analysis-tool correction) | 0 | evidence/sprint_06/validate_sprint6_run.log (≈7 min), validate_sprint6_val019_rerun.log |
| CMD-16 | `python3 -m smlsp3000.runner native-bench --out evidence/sprint_06/benchmark --seconds 5 --trials 3 --warmup 1` | 0 | evidence/sprint_06/native_bench_run.log; benchmark/ |
| CMD-17 | `python3 tools/gen_native_assets.py --check` | 0 | tests/test_native_assets.py |
| CMD-09 | `python3 -m smlsp3000.runner scope-audit --out evidence/sprint_06/scope_audit.json` (now also audits native/) | 0 | evidence/sprint_06/scope_audit_run.log |
| CMD-05 | `python3 -m unittest discover -s tests -t . -v` | 0 | evidence/sprint_06/unittest_run.log |
| regression | validate-sprint3/4/5 re-runs vs committed records (before native work and after the instrumentation change) | 0 | inherited_regression_run.log, instrumentation_regression_run.log |

## 6. Tests and results (IMPLEMENTATION ACCEPTANCE, software)

Frozen before evaluation: fixtures, metrics, limits (evidence/sprint_06/fixture_freeze.json; one analysis-tool correction recorded there: the cross-rate low-pass is applied before the interpolation).

| Check | Software (Track A) | Hardware-fit (Track B) | Evidence |
|---|---|---|---|
| VAL-021 / REQ-021 reference/production agreement | PASS: 216 cells (10 fixtures × 6 rates × product state, composed and exact-order paths at 48 kHz, 19 configuration states × 2 fixtures at 48 kHz) all within RMS ≤ max(1e-5·RMS(in), 1e-7) and peak ≤ 1e-4; worst RMS error 6.16e-16 (multitone_mix_m12, 48000 Hz, interstage_p24_clamp, 7.7e-10 of its limit); worst peak error 3.6e-15; SP 12-bit / MPC 18-bit / 16-bit code streams identical in every quantizing state (0 mismatches; bypass diagnostics compared as continuous values); clamp counters identical; static output-trim law bit-exact | BLOCKED (software oracle) | research/validation/reference_production/VAL-021_software.json |
| VAL-019 / REQ-019 rates and blocks | PASS: repeated renders and partitions (64 / irregular incl. 1-sample / seeded ≤ 8192 / single call > prepared max / prepared max 64 / all-ones) bit-identical at all six rates; same-rate budget met at every rate (RMS ≤ 8e-17); latency equal to the reference and confirmed by timing (table below), all ≤ 10 ms; cross-rate: native cross-rate discrepancy equals the reference's own within ≤ 4e-17 against bounds ≥ 3e-15 (table below) | BLOCKED | research/validation/rate_block/VAL-019_software.json |
| VAL-020 / REQ-020 aliasing / convergence | PASS: production vs reference within limits at 8x and 16x; reference 8x-vs-16x self-convergence within the kernel-derived line bound on every fixture (table below); SP image/fold-back lines and clamp harmonics identical in native and reference (no band-limited reconstruction substituted for the ZOH) | BLOCKED (G-06) | research/validation/implementation_alias/VAL-020_software.json |
| VAL-022 / REQ-022 parameters and state | PASS: state v1 round trips exact; 11 rejection cases return the expected codes (future schema, unknown/research/calibration key, out-of-range, unknown enum, bad step, identity mismatch, missing field, non-record, non-finite); preset content = product fields + identities only; assets carry provisional tags; generated header in sync; automation trajectories bit-identical across partitions; output-trim ramp bit-exact; proxy-domain ramp envelope within 0.013 dB of the linear-in-dB law; discrete switch exact | N/A | evidence/sprint_06/state_parameter/VAL-022_software.json |
| VAL-018 scope audit | PASS (reference + 14 native files) | N/A | evidence/sprint_06/scope_audit.json |
| Native self-test (ctest) | 31 cases PASS (determinism, partitions, chunking, zero/one-sample calls, non-finite input, over-range, bypass alignment, latency, automation, trim law, state, prepare rejections, reset) | N/A | evidence/sprint_06/native_selftest.log |
| Inherited | integrity PASS; full unit suite PASS (evidence/sprint_06/unittest_run.log); Sprint 3/4/5 records numerically identical | — | regression logs |

Discrete-rule statement: the native quantizers reproduce the implemented rules exactly (ties toward +∞ for ⌊r+½⌋; TRUNCATION toward −∞); ROUND_NEAREST is not unbiased in general — the measured R13 biases (−0.125 LSB16 ROUND_NEAREST, +0.375 LSB16 TRUNCATION, VAL-012) are unchanged. No boundary discrepancy occurred on any fixture (including the tie-adversarial fixture); the native kernel tables differ from the Python tables by ≤ 5 ulp (numpy's AVX-512 `exp` vs libm), which the cells measure.

Latency (declared = reference; verified independently; OWN-DEC-018 ceiling 10 ms):

| Host rate | Latency (host samples) | ms | Impulse peak offset (resampling path) | Burst envelope lag (cascade) | SP hold half period (host samples, documented separately) |
|---|---|---|---|---|---|
| 44100 | 298 | 6.76 | 298 | 299 | 0.85 |
| 48000 | 310 | 6.46 | 310 | 311 | 0.92 |
| 88200 | 426 | 4.83 | 426 | 428 | 1.69 |
| 96000 | 449 | 4.68 | 449 | 451 | 1.84 |
| 176400 | 682 | 3.87 | 682 | 685 | 3.39 |
| 192000 | 728 | 3.79 | 728 | 732 | 3.69 |

Cross-rate (frozen method; per rate vs the 44.1 kHz render: time-domain d_ref dB re signal / magnitude-spectrum d_ref dB / |d_nat − d_ref| ≤ bound):

| Fixture | 48 kHz | 88.2 kHz | 96 kHz | 176.4 kHz | 192 kHz |
|---|---|---|---|---|---|
| multitone_mix_m12 | -7.3 / -60.7 / 0e+00≤4e-07 | -11.3 / -60.7 / 3e-18≤2e-06 | -7.0 / -60.7 / 0e+00≤2e-06 | -8.3 / -60.8 / 0e+00≤3e-06 | -11.6 / -60.7 / 0e+00≤3e-06 |
| sine_1k_m20 | -51.4 / -55.8 / 1e-18≤7e-09 | -51.1 / -57.3 / 4e-18≤3e-15 | -51.4 / -55.8 / 2e-18≤6e-09 | -51.4 / -57.0 / 1e-18≤5e-15 | -52.1 / -65.1 / 6e-19≤7e-09 |
| transient_bursts | -5.9 / -44.7 / 0e+00≤7e-04 | -9.9 / -52.1 / 0e+00≤2e-03 | -5.5 / -50.6 / 0e+00≤2e-03 | -6.9 / -50.1 / 0e+00≤4e-03 | -10.2 / -57.9 / 1e-17≤3e-03 |

Finding (reference property, reproduced exactly by the native core, left for owner review): the reference anchors both machine clocks at proxy index 0, which corresponds to input time −lobes/fs_host (1.09 ms at 44.1 kHz, 1.0 ms at 48 kHz, 0.5 ms at 96 kHz, 0.25 ms at 192 kHz), so the sampling phase of the machine grids relative to the audio depends on the host rate; phase-sensitive SP fold-back products (e.g. 18 kHz → 8042 Hz) differ in phase between rates (time-domain d_ref −6…−12 dB) while their magnitudes agree (magnitude-spectrum d_ref −45…−65 dB) and the 1 kHz tone differs only by quantizer decisions (−51 dB). On hardware the machine-clock phase relative to the audio is arbitrary; a rate-independent anchor (machine sample k at input time k/f_machine) would change accepted reference behaviour and is NOT applied (OWN-DEC-023 / §1 of the authorization).

Convergence (VAL-020; reference 8x vs 16x; native vs reference):

| Fixture / rate | 8x-vs-16x RMS re signal | 8x-vs-16x max in-band spectral difference | native-vs-reference RMS 8x / 16x | production-introduced max in-band | within kernel bound |
|---|---|---|---|---|---|
| multitone_mix_m12_48000 | -86.4 dB | -120 dB | 7.7e-17 / 1.1e-16 | -344 dB | yes |
| multitone_mix_m12_96000 | -84.5 dB | -116 dB | 7.8e-17 / 1.1e-16 | -346 dB | yes |
| near_nyquist_tone_19k_48000 | -82.0 dB | -110 dB | 2.6e-16 / 3.6e-16 | -326 dB | yes |
| near_nyquist_tone_19k_96000 | -82.1 dB | -110 dB | 2.6e-16 / 3.7e-16 | -328 dB | yes |
| overrange_steps_pm16_48000 | -110.5 dB | -136 dB | 5.5e-16 / 8.1e-16 | -321 dB | yes |
| overrange_steps_pm16_96000 | -106.3 dB | -130 dB | 5.6e-16 / 8.0e-16 | -323 dB | yes |
| sine_1k_m20_48000 | -101.7 dB | -153 dB | 5.3e-17 / 7.7e-17 | -338 dB | yes |
| sine_1k_m20_96000 | -101.7 dB | -153 dB | 5.5e-17 / 7.6e-17 | -341 dB | yes |
| two_tone_18k_19p5k_48000 | -108.1 dB | -138 dB | 2.8e-16 / 4.1e-16 | -325 dB | yes |
| two_tone_18k_19p5k_96000 | -106.8 dB | -138 dB | 3.1e-16 / 4.0e-16 | -327 dB | yes |

## 7. Benchmark (OWN-DEC-017; Release core, one stereo CASCADE instance, product state, preallocated, 1 s warm-up, 3 trials × 5 s; applies only to this environment)

Machine: Intel(R) Xeon(R) Processor @ 2.10GHz, 4 vCPU shared cloud VM (Ubuntu 24.04, Linux 6.18.44), single thread, ordinary priority, no real-time scheduling, no CPU pinning; GCC 13.3.0 `-O2 -ffp-contract=off -fno-fast-math`, generic x86-64. Raw per-callback times: evidence/sprint_06/benchmark/raw_*.f64.

| Rate | Block | Limit (mean) | Mean load (3 trials) | Median | p95 (ms) | p99 (ms) | p99.9 (ms) | Max (ms) | Callback budget (ms) | Overruns |
|---|---|---|---|---|---|---|---|---|---|---|
| 176400 | 256 | 60 % | 15.5 / 14.3 / 14.4 % | 0.22 / 0.21 / 0.21 ms | 0.26 / 0.23 / 0.23 | 0.36 / 0.25 / 0.25 | 0.40 / 0.34 / 0.40 | 0.43 / 0.37 / 0.92 | 1.45 | 0 |
| 192000 | 256 | 60 % | 20.4 / 20.3 / 20.6 % | 0.26 / 0.26 / 0.27 ms | 0.34 / 0.34 / 0.35 | 0.42 / 0.39 / 0.42 | 0.47 / 0.44 / 0.47 | 0.51 / 0.48 / 0.52 | 1.33 | 0 |
| 44100 | 64 | 20 % | 9.5 / 6.6 / 7.1 % | 0.13 / 0.09 / 0.10 ms | 0.23 / 0.12 / 0.14 | 0.46 / 0.15 / 0.17 | 0.83 / 0.19 / 0.20 | 0.96 / 0.20 / 0.22 | 1.45 | 0 |
| 48000 | 64 | 20 % | 9.3 / 9.6 / 9.3 % | 0.12 / 0.12 / 0.12 ms | 0.17 / 0.16 / 0.15 | 0.20 / 0.19 / 0.20 | 0.23 / 0.24 / 0.23 | 0.31 / 0.29 / 0.35 | 1.33 | 0 |
| 88200 | 128 | 40 % | 9.4 / 9.6 / 9.0 % | 0.14 / 0.14 / 0.13 ms | 0.16 / 0.17 / 0.15 | 0.18 / 0.21 / 0.18 | 0.24 / 0.23 / 0.22 | 0.30 / 0.26 / 0.23 | 1.45 | 0 |
| 96000 | 128 | 40 % | 13.0 / 13.6 / 13.0 % | 0.17 / 0.17 / 0.17 ms | 0.23 / 0.26 / 0.20 | 0.28 / 0.29 / 0.24 | 0.34 / 0.34 / 0.29 | 0.40 / 0.35 / 0.33 | 1.33 | 0 |

All six pairs meet the owner mean-load limits with margin (all pairs); the p99.9 < 80 % target is met in this run at every pair (yes). A preceding run of the same binary (same settings) showed one overrun at 192 kHz / 256 (max 1.57 ms against a 1.33 ms budget, p99.9 = 0.84 of the budget in one of three trials; median 0.26 ms): callback-time outliers of several times the median are host preemption on the shared VM, not steady-state load; they are reported as observed, not explained away. Before optimisation the straightforward port measured 26.5 % / 54 % / 115 % at 48 / 96 / 192 kHz (budgets 20 / 40 / 60 %); the composed operator tables (not a model change) brought it to the values above. Windows performance is pending until measured on Windows.

## 8. Artifacts

Native sources and generated header, Python driver/validation/fixtures, four validation records with manifests, benchmark record + 18 raw timing files (≈ 0.5 MB), evidence/sprint_06/* (hashed in provenance.json). No audio committed. Scratch renders are not kept.

## 9. Provisional behaviour (all UNVALIDATED AGAINST HARDWARE)

Everything inherited from Sprints 3–5 plus: composed operator evaluation (float rounding order only), 10 ms ramps and event mapping (software convention), static bypass selector, state v1, fail-safe policy, no FTZ/DAZ.

## 10. Production / native release readiness (NOT implementation acceptance)

Compiled and tested on Linux x86_64 only. Windows x86_64 (the intended deployment target): NOT RUN — no Windows toolchain or cross-compiler exists in this container; the MSVC options in native/CMakeLists.txt are untested; a Linux result is not Windows validation. No plugin wrapper, host integration, bypass transition policy, GUI, preset bank, installer or release work exists (Sprint 7/8, G-09..G-11).

## 11. Assumptions

Composing linear stages into precomputed tables counts as "optimising computation, not the model" (OWN-DEC-015). Mean load as defined by the owner is the limit; p99.9 is a target reported with scheduling conditions. The 18 kHz analysis band and 44.1 kHz analysis grid define "common band" for the cross-rate method.

## 12. Deviations

Contract items that need hardware (G-06 image/alias agreement) stay BLOCKED. Human listening NOT EXECUTED. research/fit not created. Three check-design corrections before the final records (quantizer-bypass values compared as continuous, discrete-switch tolerance 1e-12, pre-event window accounting for the R16 look-ahead) and one core semantic decision (redundant retarget keeps the ramp) are recorded in this report; no limit was loosened. The first VAL-019 record was superseded by the analysis-tool correction (filter before interpolation) with the same outcome.

## 13. Documentation updated

ENGINE_SPEC, ARCHITECTURE, PARAMETERS, CONFIDENCE, DECISIONS (OWN-DEC-014..023, ENG-DEC-020..024), GATE_REGISTER (G-08), EXPERIMENT_PLAN, VALIDATION_PLAN, DSP_CHANGELOG, ACCEPTANCE_MATRIX.md/.csv (rows 019..022), SPRINT_PLAN, EXECUTION_PLAN_V2 (§9 item 7 part received), BUILD_COMMANDS (CMD-13..17), docs/README, PROJECT_HANDOFF, this report. Immutable research and contracts untouched. Previous sprint reports untouched.

## 14. Confidence / status / acceptance changes

No claim status changed. Acceptance: software cells PASS for REQ-019/020/021/022; hardware-fit cells BLOCKED; Windows NOT RUN.

## 15. Verdict

Implementation acceptance (software): PASS — the native core is the accepted reference to float rounding under the owner's G-08 limits, deterministic, within the performance budgets on the recorded machine, with the frozen controls and state v1. Native release readiness: NOT ESTABLISHED (Windows NOT RUN, no wrapper). Hardware fit: BLOCKED.

Sprint verdict: **PASS WITH EXTERNAL VALIDATION PENDING** (named external gates: Windows native validation (G-09 platform); human listening; G-07H; G-04 Track B).

## 16. Continuation gate

Sprint 7 (plugin wrapper, host integration, bypass transitions, meters/UI, REQ-023..025) requires G-09 owner inputs that the repository does not contain: plugin formats and OS/DAW matrix, framework/SDK and licence (no paid/proprietary dependency is accepted autonomously), a Windows x86_64 toolchain or machine, the bypass transition policy, host automation mapping conventions (normalized ranges / enum ordering / event timing conventions of the chosen framework). STOP before Sprint 7.

## 17. Ending commit

Implementation milestone commit `1a3ecafd98209f1b637b8aa2ba187d6003941c8a` on `claude/autonomous-build` (hash back-filled by the follow-up checkpoint commit).
