"""EXPLORATORY, post hoc (owner-approved 2026-10-22): is S01's BFCL gain a scorer artefact?

Never alters a registered result or file: it reads a package, a scored run folder and its
export, and writes only to the paths given with ``--out``. Report:
docs/xp/bfcl-s01-exploratory-2026-10-22.md.

    # 1. re-score (benchmark environment: bfcl-eval installed; CPU only, minutes)
    BPY=/path/to/bfcl-venv/bin/python
    PYTHONPATH=. $BPY -m paper1.bfcl.s01_explore rescore \
        --package PKG --run W/runs/bfcl-h2 --out W/xp-s01/rescore.jsonl
    # 2. analyse (numpy only)
    PYTHONPATH=. $BPY -m paper1.bfcl.s01_explore analyse \
        --package PKG --run W/runs/bfcl-h2 --export W/export-bfcl-h2 \
        --rescore W/xp-s01/rescore.jsonl --aen-pairs AEN/pairs.json \
        --aen-mutators AEN/mutator_map.json --out W/xp-s01/report.json

**Re-score variants** (each episode's stored ``result`` replayed through the official
``_evaluate_single_multi_turn_entry``, as ``runner.score_cell`` does, under a fresh model
name per variant so the official backends never share state):

- ``official``: unchanged; must reproduce the stored verdict (checked, ``mismatch`` count);
- ``cwd``: the state check also compares the file system's working directory
  (``GorillaFileSystem._current_dir``, skipped by ``_compare_instances`` because it is
  private; gorilla #1377, finding "multi-turn state comparison ignores the working
  directory");
- ``nopwd``: every ``pwd`` call removed from the trajectory, official checker. ``pwd`` is
  read-only, so this changes only (i) whether a turn counts as empty
  (``empty_turn_model_response``) and (ii) whether a ground-truth ``pwd`` result is found
  by the response check: the direct scorer credit of the pwd calls themselves.

**Turn-level "act"** (arXiv:2610.04429, "Asking Earns Nothing", release
YangzeLiu/asking-earns-nothing @7f20cf1, ``pairs_package``): on a scored twin pair's base
anchor turn, did the model attempt at least one world-changing call (``mutator_map.json``
labels; login/logout excluded; ``echo`` counts only with a file name; names validated
against the item's tool list). Only the ``act`` half applies: the hold half needs the
miss_func/miss_param twins, which no hand-off runs. Applied to the base instances whose
root has scored pairs; the long-context sibling is scored at the same turn as an
extension (labelled). Episode outcome ``act`` = acted on every distinct anchor turn.

**Designs.** ``h2`` (F' randomized inclusion): effects by ``slh.xp.bfcl.fprime``'s
registered estimator (``fgate.analysis.fit_outcome``, RD prior 5 points, EB grid) with the
outcome swapped; S01 minimal pairs (same instance, same other lessons, S01 flipped; the
``1000`` vector pairs with the shared anchor) for transitions and flips. ``h3`` (fixed
arms): every arm vs B1, root-weighted, paired by root, cluster bootstrap over roots
(10,000, seed 20261018, as ``slh.xp.bfcl.confirm``), with trial-matched episode pairs for
transitions and flips; arms whose notes contain S01 are flagged.
"""

from __future__ import annotations

import argparse
import collections
import copy
import json
import os
import random
import sys
from pathlib import Path
from typing import Any

S01_KEY = "call pwd to determine the current working directory"
VARIANTS = ("official", "cwd", "nopwd")
CLASSES = ("success", "empty_turn", "state_mismatch", "response_mismatch",
           "force_terminated", "inference_error", "other")
LABEL = "EXPLORATORY - post hoc, owner-approved 2026-10-22, does not change any registered result"


# --------------------------------------------------------------------------- reading


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def load_plan(package: Path) -> dict[str, Any]:
    return json.loads((package / "plan.json").read_text())


def cell_notes(plan: dict[str, Any]) -> dict[tuple[str, str], str]:
    out = {}
    for c in plan["cells"]:
        for u in c["units"]:
            out[(c["cell_id"], u["instance"])] = plan["notes"].get(u.get("notes_sha256") or "", "")
    return out


