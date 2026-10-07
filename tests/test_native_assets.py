"""The generated native asset header must match the JSON assets, research configurations, product configuration and frozen controls."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class NativeAssetHeaderTests(unittest.TestCase):
    def test_generated_header_in_sync(self):
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "gen_native_assets.py"), "--check"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_product_controls_v1(self):
        c = json.loads((ROOT / "smlsp3000" / "reference" / "assets" / "product_controls_v1.json").read_text())
        self.assertEqual(c["schema_version"], 1)
        self.assertEqual(set(c["controls"]), {"sp_input_level_db", "sp_input_gain", "interstage_level_db", "mpc_input_gain", "output_trim_db", "plugin_bypass"})
        self.assertEqual((c["controls"]["sp_input_level_db"]["min"], c["controls"]["sp_input_level_db"]["max"], c["controls"]["sp_input_level_db"]["default"]), (-60.0, 12.0, 0.0))
        self.assertEqual((c["controls"]["interstage_level_db"]["min"], c["controls"]["interstage_level_db"]["max"]), (-60.0, 24.0))
        self.assertEqual((c["controls"]["output_trim_db"]["min"], c["controls"]["output_trim_db"]["max"]), (-60.0, 12.0))
        self.assertEqual(c["controls"]["mpc_input_gain"]["default"], "LO"); self.assertFalse(c["controls"]["plugin_bypass"]["default"])
        self.assertEqual(c["product_profile"]["chain_mode"], "CASCADE"); self.assertEqual(c["product_profile"]["reduction_rule"], "ROUND_NEAREST")
        for excluded in ("drive", "wet", "reverse"):
            self.assertNotIn(excluded, " ".join(c["controls"]))


if __name__ == "__main__":
    unittest.main()
