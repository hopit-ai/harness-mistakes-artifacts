"""Audited F' sensitivity (bfcl-plan s. 6.4) on synthetic tables: never touches the primary."""

from __future__ import annotations

import copy
import hashlib
import json

import numpy as np
import pytest

from paper1.bfcl import data
from paper1.bfcl import fprime as F
from paper1.bfcl import plan_min as P
from paper1.bfcl import audited as A

N_LESSONS = 3


def _pool() -> dict:
    return P.make_pool("U", [f"- WHEN situation U{k} arises THEN do thing {k}"
                             for k in range(N_LESSONS)],
                       provenance={"evidence_roles": ["discovery"]})


def _rows(seed: int = 0, roots: int = 24, draws: int = 6) -> list[dict]:
    rng = np.random.default_rng(seed)
    fams = data.FAMILY_ORDER
    rows = []
    for root in range(roots):
        for cat in data.PRIMARY:
            inst = f"multi_turn_{cat}_{root}"
            vecs = ["0" * N_LESSONS] + [format(k % 7 + 1, f"0{N_LESSONS}b") for k in range(draws)]
            for d, x in enumerate(vecs):
                y = rng.random() < 0.45 + (0.25 if x[0] == "1" else 0.0)
                rows.append({"track": "fgate", "case_id": inst, "root": root, "category": cat,
                             "context": fams[root % len(fams)], "x": x, "y": int(y),
                             "harm": int(not y and rng.random() < 0.2), "reask": 0,
                             "error_class": None,
                             "cell_id": "h2-gate-anchor-t0" if d == 0 else f"h2-gate-U-d{d:02d}"})
    return rows


def _defects_file(tmp_path, labels):
    defects = [lab for lab in labels if A.is_defective(lab)]
    doc = {"part": "gate", "rubric": "v2", "defects": defects, "labels": labels}
    path = tmp_path / "gate-defects.json"
    path.write_text(json.dumps(doc, sort_keys=True))
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def _labels():
    labs = []
    for root, cat, sc, sev in [(0, "base", "yes", "clear"), (0, "long_context", "yes", "clear"),
                               (1, "base", "yes", "clear"), (2, "base", "yes", "arguable"),
                               (3, "long_context", "no", None)]:
        labs.append({"instance": f"multi_turn_{cat}_{root}", "root": root, "category": cat,
                     "role": "gate", "score_changing": sc, "severity": sev})
    return labs


