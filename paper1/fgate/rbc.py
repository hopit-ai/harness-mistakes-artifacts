"""RBC-style comparator on the F' screen data (SECONDARY, exploratory; pre-registered
2026-10-20 in docs/xp/rbc-comparator-registration.md before any hand-off 1b outcome was seen).

Mirrors RBC (Pham et al., arXiv:2610.18427; docs/lit/survey-2026-10-20.md item 2) adapted to
our decision units. It never changes the F' gate decision (``fgate.analysis``); confirming
the RBC-selected set in step 6 is a separate owner decision.

RBC curation stage only; RBC's fresh-episode final selection not run.

**Unit of inclusion.** The 12 pool lessons (our design has no blocks, so a lesson is an RBC
block). Each lesson's marginal inclusion probability is 1/2 (antithetic pairs), but the
inclusions are **not jointly independent**: ``fgate.design.inclusion_vectors`` rejects the
empty and the whole vector and any repeated vector (or its complement) within a prefix.

**Rows.** Track ``fgate`` rows whose inclusion vector ``x`` has at least one lesson (the
randomized draws; this drops exactly the all-zero empty-library anchors, an extra design
point RBC does not have). Every row must carry its configuration ``group`` (refused
otherwise). Error rows are kept as scored (as in the primary F' analysis) and counted.

**Estimator (per outcome).** Linear probability ridge with one unpenalized intercept per
decision prefix (``case_id``; RBC's per-task intercept)::

    y_r = a_i + sum_l x_rl b_l + e_r,   minimise  sum_r e_r^2 + lambda * sum_l b_l^2

fitted exactly by the within-prefix transform (Frisch-Waugh): x and y demeaned within each
prefix, then b = (X'X + lambda I)^+ X'y (Moore-Penrose, so lambda = 0 is OLS). b_l is a
regularized effect of lesson l under this restricted design (marginal inclusion 1/2, empty /
whole / repeated vectors excluded); it approximates, but is not exactly, RBC's Banzhaf value.
Held-out and fitted rows are weighted equally (RBC), whereas F' standardizes contexts
equally, so differences from F' reflect weighting, model and regularization as well as
gating.

**Lambda** by leave-one-task-out cross-validation (task = decision prefix) over the fixed
grid ``LAMBDA_GRID``: each prefix in turn is held out, b is refitted on the others, and the
held-out prefix's demeaned outcomes are predicted (its intercept is its own mean, as for an
unseen task). Criterion: total squared error; the minimum wins, exact ties to the larger
lambda. Success and harm each get their own lambda. Sensitivity (reported, never used):
folds = configuration group (the 3 phrasings of one configuration).

**Selection (success only, as published).** Lessons with b_l > 0, highest first (ties by
id), at most ``BUDGET_LESSONS`` = 4: the F' shortlist cap (``analysis.RULES['shortlist']``).
F' has no token budget; its budget is this lesson count, so RBC gets the same.

**Descriptive extras.** Percentile 90% intervals (descriptive, conditional on the fixed
chosen lambda, no post-selection guarantee) and selection frequencies from a cluster
bootstrap over configuration groups at the chosen lambda (``BOOT_DRAWS``, ``BOOT_SEED``);
harm estimates (not used to select); in-sample linear contrasts curated / whole / none
(``in_sample_contrasts_not_rbc_choice``: never RBC's choice).
**RBC's final step** (pick curated vs whole vs none on fresh episodes) is not run here: the
registered evaluate prefixes carry only B1 (empty library) collection units, no curated or
whole-library arm, so no fresh-episode comparison exists in hand-off 1b. It is the optional
step-6 confirmation.

**F' cross-reference (exploratory).** Overlap of the RBC set with the F' advanced set and
shortlist; for every RBC-selected lesson its F' pass, E3 (context harm) and E4 (wrong-write
harm) status and F' harm RD.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import numpy as np

SCHEMA = "xp-fgate-rbc-v1"
LAMBDA_GRID = (0.0, 1.0, 3.0, 10.0, 30.0, 100.0, 300.0, 1000.0, 3000.0, 10000.0, 30000.0,
               100000.0)
BUDGET_LESSONS = 4  # = fgate.analysis.RULES["shortlist"] (a test pins the equality)
BOOT_DRAWS = 1000
BOOT_SEED = 20261020
OUTCOMES = ("y", "harm")
STAGE = "RBC curation stage only; RBC's fresh-episode final selection not run."
CI_NOTE = ("90% intervals: cluster bootstrap over configuration groups, descriptive, "
           "conditional on the fixed chosen lambda; no post-selection guarantee.")
STATEMENT = ("Secondary, exploratory comparator (RBC-style, pre-registered 2026-10-20). It "
             "never changes the F' gate decision; confirming the RBC set is a separate owner "
             "decision (step 6). " + STAGE)


class Refused(ValueError):
    """Input the comparator does not accept (no randomized F' rows, wrong vector length)."""


# --------------------------------------------------------------------------- data


def screen_rows(table: list[dict[str, Any]], n_lessons: int) -> list[dict[str, Any]]:
    """Randomized F' rows (track ``fgate``, not anchors), in unit order."""
    rows = sorted((r for r in table if r.get("track") == "fgate"
                   and any(int(b) for b in r["x"])), key=lambda r: r["unit_id"])
    if not rows:
        raise Refused("no randomized F' rows in the table")
    for r in rows:
        if len(r["x"]) != n_lessons:
            raise Refused(f"{r['unit_id']}: inclusion vector length differs from the pool")
    return rows


class Stats:
    """Per-prefix within-transformed sufficient statistics of one outcome."""

    def __init__(self, rows: list[dict[str, Any]], outcome: str, n_lessons: int) -> None:
        by: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for r in rows:
            by[r["case_id"]].append(r)
        self.prefixes = sorted(by)
        missing = sorted(p for p in self.prefixes if any(not r.get("group") for r in by[p]))
        if missing:
            raise Refused(f"{len(missing)} prefix(es) without a configuration group, e.g. "
                          f"{missing[0]}")
        self.group = [str(by[p][0]["group"]) for p in self.prefixes]
        L = n_lessons
        self.G = np.zeros((len(self.prefixes), L, L))
        self.b = np.zeros((len(self.prefixes), L))
        self.yy = np.zeros(len(self.prefixes))
        for k, p in enumerate(self.prefixes):
            x = np.array([[int(v) for v in r["x"]] for r in by[p]], dtype=np.float64)
            y = np.array([float(r[outcome]) for r in by[p]])
            x -= x.mean(axis=0)
            y -= y.mean()
            self.G[k], self.b[k], self.yy[k] = x.T @ x, x.T @ y, float(y @ y)
        self.n_rows = len(rows)
        self.L = L

    def folds(self, key: str) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str]]:
        """(G, b, yy) summed per fold; ``key`` = ``prefix`` or ``group``."""
        labels = self.prefixes if key == "prefix" else self.group
        names = sorted(set(labels))
        idx = {n: i for i, n in enumerate(names)}
        ix = np.array([idx[x] for x in labels])
        G = np.zeros((len(names), self.L, self.L))
        b = np.zeros((len(names), self.L))
        yy = np.zeros(len(names))
        np.add.at(G, ix, self.G)
        np.add.at(b, ix, self.b)
        np.add.at(yy, ix, self.yy)
        return G, b, yy, names


