# Parameter layers, candidate IDs and state policy

Revision: execution V3 (Sprint 3) · 2026-10-07 · supersedes execution V2

Status: EXECUTION IN PROGRESS. Sprint 3 implemented the SP subset of ProductParameters as an explicit record with no defaults (`SPProductParameters`: sp_input_level_db, sp_input_gain ∈ {0,20,40}, sp_output_path, calibration_mode ∈ {NORMALIZED_RESEARCH, PHYSICAL}); MachineParameters as the versioned asset `sp1200-track-a-provisional` v1 (every value tagged per EXECUTION_PLAN_V2 §5); ResearchConfiguration as `sp-track-a-research-config` v1 (quantizer rule/offset/bypass, R3 strategy, hold fraction, proxy oversampling, kernels, slot skew, capture offset, taps). Ranges/defaults/smoothing/automation for product release remain UNKNOWN (G-07S/G-08); nothing here is a plugin control.

## Status and freeze point

These are candidate stable identifiers for engineering review, not created plugin controls or approved parameter mappings. Research gives dimensions, not ranges/defaults/UI. All numeric product ranges/defaults/smoothing and pot mappings are UNKNOWN until G-07/G-08. Schema version and released parameter IDs are frozen before S6 automation/state tests. UNSET is a blocked configuration, not0dB. No generic Amount/Drive macro, dry/wet or hidden loudness control is inferred.

## ProductParameters candidates

| Candidate stable ID | Type / unit | Meaning / boundary | Range / default | Mapping / smoothing | Basis |
|---|---|---|---|---|---|
| input_calibration_dbfs | float / dBFS reference | Named source calibration reference for physical voltage; may be fixed setting instead of automateable | UNKNOWN / UNSET | Derived from documented volts-per-unit convention; automation policy UNKNOWN | §43; R0 |
| sp_input_level_db | float / dB | Source-level trim at SP input, not rail/saturation macro | UNKNOWN / UNSET | Linear10^(dB/20) at named input; smoothing time UNKNOWN | CHAIN-DEC-012; R2 |
| sp_input_gain | enum / dB | Machine0,+20,+40dB setting | supported candidates0/20/40; product default UNKNOWN | discrete state; transition policy UNKNOWN | SP12-CLM-018 |
| sp_output_path | enum | NONE_CH7_8 / FIXED_CH5_6 / FIXED_CH3_4; MIX_OUT only if separately approved/measured | supported measured routes only; default UNDECIDED | choose path-specific immutable coefficients; no interpolation between circuits | CHAIN-DEC-003 |
| interstage_level_db | float / dB | Calibrated effective MPC record-level trim from SP output volts | UNKNOWN / UNSET | One physically named gain; no second hidden pot multiplier | CHAIN-DEC-014; R10/R11 |
| mpc_input_gain | enum | LO/MID/HI machine gain position | candidate states; default UNKNOWN | measured switch gains, not sensitivity-as-FS; transition UNKNOWN | MPC3K-CLM-007 |
| output_trim_db | float / dB | Final host output trim | UNKNOWN / UNKNOWN | Linear10^(dB/20); smoothing time UNKNOWN | §43; R16 |
| chain_mode | enum | CASCADE / SP_ONLY / MPC_ONLY / BOTH_MACHINE_BYPASSED | candidate routing; default UNKNOWN | machine-wide bypass with latency/state semantics; G-07 freeze | §43 |
| plugin_bypass | bool | Latency-aligned dry bypass | host/user policy UNKNOWN | separate from chain mode; G-09 verify | §43 |

Main stereo MPC output can remain a fixed selected MachineParameters route rather than another user switch; G-07 decides. Calibration setting versus automatable trim must not become two controls for the same physical gain accidentally. Interstage record-level effect is represented exactly once. Physical input gain enum in ProductParameters is a selected machine state; its voltage transfer curves remain immutable MachineParameters.

## MachineParameters — versioned calibrated assets

sp_rate_hz/provenance; mpc_rate_hz; input volts-per-normalized-unit; SP input gain curves and ADC_FS/offset/code range; AA poles/zeros/order; SP level-DAC unity; hold response/fraction; output route/gain/coupling; interstage canonical reference gain; MPC input sensitivity-to-FS curves/pot calibration; ADC response/latency/FS/overload; 18→16 rule and unity arithmetic once identifiable; DAC interpolation/de-emphasis configuration; I/V/output filter/coupling/gain/FS; measured revision/route/OS; asset ID/version/hash and validity conditions. Every value retains source/experiment/uncertainty and permitted range; no user preset rewrites it. Unknown assets cannot be initialized with fabricated numbers. Under OWN-DEC-001 a Track A asset may hold a provisional value only with the tags of docs/EXECUTION_PLAN_V2.md §5 (substitute_kind, UNVALIDATED AGAINST HARDWARE, decision ID, replacing experiment, model version); the serialized state references asset ID + version + hash so a later fitted asset is distinguishable from the provisional one.

## ResearchConfiguration — explicit hypothesis strategies

SP encoding/rounding/offset variants, ideal full-period versus measured hold, provisional clock override, diagnostic block bypass and inactive placeholders; MPC reduction candidates, identity arithmetic, converter response alternatives/de-emphasis hypothesis; slot skew and capture phase offsets; proxy rate/kernel/precision convergence controls; normalized research calibration. Explicit config required for research fixtures. No hypothesis hidden in UI/preset; release build cannot change them. Source exclusions remain excluded even if a research switch would be technically possible.

## Persistence and automation

Preset stores approved ProductParameters plus schema version and immutable calibration identity; no ResearchConfiguration or coefficients. Session serialization may reference selected machine asset but not alter it. Reject unknown/unsupported future versions with documented behavior; migrate known schema versions with fixed mappings and round-trip evidence. Freeze normalized host automation mappings (including endpoints, units and enum ordering) at G-08; tests cover sample-offset automation, rapid switches, restore and offline bounce. No invented factory preset is created now. Later presets declare headroom class, named trim meanings and any abstract stereo semantics.
