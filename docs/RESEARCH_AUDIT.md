# Research audit

Revision: planning V1 · 2026-10-06

Status: DRAFT PLANNING CONTRACT. Documentation creation authorized; implementation and release not authorized.

## Verdict and authority

**HARDWARE REQUIRED.** Research is sufficient to plan a replaceable reference superset and a numerical skeleton. It is not sufficient for a calibrated hardware model, production DSP, or a release claim. Hardware measured: NO. Simulations executed: NO (closed-form arithmetic exists). Listening: NO. All twenty experiments remain NOT EXECUTED.

Inspected directly this audit: both supplied V1 attachments, in full, and their parsed ID/count inventories. Not supplied or retrieved this audit: original manuals, schematics, datasheets, source web pages, unit captures, code repository, or implementation logs. Source access below is **REPORTED BY RESEARCH V1**, not independently reverified. No broad research or gap-closing experiment was restarted. Referenced materials remain future targeted inputs. The original Markdown governs its JSON summary (§44); originals are preserved byte-for-byte.

## Selected versus recommended paths

Shipping product A circuit-only / B full sample path / C measured hybrid: **NOT CHOSEN** (CHAIN-DEC-001). Reference: **B superset recommended**, replaceable and bypassable, unity pitch. SP canonical output: **UNDECIDED** (CHAIN-DEC-003/RD-P0-04). Research variants: ch7–8 none; ch5–6 higher fixed low-pass; ch3–4 lower fixed low-pass. Ch1–2 SSM2044 excluded. MIX OUT is literal mono and topology remains unknown. MPC main stereo is the recommended mix-bus route (§20), not a recorded owner product selection; individual pair is diagnostic; headphone route excluded.

Stereo reference: linked dual mono with shared sampling instants and coefficients on SP, explicitly PRODUCT ABSTRACTION; independent channel signal states. MPC phase-locked stereo is historically supported. No random mismatch, independent drift, mid/side or slot-skew product mode. Rate domains: host 44.1–192k listed in RATE_GAIN_PLAN; SP nominal 26.04k, exact 20MHz/768 provisional; MPC44.1k; analog proxy/nonlinear oversampling implementation rate UNSET. Calibration: volts-per-dBFS, machine input/output FS volts and interstage default UNSET, not digital unity. Converter strategy: SP ideal 12-bit quantizer/clamp plus sampler/AA/ZOH/output response (source A+C); MPC linear conversion responses/clamps and 16-bit storage reduction (source C), while its physical converters are 18-bit. Installed nonlinearities/INL/DNL/glitch/noise are not invented. Pitched playback: unity only; tuned round-trip extreme candidate deferred, never default.

## Contradictions reported before dependent planning

The eight source conflicts are retained below. The audit adds eleven scope/measurement/interpretation findings. These are not silent source edits or resolved owner decisions. Functional clarifications are proposed in this package; material paths, metrics and behavior require their named gate. Eight sprints are still planned, with affected implementation blocked until evidence/decisions exist.
| Source conflict | Competing wording | Source verdict | Resolution |
|---|---|---|---|
| C-01 | 27.5 kHz "in the specifications" (as reported by SRC-04) versus 26.04 kHz (SRC-05); 26 kHz tone measured (SRC-04) | 26.04 kHz | CHAIN-EXP-001, CHAIN-EXP-019 |
| C-02 | "Reconstruction filter deliberately omitted" (SRC-06 relaying Rossum) versus "Output filter is order 5" (SRC-04); "six of eight voices had a 4-pole low-pass" (tertiary wiki); "simple low-pass" on 3–6 (owners) | Channel dependent: none on 7–8, fixed low-pass on 3–6, SSM2044 on 1–2. Orders UNKNOWN | CHAIN-EXP-004, CHAIN-EXP-019 |
| C-03 | Owner's manual: plug type selects filtered vs unfiltered (SRC-03 excerpt, wording ambiguous in the extract) versus Folklore: insert the plug halfway | Contact mapping UNRESOLVED | CHAIN-EXP-004, CHAIN-EXP-019 |
| C-04 | Tertiary wiki: analog VCA + ADSR per voice versus SRC-09: level by multiplying DAC; SRC-04: digital decay envelope | No classical VCA; level DAC PROVISIONAL | CHAIN-EXP-019 |
| C-05 | "12-bit" resolution (popular) versus SRC-04: output imaging and tuning algorithm dominate | Mechanism view adopted; "12-bit" rejected as a specification | CHAIN-EXP-002, CHAIN-EXP-004 |
| C-06 | "Neutral, no sound of its own" (SRC-28) versus "Very lo-fi, distinct" (SRC-28) | UNRESOLVED | CHAIN-EXP-009, CHAIN-EXP-010, CHAIN-EXP-014 |
| C-07 | ~15 kHz attenuation onset on SP-12 (SRC-04) versus "Upper limit around 14 kHz" (SRC-08 fragment, garbled) | UNKNOWN for SP-1200 | CHAIN-EXP-002, CHAIN-EXP-019 |
| C-08 | "8-bit" (forum post) versus 12-bit linear (SRC-05) | 12-bit; source A discarded | — |

