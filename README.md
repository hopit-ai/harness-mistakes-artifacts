# Paper 1 artefacts: learning from its own traces, frozen 9B agent

Code and data to check the registered numbers of

> **Does Learning from Its Own Traces Help a Frozen 9B Agent? Registered Decompositions on
> τ²-bench Retail and BFCL Multi-Turn.** Arkid Mitra (Hopit AI), 2026.
> arXiv: `<ARXIV-ID — to be filled>`

The paper asks whether lessons written from a frozen Qwen3.5-9B agent's own failures help it
more than a matched search that never sees the failures. It answers with registered
experiments on τ²-bench retail (decision level and official conversations) and BFCL multi-turn,
a randomised-inclusion lesson gate (F′) and a blind audit of the BFCL evaluator. Every
confirmatory analysis was registered before its data existed, in a hash-chained registry
anchored by public partner-kit tags.

This repository holds **only what is needed to check or reproduce the paper's numbers**: the
analysis code (numpy only), the paper-1 rows of the registry, the frozen BFCL defect lists and
the aggregate result files the paper's tables come from. It is not the system the experiments
ran on (see [What is not here](#what-is-not-here)).

Licence: [PolyForm Noncommercial 1.0.0](LICENSE). Commercial use needs permission
([NOTICE](NOTICE)).

## Quick start

```bash
python -m venv .venv && . .venv/bin/activate
pip install "numpy>=2" "matplotlib==3.10.8" pytest   # matplotlib only for the figures
python reproduce.py          # 24 checks; writes REPRODUCTION.json; exit 0 if all pass
python -m pytest -q          # 30 tests of the analysis code on synthetic data
```

Python 3.12 or later. Nothing here needs a GPU, a model, network access or the benchmarks
installed.

## What is here

```
paper1/
  fgate/analysis.py      F′ randomised-inclusion gate: hierarchical logistic model, three named
                         priors, empirical-Bayes grid, Laplace draws, rules E1–E4, joint subsets,
                         synthetic-difficulty check (paper §7.3, §8, App. H.2)
  fgate/rbc.py           RBC-style comparator (§8, App. L), byte-identical to the registered file
  fgate/run_rbc.py       command line for rbc.py
  fgate/simulate.py      operating characteristics of the F′ rule (§8 "In simulation", App. H.2)
  fgate/pool.py          τ² lesson pool: policy screen, intent clustering, sealing (§8 "Pool")
  fgate/design.py        registered difficulty-check constants and the inclusion-vector generator
  bfcl/fprime.py         F′ on BFCL episodes (§7.3, §7.5)
  bfcl/audited.py        audited sensitivity of F′ and the frozen defect-list loader (§7.4, §7.5)
  bfcl/confirm.py        held-out confirmation H3: Holm family, cluster bootstrap, audited
                         sensitivity, official-decoding row (§7.7)
  bfcl/s01_explore.py    exploratory, post-hoc S01 re-analysis (§7.6, App. K)
  bfcl/data.py, bfcl/plan_min.py   BFCL id/family helpers and plan/pool seals
  registry.py            checks the shipped registry rows (and the full chain, given the file)
data/
  registry/              paper-1 rows of the hash-chained registry + an index of all 164 rows
  bfcl-audit/            frozen BFCL defect lists (gate 60, test 240 instances), summaries,
                         owner adjudications with rationales, REDACTION.json
  results/stage1/        Stage-1 registered results (results.json, results.md)       (§4)
  results/official-tau2/ official τ² retail score (score.json)                      (§5.3, App. C)
  results/g1/            identity-guard analysis (analysis.json)                    (§6, App. J)
  results/bfcl-gate/     BFCL F′ gate reports, pools U and S, primary and audited;
                         S01 exploratory report                                     (§7.5, §7.6)
  results/bfcl-h3/       BFCL held-out confirmation results                         (§7.7)
  results/tau2-gate/     τ² F′ gate, RBC comparator and difficulty-check results;
                         RBC comparator registration                                (§8, App. L)
  results/paper-figures.json   SHA-256 of the paper's figure files
  derived/               BFCL H3 episode outcomes (bfcl-h3-rows.jsonl) and their package seal
figures/make_fig{1,2,3}.py     rebuild Figures 1, J1 and 2 from data/results
tools/export_derived.py        owner-side exporter of minimal derived tables (see below)
reproduce.py                   the checks below
```

## Reproducing the paper's numbers

Run `python reproduce.py`. Modes: **recomputed** = computed here from shipped instance- or
decision-level data; **read** = read from a shipped aggregate result file that the project's
analysis wrote (where a registry row records the file's SHA-256, `python -m paper1.registry
files` checks it); **rebuilt** = figure regenerated and compared byte for byte.

| Paper number (section) | Value in the paper | Script and input | Command | Mode |
|---|---|---|---|---|
| Registry: paper-1 rows, index of all rows (A.1) | rows 132–150, 156–157 | `paper1/registry.py`, `data/registry/` | `python -m paper1.registry check` | recomputed |
| Shipped files equal their registered SHA-256 | rows 136, 138, 140–142 | `paper1/registry.py` | `python -m paper1.registry files` | recomputed |
| BFCL audit, gate split (§7.4, Table 10) | 42/60 = 70.0% | `bfcl/audited.py`, `data/bfcl-audit/gate-defects.json` | `python reproduce.py` | recomputed |
| BFCL audit, test split (§7.4 Table 10, §7.7) | 146/240 = 60.8% [54.5, 66.8]; κ 0.84 | `bfcl/audited.py`, `data/bfcl-audit/test-defects.json` | `python reproduce.py` | recomputed (κ read) |
| Test roots/instances left after the audit (§7.7) | 52 roots, 94 instances | same | `python reproduce.py` | recomputed |
| Stage 1 registered primary (§4.1, Table 5) | +4.0 [+2.3, +5.7] | `data/results/stage1/results.json` | `python reproduce.py` | read |
| Official τ², learned − B1, pass^1 (§5.3, Table 8) | −1.3 [−5.9, +3.3] | `data/results/official-tau2/score.json` | `python reproduce.py` | read |
| BFCL gate: nothing from U advanced; S01 from S; S01 vs empty (§7.5, Table 11) | +4.7 [+1.8, +7.7] | `data/results/bfcl-gate/FPRIME-{U,S}.json` | `python reproduce.py` | read |
| BFCL gate: B1 anchor (§7.5) | 56.7% (34 of 60) | `data/results/bfcl-gate/FPRIME-S.json` | `python reproduce.py` | recomputed |
| τ² F′ gate, L07 / L10 (§8, Table 15) | +4.7 [+4.0, +5.4] / +2.7 [+2.0, +3.4] | `data/results/tau2-gate/h1b-results-2026-10-24.md` | `python reproduce.py` | read* |
| τ² F′ gate, joint {L07, L10} (§8) | +7.4 [+6.3, +8.4] | same | `python reproduce.py` | read* |
| RBC comparator set (§8, App. L) | L07, L10, L03, L06 | same | `python reproduce.py` | read* |
| BFCL H3 P2, B1 − SEARCH (§7.7, Table 13) | +0.31 [−3.12, +3.65], Holm p 1.000 | `bfcl/confirm.py`, `data/derived/bfcl-h3-rows.jsonl` (5,760 episodes) | `python reproduce.py` | recomputed (and read) |
| BFCL H3 P3, B1 − UNGATED (§7.7, Table 13) | −0.52 [−4.38, +3.33] | same | `python reproduce.py` | recomputed (and read) |
| BFCL H3 P2, audited (§7.7) | +6.0 [+0.2, +12.0], Holm p 0.149 | same + `data/bfcl-audit/test-defects.json` | `python reproduce.py` | recomputed (and read) |
| Figures 1, 2 and J1 | — | `figures/make_fig*.py`, `data/results/` | `python reproduce.py` | rebuilt |

\* Read in this version: the τ² decision table is not yet in `data/derived/`. When
`tools/export_derived.py tau2-gate` has added it, `reproduce.py` refits the τ² gate (1,000
draws, sensitivities on, as registered) and checks these numbers as recomputed.

**Result of `python reproduce.py` on 2026-10-30:** 24 of 24 checks pass (9 recomputed,
12 read, 3 rebuilt figures; the H3 contrasts are both read and recomputed) (Python 3.13.5,
numpy 2.3.5, matplotlib 3.10.8, macOS arm64). All three figures are byte-identical to the
paper's. `python -m pytest -q`: 30 passed (also with Python 3.12.11 and numpy 2.5.3). The
full registry chain (164 rows, 305,023 bytes, head `5fd92773…6dc6b`) was verified with
`python -m paper1.registry verify-full` on the full file; the shipped rows sit at their indexed
offsets byte for byte.

### Running the analyses on their full inputs

```bash
# τ² F′ gate (§8) and the RBC comparator (App. L)
python -m paper1.fgate.analysis --table TABLE.jsonl --pool POOL.json --out FGATE.json --plan PLAN.json
python -m paper1.fgate.run_rbc  --table TABLE.jsonl --pool POOL.json --fgate FGATE.json --out RBC.json --md RBC.md
# BFCL F′ gate (§7.5) and its audited sensitivity
python -m paper1.bfcl.fprime analyse --table TABLE-U.jsonl --pool POOL-U.json --out FPRIME-U.json
python -m paper1.bfcl.audited sensitivity --table TABLE-U.jsonl --pool POOL-U.json \
    --primary FPRIME-U.json --out AUDITED-U.json            # defect list: data/bfcl-audit
# BFCL held-out confirmation (§7.7), from the H3 package and its export
python -m paper1.bfcl.confirm --package PKG-H3 --export EXPORT-H3 \
    --defects data/bfcl-audit/test-defects.json \
    --official-package PKG-H3-OFFICIAL --official-export EXPORT-H3-OFFICIAL --out CONFIRM-H3.json
# operating characteristics of the F′ rule (§8, App. H.2; minutes on a laptop at small --reps)
python -m paper1.fgate.simulate --reps 25 --out SIM.json
```

The hand-off packages (`plan.json`, `pool.json`, units) are public in the partner kit tags below.
The scored tables and exports are not in this repository (next section).

## What is not here

- **The system the experiments ran on stays private** and is available on request
  (`<CONTACT — to be filled by the owner>`): the agent harness and runtime, the safety layer,
  the host adapters, the learning loop and writers, the small trained components, the checker
  study, and the project's internal scoring pipeline. None of it is needed to check the
  numbers above, and none of the shipped code imports it.
- **Raw episodes and private task data.** No agent trajectories, prompts or conversations; no
  answer keys, gold decisions or private test membership; nothing from the synthetic retail
  database extension. The τ² decision tables were scored with private keys.
- **The τ² F′ decision table** (20,400 decisions) is not included yet, so the τ² gate numbers
  are *read* from the reported results. `tools/export_derived.py tau2-gate` writes it (outcomes,
  inclusion bits and order-preserving pseudonymous ids only); `reproduce.py` then recomputes
  them. The BFCL H3 episode outcomes are included (`data/derived/bfcl-h3-rows.jsonl`: arm,
  trial, public BFCL instance id, root, category, success, harm; no trajectories) and the H2
  episode table is not (the H2 gate reports are shipped).
- **Partner-kit material** is not duplicated: run code, packages, plans, pools and units are in
  the public kit tags (MIT) listed below.
- **Third-party code** is not vendored: τ²-bench and BFCL keep their own licences (NOTICE).
- **Redactions.** Three registry rows (136, 140, 157) and the two frozen defect lists carry
  local file paths or internal reviewer names; they ship as redacted copies, each bound to the
  hash of its original (`data/registry/INDEX.json`, `data/bfcl-audit/REDACTION.json`). The
  originals and the full registry can be checked on request.

## Registry

`data/registry/INDEX.json` lists all 164 registry rows: offset, length, the SHA-256 of each row
and the `prev_sha256` it records (the SHA-256 of every byte before it), and the head (SHA-256 of
the whole file). Paper-1 rows ship verbatim (`paper1-rows.jsonl`, 18 rows, byte-identical) or
redacted (`paper1-rows-redacted.jsonl`, 3 rows); the other 143 rows (earlier pilots and later,
unrelated work) are listed by hash only. Because each row hashes all earlier bytes, the chain
itself can be recomputed only from the full file: `python -m paper1.registry verify-full
REGISTRY.jsonl` does that and checks every indexed row in place. Public anchors are the kit
tags below, whose commits the registry rows name.

Paper-1 rows: 132 phase-1 registration; 133–135 amendments 1–3; 136 partner export opened and
scored; 137 disclosure correction; 138 phase 2 retired; 139–140 RBC comparator registration and
erratum; 141–142 BFCL audit freezes (gate, test); 143 BFCL H2 scoring serialization fix;
144–149 BFCL H3 library freezes; 150 BFCL H3 plan seal; 156–157 XD2 read-database deviation
and erratum.

## Partner kits (public, MIT)

<https://github.com/hopit-ai/self-learning-harness-kit>, tags as named in the paper:

| Tag | Commit | Used for |
|---|---|---|
| `xp-p1-phase0-v1` | `640c2766` | Stage 1, phase 0 site check |
| `xp-p1-v1` | `53a2a620` | Stage 1 (decision-level ablation) |
| `xp-h1a-v1` | `b95a226d` | BFCL baseline and ALFWorld check (hand-off 1a) |
| `xp-h1b-v1` | `a29d10e4` | τ² F′ gate data (hand-off 1b): `package-h1/plan.json`, `pool.json`, units |
| `xp-h2b-v1` | `28fd96ad` | BFCL F′ gate (hand-off 2): `package-bfcl-h2/plan.json` with pools U and S |
| `xp-h3b-v1` | `58705943` | BFCL held-out confirmation (hand-off 3) |

## Hardware and software of the experiments

- Agent: Qwen3.5-9B, revision `c2022362`, served with vLLM, thinking off, temperature 0;
  weights never updated. Teacher: Qwen3.8-Flash-Next-FP8 (deviation XD1).
- GPU runs on an external partner's H100 node from the public kits: τ² F′ gate 8 × H100,
  9.65 H100-hours; BFCL H3 2 × H100 (vLLM 0.30.0), 2.19 H100-hours. The official τ² run was
  self-served on rented L40S GPUs (A100-40GB fallback).
- τ²-bench commit `672227c6` (v1.0.1), retail; BFCL `bfcl-eval==2026.3.23` (gorilla commit
  `6ea57973`), multi-turn base and long-context.
- Analyses (this repository): CPU only; Python 3.12/3.13, numpy 2.x; figures with matplotlib
  3.10.8.

## Code provenance

Each module is a copy of the project's module of the same role; imports were trimmed so that
it runs standalone, and nothing else changed unless listed.

| Here | Project module | Changes |
|---|---|---|
| `paper1/fgate/rbc.py` | `slh/xp/fgate/rbc.py` | none (SHA-256 `9bb0ec7a…` = registry row 140) |
| `paper1/fgate/analysis.py`, `simulate.py`, `pool.py` | `slh/xp/fgate/*` | import paths and usage lines |
| `paper1/fgate/design.py` | `slh/xp/fgate/design.py` | only the difficulty-check constants and the inclusion-vector generator |
| `paper1/bfcl/fprime.py`, `confirm.py` | `slh/xp/bfcl/*` | import paths; plan seals from `plan_min.py` |
| `paper1/bfcl/audited.py` | `slh/xp/ourside/bfcl_audited.py` | import paths; defect lists checked against the shipped registry rows and REDACTION.json |
| `paper1/bfcl/s01_explore.py` | `slh/xp/ourside/bfcl_s01_explore.py` | import paths; the `rescore` step needs the kit and `bfcl-eval` |
| `paper1/bfcl/data.py`, `plan_min.py` | kit `slh/xp/bfcl/data.py`, `plan.py` | data path from the installed `bfcl-eval`; only the seal and pool helpers |
| `figures/make_fig*.py` | `docs/paper/figures/make_fig*.py` | input paths |

Docstrings refer to the project's design documents (`docs/xp/…`); their registered content is
in the paper and its appendices.

## Citation

```bibtex
@misc{mitra2026traces,
  title  = {Does Learning from Its Own Traces Help a Frozen 9B Agent? Registered Decompositions
            on tau2-bench Retail and BFCL Multi-Turn},
  author = {Mitra, Arkid},
  year   = {2026},
  note   = {Hopit AI. arXiv:<ARXIV-ID>}
}
```
