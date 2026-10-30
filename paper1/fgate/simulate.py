"""Simulation harness: power and selection calibration of the complete F' screen procedure.

    python -m paper1.fgate.simulate --reps 25 --out SIM.json [--prefixes-per-context ...]

Each replicate simulates a screen with the planned design (contexts, prefixes per
context, one empty-library anchor plus ``draws`` antithetic randomized vectors per prefix,
12 lessons), fits the pre-specified model for success and harm, and applies the complete
gate under the three named priors (``analysis.PRIORS``: per-lesson checks per prior, the
intersection, shortlist, joint subset choice) and records each prior's stand-alone result
too, so false advancement and power are reported per prior and for the intersection. Scenarios:

* ``null``: no lesson changes success or harm (family-wise false advancement);
* ``power``: lesson 0 at +3 points, lesson 1 at +2 points, lesson 2 at +1 point (true
  standardized risk differences), the rest 0;
* ``context_harm``: lesson 0 at +4 points in its own contexts and -4 points in one other
  context (it must not pass; ``--e3-variants`` compares the E3 candidates on the same fits);
* ``harmful``: lesson 0 at +3 points success and +3 points harm (it must not pass);
* ``interaction``: lessons 0 and 1 at +2.5 points each with a negative interaction that
  removes the joint gain (the joint choice should keep one, not both).

The data-generating process adds what the analysis model does not assume: prefix-specific
lesson effects (``het_sd`` on the logit scale) and a between-prefix spread of baselines
with many prefixes near the ceiling. For speed the replicates fix the hyperparameters at
the grid centre (s_a = 2, tau = 0.5 s_b) instead of the empirical-Bayes grid; the real
analysis uses the grid. Light by design: run more replicates on a server, not a laptop.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

from paper1.fgate import analysis as A

CONTEXTS = {  # context -> (fit prefixes in the full design, anchor success assumed)
    "address:act": (72, 0.80), "address:clarify": (72, 0.55), "address:confirm": (36, 0.50),
    "variant:act": (204, 0.85), "variant:clarify": (204, 0.60), "variant:confirm": (102, 0.55),
    "sequence:act": (204, 0.80), "sequence:confirm": (306, 0.55)}
HARM_BASE = 0.06
# E3 (context harm) candidates compared on the same fits (``--e3-variants``). Each overrides
# A.RULES; E3 passes iff every context has P(RD_lc < -1 point) < p_context_harm and, when
# context_harm_bound is set, P(RD_lc > bound) >= p_context_harm_bound in every context.
E3_CANDIDATES: dict[str, dict[str, Any]] = {
    "p80": {"p_context_harm": 0.80},  # the rule before 2026-10-19
    "p70": {"p_context_harm": 0.70},
    "p50": {"p_context_harm": 0.50},
    "p30": {"p_context_harm": 0.30},
    "p20": {"p_context_harm": 0.20},
    "p10": {"p_context_harm": 0.10},  # P(RD_lc >= -1) > 0.90 everywhere: registered 2026-10-19
    "bound": {"p_context_harm": 0.80, "context_harm_bound": -0.025,
              "p_context_harm_bound": 0.95},
    "p50_bound": {"p_context_harm": 0.50, "context_harm_bound": -0.025,
                  "p_context_harm_bound": 0.95},
    "mirror_e4": {"p_context_harm": 0.20, "context_harm_bound": -0.025,
                  "p_context_harm_bound": 0.95}}
LESSON_CONTEXTS = {0: ("variant:act", "variant:clarify", "variant:confirm"),
                   1: ("sequence:act", "sequence:confirm")}


def _lessons(n: int) -> list[dict[str, Any]]:
    tools = [["address"], ["items"], ["address", "items"]]
    return [{"id": f"L{k + 1:02d}", "intent": "sim", "tools": tools[k % 3]} for k in range(n)]


def _design_rows(prefixes: dict[str, int], n_lessons: int, draws: int, rng: np.random.Generator
                 ) -> tuple[list[dict[str, Any]], np.ndarray, np.ndarray]:
    rows = []
    ctx_of = []
    for ctx, n in prefixes.items():
        for p in range(n):
            pid = f"{ctx}-{p}"
            vecs = [np.zeros(n_lessons, dtype=int)]
            seen = {tuple(vecs[0])}
            while len(vecs) < draws + 1:
                v = (rng.random(n_lessons) < 0.5).astype(int)
                w = 1 - v
                if tuple(v) in seen or tuple(w) in seen or v.sum() in (0, n_lessons):
                    continue
                seen.update((tuple(v), tuple(w)))
                vecs += [v, w]
            for v in vecs:
                rows.append({"case_id": pid, "context": ctx, "x": "".join(map(str, v)),
                             "track": "fgate"})
                ctx_of.append(ctx)
    x = np.array([[int(b) for b in r["x"]] for r in rows])
    return rows, x, np.array(ctx_of)


def _logit(p: float) -> float:
    return float(np.log(p / (1 - p)))


def _calibrate(base: np.ndarray, target: float, het: np.ndarray) -> float:
    """Logit shift b such that the mean of sigmoid(base + b + het) - sigmoid(base) = target."""
    if target == 0:
        return 0.0
    lo, hi = -6.0, 6.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        rd = float(np.mean(A._sigmoid(base + mid + het) - A._sigmoid(base)))
        lo, hi = (mid, hi) if rd < target else (lo, mid)
    return 0.5 * (lo + hi)


def simulate_once(scenario: str, *, prefixes: dict[str, int] | None = None,
                  n_lessons: int = 12, draws: int = 16, het_sd: float = 0.3,
                  base_sd: float = 1.5, seed: int = 0, n_draws: int = 300,
                  priors: dict[str, dict[str, Any]] | None = None,
                  e3_variants: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    prefixes = prefixes or {c: n for c, (n, _) in CONTEXTS.items()}
    rows, x, ctx = _design_rows(prefixes, n_lessons, draws, rng)
    pids = np.array([r["case_id"] for r in rows])
    uniq, pidx = np.unique(pids, return_inverse=True)
    ctx_of_prefix = {r["case_id"]: r["context"] for r in rows}
    base_p = np.array([_logit(CONTEXTS.get(ctx_of_prefix[p], (0, 0.7))[1]) for p in uniq])
    a = base_p + rng.normal(0, base_sd, len(uniq))
    het = rng.normal(0, het_sd, (len(uniq), n_lessons))
    a_h = _logit(HARM_BASE) + rng.normal(0, 1.0, len(uniq))
    contexts = sorted(prefixes)
    # True effects on the logit scale per (lesson, context), calibrated to RD targets.
    eff = np.zeros((n_lessons, len(contexts)))
    heff = np.zeros((n_lessons, len(contexts)))
    gamma = np.zeros((n_lessons, n_lessons))
    pref_ctx = np.array([contexts.index(ctx_of_prefix[p]) for p in uniq])

    def set_rd(lesson: int, target: float, which: tuple[str, ...] | None = None,
               harm: bool = False) -> None:
        for ci, c in enumerate(contexts):
            if which is not None and c not in which:
                continue
            m = pref_ctx == ci
            base = (a_h if harm else a)[m]
            b = _calibrate(base, target, 0 if harm else het[m, lesson])
            (heff if harm else eff)[lesson, ci] = b

    truth: dict[str, Any] = {}
    if scenario == "power":
        for lesson, t in ((0, 0.03), (1, 0.02), (2, 0.01)):
            set_rd(lesson, t)
        truth = {"L01": 0.03, "L02": 0.02, "L03": 0.01}
    elif scenario == "context_harm":
        set_rd(0, 0.04, LESSON_CONTEXTS[0])
        set_rd(0, -0.04, ("sequence:confirm",))
        truth = {"L01": "context harm"}
    elif scenario == "harmful":
        set_rd(0, 0.03)
        set_rd(0, 0.03, harm=True)
        truth = {"L01": "harmful"}
    elif scenario == "interaction":
        set_rd(0, 0.025)
        set_rd(1, 0.025)
        gamma[0, 1] = gamma[1, 0] = -float(np.median(eff[0] + eff[1]))
        truth = {"L01": 0.025, "L02": 0.025, "joint": "no gain over one"}
    elif scenario != "null":
        raise ValueError(scenario)
    ci = np.array([contexts.index(c) for c in ctx])
    eta = a[pidx] + (x * (eff[:, ci].T + het[pidx])).sum(1) + 0.5 * np.einsum(
        "rl,lm,rm->r", x, gamma, x)
    eta_h = a_h[pidx] + (x * heff[:, ci].T).sum(1)
    y = (rng.random(len(rows)) < A._sigmoid(eta)).astype(int)
    h = (rng.random(len(rows)) < A._sigmoid(eta_h)).astype(int)
    for r, yy, hh in zip(rows, y, h, strict=True):
        r["y"], r["harm"] = int(yy), int(hh)
    lessons = _lessons(n_lessons)
    fits = A.fit_priors(rows, lessons, priors=priors, n_draws=n_draws, seed=seed, eb=False)
    cache: dict[Any, dict[str, Any]] = {}
    g = A.gate_priors(fits, lessons, joint_cache=cache)
    out = {"scenario": scenario, "truth": truth,
           "passes": [p["id"] for p in g["lessons"] if p["passes"]],
           "advanced": g["advanced"], "rd_mean": [round(p["rd_mean"], 4) for p in g["lessons"]],
           "by_prior": {pr: {"passes": v["passing"], "advanced": v["advanced"],
                             "rd_mean": [round(float(fits[pr][0]["rd"][:, k].mean()), 4)
                                         for k in range(n_lessons)]}
                        for pr, v in g["by_prior"].items()}}
    if e3_variants:
        # max over contexts of P(RD_lc < -1 point), per prior and lesson (offline thresholds)
        out["max_p_context_harm"] = {
            pr: [round(max(p["by_prior"][pr]["p_context_harm"].values()), 4)
                 for p in g["lessons"]] for pr in g["priors"]}
        out["e3_variants"] = {}
        for name, over in e3_variants.items():
            gv = A.gate_priors(fits, lessons, {**A.RULES, **over}, joint_cache=cache)
            out["e3_variants"][name] = {"passes": [p["id"] for p in gv["lessons"]
                                                   if p["passes"]],
                                        "advanced": gv["advanced"]}
    return out


def _rates(rs: list[dict[str, Any]], sc: str, n_lessons: int) -> dict[str, Any]:
    n = len(rs)
    per = {f"L{k + 1:02d}": sum(f"L{k + 1:02d}" in r["passes"] for r in rs) / n
           for k in range(n_lessons)}
    adv = {f"L{k + 1:02d}": sum(f"L{k + 1:02d}" in r["advanced"] for r in rs) / n
           for k in range(n_lessons)}
    rd = np.array([r["rd_mean"] for r in rs])
    out = {"p_pass": per, "p_advanced": adv,
           "p_any_advanced": sum(bool(r["advanced"]) for r in rs) / n,
           "mean_rd_estimate": [round(float(v), 4) for v in rd.mean(0)]}
    if sc == "interaction":
        out["p_both_advanced"] = sum({"L01", "L02"} <= set(r["advanced"]) for r in rs) / n
    return out


def summarize(results: list[dict[str, Any]], n_lessons: int = 12) -> dict[str, Any]:
    """Per scenario: the final (intersection) gate's rates at the top level, and each named
    prior's stand-alone rates under ``by_prior``. Null: ``p_any_advanced`` is the
    family-wise false advancement; power: ``p_advanced`` of L01/L02/L03."""
    out: dict[str, Any] = {}
    for sc in sorted({r["scenario"] for r in results}):
        rs = [r for r in results if r["scenario"] == sc]
        n = len(rs)
        out[sc] = {"reps": n, **_rates(rs, sc, n_lessons),
                   "mc_se_max": round(float(np.sqrt(0.25 / n)), 3)}
        priors = list(rs[0].get("by_prior") or {})
        if priors:
            out[sc]["by_prior"] = {pr: _rates([r["by_prior"][pr] for r in rs], sc, n_lessons)
                                   for pr in priors}
        variants = list(rs[0].get("e3_variants") or {})
        if variants:  # final (intersection) gate under each E3 candidate, same fits
            out[sc]["e3_variants"] = {}
            for v in variants:
                rr = _rates([{**r["e3_variants"][v], "rd_mean": r["rd_mean"]} for r in rs],
                            sc, n_lessons)
                out[sc]["e3_variants"][v] = {k: rr[k] for k in rr if k != "mean_rd_estimate"}
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m paper1.fgate.simulate")
    ap.add_argument("--reps", type=int, default=25)
    ap.add_argument("--scenarios", default="null,power,context_harm,harmful,interaction")
    ap.add_argument("--scale", type=float, default=1.0,
                    help="multiply prefixes per context (1.0 = planned full design)")
    ap.add_argument("--draws", type=int, default=16)  # the planned design (D.DRAWS)
    ap.add_argument("--posterior-draws", type=int, default=300)
    ap.add_argument("--e3-variants", action="store_true",
                    help="also apply every E3_CANDIDATES rule to the same fits")
    ap.add_argument("--seed-offset", type=int, default=0,
                    help="first replicate index (split a run across processes)")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args(argv)
    prefixes = {c: max(2, round(n * args.scale)) for c, (n, _) in CONTEXTS.items()}
    results = []
    t0 = time.time()
    for sc in args.scenarios.split(","):
        for rep in range(args.seed_offset, args.seed_offset + args.reps):
            results.append(simulate_once(sc, prefixes=prefixes, draws=args.draws,
                                         seed=1000 * rep + 7 * args.scenarios.split(",").index(sc),
                                         n_draws=args.posterior_draws,
                                         e3_variants=E3_CANDIDATES if args.e3_variants
                                         else None))
            if args.out and len(results) % 10 == 0:  # partial results (resume by seed range)
                args.out.write_text(json.dumps({"partial": True, "results": results}))
    summary = {"design": {"prefixes": prefixes, "draws": args.draws,
                          "decisions": sum(prefixes.values()) * (args.draws + 1)},
               "wall_s": round(time.time() - t0, 1), "scenarios": summarize(results)}
    if args.out:
        args.out.write_text(json.dumps({"summary": summary, "results": results}, indent=1))
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