| Audit ID | Issue | Locators | Disposition / impact | Decision owner/gate |
|---|---|---|---|---|
| AUD-C01 | Product selection wording | §2 and CHAIN-DEC-001 NOT CHOSEN; §22 recommends B only for reference; JSON status WITH_CONDITIONS | B is reference superset only; A/B/C shipping choice OPEN. No approval inferred. | G-07; owner S5 |
| AUD-C02 | Selected outputs versus evidence | CHAIN-DEC-003 default UNDECIDED; §20 recommends MPC main stereo | SP default OPEN; MPC main proposed, not formally selected; ch7–8 unfiltered is explicit research fixture, never factory default. | RD-P0-04; G-07 |
| AUD-C03 | 192 kHz capture cannot measure 208.33 kHz spur directly | §30 capture Nyquist 96 kHz; CHAIN-EXP-006 hypothesis at 208.33 kHz | Use wideband acquisition with sufficient bandwidth/sample rate or log NOT OBSERVABLE. Do not infer spur absence from 192k data. In-band noise still required. | RD-P1-06; S2 operator |
| AUD-C04 | ADC 18→16 reduction is not identifiable from 16-bit digital input alone | §14 YM3623B 16-bit output; CHAIN-EXP-008 says select R13 via S/PDIF + analog | S/PDIF checks receiver/storage bits. Analog low-level data may distinguish composite candidates; if internal rule cannot be isolated, retain UNKNOWN and gate affected claim. | RD-P0-05; S2/S4 reviewer |
| AUD-C05 | Overload recovery is P2 but a P1 prerequisite includes it | RD-P2-04 versus RD-P1-02 and §26 MPC ADC recovery UNKNOWN | No wholesale priority relabeling. Initial onset/recovery characterization is mandatory for driven modes; deeper dynamics P2 only if residual/safety evidence permits. | G-05/G-08; owner |
| AUD-C06 | No simulation run versus SIMULATED tag | Header simulations NO; arithmetic SP12-CLM-019/020 and ratios SIMULATED | Preserve source status; tag derived evaluation CLOSED-FORM ARITHMETIC, NOT EXECUTED numerical experiment. It does not establish a simulation run. | Docs authority clarification |
| AUD-C07 | Reference readiness language could be read as fidelity readiness | JSON reference WITH_CONDITIONS versus §41 invalid SP model without AA filter and §42 HARDWARE REQUIRED | Skeleton is research harness only; production/calibrated-reference readiness BLOCKED. No claim of a validated machine model. | G-05/G-06 |
| AUD-C08 | Ideal sampler state listed as None while rate scheduler must retain phase | §28/JSON R4 states None; §25 sample sequence/block-size invariance | Physical ideal sampler has no signal memory, but implementation retains clock/phase/count/resampler history. Explicit scheduler state in ARCHITECTURE; not new coloration. | REQ-019; architecture proposal |
| AUD-C09 | Host-rate invariance needs a common-input definition | §25 absolute host-independent sample sequence; finite host representations differ | Use identical continuous-time analytic/common-band input, fixed phase and reconstruction. Exact cross-rate code equality near quantizer boundaries not assumed; G-08 numeric policy required. | REQ-019; validation lead |
| AUD-C10 | Pilot, capture-length and warm-up plan incomplete | §30 10s sweep versus SP ≤2.3s including pilots; warm-up threshold unspecified | Freeze segmentation/pilot budget, cycles/settling validity and observed warm-up/drift criterion before campaign. Captures that cannot meet them are invalid/pending. | G-04; S2 operator |
| AUD-C11 | Gain normalization differs by purpose | §32 calibration-tone scalar for null; §33 program RMS for listening | Separate analysis branches: calibration only for fidelity null; logged excerpt-RMS gain only for blind listening. No shared normalized capture replaces raw data. | G-02/G-06; validation engineer |

## Evidence limits and readiness

Documentary VERIFIED is not this project's hardware measurement. SP-12 results stay sibling-machine literature; transfer to SP-1200 is RD-P1-09. Datasheet capability is not installed unit behavior. The MPC coloration claim MPC3K-CLM-020 remains UNKNOWN; a neutral measured result is a valid outcome and must not cause invented saturation. Channel orders, rails, nominal/max levels and filter coefficients remain unknown where the research says so.

Reference skeleton readiness: WITH CONDITIONS as reported, not executed. Calibrated reference: BLOCKED by G-04/G-05/G-06. Production: BLOCKED by those and G-07/G-08/G-09. Planning package: complete files, draft contracts, execution readiness intentionally BLOCKED. Full claim register is CONFIDENCE.md; full debt is RESEARCH_DEBT.md; hardware/human gates are GATE_REGISTER.md; replaceable modules are ARCHITECTURE.md. No primary source fetch, listening, hardware work or simulation occurred in this planning task.

## Targeted next research, without broad restart

Prioritize readable SRC-01 sheets pp67–88; SRC-20 AD/DA 13-3 L401203 and 8DACS13-4 L401204M; AD7541 grade/timing, AK5328 and SM5841 responses; SRC-01/SRC-02 comparison if sibling equivalence is used. Preserve access failures and rights: SP manual owner-use-only notice means consultation, no redistributed scan. Hardware stock-unit campaign is irreplaceable for calibration/clip/noise/cascade. No documents prove the unit behavior by themselves.
