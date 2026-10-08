"""Classify a dirty working tree before a stabilization commit (owner-side helper; read-only).

Prints every modified/added/deleted/untracked path with a class:
  FROZEN-DSP      native/ (core, adapter, generated assets), plugin/src/ (processor, editor, identity), reference implementation,
                  controls/assets, acceptance tolerances, reference outputs -> any change here must STOP the task
  IMMUTABLE       docs/research/, docs/sprint_prompts/ -> must never change
  VALIDATION      smlsp3000/validation/, tests/, plugin/tools/, plugin/CMakeLists.txt, native/tests/ -> approved harness/regression work
  DOCS-EVIDENCE   docs/, evidence/, research/, presets/, reference/, README/AGENTS -> documentation/evidence
  OTHER           everything else (review by hand)
Exit code 2 when FROZEN-DSP or IMMUTABLE paths are dirty, 0 otherwise. Usage: python3 tools/audit_worktree.py [--json]
"""
from __future__ import annotations

import json
import subprocess
import sys

FROZEN = ("native/include/", "native/src/", "native/generated/", "native/CMakeLists.txt", "plugin/src/", "smlsp3000/reference/", "smlsp3000/native/driver.py",
          "plugin/product_identity.json", "plugin/JUCE_PIN.json", "docs/ACCEPTANCE_MATRIX")
IMMUTABLE = ("docs/research/", "docs/sprint_prompts/")
VALIDATION = ("smlsp3000/validation/", "tests/", "plugin/tools/", "plugin/CMakeLists.txt", "native/tests/", "native/tools/", "tools/")
DOCS = ("docs/", "evidence/", "research/", "presets/", "reference/", "README.md", "AGENTS.md", ".gitignore")


def classify(path: str) -> str:
    if path.startswith(IMMUTABLE):
        return "IMMUTABLE"
    if path.startswith(FROZEN):
        return "FROZEN-DSP"
    if path.startswith(VALIDATION):
        return "VALIDATION"
    if path.startswith(DOCS):
        return "DOCS-EVIDENCE"
    return "OTHER"


def main(argv: list[str]) -> int:
    out = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], capture_output=True, text=True, check=True).stdout
    rows = []
    for line in out.splitlines():
        status, path = line[:2].strip() or "??", line[3:]
        if " -> " in path:
            path = path.split(" -> ")[-1]
        rows.append({"status": status, "path": path, "class": classify(path)})
    blocking = [r for r in rows if r["class"] in ("FROZEN-DSP", "IMMUTABLE")]
    if "--json" in argv:
        print(json.dumps({"rows": rows, "blocking": blocking, "verdict": "STOP" if blocking else "OK"}, indent=1))
    else:
        for r in rows:
            print(f"{r['class']:14} {r['status']:3} {r['path']}")
        print(f"\n{len(rows)} dirty paths; blocking (FROZEN-DSP/IMMUTABLE): {len(blocking)} -> {'STOP: review before any commit' if blocking else 'OK for a stabilization commit after review'}")
    return 2 if blocking else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