def results(run: Path, plan: dict[str, Any]) -> dict[tuple[str, str], Any]:
    """(cell, instance) -> the stored BFCL ``result`` (list of turns of steps)."""
    out = {}
    for c in plan["cells"]:
        p = run / "cells" / c["cell_id"] / "results.jsonl"
        if not p.is_file():
            continue
        for line in p.read_text().splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:  # torn tail: not a row (as runner.read_results)
                continue
            out[(c["cell_id"], r["id"])] = r["result"]
    return out


def turn_calls(turn: Any) -> list[tuple[str, dict[str, Any]]]:
    """Native function-calling steps only: [(name, args)] in order."""
    out = []
    for step in turn if isinstance(turn, list) else []:
        if isinstance(step, list):
            for c in step:
                if isinstance(c, dict):
                    for name, raw in c.items():
                        try:
                            args = json.loads(raw) if isinstance(raw, str) else (raw or {})
                        except json.JSONDecodeError:
                            args = {}
                        out.append((name, args if isinstance(args, dict) else {}))
    return out


def strip_pwd(result: Any) -> Any:
    if not isinstance(result, list):
        return result
    out = []
    for turn in result:
        nt = []
        for step in turn:
            if isinstance(step, list):
                nt.append([c for c in step if not (isinstance(c, dict) and "pwd" in c)])
            else:
                nt.append(step)
        out.append(nt)
    return out


def fclass(valid: bool, etype: str | None) -> str:
    if valid:
        return "success"
    return {"multi_turn:empty_turn_model_response": "empty_turn",
            "multi_turn:instance_state_mismatch": "state_mismatch",
            "multi_turn:execution_response_mismatch": "response_mismatch",
            "multi_turn:force_terminated": "force_terminated",
            "multi_turn:inference_error": "inference_error"}.get(etype or "", "other")


# --------------------------------------------------------------------------- re-score


def _cwd_path(fs: Any) -> str:
    path, d = [], getattr(fs, "_current_dir", None)
    while d is not None and d is not fs.root:
        path.append(d.name)
        d = d.parent
    return "/" + "/".join(reversed(path))


def _install_cwd_patch(enabled: dict[str, bool]) -> None:
    """``_compare_instances`` plus the working directory, only while ``enabled['cwd']``."""
    from bfcl_eval.eval_checker.multi_turn_eval import multi_turn_checker as MC

    orig = MC._compare_instances

    def compare(model_obj: Any, gt_obj: Any) -> tuple[bool, dict[str, Any]]:
        valid, diff = orig(model_obj, gt_obj)
        if enabled["cwd"] and hasattr(gt_obj, "_current_dir") and hasattr(gt_obj, "root"):
            m, g = _cwd_path(model_obj), _cwd_path(gt_obj)
            if m != g:
                valid = False
                diff = {**diff, "_current_dir": {"model": m, "ground_truth": g}}
        return valid, diff

    MC._compare_instances = compare


def _clear_backends(keep: set[str]) -> None:
    from bfcl_eval.eval_checker.multi_turn_eval import multi_turn_utils as MU

    for k in [k for k in vars(MU) if k not in keep]:
        del vars(MU)[k]


