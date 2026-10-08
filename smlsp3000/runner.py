"""Minimal analysis runner CLI.

    python3 -m smlsp3000.runner run CHAIN-EXP-016 --out research/sim/CHAIN-EXP-016
    python3 -m smlsp3000.runner verify-manifest research/sim/CHAIN-EXP-016
    python3 -m smlsp3000.runner integrity

Experiments are addressed by their repository IDs only. Unknown IDs are an error,
never a silently substituted test.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .experiments import exp016, exp017
from .hashing import verify_manifest

EXPERIMENTS = {
    exp016.EXPERIMENT_ID: exp016.run,
    exp017.EXPERIMENT_ID: exp017.run,
}


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    ap = argparse.ArgumentParser(prog="smlsp3000.runner")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run an experiment by repository ID")
    r.add_argument("experiment_id")
    r.add_argument("--out", required=True)
    v = sub.add_parser("verify-manifest", help="verify manifest.sha256 in a directory")
    v.add_argument("directory")
    sub.add_parser("integrity", help="VAL-001 repository integrity checks")
    s3 = sub.add_parser("validate-sprint3", help="Sprint 3 software-track checks VAL-008/009/010/011/017 (Track A)")
    s3.add_argument("--out", required=True)
    s4 = sub.add_parser("validate-sprint4", help="Sprint 4 software-track checks VAL-012/013/014 (Track A, MPC)")
    s4.add_argument("--out", required=True)
    s5 = sub.add_parser("validate-sprint5", help="Sprint 5 software-track checks VAL-015/016 (Track A, cascade)")
    s5.add_argument("--out", required=True)
    s6 = sub.add_parser("validate-sprint6", help="Sprint 6 software-track checks VAL-019/020/021/022 (Track A, native production core vs reference)")
    s6.add_argument("--out", default="research/validation"); s6.add_argument("--evidence", default="evidence/sprint_06"); s6.add_argument("--quick", action="store_true"); s6.add_argument("--only", default=None, help="run a single check (VAL-019/020/021/022)")
    s7 = sub.add_parser("validate-sprint7", help="Sprint 7 plugin-wrapper checks VAL-023/024/025/026 + pluginval (Linux build)")
    s7.add_argument("--evidence", default="evidence/sprint_07"); s7.add_argument("--quick", action="store_true"); s7.add_argument("--only", default=None)
    nb = sub.add_parser("native-bench", help="Sprint 6 native Release benchmark (OWN-DEC-017)")
    nb.add_argument("--out", default="evidence/sprint_06/benchmark"); nb.add_argument("--seconds", type=float, default=5.0); nb.add_argument("--trials", type=int, default=3); nb.add_argument("--warmup", type=float, default=1.0)
    lk = sub.add_parser("listening-kit", help="CHAIN-EXP-018 software-only listening kit (preparation only)")
    lk.add_argument("--out", required=True)
    sa = sub.add_parser("scope-audit", help="VAL-018 scope audit")
    sa.add_argument("--out", required=True)
    pd = sub.add_parser("preset-lab-demo-source", help="Preset Lab: regenerate the deterministic synthetic demo beat (tool demonstration/tests only)")
    pd.add_argument("--out", default="reference/preset_lab/sources"); pd.add_argument("--rate", type=int, default=48000)
    ns = ap.parse_args(argv)

    if ns.cmd == "run":
        fn = EXPERIMENTS.get(ns.experiment_id)
        if fn is None:
            print(f"unknown experiment id {ns.experiment_id}; known: {sorted(EXPERIMENTS)}", file=sys.stderr)
            return 2
        record = fn(ns.out, command="python3 -m smlsp3000.runner " + " ".join(argv))
        print(json.dumps({"experiment_id": record["experiment_id"], "outcome": record["outcome"],
                          "floor": record["results"].get("floor"), "pattern_consistent": record["results"].get("pattern_consistent")}, indent=1))
        return 0 if record["outcome"] in ("PASS", "INFORMATIONAL") else 1
    if ns.cmd == "verify-manifest":
        res = verify_manifest(ns.directory)
        bad = {k: v for k, v in res.items() if v != "OK"}
        for k, v in sorted(res.items()):
            print(f"{v:9s} {k}")
        return 0 if not bad else 1
    if ns.cmd == "validate-sprint3":
        from .validation.sp1200_track_a import run_all
        res = run_all(ns.out, "python3 -m smlsp3000.runner " + " ".join(argv))
        print(json.dumps(res, indent=1))
        return 0 if all(v == "PASS" for v in res.values()) else 1
    if ns.cmd == "validate-sprint4":
        from .validation.mpc3000_track_a import run_all as run4
        res = run4(ns.out, "python3 -m smlsp3000.runner " + " ".join(argv))
        print(json.dumps(res, indent=1))
        return 0 if all(v == "PASS" for v in res.values()) else 1
    if ns.cmd == "validate-sprint7":
        from .validation import plugin_track_a
        res = plugin_track_a.run_all(ns.evidence, "python3 -m smlsp3000.runner validate-sprint7 --evidence " + ns.evidence + (" --quick" if ns.quick else "") + (" --only " + ns.only if ns.only else ""), quick=ns.quick, only=ns.only)
        print(json.dumps(res, indent=1)); return 0 if all(v == "PASS" for v in res.values()) else 1
    if ns.cmd == "validate-sprint6":
        from .validation import production_track_a
        res = production_track_a.run_all(ns.out, ns.evidence, "python3 -m smlsp3000.runner validate-sprint6 --out " + ns.out + (" --quick" if ns.quick else "") + (" --only " + ns.only if ns.only else ""), quick=ns.quick, only=ns.only)
        print(json.dumps(res, indent=1)); return 0 if all(v == "PASS" for v in res.values()) else 1
    if ns.cmd == "native-bench":
        from .validation import production_track_a
        rec = production_track_a.benchmark(ns.out, ns.seconds, ns.trials, ns.warmup)
        print(json.dumps({k: {"max_mean_load": v["max_mean_load"], "limit": v["limit_mean_load"], "p999_target_met": v["p999_target_met"], "overruns": v["overruns_total"]} for k, v in rec["pairs"].items()} | {"mean_load_limits_all_pass": rec["all_pass"], "p999_target_met_all_pairs": rec["p999_target_met_all_pairs"]}, indent=1)); return 0 if rec["all_pass"] else 1
    if ns.cmd == "validate-sprint5":
        from .validation.cascade_track_a import run_all as run5
        res = run5(ns.out, "python3 -m smlsp3000.runner " + " ".join(argv))
        print(json.dumps(res, indent=1))
        return 0 if all(v == "PASS" for v in res.values()) else 1
    if ns.cmd == "listening-kit":
        from .listening.kit import generate
        r = generate(ns.out, command="python3 -m smlsp3000.runner " + " ".join(argv))
        print(json.dumps({"experiment_id": r["experiment_id"], "status": r["status"], "files": len(r["entries"])}, indent=1))
        return 0
    if ns.cmd == "preset-lab-demo-source":
        from .preset_lab.demo_source import write_demo_source
        rec = write_demo_source(Path(ns.out), ns.rate)
        print(json.dumps({"file": rec["file"], "wav_sha256": rec["wav_sha256"], "samples_sha256": rec["samples_sha256"]}, indent=1))
        return 0
    if ns.cmd == "scope-audit":
        from .validation.scope_audit import run as scope_run
        r = scope_run(ns.out, "python3 -m smlsp3000.runner " + " ".join(argv))
        print(json.dumps({"check_id": r["check_id"], "outcome": r["outcome"]}))
        return 0 if r["outcome"] == "PASS" else 1
    if ns.cmd == "integrity":
        from tools.check_repo_integrity import main as integrity_main  # noqa: WPS433
        return integrity_main([])
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
