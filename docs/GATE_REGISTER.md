# Hardware, human and delivery gates

Revision: planning V1 · 2026-10-06

Status: DRAFT PLANNING CONTRACT. Documentation creation authorized; implementation and release not authorized.

## Mandatory dependency gates

Every gate is currently OPEN/NOT EXECUTED. A prior sprint milestone does not waive the next gate. Independent preparation may proceed inside authorized scope; no calibrated fitting/production work may assume favorable missing results. RESEARCH_DEBT retains original priorities; gates are dependency controls, not relabeled evidence.

| Gate | Name | Required evidence | Current status | Blocks | Owner | First sprint |
|---|---|---|---|---|---|---|
| G-01 | Execution activation and capability freeze | G-01A: separate owner execution instruction, repository/baseline/branch, allowed operations/budgets before S1 edits. G-01B: actual toolchain/target plan and smoke-tested command manifest established within S1 before dependent executable work. Full gate closes at S1 exit. | OPEN; current request planning only | G-01A blocks S1 mutations; G-01B blocks dependent executable work | Owner + execution engineer | 1 |
| G-02 | Null/measurement framework self-test | CHAIN-EXP-016 recovery against independent truth; instrument/evaluation method and numerical floor documented | NOT EXECUTED | Trusting fitted residuals or hardware comparison | Validation engineer | 1 |
| G-03 | Targeted documentary closure | CHAIN-EXP-019/020, AD7541/AK5328/SM5841 retrieval, stock revision/route scope; each remaining unknown retained | OPEN | Using extracted/guessed coefficients; dependent P0/P1 closure | Research engineer | 1 |
| G-04 | Hardware campaign validity | Stock units/revisions identified, import/export demonstrated, calibrated 192k/24 interface, S/PDIF44.1, three repeat captures, pilot/metadata/hash validation; bandwidth exceptions resolved | HARDWARE REQUIRED | All hardware-fit conclusions | Measurement operator | 2 |
| G-05 | P0/P1 evidence closure | All 6 P0/12 P1 ledger items closed with resolving evidence, or owner-approved restricted scope and justification that dependent behavior does not rely on unresolved item | OPEN: 18 items | Calibrated machine references (S3/S4), cascade/product (S5+) | Evidence reviewer + owner | 2 |
| G-06 | Acceptance threshold and dataset freeze | Hardware self-null floor, instrument uncertainty, numeric tolerances by metric/domain/material/level, disjoint FIT/VALIDATION IDs; owner acceptance before fit | UNKNOWN thresholds | PASS for hardware fits in S3/S4/S5 | Validation engineer + owner | 2 |
| G-07 | Product and output path decision | B reference comparisons, listening logs; owner-recorded A/B/C selection, SP canonical route, MPC route, retained blocks, control defaults and claim limits | NOT CHOSEN | Production optimization, UI/defaults/presets | Product owner | 5 |
| G-08 | Production/parameter/numerical budgets | Platform cross-precision tolerance, resampler/alias convergence budget, proxy rate, maximum block/input domain, CPU and latency budget, parameter ranges/mappings/smoothing/state version approved before optimization | UNKNOWN | Executable S6 numeric optimization and S7 runtime criteria | Engineering lead + owner | 6 |
| G-09 | Native platform and host proof | Approved OS/CPU/format/DAW versions and SDK/license plan; native builds/hosts available and validation evidence | UNKNOWN targets/access | Format delivery and final release verdict | Platform engineer | 7 |
| G-10 | Owner listening and UI/manual acceptance | CHAIN-EXP-018 product judgment plus final preset headroom, UI automation/bypass meanings and claims review | NOT EXECUTED | Product acceptance and S8 candidate completion | Owner/listeners | 7 |
| G-11 | Release provenance and readiness | All mandatory gates passed; dependency/source rights, clean rebuild, regression, native host evidence, exact package/hash/source mapping; signing/install policy resolved as applicable | BLOCKED | Declaring RELEASE READY YES; any install/distribution | Release engineer + owner | 8 |

## Hardware-measurement gates in full

- SP exact clock CHAIN-EXP-001 (documentary clock extraction can corroborate, but unit rate is measured); input/AA/quantizer CHAIN-EXP-002; unity/level-DAC/hold CHAIN-EXP-003; output contacts/filter/MIX topology CHAIN-EXP-004; physical FS/gain/clip CHAIN-EXP-005; in-band noise/spurs CHAIN-EXP-006; stereo slot/hold fraction CHAIN-EXP-007.
- MPC receiver/storage/analog reduction evidence CHAIN-EXP-008; input/ADC/FS/overload CHAIN-EXP-009; DAC/main output response/FS/noise THD/IMD/de-emphasis CHAIN-EXP-010; main/individual comparison CHAIN-EXP-011.
- Physical chain and interstage CHAIN-EXP-012; IMD unexplained-residual gate CHAIN-EXP-015; level-matched contribution comparison CHAIN-EXP-014 where it supports product selection. Reverse order CHAIN-EXP-013 remains informational, may be nonblocking with recorded rationale; it cannot create a product feature.
- Three repeats are an uncertainty estimate, not a passing tolerance. Warm-up, pilot budgets, instrument floor and dataset split must be valid before fitting. 208.33k spur is outside 192k capture Nyquist; absent wideband instrument record NOT OBSERVABLE, not zero. Any unresolved characteristic in-band component affecting the model blocks the affected fit.

Human judgments: owner future execution/target authorization G-01; dataset/threshold acceptance G-06; product/output/listening G-07; CPU/latency/parameter policy G-08; final UI/manual/listening G-10; release scope/rights/native proof G-11. Target-platform and legal dependency/source rights are release gates, not assumed hardware claims. Signing or paid SDK access is required only where the approved target/delivery plan calls for it.

## Resolution protocol

Record gate ID, requirement/claim/debt IDs, immutable evidence references/hashes, decision owner/date, numeric policy revision where relevant, exact scope allowed to continue and unresolved exceptions. Mark PASS only after review of actual evidence. If scope changes, revise DECISIONS, relevant contract and acceptance rows consistently. No implicit P0/P1 closure from software PASS. No missing capture is silently external-pending for a mandatory dependent milestone.