def solve(G: np.ndarray, b: np.ndarray, lam: float) -> np.ndarray:
    """Ridge coefficients (Moore-Penrose; batched over a leading axis)."""
    eye = np.eye(G.shape[-1])
    return np.einsum("...ij,...j->...i", np.linalg.pinv(G + lam * eye), b)


def cv_curve(st: Stats, grid: tuple[float, ...] = LAMBDA_GRID, *, folds: str = "prefix"
             ) -> list[dict[str, float]]:
    """Leave-one-fold-out squared error per lambda (folds: prefix = RBC's task)."""
    Gf, bf, yyf, _ = st.folds(folds)
    G, b = Gf.sum(axis=0), bf.sum(axis=0)
    out = []
    for lam in grid:
        beta = solve(G[None] - Gf, b[None] - bf, lam)  # one fit per held-out fold
        err = yyf - 2 * np.einsum("fi,fi->f", beta, bf) + np.einsum(
            "fi,fij,fj->f", beta, Gf, beta)
        out.append({"lambda": float(lam), "sse": float(err.sum()),
                    "mse": float(err.sum() / max(1, st.n_rows))})
    return out


def choose_lambda(curve: list[dict[str, float]]) -> float:
    """Smallest CV error; exact ties to the larger lambda."""
    return max(curve, key=lambda c: (-c["sse"], c["lambda"]))["lambda"]


