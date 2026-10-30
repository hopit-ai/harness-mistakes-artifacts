"""F' on complete BFCL episodes: randomized lesson inclusion on the gate split.

    python -m paper1.bfcl.fprime table   --package PKG-H2 --export EXPORT-H2 --pool U --out TABLE-U.jsonl
    python -m paper1.bfcl.fprime analyse --table TABLE-U.jsonl --pool POOL-U.json --out FPRIME-U.json
    python -m paper1.bfcl.fprime simulate --reps 10 [--draws 32] [--out SIM.json]   # light

Design (pre-specified). Population: the 30 gate roots x {base, long_context} = 60
instances. Per instance: one **empty-library anchor** (the official B1 conversation,
shared by both pools) and ``draws`` (32; ``plan.FPRIME_DRAWS``) randomized inclusion vectors over the pool's
2..8 lessons in antithetic pairs (each lesson in exactly half of the draws of every
instance; no empty or full vector; ``slh.xp.fgate.design.inclusion_vectors`` with the
salt ``bfcl-fprime-<pool>-v1``). Included lessons render in canonical order as one
``## Lessons`` system note (``slh.xp.fgate.pool.render``). Each unit is one full
episode scored by the official checker.

Outcomes per episode (``slh.xp.bfcl.traces.outcome``): ``y`` = official success,
``harm`` = first failure is a backend state mismatch (wrong write), ``reask`` = a turn
with no executable call where the answer has one (inaction; reported, not gated).

Analysis: ``slh.xp.fgate.analysis`` unchanged (prefix = instance intercepts partially
pooled within context; context = the root's domain **family**: files, vehicle,
finance, travel; lesson x family deviations shrunk with one shared tau; pairwise
interactions strongly shrunk; empirical-Bayes grid; posterior-standardized risk
differences; gate E1-E4; joint choice over a shortlist of at most 4). One BFCL rule
differs: ``min_exposure`` = 64 episodes per family (the gate split has 6-9 roots per
family, i.e. 96-144 exposures per lesson; 100 would fail the vehicle family by design).
Sensitivities: prior x2, sampled-context weights, error rows removed, every grid point,
and base-only / long-context-only refits (descriptive). The sequencing exception of the
decision screen does not apply (episodes already contain the sequence).

The advanced subset is L* (the FPRIME arm for pool U, the SEARCH arm for pool S); an
empty advanced set means the arm is B1 itself, a reportable null.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

from paper1.bfcl import data
from paper1.fgate import analysis as A

RULES = {**A.RULES, "min_exposure": 64}
# Prior SD of a lesson's risk difference near the anchors' baseline (decision screen: 3
# points). Episodes: 5 points, set from the simulation of 2026-10-18 (docs/xp/bfcl-plan.md
# s. 5.4) before any BFCL data exist.
RD_PRIOR_SD = 0.05
REPORT_SCHEMA = "xp-bfcl-fprime-report-v1"


def salt(pool_name: str) -> str:
    return f"bfcl-fprime-{pool_name}-v1"


def design(pool: dict[str, Any], instances: list[str], *, draws: int) -> list[dict[str, Any]]:
    """Units (instance, draw 1..draws, x bits, notes); the anchor (draw 0) is shared."""
    from paper1.fgate import design as D
    from paper1.fgate import pool as fp

    lessons = pool["lessons"]
    out = []
    for inst in instances:
        vecs = D.inclusion_vectors(inst, len(lessons), draws, salt=salt(pool["pool"]))
        for d, x in enumerate(vecs):
            if d == 0:
                continue
            out.append({"instance": inst, "draw": d, "x": D.bits(x),
                        "notes": fp.render(lessons, x)})
    return out


def table(plan: dict[str, Any], outcomes: dict[tuple[str, str], dict[str, Any]], pool_name: str
          ) -> list[dict[str, Any]]:
    """Analysis rows for one pool: anchors (x = all zero) and that pool's draws.
    ``outcomes``: (cell_id, instance) -> outcome row (``traces.outcome`` fields)."""
    pool = plan["pools"][pool_name]
    n = len(pool["lessons"])
    rows = []
    for cell in plan["cells"]:
        if cell["purpose"] == "fprime-anchor":
            mine = True
        else:
            mine = cell["cell_id"].startswith(f"h2-gate-{pool_name}-")
        if not mine:
            continue
        for u in cell["units"]:
            o = outcomes.get((cell["cell_id"], u["instance"]))
            if o is None:
                continue
            root, cat = data.parse_instance(u["instance"])
            rows.append({"track": "fgate", "case_id": u["instance"], "root": root,
                         "category": cat, "context": _family(root),
                         "x": u.get("x") or "0" * n, "y": int(o["success"]),
                         "harm": int(o["harm"]), "reask": int(o["inaction"]),
                         "error_class": "inference_error" if o["inference_error"] else None,
                         "cell_id": cell["cell_id"]})
    return rows


_FAMILY: dict[int, str] = {}


def _family(root: int) -> str:
    if not _FAMILY:
        for r in data.roots():
            _FAMILY[r["root"]] = r["family"]
    return _FAMILY[root]


def analyse(rows: list[dict[str, Any]], pool: dict[str, Any], *, n_draws: int = 1000,
            seed: int = 0, sensitivities: bool = True) -> dict[str, Any]:
    lessons = pool["lessons"]
    succ = A.fit_outcome(rows, "y", lessons, n_draws=n_draws, seed=seed,
                         rd_prior_sd=RD_PRIOR_SD)
    harm = A.fit_outcome(rows, "harm", lessons, n_draws=n_draws, seed=seed + 1,
                         rd_prior_sd=RD_PRIOR_SD)
    reask = A.fit_outcome(rows, "reask", lessons, n_draws=n_draws, seed=seed + 2,
                          rd_prior_sd=RD_PRIOR_SD)
    g = A.gate(succ, harm, lessons, RULES)
    g["sequencing_candidate"] = None  # not used on episodes
    d = succ["design"]
    anchors = {c: {"n": int(((d.c == i) & d.anchor).sum()),
                   "success": float(d.y[(d.c == i) & d.anchor].mean())
                   if ((d.c == i) & d.anchor).any() else None}
               for i, c in enumerate(d.contexts)}
    rep: dict[str, Any] = {
        "schema": REPORT_SCHEMA, "pool": pool["pool"], "pool_sha256": pool["sha256"],
        "rows": len(rows), "instances": d.n_prefix, "contexts": d.contexts,
        "anchors": anchors, "error_rows": sum(1 for r in rows if r.get("error_class")),
        "s_b": succ["s_b"], "eb_grid": succ["grid"],
        "chosen": {"s_a": succ["fit"]["s_a"], "tau": succ["fit"]["tau"]}, "gate": g,
        "advanced": g["advanced"],
        "reask": {les["id"]: {"rd_mean": float(reask["rd"][:, k].mean())}
                  for k, les in enumerate(lessons)}}
    if sensitivities:
        sens: dict[str, Any] = {}
        for name, kw in (("prior_x2", {"prior_mult": 2.0}),
                         ("weights_sampled", {"weights": "sampled"})):
            s2 = A.fit_outcome(rows, "y", lessons, n_draws=n_draws, seed=seed,
                                rd_prior_sd=RD_PRIOR_SD, **kw)
            h2 = A.fit_outcome(rows, "harm", lessons, n_draws=n_draws, seed=seed + 1,
                                rd_prior_sd=RD_PRIOR_SD, **kw)
            sens[name] = {"advanced": A.gate(s2, h2, lessons, RULES)["advanced"]}
        clean = [r for r in rows if not r.get("error_class")]
        if len(clean) != len(rows):
            s3 = A.fit_outcome(clean, "y", lessons, n_draws=n_draws, seed=seed,
                                rd_prior_sd=RD_PRIOR_SD)
            h3 = A.fit_outcome(clean, "harm", lessons, n_draws=n_draws, seed=seed + 1,
                                rd_prior_sd=RD_PRIOR_SD)
            sens["without_error_rows"] = {"advanced": A.gate(s3, h3, lessons, RULES)["advanced"]}
        for cat in data.PRIMARY:
            sub = [r for r in rows if r["category"] == cat]
            if len({r["case_id"] for r in sub}) >= 4:
                s4 = A.fit_outcome(sub, "y", lessons, n_draws=n_draws, seed=seed, eb=False,
                                    rd_prior_sd=RD_PRIOR_SD)
                sens[f"only_{cat}"] = {"rd_mean": [round(float(s4["rd"][:, k].mean()), 4)
                                                   for k in range(len(lessons))]}
        rep["sensitivity"] = sens
    return rep


# --------------------------------------------------------------------------- simulation


def simulate_once(scenario: str, *, families: dict[str, int], n_lessons: int, draws: int,
                  base: float = 0.5, het_sd: float = 0.3, base_sd: float = 1.5,
                  seed: int = 0, n_draws: int = 300, rd_prior_sd: float = RD_PRIOR_SD
                  ) -> dict[str, Any]:
    """The complete F' procedure on simulated episodes (``fgate.simulate``'s generator,
    BFCL design: instances per family, one anchor, ``draws`` antithetic vectors)."""
    from paper1.fgate import simulate as S

    rng = np.random.default_rng(seed)
    rows, x, _ctx = S._design_rows(families, n_lessons, draws, rng)
    pids = np.array([r["case_id"] for r in rows])
    uniq, pidx = np.unique(pids, return_inverse=True)
    a = S._logit(base) + rng.normal(0, base_sd, len(uniq))
    het = rng.normal(0, het_sd, (len(uniq), n_lessons))
    a_h = S._logit(0.25) + rng.normal(0, 1.0, len(uniq))
    eff = np.zeros(n_lessons)
    heff = np.zeros(n_lessons)
    targets = {"null": {}, "power": {0: 0.06, 1: 0.04, 2: 0.02},
               "harmful": {0: 0.04}}[scenario]
    for lesson, t in targets.items():
        eff[lesson] = S._calibrate(a, t, het[:, lesson])
    if scenario == "harmful":
        heff[0] = S._calibrate(a_h, 0.04, np.zeros(len(uniq)))
    eta = a[pidx] + (x * (eff + het[pidx])).sum(1)
    eta_h = a_h[pidx] + (x * heff).sum(1)
    y = (rng.random(len(rows)) < A._sigmoid(eta)).astype(int)
    h = (rng.random(len(rows)) < A._sigmoid(eta_h)).astype(int)
    for r, yy, hh in zip(rows, y, h, strict=True):
        r["y"], r["harm"] = int(yy), int(hh)
    lessons = [{"id": f"L{k + 1:02d}", "intent": "bfcl", "tools": ["any"]}
               for k in range(n_lessons)]
    succ = A.fit_outcome(rows, "y", lessons, n_draws=n_draws, seed=seed, eb=False,
                         rd_prior_sd=rd_prior_sd)
    harm = A.fit_outcome(rows, "harm", lessons, n_draws=n_draws, seed=seed + 1, eb=False,
                         rd_prior_sd=rd_prior_sd)
    g = A.gate(succ, harm, lessons, RULES)
    return {"scenario": scenario, "advanced": g["advanced"],
            "passes": [p["id"] for p in g["lessons"] if p["passes"]],
            "rd_mean": [round(p["rd_mean"], 4) for p in g["lessons"]],
            "rd_ci90_width": [round(p["rd_ci90"][1] - p["rd_ci90"][0], 4) for p in g["lessons"]]}


def gate_families(man: dict[str, Any]) -> dict[str, int]:
    fam = {r["root"]: r["family"] for r in man["roots"]}
    out: dict[str, int] = {}
    for root in man["roles"]["gate"]:
        out[fam[root]] = out.get(fam[root], 0) + len(data.PRIMARY)
    return dict(sorted(out.items()))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m paper1.bfcl.fprime")
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("table")
    t.add_argument("--package", type=Path, required=True)
    t.add_argument("--export", type=Path, required=True)
    t.add_argument("--pool", required=True, choices=("U", "S"))
    t.add_argument("--out", type=Path, required=True)
    a = sub.add_parser("analyse")
    a.add_argument("--table", type=Path, required=True)
    a.add_argument("--pool", type=Path, required=True)
    a.add_argument("--out", type=Path, required=True)
    a.add_argument("--draws", type=int, default=1000)
    s = sub.add_parser("simulate")
    s.add_argument("--reps", type=int, default=10)
    s.add_argument("--draws", type=int, default=32)
    s.add_argument("--lessons", type=int, default=8)
    s.add_argument("--scenarios", default="null,power,harmful")
    s.add_argument("--rd-prior-sd", type=float, default=RD_PRIOR_SD)
    s.add_argument("--out", type=Path)
    args = ap.parse_args(argv)
    if args.cmd == "table":
        from paper1.bfcl import plan_min as P
        from slh.xp.bfcl import runner as R  # public kit (hopit-ai/self-learning-harness-kit), only to read raw hand-off files

        pkg = P.check_seal(json.loads((args.package / "plan.json").read_text()), "plan")
        outcomes = R.read_outcomes(args.export)
        rows = table(pkg, outcomes, args.pool)
        with args.out.open("w") as f:
            for r in rows:
                f.write(json.dumps(r, sort_keys=True) + "\n")
        print(json.dumps({"rows": len(rows)}))
        return 0
    if args.cmd == "analyse":
        from paper1.bfcl import plan_min as P

        pool = P.verify_pool(json.loads(args.pool.read_text()))
        rows = [json.loads(line) for line in args.table.read_text().splitlines() if line]
        rep = analyse(rows, pool, n_draws=args.draws)
        args.out.write_text(json.dumps(rep, indent=1, default=float))
        print(json.dumps({"advanced": rep["advanced"]}))
        return 0
    from slh.xp.bfcl import splits  # public kit (hopit-ai/self-learning-harness-kit), only to read raw hand-off files

    fams = gate_families(splits.load(recompute=False))
    t0 = time.time()
    res = []
    for k, sc in enumerate(args.scenarios.split(",")):
        for rep in range(args.reps):
            res.append(simulate_once(sc, families=fams, n_lessons=args.lessons,
                                     draws=args.draws, seed=1000 * rep + k,
                                     rd_prior_sd=args.rd_prior_sd))
    summ = {}
    for sc in args.scenarios.split(","):
        rs = [r for r in res if r["scenario"] == sc]
        summ[sc] = {"reps": len(rs),
                    "p_any_advanced": sum(bool(r["advanced"]) for r in rs) / len(rs),
                    "p_advanced": {f"L{k + 1:02d}": sum(f"L{k + 1:02d}" in r["advanced"]
                                                       for r in rs) / len(rs)
                                   for k in range(3)},
                    "mean_rd": [round(float(v), 4) for v in
                                np.mean([r["rd_mean"] for r in rs], 0)[:3]],
                    "mean_ci90_width": round(float(np.mean([r["rd_ci90_width"] for r in rs])), 4)}
    out = {"families": fams, "draws": args.draws, "rd_prior_sd": args.rd_prior_sd, "lessons": args.lessons,
           "episodes": sum(fams.values()) * (args.draws + 1), "wall_s": round(time.time() - t0, 1),
           "scenarios": summ}
    if args.out:
        args.out.write_text(json.dumps({"summary": out, "results": res}, indent=1))
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
