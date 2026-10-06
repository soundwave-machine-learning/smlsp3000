import tempfile
import unittest
from pathlib import Path

import numpy as np

from smlsp3000.hashing import read_manifest, sha256_array, sha256_bytes, sha256_file, verify_manifest, write_manifest


class HashingTests(unittest.TestCase):
    def test_known_sha256(self):
        self.assertEqual(sha256_bytes(b"abc"), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")

    def test_array_hash_distinguishes_dtype_and_shape(self):
        a = np.arange(6, dtype=np.float64)
        self.assertEqual(sha256_array(a), sha256_array(a.copy()))
        self.assertNotEqual(sha256_array(a), sha256_array(a.astype(np.float32)))
        self.assertNotEqual(sha256_array(a), sha256_array(a.reshape(2, 3)))

    def test_manifest_roundtrip_and_verify(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "a.txt").write_bytes(b"hello")
            (root / "b.bin").write_bytes(bytes(range(256)))
            write_manifest(root, ["a.txt", "b.bin"])
            m = read_manifest(root / "manifest.sha256")
            self.assertEqual(m["a.txt"], sha256_file(root / "a.txt"))
            self.assertEqual(verify_manifest(root), {"a.txt": "OK", "b.bin": "OK"})
            (root / "b.bin").write_bytes(b"tampered")
            (root / "a.txt").unlink()
            self.assertEqual(verify_manifest(root), {"a.txt": "MISSING", "b.bin": "MISMATCH"})


if __name__ == "__main__":
    unittest.main()
