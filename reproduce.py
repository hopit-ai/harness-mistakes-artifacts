"""Check the paper's key numbers against this release.

    python reproduce.py                 # all checks; writes REPRODUCTION.json
    python reproduce.py --no-figures    # skip the figure rebuild (no matplotlib needed)

Each check says how the number is obtained:

  recomputed   computed here from shipped instance- or decision-level data;
  read         read from a shipped aggregate result file (the file is the registered or
               committed output of the project's analysis; where a registry row records its
               SHA-256, ``python -m paper1.registry files`` verifies it);
  rebuilt      a figure regenerated from shipped data and compared with the paper's figure.

If the derived tables of ``tools/export_derived.py`` are present in ``data/derived/``, the τ²
F' gate and the BFCL held-out confirmation are also recomputed from them (mode ``recomputed``).
Exit status 0 if every check passes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from paper1 import DATA  # noqa: E402
from paper1 import registry as REG  # noqa: E402

RES = DATA / "results"
DERIVED = DATA / "derived"
CHECKS: list[dict[str, Any]] = []


def check(name: str, paper: str, got: str, ok: bool, mode: str, source: str) -> None:
    CHECKS.append({"number": name, "paper": paper, "this_release": got, "ok": bool(ok),
                   "mode": mode, "source": source})


def pts(x: float, nd: int = 1) -> str:
    return f"{100 * x:+.{nd}f}"


def ci(lo: float, hi: float, nd: int = 1) -> str:
    return f"[{pts(lo, nd)}, {pts(hi, nd)}]"


def wilson(k: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


# --------------------------------------------------------------------------- registry


def registry_checks() -> None:
    sub = REG.check_shipped()
    check("Registry: shipped rows match the index of all 164 rows", "hash-chained registry",
          f"{sub['verbatim']} verbatim, {sub['redacted']} redacted, {sub['withheld']} withheld",
          sub["ok"], "recomputed", "data/registry/")
    files = REG.check_files()
    n = sum(f["match"] for f in files["files"])
    check("Registry: shipped files equal the SHA-256 recorded in their registry rows",
          "files bound by rows 136, 138, 140, 141, 142", f"{n}/{len(files['files'])} match",
          files["ok"], "recomputed", "python -m paper1.registry files")


# --------------------------------------------------------------------------- BFCL audit


def audit_checks() -> None:
    from paper1.bfcl import audited as AUD

    for part, n_exp, k_exp, paper_rate, paper_ci in (
            ("gate", 60, 42, "70%", None), ("test", 240, 146, "60.8%", "[54.5, 66.8]")):
        path = DATA / "bfcl-audit" / f"{part}-defects.json"
        d = AUD.load_defects(path, part=part)      # hash-bound; list == rule over labels
        doc = json.loads(path.read_text())
        labels = [x for x in doc["labels"] if x.get("role", part) == part]
        k = sum(AUD.is_defective(x) for x in labels)
        lo, hi = wilson(k, len(labels))
        got = f"{k}/{len(labels)} = {100 * k / len(labels):.1f}% [{100 * lo:.1f}, {100 * hi:.1f}]"
        want = f"{k_exp}/{n_exp} = {paper_rate}" + (f" {paper_ci}" if paper_ci else "")
        ok = k == k_exp and len(labels) == n_exp and k == len(d["instances"])
        if paper_ci:
            ok = ok and f"[{100 * lo:.1f}, {100 * hi:.1f}]" == paper_ci
        check(f"BFCL audit, {part} split: clear score-changing defects", want, got, ok,
              "recomputed", f"data/bfcl-audit/{part}-defects.json (labels)")
        kappa = doc["summary"]["agreement"]["kappa_defective"]
        check(f"BFCL audit, {part} split: reviewer agreement κ (defective flag)", "0.84",
              f"{kappa:.2f}", f"{kappa:.2f}" == "0.84", "read",
              f"data/bfcl-audit/{part}-defects.json summary")
        if part == "test":
            roots = {x["root"] for x in labels}
            left = roots - set(d["roots_dropped"])
            inst = len(labels) - k
            check("BFCL audit, test split: roots and instances left after dropping defects",
                  "52 roots, 94 instances (68 roots drop out)",
                  f"{len(left)} roots, {inst} instances ({len(d['roots_dropped'])} drop out)",
                  len(left) == 52 and inst == 94 and len(d["roots_dropped"]) == 68,
                  "recomputed", "data/bfcl-audit/test-defects.json")


# --------------------------------------------------------------------------- aggregates


def stage1_and_official() -> None:
    r = json.loads((RES / "stage1/results.json").read_text())
    g = r["gate"]["primary"]
    got = f"+{g['estimate']:.1f} [+{g['interval'][0]:.1f}, +{g['interval'][1]:.1f}]"
    check("Stage 1 registered primary: T+ learned − search control (points)",
          "+4.0 [+2.3, +5.7]", got, got == "+4.0 [+2.3, +5.7]", "read",
          "data/results/stage1/results.json gate.primary")
    s = json.loads((RES / "official-tau2/score.json").read_text())
    d1 = s["variants"]["tau2"]["all"]["learned_minus_b1"][0]
    got = f"{pts(d1['diff'])} {ci(*d1['ci95'])}"
    check("Official τ² retail: learned − B1, pass^1 (points)", "−1.3 [−5.9, +3.3]",
          got, got == "-1.3 [-5.9, +3.3]", "read",
          "data/results/official-tau2/score.json")


def bfcl_gate() -> None:
    s = json.loads((RES / "bfcl-gate/FPRIME-S.json").read_text())
    u = json.loads((RES / "bfcl-gate/FPRIME-U.json").read_text())
    sub = [x for x in s["gate"]["subsets"] if x["lessons"] == ["S01"]][0]
    got = (f"U advanced {u['advanced'] or 'none'} of {len(u['gate']['lessons'])}; "
           f"S advanced {s['advanced']}; S01 vs empty {pts(sub['exact_vs_empty_rd_mean'])} "
           f"{ci(*sub['exact_vs_empty_ci90'])}")
    a = json.loads((RES / "bfcl-gate/AUDITED-S.json").read_text())["lessons"]["S01"]
    est = (f"{pts(a['primary']['rd_mean'])} {ci(*a['primary']['rd_ci90'])}; audited "
           f"{pts(a['audited']['rd_mean'])} {ci(*a['audited']['rd_ci90'])}")
    lesson = [x for x in s["gate"]["lessons"] if x["id"] == "S01"][0]
    got += f"; S01 estimate {est}"
    ok = (u["advanced"] == [] and len(u["gate"]["lessons"]) == 8 and s["advanced"] == ["S01"]
          and f"{pts(sub['exact_vs_empty_rd_mean'])} {ci(*sub['exact_vs_empty_ci90'])}"
          == "+4.7 [+1.8, +7.7]"
          and lesson["rd_mean"] == a["primary"]["rd_mean"]
          and est == "+4.9 [+1.9, +8.0]; audited +3.9 [-0.4, +8.3]")
    check("BFCL gate (H2): advanced lessons; S01 alone vs the empty library; S01 estimate, "
          "primary and audited (points, 90% CrI)",
          "none of 8 U lessons; S01 from S; +4.7 [+1.8, +7.7]; S01 +4.9 [+1.9, +8.0], "
          "audited +3.9 [−0.4, +8.3]", got, ok, "read",
          "data/results/bfcl-gate/FPRIME-{U,S}.json, AUDITED-S.json")
    anchors = sum(v["n"] * v["success"] for v in s["anchors"].values())
    n = sum(v["n"] for v in s["anchors"].values())
    check("BFCL gate: B1 anchor success", "56.7% (34 of 60)",
          f"{100 * anchors / n:.1f}% ({round(anchors)} of {n})",
          round(anchors) == 34 and n == 60, "recomputed",
          "data/results/bfcl-gate/FPRIME-S.json anchors")


def _md_row(text: str, label: str) -> list[str]:
    for line in text.splitlines():
        cells = [c.strip().strip("*") for c in line.strip().strip("|").split("|")]
        if cells and cells[0].strip("*").startswith(label):
            return cells
    raise KeyError(label)


def tau2_gate_read() -> None:
    md = (RES / "tau2-gate/h1b-results-2026-10-24.md").read_text()
    for les, want in (("L07", ("+4.7", "[+4.0, +5.4]")), ("L10", ("+2.7", "[+2.0, +3.4]"))):
        c = _md_row(md, les)
        check(f"τ² F′ gate: {les} success RD, sceptical prior (points, 90% CrI)",
              f"{want[0]} {want[1]}", f"{c[2]} {c[3]}", (c[2], c[3]) == want, "read",
              "data/results/tau2-gate/h1b-results-2026-10-24.md §2")
    m = re.search(r"\|\s*\*\*\{L07, L10\}\*\*\s*\|\s*\*\*([^*]+)\*\*\s*\|\s*(\[[^\]]+\])", md)
    got = f"{m.group(1)} {m.group(2)}" if m else "not found"
    check("τ² F′ gate: joint {L07, L10} (points, 90% CrI)", "+7.4 [+6.3, +8.4]", got,
          got == "+7.4 [+6.3, +8.4]", "read",
          "data/results/tau2-gate/h1b-results-2026-10-24.md §2")
    rbc = re.search(r"RBC set \(≤ 4\): ([L0-9, ]+)\.", md)
    got = rbc.group(1) if rbc else "not found"
    check("RBC comparator: selected set", "L07, L10, L03, L06", got,
          got == "L07, L10, L03, L06", "read",
          "data/results/tau2-gate/h1b-results-2026-10-24.md §3")


def h3_read() -> None:
    md = (RES / "bfcl-h3/bfcl-h3-results-2026-10-24.md").read_text()
    for label, want in (("P2 FPRIME − SEARCH (= B1 − SEARCH)", ("+0.31", "[−3.12, +3.65]")),
                        ("P3 FPRIME − UNGATED (= B1 − UNGATED)", ("−0.52", "[−4.38, +3.33]"))):
        c = _md_row(md, label)
        check(f"BFCL held-out (H3) {label.split()[0]}: diff (points, 95% CI)",
              f"{want[0]} {want[1]}", f"{c[1]} {c[2]}", (c[1], c[2]) == want, "read",
              "data/results/bfcl-h3/bfcl-h3-results-2026-10-24.md §1")
    c = _md_row(md, "P2 FPRIME − SEARCH")
    sec = md.split("## 4.")[1]
    c = _md_row(sec, "P2 FPRIME − SEARCH")
    check("BFCL held-out P2, audited sensitivity (points, 95% CI; Holm p)",
          "+6.0 [+0.2, +12.0], Holm p 0.149", f"{c[1]} {c[2]}, Holm p {c[4]}",
          (c[1], c[2], c[4]) == ("+6.01", "[+0.24, +12.02]", "0.149"), "read",
          "data/results/bfcl-h3/bfcl-h3-results-2026-10-24.md §4")


# --------------------------------------------------------------------------- recomputation


def tau2_gate_recompute() -> None:
    table, pool = DERIVED / "tau2-fgate-table.jsonl", DERIVED / "tau2-fgate-pool.json"
    if not (table.is_file() and pool.is_file()):
        return
    from paper1 import _io
    from paper1.fgate import analysis as A
    from paper1.fgate import pool as fp

    rep = A.analyse(_io.read_jsonl(table), fp.verify_pool(_io.read_json(pool)), n_draws=1000,
                    sensitivities=True)   # as registered: 1,000 draws, sensitivities on
    les = {x["id"]: x for x in rep["gate"]["lessons"]}
    for lid, want in (("L07", "+4.7 [+4.0, +5.4]"), ("L10", "+2.7 [+2.0, +3.4]")):
        got = f"{pts(les[lid]['rd_mean'])} {ci(*les[lid]['rd_ci90'])}"
        check(f"τ² F′ gate: {lid} (refit)", want, got, got == want, "recomputed",
              "data/derived/tau2-fgate-table.jsonl")
    joint = [s for s in rep["gate"]["subsets"] if sorted(s["lessons"]) == ["L07", "L10"]]
    got = f"{pts(joint[0]['rd_mean'])} {ci(*joint[0]['rd_ci90'])}" if joint else "absent"
    check("τ² F′ gate: joint {L07, L10} (refit); advanced set", "+7.4 [+6.3, +8.4]; L07, L10",
          f"{got}; {', '.join(rep['gate']['advanced'])}",
          got == "+7.4 [+6.3, +8.4]" and sorted(rep["gate"]["advanced"]) == ["L07", "L10"],
          "recomputed", "data/derived/tau2-fgate-table.jsonl")


def h3_recompute() -> None:
    rows_p = DERIVED / "bfcl-h3-rows.jsonl"
    if not rows_p.is_file():
        return
    from paper1 import _io
    from paper1.bfcl import audited as AUD
    from paper1.bfcl import confirm as C

    meta = _io.read_json(DERIVED / "bfcl-h3-meta.json")
    rows = _io.read_jsonl(rows_p)
    rep = C.analyse(rows, empty_arms=meta["empty_arms"], design=meta["design"])
    p2 = rep["registered_family"][1]
    got = f"{100 * p2['diff']:+.2f} [{100 * p2['ci95'][0]:+.2f}, {100 * p2['ci95'][1]:+.2f}]"
    check("BFCL held-out P2 (recomputed from episode outcomes)", "+0.31 [−3.12, +3.65]",
          got, got == "+0.31 [-3.12, +3.65]", "recomputed", "data/derived/bfcl-h3-rows.jsonl")
    p3 = rep["registered_family"][2]
    got = f"{100 * p3['diff']:+.2f} [{100 * p3['ci95'][0]:+.2f}, {100 * p3['ci95'][1]:+.2f}]"
    check("BFCL held-out P3 (recomputed from episode outcomes)", "−0.52 [−4.38, +3.33]",
          got, got == "-0.52 [-4.38, +3.33]", "recomputed", "data/derived/bfcl-h3-rows.jsonl")
    d = AUD.load_defects(DATA / "bfcl-audit/test-defects.json", part="test")
    aud = C.audited(rows, d, empty_arms=meta["empty_arms"], design=meta["design"])
    a2 = aud["registered_family"][1]
    got = f"{100 * a2['diff']:+.2f} [{100 * a2['ci95'][0]:+.2f}, {100 * a2['ci95'][1]:+.2f}]"
    check("BFCL held-out P2, audited (recomputed)", "+6.01 [+0.24, +12.02]", got,
          got == "+6.01 [+0.24, +12.02]", "recomputed", "data/derived/bfcl-h3-rows.jsonl")


# --------------------------------------------------------------------------- figures


def figures() -> None:
    want = json.loads((DATA / "results/paper-figures.json").read_text())
    for name, meta in want["figures"].items():
        script = ROOT / "figures" / meta["script"]
        subprocess.run([sys.executable, str(script)], check=True, capture_output=True)
        got = hashlib.sha256((ROOT / "figures" / name).read_bytes()).hexdigest()
        check(f"Figure {meta['paper_label']} rebuilt ({name})", f"PNG SHA-256 {meta['sha256'][:12]}…",
              f"{got[:12]}…", got == meta["sha256"], "rebuilt",
              f"figures/{meta['script']} (byte equality needs matplotlib {want['matplotlib']})")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-figures", action="store_true")
    ap.add_argument("--out", type=Path, default=ROOT / "REPRODUCTION.json")
    args = ap.parse_args(argv)
    registry_checks()
    audit_checks()
    stage1_and_official()
    bfcl_gate()
    tau2_gate_read()
    h3_read()
    tau2_gate_recompute()
    h3_recompute()
    if not args.no_figures:
        figures()
    width = max(len(c["number"]) for c in CHECKS)
    for c in CHECKS:
        print(f"{'ok ' if c['ok'] else 'FAIL'} {c['mode']:<11} {c['number']:<{width}}  "
              f"paper {c['paper']}  |  here {c['this_release']}")
    ok = all(c["ok"] for c in CHECKS)
    print(f"\n{sum(c['ok'] for c in CHECKS)}/{len(CHECKS)} checks pass")
    args.out.write_text(json.dumps({"ok": ok, "checks": CHECKS}, indent=1, ensure_ascii=False)
                        + "\n", encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
