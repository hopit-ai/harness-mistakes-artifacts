"""Command line for the RBC comparator (``paper1.fgate.rbc``, unchanged from the registered
file). Same call as the project's scoring pipeline (``h1b rbc``) without its archive checks.

    python -m paper1.fgate.run_rbc --table TABLE.jsonl --pool POOL.json \
        --fgate FGATE-REPORT.json --out RBC.json [--md RBC.md]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from paper1 import _io
from paper1.fgate import pool as fp
from paper1.fgate import rbc as R


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m paper1.fgate.run_rbc")
    ap.add_argument("--table", type=Path, required=True)
    ap.add_argument("--pool", type=Path, required=True)
    ap.add_argument("--fgate", type=Path, required=True, help="the F' report of this table")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--md", type=Path)
    args = ap.parse_args(argv)
    pool = fp.verify_pool(_io.read_json(args.pool))
    fg = _io.read_json(args.fgate)
    if fg.get("pool_sha256") != pool["sha256"]:
        print("refused: the F' report was fitted on another pool", file=sys.stderr)
        return 2
    try:
        rep = R.rbc(_io.read_jsonl(args.table), pool["lessons"], fgate=fg)
    except R.Refused as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    _io.write_json(args.out, rep)
    if args.md:
        args.md.write_text(R.render(rep), encoding="utf-8")
    print(json.dumps({"selected": rep.get("selected")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
