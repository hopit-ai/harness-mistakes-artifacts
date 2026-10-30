"""Audited sensitivity of F' on the BFCL gate (docs/xp/bfcl-plan.md s. 6.4 "Analyses").

    python -m paper1.bfcl.audited sensitivity --table TABLE-U.jsonl \
        --pool docs/xp/bfcl-learned/POOL-U.json --primary FPRIME-U.json --out AUDITED-U.json

**Audited sensitivity -- not used for selection.** Official scoring stays primary: L*
(FPRIME), the SEARCH subset and every frozen library come from the primary F' report of
``python -m paper1.bfcl.fprime analyse`` alone. This module never writes, edits or feeds
that report: it reads the same analysis table (``fprime table``), removes the rows of the
**defective** gate instances of the frozen defect list, and refits with the registered
``fprime.analyse`` unchanged. Its output is a separate file with its own schema, a
``use`` label, no top-level ``advanced`` key, and it refuses to overwrite a primary report
or any of its inputs.

- **Frozen list**: ``docs/xp/bfcl-audit/gate-defects.json``; its SHA-256 must equal the
  ``defect_list_sha256`` of the registry row ``bfcl_audit_freeze_gate``
  (``learner_runs/REGISTRY.jsonl``, hash chain verified). Defective = ``score_changing``
  yes **and** ``severity`` clear (rubric v2); the ``defects`` list must equal that rule
  recomputed over the frozen ``labels`` of the gate role.
- **Refit**: every row (anchor and draws) of a defective instance is dropped; a root with
  both instances defective therefore drops out. Same seeds, draws and rules as the primary
  (``fprime.RULES``, ``RD_PRIOR_SD``); the registered sensitivities are not rerun.
- **Weighting** (clarification of 2026-10-22, plan s. 6.4, before any F' output existed):
  the registered estimator is used unchanged (no new estimator). It weights the domain
  families equally and the instances equally within a family
  (``slh.xp.fgate.analysis``, the standardized risk difference). In the primary every root
  has both instances, so this equals equal root weighting within family; after the
  exclusions a root that keeps one instance carries half the weight of a root that keeps
  both. Recorded in the output's ``weighting`` field.
- **Exposure (design only)**: E2 needs ``min_exposure`` (64) included-lesson episodes in
  every family. After the drop, pool U's minimum exposure is exactly 64 (files, travel,
  vehicle), so one missing row there fails E2; pool S (14 draws) falls to 28, so every S
  lesson fails E2 in the sensitivity by construction (its gate outcome is uninformative;
  its estimates are still reported). The output lists each lesson's per-family exposure.
- **Table tie**: the output records the table's SHA-256; ``--primary`` must be the primary
  report of this pool fitted on this table (its row and instance counts equal the
  table's, and any table hash it records equals it), else refused.
- **Reported**: per lesson, the primary's and the refit's estimates and gate outcome side
  by side (when ``--primary`` is given), the refit's advanced set as a descriptive field,
  and, descriptively, success on the defective instances alone per arm (B1 anchor; the
  pool's F' draws).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from paper1 import DATA

SCHEMA = "xp-bfcl-fprime-audited-sensitivity-v1"
USE = "audited sensitivity — not used for selection"
DEFECTS = DATA / "bfcl-audit" / "gate-defects.json"
REGISTRY_DIR = DATA / "registry"
FREEZE_EVENT = "bfcl_audit_freeze_gate"
WEIGHTING = ("registered fprime.analyse estimator unchanged: families weighted equally, "
             "instances equally within family; equals equal roots in the primary (every root "
             "has both instances); after exclusions a root keeping one instance carries half "
             "the weight of a root keeping both (plan s. 6.4 clarification 2026-10-22)")
LESSON_FIELDS = ("rd_mean", "rd_ci90", "p_rd_gt_delta", "p_rd_gt_0", "harm_rd_mean",
                 "p_harm_gt_delta", "checks", "passes")


class Refused(RuntimeError):
    pass


def is_defective(label: dict[str, Any]) -> bool:
    return label.get("score_changing") == "yes" and label.get("severity") == "clear"


def load_defects(path: Path = DEFECTS, registry_dir: Path | None = REGISTRY_DIR,
                 expected_sha256: str | None = None, *, part: str = "gate") -> dict[str, Any]:
    """The frozen defect list of ``part`` (gate, or test for the H3 confirmation), checked
    against its registry row ``bfcl_audit_freeze_<part>`` (or ``expected_sha256`` for
    tests); returns ids of defective instances and dropped roots."""
    if part not in ("gate", "test"):
        raise Refused(f"part {part!r}")
    event = FREEZE_EVENT if part == "gate" else f"bfcl_audit_freeze_{part}"
    raw = Path(path).read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if expected_sha256 is None:
        # Public release: the registry rows are the shipped verbatim subset (paper1.registry);
        # the shipped defect lists are redacted copies (reviewer file names in
        # ``inputs_sha256`` replaced), bound to the frozen file's hash by REDACTION.json.
        from paper1 import registry as REG

        rows = [r for r in REG.shipped_rows(Path(registry_dir)) if r.get("event") == event]
        if len(rows) != 1:
            raise Refused(f"registry: {len(rows)} {event} rows (want exactly 1)")
        expected_sha256 = rows[0]["defect_list_sha256"]
        if sha != expected_sha256:
            expected_sha256 = REG.redacted_copy_sha256(Path(path), expected_sha256)
    if sha != expected_sha256:
        raise Refused(f"{path}: sha256 {sha[:12]}… differs from the frozen "
                      f"{expected_sha256[:12]}…")
    doc = json.loads(raw)
    if doc.get("part") != part or doc.get("rubric") != "v2":
        raise Refused(f"defect list is not the {part} part under rubric v2")
    listed = {d["instance"] for d in doc["defects"]}
    if not all(is_defective(d) for d in doc["defects"]):
        raise Refused("defect list holds an entry that is not score-changing and clear")
    recomputed = {lab["instance"] for lab in doc.get("labels", [])
                  if lab.get("role", part) == part and is_defective(lab)}
    if doc.get("labels") is not None and recomputed != listed:
        raise Refused("defect list differs from the rule recomputed over its labels")
    roots: dict[int, int] = {}
    for d in doc["defects"]:
        roots[d["root"]] = roots.get(d["root"], 0) + 1
    return {"sha256": sha, "instances": sorted(listed),
            "roots_dropped": sorted(r for r, n in roots.items() if n >= 2)}


def _rate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    return {"episodes": n, "instances": len({r["case_id"] for r in rows}),
            "success": (sum(r["y"] for r in rows) / n) if n else None}


def sensitivity(rows: list[dict[str, Any]], pool: dict[str, Any], defects: dict[str, Any],
                *, primary: dict[str, Any] | None = None, n_draws: int = 1000,
                seed: int = 0) -> dict[str, Any]:
    from paper1.bfcl import fprime as F

    bad = set(defects["instances"])
    kept = [dict(r) for r in rows if r["case_id"] not in bad]   # copies: inputs untouched
    on_defective = [r for r in rows if r["case_id"] in bad]
    if not kept:
        raise Refused("no non-defective instance left")
    refit = F.analyse(kept, pool, n_draws=n_draws, seed=seed, sensitivities=False)
    lessons: dict[str, Any] = {}
    prim = {p["id"]: p for p in (primary or {}).get("gate", {}).get("lessons", [])}
    for p in refit["gate"]["lessons"]:
        lessons[p["id"]] = {"audited": {k: p.get(k) for k in LESSON_FIELDS},
                            "audited_exposure_by_family": {
                                ctx: v.get("exposure")
                                for ctx, v in (p.get("rd_by_context") or {}).items()}}
        if p["id"] in prim:
            lessons[p["id"]]["primary"] = {k: prim[p["id"]].get(k) for k in LESSON_FIELDS}
    anchors = [r for r in on_defective if set(r["x"]) <= {"0"}]
    draws = [r for r in on_defective if not set(r["x"]) <= {"0"}]
    return {
        "schema": SCHEMA, "use": USE, "pool": pool["pool"], "pool_sha256": pool["sha256"],
        "defect_list_sha256": defects["sha256"],
        "definition": "defective = score_changing yes AND severity clear (rubric v2)",
        "dropped": {"instances": sorted({r["case_id"] for r in on_defective}),
                    "roots_with_both_instances": defects["roots_dropped"],
                    "rows": len(on_defective)},
        "weighting": WEIGHTING,
        "refit": {"rows": len(kept), "instances": refit["instances"],
                  "contexts": refit["contexts"], "anchors": refit["anchors"],
                  "rules": refit["gate"]["rules"],
                  "advanced_descriptive": refit["gate"]["advanced"],
                  "shortlist_descriptive": refit["gate"]["shortlist"]},
        "primary": None if primary is None else {
            "schema": primary.get("schema"), "advanced": primary.get("advanced"),
            "rows": primary.get("rows"), "instances": primary.get("instances")},
        "lessons": lessons,
        "defective_only_descriptive": {"B1_anchor": _rate(anchors),
                                       f"draws_pool_{pool['pool']}": _rate(draws)},
    }


def table_sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_primary(primary: dict[str, Any], pool: dict[str, Any], rows: list[dict[str, Any]],
                  table_sha: str) -> None:
    """``primary`` must be the primary F' report of ``pool`` fitted on this table."""
    from paper1.bfcl import fprime as F

    if primary.get("schema") != F.REPORT_SCHEMA or primary.get("pool_sha256") != pool["sha256"]:
        raise Refused("--primary is not the primary F' report of this pool")
    if primary.get("rows") != len(rows) or \
            primary.get("instances") != len({r["case_id"] for r in rows}):
        raise Refused(f"--primary was fitted on {primary.get('rows')} rows / "
                      f"{primary.get('instances')} instances, the table has {len(rows)} / "
                      f"{len({r['case_id'] for r in rows})}")
    recorded = primary.get("table_sha256")
    if recorded is not None and recorded != table_sha:
        raise Refused("--primary records another table's sha256")


