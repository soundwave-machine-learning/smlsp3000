"""Preset Lab (development tool) checks driven through its headless modes: candidate validation/round trip, deterministic
renders, product-path equivalence (lab render == native HostAdapter render, bit for bit) and metadata independence.
Skipped when the lab binary is not built (CMD-21)."""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import numpy as np

from smlsp3000 import wavio
from smlsp3000.native import driver

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "plugin" / "build" / "tools" / "preset_lab" / "smlsp3000_preset_lab_artefacts" / "Release" / "smlsp3000_preset_lab"
DEMO_DIR = ROOT / "presets" / "candidates" / "demo"
HAVE = LAB.exists() and driver.available()


def _xvfb(cmd):
    return (["xvfb-run", "-a", "-s", "-screen 0 1280x800x24"] if shutil.which("xvfb-run") else []) + cmd


def lab(*args, cwd=None):
    r = subprocess.run(_xvfb([str(LAB)] + [str(a) for a in args]), capture_output=True, text=True, cwd=cwd or ROOT, timeout=600)
    lines = [l for l in r.stdout.splitlines() if l.startswith("{")]
    return r.returncode, (json.loads(lines[-1]) if lines else {}), r.stdout + r.stderr


def demo_candidate(**pp):
    c = {"format": "smlsp3000-preset-candidate", "schema": 1, "id": "cand_pytest_0001", "name": "pytest", "category": "EXPERIMENTAL", "revision": 1,
         "product_parameters": {"sp_input_level_db": 0.0, "sp_input_gain_db": 0, "interstage_level_db": 0.0, "mpc_input_gain": "LO", "output_trim_db": 0.0, "plugin_bypass": False},
         "authoring_metadata": {"author": "pytest", "description": "d", "acceptance_status": "DRAFT", "source_material": ["synthetic"]}}
    c["product_parameters"].update(pp)
    return c