def rescore(package: Path, run: Path, out: Path, variants: tuple[str, ...],
            work: Path, cells: set[str] | None = None) -> dict[str, Any]:
    from bfcl_eval.eval_checker.multi_turn_eval import multi_turn_utils as MU

    from paper1.bfcl import data
    from slh.xp.bfcl import handler as H  # public kit (hopit-ai/self-learning-harness-kit), only to read raw hand-off files
    from slh.xp.bfcl.runner import FakeClient  # public kit (hopit-ai/self-learning-harness-kit), only to read raw hand-off files

    os.environ["BFCL_PROJECT_ROOT"] = str(work)
    work.mkdir(parents=True, exist_ok=True)
    plan = load_plan(package)
    res = results(run, plan)
    if cells:
        res = {k: v for k, v in res.items() if k[0] in cells}
    stored = {}
    for c in plan["cells"]:
        p = run / "cells" / c["cell_id"] / "verdicts.jsonl"
        if p.is_file():
            for v in _jsonl(p):
                stored[(c["cell_id"], v["id"])] = v["verdict"]
    cats = sorted({data.parse_instance(i)[1] for _, i in res})
    prompts, answers = {}, {}
    for cat in cats:
        p, a = H.load_entries(cat)
        prompts.update(p)
        answers.update(a)
    enabled = {"cwd": False}
    _install_cwd_patch(enabled)
    keep = set(vars(MU))
    h = H.build_handler(served_model=plan["served_model"], registry_name="slh-xp-s01",
                        base_url="http://127.0.0.1:9/v1", temperature=0.001,
                        client=FakeClient())
    n, mismatch = 0, 0
    with out.open("w") as f:
        for inst in sorted({i for _, i in res}):
            gt = answers[inst]["ground_truth"]
            names = [[c.split("(", 1)[0].strip() for c in t] for t in gt]
            f.write(json.dumps({"kind": "gt", "instance": inst, "turn_calls": names}) + "\n")
        for k, ((cell, inst), result) in enumerate(sorted(res.items())):
            row: dict[str, Any] = {"kind": "episode", "cell_id": cell, "instance": inst}
            for var in variants:
                enabled["cwd"] = var == "cwd"
                r = strip_pwd(result) if var == "nopwd" else result
                v = H.score_entry(h, {"id": inst, "result": copy.deepcopy(r)}, prompts[inst],
                                  answers[inst], model_name=f"xs01_{var}_{k}")
                err = v.get("error") or {}
                et = None if v.get("valid") else (err.get("error_type") or v.get("error_type"))
                row[var] = {"valid": bool(v.get("valid")), "error_type": et}
                _clear_backends(keep)
            enabled["cwd"] = False
            sv = stored.get((cell, inst))
            if sv is not None and "official" in row:
                row["stored_valid"] = bool(sv.get("valid"))
                mismatch += row["stored_valid"] != row["official"]["valid"]
            f.write(json.dumps(row) + "\n")
            n += 1
    return {"episodes": n, "variants": list(variants), "official_vs_stored_mismatch": mismatch}


# --------------------------------------------------------------------------- AEN act


class Act:
    """The ``act`` half of arXiv:2610.04429's turn-level scorer, on our trajectories."""

    def __init__(self, pairs_path: Path, mutators_path: Path) -> None:
        man = json.loads(pairs_path.read_text())
        fn = json.loads(mutators_path.read_text())["functions"]
        self.mutate = {n for n, v in fn.items() if v["label"] == "mutate"}
        self.toolsets = man["toolsets"]
        self.anchors: dict[int, set[int]] = collections.defaultdict(set)
        self.tools: dict[int, set[str]] = {}
        for p in man["pairs"]:
            if not p.get("scored"):
                continue
            root = int(p["base_id"].rsplit("_", 1)[1])
            self.anchors[root].add(int(p["anchor_turn"]))
            self.tools[root] = set(self.toolsets[p["base_tools"]])

    def is_mut(self, name: str, args: dict[str, Any]) -> bool:
        if name == "echo":
            return "file_name" in args
        return name in self.mutate

    def episode(self, root: int, result: Any) -> dict[str, Any] | None:
        if root not in self.anchors or not isinstance(result, list):
            return None
        per = {}
        for t in sorted(self.anchors[root]):
            calls = turn_calls(result[t]) if t < len(result) else []
            per[t] = int(any(self.is_mut(n, a) for n, a in calls if n in self.tools[root]))
        return {"turns": per, "act": int(all(per.values()))}


# --------------------------------------------------------------------------- features


def episode_features(result: Any, gt_names: list[list[str]] | None) -> dict[str, Any]:
    turns = result if isinstance(result, list) else []
    pwd_turns, pwd_only, pwd_only_gt_nonempty, pwd_on_gt_pwd = [], [], [], []
    n_pwd = 0
    for t, turn in enumerate(turns):
        names = [n for n, _ in turn_calls(turn)]
        k = names.count("pwd")
        n_pwd += k
        if not k:
            continue
        pwd_turns.append(t)
        gtn = gt_names[t] if gt_names and t < len(gt_names) else []
        if len(names) == k:
            pwd_only.append(t)
            if gtn:
                pwd_only_gt_nonempty.append(t)
        if "pwd" in gtn:
            pwd_on_gt_pwd.append(t)
    return {"n_pwd": n_pwd, "pwd_turns": pwd_turns, "pwd_only_turns": pwd_only,
            "pwd_only_gt_nonempty": pwd_only_gt_nonempty, "pwd_on_gt_pwd_turn": pwd_on_gt_pwd}


