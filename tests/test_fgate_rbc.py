"""RBC-style comparator (paper1.fgate.rbc): planted effects are recovered, the budget is
the F' shortlist cap and results are deterministic. Synthetic tables only. (The project's
orchestration tests of its scoring pipeline are not part of this release.)"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from paper1.fgate import analysis as A
from paper1.fgate import pool as P
from paper1.fgate import rbc as R
from paper1 import _io as pc

REPO = Path(__file__).resolve().parents[1]
L = 12
IDS = [f"L{i:02d}" for i in range(1, L + 1)]
CONTEXTS = ("address:act", "variant:confirm", "sequence:clarify")


def _table(effects: dict[str, float], *, harm: dict[str, float] | None = None,
           prefixes: int = 360, draws: int = 16, seed: int = 7, base: float = 0.55
           ) -> list[dict]:
    """F' rows: per prefix one anchor + ``draws`` antithetic p = 1/2 vectors; success and
    harm Bernoulli with additive planted lesson effects and a prefix-level shift."""
    rng = np.random.default_rng(seed)
    eff = np.array([effects.get(i, 0.0) for i in IDS])
    heff = np.array([(harm or {}).get(i, 0.0) for i in IDS])
    rows = []
    for p in range(prefixes):
        cid = f"c{p:04d}"
        shift = rng.normal(0, 0.1)
        vecs = [np.zeros(L, dtype=int)]
        for _ in range(draws // 2):
            v = rng.integers(0, 2, L)
            vecs += [v, 1 - v]
        for k, v in enumerate(vecs):
            py = np.clip(base + shift + v @ eff, 0.01, 0.99)
            ph = np.clip(0.05 + v @ heff, 0.0, 0.99)
            rows.append({"unit_id": f"{cid}-{k:02d}", "track": "fgate", "case_id": cid,
                         "group": f"g{p // 3:04d}", "context": CONTEXTS[p % 3],
                         "x": "".join(str(int(b)) for b in v), "anchor": not v.any(),
                         "y": int(rng.random() < py), "harm": int(rng.random() < ph),
                         "reask": 0, "error_class": None})
    return rows


LESSONS = [{"id": i, "intent": "x"} for i in IDS]


def test_budget_is_the_fgate_shortlist_cap():
    assert R.BUDGET_LESSONS == A.RULES["shortlist"] == 4


def test_planted_effects_recovered_and_selected():
    rep = R.rbc(_table({"L01": 0.15, "L02": 0.10, "L03": -0.10}), LESSONS, boot=200)
    b = {x["id"]: x["success_b"] for x in rep["lessons"]}
    assert abs(b["L01"] - 0.15) < 0.03 and abs(b["L02"] - 0.10) < 0.03
    assert abs(b["L03"] + 0.10) < 0.03
    assert rep["selected"][:2] == ["L01", "L02"]
    assert "L03" not in rep["positive"]
    assert rep["rows"] == 360 * 16  # anchors excluded
    assert rep["lambda"]["success"] in R.LAMBDA_GRID
    ci = next(x for x in rep["lessons"] if x["id"] == "L01")["success_ci90"]
    assert ci[0] < 0.15 < ci[1]


def test_budget_keeps_the_four_highest_positive():
    eff = {"L01": 0.04, "L02": 0.20, "L03": 0.12, "L04": 0.16, "L05": 0.08, "L06": 0.10}
    rep = R.rbc(_table(eff, prefixes=600), LESSONS, boot=0)
    assert rep["selected"] == ["L02", "L04", "L03", "L06"]
    assert len(rep["positive"]) >= 6


def test_harm_is_reported_but_not_used_for_selection():
    rep = R.rbc(_table({"L01": 0.15}, harm={"L01": 0.20}), LESSONS, boot=0)
    les = {x["id"]: x for x in rep["lessons"]}
    assert les["L01"]["selected"] and abs(les["L01"]["harm_b"] - 0.20) < 0.03


def test_ridge_matches_dummy_intercept_regression():
    rows = [r for r in _table({"L01": 0.1}, prefixes=30) if not r["anchor"]]
    st = R.Stats(rows, "y", L)
    beta = R.solve(st.G.sum(0), st.b.sum(0), 10.0)
    cids = sorted({r["case_id"] for r in rows})
    D = np.array([[r["case_id"] == c for c in cids] for r in rows], float)
    X = np.array([[int(v) for v in r["x"]] for r in rows], float)
    y = np.array([r["y"] for r in rows], float)
    Z = np.hstack([D, X])
    pen = np.diag([0.0] * len(cids) + [10.0] * L)
    full = np.linalg.solve(Z.T @ Z + pen, Z.T @ y)[len(cids):]
    assert np.allclose(beta, full, atol=1e-9)


def test_loo_cv_matches_explicit_refit():
    rows = [r for r in _table({"L01": 0.1}, prefixes=12) if not r["anchor"]]
    st = R.Stats(rows, "y", L)
    curve = R.cv_curve(st, (3.0,))
    sse = 0.0
    for k in range(len(st.prefixes)):
        keep = [j for j in range(len(st.prefixes)) if j != k]
        beta = R.solve(st.G[keep].sum(0), st.b[keep].sum(0), 3.0)
        sse += st.yy[k] - 2 * beta @ st.b[k] + beta @ st.G[k] @ beta
    assert curve[0]["sse"] == pytest.approx(sse)


def test_lambda_ties_go_to_the_larger_value():
    curve = [{"lambda": 1.0, "sse": 5.0}, {"lambda": 10.0, "sse": 5.0},
             {"lambda": 100.0, "sse": 6.0}]
    assert R.choose_lambda(curve) == 10.0


def test_deterministic():
    t = _table({"L01": 0.1})
    a = json.dumps(R.rbc(t, LESSONS, boot=100), sort_keys=True)
    b = json.dumps(R.rbc(list(reversed(t)), LESSONS, boot=100), sort_keys=True)
    assert a == b


def test_refuses_without_randomized_rows_or_wrong_length():
    t = [r for r in _table({}, prefixes=3) if r["anchor"]]
    with pytest.raises(R.Refused):
        R.rbc(t, LESSONS, boot=0)
    with pytest.raises(R.Refused):
        R.rbc(_table({}, prefixes=3), LESSONS[:11], boot=0)


def test_crossref_reports_fgate_status_of_rbc_lessons():
    fg = {"ourside": {"partial": False}, "gate": {
        "advanced": ["L01", "L05"], "shortlist": ["L01", "L05", "L07"],
        "lessons": [{"id": i, "passes": i in ("L01", "L05", "L07"),
                     "passes_by_prior": {}, "checks": {"E3": i != "L02", "E4": True},
                     "max_p_context_harm": 0.3 if i == "L02" else 0.01,
                     "harm_rd_mean": 0.0, "p_harm_gt_delta": 0.0} for i in IDS]}}
    x = R.crossref(["L01", "L02"], fg)
    assert x["overlap_advanced"] == ["L01"] and x["rbc_only"] == ["L02"]
    assert x["fgate_only"] == ["L05"] and x["jaccard_advanced"] == pytest.approx(1 / 3)
    st = {s["id"]: s for s in x["selected_status"]}
    assert st["L02"]["E3"] is False and st["L02"]["fgate_passes"] is False
