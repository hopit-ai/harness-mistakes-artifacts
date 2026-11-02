"""Owner-side helper: write the minimal derived tables that let ``reproduce.py`` recompute the
τ² F' gate and the BFCL held-out confirmation, instead of reading their reported results.

Not run for this release: the tables are added only after the owner decides to publish them
(README, "What is not here"). Output columns are the analysis inputs and nothing else.

    # τ² F' gate: the scored decision table and the hand-off pool (experiment kit tag xp-h1b-v1; kits private, on request)
    python tools/export_derived.py tau2-gate --table W/table.jsonl --pool PKG-H1/pool.json \
        --out data/derived

    # BFCL held-out confirmation: the H3 package (experiment kit tag xp-h3b-v1) and its export
    python tools/export_derived.py bfcl-h3 --package PKG-H3 --export EXPORT-H3 --out data/derived

What is kept
  tau2-gate  tracks ``fgate`` and ``difficulty`` only; per decision: track, unit, prefix
             (case_id) and configuration group (each replaced by an order-preserving pseudonym),
             context, inclusion bits, success, harm, re-ask, error class; for the difficulty
             track also arm, pair, phrasing and task. No messages, no gold decision, no
             answer key, no database content. The analyses sort units, prefixes and groups
             by id, so order-preserving pseudonyms leave every result unchanged.
  bfcl-h3    per episode: arm, trial, BFCL instance id, root, category, official success,
             harm. BFCL instances are public benchmark items; no trajectory is exported.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from paper1 import _io  # noqa: E402

TAU2_TRACKS = ("fgate", "difficulty")
TAU2_FIELDS = ("track", "unit_id", "case_id", "group", "context", "x", "y", "harm", "reask",
               "error_class")
DIFFICULTY_FIELDS = ("arm", "pair", "variant", "task")


def _pseudonyms(values: set[str], prefix: str) -> dict[str, str]:
    width = len(str(len(values)))
    return {v: f"{prefix}{k:0{width}d}" for k, v in enumerate(sorted(values))}


def tau2_gate(table: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [r for r in table if r.get("track") in TAU2_TRACKS]
    cases = _pseudonyms({r["case_id"] for r in rows}, "P")
    groups = _pseudonyms({str(r["group"]) for r in rows if r.get("group") is not None}, "G")
    units = _pseudonyms({str(r["unit_id"]) for r in rows if r.get("unit_id") is not None}, "U")
    out = []
    for r in rows:
        o = {k: r.get(k) for k in TAU2_FIELDS if k in r}
        o["case_id"] = cases[r["case_id"]]
        if r.get("group") is not None:
            o["group"] = groups[str(r["group"])]
        if r.get("unit_id") is not None:
            o["unit_id"] = units[str(r["unit_id"])]
        if r["track"] == "difficulty":
            o.update({k: r.get(k) for k in DIFFICULTY_FIELDS if k in r})
        out.append(o)
    return out


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> str:
    data = "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows).encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python tools/export_derived.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("tau2-gate")
    t.add_argument("--table", type=Path, required=True)
    t.add_argument("--pool", type=Path, required=True)
    t.add_argument("--out", type=Path, required=True)
    b = sub.add_parser("bfcl-h3")
    b.add_argument("--package", type=Path, required=True)
    b.add_argument("--export", type=Path, required=True)
    b.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    if args.cmd == "tau2-gate":
        from paper1.fgate import pool as fp

        pool = fp.verify_pool(_io.read_json(args.pool))
        rows = tau2_gate(_io.read_jsonl(args.table))
        sha = _write_jsonl(args.out / "tau2-fgate-table.jsonl", rows)
        _io.write_json(args.out / "tau2-fgate-pool.json", pool)
        print(json.dumps({"rows": len(rows), "table_sha256": sha, "pool_sha256": pool["sha256"]}))
        return 0
    from paper1.bfcl import confirm as C

    got = C.load_export(args.package, args.export)
    if got["problems"]:
        print(json.dumps({"refused": got["problems"]}), file=sys.stderr)
        return 3
    plan = got["plan"]
    design = "B-D9" if (plan.get("design") or {}).get("deviation") == "B-D9" else "registered"
    sha = _write_jsonl(args.out / "bfcl-h3-rows.jsonl", got["rows"])
    _io.write_json(args.out / "bfcl-h3-meta.json",
                   {"package_sha256": plan["sha256"], "design": design,
                    "empty_arms": plan.get("empty_arms") or [], "rows_sha256": sha,
                    "rows": len(got["rows"])})
    print(json.dumps({"rows": len(got["rows"]), "rows_sha256": sha}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