# --------------------------------------------------------------------------- statistics


def boot_mean_ci(vals_by_cluster: dict[Any, list[float]], *, reps: int = 10000,
                 seed: int = 20261018) -> dict[str, float]:
    """Mean over clusters of the cluster mean; percentile 90% and 95% intervals."""
    import numpy as np

    keys = sorted(vals_by_cluster, key=str)
    m = np.array([float(np.mean(vals_by_cluster[k])) for k in keys])
    if len(m) == 0:
        return {"mean": float("nan"), "n_clusters": 0}
    rng = np.random.default_rng(seed)
    b = m[rng.integers(0, len(m), (reps, len(m)))].mean(1)
    return {"mean": float(m.mean()), "ci90": [float(np.percentile(b, 5)), float(np.percentile(b, 95))],
            "ci95": [float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))],
            "n_clusters": len(m)}


def fprime_effects(plan: dict[str, Any], ep: dict[tuple[str, str], dict[str, Any]],
                   outcome: str, pool_name: str, *, n_draws: int,
                   keep: Any = None) -> dict[str, Any] | None:
    """Registered F' estimator (``fit_outcome`` as ``fprime.analyse``) on another outcome."""
    import numpy as np

    from paper1.bfcl import fprime as F
    from paper1.fgate import analysis as A

    outs = {}
    for k, e in ep.items():
        y = e["y"].get(outcome)
        if y is None:
            continue
        outs[k] = {"success": bool(y), "harm": False, "inaction": False,
                   "inference_error": e["inference_error"]}
    rows = F.table(plan, outs, pool_name)
    if keep is not None:
        rows = [r for r in rows if keep(r)]
    if len({r["case_id"] for r in rows}) < 4:
        return None
    lessons = plan["pools"][pool_name]["lessons"]
    fit = A.fit_outcome(rows, "y", lessons, n_draws=n_draws, seed=0, rd_prior_sd=F.RD_PRIOR_SD)
    rd = fit["rd"]
    return {"rows": len(rows), "instances": len({r["case_id"] for r in rows}),
            "mean_y": float(np.mean([r["y"] for r in rows])),
            "lessons": {les["id"]: {"rd_mean": round(float(rd[:, j].mean()), 4),
                                    "ci90": [round(float(np.percentile(rd[:, j], 5)), 4),
                                             round(float(np.percentile(rd[:, j], 95)), 4)],
                                    "p_gt_0": round(float((rd[:, j] > 0).mean()), 3)}
                        for j, les in enumerate(lessons)}}


# --------------------------------------------------------------------------- analysis


def build_episodes(plan, run, export, rescore_rows, act: Act | None):
    from paper1.bfcl import data

    res = results(run, plan)
    notes = cell_notes(plan)
    arm_of = {c["cell_id"]: c for c in plan["cells"]}
    gt = {r["instance"]: r["turn_calls"] for r in rescore_rows if r["kind"] == "gt"}
    rs = {(r["cell_id"], r["instance"]): r for r in rescore_rows if r["kind"] == "episode"}
    outcomes = {}
    for p in sorted(Path(export).glob("cells/*/outcomes.jsonl")):
        for o in _jsonl(p):
            outcomes[(o["cell_id"], o["instance"])] = o
    ep = {}
    for key, result in res.items():
        cell, inst = key
        o = outcomes.get(key)
        if o is None:
            continue
        root, cat = data.parse_instance(inst)
        y = {"official": int(o["success"])}
        cls = {"official": fclass(o["success"], o["error_type"])}
        r = rs.get(key)
        for var in VARIANTS[1:]:
            if r and var in r:
                y[var] = int(r[var]["valid"])
                cls[var] = fclass(r[var]["valid"], r[var]["error_type"])
        a = act.episode(root, result) if act else None
        if a is not None:
            y["act_base" if cat == "base" else "act_lc"] = a["act"]
            y["act_all"] = a["act"]
        c = arm_of[cell]
        ep[key] = {"cell_id": cell, "instance": inst, "root": root, "category": cat,
                   "arm": c.get("arm"), "trial": c.get("trial"),
                   "s01": S01_KEY in notes.get(key, ""), "y": y, "cls": cls,
                   "failed_turn": o.get("failed_turn"),
                   "inference_error": bool(o.get("inference_error")),
                   "feat": episode_features(result, gt.get(inst)), "act": a}
    return ep


