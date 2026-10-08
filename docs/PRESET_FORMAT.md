# SML SP-3000 preset candidate format (development manifest, schema 1)

Revision: V1 · 2026-10-08

Scope: files written and read by the Preset Lab (docs/PRESET_LAB.md). This is a **development** format. It is not the plugin state (SMLSP3000_STATE_V1 wrapping the native schema v1, docs/PARAMETERS.md), it is not a factory bank, and nothing in it is read by the plugin. The native state schema is unchanged.

## File

One candidate per UTF-8 JSON file, `presets/candidates/<id>_r<revision>.json`, at most 256 KiB. Example:

```json
{
  "format": "smlsp3000-preset-candidate",
  "schema": 1,
  "id": "cand_3f9a1c2b7d4e",
  "name": "Example name",
  "category": "SP CHARACTER",
  "revision": 2,
  "product_parameters": {
    "sp_input_level_db": 4.5,
    "sp_input_gain_db": 0,
    "interstage_level_db": -2.0,
    "mpc_input_gain": "LO",
    "output_trim_db": -4.5,
    "plugin_bypass": false
  },
  "authoring_metadata": {
    "author": "owner",
    "description": "what it is for",
    "audition_notes": "what was heard, on which material",
    "clamp_observations": "SP 12-bit clamps: L 120 R 131 ...",
    "engineering_note": "",
    "source_material": ["beat_a.wav (sha256 ...)", "beat_b.wav"],
    "acceptance_status": "AUDITIONED",
    "input_peak": 0.89,
    "output_peak": 0.71,
    "created_utc": "2026-10-08T12:00:00Z",
    "modified_utc": "2026-10-08T12:30:00Z",
    "tool_version": "smlsp3000-preset-lab-0.1.0",
    "native_core_version": "smlsp3000-native-core-1.0.0",
    "adapter_version": "smlsp3000-host-adapter-1.0.0"
  }
}
```

## Fields

| Key | Type | Rule |
|---|---|---|
| `format` | string | must be `smlsp3000-preset-candidate` (else NOT_A_CANDIDATE) |
| `schema` | integer | must be 1; a larger value is UNSUPPORTED_SCHEMA_VERSION (no migration exists), a non-integer is MALFORMED_SCHEMA |
| `id` | string | 1–64 characters of `[A-Za-z0-9_-]`; stable across revisions (BAD_ID) |
| `name` | string | non-empty, ≤ 128 characters (BAD_NAME) |
| `category` | string | one of UTILITY, CLEAN, SP CHARACTER, MPC CHARACTER, DUAL STAGE, DRUMS, BASS, SAMPLE / DENSE, HEAVY, EXPERIMENTAL (UNKNOWN_CATEGORY). Authoring categories only; none implies hardware authenticity |
| `revision` | integer ≥ 1 | a changed candidate is saved as revision + 1 unless explicitly overwritten (BAD_REVISION) |
| `product_parameters` | object | exactly the six keys below, **physical values** |
| `authoring_metadata` | object | the keys listed below; all optional; any other key is rejected |

`product_parameters` (exactly these keys; any other key, including research or hidden parameters, is UNKNOWN_KEY; a missing key is MISSING_FIELD):

| Key | Type | Values | Note |
|---|---|---|---|
| `sp_input_level_db` | number | −60.0 … +12.0 | dB |
| `sp_input_gain_db` | integer | 0, 20 or 40 | the physical step in dB — **not** the choice index (an index such as 1 is UNKNOWN_ENUM) |
| `interstage_level_db` | number | −60.0 … +24.0 | dB |
| `mpc_input_gain` | string | `LO`, `MID`, `HI` | the enum name — not an index (relative gain 0 / +20 / +40 dB) |
| `output_trim_db` | number | −60.0 … +12.0 | dB |
| `plugin_bypass` | boolean | true / false | numeric 0/1 is rejected |

Value validation is delegated to the native core: the lab writes the six values into a schema-v1 state text and runs the core's own parser (`Engine::parse_state`), so the accepted set is exactly what the plugin accepts (OUT_OF_RANGE, UNKNOWN_ENUM, NON_FINITE_OR_MALFORMED). INIT is `0.0 / 0 / 0.0 / LO / 0.0 / false`.

`authoring_metadata` keys: `author`, `description`, `audition_notes`, `clamp_observations`, `engineering_note` (strings); `source_material` (array of strings); `acceptance_status` (DRAFT, AUDITIONED, CANDIDATE, REJECTED, TOOL_DEMO); `input_peak`, `output_peak` (finite numbers, linear sample peaks observed on the last audition render; −1 = not recorded); `created_utc`, `modified_utc`, `tool_version`, `native_core_version`, `adapter_version` (strings). Metadata never influences the audio (tested).

## Rejection policy

A candidate is parsed completely before anything is applied. Any rejection (listed codes above plus MALFORMED_JSON, OVERSIZED, MALFORMED_METADATA, IO) leaves the lab's current values untouched — no partial application.

## Manifest

`presets/candidates/MANIFEST.json` (written by Export manifest): `record` = `smlsp3000-preset-candidate-manifest`, `schema` 1, `generated_utc`, `tool_version`, and `candidates`: one entry per JSON file under presets/candidates/ with `file`, `valid`, `id`, `name`, `category`, `revision`, `acceptance_status` (or `reject_code`) and the file's `sha256`. It is a review aid, not a bank.

## Render record

`reference/preset_lab/renders/<id>_r<rev>/<source>_<rate>.render.json` (`record` = `smlsp3000-preset-lab-render`, schema 1): see docs/PRESET_LAB.md "Headless modes". The WAV next to it is 32-bit float; the float64 sample hash (`output_f64_sha256`) is the deterministic identity of the render.

## Relation to the plugin state

| | Candidate file | Plugin state (SMLSP3000_STATE_V1) |
|---|---|---|
| Written by | Preset Lab | the plugin (host session) |
| Contains | six physical values + authoring metadata | six values + model identity, schema 1 |
| Read by the plugin | never | yes |
| Factory bank | no | no (INIT only) |

Turning candidates into a factory bank is a later, owner-approved step that will define how (and whether) candidate values enter the plugin; it is not implied by this format.
