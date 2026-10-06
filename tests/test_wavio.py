import tempfile
import unittest
from pathlib import Path

import numpy as np

from smlsp3000.wavio import read_wav, write_wav


class WavIOTests(unittest.TestCase):
    def _roundtrip(self, bits, channels):
        rng = np.random.default_rng(1)
        x = rng.uniform(-0.9, 0.9, size=(1000, channels))
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "t.wav"
            write_wav(p, x, 48000, bits)
            y, rate, depth, tag = read_wav(p)
        self.assertEqual(rate, 48000)
        self.assertEqual(depth, bits)
        self.assertEqual(y.shape, x.shape)
        return x, y, tag

    def test_pcm16(self):
        x, y, tag = self._roundtrip(16, 1)
        self.assertEqual(tag, 1)
        self.assertLess(np.max(np.abs(x - y)), 1.0 / 32768)

    def test_pcm24_stereo(self):
        x, y, tag = self._roundtrip(24, 2)
        self.assertEqual(tag, 1)
        self.assertLess(np.max(np.abs(x - y)), 1.0 / (1 << 23))

    def test_float32_exact_for_float32_values(self):
        x = np.linspace(-1, 1, 500).astype(np.float32).astype(np.float64)[:, None]
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "f.wav"
            write_wav(p, x, 192000, 32)
            y, rate, depth, tag = read_wav(p)
        self.assertEqual((rate, depth, tag), (192000, 32, 3))
        self.assertTrue(np.array_equal(x, y))

    def test_integer_write_clamps_instead_of_wrapping(self):
        x = np.array([[2.0], [-2.0], [0.5]])
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "c.wav"
            write_wav(p, x, 44100, 16)
            y, *_ = read_wav(p)
        self.assertAlmostEqual(y[0, 0], (32767 / 32768))
        self.assertAlmostEqual(y[1, 0], -1.0)


if __name__ == "__main__":
    unittest.main()
