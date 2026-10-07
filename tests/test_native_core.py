"""Native production core tests (Sprint 6). Skipped with an explicit reason when the native binary is not built
(docs/BUILD_COMMANDS.md CMD-13); the Sprint 6 evidence shows them executed."""
import unittest

import numpy as np

from smlsp3000.native import driver
from smlsp3000.validation import fixtures as F
from smlsp3000.validation.production_track_a import compare, ref_render

HAVE = driver.available()


@unittest.skipUnless(HAVE, f"native binary not built at {driver.binary_path()} (CMD-13)")
class NativeCoreTests(unittest.TestCase):
    def test_latency_matches_reference_and_ceiling(self):
        for fs, expect in ((48000, 310), (96000, 449)):
            j = driver.info(fs)
            self.assertTrue(j["ok"]); self.assertEqual(j["info"]["latency_host_samples"], expect)
            self.assertLessEqual(expect / fs, 0.010)

    def test_determinism_and_partition_invariance(self):
        x = F.render_fixture("multitone_mix_m12", 48000, 0.2)
        a, _ = driver.render(x, 48000, block=64); b, _ = driver.render(x, 48000, blocks=[1, 7, 500, 8192, 64, 3]); c, _ = driver.render(x, 48000, block=20000)
        self.assertTrue(np.array_equal(a, b)); self.assertTrue(np.array_equal(a, c))

    def test_agreement_with_reference_within_owner_limits(self):
        x = F.render_fixture("overrange_steps_pm16", 48000, 0.2)
        y_ref, e = ref_render(x, 48000, {})
        for exact in (0, 1):
            y, j = driver.render(x, 48000, config={"exact_order": exact}, block=64)
            cells = compare(x, y_ref, y)
            for c in cells:
                self.assertTrue(c["pass"], c)
            self.assertEqual(j["meters"]["channel"][0]["sp_clip"], e.meters()["sp"][0]["converter_clip_count"])

    def test_state_rejections(self):
        base = driver.info(48000)["state"]
        self.assertTrue(driver.state_load(base)["ok"])
        self.assertEqual(driver.state_load(base.replace("schema_version=1", "schema_version=2"))["code"], "UNSUPPORTED_SCHEMA_VERSION")
        self.assertEqual(driver.state_load(base + "reduction_rule=TRUNCATION\n")["code"], "UNKNOWN_KEY")
        self.assertEqual(driver.state_load(base.replace("output_trim_db=0\n", "output_trim_db=99\n"))["code"], "OUT_OF_RANGE")

    def test_nonfinite_input_and_bypass(self):
        x = F.render_fixture("sine_1k_m20", 48000, 0.1); x[100, 0] = np.nan
        y, j = driver.render(x, 48000, block=64)
        self.assertEqual(j["meters"]["nonfinite_input_samples"], 1); self.assertTrue(np.all(np.isfinite(y))); self.assertEqual(j["meters"]["faults"], 0)
        yb, jb = driver.render(np.nan_to_num(x), 48000, config={"bypass": 1}, block=64); lat = jb["info"]["latency_host_samples"]
        self.assertTrue(np.array_equal(yb[lat:lat + x.shape[0]], np.nan_to_num(x)))


if __name__ == "__main__":
    unittest.main()
