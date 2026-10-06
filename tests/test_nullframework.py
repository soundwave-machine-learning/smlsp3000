"""VAL-003 / REQ-003: null framework structural checks against independently generated truth."""
import unittest

import numpy as np

from smlsp3000.nullframework import EvaluatorConfig, align, kaiser_sinc_interpolate, null_identical, null_metrics
from smlsp3000.stimuli import self_test_stimulus


class NullFrameworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stim = self_test_stimulus()
        cls.fs = float(cls.stim.sample_rate_hz)
        cls.ref = cls.stim.render()

    def test_identical_arrays_null_to_exact_zero_without_preprocessing(self):
        res = null_identical(self.ref, self.ref.copy())
        self.assertTrue(np.all(res == 0.0))
        self.assertTrue(np.array_equal(self.ref, self.ref.copy()))
        m = null_metrics(self.ref, self.ref.copy(), self.fs)
        self.assertTrue(m.max_abs_residual_exact_zero)
        self.assertIsNone(m.residual_peak_dbfs)  # log of zero is undefined, reported as None, never as a pass/fail number

    def test_interpolator_is_identity_at_integer_positions(self):
        y = np.sin(np.arange(2000) * 0.01)
        out = kaiser_sinc_interpolate(y, np.arange(2000, dtype=np.float64), 48, 12.0)
        self.assertTrue(np.array_equal(out, y))

    def test_relative_metric_undefined_on_silence(self):
        z = np.zeros(1000)
        m = null_metrics(z, z, self.fs)
        self.assertIsNone(m.residual_rms_db_re_signal)
        self.assertIsNone(m.correlation)
        self.assertEqual(m.residual_rms, 0.0)

    def test_recovers_combined_perturbation_from_independent_truth(self):
        fs = self.fs
        true = dict(clock_ratio=1.0 + 61e-6, delay_s=7.63 / fs, polarity=-1, gain=10 ** (-2.5 / 20.0), dc=-0.004)
        cap = self.stim.render_perturbed(**true)
        est, corrected, ref_hp = align(self.ref, cap, self.stim, EvaluatorConfig())
        # Structural expectations: correct polarity sign; estimates land in the right
        # neighbourhood (the exact floor is recorded by CHAIN-EXP-016, not asserted here
        # with an invented tolerance): same sign and magnitude class as the truth.
        self.assertEqual(est.polarity, -1)
        self.assertEqual(round(est.delay_samples), 8)
        self.assertEqual(round((est.clock_ratio - 1.0) * 1e6), 61)
        self.assertEqual(round(20 * np.log10(est.gain) * 10) / 10, -2.5)
        self.assertEqual(round(est.dc_capture, 3), -0.004)
        a, b = int(0.92 * fs), int(1.98 * fs)
        m = null_metrics(ref_hp[a:b], corrected[a:b], fs)
        self.assertLess(m.residual_rms, m.signal_rms)  # the null reduces, never increases, the residual


if __name__ == "__main__":
    unittest.main()