def _guard_out(out: Path, inputs: list[Path]) -> None:
    out = Path(out).resolve()
    if any(out == Path(p).resolve() for p in inputs if p):
        raise Refused(f"{out}: is an input; write the sensitivity to its own file")
    if out.exists():
        try:
            schema = json.loads(out.read_text()).get("schema")
        except (ValueError, AttributeError):
            schema = None
        if schema != SCHEMA:
            raise Refused(f"{out}: exists and is not an audited-sensitivity file "
                          f"(schema {schema!r}; a primary F' report is never overwritten)")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m paper1.bfcl.audited")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sensitivity")
    s.add_argument("--table", type=Path, required=True)
    s.add_argument("--pool", type=Path, required=True)
    s.add_argument("--primary", type=Path)
    s.add_argument("--defects", type=Path, default=DEFECTS)
    s.add_argument("--out", type=Path, required=True)
    s.add_argument("--draws", type=int, default=1000)
    args = ap.parse_args(argv)
    from paper1.bfcl import plan_min as P

    try:
        _guard_out(args.out, [args.table, args.pool, args.primary, args.defects])
        pool = P.verify_pool(json.loads(args.pool.read_text()))
        rows = [json.loads(x) for x in args.table.read_text().splitlines() if x.strip()]
        tsha = table_sha256(args.table)
        primary = None
        if args.primary:
            primary = json.loads(args.primary.read_text())
            check_primary(primary, pool, rows, tsha)
        rep = sensitivity(rows, pool, load_defects(args.defects), primary=primary,
                          n_draws=args.draws)
        rep["table_sha256"] = tsha
        args.out.write_text(json.dumps(rep, indent=1, default=float))
        print(json.dumps({"use": USE, "out": str(args.out), "rows": rep["refit"]["rows"],
                          "dropped_rows": rep["dropped"]["rows"]}))
        return 0
    except Refused as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    sys.exit(main())
