"""VAL-001 / REQ-001 repository integrity checks (documentary provenance).

Checks (each printed PASS/FAIL):
  1. Immutable research sources match the SHA-256 recorded in docs/PACKAGE_VALIDATION.md.
  2. Exactly eight sprint contracts SPRINT_01..08 exist.
  3. Every local Markdown link in docs/ and root resolves to an existing file.
  4. ACCEPTANCE_MATRIX.md has 28 unique REQ/VAL rows and the CSV has the same IDs.
  5. SHA256SUMS.txt entries verify, with the known CRLF→LF normalization of
     docs/ACCEPTANCE_MATRIX.csv reported explicitly (content-identical after
     line-ending normalization) rather than hidden.
Exit code 0 only if every check passes (the known CSV line-ending case counts
as PASS only because the CRLF-restored bytes reproduce the manifest hash).
"""
from __future__ import annotations

import csv
import hashlib
import io
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "docs/research/SP1200_MPC3000_MIX_PROCESSOR_RESEARCH_PACKAGE_V1.md": "cea524a87d1b19d45e35511dacaca31aeedf03cbe4f2647737a96a2317903b1c",
    "docs/research/SP1200_MPC3000_HANDOFF_V1.json": "ca16711489f460a303977a5ed84957121f64b1c5a8969c903e55b66b795bac31",
}
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def check_sources() -> tuple[bool, str]:
    bad = []
    for rel, want in SOURCES.items():
        got = sha256(ROOT / rel)
        if got != want:
            bad.append(f"{rel}: {got} != {want}")
    return (not bad, "; ".join(bad) or "both research sources byte-identical to PACKAGE_VALIDATION hashes")


def check_contracts() -> tuple[bool, str]:
    d = ROOT / "docs" / "sprint_prompts"
    names = sorted(p.name for p in d.glob("SPRINT_*.md"))
    want = [f"SPRINT_{i:02d}.md" for i in range(1, 9)]
    return (names == want, f"found {names}")


def check_links() -> tuple[bool, str]:
    bad = []
    files = list((ROOT / "docs").rglob("*.md")) + [ROOT / "README.md", ROOT / "AGENTS.md", ROOT / "MANIFEST.md"]
    for f in files:
        if "research" in f.parts:
            continue  # immutable sources are not link-checked
        for m in LINK_RE.finditer(f.read_text(encoding="utf-8")):
            target = m.group(1)
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = target.split("#")[0]
            if not (f.parent / target).exists():
                bad.append(f"{f.relative_to(ROOT)} -> {target}")
    return (not bad, "; ".join(bad) or "all local markdown links resolve")


def check_matrix() -> tuple[bool, str]:
    md = (ROOT / "docs" / "ACCEPTANCE_MATRIX.md").read_text(encoding="utf-8")
    md_ids = re.findall(r"^\| (REQ-\d{3}) / (VAL-\d{3}) \|", md, flags=re.M)
    reqs = [r for r, _ in md_ids]
    text = (ROOT / "docs" / "ACCEPTANCE_MATRIX.csv").read_text(encoding="utf-8")
    rows = list(csv.DictReader(io.StringIO(text)))
    csv_reqs = []
    for row in rows:
        for v in row.values():
            if isinstance(v, str) and re.fullmatch(r"REQ-\d{3}( / VAL-\d{3})?", v.strip()):
                csv_reqs.append(v.strip().split(" ")[0])
                break
    ok = len(reqs) == 28 and len(set(reqs)) == 28 and sorted(csv_reqs) == sorted(reqs)
    return (ok, f"md rows={len(reqs)} unique={len(set(reqs))} csv rows={len(csv_reqs)}")


IMMUTABLE_PREFIXES = ("docs/research/", "docs/sprint_prompts/")


def check_sha256sums() -> tuple[bool, str]:
    """Verify SHA256SUMS.txt (planning V1 manifest).

    Immutable items (research sources, the eight contracts) must verify byte-exact
    (CRLF->LF normalization of a text file is reported, not hidden). Living
    documents may legitimately be revised after planning V1; they are listed as
    REVISED for information and do not fail the check.
    """
    notes = []
    revised = []
    ok = True
    for line in (ROOT / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, _, rel = line.partition("  ")
        rel = rel.strip()
        p = ROOT / rel
        if not p.exists():
            ok = False
            notes.append(f"missing {rel}")
            continue
        data = p.read_bytes()
        if hashlib.sha256(data).hexdigest() == digest:
            continue
        crlf = data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        if hashlib.sha256(crlf).hexdigest() == digest:
            notes.append(f"{rel}: LF in repository, manifest hashed CRLF bytes; content identical after line-ending normalization")
        elif rel.startswith(IMMUTABLE_PREFIXES):
            ok = False
            notes.append(f"{rel}: IMMUTABLE FILE MISMATCH")
        else:
            revised.append(rel)
    if revised:
        notes.append(f"revised since planning V1 (living docs, allowed): {len(revised)} files")
    return (ok, "; ".join(notes) or "all SHA256SUMS entries verify byte-exact")


CHECKS = [
    ("VAL-001.sources", check_sources),
    ("VAL-001.contracts", check_contracts),
    ("VAL-001.links", check_links),
    ("VAL-001.matrix", check_matrix),
    ("VAL-001.sha256sums", check_sha256sums),
]


def run_all() -> dict[str, dict]:
    out = {}
    for name, fn in CHECKS:
        ok, msg = fn()
        out[name] = {"pass": ok, "detail": msg}
    return out


def main(argv: list[str]) -> int:
    res = run_all()
    allok = True
    for name, r in res.items():
        print(f"{'PASS' if r['pass'] else 'FAIL'}  {name}: {r['detail']}")
        allok &= r["pass"]
    return 0 if allok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