def h2_pairs(plan, ep):
    """S01 minimal pairs: (off, on) episodes of one instance whose other bits agree."""
    pool = plan["pools"]["S"]
    j = [les["id"] for les in pool["lessons"]].index("S01")
    by: dict[tuple[str, str], tuple[str, str]] = {}
    for c in plan["cells"]:
        for u in c["units"]:
            x = u.get("x") if c["cell_id"].startswith("h2-gate-S-") else (
                "0" * len(pool["lessons"]) if c["purpose"] == "fprime-anchor" else None)
            if x is not None:
                by[(u["instance"], x)] = (c["cell_id"], u["instance"])
    pairs = []
    for (inst, x), key_on in by.items():
        if x[j] != "1":
            continue
        off = x[:j] + "0" + x[j + 1:]
        if (inst, off) in by and by[(inst, off)] in ep and key_on in ep:
            pairs.append((ep[by[(inst, off)]], ep[key_on], x))
    return pairs


def h3_pairs(plan, ep, arm, ref="B1"):
    b1 = {(e["instance"], e["trial"]): e for e in ep.values() if e["arm"] == ref}
    return [(b1[(e["instance"], e["trial"])], e, arm) for e in ep.values()
            if e["arm"] == arm and (e["instance"], e["trial"]) in b1]


def describe_pairs(pairs, *, sample: int, seed: int = 20261022) -> dict[str, Any]:
    trans = collections.Counter((a["cls"]["official"], b["cls"]["official"]) for a, b, _ in pairs)
    up = [(a, b) for a, b, _ in pairs if not a["y"]["official"] and b["y"]["official"]]
    down = [(a, b) for a, b, _ in pairs if a["y"]["official"] and not b["y"]["official"]]
    by_inst: dict[str, list[float]] = collections.defaultdict(list)
    by_root: dict[int, list[float]] = collections.defaultdict(list)
    for a, b, _ in pairs:
        by_inst[b["instance"]].append(b["y"]["official"] - a["y"]["official"])
    for inst, v in by_inst.items():
        by_root[int(inst.rsplit("_", 1)[1])].append(sum(v) / len(v))
    cls_diff = {}
    for cl in CLASSES:
        d: dict[int, list[float]] = collections.defaultdict(list)
        for a, b, _ in pairs:
            d[b["root"]].append(int(b["cls"]["official"] == cl) - int(a["cls"]["official"] == cl))
        cls_diff[cl] = boot_mean_ci(d)
    def flip_note(a, b):
        fb, fa = b["feat"], a["feat"]
        return {"instance": b["instance"], "off_cell": a["cell_id"], "on_cell": b["cell_id"],
                "off_class": a["cls"]["official"], "off_failed_turn": a["failed_turn"],
                "on_pwd_turns": fb["pwd_turns"], "on_pwd_only_turns": fb["pwd_only_turns"],
                "on_pwd_only_gt_nonempty": fb["pwd_only_gt_nonempty"],
                "on_pwd_on_gt_pwd_turn": fb["pwd_on_gt_pwd_turn"],
                "off_pwd_turns": fa["pwd_turns"],
                "on_nopwd_valid": b["y"].get("nopwd"), "on_cwd_valid": b["y"].get("cwd")}
    rng = random.Random(seed)
    samp = rng.sample(up, min(sample, len(up)))
    up_pwd = sum(1 for _, b in up if b["feat"]["n_pwd"])
    up_lost_nopwd = sum(1 for _, b in up if b["y"].get("nopwd") == 0)
    up_lost_cwd = sum(1 for _, b in up if b["y"].get("cwd") == 0)
    up_from = collections.Counter(a["cls"]["official"] for a, _ in up)
    return {"pairs": len(pairs), "up_fail_to_pass": len(up), "down_pass_to_fail": len(down),
            "net_per_pair": (len(up) - len(down)) / max(1, len(pairs)),
            "paired_diff_root_bootstrap": boot_mean_ci(by_root),
            "up_by_off_class": dict(up_from),
            "up_with_pwd_in_on": up_pwd, "up_lost_when_pwd_stripped": up_lost_nopwd,
            "up_lost_under_cwd_check": up_lost_cwd,
            "class_rate_diff_on_minus_off": cls_diff,
            "transitions": {f"{k[0]}->{k[1]}": v for k, v in sorted(trans.items())},
            "flip_sample": [flip_note(a, b) for a, b in samp]}


