"""F' gate under three named priors (owner decision 2026-10-18): a lesson passes only if
the gate holds under the sceptical, weakly informative and literature-informed priors."""

from __future__ import annotations

import copy

import numpy as np
import pytest

from paper1.fgate import analysis as A
from paper1.fgate import design as D
from paper1.fgate import simulate as SIM

LESSONS = [{"id": f"L{k}", "intent": "x", "tools": ["t"]} for k in range(4)]
# small test data: relaxed exposure and harm-precision rules (E4 needs large n)
RULES = {**A.RULES, "min_exposure": 10, "p_harm": 0.5, "harm_bound": 0.10}


def _rows(effect: float, seed: int = 0, n_prefix: int = 160) -> list[dict]:
    rng = np.random.default_rng(seed)
    rows = []
    for p in range(n_prefix):
        ctx = ("a:act", "b:confirm")[p % 2]
        a = rng.normal(0.8, 1.0)
        for v in D.inclusion_vectors(f"p{p}", 4, 8):
            eta = a + effect * v[0]
            rows.append({"case_id": f"p{p}", "context": ctx, "x": D.bits(v), "track": "fgate",
                         "y": int(rng.random() < 1 / (1 + np.exp(-eta))),
                         "harm": int(rng.random() < 0.05), "reask": 0})
    return rows


@pytest.fixture(scope="module")
def rows() -> list[dict]:
    return _rows(0.5)


def test_named_priors_registered() -> None:
    assert A.PRIORS["sceptical"] == {"mean": 0.0, "sd": 0.03, "primary": True}
    assert A.PRIORS["weak"]["mean"] == 0.0 and A.PRIORS["weak"]["sd"] == 0.06
    assert A.PRIORS["literature"]["mean"] < 0 and A.PRIORS["literature"]["sd"] == 0.03
    assert [k for k, v in A.PRIORS.items() if v.get("primary")] == ["sceptical"]


def test_prior_centre_shifts_posterior(rows: list[dict]) -> None:
    kw = {"n_draws": 400, "eb": False, "seed": 1, "interaction_rd_sd": A.BASE_RD_SD}
    base = A.fit_outcome(rows, "y", LESSONS, **kw)
    lit = A.fit_outcome(rows, "y", LESSONS, rd_prior_mean=-0.01, **kw)
    far = A.fit_outcome(rows, "y", LESSONS, rd_prior_mean=-0.05, **kw)
    up = A.fit_outcome(rows, "y", LESSONS, rd_prior_mean=+0.01, **kw)
    m = {k: f["rd"].mean(0) for k, f in (("0", base), ("-1", lit), ("-5", far), ("+1", up))}
    # every lesson moves towards the prior centre, monotone in the centre, less than the shift
    assert (m["-5"] < m["-1"]).all() and (m["-1"] < m["0"]).all() and (m["0"] < m["+1"]).all()
    assert ((m["0"] - m["-1"]) < 0.01).all() and ((m["0"] - m["-1"]) > 0).all()
    assert lit["mu_b"] < 0 and base["mu_b"] == 0 and lit["s_b"] == pytest.approx(base["s_b"])
    # the interaction scale does not move with the main-effect prior
    assert lit["s_int"] == pytest.approx(base["s_int"])
    # a wider prior shrinks the real effect less
    weak = A.fit_outcome(rows, "y", LESSONS, rd_prior_sd=0.06, **kw)
    assert weak["rd"].mean(0)[0] > base["rd"].mean(0)[0]
    assert weak["s_b"] == pytest.approx(2 * base["s_b"]) and weak["s_int"] == base["s_int"]


def test_default_single_scale_unchanged(rows: list[dict]) -> None:
    """Callers that pass only rd_prior_sd (BFCL F') keep one scale for mains and interactions."""
    f = A.fit_outcome(rows, "y", LESSONS, n_draws=50, eb=False, rd_prior_sd=0.05)
    assert f["s_int"] == pytest.approx(f["s_b"]) and f["mu_b"] == 0


@pytest.fixture(scope="module")
def fits(rows: list[dict]) -> dict:
    return A.fit_priors(rows, LESSONS, n_draws=300, seed=0, eb=False)


