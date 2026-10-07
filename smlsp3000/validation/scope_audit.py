"""VAL-018 / REQ-018 scope audit: unity pitch and sampler non-goals (software inspection)."""
from __future__ import annotations

import io
import json
import re
import tokenize
from dataclasses import fields
from pathlib import Path

from .. import environment as env
from ..reference import sp1200
from ..reference.assets import load_asset, load_research_config

FORBIDDEN_TOKENS = {
    "tuned playback / pitch": re.compile(r"\b(pitch|tuning|semitone|drop_sample|playback_rate)\b", re.I),
    "reverse order product": re.compile(r"\b(mpc_to_sp|reverse_order)\b", re.I),
    "SSM2044 / dynamic filter": re.compile(r"\b(ssm2044|ssi2144|vcf|envelope_filter)\b", re.I),
    "noise / jitter / mismatch / sag": re.compile(r"\b(random|rng|jitter|noise_floor|mismatch|sag|hysteresis|tanh)\b", re.I),
    "limiter / normalization": re.compile(r"\b(limiter|normalize_loudness|auto_gain)\b", re.I),
    "sampler workflow": re.compile(r"\b(loop_points|velocity|sequencer|voice_alloc)\b", re.I),
}


def run(out_path: str | Path, command: str) -> dict:
    src_dir = Path(sp1200.__file__).resolve().parent
    hits = {}
    for py in sorted(src_dir.glob("*.py")):
        text = py.read_text(encoding="utf-8")
        toks = [t.string for t in tokenize.generate_tokens(io.StringIO(text).readline) if t.type not in (tokenize.COMMENT, tokenize.STRING, tokenize.NL, tokenize.NEWLINE)]
        code_only = " ".join(toks)  # identifiers/keywords only; docstrings and comments excluded
        for label, rx in FORBIDDEN_TOKENS.items():
            for m in rx.finditer(code_only):
                hits.setdefault(label, []).append(f"{py.name}: {m.group(0)}")
    # Sprint 6: the native production core is audited with the same tokens (C/C++ comments and string literals stripped)
    native_root = Path(sp1200.__file__).resolve().parents[2] / "native"
    native_files = sorted(list((native_root / "include").rglob("*.hpp")) + list((native_root / "src").glob("*.cpp")) + list((native_root / "tools").glob("*.cpp")) + list((native_root / "generated").glob("*.hpp")))
    strip_rx = re.compile(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"', re.S)
    for cpp in native_files:
        code_only = strip_rx.sub(" ", cpp.read_text(encoding="utf-8"))
        for label, rx in FORBIDDEN_TOKENS.items():
            for m in rx.finditer(code_only):
                hits.setdefault(label, []).append(f"native/{cpp.relative_to(native_root)}: {m.group(0)}")
    asset, asha = load_asset()
    cfg, rsha = load_research_config()
    product_fields = [f.name for f in fields(sp1200.SPProductParameters)]
    rec = {
        "check_id": "VAL-018", "requirement_id": "REQ-018", "track": "A", "artifact_class": "SIMULATION",
        "asset_identity": {"asset_id": asset["asset_id"], "version": asset["version"], "model_version": asset["model_version"], "sha256": asha},
        "research_config_sha256": rsha, "software": env.software_record(), "source_commit": env.git_describe(), "command": command,
        "inspection": {
            "product_parameters": product_fields,
            "no_pitch_parameter": not any("pitch" in f or "tun" in f for f in product_fields),
            "r6_machine_domain": "identity at unity (no tuned-playback block)",
            "quantizer_rules_registered": sorted(sp1200.QUANTIZER_RULES),
            "r3_strategies_registered": sorted(sp1200.R3_STRATEGIES), "r3_reserved_slots_not_populated": list(sp1200.R3_RESERVED_SLOTS),
            "r8_routes_registered": sorted(sp1200.R8_ROUTES),
            "asset_routes_status": {k: v["status"] for k, v in asset["values"]["output_routes"]["value"].items()},
            "research_switches": cfg["switches"],
            "forbidden_token_hits_in_reference_code": hits,
            "chain_order": "SP → MPC product order; reverse order only behind the research switch reverse_order_research (never product)",
            "native_files_audited": [str(f.relative_to(native_root)) for f in native_files],
            "noise_jitter_mismatch_sag_limiter": "none implemented",
        },
        "outcome": "PASS" if (not hits and not any("pitch" in f for f in product_fields)) else "FAIL",
        "hardware_fit_outcome": "NOT RUN",
        "timestamp_utc": env.utc_now(),
    }
    out = Path(out_path); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rec, indent=1, sort_keys=True), encoding="utf-8")
    return rec