def pwd_stats(ep_list) -> dict[str, Any]:
    n = len(ep_list)
    def frac(f):
        return round(sum(1 for e in ep_list if f(e)) / n, 4) if n else None
    return {"episodes": n,
            "any_pwd": frac(lambda e: e["feat"]["n_pwd"] > 0),
            "pwd_calls_per_episode": round(sum(e["feat"]["n_pwd"] for e in ep_list) / n, 3) if n else None,
            "has_pwd_only_turn": frac(lambda e: e["feat"]["pwd_only_turns"]),
            "pwd_only_turn_where_gt_nonempty": frac(lambda e: e["feat"]["pwd_only_gt_nonempty"]),
            "pwd_on_turn_whose_gt_has_pwd": frac(lambda e: e["feat"]["pwd_on_gt_pwd_turn"]),
            "official_success": frac(lambda e: e["y"]["official"]),
            "success_but_fails_without_pwd": frac(lambda e: e["y"]["official"] and e["y"].get("nopwd") == 0),
            "success_but_fails_cwd_check": frac(lambda e: e["y"]["official"] and e["y"].get("cwd") == 0),
            "class_rates": {cl: frac(lambda e, cl=cl: e["cls"]["official"] == cl) for cl in CLASSES}}


def analyse(plan, ep, *, n_draws: int, sample: int, ref: str = "B1") -> dict[str, Any]:
    rep: dict[str, Any] = {"label": LABEL, "handoff": plan.get("handoff"),
                           "episodes": len(ep), "plan_sha256": plan.get("sha256")}
    outcomes = ["official", "cwd", "nopwd", "act_base", "act_all"]
    if plan.get("handoff") == "h2" or any(c.get("purpose") == "fprime-anchor" for c in plan["cells"]):
        pairs = h2_pairs(plan, ep)
        rep["design"] = "h2-fprime"
        rep["s01_minimal_pairs"] = describe_pairs(pairs, sample=sample)
        rep["pwd_by_s01"] = {
            "s01_on": pwd_stats([b for _, b, _ in pairs]),
            "s01_off_matched": pwd_stats([a for a, _, _ in pairs]),
            "pool_S_on_all": pwd_stats([e for e in ep.values() if e["s01"]]),
            "pool_S_off_all": pwd_stats([e for e in ep.values() if not e["s01"]
                                         and (e["cell_id"].startswith("h2-gate-S-")
                                              or e["arm"] == "B1")]),
            "pool_U_all": pwd_stats([e for e in ep.values() if e["cell_id"].startswith("h2-gate-U-")])}
        rep["effects"] = {}
        for pool in plan["pools"]:
            rep["effects"][pool] = {o: fprime_effects(plan, ep, o, pool, n_draws=n_draws)
                                    for o in outcomes}
        # failure classes as outcomes under the registered estimator (S pool)
        for cl in ("empty_turn", "state_mismatch", "response_mismatch", "other"):
            for e in ep.values():
                e["y"][f"cls_{cl}"] = int(e["cls"]["official"] == cl)
            rep["effects"]["S"][f"cls_{cl}"] = fprime_effects(plan, ep, f"cls_{cl}", "S",
                                                              n_draws=n_draws)
        # where the S01 gain sits: families without a file system (no pwd possible) and
        # leave-one-root-out on the official outcome
        rep["s01_sensitivity"] = {
            "non_file_families": fprime_effects(plan, ep, "official", "S", n_draws=n_draws,
                                                keep=lambda r: r["context"] != "files"),
            "files_family_only": fprime_effects(plan, ep, "official", "S", n_draws=n_draws,
                                                keep=lambda r: r["context"] == "files")}
        loo = {}
        for root in sorted({e["root"] for e in ep.values()}):
            f = fprime_effects(plan, ep, "official", "S", n_draws=n_draws,
                               keep=lambda r, root=root: r["root"] != root)
            loo[root] = f["lessons"]["S01"]["rd_mean"] if f else None
        rep["s01_sensitivity"]["leave_one_root_out"] = loo
    else:
        rep["design"] = "h3-arms"
        if not any(e["arm"] == ref for e in ep.values()):
            raise SystemExit(f"reference arm {ref!r} not in the run (use --reference)")
        rep["reference"] = ref
        arms = sorted({e["arm"] for e in ep.values()} - {ref})
        rep["arms"] = {}
        for arm in arms:
            prs = h3_pairs(plan, ep, arm, ref)
            eff = {}
            for o in outcomes:
                d: dict[int, list[float]] = collections.defaultdict(list)
                for a, b, _ in prs:
                    if o in a["y"] and o in b["y"]:
                        d[b["root"]].append(b["y"][o] - a["y"][o])
                eff[o] = boot_mean_ci(d)
            rep["arms"][arm] = {"has_s01": any(e["s01"] for e in ep.values() if e["arm"] == arm),
                                "effects_vs_b1": eff,
                                "pairs": describe_pairs(prs, sample=sample),
                                "pwd": pwd_stats([b for _, b, _ in prs])}
        rep["pwd_reference"] = pwd_stats([e for e in ep.values() if e["arm"] == ref])
    gt_rows = [e for e in ep.values() if e["feat"]["pwd_on_gt_pwd_turn"]]
    rep["n_instances"] = len({e["instance"] for e in ep.values()})
    rep["episodes_with_pwd_on_a_gt_pwd_turn"] = len(gt_rows)
    rep["variant_disagreement"] = {
        v: {"official_pass_variant_fail": sum(1 for e in ep.values() if e["y"]["official"] and e["y"].get(v) == 0),
            "official_fail_variant_pass": sum(1 for e in ep.values() if not e["y"]["official"] and e["y"].get(v) == 1)}
        for v in ("cwd", "nopwd")}
    return rep


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m paper1.bfcl.s01_explore")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("rescore")
    r.add_argument("--package", type=Path, required=True)
    r.add_argument("--run", type=Path, required=True)
    r.add_argument("--out", type=Path, required=True)
    r.add_argument("--variants", default=",".join(VARIANTS))
    r.add_argument("--cells", help="comma-separated cell ids (default: all; for a quick check)")
    r.add_argument("--work", type=Path, help="BFCL project root for the replay (default: next to --out)")
    a = sub.add_parser("analyse")
    a.add_argument("--package", type=Path, required=True)
    a.add_argument("--run", type=Path, required=True)
    a.add_argument("--export", type=Path, required=True)
    a.add_argument("--rescore", type=Path, required=True)
    a.add_argument("--aen-pairs", type=Path)
    a.add_argument("--aen-mutators", type=Path)
    a.add_argument("--draws", type=int, default=1000)
    a.add_argument("--sample", type=int, default=10)
    a.add_argument("--reference", default="B1", help="h3: the no-lesson arm (default B1)")
    a.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    for p in (getattr(args, "out", None),):
        if p is not None and p.resolve().is_relative_to(args.run.resolve()):
            raise SystemExit("refused: --out inside the run folder")
    if args.cmd == "rescore":
        work = args.work or args.out.parent / "bfcl-replay-root"
        print(json.dumps(rescore(args.package, args.run, args.out,
                                 tuple(args.variants.split(",")), work,
                                 set(args.cells.split(",")) if args.cells else None)))
        return 0
    plan = load_plan(args.package)
    act = Act(args.aen_pairs, args.aen_mutators) if args.aen_pairs and args.aen_mutators else None
    ep = build_episodes(plan, args.run, args.export, _jsonl(args.rescore), act)
    rep = analyse(plan, ep, n_draws=args.draws, sample=args.sample, ref=args.reference)
    args.out.write_text(json.dumps(rep, indent=1, default=float))
    print(json.dumps({"episodes": rep["episodes"], "design": rep["design"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
