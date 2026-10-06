"""SHA-256 hashing of files, byte strings and numpy arrays; manifest read/write.

Manifest format (``manifest.sha256``): one entry per line,
``<sha256>  <relative/path>`` — compatible with ``sha256sum -c``.
Array hashes are taken over the raw little-endian bytes of the array in C
order together with a header string ``dtype|shape`` so that the same numbers
in a different dtype or shape do not collide.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Iterable

import numpy as np

CHUNK = 1 << 20


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | os.PathLike) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(CHUNK)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def sha256_array(a: np.ndarray) -> str:
    a = np.ascontiguousarray(a)
    le = a.dtype.newbyteorder("<") if a.dtype.byteorder in (">", "=") and a.dtype.itemsize > 1 else a.dtype
    data = a.astype(le, copy=False).tobytes(order="C")
    header = f"{le.str}|{a.shape}".encode()
    h = hashlib.sha256()
    h.update(header)
    h.update(data)
    return h.hexdigest()


def write_manifest(root: str | os.PathLike, paths: Iterable[str | os.PathLike], manifest_name: str = "manifest.sha256") -> Path:
    """Hash each path (relative to root) and write a sha256sum-compatible manifest.

    The manifest itself is excluded from its own listing.
    """
    root = Path(root)
    lines = []
    for p in sorted(str(Path(p)) for p in paths):
        if p == manifest_name:
            continue
        lines.append(f"{sha256_file(root / p)}  {p}")
    out = root / manifest_name
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def read_manifest(path: str | os.PathLike) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.rstrip("\n")
        if not line.strip():
            continue
        digest, _, rel = line.partition("  ")
        entries[rel.strip()] = digest.strip()
    return entries


def verify_manifest(root: str | os.PathLike, manifest_name: str = "manifest.sha256") -> dict[str, str]:
    """Return {path: 'OK' | 'MISMATCH' | 'MISSING'} for every manifest entry."""
    root = Path(root)
    result: dict[str, str] = {}
    for rel, digest in read_manifest(root / manifest_name).items():
        p = root / rel
        if not p.exists():
            result[rel] = "MISSING"
        elif sha256_file(p) != digest:
            result[rel] = "MISMATCH"
        else:
            result[rel] = "OK"
    return result
