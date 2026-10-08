# Preset Lab reference material and renders

* `sources/` — reference material for auditioning. Audio is git-ignored; `demo_beat_48000.json` records the hash of the deterministic synthetic demo beat, regenerated with `python3 -m smlsp3000.runner preset-lab-demo-source --out reference/preset_lab/sources --rate 48000`. The owner's own beats are loaded from anywhere and are never committed.
* `renders/<id>_r<rev>/` — audition renders (32-bit float WAV, git-ignored) and their `.render.json` records (kept). Regenerate with `smlsp3000_preset_lab --render <candidate.json> <source.wav> <out_dir>` (docs/PRESET_LAB.md).
