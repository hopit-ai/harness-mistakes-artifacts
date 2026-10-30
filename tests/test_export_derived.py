"""tools/export_derived.py on synthetic inputs: the exported tables give the same analysis as
the originals, and only the listed columns leave."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

from paper1 import _io
from paper1.bfcl import confirm as C
from paper1.bfcl import plan_min as PM
from paper1.fgate import analysis as A
from paper1.fgate import pool as fp
from tests.test_fgate_priors import _rows

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import export_derived as X  # noqa: E402


def _pool(n: int = 4) -> dict:
    lessons = [{"id": f"L{k}", "intent": "x", "task": "address", "tools": ["t"],
                "text": f"- lesson {k}", "sha256": hashlib.sha256(f"- lesson {k}".encode()).hexdigest()}
               for k in range(n)]
    body = {"schema": fp.POOL_SCHEMA, "lessons": lessons}
    body["sha256"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    return body


def test_tau2_export_keeps_the_analysis_and_drops_other_columns(tmp_path):
    rows = _rows(0.5, n_prefix=40)
    for k, r in enumerate(rows):
        r.update({"group": r["case_id"] + "-g", "unit_id": f"u{k}", "messages": ["secret"],
                  "gold": {"k": 1}})
    rows.append({"track": "c-collect", "case_id": "zz", "messages": ["private"]})
    (tmp_path / "table.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    _io.write_json(tmp_path / "pool.json", _pool())
    assert X.main(["tau2-gate", "--table", str(tmp_path / "table.jsonl"), "--pool",
                   str(tmp_path / "pool.json"), "--out", str(tmp_path / "d")]) == 0
    out = _io.read_jsonl(tmp_path / "d/tau2-fgate-table.jsonl")
    assert len(out) == len(rows) - 1
    assert all(set(r) <= set(X.TAU2_FIELDS) for r in out)
    assert not ({r["case_id"] for r in out} & {r["case_id"] for r in rows})
    pool = fp.verify_pool(_io.read_json(tmp_path / "d/tau2-fgate-pool.json"))
    a = A.fit_outcome([r for r in rows if r["track"] == "fgate"], "y", pool["lessons"],
                      n_draws=200, seed=0)
    b = A.fit_outcome(out, "y", pool["lessons"], n_draws=200, seed=0)
    assert np.allclose(a["rd"], b["rd"])
    from paper1.fgate import rbc as R

    ra = R.rbc([r for r in rows if r["track"] == "fgate"], pool["lessons"], boot=50)
    rb = R.rbc(out, pool["lessons"], boot=50)
    assert ra["selected"] == rb["selected"] and ra["lessons"] == rb["lessons"]


def _h3(tmp_path: Path) -> tuple[Path, Path]:
    cells = []
    for arm in ("B1", "SEARCH", "UNGATED"):
        for trial in range(2):
            cells.append({"cell_id": f"h3-{arm}-t{trial}", "arm": arm, "trial": trial,
                          "units": [{"instance": f"multi_turn_{c}_{r}"}
                                    for r in range(6) for c in ("base", "long_context")]})
    plan = PM.seal({"handoff": "h3", "cells": cells, "empty_arms": ["FPRIME"]})
    pkg, exp = tmp_path / "pkg", tmp_path / "exp"
    _io.write_json(pkg / "plan.json", plan)
    ident = {"plan_sha256": plan["sha256"], "mode": "full"}
    _io.write_json(exp / "run/identity.json", ident)
    _io.write_json(exp / "manifest.json", {"plan_sha256": plan["sha256"], "handoff": "h3",
                                           "halted_cells": [], "identity": ident})
    rng = np.random.default_rng(1)
    for c in cells:
        p = exp / "cells" / c["cell_id"] / "outcomes.jsonl"
        p.parent.mkdir(parents=True)
        p.write_text("".join(json.dumps({"cell_id": c["cell_id"], "instance": u["instance"],
                                         "success": int(rng.random() < 0.5), "harm": 0,
                                         "trajectory": ["not exported"]}) + "\n"
                             for u in c["units"]))
    return pkg, exp


def test_h3_export_matches_load_export(tmp_path):
    pkg, exp = _h3(tmp_path)
    assert X.main(["bfcl-h3", "--package", str(pkg), "--export", str(exp), "--out",
                   str(tmp_path / "d")]) == 0
    rows = _io.read_jsonl(tmp_path / "d/bfcl-h3-rows.jsonl")
    meta = _io.read_json(tmp_path / "d/bfcl-h3-meta.json")
    assert len(rows) == 72 and meta["empty_arms"] == ["FPRIME"]
    assert all(set(r) == {"arm", "trial", "instance", "root", "category", "success", "harm"}
               for r in rows)
    got = C.analyse(rows, empty_arms=meta["empty_arms"])
    ref = C.analyse(C.load_export(pkg, exp)["rows"], empty_arms=["FPRIME"])
    assert got["registered_family"] == ref["registered_family"]