def select(ids: list[str], beta: np.ndarray, budget: int = BUDGET_LESSONS) -> dict[str, Any]:
    """Positive estimates, highest first (ties by id), at most ``budget``."""
    pos = sorted((i for i in range(len(ids)) if beta[i] > 0), key=lambda i: (-beta[i], ids[i]))
    return {"positive": [ids[i] for i in pos], "selected": [ids[i] for i in pos[:budget]]}


def fit_outcome(rows: list[dict[str, Any]], outcome: str, ids: list[str], *,
                grid: tuple[float, ...] = LAMBDA_GRID, boot: int = BOOT_DRAWS,
                seed: int = BOOT_SEED) -> dict[str, Any]:
    st = Stats(rows, outcome, len(ids))
    curve = cv_curve(st, grid)
    lam = choose_lambda(curve)
    G, b = st.G.sum(axis=0), st.b.sum(axis=0)
    beta = solve(G, b, lam)
    group_curve = cv_curve(st, grid, folds="group")
    lam_g = choose_lambda(group_curve)
    beta_g = solve(G, b, lam_g)
    # cluster bootstrap over configuration groups, lambda fixed at the chosen value
    Gg, bg, _, names = st.folds("group")
    rng = np.random.default_rng(seed)
    w = np.stack([np.bincount(rng.integers(0, len(names), len(names)), minlength=len(names))
                  for _ in range(boot)]).astype(np.float64) if boot else np.zeros((0, len(names)))
    bb = solve(np.einsum("dg,gij->dij", w, Gg), np.einsum("dg,gi->di", w, bg), lam) \
        if boot else np.zeros((0, len(ids)))
    return {"outcome": outcome, "rows": st.n_rows, "prefixes": len(st.prefixes),
            "groups": len(names), "lambda": lam, "cv": curve, "beta": beta,
            "boot": bb, "group_folds": {"lambda": lam_g, "cv": group_curve, "beta": beta_g}}


def _ci(v: np.ndarray) -> list[float] | None:
    return [float(np.quantile(v, 0.05)), float(np.quantile(v, 0.95))] if len(v) else None


# --------------------------------------------------------------------------- report


