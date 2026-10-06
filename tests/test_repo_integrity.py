"""VAL-001 / REQ-001 and the structural part of VAL-028 / REQ-028."""
import unittest

from tools.check_repo_integrity import run_all


class RepoIntegrityTests(unittest.TestCase):
    def test_all_integrity_checks_pass(self):
        res = run_all()
        failed = {k: v for k, v in res.items() if not v["pass"]}
        self.assertEqual(failed, {}, msg=str(failed))


if __name__ == "__main__":
    unittest.main()
