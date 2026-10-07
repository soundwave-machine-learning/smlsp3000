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
    sa = sub.add_parser("scope-audit", help="VAL-018 scope audit")
    sa.add_argument("--out", required=True)
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
