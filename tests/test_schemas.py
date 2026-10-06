import unittest

from smlsp3000 import schemas as S


class SchemaTests(unittest.TestCase):
    def test_vocabularies_frozen(self):
        self.assertIn("SIMULATION", S.ARTIFACT_CLASSES)
        self.assertIn("HARDWARE MEASUREMENT", S.ARTIFACT_CLASSES)
        self.assertEqual(S.DATASET_ROLES, ("FIT", "VALIDATION", "SELF_NULL", "NONE"))

    def test_artifact_entry_rejects_wrong_class(self):
        rec = {"path": "x.wav", "sha256": "0" * 64, "bytes": 1, "artifact_class": "HARDWARE", "dataset_role": "FIT"}
        probs = S.validate(rec, S.ARTIFACT_ENTRY)
        self.assertTrue(any("artifact_class" in p for p in probs))

    def test_unknown_field_is_reported_in_strict_mode(self):
        rec = {"path": "x", "sha256": "0" * 64, "bytes": 1, "artifact_class": "SIMULATION", "dataset_role": "NONE", "hidden_switch": True}
        self.assertTrue(any("unknown field" in p for p in S.validate(rec, S.ARTIFACT_ENTRY)))
        self.assertEqual(S.validate(rec, S.ARTIFACT_ENTRY, strict=False), [])

    def test_unset_semantics(self):
        rec = {"config_id": "c", "version": "1", "switches": {"sp_rounding_rule": S.UNSET}, "normalized_research_calibration": True, "notes": ""}
        self.assertEqual(S.validate(rec, S.RESEARCH_CONFIGURATION), [])
        self.assertEqual(S.require_set(rec["switches"], ["sp_rounding_rule", "hold_fraction"]), ["sp_rounding_rule", "hold_fraction"])
        asset = {"asset_id": "a", "version": "1", "machine": "SP-1200", "block_ids": ["R3"], "values": {},
                 "provenance": {}, "validity_conditions": "none", "sha256": S.UNSET}
        self.assertTrue(any("UNSET" in p for p in S.validate(asset, S.MACHINE_ASSET)))

    def test_missing_required_and_bool_type_strictness(self):
        rec = {"capture_id": "c"}
        probs = S.validate(rec, S.CAPTURE_SIDECAR)
        self.assertTrue(any("missing required field: unit_id" in p for p in probs))
        # a bool must not satisfy an int field
        entry = {"path": "x", "sha256": "0" * 64, "bytes": True, "artifact_class": "SIMULATION", "dataset_role": "NONE"}
        self.assertTrue(any("bytes" in p for p in S.validate(entry, S.ARTIFACT_ENTRY)))


if __name__ == "__main__":
    unittest.main()
