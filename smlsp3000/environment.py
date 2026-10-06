"""Environment and provenance capture for result records."""
from __future__ import annotations

import datetime as _dt
import platform
import subprocess
import sys

import numpy as np

from . import __version__


def git_describe(cwd: str = ".") -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()
        return out + ("-dirty" if dirty else "")
    except Exception:  # noqa: BLE001 - provenance must never crash a run
        return "UNKNOWN"


def software_record() -> dict:
    return {
        "smlsp3000": __version__,
        "python": sys.version.split()[0],
        "numpy": np.__version__,
    }


def environment_record() -> dict:
    return {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor() or "UNKNOWN",
        "python_implementation": platform.python_implementation(),
    }


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()
