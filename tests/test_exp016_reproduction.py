"""Same-build determinism (validation domain 2): re-running CHAIN-EXP-016 reproduces the committed record exactly."""
import json
import tempfile
import unittest
from pathlib import Path

from smlsp3000.experiments import exp016

ROOT = Path(__file__).resolve().parents[1]
COMMITTED = ROOT / "research" / "sim" / "CHAIN-EXP-016" / "result.json"


class Exp016ReproductionTests(unittest.TestCase):
    def test_rerun_reproduces_committed_results_and_hashes(self):
        self.assertTrue(COMMITTED.exists(), "committed CHAIN-EXP-016 record missing")
        committed = json.loads(COMMITTED.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as d:
            rec = exp016.run(d, command="unittest")
        self.assertEqual(rec["outcome"], "PASS")
        self.assertTrue(rec["results"]["identical_array_exact_zero"])
        self.assertEqual(rec["raw_output_sha256"], committed["raw_output_sha256"])
        self.assertEqual(rec["results"], committed["results"])
        self.assertEqual(rec["input_config_sha256"], committed["input_config_sha256"])
        self.assertEqual(rec["algorithm_version"], committed["algorithm_version"])


if __name__ == "__main__":
    unittest.main()
