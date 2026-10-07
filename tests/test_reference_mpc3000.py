"""Sprint 4 software-track unit tests for the MPC reference (Track A). Software behaviour only; no hardware claim."""
import unittest

import numpy as np

from smlsp3000.reference.assets import load_asset, load_research_config
from smlsp3000.reference.errors import InvalidConfiguration
from smlsp3000.reference.mpc3000 import (R12_STRATEGIES, R14_STRATEGIES, R15_ROUTES, R15_STRATEGIES, REDUCTION_RULES,
                                         MPCProductParameters, MPCReferenceEngine)
from smlsp3000.reference.render import render_offline, with_switches
from smlsp3000.schemas import validate_machine_asset
from smlsp3000.validation.measure import fit_components

PRODUCT = MPCProductParameters("LO", 0.0, "MAIN_LR", "NORMALIZED_RESEARCH")


class MPCAssetTests(unittest.TestCase):
    def test_asset_validates_and_owner_defaults(self):
        asset, sha = load_asset(machine="MPC3000")
        self.assertEqual(validate_machine_asset(asset), [])
        cfg, _ = load_research_config(machine="MPC3000")
        v = asset["values"]
        self.assertEqual(v["r12_strategy"]["value"], "TRANSPARENT")
        self.assertEqual(v["r15_strategy"]["value"], "TRANSPARENT")
        self.assertEqual(v["reduction_rule_default"]["value"], "ROUND_NEAREST")
        self.assertEqual(cfg["switches"]["reduction_rule"], "ROUND_NEAREST")
        self.assertEqual(v["de_emphasis"]["value"], "OFF_UNASSERTED")
        self.assertEqual(v["volts_per_normalized_unit"]["value"], "UNSET")
        self.assertEqual(v["output_routes"]["value"]["MAIN_LR"]["status"], "POPULATED")
        self.assertEqual(v["output_routes"]["value"]["INDIVIDUAL_PAIR"]["status"], "NOT POPULATED")
        self.assertEqual(v["output_routes"]["value"]["HEADPHONES"]["status"], "EXCLUDED")
        for name, rec in v.items():
            self.assertEqual(rec["hardware_validation"], "UNVALIDATED AGAINST HARDWARE", name)

    def test_registries_only_contain_populated_strategies(self):
        self.assertEqual(set(R12_STRATEGIES), {"TRANSPARENT"}); self.assertEqual(set(R15_STRATEGIES), {"TRANSPARENT"})
        self.assertEqual(set(R14_STRATEGIES), {"IDENTITY_UNITY"}); self.assertEqual(set(R15_ROUTES), {"MAIN_LR"})
        self.assertEqual(set(REDUCTION_RULES), {"ROUND_NEAREST", "TRUNCATION"})


class ReductionRuleTests(unittest.TestCase):
    def test_definitions_boundaries_zero_negatives_extremes(self):
        c = np.array([-131072, -131071, -4, -3, -2, -1, 0, 1, 2, 3, 4, 131070, 131071], dtype=np.float64)
        rn = REDUCTION_RULES["ROUND_NEAREST"](c); tr = REDUCTION_RULES["TRUNCATION"](c)
        self.assertTrue(np.array_equal(rn, np.floor(c / 4 + 0.5)))
        self.assertTrue(np.array_equal(tr, np.floor(c / 4)))
        self.assertEqual(rn[6], 0.0); self.assertEqual(tr[6], 0.0)
        self.assertEqual(rn[8], 1.0)      # c18 = 2 → tie → 1 (toward +inf)
        self.assertEqual(tr[8], 0.0)
        self.assertEqual(rn[5], 0.0)      # c18 = -1 → -0.25+0.5 → floor(0.25)=0
        self.assertEqual(tr[5], -1.0)     # truncation toward -inf
        self.assertEqual(rn[-1], 32768.0)  # overflows → clamped by the engine
        self.assertEqual(tr[-1], 32767.0)

    def test_engine_clamps_overflow_and_counts(self):
        asset, asha = load_asset(machine="MPC3000"); cfg, rsha = load_research_config(machine="MPC3000")
        e = MPCReferenceEngine(); e.prepare(48000, 1, asset, asha, PRODUCT, cfg, rsha)
        c16, n = e.reduce_codes(np.array([131071, 131070, -131072, 0], dtype=np.float64))
        self.assertTrue(np.array_equal(c16, [32767, 32767, -32768, 0])); self.assertEqual(n, 2)
        self.assertTrue(np.array_equal(e.expand_codes(c16), c16 * 4))


class MPCEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.asset, cls.asha = load_asset(machine="MPC3000"); cls.cfg, cls.rsha = load_research_config(machine="MPC3000")

    def _prep(self, product=PRODUCT, cfg=None, fs=48000, ch=1):
        return MPCReferenceEngine().prepare(fs, ch, self.asset, self.asha, product, cfg or self.cfg, self.rsha)

    def test_rejections(self):
        for route, code in (("INDIVIDUAL_PAIR", "ROUTE_NOT_POPULATED"), ("HEADPHONES", "ROUTE_EXCLUDED")):
            with self.assertRaises(InvalidConfiguration) as cm:
                self._prep(MPCProductParameters("LO", 0.0, route, "NORMALIZED_RESEARCH"))
            self.assertEqual(cm.exception.code, code)
        with self.assertRaises(InvalidConfiguration) as cm:
            self._prep(MPCProductParameters("LO", 0.0, "MAIN_LR", "PHYSICAL"))
        self.assertEqual(cm.exception.code, "ASSET_VALUE_UNSET")
        for key, val in (("r12_strategy", "ESTIMATE_FIR"), ("r15_strategy", "MEASURED_RESPONSE"), ("reduction_rule", "DITHER"), ("de_emphasis", "ON")):
            with self.assertRaises(InvalidConfiguration):
                self._prep(cfg=with_switches(self.cfg, **{key: val}))
        with self.assertRaises(InvalidConfiguration):
            self._prep(MPCProductParameters("MAX", 0.0, "MAIN_LR", "NORMALIZED_RESEARCH"))
        with self.assertRaises(InvalidConfiguration):
            self._prep(MPCProductParameters("LO", 1.0, "MAIN_LR", "NORMALIZED_RESEARCH"))

    def test_info_and_latency(self):
        info = self._prep()
        self.assertEqual(info.mpc_over_host_ratio, "147/160")
        self.assertIn("UNVALIDATED AGAINST HARDWARE", info.fidelity)
        self.assertIn("NOT a measured", info.latency_note)
        self.assertEqual(sum(info.latency_breakdown_proxy_samples.values()), info.latency_host_samples * info.proxy_oversampling)

    def test_determinism_partition_and_rules_differ(self):
        x = 0.5 * np.sin(2 * np.pi * 1234.5 * np.arange(12000) / 48000)
        y1, _, _, _ = render_offline(x, 48000, PRODUCT, self.cfg)
        y2, _, _, _ = render_offline(x, 48000, PRODUCT, self.cfg, block_sizes=[1] * 30 + [5, 64, 777, 4000])
        self.assertTrue(np.array_equal(y1, y2))
        y3, _, _, _ = render_offline(x, 48000, PRODUCT, with_switches(self.cfg, reduction_rule="TRUNCATION"))
        self.assertFalse(np.array_equal(y1, y3))

    def test_transparent_in_band_tone_within_kernel_bound(self):
        fs = 96000; f = 15000.0
        x = 0.5 * np.sin(2 * np.pi * f * np.arange(int(0.2 * fs)) / fs)
        y, info, _, eng = render_offline(x, fs, PRODUCT, with_switches(self.cfg, converter_quantization_bypass_diagnostic=True))
        amps, _ = fit_components(y[3000:-3000, 0], fs, [f])
        from smlsp3000.reference.kernels import frequency_response, interpolation_kernel_response
        fp = fs * info.proxy_oversampling
        exp = 0.5 * abs(frequency_response(eng.h_lp, f / fp)[0]) ** 2 * abs(frequency_response(eng.h_r12, f / fp)[0]) * float(interpolation_kernel_response(eng.hw_r, eng.interp_beta, f / 44100)[0])
        self.assertLessEqual(abs(amps[f] - exp), 0.5 * info.kernel_properties["line_amplitude_bound_relative"])

    def test_true_stereo_identity_and_isolation(self):
        n = 8000; a = 0.4 * np.sin(2 * np.pi * 500.0 * np.arange(n) / 48000)
        y, _, _, _ = render_offline(np.stack([a, a], 1), 48000, PRODUCT, self.cfg)
        self.assertTrue(np.array_equal(y[:, 0], y[:, 1]))
        y2, _, _, _ = render_offline(np.stack([a, np.zeros(n)], 1), 48000, PRODUCT, self.cfg)
        self.assertTrue(np.all(y2[:, 1] == 0.0)); self.assertTrue(np.array_equal(y2[:, 0], y[:, 0]))

    def test_clamp_meters(self):
        x = 1.5 * np.sin(2 * np.pi * 1000.0 * np.arange(4800) / 48000)
        y, _, rec, e = render_offline(x, 48000, PRODUCT, with_switches(self.cfg, diagnostic_taps=True))
        c18 = e.tap_codes(0, "c18")
        self.assertEqual((int(c18.max()), int(c18.min())), (131071, -131072))
        self.assertGreater(rec["meters"][0]["converter_clip_count_18bit"], 0)


if __name__ == "__main__":
    unittest.main()