def rbc(table: list[dict[str, Any]], lessons: list[dict[str, Any]], *,
        fgate: dict[str, Any] | None = None, grid: tuple[float, ...] = LAMBDA_GRID,
        budget: int = BUDGET_LESSONS, boot: int = BOOT_DRAWS, seed: int = BOOT_SEED
        ) -> dict[str, Any]:
    ids = [les["id"] for les in lessons]
    rows = screen_rows(table, len(ids))
    fits = {o: fit_outcome(rows, o, ids, grid=grid, boot=boot, seed=seed) for o in OUTCOMES}
    s, h = fits["y"], fits["harm"]
    sel = select(ids, s["beta"], budget)
    boot_sel = [select(ids, bb, budget)["selected"] for bb in s["boot"]]
    per = []
    for k, lid in enumerate(ids):
        per.append({"id": lid, "intent": lessons[k].get("intent"),
                    "success_b": float(s["beta"][k]), "success_ci90": _ci(s["boot"][:, k]),
                    "p_boot_positive": (float((s["boot"][:, k] > 0).mean())
                                        if len(s["boot"]) else None),
                    "boot_selected_freq": (sum(lid in b for b in boot_sel) / len(boot_sel)
                                           if boot_sel else None),
                    "harm_b": float(h["beta"][k]), "harm_ci90": _ci(h["boot"][:, k]),
                    "positive": lid in sel["positive"], "selected": lid in sel["selected"]})
    sel_idx = [ids.index(x) for x in sel["selected"]]
    gsel = select(ids, s["group_folds"]["beta"], budget)
    rep: dict[str, Any] = {
        "schema": SCHEMA, "statement": STATEMENT,
        "estimator": {"model": "linear probability ridge, one unpenalized intercept per "
                               "decision prefix (within transform), lessons as blocks",
                      "rows": "track fgate, randomized draws only (anchors excluded)",
                      "lambda_grid": list(grid), "cv": "leave-one-prefix-out, total SSE, "
                      "ties to larger lambda", "budget_lessons": budget,
                      "budget_basis": "F' shortlist cap (analysis.RULES['shortlist']); F' "
                                      "has no token budget",
                      "bootstrap": {"draws": boot, "seed": seed,
                                    "cluster": "configuration group", "lambda": "fixed"}},
        "rows": s["rows"], "prefixes": s["prefixes"], "groups": s["groups"],
        "error_rows": sum(1 for r in rows if r.get("error_class")),
        "lambda": {"success": s["lambda"], "harm": h["lambda"]},
        "cv": {"success": s["cv"], "harm": h["cv"]},
        "lessons": per, "positive": sel["positive"], "selected": sel["selected"],
        "sensitivity_group_folds": {"lambda": s["group_folds"]["lambda"],
                                    "selected": gsel["selected"],
                                    "same_as_primary": gsel["selected"] == sel["selected"]},
        "ci_note": CI_NOTE,
        "weighting_note": "rows weighted equally (RBC); F' standardizes contexts equally, so "
                          "differences reflect weighting, model and regularization too, not "
                          "only gating",
        "in_sample_contrasts_not_rbc_choice": {
            "note": "in-sample linear predictions vs the empty library on the fitted data; "
                    "NOT RBC's choice (its fresh-episode final selection was not run)",
            "curated_success": float(s["beta"][sel_idx].sum()) if sel_idx else 0.0,
            "whole_success": float(s["beta"].sum()), "none_success": 0.0,
            "curated_harm": float(h["beta"][sel_idx].sum()) if sel_idx else 0.0,
            "whole_harm": float(h["beta"].sum()), "none_harm": 0.0},
        "stage": STAGE,
        "final_step": {"run": False,
                       "reason": "RBC's curated/whole/none choice needs fresh episodes with "
                                 "those libraries; hand-off 1b's evaluate prefixes carry only "
                                 "B1 (empty-library) units. Optional step-6 confirmation, a "
                                 "separate owner decision."}}
    rep["fgate"] = crossref(sel["selected"], fgate) if fgate is not None else None
    return rep


def crossref(selected: list[str], fgate: dict[str, Any]) -> dict[str, Any]:
    """Overlap with F' and (exploratory) the F' harm / E3 status of each RBC lesson."""
    g = fgate["gate"]
    by = {les["id"]: les for les in g["lessons"]}
    adv, sl = list(g.get("advanced") or []), list(g.get("shortlist") or [])
    union = set(selected) | set(adv)
    return {
        "fgate_partial": (fgate.get("ourside") or {}).get("partial"),
        "advanced": adv, "shortlist": sl,
        "overlap_advanced": [x for x in selected if x in adv],
        "overlap_shortlist": [x for x in selected if x in sl],
        "jaccard_advanced": (len(set(selected) & set(adv)) / len(union)) if union else None,
        "rbc_only": [x for x in selected if x not in adv],
        "fgate_only": [x for x in adv if x not in selected],
        "selected_status": [{
            "id": x, "fgate_passes": by[x]["passes"],
            "passes_by_prior": by[x].get("passes_by_prior"),
            "E3": by[x]["checks"]["E3"], "E4": by[x]["checks"]["E4"],
            "max_p_context_harm": by[x].get("max_p_context_harm"),
            "harm_rd_mean": by[x].get("harm_rd_mean"),
            "p_harm_gt_delta": by[x].get("p_harm_gt_delta")} for x in selected if x in by]}


def _pp(x: float | None) -> str:
    return "–" if x is None else f"{100 * x:+.1f}"


