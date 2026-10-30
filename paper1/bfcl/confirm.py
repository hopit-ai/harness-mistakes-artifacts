"""Our side: the pre-specified confirmation analysis on the sealed test split (hand-off 3).

    python -m paper1.bfcl.confirm --package PKG-H3 --export EXPORT-H3 --out CONFIRM.json

Data: 120 test roots x {base, long_context} x 4 trials x 7 arms, every library frozen
before H3 was built; outcome = official success. An arm whose frozen selection is empty
(F' or search selected nothing) **is** B1: its episodes are B1's and its contrast with
B1 is zero by construction (reported, not run twice).

Estimand per arm: success rate with roots weighted equally (mean over roots of the
root's mean over its 2 categories x 4 trials). Contrasts are paired by root.

Primary (family of three, Holm-adjusted at two-sided alpha = 0.05):
  P1  FPRIME - B1        (does the selected library beat the standard harness?)
  P2  FPRIME - SEARCH    (evidence vs matched-budget no-evidence search)
  P3  FPRIME - UNGATED   (value of selection)
Secondary, descriptive (95% intervals, no multiplicity claim): every other arm vs B1
(B1P, PERSON, UNGATED, SEARCH, MEMORY), FPRIME vs MEMORY and vs PERSON, pass^4 (all four
trials of an instance succeed) for every arm, base and long-context separately, and the
harm rate (state mismatch) per arm.

**Empty L* (plan s. 0, deviation B-D9, PROPOSED 2026-10-22, owner approval pending).**
As registered, an empty FPRIME makes P1 zero by construction (p = 1, never significant;
"learning beats the standard harness" fails: a reportable null at the gate), P2 becomes
B1 - SEARCH and P3 B1 - UNGATED, Holm over the three. That family is always reported
(``registered_family``; P3 only when UNGATED was run). A package built with the B-D9 arms
(``plan.json`` ``design.deviation == "B-D9"``) adds the proposed primary, a family of one:
**Q1 SEARCH - B1** (the gate winner S01 against the standard harness), two-sided 0.05, same
estimand, bootstrap and test; UNGATED - B1 is descriptive.

**Audited sensitivity** (plan s. 6.4; ``--defects``, the frozen test list): the same
contrasts with every defective instance (score-changing and clear) removed; a root with
both instances defective drops out; remaining roots weighted equally. Reported beside the
official primary, never instead of it; plus per-arm success on defective instances alone.

    python -m paper1.bfcl.confirm --package PKG-H3 --export EXPORT-H3 \
        --defects docs/xp/bfcl-audit/test-defects.json \
        [--official-package PKG-H3-OFFICIAL --official-export EXPORT-H3-OFFICIAL] --out CONFIRM.json

Intervals: cluster bootstrap over roots (10,000 resamples, seed 20261018), percentile
95%; p-values from the paired root-level t statistic (two-sided), Holm across P1-P3.
"Learning beats the standard harness" is claimed only if P1 holds after Holm; P2 and P3
qualify the claim. A +3-6 point effect is below the design's minimum detectable effect
under official decoding (docs/xp/bfcl-plan.md s. 6.3): an inconclusive result is
reported as such.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

from paper1.bfcl import data

PRIMARY = (("FPRIME", "B1"), ("FPRIME", "SEARCH"), ("FPRIME", "UNGATED"))
SECONDARY = (("B1P", "B1"), ("PERSON", "B1"), ("UNGATED", "B1"), ("SEARCH", "B1"),
             ("MEMORY", "B1"), ("FPRIME", "MEMORY"), ("FPRIME", "PERSON"))
PRIMARY_BD9 = (("SEARCH", "B1"),)
DESCRIPTIVE_BD9 = (("UNGATED", "B1"),)
AUDITED_USE = "audited sensitivity — reported beside the official primary, never instead"
BOOT = 10_000
SEED = 20261018


def root_means(rows: list[dict[str, Any]], arm: str, *, field: str = "success",
               category: str | None = None) -> dict[int, float]:
    acc: dict[int, list[float]] = {}
    for r in rows:
        if r["arm"] != arm or (category and r["category"] != category):
            continue
        acc.setdefault(r["root"], []).append(float(r[field]))
    return {k: float(np.mean(v)) for k, v in acc.items()}


def pass_k(rows: list[dict[str, Any]], arm: str, k: int) -> float | None:
    by: dict[str, list[int]] = {}
    for r in rows:
        if r["arm"] == arm:
            by.setdefault(r["instance"], []).append(int(r["success"]))
    vals = [all(v) for v in by.values() if len(v) >= k]
    return float(np.mean(vals)) if vals else None


def _t_p(d: np.ndarray) -> float:
    n = len(d)
    sd = d.std(ddof=1) if n > 1 else 0.0
    if sd == 0:
        return 1.0 if d.mean() == 0 else 0.0
    t = d.mean() / (sd / math.sqrt(n))
    # normal approximation to the t distribution (n = 120 roots)
    return float(math.erfc(abs(t) / math.sqrt(2)))


def contrast(rows: list[dict[str, Any]], a: str, b: str, *, rng: np.random.Generator,
             category: str | None = None) -> dict[str, Any]:
    ma, mb = root_means(rows, a, category=category), root_means(rows, b, category=category)
    roots = sorted(set(ma) & set(mb))
    if not roots:
        return {"a": a, "b": b, "roots": 0}
    d = np.array([ma[r] - mb[r] for r in roots])
    idx = rng.integers(0, len(d), (BOOT, len(d)))
    boots = d[idx].mean(1)
    return {"a": a, "b": b, "roots": len(roots), "diff": float(d.mean()),
            "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))],
            "p": _t_p(d)}


def holm(ps: list[float]) -> list[float]:
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj = [0.0] * len(ps)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = running
    return adj


def expand_empty_arms(rows: list[dict[str, Any]], empty_arms: list[str]) -> list[dict[str, Any]]:
    """An empty selection is B1: copy B1's episodes under that arm's name."""
    b1 = [r for r in rows if r["arm"] == "B1"]
    return rows + [{**r, "arm": arm, "copied_from_b1": True} for arm in empty_arms for r in b1]


def _family(rows: list[dict[str, Any]], pairs: tuple[tuple[str, str], ...],
            rng: np.random.Generator | None = None) -> list[dict[str, Any]]:
    """Contrasts of one family, Holm across the family (``rng``: default a fresh generator
    at SEED). A contrast with no data (arm not run, or no roots left) is flagged and gets p = 1."""
    rng = rng if rng is not None else np.random.default_rng(SEED)
    fam = [contrast(rows, a, b, rng=rng) for a, b in pairs]
    adj = holm([c.get("p", 1.0) for c in fam])
    for c, p in zip(fam, adj, strict=True):
        if not c["roots"]:
            c["no_data"] = True  # arm not run, or no roots left
        c["p_holm"] = p
        c["significant"] = bool(c["roots"]) and p < 0.05
    return fam


def _per_arm(rows: list[dict[str, Any]]) -> dict[str, Any]:
    per_arm = {}
    for arm in sorted({r["arm"] for r in rows}):
        rm = root_means(rows, arm)
        hm = root_means(rows, arm, field="harm")
        per_arm[arm] = {"success": float(np.mean(list(rm.values()))) if rm else None,
                        "harm": float(np.mean(list(hm.values()))) if hm else None,
                        "pass^4": pass_k(rows, arm, 4), "roots": len(rm),
                        "episodes": sum(1 for r in rows if r["arm"] == arm)}
    return per_arm


def analyse(rows: list[dict[str, Any]], *, empty_arms: list[str] = (),
            design: str = "registered") -> dict[str, Any]:
    if design not in ("registered", "B-D9"):
        raise ValueError(f"design {design!r}")
    keys: dict[str, set[tuple[str, int]]] = {}
    for r in rows:
        keys.setdefault(r["arm"], set()).add((r["instance"], r["trial"]))
    if len({frozenset(v) for v in keys.values()}) > 1:  # contrasts must pair observations
        raise ValueError(f"{INCOMPLETE}: arms cover different (instance, trial) sets")
    rows = expand_empty_arms(rows, list(empty_arms))
    rng = np.random.default_rng(SEED)
    prim = _family(rows, PRIMARY, rng)  # the registered generator sequence, unchanged
    sec = [contrast(rows, a, b, rng=rng) for a, b in SECONDARY]
    by_cat = {cat: [contrast(rows, a, b, rng=rng, category=cat) for a, b in PRIMARY]
              for cat in data.PRIMARY}
    rep: dict[str, Any] = {
        "schema": "xp-bfcl-confirm-v1", "design": design, "arms": _per_arm(rows),
        "registered_family": prim, "primary": prim, "secondary": sec,
        "by_category": by_cat, "empty_arms": list(empty_arms),
        "claim_p1": bool(prim[0].get("significant") and prim[0]["diff"] > 0)}
    if "FPRIME" in empty_arms:
        rep["registered_note"] = ("L* empty: FPRIME is B1, P1 = 0 by construction (p = 1), "
                                  "P2 = B1 - SEARCH, P3 = B1 - UNGATED (plan s. 5, s. 6.1)")
    if design == "B-D9":
        q = _family(rows, PRIMARY_BD9)
        rep["primary"] = q
        rep["descriptive_bd9"] = [contrast(rows, a, b, rng=rng) for a, b in DESCRIPTIVE_BD9]
        rep["by_category_bd9"] = {cat: [contrast(rows, a, b, rng=rng, category=cat)
                                        for a, b in PRIMARY_BD9 + DESCRIPTIVE_BD9]
                                  for cat in data.PRIMARY}
        rep["claim_q1"] = bool(q[0]["significant"] and q[0]["diff"] > 0)
    return rep


def audited(rows: list[dict[str, Any]], defects: dict[str, Any], *,
            empty_arms: list[str] = (), design: str = "registered") -> dict[str, Any]:
    """The same analysis on the non-defective instances (plan s. 6.4), and per-arm success
    on the defective instances alone (descriptive)."""
    bad = set(defects["instances"])
    kept = [r for r in rows if r["instance"] not in bad]
    rep = analyse(kept, empty_arms=empty_arms, design=design)
    on_bad = expand_empty_arms([r for r in rows if r["instance"] in bad], list(empty_arms))
    return {"use": AUDITED_USE, "defect_list_sha256": defects["sha256"],
            "definition": "defective = score_changing yes AND severity clear (rubric v2)",
            "instances_dropped": len(bad & {r["instance"] for r in rows}),
            "roots_dropped": defects["roots_dropped"],
            "weighting": "remaining roots weighted equally (a root keeping one instance "
                         "counts as one root)",
            "primary": rep["primary"], "registered_family": rep["registered_family"],
            "secondary": rep["secondary"], "by_category": rep["by_category"],
            "arms": rep["arms"], "defective_only_descriptive": _per_arm(on_bad),
            **({k: rep[k] for k in ("descriptive_bd9", "by_category_bd9")}
               if design == "B-D9" else {})}


def official_row(rows_official: list[dict[str, Any]], rows: list[dict[str, Any]]
                 ) -> dict[str, Any]:
    """Descriptive: B1 at the official temperature (one trial) beside sampled B1."""
    rng = np.random.default_rng(SEED)
    both = [{**r, "arm": "B1-official"} for r in rows_official] + \
        [r for r in rows if r["arm"] == "B1"]
    return {"use": "descriptive comparability row (decision 1), not in any family",
            "arms": {k: v for k, v in _per_arm(both).items()},
            "B1_official_minus_B1_sampled": contrast(both, "B1-official", "B1", rng=rng)}


INCOMPLETE = "incomplete — confirmatory analysis not run"


def load_export(package: Path, export: Path) -> dict[str, Any]:
    """The sealed plan, the export's outcome rows and the **coverage gate**: the export
    belongs to this package (``manifest.json`` and ``run/identity.json`` carry the plan's
    seal, run mode ``full``) and holds every registered (cell, instance) of the plan
    exactly once with an outcome, and nothing else. ``problems`` empty = complete."""
    from paper1.bfcl import plan_min as P

    plan = P.check_seal(json.loads((Path(package) / "plan.json").read_text()), "plan")
    problems: list[str] = []
    man_p, ident_p = Path(export) / "manifest.json", Path(export) / "run" / "identity.json"
    man = json.loads(man_p.read_text()) if man_p.is_file() else None
    ident = json.loads(ident_p.read_text()) if ident_p.is_file() else None
    if man is None:
        problems.append("export manifest.json missing")
    else:
        if man.get("plan_sha256") != plan["sha256"]:
            problems.append("export manifest names another package seal")
        if man.get("handoff") != plan["handoff"]:
            problems.append(f"export is hand-off {man.get('handoff')!r}, not {plan['handoff']!r}")
        if man.get("halted_cells"):
            problems.append(f"halted cells {man['halted_cells']}")
        if man.get("identity") != ident:
            problems.append("manifest identity differs from run/identity.json")
    if ident is None:
        problems.append("run/identity.json missing")
    else:
        if ident.get("plan_sha256") != plan["sha256"]:
            problems.append("run identity names another package seal")
        if ident.get("mode") != "full":
            problems.append(f"run mode {ident.get('mode')!r}, not 'full'")
    cells = {c["cell_id"]: c for c in plan["cells"]}
    expected = {(c["cell_id"], u["instance"]) for c in plan["cells"] for u in c["units"]}
    seen: dict[tuple[str, str], int] = {}
    rows = []
    for path in sorted(Path(export).glob("cells/*/outcomes.jsonl")):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            o = json.loads(line)
            key = (o.get("cell_id"), o.get("instance"))
            seen[key] = seen.get(key, 0) + 1
            if key not in expected or seen[key] > 1:
                continue
            root, cat = data.parse_instance(key[1])
            rows.append({"arm": cells[key[0]]["arm"], "trial": cells[key[0]]["trial"],
                         "instance": key[1], "root": root, "category": cat,
                         "success": int(o["success"]), "harm": int(o["harm"])})
    missing = expected - set(seen)
    extra = set(seen) - expected
    dup = sorted(k for k, n in seen.items() if n > 1)
    if missing:
        problems.append(f"{len(missing)} of {len(expected)} registered episodes missing")
    if extra:
        problems.append(f"{len(extra)} outcomes not in the plan")
    if dup:
        problems.append(f"{len(dup)} episodes recorded more than once")
    counts: dict[str, int] = {}
    for c in plan["cells"]:
        counts[c["arm"]] = counts.get(c["arm"], 0) + sum(
            1 for u in c["units"] if (c["cell_id"], u["instance"]) in seen)
    return {"plan": plan, "rows": rows, "problems": problems,
            "descriptive_counts": {"registered_episodes": len(expected),
                                   "finished_by_arm": counts,
                                   "finished": len(set(seen) & expected)}}


def _rows(package: Path, export: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    got = load_export(package, export)
    if got["problems"]:
        raise ValueError(f"{INCOMPLETE}: " + "; ".join(got["problems"]))
    return got["plan"], got["rows"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m paper1.bfcl.confirm")
    ap.add_argument("--package", type=Path, required=True)
    ap.add_argument("--export", type=Path, required=True)
    ap.add_argument("--defects", type=Path,
                    help="frozen test defect list (audited sensitivity, plan s. 6.4)")
    ap.add_argument("--official-package", type=Path)
    ap.add_argument("--official-export", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    got = load_export(args.package, args.export)
    plan, rows = got["plan"], got["rows"]
    if plan["handoff"] != "h3":
        raise SystemExit("not an H3 package")
    if got["problems"]:  # no confirmatory output of any kind on partial coverage
        rep = {"schema": "xp-bfcl-confirm-v1", "status": INCOMPLETE,
               "problems": got["problems"], "package_sha256": plan["sha256"],
               "descriptive_counts": got["descriptive_counts"]}
        args.out.write_text(json.dumps(rep, indent=1))
        print(json.dumps({"status": INCOMPLETE, "problems": got["problems"]}))
        return 3
    design = "B-D9" if (plan.get("design") or {}).get("deviation") == "B-D9" else "registered"
    empty = plan.get("empty_arms") or []
    rep = analyse(rows, empty_arms=empty, design=design)
    rep["status"] = "complete"
    rep["package_sha256"] = plan["sha256"]
    defects = None
    if args.defects:
        from paper1.bfcl.audited import load_defects

        defects = load_defects(args.defects, part="test")
        rep["audited_sensitivity"] = audited(rows, defects, empty_arms=empty, design=design)
    if args.official_package and args.official_export:
        og = load_export(args.official_package, args.official_export)
        if og["plan"]["handoff"] != "h3-official":
            raise SystemExit("not an h3-official package")
        if og["problems"]:
            rep["official_decoding"] = {"status": INCOMPLETE, "problems": og["problems"],
                                        "descriptive_counts": og["descriptive_counts"]}
        else:
            rep["official_decoding"] = official_row(og["rows"], rows)
            if defects is not None:
                bad = set(defects["instances"])
                rep["audited_sensitivity"]["official_decoding"] = official_row(
                    [r for r in og["rows"] if r["instance"] not in bad],
                    [r for r in rows if r["instance"] not in bad])
    args.out.write_text(json.dumps(rep, indent=1))
    head = {"status": "complete", "design": design, "primary": rep["primary"]}
    if "audited_sensitivity" in rep:
        head["audited_primary"] = rep["audited_sensitivity"]["primary"]
    print(json.dumps(head))
    return 0


if __name__ == "__main__":
    sys.exit(main())