def test_defect_list_rule_sha_and_dropped_roots(tmp_path):
    path, sha = _defects_file(tmp_path, _labels())
    d = A.load_defects(path, expected_sha256=sha)
    assert d["instances"] == ["multi_turn_base_0", "multi_turn_base_1",
                              "multi_turn_long_context_0"]       # arguable / "no" kept
    assert d["roots_dropped"] == [0]
    with pytest.raises(A.Refused):
        A.load_defects(path, expected_sha256="0" * 64)
    doc = json.loads(path.read_text())
    doc["defects"] = doc["defects"][:1]                           # list != rule over labels
    path.write_text(json.dumps(doc))
    with pytest.raises(A.Refused):
        A.load_defects(path, expected_sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def test_real_frozen_list_matches_its_registry_row():
    # The shipped lists are redacted copies (reviewer file names); REDACTION.json binds each
    # to the frozen hash recorded in its registry row (gate: ee8a020c..., test: dbe63196...).
    from paper1 import DATA

    red = {f["file"]: f for f in json.loads((DATA / "bfcl-audit/REDACTION.json").read_text())["files"]}
    d = A.load_defects()
    assert len(d["instances"]) == 42 and d["sha256"] == red["gate-defects.json"]["redacted_sha256"]
    assert red["gate-defects.json"]["frozen_sha256"].startswith("ee8a020c")
    t = A.load_defects(DATA / "bfcl-audit/test-defects.json", part="test")
    assert len(t["instances"]) == 146 and len(t["roots_dropped"]) == 68
    assert red["test-defects.json"]["frozen_sha256"].startswith("dbe63196")


def test_refit_drops_defective_rows_and_leaves_the_primary_identical(tmp_path):
    rows, pool = _rows(), _pool()
    path, sha = _defects_file(tmp_path, _labels())
    defects = A.load_defects(path, expected_sha256=sha)
    before = F.analyse(copy.deepcopy(rows), pool, n_draws=200, sensitivities=False)
    snapshot = copy.deepcopy(rows)
    rep = A.sensitivity(rows, pool, defects, primary=before, n_draws=200)
    after = F.analyse(copy.deepcopy(rows), pool, n_draws=200, sensitivities=False)
    assert json.dumps(before, sort_keys=True, default=float) == \
        json.dumps(after, sort_keys=True, default=float)          # primary unchanged
    assert rows == snapshot                                        # input not mutated
    assert rep["use"] == A.USE and rep["schema"] == A.SCHEMA and "advanced" not in rep
    per_inst = 1 + 6
    assert rep["dropped"]["rows"] == 3 * per_inst
    assert rep["refit"]["rows"] == len(rows) - 3 * per_inst
    assert rep["refit"]["instances"] == 24 * 2 - 3
    assert rep["dropped"]["roots_with_both_instances"] == [0]
    # the refit equals the registered analysis on the kept rows (no other change)
    kept = [r for r in rows if r["case_id"] not in set(defects["instances"])]
    direct = F.analyse(kept, pool, n_draws=200, sensitivities=False)
    for p in direct["gate"]["lessons"]:
        assert rep["lessons"][p["id"]]["audited"]["rd_mean"] == p["rd_mean"]
        assert rep["lessons"][p["id"]]["audited"]["passes"] == p["passes"]
    assert rep["refit"]["advanced_descriptive"] == direct["gate"]["advanced"]
    for p in before["gate"]["lessons"]:
        assert rep["lessons"][p["id"]]["primary"]["rd_mean"] == p["rd_mean"]
    desc = rep["defective_only_descriptive"]
    assert desc["B1_anchor"]["episodes"] == 3 and desc["draws_pool_U"]["episodes"] == 18


def test_cli_writes_its_own_file_and_never_a_primary(tmp_path, monkeypatch):
    rows, pool = _rows(1), _pool()
    path, sha = _defects_file(tmp_path, _labels())
    real = A.load_defects
    monkeypatch.setattr(A, "load_defects", lambda p: real(p, expected_sha256=sha))
    table = tmp_path / "TABLE-U.jsonl"
    table.write_text("".join(json.dumps(r) + "\n" for r in rows))
    pool_f = tmp_path / "POOL-U.json"
    pool_f.write_text(json.dumps(pool))
    prim = F.analyse(rows, pool, n_draws=100, sensitivities=False)
    prim_f = tmp_path / "FPRIME-U.json"
    prim_f.write_text(json.dumps(prim, indent=1, default=float))
    prim_bytes = prim_f.read_bytes()
    base = ["sensitivity", "--table", str(table), "--pool", str(pool_f), "--primary",
            str(prim_f), "--defects", str(path), "--draws", "100"]
    assert A.main([*base, "--out", str(prim_f)]) == 4             # input / primary refused
    other = tmp_path / "other-primary.json"
    other.write_text(json.dumps({"schema": F.REPORT_SCHEMA}))
    assert A.main([*base, "--out", str(other)]) == 4              # never overwrite a primary
    out = tmp_path / "AUDITED-U.json"
    assert A.main([*base, "--out", str(out)]) == 0
    assert A.main([*base, "--out", str(out)]) == 0                # rerun replaces its own file
    rep = json.loads(out.read_text())
    assert rep["use"] == A.USE and "advanced" not in rep
    assert prim_f.read_bytes() == prim_bytes



def test_primary_is_tied_to_the_table(tmp_path, monkeypatch):
    rows, pool = _rows(2), _pool()
    path, sha = _defects_file(tmp_path, _labels())
    real = A.load_defects
    monkeypatch.setattr(A, "load_defects", lambda p: real(p, expected_sha256=sha))
    table = tmp_path / "TABLE-U.jsonl"
    table.write_text("".join(json.dumps(r) + "\n" for r in rows))
    pool_f = tmp_path / "POOL-U.json"
    pool_f.write_text(json.dumps(pool))
    other_rows = [r for r in rows if r["root"] != 23]          # another table
    stale = F.analyse(other_rows, pool, n_draws=100, sensitivities=False)
    stale_f = tmp_path / "FPRIME-stale.json"
    stale_f.write_text(json.dumps(stale, default=float))
    base = ["sensitivity", "--table", str(table), "--pool", str(pool_f), "--defects",
            str(path), "--draws", "100"]
    assert A.main([*base, "--primary", str(stale_f), "--out", str(tmp_path / "a.json")]) == 4
    good = F.analyse(rows, pool, n_draws=100, sensitivities=False)
    good_f = tmp_path / "FPRIME-U.json"
    good_f.write_text(json.dumps({**good, "table_sha256": "0" * 64}, default=float))
    assert A.main([*base, "--primary", str(good_f), "--out", str(tmp_path / "b.json")]) == 4
    good_f.write_text(json.dumps(good, default=float))
    out = tmp_path / "c.json"
    assert A.main([*base, "--primary", str(good_f), "--out", str(out)]) == 0
    rep = json.loads(out.read_text())
    assert rep["table_sha256"] == hashlib.sha256(table.read_bytes()).hexdigest()
    assert rep["weighting"] == A.WEIGHTING and "half the weight" in rep["weighting"]
    exp = rep["lessons"]["U01"]["audited_exposure_by_family"]
    assert set(exp) <= set(data.FAMILY_ORDER) and all(v > 0 for v in exp.values())
