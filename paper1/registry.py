"""The paper-1 subset of the project's hash-chained pre-registration registry.

The project keeps one append-only registry (``REGISTRY.jsonl``). Every row carries
``prev_sha256``, the SHA-256 of *all registry bytes before it*, and a sidecar head records
the length and SHA-256 of the whole file. Editing or deleting any earlier row breaks the chain.

This release ships (``data/registry/``):

- ``paper1-rows.jsonl``: the paper-1 rows, byte-identical to the registry lines;
- ``paper1-rows-redacted.jsonl``: three paper-1 rows with private local paths or internal
  reviewer names replaced (each carries a ``_redacted`` note with the source line's hash);
- ``INDEX.json``: one entry per registry row (all 164): offset, length, the line's SHA-256,
  the ``prev_sha256`` recorded in it and whether it is shipped verbatim, redacted or withheld;
  plus the head (bytes, records, SHA-256 of the whole file).

Because ``prev_sha256`` hashes every earlier byte, the chain itself can be recomputed only
from the full file, which is available on request (README). ``verify_full`` does that and also
checks that the shipped rows sit, byte for byte, at their indexed positions. Without the full
file, ``check_shipped`` verifies the shipped rows against the index and the index against
itself (offsets, lengths, row count and byte total equal the head).

    python -m paper1.registry check                          # shipped subset
    python -m paper1.registry verify-full REGISTRY.jsonl     # with the full registry
    python -m paper1.registry files                          # registered file hashes
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from paper1 import DATA, ROOT

REG_DIR = DATA / "registry"

# Files shipped in this release whose SHA-256 is recorded in a registry row:
# (shipped path, registry row, key in that row's files_sha256 or the field that holds the hash).
REGISTERED_FILES = (
    ("data/results/stage1/results.json", 136, "docs/xp/results-2026-10-16/results.json"),
    ("data/results/stage1/results.md", 136, "docs/xp/results-2026-10-16/results.md"),
    ("data/results/official-tau2/score.json", 138, "docs/xp/official-tau2-2026-10-17/score.json"),
    ("paper1/fgate/rbc.py", 140, "slh/xp/fgate/rbc.py"),
    ("data/bfcl-audit/gate-summary.md", 141, "docs/xp/bfcl-audit/gate-summary.md"),
    ("data/bfcl-audit/test-summary.md", 142, "docs/xp/bfcl-audit/test-summary.md"),
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def index(reg_dir: Path = REG_DIR) -> dict[str, Any]:
    return json.loads((Path(reg_dir) / "INDEX.json").read_text(encoding="utf-8"))


def _lines(path: Path) -> list[bytes]:
    return Path(path).read_bytes().splitlines(keepends=True) if Path(path).is_file() else []


def shipped_rows(reg_dir: Path = REG_DIR) -> list[dict[str, Any]]:
    """Every shipped paper-1 row (verbatim and redacted), in registry order, each with its
    registry row number under ``_row``."""
    idx = index(reg_dir)
    verb = [e for e in idx["rows"] if e["shipped"] == "verbatim"]
    out = []
    for e, line in zip(verb, _lines(Path(reg_dir) / "paper1-rows.jsonl"), strict=True):
        out.append({**json.loads(line), "_row": e["row"]})
    for line in _lines(Path(reg_dir) / "paper1-rows-redacted.jsonl"):
        r = json.loads(line)
        out.append({**r, "_row": r["_redacted"]["row"]})
    return sorted(out, key=lambda r: r["_row"])


def row(n: int, reg_dir: Path = REG_DIR) -> dict[str, Any]:
    found = [r for r in shipped_rows(reg_dir) if r["_row"] == n]
    if len(found) != 1:
        raise KeyError(f"registry row {n} is not shipped")
    return found[0]


def check_shipped(reg_dir: Path = REG_DIR) -> dict[str, Any]:
    """Shipped rows against the index; the index against itself and its head."""
    idx = index(reg_dir)
    problems: list[str] = []
    rows, head = idx["rows"], idx["head"]
    pos = 0
    for k, e in enumerate(rows, 1):
        if e["row"] != k or e["offset"] != pos:
            problems.append(f"index row {k}: numbering or offset out of sequence")
        pos += e["bytes"]
    if pos != head["bytes"] or len(rows) != head["records"]:
        problems.append("index rows do not add up to the head (bytes / records)")
    verb = [e for e in rows if e["shipped"] == "verbatim"]
    lines = _lines(Path(reg_dir) / "paper1-rows.jsonl")
    if len(lines) != len(verb):
        problems.append(f"{len(lines)} verbatim lines, index lists {len(verb)}")
    for e, line in zip(verb, lines):
        if len(line) != e["bytes"] or _sha(line) != e["line_sha256"]:
            problems.append(f"row {e['row']}: bytes differ from the indexed line")
        r = json.loads(line)
        if r.get("event") != e.get("event") or r.get("prev_sha256") != e["prev_sha256"]:
            problems.append(f"row {e['row']}: event or prev_sha256 differs from the index")
    red = {e["row"]: e for e in rows if e["shipped"] == "redacted"}
    seen = set()
    for line in _lines(Path(reg_dir) / "paper1-rows-redacted.jsonl"):
        r = json.loads(line)
        n = r["_redacted"]["row"]
        seen.add(n)
        e = red.get(n)
        if e is None or r["_redacted"]["source_line_sha256"] != e["line_sha256"] or \
                r.get("prev_sha256") != e["prev_sha256"] or r.get("event") != e.get("event"):
            problems.append(f"redacted row {n}: does not match its index entry")
    if seen != set(red):
        problems.append("redacted rows differ from the index")
    return {"ok": not problems, "problems": problems, "rows_total": len(rows),
            "verbatim": len(verb), "redacted": len(red),
            "withheld": sum(1 for e in rows if e["shipped"] == "withheld"),
            "head_sha256": head["sha256"]}


def verify_full(registry: Path, reg_dir: Path = REG_DIR) -> dict[str, Any]:
    """With the full registry file: recompute the prefix-hash chain and the head, and check
    that every indexed line (so every shipped verbatim row) sits at its offset unchanged."""
    raw = Path(registry).read_bytes()
    idx = index(reg_dir)
    problems: list[str] = []
    if len(raw) != idx["head"]["bytes"] or _sha(raw) != idx["head"]["sha256"]:
        problems.append("file length or SHA-256 differs from the head in INDEX.json")
    pos, chained = 0, False
    lines = raw.splitlines(keepends=True)
    if len(lines) != len(idx["rows"]):
        problems.append(f"{len(lines)} rows, index lists {len(idx['rows'])}")
    for k, (line, e) in enumerate(zip(lines, idx["rows"]), 1):
        r = json.loads(line)
        if "prev_sha256" in r:
            chained = True
            if r["prev_sha256"] != _sha(raw[:pos]):
                problems.append(f"row {k}: prev_sha256 is not the hash of the bytes before it")
        elif chained:
            problems.append(f"row {k}: unchained row after chained rows")
        if e["offset"] != pos or _sha(line) != e["line_sha256"]:
            problems.append(f"row {k}: differs from INDEX.json")
        pos += len(line)
    shipped = check_shipped(reg_dir)
    return {"ok": not problems and shipped["ok"], "problems": problems + shipped["problems"],
            "rows": len(lines), "bytes": len(raw), "sha256": _sha(raw)}


def redacted_copy_sha256(path: Path, frozen_sha256: str) -> str:
    """The accepted SHA-256 for a shipped redacted copy of a frozen file: its redacted hash
    if REDACTION.json binds that copy to ``frozen_sha256``, else ``frozen_sha256`` (so a
    caller comparing hashes refuses)."""
    red = json.loads((DATA / "bfcl-audit" / "REDACTION.json").read_text(encoding="utf-8"))
    sha = _sha(Path(path).read_bytes())
    for f in red["files"]:
        if f["frozen_sha256"] == frozen_sha256 and f["redacted_sha256"] == sha:
            return sha
    return frozen_sha256


def check_files(reg_dir: Path = REG_DIR) -> dict[str, Any]:
    """Shipped files whose SHA-256 a registry row records, and the redacted defect lists
    against the frozen hashes of rows 141 and 142."""
    out = []
    for rel, n, key in REGISTERED_FILES:
        want = row(n, reg_dir)["files_sha256"][key]
        got = _sha((ROOT / rel).read_bytes())
        out.append({"file": rel, "row": n, "registered_as": key, "match": got == want})
    red = json.loads((DATA / "bfcl-audit" / "REDACTION.json").read_text(encoding="utf-8"))
    for f in red["files"]:
        r = [x for x in shipped_rows(reg_dir) if x.get("event") == f["registry_event"]]
        got = _sha((DATA / "bfcl-audit" / f["file"]).read_bytes())
        out.append({"file": f"data/bfcl-audit/{f['file']}", "row": r[0]["_row"],
                     "registered_as": "defect_list_sha256 (frozen original; this is the "
                                      "redacted copy bound to it by REDACTION.json)",
                     "match": len(r) == 1 and r[0]["defect_list_sha256"] == f["frozen_sha256"]
                     and got == f["redacted_sha256"]})
    return {"ok": all(x["match"] for x in out), "files": out}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m paper1.registry")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    v = sub.add_parser("verify-full")
    v.add_argument("registry", type=Path)
    sub.add_parser("files")
    args = ap.parse_args(argv)
    if args.cmd == "check":
        rep = check_shipped()
    elif args.cmd == "files":
        rep = check_files()
    else:
        rep = verify_full(args.registry)
    print(json.dumps(rep, indent=1))
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
