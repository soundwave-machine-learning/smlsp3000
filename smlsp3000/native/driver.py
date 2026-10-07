"""Drive the native offline tool (native/build/smlsp3000_native) from the analysis stack.

Exchange format: raw float64 interleaved files (.f64) in a scratch directory; configuration through command-line
flags; results as JSON on stdout. Nothing here runs on an audio thread; the production core has no file access.
"""
from __future__ import annotations

import json
import os
import platform
import subprocess
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BINARY = ROOT / "native" / "build" / "smlsp3000_native"
DEFAULT_SELFTEST = ROOT / "native" / "build" / "smlsp3000_selftest"
PARAM_NAMES = ("sp_input_level_db", "sp_input_gain_db", "interstage_level_db", "mpc_input_gain", "output_trim_db", "plugin_bypass")


def binary_path() -> Path:
    p = Path(os.environ.get("SMLSP3000_NATIVE", str(DEFAULT_BINARY)))
    return p


def available() -> bool:
    return binary_path().exists()


def _args_from(config: dict) -> list[str]:
    """Map a configuration dict (keys = tool flag names with underscores) to tool flags."""
    out = []
    for k, v in config.items():
        if v is None:
            continue
        if isinstance(v, bool):
            v = 1 if v else 0
        out += ["--" + k.replace("_", "-"), str(v)]
    return out


def run_tool(args: list[str], binary: Path | None = None) -> dict:
    b = binary or binary_path()
    r = subprocess.run([str(b)] + args, capture_output=True, text=True)
    try:
        j = json.loads(r.stdout.strip().splitlines()[-1]) if r.stdout.strip() else {}
    except json.JSONDecodeError as e:
        raise RuntimeError(f"native tool returned non-JSON: {r.stdout[:400]} / {r.stderr[:400]}") from e
    j["_exit_code"] = r.returncode
    j["_stderr"] = r.stderr
    return j


def info(rate: int, channels: int = 2, max_block: int = 8192, config: dict | None = None) -> dict:
    return run_tool(["info", "--rate", str(rate), "--channels", str(channels), "--max-block", str(max_block)] + _args_from(config or {}))


def render(x: np.ndarray, rate: int, config: dict | None = None, blocks: list[int] | None = None, block: int | None = None, block_seed: int | None = None,
           block_max: int = 8192, max_block: int = 8192, drain: bool = True, events: list[tuple[int, str, float]] | None = None, taps: bool = False,
           workdir: Path | None = None, keep: bool = False) -> tuple[np.ndarray, dict]:
    """Render x (frames, channels) float64 through the native core. Returns (y, result json). y includes the drained tail when drain."""
    x = np.ascontiguousarray(np.asarray(x, dtype=np.float64))
    if x.ndim == 1:
        x = x[:, None]
    wd = Path(workdir) if workdir else Path(tempfile.mkdtemp(prefix="smlsp3000_native_"))
    wd.mkdir(parents=True, exist_ok=True)
    fin, fout = wd / "in.f64", wd / "out.f64"
    x.tofile(fin)
    args = ["render", "--rate", str(rate), "--channels", str(x.shape[1]), "--in", str(fin), "--out", str(fout), "--max-block", str(max_block), "--drain", "1" if drain else "0"]
    if blocks is not None:
        args += ["--blocks", ",".join(str(int(b)) for b in blocks)]
    elif block_seed is not None:
        args += ["--block-seed", str(block_seed), "--block-max", str(block_max)]
    else:
        args += ["--block", str(block or max_block)]
    if events:
        fe = wd / "events.txt"
        fe.write_text("".join(f"{int(o)} {n} {float(v)!r}\n" for o, n, v in events), encoding="utf-8")
        args += ["--events", str(fe)]
    if taps:
        args += ["--taps", str(wd / "taps")]
    args += _args_from(config or {})
    j = run_tool(args)
    if not j.get("ok"):
        return np.zeros((0, x.shape[1])), j
    y = np.fromfile(fout, dtype=np.float64).reshape(-1, x.shape[1])
    if taps:
        j["tap_arrays"] = {(t["channel"], t["kind"]): np.fromfile(t["path"], dtype=np.float64) for t in j["taps"]}
    if not keep and workdir is None:
        for p in wd.iterdir():
            p.unlink()
        wd.rmdir()
    return y, j


def dump_kernels(rate: int, config: dict | None = None, workdir: Path | None = None) -> dict:
    wd = Path(workdir) if workdir else Path(tempfile.mkdtemp(prefix="smlsp3000_kernels_"))
    wd.mkdir(parents=True, exist_ok=True)
    j = run_tool(["dump-kernels", "--rate", str(rate), "--out-prefix", str(wd / "k")] + _args_from(config or {}))
    if j.get("ok"):
        j["tables"] = {name: np.fromfile(wd / f"k_{name}.f64", dtype=np.float64) for name in ("h_lp", "h_r12", "sp_taps", "mpc_staps", "mpc_rtaps", "step")}
    return j


def bench(rate: int, block: int, seconds: float, trials: int, warmup: float, config: dict | None = None, raw_prefix: Path | None = None) -> dict:
    args = ["bench", "--rate", str(rate), "--block", str(block), "--channels", "2", "--seconds", str(seconds), "--trials", str(trials), "--warmup", str(warmup)]
    if raw_prefix:
        args += ["--raw", str(raw_prefix)]
    return run_tool(args + _args_from(config or {}))


def state_load(text: str, workdir: Path | None = None) -> dict:
    wd = Path(workdir) if workdir else Path(tempfile.mkdtemp(prefix="smlsp3000_state_"))
    wd.mkdir(parents=True, exist_ok=True)
    f = wd / "state.txt"
    f.write_text(text, encoding="utf-8")
    return run_tool(["state-load", "--state", str(f)])


def build_record(build_dir: Path | None = None) -> dict:
    """Compiler/options record of the native build (from CMakeCache / compile commands)."""
    bd = Path(build_dir) if build_dir else DEFAULT_BINARY.parent
    rec = {"build_dir": str(bd), "binary": str(binary_path()), "platform": platform.platform(), "machine": platform.machine()}
    cache = bd / "CMakeCache.txt"
    if cache.exists():
        for line in cache.read_text(encoding="utf-8", errors="replace").splitlines():
            for key in ("CMAKE_CXX_COMPILER:", "CMAKE_CXX_FLAGS:", "CMAKE_CXX_FLAGS_RELEASE:", "CMAKE_BUILD_TYPE:", "SMLSP3000_NATIVE_ARCH:", "CMAKE_GENERATOR:"):
                if line.startswith(key):
                    rec[key.rstrip(":")] = line.split("=", 1)[1]
    try:
        rec["compiler_version"] = subprocess.run([rec.get("CMAKE_CXX_COMPILER", "c++"), "--version"], capture_output=True, text=True).stdout.splitlines()[0]
    except Exception as e:  # pragma: no cover
        rec["compiler_version"] = f"unavailable ({e})"
    rec["target_compile_options"] = "-Wall -Wextra -O2 -ffp-contract=off -fno-fast-math -fexcess-precision=standard (GCC/Clang; see native/CMakeLists.txt); MSVC: /W4 /fp:precise /O2 (not compiled here)"
    rec["fma_contraction_policy"] = "OFF: -ffp-contract=off (GCC default for GNU C++ is 'fast'); products and sums are rounded separately so FIR accumulation reproduces the numpy pairwise order"
    rec["fast_math"] = "OFF (-fno-fast-math)"
    rec["denormal_policy"] = "none (no FTZ/DAZ; bit-identity with the reference; all filters are feed-forward so denormals cannot self-sustain)"
    return rec
