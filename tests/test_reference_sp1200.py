"""Sprint 3 software-track unit tests for the SP reference (Track A). Software behaviour only; no hardware claim."""
import unittest
from fractions import Fraction

import numpy as np

from smlsp3000.reference.assets import load_asset, load_research_config
from smlsp3000.reference.errors import InvalidConfiguration
from smlsp3000.reference.kernels import DC_GAIN_BOUND, BandlimitedStepTable, kaiser_sinc_lowpass
from smlsp3000.reference.render import render_offline, with_switches
from smlsp3000.reference.scheduler import RationalClock
from smlsp3000.reference.sp1200 import QUANTIZER_RULES, R3_STRATEGIES, R8_ROUTES, SPProductParameters, SPReferenceEngine
from smlsp3000.reference.streaming import Decimator, PolyphaseUpsampler, StreamingFIR
from smlsp3000.schemas import validate_machine_asset
from smlsp3000.validation.measure import fit_components, zoh_magnitude

PRODUCT = SPProductParameters(0.0, 0, "NONE_CH7_8", "NORMALIZED_RESEARCH")


class AssetTests(unittest.TestCase):
    def test_provisional_asset_validates_and_is_tagged(self):
        asset, sha = load_asset()
        self.assertEqual(validate_machine_asset(asset), [])
        for name, rec in asset["values"].items():
            self.assertEqual(rec["hardware_validation"], "UNVALIDATED AGAINST HARDWARE", name)
            self.assertTrue(rec["source_ids"] is not None and rec["decision_id"], name)
        self.assertEqual(len(sha), 64)

    def test_magic_value_rejected(self):
        asset, _ = load_asset()
        bad = {**asset, "values": {**asset["values"], "hold_fraction": {"value": 0.9, "unit": "x"}}}
        self.assertTrue(any("hold_fraction" in p for p in validate_machine_asset(bad)))

    def test_owner_defaults_recorded(self):
        asset, _ = load_asset()
        cfg, _ = load_research_config()
        self.assertEqual(asset["values"]["r3_strategy"]["value"], "INACTIVE")
        self.assertEqual(asset["values"]["quantizer_rule_default"]["value"], "ROUND_NEAREST")
        self.assertEqual(cfg["switches"]["quantizer_rule"], "ROUND_NEAREST")
        self.assertEqual(asset["values"]["output_routes"]["value"]["NONE_CH7_8"]["status"], "POPULATED")
        self.assertTrue(all(v["status"] == "NOT POPULATED" for k, v in asset["values"]["output_routes"]["value"].items() if k != "NONE_CH7_8"))
        self.assertEqual(asset["values"]["volts_per_normalized_unit"]["value"], "UNSET")


class KernelTests(unittest.TestCase):
    def test_lowpass_unity_dc_and_symmetry(self):
        h = kaiser_sinc_lowpass(2 * 8 * 4 + 1, 0.5 / 4, 9.0)
        self.assertLessEqual(abs(float(np.sum(h)) - 1.0), DC_GAIN_BOUND)
        self.assertTrue(np.array_equal(h, h[::-1]))

    def test_streaming_fir_partition_invariant(self):
        h = kaiser_sinc_lowpass(65, 0.2, 8.0)
        x = np.random.default_rng(3).standard_normal(5000)
        a = StreamingFIR(h).process(x)
        f = StreamingFIR(h)
        b = np.concatenate([f.process(x[:1]), f.process(x[1:8]), f.process(x[8:3000]), f.process(x[3000:])])
        self.assertTrue(np.array_equal(a, b))

    def test_upsample_then_decimate_delay_is_integer(self):
        L, lobes = 4, 8
        h = kaiser_sinc_lowpass(2 * lobes * L + 1, 0.5 / L, 9.0)
        x = np.zeros(400); x[100] = 1.0
        y = Decimator(L, h).process(PolyphaseUpsampler(L, h).process(x))
        self.assertEqual(int(np.argmax(y)), 100 + 2 * lobes)

    def test_bandlimited_step_limits(self):
        S = BandlimitedStepTable(16, 12.0)
        self.assertEqual(float(S(np.array([-20.0]))[0]), 0.0)
        self.assertEqual(float(S(np.array([16.0]))[0]), 1.0)
        self.assertAlmostEqual(float(S(np.array([0.0]))[0]), 0.5, places=6)
        self.assertLess(S.truncation_residual, 1e-6)


