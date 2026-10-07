"""Loading, validation and hashing of machine assets and research configurations."""
from __future__ import annotations

import json
from pathlib import Path

from ..hashing import sha256_bytes
from ..schemas import RESEARCH_CONFIGURATION, UNSET, validate, validate_machine_asset
from .errors import InvalidConfiguration

ASSET_DIR = Path(__file__).resolve().parent / "assets"


def canonical_bytes(record: dict) -> bytes:
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


DEFAULT_ASSETS = {"SP-1200": "sp1200_provisional_v1.json", "MPC3000": "mpc3000_provisional_v1.json"}
DEFAULT_RESEARCH_CONFIGS = {"SP-1200": "research_config_sp_track_a_v1.json", "MPC3000": "research_config_mpc_track_a_v1.json"}


def load_asset(path: str | Path | None = None, machine: str = "SP-1200") -> tuple[dict, str]:
    """Load + validate a machine asset; returns (asset, sha256 of canonical bytes)."""
    path = Path(path) if path else ASSET_DIR / DEFAULT_ASSETS[machine]
    asset = load_json(path)
    problems = validate_machine_asset(asset)
    if problems:
        raise InvalidConfiguration("ASSET_INVALID", "; ".join(problems))
    return asset, sha256_bytes(canonical_bytes(asset))


def load_research_config(path: str | Path | None = None, machine: str = "SP-1200") -> tuple[dict, str]:
    path = Path(path) if path else ASSET_DIR / DEFAULT_RESEARCH_CONFIGS[machine]
    cfg = load_json(path)
    problems = validate(cfg, RESEARCH_CONFIGURATION, strict=False)
    if problems:
        raise InvalidConfiguration("RESEARCH_CONFIG_INVALID", "; ".join(problems))
    return cfg, sha256_bytes(canonical_bytes(cfg))


def asset_value(asset: dict, name: str):
    """Return the value of an asset entry; UNSET raises INVALID_CONFIGURATION (blocked configuration)."""
    try:
        rec = asset["values"][name]
    except KeyError as e:
        raise InvalidConfiguration("ASSET_MISSING_VALUE", f"asset has no value {name!r}") from e
    if rec["value"] == UNSET:
        raise InvalidConfiguration("ASSET_VALUE_UNSET", f"{name} is UNSET ({rec.get('note', '')})")
    return rec["value"]


def asset_identity(asset: dict, sha: str) -> dict:
    return {"asset_id": asset["asset_id"], "version": asset["version"], "model_version": asset["model_version"], "sha256": sha}
