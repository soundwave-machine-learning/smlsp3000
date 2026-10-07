"""Offline rendering with provenance (docs/ARCHITECTURE.md offline renderer).

``render_offline`` prepares an engine, processes the whole input (optionally in
caller-chosen block sizes), drains the implementation delay, aligns the output
to the input by the reported integer latency and returns the output plus a
render record (asset identity, research configuration hash, input/output
hashes, software, commit, model implementation version).
"""
from __future__ import annotations

import numpy as np

from .. import environment as env
from ..hashing import sha256_array
from .assets import load_asset, load_research_config
from .sp1200 import MODEL_IMPLEMENTATION_VERSION, SPProductParameters, SPReferenceEngine


def with_switches(research: dict, **overrides) -> dict:
    """Return a copy of a research configuration with explicit switch overrides (never implicit)."""
    sw = dict(research["switches"])
    for k, v in overrides.items():
        if k not in sw:
            raise KeyError(f"unknown research switch {k!r}")
        sw[k] = v
    return {**research, "switches": sw}


def render_offline(x: np.ndarray, host_rate_hz: int, product: SPProductParameters, research: dict | None = None,
                   asset: dict | None = None, block_sizes: list[int] | None = None, align: bool = True):
    """Returns (y aligned to x, info, record, engine)."""
    if asset is None:
        asset, asha = load_asset()
    else:
        from .assets import canonical_bytes
        from ..hashing import sha256_bytes
        asha = sha256_bytes(canonical_bytes(asset))
    if research is None:
        research, rsha = load_research_config()
    else:
        from .assets import canonical_bytes
        from ..hashing import sha256_bytes
        rsha = sha256_bytes(canonical_bytes(research))
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        x = x[:, None]
    eng = SPReferenceEngine()
    info = eng.prepare(host_rate_hz, x.shape[1], asset, asha, product, research, rsha)
    outs = []
    if block_sizes is None:
        outs.append(eng.process(x))
    else:
        i = 0
        for n in block_sizes:
            if i >= x.shape[0]:
                break
            outs.append(eng.process(x[i:i + n]))
            i += n
        if i < x.shape[0]:
            outs.append(eng.process(x[i:]))
    outs.append(eng.drain())
    y_full = np.concatenate(outs, axis=0)
    y = y_full[info.latency_host_samples:info.latency_host_samples + x.shape[0]] if align else y_full
    record = {
        "model_implementation_version": MODEL_IMPLEMENTATION_VERSION,
        "asset_identity": info.asset_identity,
        "research_config_sha256": rsha,
        "product_parameters": product.__dict__,
        "host_rate_hz": host_rate_hz,
        "latency_host_samples": info.latency_host_samples,
        "fidelity": info.fidelity,
        "input_sha256": sha256_array(x),
        "output_sha256": sha256_array(y),
        "software": env.software_record(),
        "source_commit": env.git_describe(),
        "meters": eng.meters(),
    }
    return y, info, record, eng
