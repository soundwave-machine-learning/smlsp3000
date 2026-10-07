"""SP → R10 → MPC cascade reference engine (Track A, provisional; OWN-DEC-009..012).

Composition on the proxy grid (docs/ARCHITECTURE.md: R10 is a proxy-domain gain; the proxy carries SP images):

    host x ─R1→ proxy ─[SP core R2–R9]─ ×g10 (R10) ─[MPC core R11–R15]─ R16→ host y

Chain modes (ProductParameters candidate ``chain_mode``; product default CASCADE, OWN-DEC-012):

    CASCADE               R1 → SP core → R10 → MPC core → R16
    SP_ONLY               R1 → SP core → delay(MPC core) → R16            (R10 not applied: no interstage without a second machine)
    MPC_ONLY              R1 → delay(SP core) → MPC core → R16            (R10 not applied)
    BOTH_MACHINE_BYPASSED R1 → delay(SP core + MPC core) → R16            (resampling-only diagnostic path)

Every mode has the same integer host latency (constant-delay compensation, explicitly documented as a
software alignment choice, not machine behaviour). Bypassing a machine removes all of its blocks including
its sampling grid and quantizers. SP_ONLY/MPC_ONLY/BOTH_MACHINE_BYPASSED are research/diagnostic
configurations; only CASCADE is the product default.

Reverse order (MPC core → R10 → SP core) exists only behind the research switch ``reverse_order_research``
for INFORMATIONAL SIMULATION (CHAIN-DEC-013 software derivative); it is never a product mode.

R10: interstage_level_db, owner-set provisional software default 0.0 dB = SP normalized full scale maps to
MPC normalized full scale. NON-HISTORICAL, UNVALIDATED AGAINST HARDWARE; volts UNSET. The converter clamp
of the MPC stage is the only overload mechanism; nothing else is added.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np

from ..hashing import sha256_bytes
from .assets import ASSET_DIR, canonical_bytes, load_asset, load_json, load_research_config
from .errors import InvalidConfiguration
from .mpc3000 import MPCProductParameters, MPCReferenceEngine
from .sp1200 import SPProductParameters, SPReferenceEngine
from .streaming import Decimator, PolyphaseUpsampler

CASCADE_IMPLEMENTATION_VERSION = "cascade-reference-impl-1.0.0"
CHAIN_MODES = ("CASCADE", "SP_ONLY", "MPC_ONLY", "BOTH_MACHINE_BYPASSED")
PRODUCT_DEFAULT_CHAIN_MODE = "CASCADE"
RESEARCH_CHAIN_MODES = ("SP_ONLY", "MPC_ONLY", "BOTH_MACHINE_BYPASSED")


@dataclass(frozen=True)
class CascadeProductParameters:
    """Product-level parameters of the cascade (docs/PARAMETERS.md candidates). No defaults."""
    sp: SPProductParameters
    mpc: MPCProductParameters
    interstage_level_db: float
    chain_mode: str


@dataclass
class CascadePreparedInfo:
    host_rate_hz: int
    proxy_rate_hz: int
    chain_mode: str
    interstage_level_db: float
    interstage_gain_linear: float
    interstage_status: str
    latency_host_samples: int
    latency_breakdown_proxy_samples: dict
    sp_info: dict
    mpc_info: dict
    product_path: str
    stereo: str
    fidelity: str

    def to_dict(self) -> dict:
        return asdict(self)


class _Delay:
    """Exact integer-sample delay line (zero initial state)."""

    def __init__(self, n: int):
        self.n = int(n)
        self.reset()

    def reset(self):
        self.buf = np.zeros(self.n, dtype=np.float64)

    def process(self, v: np.ndarray) -> np.ndarray:
        if self.n == 0:
            return v
        full = np.concatenate([self.buf, v])
        self.buf = full[-self.n:].copy()
        return full[:v.size]


def load_product_config(path=None) -> tuple[dict, str]:
    cfg = load_json(path or ASSET_DIR / "product_config_track_a_v1.json")
    return cfg, sha256_bytes(canonical_bytes(cfg))


def load_cascade_research_config(path=None) -> tuple[dict, str]:
    cfg = load_json(path or ASSET_DIR / "research_config_cascade_track_a_v1.json")
    return cfg, sha256_bytes(canonical_bytes(cfg))


class CascadeReferenceEngine:
    def __init__(self):
        self.prepared = False

    def prepare(self, host_rate_hz: int, channels: int, product: CascadeProductParameters,
                sp_asset=None, sp_research=None, mpc_asset=None, mpc_research=None,
                product_config=None, cascade_research=None) -> CascadePreparedInfo:
        sp_asset, sp_sha = sp_asset or load_asset(machine="SP-1200")
        sp_research, sp_rsha = sp_research or load_research_config(machine="SP-1200")
        mpc_asset, mpc_sha = mpc_asset or load_asset(machine="MPC3000")
        mpc_research, mpc_rsha = mpc_research or load_research_config(machine="MPC3000")
        pcfg, self.product_sha = product_config or load_product_config()
        ccfg, self.cascade_sha = cascade_research or load_cascade_research_config()
        if product.chain_mode not in CHAIN_MODES:
            raise InvalidConfiguration("CHAIN_MODE", f"{product.chain_mode!r} not in {CHAIN_MODES}")
        if product.sp.sp_output_path != pcfg["routes"]["sp_output_path"] or product.mpc.mpc_output_route != pcfg["routes"]["mpc_output_route"]:
            raise InvalidConfiguration("ROUTE_NOT_PRODUCT", "route differs from the owner-approved product configuration")
        ist = pcfg["interstage"]
        if not (ist["research_range_db"][0] <= product.interstage_level_db <= ist["research_range_db"][1]):
            raise InvalidConfiguration("INTERSTAGE_RANGE", f"interstage_level_db outside the approved research range {ist['research_range_db']}")
        self.sp = SPReferenceEngine(); self.sp_info = self.sp.prepare(host_rate_hz, channels, sp_asset, sp_sha, product.sp, sp_research, sp_rsha)
        self.mpc = MPCReferenceEngine(); self.mpc_info = self.mpc.prepare(host_rate_hz, channels, mpc_asset, mpc_sha, product.mpc, mpc_research, mpc_rsha)
        if self.sp.L != self.mpc.L or self.sp.proxy_rate != self.mpc.proxy_rate:
            raise InvalidConfiguration("PROXY_MISMATCH", "SP and MPC research configurations must share the proxy oversampling for composition")
        if not np.array_equal(self.sp.h_lp, self.mpc.h_lp):
            raise InvalidConfiguration("KERNEL_MISMATCH", "SP and MPC R1/R16 kernels must be identical for composition")
        self.L = self.sp.L; self.host_rate = int(host_rate_hz); self.proxy_rate = self.sp.proxy_rate
        self.channels = int(channels); self.mode = product.chain_mode
        self.reverse = bool(ccfg["switches"]["reverse_order_research"])
        if self.reverse and self.mode != "CASCADE":
            raise InvalidConfiguration("REVERSE_MODE", "reverse_order_research applies to CASCADE only")
        self.g10 = 10.0 ** (product.interstage_level_db / 20.0)
        self.interstage_db = float(product.interstage_level_db)
        d_sp, d_mpc = self.sp.core_delay_proxy, self.mpc.core_delay_proxy
        lobes_proxy = (self.sp.h_lp.size - 1) // 2
        self.delay_proxy = lobes_proxy + d_sp + d_mpc + lobes_proxy
        assert self.delay_proxy % self.L == 0
        self.latency_host = self.delay_proxy // self.L
        self.up = [PolyphaseUpsampler(self.L, self.sp.h_lp) for _ in range(self.channels)]
        self.down = [Decimator(self.L, self.sp.h_lp) for _ in range(self.channels)]
        self.dly_sp = [_Delay(d_sp) for _ in range(self.channels)]
        self.dly_mpc = [_Delay(d_mpc) for _ in range(self.channels)]
        self.peak_in = [0.0] * self.channels
        self.prepared = True
        self.info = CascadePreparedInfo(
            host_rate_hz=self.host_rate, proxy_rate_hz=self.proxy_rate, chain_mode=self.mode,
            interstage_level_db=self.interstage_db, interstage_gain_linear=self.g10,
            interstage_status="OWNER-SET PROVISIONAL SOFTWARE DEFAULT 0.0 dB (OWN-DEC-009); NON-HISTORICAL; UNVALIDATED AGAINST HARDWARE; volts UNSET" if self.interstage_db == 0.0 else "research value; NON-HISTORICAL; UNVALIDATED AGAINST HARDWARE; volts UNSET",
            latency_host_samples=self.latency_host,
            latency_breakdown_proxy_samples={"R1": lobes_proxy, "SP_core_or_aligned_delay": d_sp, "MPC_core_or_aligned_delay": d_mpc, "R16": lobes_proxy},
            sp_info=self.sp_info.to_dict(), mpc_info=self.mpc_info.to_dict(),
            product_path="B — full sample path (OWN-DEC-010, software product decision; G-07H BLOCKED)",
            stereo="linked dual mono on the SP stage (PRODUCT ABSTRACTION, CHAIN-DEC-005) → true stereo on the MPC stage",
            fidelity="NORMALIZED RESEARCH SKELETON CASCADE — NOT A MODEL OF MEASURED HARDWARE; UNVALIDATED AGAINST HARDWARE",
        )
        return self.info

    def _require(self):
        if not self.prepared:
            raise InvalidConfiguration("NOT_PREPARED", "call prepare() first")

    def reset(self):
        self._require()
        self.sp.reset(); self.mpc.reset()
        for c in range(self.channels):
            self.up[c].reset(); self.down[c].reset(); self.dly_sp[c].reset(); self.dly_mpc[c].reset()
        self.peak_in = [0.0] * self.channels

    def latency(self) -> int:
        self._require()
        return self.latency_host

    def process(self, x: np.ndarray) -> np.ndarray:
        self._require()
        x = np.asarray(x, dtype=np.float64)
        if x.ndim == 1:
            x = x[:, None]
        if x.shape[1] != self.channels:
            raise InvalidConfiguration("CHANNELS", "channel count differs from prepare()")
        y = np.empty_like(x)
        for c in range(self.channels):
            self.peak_in[c] = max(self.peak_in[c], float(np.max(np.abs(x[:, c]))) if x.shape[0] else 0.0)
            v = self.up[c].process(x[:, c])                                   # R1
            if self.mode == "CASCADE":
                if not self.reverse:
                    h = self.sp.core_channel(self.sp.ch[c], v)                 # R2–R9
                    h = h * self.g10                                           # R10
                    h = self.mpc.core_channel(self.mpc.ch[c], h)               # R11–R15
                else:                                                          # INFORMATIONAL research only
                    h = self.mpc.core_channel(self.mpc.ch[c], v)
                    h = h * self.g10
                    h = self.sp.core_channel(self.sp.ch[c], h)
            elif self.mode == "SP_ONLY":
                h = self.dly_mpc[c].process(self.sp.core_channel(self.sp.ch[c], v))
            elif self.mode == "MPC_ONLY":
                h = self.mpc.core_channel(self.mpc.ch[c], self.dly_sp[c].process(v))
            else:  # BOTH_MACHINE_BYPASSED
                h = self.dly_mpc[c].process(self.dly_sp[c].process(v))
            y[:, c] = self.down[c].process(h)                                 # R16
        return y

    def drain(self) -> np.ndarray:
        self._require()
        return self.process(np.zeros((self.latency_host, self.channels)))

    def meters(self) -> dict:
        self._require()
        return {"host_input_peak": list(self.peak_in), "sp": self.sp.meters(), "mpc": self.mpc.meters()}
