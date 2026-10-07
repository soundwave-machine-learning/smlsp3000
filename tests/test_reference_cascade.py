"""Sprint 5 software-track unit tests for the SP→MPC cascade (Track A). Software behaviour only."""
import unittest

import numpy as np

from smlsp3000.reference.cascade import CHAIN_MODES, PRODUCT_DEFAULT_CHAIN_MODE, CascadeProductParameters, CascadeReferenceEngine, load_product_config
from smlsp3000.reference.errors import InvalidConfiguration
from smlsp3000.reference.mpc3000 import MPCProductParameters
from smlsp3000.reference.render import render_offline
from smlsp3000.reference.sp1200 import SPProductParameters

SP = SPProductParameters(0.0, 0, "NONE_CH7_8", "NORMALIZED_RESEARCH")
MPC = MPCProductParameters("LO", 0.0, "MAIN_LR", "NORMALIZED_RESEARCH")
FS = 48000


def run(x, mode, g=0.0, chunks=None):
    x = np.asarray(x); x = x[:, None] if x.ndim == 1 else x
    e = CascadeReferenceEngine(); info = e.prepare(FS, x.shape[1], CascadeProductParameters(SP, MPC, g, mode))
    outs = []
    if chunks is None:
        outs.append(e.process(x))
    else:
        i = 0
        for n in chunks:
            outs.append(e.process(x[i:i + n])); i += n
        outs.append(e.process(x[i:]))
    outs.append(e.drain()); y = np.concatenate(outs)
    return y[info.latency_host_samples:info.latency_host_samples + x.shape[0]], info, e


class CascadeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.x = 0.5 * np.sin(2 * np.pi * 1234.5 * np.arange(12000) / FS) + 0.2 * np.sin(2 * np.pi * 7777.0 * np.arange(12000) / FS)

    def test_product_config_owner_decisions(self):
        pc, _ = load_product_config()
        self.assertEqual(pc["product_path"]["selected"], "B")
        self.assertEqual(pc["interstage"]["default_db"], 0.0)
        self.assertEqual(pc["chain_modes"]["product_default"], "CASCADE")
        self.assertEqual((pc["routes"]["sp_output_path"], pc["routes"]["mpc_output_route"]), ("NONE_CH7_8", "MAIN_LR"))
        self.assertIn("drive macro", pc["controls"]["excluded"]); self.assertIn("wet/dry", pc["controls"]["excluded"])
        self.assertEqual(PRODUCT_DEFAULT_CHAIN_MODE, "CASCADE"); self.assertEqual(set(CHAIN_MODES), {"CASCADE", "SP_ONLY", "MPC_ONLY", "BOTH_MACHINE_BYPASSED"})

    def test_sp_only_bit_identical_to_sp_engine_and_latency_equal_all_modes(self):
        ysp, info_sp, _ = run(self.x, "SP_ONLY")
        ref, _, _, _ = render_offline(self.x, FS, SP)
        self.assertTrue(np.array_equal(ysp[:, 0], ref[:, 0]))
        lats = {run(self.x[:200], m)[1].latency_host_samples for m in CHAIN_MODES}
        self.assertEqual(len(lats), 1)

    def test_mpc_only_equals_mpc_engine_on_delayed_input(self):
        ym, info, e = run(self.x, "MPC_ONLY")
        d = e.sp.core_delay_proxy // e.L
        xd = np.concatenate([np.zeros(d), self.x])          # full length + d
        ref, _, _, _ = render_offline(xd, FS, MPC)
        # cascade alignment removes the SP-core delay, so compare shifted by d (same 44.1 kHz sampling phase)
        self.assertTrue(np.array_equal(ym[:, 0], ref[d:d + self.x.size, 0]))

    def test_cascade_deterministic_partition_invariant_and_distinct(self):
        y1, _, _ = run(self.x, "CASCADE"); y2, _, _ = run(self.x, "CASCADE", chunks=[1] * 20 + [5, 64, 777, 4000])
        self.assertTrue(np.array_equal(y1, y2))
        ysp, _, _ = run(self.x, "SP_ONLY"); ym, _, _ = run(self.x, "MPC_ONLY")
        self.assertFalse(np.array_equal(y1, ysp)); self.assertFalse(np.array_equal(y1, ym))

    def test_interstage_gain_and_clamp(self):
        t = 0.5 * np.sin(2 * np.pi * 1000.0 * np.arange(6000) / FS)
        _, _, e20 = run(t, "CASCADE", g=20.0)
        self.assertGreater(e20.meters()["mpc"][0]["converter_clip_count_18bit"], 0)
        self.assertEqual(e20.meters()["sp"][0]["converter_clip_count"], 0)
        _, _, e0 = run(t, "CASCADE", g=0.0)
        self.assertEqual(e0.meters()["mpc"][0]["converter_clip_count_18bit"], 0)
        with self.assertRaises(InvalidConfiguration):
            run(t[:100], "CASCADE", g=30.0)
        with self.assertRaises(InvalidConfiguration):
            run(t[:100], "NOT_A_MODE")

    def test_non_product_route_rejected(self):
        with self.assertRaises(InvalidConfiguration) as cm:
            CascadeReferenceEngine().prepare(FS, 1, CascadeProductParameters(SPProductParameters(0.0, 0, "FIXED_CH3_4", "NORMALIZED_RESEARCH"), MPC, 0.0, "CASCADE"))
        self.assertEqual(cm.exception.code, "ROUTE_NOT_PRODUCT")

    def test_stereo_linkage(self):
        a = 0.4 * np.sin(2 * np.pi * 500.0 * np.arange(6000) / FS)
        y, _, _ = run(np.stack([a, a], 1), "CASCADE")
        self.assertTrue(np.array_equal(y[:, 0], y[:, 1]))
        y2, _, _ = run(np.stack([a, np.zeros(6000)], 1), "CASCADE")
        self.assertTrue(np.all(y2[:, 1] == 0.0)); self.assertTrue(np.array_equal(y2[:, 0], y[:, 0]))


if __name__ == "__main__":
    unittest.main()
