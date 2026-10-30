"""F' gate E3 (context harm): the threshold and the optional per-context harm bound."""

from __future__ import annotations

import copy
import itertools

import numpy as np
import pytest

from paper1.fgate import analysis as A
from paper1.fgate import simulate as SIM
from tests.test_fgate_priors import LESSONS, RULES, _rows


@pytest.fixture(scope="module")
def fit() -> tuple[dict, dict]:
    f = A.fit_priors(_rows(0.5), LESSONS, n_draws=400, seed=0, eb=False)
    return f["sceptical"]


def _ctx(fit: tuple[dict, dict], li: int, ctx: int, centre: float, sd: float
         ) -> tuple[dict, dict]:
    """L``li`` clearly helps overall (RD ~ +4 points) but RD_lc in context ``ctx`` is
    N(centre, sd)."""
    succ = copy.copy(fit[0])
    rng = np.random.default_rng(11)
    rd, rdc = succ["rd"].copy(), succ["rdc"].copy()
    rd[:, li] = rng.normal(0.04, 0.003, rd.shape[0])
    rdc[:, li, :] = rd[:, li][:, None]
    rdc[:, li, ctx] = rng.normal(centre, sd, rd.shape[0])
    succ.update(rd=rd, rdc=rdc)
    return succ, fit[1]


def _e3(fit: tuple[dict, dict], over: dict) -> bool:
    per = A.lesson_checks(*fit, LESSONS, {**RULES, **over})
    return per[0]["checks"]["E3"]


def test_threshold_catches_moderate_context_harm(fit: tuple[dict, dict]) -> None:
    # P(RD_lc < -1 point) ~ 0.69: passes the old 0.80 bar, rejected at 0.50
    f = _ctx(fit, 0, 1, -0.015, 0.01)
    assert _e3(f, SIM.E3_CANDIDATES["p80"])
    assert not _e3(f, SIM.E3_CANDIDATES["p50"])
    assert not _e3(f, {})  # the registered rule (A.RULES) rejects it


def test_bound_rejects_wide_downside(fit: tuple[dict, dict]) -> None:
    # P(RD_lc < -1) ~ 0.37 (< 0.50) but P(RD_lc > -2.5) ~ 0.91 (< 0.95): only the bound bites
    f = _ctx(fit, 0, 1, -0.005, 0.015)
    assert _e3(f, SIM.E3_CANDIDATES["p50"])
    assert not _e3(f, SIM.E3_CANDIDATES["p50_bound"])
    per = A.lesson_checks(*f, LESSONS, {**RULES, **SIM.E3_CANDIDATES["p50_bound"]})[0]
    assert per["min_p_context_above_bound"] == pytest.approx(0.91, abs=0.05)
    assert per["max_p_context_harm"] == pytest.approx(0.37, abs=0.06)


def test_clean_lesson_passes_every_candidate(fit: tuple[dict, dict]) -> None:
    f = _ctx(fit, 0, 1, 0.04, 0.003)
    for over in SIM.E3_CANDIDATES.values():
        assert _e3(f, over)


def test_simulation_e3_variants_share_fits() -> None:
    small = {c: 4 for c in SIM.CONTEXTS}
    r = SIM.simulate_once("context_harm", prefixes=small, n_lessons=4, draws=4, seed=3,
                          n_draws=40, e3_variants=SIM.E3_CANDIDATES)
    assert set(r["e3_variants"]) == set(SIM.E3_CANDIDATES)
    assert set(r["max_p_context_harm"]) == set(A.PRIORS)
    s = SIM.summarize([r], n_lessons=4)["context_harm"]
    assert set(s["e3_variants"]) == set(SIM.E3_CANDIDATES)
    # a stricter E3 never passes more lessons than a laxer one on the same fits
    order = ["p80", "p70", "p50", "p30", "p20", "p10"]
    for lax, strict in itertools.pairwise(order):
        assert set(r["e3_variants"][strict]["passes"]) <= set(r["e3_variants"][lax]["passes"])


def test_registered_e3_rule() -> None:
    """Pre-registered 2026-10-19 (plan s. 3.5): P(RD_lc < -1 point) < 0.10 in every
    context, no extra bound."""
    assert A.RULES["p_context_harm"] == 0.10 and A.RULES["context_harm_delta"] == -0.01
    assert A.RULES.get("context_harm_bound") is None
    assert {**A.RULES, **SIM.E3_CANDIDATES["p10"]} == A.RULES
