"""Minimal WAV read/write on the standard library ``wave`` module plus numpy.

Supports PCM 16/24/32-bit integer and IEEE float32 (format tag 3, written via a
small RIFF writer because ``wave`` only writes PCM). Reads return float64 arrays
scaled to [-1, 1) for integer PCM (divide by 2**(bits-1)) and unscaled floats
for float32. Shape is (frames, channels).

This is tooling for stimuli/captures/sidecars; it is not an audio engine.
"""
from __future__ import annotations

import struct
import wave
from pathlib import Path

import numpy as np


def write_wav(path, data: np.ndarray, sample_rate: int, bit_depth: int = 24) -> None:
    data = np.asarray(data)
    if data.ndim == 1:
        data = data[:, None]
    frames, channels = data.shape
    path = Path(path)
    if bit_depth == 32 and np.issubdtype(data.dtype, np.floating):
        _write_float32(path, data.astype("<f4"), sample_rate)
        return
    if bit_depth not in (16, 24, 32):
        raise ValueError("bit_depth must be 16, 24 or 32")
    full = float(2 ** (bit_depth - 1))
    # Explicit clamp to the integer code range: writing is not allowed to wrap.
    codes = np.clip(np.round(data * full), -full, full - 1).astype(np.int64)
    if bit_depth == 16:
        raw = codes.astype("<i2").tobytes()
    elif bit_depth == 24:
        i32 = codes.astype("<i4").tobytes()
        b = np.frombuffer(i32, dtype=np.uint8).reshape(-1, 4)[:, :3]
        raw = b.tobytes()
    else:
        raw = codes.astype("<i4").tobytes()
    with wave.open(str(path), "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(bit_depth // 8)
        w.setframerate(sample_rate)
        w.writeframes(raw)


def _write_float32(path: Path, data: np.ndarray, sample_rate: int) -> None:
    frames, channels = data.shape
    raw = data.tobytes(order="C")
    byte_rate = sample_rate * channels * 4
    fmt = struct.pack("<HHIIHH", 3, channels, sample_rate, byte_rate, channels * 4, 32)
    fact = struct.pack("<I", frames)
    size = 4 + (8 + len(fmt)) + (8 + len(fact)) + (8 + len(raw))
    with open(path, "wb") as f:
        f.write(b"RIFF" + struct.pack("<I", size) + b"WAVE")
        f.write(b"fmt " + struct.pack("<I", len(fmt)) + fmt)
        f.write(b"fact" + struct.pack("<I", len(fact)) + fact)
        f.write(b"data" + struct.pack("<I", len(raw)) + raw)


def read_wav(path):
    """Return (data[frames, channels] float64, sample_rate, bit_depth, format_tag)."""
    path = Path(path)
    with open(path, "rb") as f:
        riff = f.read(12)
        if riff[:4] != b"RIFF" or riff[8:12] != b"WAVE":
            raise ValueError("not a RIFF/WAVE file")
        fmt = None
        data = None
        while True:
            hdr = f.read(8)
            if len(hdr) < 8:
                break
            cid, csize = hdr[:4], struct.unpack("<I", hdr[4:])[0]
            body = f.read(csize)
            if csize % 2:
                f.read(1)
            if cid == b"fmt ":
                fmt = body
            elif cid == b"data":
                data = body
        if fmt is None or data is None:
            raise ValueError("missing fmt or data chunk")
    tag, channels, rate, _, _, bits = struct.unpack("<HHIIHH", fmt[:16])
    if tag == 0xFFFE and len(fmt) >= 26:  # WAVE_FORMAT_EXTENSIBLE: subformat GUID first 2 bytes
        tag = struct.unpack("<H", fmt[24:26])[0]
    if tag == 3 and bits == 32:
        arr = np.frombuffer(data, dtype="<f4").astype(np.float64)
    elif tag == 1 and bits == 16:
        arr = np.frombuffer(data, dtype="<i2").astype(np.float64) / 32768.0
    elif tag == 1 and bits == 24:
        b = np.frombuffer(data, dtype=np.uint8).reshape(-1, 3)
        i32 = (b[:, 0].astype(np.int32) | (b[:, 1].astype(np.int32) << 8) | (b[:, 2].astype(np.int32) << 16))
        i32 = np.where(i32 >= 1 << 23, i32 - (1 << 24), i32)
        arr = i32.astype(np.float64) / float(1 << 23)
    elif tag == 1 and bits == 32:
        arr = np.frombuffer(data, dtype="<i4").astype(np.float64) / float(1 << 31)
    else:
        raise ValueError(f"unsupported WAV format tag={tag} bits={bits}")
    return arr.reshape(-1, channels), rate, bits, tag
