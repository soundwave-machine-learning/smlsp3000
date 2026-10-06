# Validation domains, thresholds and release proof

Revision: planning V1 · 2026-10-06

Status: DRAFT PLANNING CONTRACT. Documentation creation authorized; implementation and release not authorized.

## Check execution status

All DSP/build/hardware/listening/host checks are NOT EXECUTED. PACKAGE_VALIDATION records only documentation checks actually run in this task. Mandatory commands are UNKNOWN: Sprint1 must select the actual toolchain, create docs/BUILD_COMMANDS.md with exact shell/working-directory/version/flags/check IDs/artifact paths and demonstrate a smoke run before a dependent executable contract is frozen. Later checks use that manifest, not fabricated command names. Unknown command or criterion means DRAFT/BLOCKED for the affected check.

## Independent acceptance domains

1. Source integrity and document/count checks: SHA equality and exact contract count, executed by planner.
2. Same-build deterministic rendering and block partition invariance: exact sample sequence equality on common configuration; never use this as hardware fidelity.
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

Code transition matching targets exact agreement where raw digital data and thresholds are identifiable. Sensitivity/nominal level does not define ADC_FS. Silence/anti-phase may make a relative RMS metric undefined; record absolute residual and defined metric applicability, never Inf interpreted as model failure/pass. Image/alias frequencies and levels need calibrated spectral analysis; same-band limits include capture/host bandwidth.

## Complete requirement/check/evidence matrix

ACCEPTANCE_MATRIX.md and ACCEPTANCE_MATRIX.csv are the authoritative indexed mapping of all28 requirements to stimulus, expected behavior/tolerance, target environment, owner sprint and evidence path. Sprints refer to check IDs and restate their required tests. Each executed report records exact command/version/exit code plus immutable logs, raw config/input hash and threshold revision. Existing valid tests persist across sprints; test changes need independent defect justification and rerun, not convenient golden rebaselining. Any owner acceptance-policy change revises the matrix/contracts before rerun.

## Release and target matrix

OS/version, architecture, formats, DAW/version, SDK/framework/license, build compiler, install/signing policy and target runtime access are UNKNOWN until G-01/G-09. Proposed native candidates are chosen from the actual owner use case, not promised in this package. A cross-compiled binary is a build artifact only; it does not establish native AU/VST3 loading, scanning, latency, automation, GUI or session restore. A mandatory target cannot be waved through as external-pending. Nonblocking advisory platforms must be designated explicitly before continuing.

S8 clean rebuild uses the approved exact commands, full inherited regression and all selected native matrix rows. Record binary hashes and platform toolchains; bit-identical binaries are claimed only if demonstrated with stable timestamps/toolchain, otherwise state the achieved reproducibility (source/dependency/build/behavior). Release-ready YES requires every mandatory gate, not simply a successful build.