def render(rep: dict[str, Any]) -> str:
    o = rep.get("ourside") or {}
    out = ["# Hand-off 1b: RBC-style comparator (secondary, exploratory)", ""]
    if o.get("partial"):
        out += [(f"**STATUS: {o.get('status')}.** Not the registered comparator: the screen "
                 "is incomplete; the numbers below are descriptive only."), ""]
    elif o and not o.get("registered_analysis"):
        out += [(f"**STATUS: not registered** ({'; '.join(o.get('not_registered') or [])}). "
                 "Descriptive only."), ""]
    out += [rep["statement"], "",
            (f"{rep['rows']} randomized rows on {rep['prefixes']} prefixes ({rep['groups']} "
             f"configuration groups; {rep['error_rows']} error rows kept); anchors excluded. "
             f"Ridge with prefix intercepts; lambda by leave-one-prefix-out: success "
             f"{rep['lambda']['success']:g}, harm {rep['lambda']['harm']:g}. Budget: at most "
             f"{rep['estimator']['budget_lessons']} lessons (the F' shortlist cap). Registered "
             f"comparator: **{o.get('registered_analysis')}**."), "",
            CI_NOTE, "",
            ("| Lesson | Intent | Success b (pts) | Descriptive 90% interval | Boot sel. | "
             "Harm b (pts) | RBC |"),
            "|---|---|---:|---|---:|---:|---|"]
    for les in rep["lessons"]:
        ci = les["success_ci90"]
        f = les["boot_selected_freq"]
        out.append(f"| {les['id']} | {les.get('intent') or ''} | {_pp(les['success_b'])} | "
                   + (f"[{_pp(ci[0])}, {_pp(ci[1])}]" if ci else "–") + " | "
                   + ("–" if f is None else f"{f:.2f}") + f" | {_pp(les['harm_b'])} | "
                   + ("**selected**" if les["selected"] else "positive" if les["positive"]
                      else "") + " |")
    c = rep["in_sample_contrasts_not_rbc_choice"]
    sg = rep["sensitivity_group_folds"]
    out += ["", (f"**RBC set: {rep['selected'] or 'none'}** (positive: "
                 f"{rep['positive'] or 'none'}). Group-fold sensitivity: lambda "
                 f"{sg['lambda']:g}, set {sg['selected'] or 'none'}."), "",
            (f"In-sample linear contrasts vs none — NOT RBC's choice (its fresh-episode final "
             f"selection was not run): curated success "
             f"{_pp(c['curated_success'])}, whole {_pp(c['whole_success'])}; harm curated "
             f"{_pp(c['curated_harm'])}, whole {_pp(c['whole_harm'])}."), "",
            f"Weighting: {rep['weighting_note']}.", "",
            f"Final step not run: {rep['final_step']['reason']}"]
    fx = rep.get("fgate")
    if fx:
        out += ["", "## F' cross-reference (exploratory)", ""]
        if o and not o.get("fgate_registered"):
            out += [("**STATUS: cross-reference not registered**: the F' report is not the "
                     "registered analysis (1000 draws + sensitivities on the complete "
                     "archive)."), ""]
        out += [
                (f"F' advanced {fx['advanced'] or 'none'}, shortlist {fx['shortlist'] or 'none'}"
                 f". Overlap with advanced {fx['overlap_advanced'] or 'none'} (Jaccard "
                 f"{'–' if fx['jaccard_advanced'] is None else round(fx['jaccard_advanced'], 2)}"
                 f"); RBC only {fx['rbc_only'] or 'none'}; F' only {fx['fgate_only'] or 'none'}."),
                "", "| RBC lesson | F' pass | E3 | E4 | max P(ctx harm) | F' harm RD |",
                "|---|---|---|---|---:|---:|"]
        yn = {True: "y", False: "n", None: "?"}
        for s in fx["selected_status"]:
            mp = s["max_p_context_harm"]
            out.append(f"| {s['id']} | {yn[s['fgate_passes']]} | {yn[s['E3']]} | "
                       f"{yn[s['E4']]} | {'–' if mp is None else f'{mp:.2f}'} | "
                       f"{_pp(s['harm_rd_mean'])} |")
    return "\n".join(out) + "\n"
