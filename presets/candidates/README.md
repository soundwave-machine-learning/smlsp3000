# Preset candidates (development; NOT a factory bank)

Candidate preset files written by the SML SP-3000 Preset Lab (docs/PRESET_LAB.md; format docs/PRESET_FORMAT.md). Nothing here is read by the plugin, nothing is part of the plugin state, and nothing is a factory preset.

* `demo/` — four tool demonstrations (`acceptance_status` TOOL_DEMO) used for the Preset Lab screenshots and tests. Their numbers are illustrative only: not auditioned by the owner, not recommendations, not factory presets.
* Owner-authored candidates are saved here as `<id>_r<revision>.json`; `MANIFEST.json` is produced by the lab's Export manifest.
* `character_audit/` — eight rule-derived CHARACTER-AUDIT STARTING POINTS (INIT, SP LIGHT, SP HARD, MPC LIGHT, MPC HARD, DUAL LIGHT, DUAL MEDIUM, DUAL HARD; status DRAFT, not auditioned, not tuned by preference, not factory presets). Linux-render telemetry on the synthetic demo beat: evidence/preset_lab/character_audit/.
* `foundations/` — five OWNER-APPROVED foundational directions (CLEAN PRINT, DUSTED SOUL, DRUM AUTHORITY, MPC PRESSURE, DUAL MACHINE; status AUDITIONED, owner ratings not yet recorded, not factory presets). docs/DRUM_IMPACT_AUTHORING.md.
* `drum_authority_2001/` — the 2001 DRUM AUTHORITY exploration family (working name; creative listening reference, no emulation claim): root = DRUM AUTHORITY plus one-control variations A–E, status DRAFT, not auditioned; `AUDITION_LOG.csv` is the owner's rating log. Windows synthetic-beat preparation telemetry: evidence/preset_lab/drum_authority_2001_windows_demo_telemetry.json.
* Owner lab-saved files at this level (`ca_dual_light_r2/r3`, `ca_mpc_light_r2/r3/r4`, `cand_46417de5f6cf_r1`) are preserved as saved; their inherited description text is stale (see the authoring guide).
* Intensity words in the `character_audit/` names (LIGHT/MEDIUM/HARD) are not classifications: the owner found `ca_dual_light_r1` clearly too hot. Intensity classes come from owner audition only (docs/DRUM_IMPACT_AUTHORING.md).