def test_intersection_agrees_with_every_prior(fits: dict) -> None:
    g = A.gate_priors(fits, LESSONS, RULES, primary="sceptical")
    assert g["priors"] == ["sceptical", "weak", "literature"] and g["primary"] == "sceptical"
    for les, row in zip(g["lessons"], g["table"], strict=True):
        assert les["passes"] == all(les["passes_by_prior"].values()) == row["final"]
        for k, ok in les["checks"].items():
            assert ok == all(les["by_prior"][pr]["checks"][k] for pr in g["priors"])
    assert set(g["shortlist"]) <= {p["id"] for p in g["lessons"] if p["passes"]}
    assert set(g["advanced"]) <= set(g["shortlist"])
    for s in g["subsets"]:
        assert s["ok"] == all(v["ok"] for v in s["by_prior"].values())
    assert g["lessons"][0]["passes"]  # a clear effect passes under all three


def test_extreme_prior_vetoes(rows: list[dict]) -> None:
    """One prior that rules effects out is enough to reject every lesson."""
    pri = {"sceptical": A.PRIORS["sceptical"], "veto": {"mean": -0.2, "sd": 0.002}}
    f = A.fit_priors(rows, LESSONS, priors=pri, n_draws=200, seed=0, eb=False)
    g = A.gate_priors(f, LESSONS, RULES)
    assert "L0" in g["by_prior"]["sceptical"]["passing"]
    assert g["by_prior"]["veto"]["passing"] == []
    assert not any(p["passes"] for p in g["lessons"])
    assert g["shortlist"] == [] and g["advanced"] == [] and g["subsets"] == []


def _with_rd(fit: tuple[dict, dict], li: int, centre: float) -> tuple[dict, dict]:
    succ, harm = copy.copy(fit[0]), fit[1]
    rng = np.random.default_rng(7)
    rd = succ["rd"].copy()
    rd[:, li] = rng.normal(centre, 0.003, rd.shape[0])
    rdc = succ["rdc"].copy()
    rdc[:, li, :] = rd[:, li][:, None]
    succ.update(rd=rd, rdc=rdc)
    return succ, harm


def test_lesson_passing_only_under_weak_prior_is_rejected(fits: dict) -> None:
    """L1 clears E1 under the weak prior only (posterior RD > 1 point there, below it
    under the sceptical and literature priors): it is not passed, shortlisted or advanced."""
    crafted = {"sceptical": _with_rd(fits["sceptical"], 1, 0.006),
               "weak": _with_rd(fits["weak"], 1, 0.02),
               "literature": _with_rd(fits["literature"], 1, 0.004)}
    g = A.gate_priors(crafted, LESSONS, RULES, primary="sceptical")
    l1 = next(p for p in g["lessons"] if p["id"] == "L1")
    assert l1["passes_by_prior"] == {"sceptical": False, "weak": True, "literature": False}
    assert not l1["passes"] and not l1["checks"]["E1"]
    assert "L1" in g["by_prior"]["weak"]["passing"]
    assert "L1" not in g["shortlist"] and "L1" not in g["advanced"]
    assert all("L1" not in s["lessons"] for s in g["subsets"])
    assert next(r for r in g["table"] if r["id"] == "L1") == {
        "id": "L1", "sceptical": False, "weak": True, "literature": False, "final": False}


def test_single_prior_gate_shape(fits: dict) -> None:
    g = A.gate(*fits["sceptical"], LESSONS, RULES)
    assert set(g) == {"lessons", "shortlist", "subsets", "advanced", "sequencing_candidate",
                      "rules"}
    assert "by_prior" not in g["lessons"][0]


def test_simulation_reports_per_prior() -> None:
    small = {c: 4 for c in SIM.CONTEXTS}
    r = SIM.simulate_once("null", prefixes=small, n_lessons=4, draws=4, seed=3, n_draws=40)
    assert set(r["by_prior"]) == set(A.PRIORS)
    s = SIM.summarize([r], n_lessons=4)["null"]
    assert set(s["by_prior"]) == set(A.PRIORS) and "p_any_advanced" in s["by_prior"]["weak"]
    # the intersection never advances more than any single prior
    for pr in A.PRIORS:
        assert s["p_any_advanced"] <= s["by_prior"][pr]["p_any_advanced"] or not r["advanced"]