class SchedulerTests(unittest.TestCase):
    def test_positions_exact_and_block_independent(self):
        c = RationalClock(20_000_000, 768, 48000 * 8)
        self.assertEqual(c.period_proxy, Fraction(48000 * 8 * 768, 20_000_000))
        self.assertEqual(c.position(1_000_000), 1_000_000 * c.period_proxy)
        ks = c.latest_samples_at(np.arange(0, 2000))
        expect = np.array([c.latest_sample_at(Fraction(n)) for n in range(2000)])
        self.assertTrue(np.array_equal(ks, expect))
        self.assertEqual(c.latest_sample_at(Fraction(-1)), -1)


class QuantizerTests(unittest.TestCase):
    def test_both_rules_exact_definitions(self):
        r = np.array([-0.5, -0.5 + 1e-12, 0.49, 0.5, 1.5, 2046.5, 2047.4])
        self.assertTrue(np.array_equal(QUANTIZER_RULES["ROUND_NEAREST"](r), np.floor(r + 0.5)))
        self.assertTrue(np.array_equal(QUANTIZER_RULES["FLOOR"](r), np.floor(r)))
        self.assertEqual(set(QUANTIZER_RULES), {"ROUND_NEAREST", "FLOOR"})

    def test_rules_produce_different_outputs_and_are_selectable(self):
        cfg, _ = load_research_config()
        x = 0.3 * np.sin(2 * np.pi * 997.0 * np.arange(6000) / 48000)
        y_rn, _, r_rn, _ = render_offline(x, 48000, PRODUCT, with_switches(cfg, quantizer_rule="ROUND_NEAREST"))
        y_fl, _, r_fl, _ = render_offline(x, 48000, PRODUCT, with_switches(cfg, quantizer_rule="FLOOR"))
        self.assertFalse(np.array_equal(y_rn, y_fl))
        self.assertNotEqual(r_rn["output_sha256"], r_fl["output_sha256"])
        with self.assertRaises(InvalidConfiguration):
            render_offline(x, 48000, PRODUCT, with_switches(cfg, quantizer_rule="CEIL"))


class EngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg, _ = load_research_config()
        cls.asset, cls.asha = load_asset()
        _, cls.rsha = load_research_config()

    def _prep(self, product, cfg=None, fs=48000, ch=1):
        e = SPReferenceEngine()
        return e.prepare(fs, ch, self.asset, self.asha, product, cfg or self.cfg, self.rsha)

    def test_rejects_unpopulated_routes_physical_mode_and_reserved_r3(self):
        for route in ("FIXED_CH5_6", "FIXED_CH3_4", "MIX_OUT"):
            with self.assertRaises(InvalidConfiguration) as cm:
                self._prep(SPProductParameters(0.0, 0, route, "NORMALIZED_RESEARCH"))
            self.assertEqual(cm.exception.code, "ROUTE_NOT_POPULATED")
        with self.assertRaises(InvalidConfiguration) as cm:
            self._prep(SPProductParameters(0.0, 0, "NONE_CH7_8", "PHYSICAL"))
        self.assertEqual(cm.exception.code, "ASSET_VALUE_UNSET")
        with self.assertRaises(InvalidConfiguration):
            self._prep(PRODUCT, with_switches(self.cfg, r3_strategy="LITERATURE_DERIVED_LOWPASS"))
        with self.assertRaises(InvalidConfiguration):
            self._prep(PRODUCT, with_switches(self.cfg, hold_fraction=0.9))
        with self.assertRaises(InvalidConfiguration):
            self._prep(SPProductParameters(0.0, 30, "NONE_CH7_8", "NORMALIZED_RESEARCH"))
        with self.assertRaises(InvalidConfiguration):
            self._prep(PRODUCT, fs=22050)

    def test_registries_only_contain_populated_strategies(self):
        self.assertEqual(set(R3_STRATEGIES), {"INACTIVE"})
        self.assertEqual(set(R8_ROUTES), {"NONE_CH7_8"})

    def test_latency_and_info(self):
        info = self._prep(PRODUCT)
        lobes = self.cfg["switches"]["r1_r16_kernel"]["lobes_per_side"]
        hw = self.cfg["switches"]["sampler_half_width_host_samples"] + self.cfg["switches"]["hold_kernel_half_width_host_samples"]
        self.assertEqual(info.latency_host_samples, 2 * lobes + hw)
        self.assertEqual(info.sp_over_host_ratio, "625/1152")
        self.assertIn("UNVALIDATED AGAINST HARDWARE", info.fidelity)

    def test_determinism_and_partition_invariance(self):
        x = 0.5 * np.sin(2 * np.pi * 1234.5 * np.arange(12000) / 48000)
        y1, _, _, _ = render_offline(x, 48000, PRODUCT, self.cfg)
        y2, _, _, _ = render_offline(x, 48000, PRODUCT, self.cfg, block_sizes=[1] * 30 + [5, 64, 777, 4000])
        self.assertTrue(np.array_equal(y1, y2))

    def test_linked_dual_mono_identity_and_isolation(self):
        n = 8000
        a = 0.4 * np.sin(2 * np.pi * 500.0 * np.arange(n) / 48000)
        y, _, _, _ = render_offline(np.stack([a, a], axis=1), 48000, PRODUCT, self.cfg)
        self.assertTrue(np.array_equal(y[:, 0], y[:, 1]))
        y2, _, _, _ = render_offline(np.stack([a, np.zeros(n)], axis=1), 48000, PRODUCT, self.cfg)
        self.assertTrue(np.all(y2[:, 1] == 0.0))
        self.assertTrue(np.array_equal(y2[:, 0], y[:, 0]))

    def test_hold_droop_matches_closed_form_within_kernel_bound(self):
        fs = 96000
        f = 10000.0
        x = 0.5 * np.sin(2 * np.pi * f * np.arange(int(0.2 * fs)) / fs)
        y, info, _, eng = render_offline(x, fs, PRODUCT, with_switches(self.cfg, quantizer_bypass_diagnostic=True))
        seg = y[3000:-3000, 0]
        fsp = 20_000_000 / 768
        amps, _ = fit_components(seg, fs, [f, fsp - f])
        from smlsp3000.reference.kernels import frequency_response
        fp = fs * info.proxy_oversampling
        exp_f = 0.5 * zoh_magnitude(f, fsp) * abs(frequency_response(eng.h_lp, f / fp)[0]) ** 2
        exp_img = 0.5 * zoh_magnitude(fsp - f, fsp) * abs(frequency_response(eng.h_lp, f / fp)[0]) * abs(frequency_response(eng.h_lp, (fsp - f) / fp)[0])
        bound = 0.5 * info.kernel_properties["line_amplitude_bound_relative"]
        self.assertLessEqual(abs(amps[f] - exp_f), bound)
        self.assertLessEqual(abs(amps[fsp - f] - exp_img), bound)

    def test_clamp_and_meters(self):
        x = 1.5 * np.sin(2 * np.pi * 1000.0 * np.arange(4800) / 48000)
        y, _, rec, eng = render_offline(x, 48000, PRODUCT, with_switches(self.cfg, diagnostic_taps=True))
        c = eng.tap_codes(0)
        self.assertEqual((int(c.max()), int(c.min())), (2047, -2048))
        self.assertGreater(rec["meters"][0]["converter_clip_count"], 0)


if __name__ == "__main__":
    unittest.main()