@unittest.skipUnless(HAVE, f"preset lab binary not built at {LAB} (CMD-21) or native tool missing (CMD-13)")
class TestPresetLab(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="smlsp3000_preset_lab_"))
        rate = 48000; n = rate // 2; t = np.arange(n) / rate
        x = 0.5 * np.exp(-3.0 * (t % 0.25)) * (np.sin(2 * np.pi * 55.0 * t) + 0.3 * np.sin(2 * np.pi * 1870.0 * t))
        cls.rate = rate; cls.src = np.stack([x, 0.8 * x], axis=1)
        cls.wav = cls.tmp / "src.wav"; wavio.write_wav(cls.wav, cls.src.astype(np.float32), rate, bit_depth=32)

    def write(self, cand, name="c.json"):
        p = self.tmp / name; p.write_text(json.dumps(cand, indent=1), encoding="utf-8"); return p

    def test_demo_candidates_validate(self):
        files = sorted(DEMO_DIR.glob("*.json"))
        self.assertGreaterEqual(len(files), 4)
        for f in files:
            rc, j, _ = lab("--validate", f)
            self.assertEqual((rc, j.get("code")), (0, "OK"), f.name)
            self.assertEqual(json.loads(f.read_text())["authoring_metadata"]["acceptance_status"], "TOOL_DEMO", "demo candidates are tool demonstrations, not factory presets")

    def test_round_trip_and_bounds(self):
        p = self.write(demo_candidate(sp_input_level_db=-7.25, sp_input_gain_db=20, interstage_level_db=3.5, mpc_input_gain="HI", output_trim_db=-2.0, plugin_bypass=True))
        out = self.tmp / "rt.json"
        rc, j, _ = lab("--roundtrip", p, out)
        self.assertEqual(rc, 0, j)
        back = json.loads(out.read_text())
        self.assertEqual(back["product_parameters"], json.loads(p.read_text())["product_parameters"])
        self.assertIn("sp_input_level_db=-7.25", j["state_text"]); self.assertIn("mpc_input_gain=HI", j["state_text"]); self.assertIn("plugin_bypass=1", j["state_text"])
        for bad, code in ((dict(sp_input_level_db=12.01), "OUT_OF_RANGE"), (dict(interstage_level_db=-60.5), "OUT_OF_RANGE"), (dict(output_trim_db=12.5), "OUT_OF_RANGE"),
                          (dict(sp_input_gain_db=10), "UNKNOWN_ENUM"), (dict(sp_input_gain_db=1), "UNKNOWN_ENUM"), (dict(mpc_input_gain="MEDIUM"), "UNKNOWN_ENUM"), (dict(mpc_input_gain=1), "UNKNOWN_ENUM"), (dict(plugin_bypass=0), "UNKNOWN_ENUM")):
            rc, j, _ = lab("--validate", self.write(demo_candidate(**bad), "bad.json"))
            self.assertEqual((rc, j.get("code")), (1, code), bad)

    def test_malformed_future_unknown_rejected(self):
        for mutate, code in (((lambda c: c.update(schema=2)), "UNSUPPORTED_SCHEMA_VERSION"), ((lambda c: c.update(format="other")), "NOT_A_CANDIDATE"), ((lambda c: c.update(extra=1)), "UNKNOWN_KEY"),
                             ((lambda c: c["product_parameters"].update(drive=0.5)), "UNKNOWN_KEY"), ((lambda c: c["product_parameters"].update(quantizer_rule="FLOOR")), "UNKNOWN_KEY"),
                             ((lambda c: c["product_parameters"].pop("output_trim_db")), "MISSING_FIELD"), ((lambda c: c.update(category="FACTORY")), "UNKNOWN_CATEGORY"),
                             ((lambda c: c["authoring_metadata"].update(acceptance_status="SHIPPED")), "UNKNOWN_ENUM")):
            c = demo_candidate(); mutate(c)
            rc, j, _ = lab("--validate", self.write(c, "m.json"))
            self.assertEqual((rc, j.get("code")), (1, code), code)
        garbage = self.tmp / "g.json"; garbage.write_bytes(b"\x00\xff{not json")
        rc, j, _ = lab("--validate", garbage); self.assertEqual((rc, j.get("code")), (1, "MALFORMED_JSON"))

    def test_init_state_equals_core_defaults(self):
        r = subprocess.run(_xvfb([str(LAB), "--init-state"]), capture_output=True, text=True, cwd=ROOT)
        self.assertIn("sp_input_level_db=0\n", r.stdout); self.assertIn("sp_input_gain_db=0\n", r.stdout); self.assertIn("interstage_level_db=0\n", r.stdout)
        self.assertIn("mpc_input_gain=LO\n", r.stdout); self.assertIn("output_trim_db=0\n", r.stdout); self.assertIn("plugin_bypass=0\n", r.stdout)
        info = driver.info(48000)
        self.assertTrue(info.get("ok", True))

    def _render(self, cand_path, out_name):
        out = self.tmp / out_name; rc, j, log = lab("--render", cand_path, self.wav, out)
        self.assertEqual(rc, 0, log[-500:]); self.assertTrue(j["ok"])
        return j, np.fromfile(j["raw_f64_path"], dtype=np.float64).reshape(-1, 2)

    def test_render_deterministic_and_equals_native_adapter_path(self):
        cand = self.write(demo_candidate(sp_input_level_db=6.0, interstage_level_db=3.0, sp_input_gain_db=20, mpc_input_gain="MID", output_trim_db=-6.0))
        j1, y1 = self._render(cand, "r1"); j2, y2 = self._render(cand, "r2")
        self.assertEqual(j1["output_f64_sha256"], j2["output_f64_sha256"]); self.assertTrue(np.array_equal(y1, y2))
        self.assertEqual(j1["frames_out"], j1["frames_in"] + j1["latency"]); self.assertEqual(j1["latency"], 310)
        # same ProductParameters through the native HostAdapter path (what the plugin runs) must give the same product output.
        # The lab applies values through the plugin's host parameters (float32 normalised mapping), so the EFFECTIVE values are used.
        e = j1["effective_host_mapped_values"]
        x32 = self.src.astype(np.float32).astype(np.float64)     # the lab reads WAV through JUCE as float32 then promotes (same as a float32 host)
        y_nat, rec = driver.render(x32, self.rate, config={"adapter": 1, "precision": 64, "sp_level": repr(e["sp_input_level_db"]), "sp_gain": int(e["sp_input_gain_db"]), "interstage": repr(e["interstage_level_db"]),
                                                             "mpc_gain": ["LO", "MID", "HI"][int(e["mpc_input_gain"])], "trim": repr(e["output_trim_db"]), "bypass": int(e["plugin_bypass"])}, block=512, max_block=512, drain=True)
        self.assertEqual(y_nat.shape, y1.shape, (y_nat.shape, y1.shape))
        self.assertTrue(np.array_equal(y_nat, y1), f"lab render differs from the native adapter render: max |d| = {np.max(np.abs(y_nat - y1))}")

    def test_metadata_does_not_alter_output_and_init_render_matches_native(self):
        a = self.write(demo_candidate(interstage_level_db=9.0), "a.json")
        b_c = demo_candidate(interstage_level_db=9.0); b_c.update(id="cand_pytest_0002", name="other", category="HEAVY", revision=5); b_c["authoring_metadata"].update(description="completely different", acceptance_status="CANDIDATE", audition_notes="x", clamp_observations="y", engineering_note="z", input_peak=0.5, output_peak=0.7)
        b = self.write(b_c, "b.json")
        ja, ya = self._render(a, "ma"); jb, yb = self._render(b, "mb")
        self.assertEqual(ja["output_f64_sha256"], jb["output_f64_sha256"]); self.assertTrue(np.array_equal(ya, yb))
        jc, yc = self._render(self.write(demo_candidate(interstage_level_db=3.0), "c2.json"), "mc"); self.assertNotEqual(ja["output_f64_sha256"], jc["output_f64_sha256"])
        ji, yi = self._render("INIT", "init")
        y_nat, _ = driver.render(self.src.astype(np.float32).astype(np.float64), self.rate, config={"adapter": 1, "precision": 64}, block=512, max_block=512, drain=True)
        self.assertTrue(np.array_equal(y_nat, yi), "INIT lab render differs from the native adapter render")
        self.assertEqual(ji["clamp_report"]["sp_clip"], [0, 0])

    def test_render_record_fields(self):
        j, _ = self._render(self.write(demo_candidate(sp_input_level_db=12.0, sp_input_gain_db=40, interstage_level_db=24.0), "hot.json"), "hot")
        for k in ("source_sha256", "output_f64_sha256", "output_file_sha256", "candidate_id", "candidate_revision", "rate", "product_parameters", "effective_host_mapped_values", "clamp_report", "tool_build_id", "native_core_version"):
            self.assertIn(k, j)
        self.assertGreater(j["clamp_report"]["sp_clip"][0], 0); self.assertGreater(j["clamp_report"]["mpc_clip18"][0], 0)
        self.assertEqual(j["product_parameters"]["sp_input_gain_db"], 40); self.assertEqual(j["product_parameters"]["mpc_input_gain"], "LO")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
