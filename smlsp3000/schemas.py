"""Immutable record schemas for experiments, units, captures, assets and configs.

These are deliberately dependency-free (no jsonschema). A schema is a mapping
``field -> FieldSpec``. ``validate`` returns a list of human-readable problems;
an empty list means the record conforms. Records are plain dicts so they can be
written as JSON sidecars.

Authority lanes (docs/CONFIDENCE.md, AGENTS.md): a record *describes* evidence;
it never promotes it. The ``artifact_class`` and ``dataset_role`` vocabularies
are frozen here so that a SIMULATION can never be filed as a HARDWARE
MEASUREMENT by accident.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# --- frozen vocabularies -------------------------------------------------------

ARTIFACT_CLASSES = (
    "SOURCE EVIDENCE",
    "SIMULATION",
    "HARDWARE MEASUREMENT",
    "FIT RESULT",
    "VALIDATION RESULT",
    "LISTENING STIMULUS",
    "REFERENCE AUDIO",
)

DATASET_ROLES = ("FIT", "VALIDATION", "SELF_NULL", "NONE")

EVIDENCE_STATUSES = (
    "VERIFIED",
    "STRONGLY SUPPORTED",
    "LITERATURE-DERIVED",
    "SIMULATED",
    "PROVISIONAL",
    "SPECULATIVE",
    "UNKNOWN",
    "NOT EXECUTED",
)

EXPERIMENT_OUTCOMES = ("PASS", "FAIL", "BLOCKED", "NOT EXECUTED", "INFORMATIONAL")

#: Track A implementation tags (docs/EXECUTION_PLAN_V2.md §5; OWN-DEC-001). They never change an
#: evidence status; they describe why a provisional software value exists.
SUBSTITUTE_KINDS = ("PROVISIONAL", "LITERATURE-DERIVED", "SIMULATED", "ESTIMATE", "VERIFIED-FORMAT", "INACTIVE", "NOT POPULATED")
HARDWARE_VALIDATION_TAGS = ("UNVALIDATED AGAINST HARDWARE", "HARDWARE-FIT")
TRACKS = ("A", "B")

DEBT_STATES = ("OPEN", "PARTIAL", "CLOSED", "NOT APPLICABLE WITH APPROVED SCOPE")

#: Sentinel for a calibration/asset value that has no evidence yet. A record may
#: carry UNSET explicitly; it is a *blocked configuration*, never 0 dB / unity.
UNSET = "UNSET"


@dataclass(frozen=True)
class FieldSpec:
    types: tuple[type, ...]
    required: bool = True
    choices: tuple[Any, ...] | None = None
    allow_unset: bool = False
    doc: str = ""


def _t(*types: type, required: bool = True, choices=None, allow_unset: bool = False, doc: str = "") -> FieldSpec:
    return FieldSpec(types=types, required=required, choices=choices, allow_unset=allow_unset, doc=doc)


# --- schemas ---------------------------------------------------------------------

#: One entry of an artifact hash manifest (docs/MEASUREMENT_PLAN.md).
ARTIFACT_ENTRY = {
    "path": _t(str, doc="repository-relative or evidence-route-relative path"),
    "sha256": _t(str),
    "bytes": _t(int),
    "artifact_class": _t(str, choices=ARTIFACT_CLASSES),
    "dataset_role": _t(str, choices=DATASET_ROLES),
}

#: Experiment result record (docs/EXPERIMENT_PLAN.md “Result record”).
EXPERIMENT_RESULT_RECORD = {
    "experiment_id": _t(str, doc="CHAIN-EXP-NNN"),
    "question": _t(str),
    "hypothesis": _t(str),
    "requirement_ids": _t(list),
    "debt_ids": _t(list),
    "artifact_class": _t(str, choices=ARTIFACT_CLASSES),
    "dataset_role": _t(str, choices=DATASET_ROLES),
    "input_config_sha256": _t(str),
    "unit_routes": _t(str, dict, doc="N/A for simulation"),
    "software": _t(dict, doc="package version, python, numpy, platform"),
    "source_commit": _t(str),
    "environment": _t(dict),
    "command": _t(str),
    "algorithm_version": _t(str),
    "preprocessing_version": _t(str),
    "raw_output_sha256": _t(dict, doc="name -> sha256 of raw arrays/files"),
    "metric_definitions": _t(dict),
    "threshold_policy": _t(dict, doc="revision + status; UNKNOWN thresholds stay UNKNOWN"),
    "uncertainty": _t(dict),
    "results": _t(dict),
    "outcome": _t(str, choices=EXPERIMENT_OUTCOMES),
    "limitations": _t(list),
    "resulting_decision": _t(str),
    "timestamp_utc": _t(str),
}

#: Unit metadata (docs/MEASUREMENT_PLAN.md “Hardware entry conditions”).
UNIT_METADATA = {
    "unit_id": _t(str),
    "machine": _t(str, choices=("SP-1200", "MPC3000")),
    "serial": _t(str),
    "revision": _t(str),
    "board_ids": _t(list, required=False),
    "os_firmware": _t(str),
    "modification_status": _t(str, choices=("STOCK", "REPAIRED_STOCK", "MODIFIED", "UNKNOWN")),
    "modification_notes": _t(str),
    "operator": _t(str),
    "session_id": _t(str),
    "power_on_time_utc": _t(str),
    "ambient_temperature_c": _t(float, int, allow_unset=True),
    "warmup_criterion": _t(str, doc="frozen criterion or UNKNOWN"),
}

#: Capture sidecar (docs/MEASUREMENT_PLAN.md “Fit versus validation split and artifact contract”).
CAPTURE_SIDECAR = {
    "capture_id": _t(str),
    "unit_id": _t(str),
    "session_id": _t(str),
    "machine": _t(str, choices=("SP-1200", "MPC3000", "CASCADE")),
    "revision": _t(str),
    "modification_status": _t(str),
    "os_firmware": _t(str),
    "warmup_minutes": _t(float, int, allow_unset=True),
    "temperature_c": _t(float, int, allow_unset=True),
    "interface": _t(dict, doc="model, calibration volts_per_dbfs in/out, uncertainty, loopback refs"),
    "cables_load": _t(str),
    "path": _t(str, doc="route / contact / output"),
    "pot_switch_positions": _t(dict),
    "photo_refs": _t(list),
    "stimulus_sha256": _t(str),
    "sample_rate_hz": _t(int),
    "bit_depth": _t(int),
    "channels": _t(int),
    "gain_level": _t(dict),
    "pilot": _t(dict, doc="pilot frequencies/durations and clock-ratio estimate"),
    "capture_sha256": _t(str),
    "take": _t(int),
    "dataset_role": _t(str, choices=DATASET_ROLES),
    "artifact_class": _t(str, choices=ARTIFACT_CLASSES),
    "measurement_category": _t(str, choices=("LINEAR", "LEVEL", "DISTORTION", "NOISE", "DIGITAL", "TRANSIENT", "STEREO")),
    "clipping_observed": _t(bool),
    "validity": _t(str, choices=("VALID", "INVALID", "PENDING")),
}

#: One value inside a machine asset (docs/EXECUTION_PLAN_V2.md §5.2). A value without these tags is
#: a "magic value" and fails validation; prepare() must then return INVALID_CONFIGURATION.
ASSET_VALUE = {
    "value": _t(object, allow_unset=True, doc="number, string, list or dict; UNSET = blocked configuration"),
    "unit": _t(str),
    "evidence_status": _t(str, choices=EVIDENCE_STATUSES),
    "substitute_kind": _t(str, choices=SUBSTITUTE_KINDS),
    "hardware_validation": _t(str, choices=HARDWARE_VALIDATION_TAGS),
    "source_ids": _t(list),
    "claim_ids": _t(list),
    "decision_id": _t(str),
    "replaced_by": _t(str, doc="Track B experiment / closure that would replace this value"),
    "uncertainty": _t(str, required=False),
    "permitted_range": _t(str, list, required=False),
    "note": _t(str, required=False),
}

#: Versioned calibrated machine asset (docs/PARAMETERS.md “MachineParameters”).
MACHINE_ASSET = {
    "asset_id": _t(str),
    "version": _t(str),
    "model_version": _t(str),
    "track": _t(str, choices=TRACKS),
    "machine": _t(str, choices=("SP-1200", "MPC3000", "CASCADE")),
    "block_ids": _t(list, doc="R0..R16"),
    "values": _t(dict, doc="name -> ASSET_VALUE record"),
    "provenance": _t(dict, doc="claim_ids, experiment_ids, source_ids, capture_ids, unit_id, route"),
    "validity_conditions": _t(str),
    "normalized_research_calibration": _t(bool, doc="True = non-fidelity skeleton; physical volts UNSET"),
    "sha256": _t(str, required=False),
}

#: Validation record for a software-track check (VAL-NNN software cell).
VALIDATION_RECORD = {
    "check_id": _t(str),
    "requirement_id": _t(str),
    "track": _t(str, choices=TRACKS),
    "artifact_class": _t(str, choices=ARTIFACT_CLASSES),
    "dataset_role": _t(str, choices=DATASET_ROLES),
    "asset_identity": _t(dict, doc="asset_id, version, model_version, sha256"),
    "research_config_sha256": _t(str),
    "software": _t(dict),
    "source_commit": _t(str),
    "environment": _t(dict),
    "command": _t(str),
    "stimulus": _t(dict),
    "method": _t(str),
    "tolerance_policy": _t(dict, doc="how each nonzero bound is derived; UNKNOWN stays UNKNOWN"),
    "results": _t(dict),
    "outcome": _t(str, choices=EXPERIMENT_OUTCOMES),
    "hardware_fit_outcome": _t(str, choices=("BLOCKED", "NOT RUN", "DEFERRED")),
    "limitations": _t(list),
    "timestamp_utc": _t(str),
}

#: Research configuration: every hypothesis switch explicit (docs/PARAMETERS.md).
RESEARCH_CONFIGURATION = {
    "config_id": _t(str),
    "version": _t(str),
    "switches": _t(dict, doc="name -> explicit value or UNSET; no implicit defaults"),
    "normalized_research_calibration": _t(bool, doc="True marks a non-fidelity skeleton run"),
    "notes": _t(str),
}

SCHEMAS = {
    "ARTIFACT_ENTRY": ARTIFACT_ENTRY,
    "ASSET_VALUE": ASSET_VALUE,
    "VALIDATION_RECORD": VALIDATION_RECORD,
    "EXPERIMENT_RESULT_RECORD": EXPERIMENT_RESULT_RECORD,
    "UNIT_METADATA": UNIT_METADATA,
    "CAPTURE_SIDECAR": CAPTURE_SIDECAR,
    "MACHINE_ASSET": MACHINE_ASSET,
    "RESEARCH_CONFIGURATION": RESEARCH_CONFIGURATION,
}

SCHEMA_VERSION = "2"


def validate(record: dict, schema: dict[str, FieldSpec], *, strict: bool = True) -> list[str]:
    """Return a list of problems (empty == valid).

    strict=True also reports unknown fields, so a record cannot silently carry
    an undeclared hypothesis.
    """
    problems: list[str] = []
    if not isinstance(record, dict):
        return ["record is not a dict"]
    for name, spec in schema.items():
        if name not in record:
            if spec.required:
                problems.append(f"missing required field: {name}")
            continue
        v = record[name]
        if v == UNSET:
            if not spec.allow_unset:
                problems.append(f"field {name} is UNSET but UNSET is not permitted here")
            continue
        if object in spec.types:
            pass
        elif not isinstance(v, spec.types) or isinstance(v, bool) and bool not in spec.types:
            problems.append(f"field {name}: expected {[t.__name__ for t in spec.types]}, got {type(v).__name__}")
            continue
        if spec.choices is not None and v not in spec.choices:
            problems.append(f"field {name}: {v!r} not in {spec.choices}")
    if strict:
        for name in record:
            if name not in schema:
                problems.append(f"unknown field: {name}")
    return problems


def is_set(value: Any) -> bool:
    return value != UNSET


def require_set(record: dict, fields: list[str]) -> list[str]:
    """Names of fields that are UNSET/missing — a non-empty list is a BLOCKED configuration."""
    return [f for f in fields if f not in record or record[f] == UNSET]


def validate_machine_asset(asset: dict) -> list[str]:
    """Validate an asset record and every one of its values (no magic values)."""
    problems = validate(asset, MACHINE_ASSET)
    if isinstance(asset.get("values"), dict):
        for name, rec in asset["values"].items():
            if not isinstance(rec, dict):
                problems.append(f"value {name}: not a record")
                continue
            for q in validate(rec, ASSET_VALUE):
                problems.append(f"value {name}: {q}")
            if asset.get("track") == "A" and rec.get("hardware_validation") != "UNVALIDATED AGAINST HARDWARE":
                problems.append(f"value {name}: Track A values must be tagged UNVALIDATED AGAINST HARDWARE")
    return problems
