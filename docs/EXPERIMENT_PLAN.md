# Twenty experiments and resolving protocols

Revision: execution V1 (Sprint 1) · 2026-10-06 · supersedes planning V1

Status: EXECUTION IN PROGRESS. CHAIN-EXP-016 EXECUTED (SIMULATION, PASS); CHAIN-EXP-019/020 ATTEMPTED, BLOCKED; all others NOT EXECUTED.

## Execution status and experiment governance

Sprint 1 (2026-10-06): CHAIN-EXP-016 EXECUTED — SIMULATION, outcome PASS, record research/sim/CHAIN-EXP-016/result.json; CHAIN-EXP-019 and CHAIN-EXP-020 ATTEMPTED and BLOCKED (source hosts denied by the execution-environment network policy; reference/sources/*/ACCESS_RECORD.json). The other seventeen experiments are NOT EXECUTED. The table below preserves the original planning rows; the living status is in this paragraph, docs/GATE_REGISTER.md and the sprint reports. The table preserves original question/hypothesis/criterion; extensions below define prerequisite discipline. Source short EXP IDs mean CHAIN-EXP IDs, never unrelated project tests. Artifact directories are repository-relative, despite leading slashes in historical source. No absolute filesystem root is an authorized write target.

| ID | Question/hypothesis | Prerequisite | Procedure / metrics | Original decision criterion | Owner sprint / artifact |
|---|---|---|---|---|---|
| CHAIN-EXP-001 | What is the SP sample rate?; 26 041.67 Hz | SP unit | Load a sample holding a sine of known period in samples; measure output frequency and the clock spur against the calibrated interface clock; Hz, ppm | Replace constant if outside measurement uncertainty | S2; /reference/hardware/sp1200/unit_001/digital/ |
| CHAIN-EXP-002 | SP input chain and quantizer transfer; AA response as SP-12; ideal 12-bit with clamp | Sample export route | Record sweeps, ramps, stepped and low-level sines at each gain; export sample data; Response, fold-back, code transitions, clamp codes | Fit filter; select rounding rule | S2; …/sp1200/unit_001/digital/, /linear/ |
| CHAIN-EXP-003 | SP DAC, hold and unity playback; Full-period hold; identity at unity | Sample import route | Load synthetic 12-bit data; capture at each output; Hold fraction, droop, images, transfer linearity | Confirm or replace R6/R7 | S2; …/sp1200/unit_001/digital/ |
| CHAIN-EXP-004 | SP output paths; Filters differ as documented | EXP-003 | Same sample at every output and contact, and MIX OUT; Complex response per path, to 96 kHz | Populate R8/R9; choose default | S2; …/sp1200/unit_001/linear/ |
| CHAIN-EXP-005 | SP level calibration; — | Calibrated interface | Stepped sine at each gain; FS sine playback; Volts for FS in and out; clip onset | Close RD-P0-02 | S2; …/sp1200/unit_001/calibration/ |
| CHAIN-EXP-006 | SP noise and spurs; Spurs at 26.04 and 208.33 kHz | — | Idle and loaded captures at 192 kHz; Spectrum, hum, DC | Keep noise OMITTED unless characteristic | S2; …/sp1200/unit_001/noise/ |
| CHAIN-EXP-007 | SP inter-channel skew; 4.8 µs per slot | EXP-003 | Same sample triggered on two channels; Inter-channel delay vs channel pair | Offer slot-skew research config or not | S2; …/sp1200/unit_001/stereo/ |
| CHAIN-EXP-008 | MPC digital transparency; S/PDIF → storage is bit-exact; reduction rule unknown | S/PDIF source | Sample known data digitally and via analog; save; compare; Bit differences; low-level harmonic signature | Select rule for R13 | S2; /reference/hardware/mpc3000/unit_001/digital/ |
| CHAIN-EXP-009 | MPC input chain + ADC; Linear to FS; clip location unknown | — | Stimuli at each switch position and several pot positions; save files; Response, FS volts, clip onset, overload recovery | Populate R11/R12 | S2; …/mpc3000/unit_001/linear/, /nonlinear/ |
| CHAIN-EXP-010 | MPC DAC + output; Linear; flat to 20 kHz | — | Load synthetic 16-bit sounds; capture main out; Response, group delay, THD, IMD, noise, FS volts | Populate R14/R15; test CLM-020 | S2; …/mpc3000/unit_001/linear/, /nonlinear/, /noise/ |
| CHAIN-EXP-011 | MPC main vs individual; Same within tolerance | EXP-010 | Same sound to both paths; Response and level differences | Decide whether paths differ in model | S2; …/mpc3000/unit_001/linear/ |
| CHAIN-EXP-012 | Physical cascade; Images pass; overload depends on record level | EXP-005, -009 | SP output into MPC input at documented settings; Captured files; level at each node | Set interstage default | S2; /reference/hardware/cascade/ |
| CHAIN-EXP-013 | Order; Small difference unless MPC input driven | Both units | SP→MPC vs MPC→SP on four material types (≤ 2.3 s excerpts); Section 32 metric set | Informational | S5; /reference/hardware/cascade/ |
| CHAIN-EXP-014 | Level-matched cascade; — | EXP-012 | DRY / SP / MPC / SP→MPC / MPC→SP; Section 32 metric set | Informational | S5; /reference/hardware/cascade/ |
| CHAIN-EXP-015 | IMD suite; Products explained by sampling and quantization | EXP-002…-010 | SMPTE, CCIF, multitone on each machine; Product levels | Any unexplained product opens a nonlinear-block investigation | S2; …/nonlinear/ |
| CHAIN-EXP-016 | Null-framework self-test; Framework nulls an ideal reference to numerical floor | None | Simulation only; Residual of identical signals after alignment | Framework accepted when its own floor is known | S1; /research/sim/ |
| CHAIN-EXP-017 | Skeleton vs published SP-12 figures; Skeleton reproduces the alias/image pattern reported in SRC-04 qualitatively | None | Simulation only: sweep through R3–R8 with placeholder filters; Spectrogram pattern | Sanity check only; never evidence about hardware | S3; /research/sim/ |
| CHAIN-EXP-018 | Listening test; — | Fitted models | Section 33; Blind scores | — | S5; /research/listening/ |
| CHAIN-EXP-019 | SP schematic extraction and SPICE; Responses consistent with SRC-04 | Readable copy of SRC-01 | Transcribe AA, channel-filter, mix and clock circuits; AC analysis; Transfer functions, corners, Q, gains, clock divider | Close RD-P0-01 documentarily | S1; /reference/sources/sp1200/ |
| CHAIN-EXP-020 | MPC schematic extraction and SPICE; Low-order filters | SRC-20 scan | Transcribe AD/DA and 8DACS analog sections; AC analysis; Transfer functions, gains, coupling poles, FS volts | Close RD-P0-06 documentarily | S1; /reference/sources/mpc3000/ |

## Targeted documentary campaign (S1)

Read net-connected schematics before deriving analog transfer functions. For SP record every refdes/value/net for AA, fixed ch3–6, mix and clock; for MPC record AD/DA13-3 and8DACS13-4 input, I/V/filter/coupling and gain networks. Use source-derived topology/order and component tolerances, record unreadable values as UNKNOWN. Run AC analysis only when a complete unambiguous transcription exists, preserve simulator version/input/output and label SIMULATION. Do not transplant an order11 SP-12 digital fit as analog order. Compare stock revisions and sibling drawings only if readable evidence is available. AD7541/AK5328/SM5841 datasheets are targeted P1 inputs; a compatible part's datasheet is not a substitute for the fitted part/revision. Access failure leaves debt OPEN.

## Framework self-test (S1)

CHAIN-EXP-016 uses independently generated synthetic signal truth. First compare identical arrays with no preprocessing: exact zero residual. Then perturb one constant clock ratio, one fixed fractional delay, polarity, a calibration-tone scalar and documented DC treatment; recover them using pilots, compare estimated vs known values and measure evaluator floor. Do not add time-varying warping or fitted EQ. Freeze numerical analysis tolerances before accepting this tool for hardware comparison; do not tune them to force a fitted model pass. CHAIN-EXP-017 in S3 is qualitative SP-12 sanity only, never proof for SP-1200.

## Hardware campaign (S2)

MEASUREMENT_PLAN supplies setup/stimuli/routes. Hardware operator owns capture validity and unit metadata. Bit tests separate S/PDIF16-bit receiver/storage from analog ADC reduction; infer only observable composite behavior. Complete physical cascade capture after SP/MPC level calibration. CHAIN-EXP-015 tests residual IMD before nonlinear model authorization; unexplained products reopen evidence/decision, not automatically a tanh fit. Measure multiplex skew/hold fraction but keep slot-skew research-only. Every mandatory P1 either resolves or prevents dependent work.

## Fit, validation and listening (S3–S5)

Fit SPLinear blocks with topology-constrained pole/zero parameters; quantizer rule/offset with code transitions; hold fraction with synthetic loaded sounds; levels from stepped sine. MPC digital filters use measured/datasheet linear responses, not modulator-circuit fantasies. Fit only FIT captures, verify on separately frozen VALIDATION captures. Validation cannot add per-file gains/EQ to hide mismatch. A previously unexplained nonlinear residual requires a new decision/experiment with IMD held-out validation before model complexity expands. CHAIN-EXP-013 reverse order informational; never shipping route without a new product decision. CHAIN-EXP-018 cannot execute until fitted candidates exist; LISTENING_TEST_PLAN owns human protocol.

## Result record

Store experiment ID, question/hypothesis, requirements/debt, input/config hash, unit/routes, exact software/source commit/environment/command, algorithm and preprocessing versions, raw output hash, metric definitions/threshold policy, confidence interval/uncertainty, outcome, limitation and resulting decision. A plot/WAV/title/sidecar all carry artifact class. Executed experiment replaces NOT EXECUTED only in living result/register, never historical research V1. Preserve failed fits as failed evidence, no notebook-only findings.
