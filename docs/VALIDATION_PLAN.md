# Validation domains, thresholds and release proof

Revision: execution V2 (owner decision OWN-DEC-001) · 2026-10-06 · supersedes execution V1

Status: EXECUTION IN PROGRESS. Commands frozen in docs/BUILD_COMMANDS.md; hardware/production thresholds still UNKNOWN.

## Check execution status

Sprint 1 executed VAL-001, VAL-002, VAL-003 (SIMULATION) and VAL-028 with logged commands/exit codes (evidence/sprint_01/); VAL-004 is BLOCKED (source access). All hardware/listening/host checks remain NOT EXECUTED. Mandatory commands are now frozen in docs/BUILD_COMMANDS.md (Python 3.13 + numpy reference/analysis stack, ENG-DEC-011); later checks use that manifest, not fabricated command names. Unknown command or criterion still means DRAFT/BLOCKED for the affected check.

## Track split (OWN-DEC-001)

Domains 1–4 below are SOFTWARE ACCEPTANCE (Track A) and may PASS on software evidence; domains 5–6 (hardware fit; hardware-arm listening) are HARDWARE-FIT ACCEPTANCE (Track B) and stay BLOCKED until G-04. Software numeric tolerances (cross-rate, reference/production, implementation alias budget) are owner decisions under G-08 and are never presented as hardware fidelity. Software-only listening comparisons (reference / simplified / bypass, no hardware condition) are permitted as informational LISTENING STIMULUS artifacts for G-07S.

## Independent acceptance domains

1. Source integrity and document/count checks: SHA equality and exact contract count, executed by planner.
2. Same-build deterministic rendering and block partition invariance: exact sample sequence equality on common configuration; never use this as hardware fidelity. In force since Sprint 1 for CHAIN-EXP-016 (tests/test_exp016_reproduction.py compares a re-run to the committed record exactly).
3. Cross-host-rate/precision/platform comparisons: G-08 numeric tolerances on common-band continuous-input fixtures; algorithms/quantizer-boundary considerations documented separately.
4. Reference/production and plugin/offline agreement: G-08 frozen numerical budget and latency alignment, not the G-06 hardware budget.
5. Hardware fit: G-06 thresholds from instrument uncertainty and three-take unit self-null floor, disjoint validation data and metric/domain/level-specific thresholds.
6. Listening/UI/native release: actual human/host/target evidence; software PASS cannot substitute.

## Hardware null protocol

Normalize hardware/model to192kHz; estimate one constant clock ratio from start/end pilots; sub-sample delay from pilot cross-correlation; single scalar from1kHz calibration tone; fixed path polarity from impulse; report DC then remove identically with documented high-pass. No program-fit EQ, free gain, dynamic gain or time-varying warp. Report residual peakdBFS, residual RMS relative to signalRMS, residual spectrum/per-band and correlation. If drift is not representable by one ratio, reject/recapture or revise protocol explicitly, never mask it.

| Metric | Current threshold | Freeze rationale |
|---|---|---|
| frequency response error | UNKNOWN; cannot PASS yet | G-06: measured hardware self-null/instrument floor and application-specific bound before fitting |
| phase error | UNKNOWN; cannot PASS yet | G-06: measured hardware self-null/instrument floor and application-specific bound before fitting |
| group delay error | UNKNOWN; cannot PASS yet | G-06: measured hardware self-null/instrument floor and application-specific bound before fitting |
| harmonic residual | UNKNOWN; cannot PASS yet | G-06: measured hardware self-null/instrument floor and application-specific bound before fitting |
| IMD residual (SMPTE, CCIF, multitone) | UNKNOWN; cannot PASS yet | G-06: measured hardware self-null/instrument floor and application-specific bound before fitting |
| alias/image profile | UNKNOWN; cannot PASS yet | G-06: measured hardware self-null/instrument floor and application-specific bound before fitting |
| quantization transfer | UNKNOWN; cannot PASS yet | G-06: measured hardware self-null/instrument floor and application-specific bound before fitting |
| null residual | UNKNOWN; cannot PASS yet | G-06: measured hardware self-null/instrument floor and application-specific bound before fitting |
| stereo correlation | UNKNOWN; cannot PASS yet | G-06: measured hardware self-null/instrument floor and application-specific bound before fitting |
| peak/RMS/crest change | UNKNOWN; cannot PASS yet | G-06: measured hardware self-null/instrument floor and application-specific bound before fitting |

Evaluator floor (measured in Sprint 1, SIMULATION; research/sim/CHAIN-EXP-016/result.json): identical arrays null to exactly zero; with one constant clock ratio, one sub-sample delay, polarity, scalar gain and DC perturbations the framework residual is ≤ −92.6 dB RMS re signal (−149 dB with no perturbation), clock-ratio error ≤ 0.0005 ppm, delay error ≤ 2e-5 samples and gain error ≤ 3e-8 dB on a 50 Hz–18 kHz multitone at 192 kHz. A hardware model can never be required to null below this evaluator floor plus the measured hardware self-null floor (G-06). Code transition matching targets exact agreement where raw digital data and thresholds are identifiable. Sensitivity/nominal level does not define ADC_FS. Silence/anti-phase may make a relative RMS metric undefined; record absolute residual and defined metric applicability, never Inf interpreted as model failure/pass. Image/alias frequencies and levels need calibrated spectral analysis; same-band limits include capture/host bandwidth.

## Complete requirement/check/evidence matrix

ACCEPTANCE_MATRIX.md and ACCEPTANCE_MATRIX.csv are the authoritative indexed mapping of all28 requirements to stimulus, expected behavior/tolerance, target environment, owner sprint and evidence path. Sprints refer to check IDs and restate their required tests. Each executed report records exact command/version/exit code plus immutable logs, raw config/input hash and threshold revision. Existing valid tests persist across sprints; test changes need independent defect justification and rerun, not convenient golden rebaselining. Any owner acceptance-policy change revises the matrix/contracts before rerun.

## Release and target matrix

OS/version, architecture, formats, DAW/version, SDK/framework/license, build compiler, install/signing policy and target runtime access are UNKNOWN until G-01/G-09. Proposed native candidates are chosen from the actual owner use case, not promised in this package. A cross-compiled binary is a build artifact only; it does not establish native AU/VST3 loading, scanning, latency, automation, GUI or session restore. A mandatory target cannot be waved through as external-pending. Nonblocking advisory platforms must be designated explicitly before continuing.

S8 clean rebuild uses the approved exact commands, full inherited regression and all selected native matrix rows. Record binary hashes and platform toolchains; bit-identical binaries are claimed only if demonstrated with stable timestamps/toolchain, otherwise state the achieved reproducibility (source/dependency/build/behavior). Release-ready YES requires every mandatory gate, not simply a successful build.
