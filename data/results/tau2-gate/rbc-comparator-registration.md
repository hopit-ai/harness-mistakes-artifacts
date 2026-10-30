# Registration: RBC-style comparator on the hand-off 1b F′ data (secondary, exploratory)

**RBC curation stage only; RBC's fresh-episode final selection not run.**

- **Date:** 2026-10-20 (owner-approved in chat the same day).
- **Revised 2026-10-20 (erratum, same day, still before any 1b outcome was seen)** after a
  three-way review (three independent reviewers): content binding of the F′ report to the scored table,
  registered status tied to the registered F′ analysis, missing configuration group refused,
  clean refusals, design and weighting disclosures, interval wording, the curation-stage
  statement. Recorded as a second registry row (`fgate_rbc_comparator_erratum`).
- **Status:** pre-registered **before any hand-off 1b outcome was seen.** The only 1b
  information known at registration is the coverage count from `h1b verify` on the partial
  archive (13,779 of 23,010 units present and verified). Nothing was scored: `h1b score` has
  not been run, no `table.jsonl`, `fgate-report.json` or success/harm/re-ask rate exists or
  was looked at, and the export was not opened.
- **Role:** a **secondary, exploratory** analysis. It **never changes the F′ gate decision**
  (docs/xp/partner-c-fgate-plan.md §3.4: the three-prior intersection gate, shortlist and
  joint subset choice stay the only decision). Confirming the RBC-selected set next to the F′
  set in step 6 is an optional, separate owner decision.
- **Code:** `slh/xp/fgate/rbc.py` (new file; not one of the files the H1 plan hashes, so
  `h1b preflight` is unaffected) and the `rbc` subcommand of `slh/xp/ourside/h1b.py`. The
  SHA-256 of `rbc.py` and of this document are in the registry row
  (`learner_runs/REGISTRY.jsonl`, event `fgate_rbc_comparator_registration`).

## 1. Rationale

The literature survey of 2026-10-20 (docs/lit/survey-2026-10-20.md, item 2) found RBC —
Pham et al., *Curating Self-Written Agent Playbooks with Randomized Experiments*,
arXiv:2610.18427 (2026-10-13) — which already randomizes the inclusion of self-written
lesson blocks (p = ½) and keeps blocks by a ridge estimate of their effect, including on a
9B Qwen model. F′ is therefore not novel as "randomized inclusion of lessons"; its claim is
the gate (priors, harm bound, context non-inferiority, multiplicity via intersection) and the
decomposition. To show what the gate adds, we register RBC's selection rule, adapted to our
units, on the same data, before the data are seen (survey §"recommended plan changes",
item 2).

## 2. Data

- Input: the scored table `W/table.jsonl` written by `h1b score` (its SHA-256 must match
  `W/score.json`), the package's `pool.json` (12 lessons, hash-verified) and the F′ report
  `W/fgate-report.json` from `h1b analyse`. **Binding:** `h1b analyse` writes
  `ourside.inputs` (SHA-256 of the table, plan and pool it analysed) into the F′ report; `rbc`
  refuses an F′ report without this binding or whose table / plan / pool hash differs from
  the scored table (`score.json`), the package plan and the pool. The F′ report's own SHA-256
  is recorded in `rbc-report.json`.
- Rows: track `fgate` (fit prefixes) whose inclusion vector `x` has at least one lesson,
  i.e. the **randomized draws** (16 per prefix, 8 antithetic pairs); this drops exactly the
  all-zero empty-library anchor of each prefix, a design point RBC does not have. Every row
  must carry its configuration `group` (refused otherwise; no silent fallback). Error rows
  are kept as scored (as in the primary F′ analysis) and counted.
- **Design disclosure:** each lesson's marginal inclusion probability is ½, but inclusions
  are **not jointly independent**: `fgate.design.inclusion_vectors` rejects the empty and the
  whole vector and any repeated vector (or its complement) within a prefix. RBC assumes
  independent p = ½ inclusion.
- **Unit of inclusion:** the 12 pool lessons L01–L12. Our design has no lesson blocks, so
  each lesson is one RBC block.
- **Outcome for selection:** per-decision **success** (`y`, the deterministic decision
  scorer), as RBC selects on success only. **Harm** (`harm`, a write that is not the exact
  expected write) is estimated the same way and reported separately; it is not used to
  select.

## 3. Estimator (exact)

Per outcome, a linear-probability ridge regression with one unpenalized intercept per
decision prefix (RBC's per-task intercept; a decision prefix is our task instance):

    y_r = a_i + Σ_l x_rl b_l + e_r,    minimise Σ_r e_r² + λ Σ_l b_l²

fitted exactly by the within-prefix transform (x and y demeaned within each prefix; then
b = (X̃ᵀX̃ + λI)⁺ X̃ᵀỹ with the Moore–Penrose inverse, so λ = 0 is OLS). Under independent
b_l is a **regularized effect of lesson l under this restricted design**; it approximates,
but is not exactly, RBC's Banzhaf value (which presumes independent p = ½ inclusion).

**Weighting:** every row (and every held-out row in cross-validation) has equal weight, as
in RBC, whereas F′ standardizes over contexts weighted equally (`fgate.analysis`, weights
`"equal"`). Differences between the RBC set and the F′ set, and in their harm profile,
therefore reflect weighting, model (linear vs logistic, no context terms, no priors) and
regularization as well as the gate itself.

- **λ grid (fixed):** 0, 1, 3, 10, 30, 100, 300, 1,000, 3,000, 10,000, 30,000, 100,000
  (`rbc.LAMBDA_GRID`).
- **λ choice:** leave-one-task-out cross-validation with task = decision prefix: each
  prefix in turn is held out, b is refitted on all other prefixes, and the held-out
  prefix's within-demeaned outcomes are predicted (its intercept is its own mean, as for an
  unseen task). Criterion: total squared error over all held-out rows; the smallest wins,
  exact ties go to the larger λ. Success and harm each choose their own λ.
- **Selection rule (success only):** lessons with b_l > 0, ordered by b_l descending (ties
  by lesson id), keeping at most **4**.
- **Budget:** RBC keeps blocks within a token budget. F′ has no token budget; its budget is
  the shortlist cap of **4 lessons** (`fgate.analysis.RULES["shortlist"]`, plan §3.4). The
  comparator uses the same cap (`rbc.BUDGET_LESSONS = 4`, pinned equal by a test). Every
  pool lesson is a single WHEN/THEN line, so a lesson count is the operative budget.
- **RBC's final step** (choose among curated / whole library / none on fresh episodes) is
  **omitted** in this analysis: the registered `evaluate` prefixes of hand-off 1b carry only
  B1 (empty-library) collection units for track C; no curated or whole-library arm was run on
  them, so no fresh-episode comparison exists in the 1b data. It is the optional step-6
  confirmation (separate owner decision).

## 4. Descriptive extras (not part of the selection)

- Per-lesson 90% percentile intervals (**descriptive, conditional on the fixed chosen λ;
  no post-selection guarantee**), P(b > 0) and the frequency with which each lesson is
  selected, from a **cluster bootstrap over configuration groups** (the 3 phrasings of one
  configuration), λ fixed at the chosen value, 1,000 draws, seed 20261020.
- Sensitivity: λ chosen by leave-one-configuration-group-out instead of leave-one-prefix-out,
  and the set it selects (reported, never used).
- In-sample linear contrasts against the empty library (sum of b over the curated set and
  over all 12 lessons) for success and harm, reported as `in_sample_contrasts_not_rbc_choice`
  and labelled "NOT RBC's choice": they are fitted-data predictions, never RBC's
  fresh-episode selection, which is not run.

## 5. Outputs

`python -m slh.xp.ourside.h1b rbc --work W --package PKG` (after `score` and `analyse`)
writes `W/rbc-report.json` (schema `xp-fgate-rbc-v1`) and `W/rbc-report.md`:

1. per lesson: success estimate b (points) with its descriptive bootstrap 90% interval, bootstrap selection
   frequency, harm estimate; positive and selected flags;
2. chosen λ (success, harm) and the full CV curves;
3. the RBC-selected set (and all positive lessons);
4. overlap with the F′ **advanced** set and shortlist (intersection, Jaccard, RBC-only,
   F′-only);
5. exploratory: for every RBC-selected lesson its F′ status — pass (final and by prior),
   **E3** (context non-inferiority), **E4** (wrong-write harm bound), max P(context harm) and
   the F′ harm RD.

**Partial input:** the step refuses exactly what `analyse` refuses (verify status not
`complete`/`partial-allowed`; no `table.jsonl`, i.e. not scored) and additionally: no
`fgate-report.json`, a table that differs from the scored one, an F′ report not bound to
this table/plan/pool, a pool that fails its hash, or a row without a configuration group
(all exit 2, except a changed table: exit 3). On a `partial-allowed` archive it runs and
labels everything partial (STATUS banner), as `analyse` does.

**Registered status:** `registered_analysis: true` only if the archive is complete **and**
the bound F′ report is itself the registered analysis (complete, 1000 draws, sensitivities
on). Otherwise `registered_analysis: false` with the reasons listed, a "not registered"
STATUS banner, and a "cross-reference not registered" banner on the F′ section.

## 6. What it cannot do

It does not gate, does not advance any lesson, and does not alter `fgate-report.json` or
`report.md`. Its numbers are averages over randomized other lessons, not contributions in a
final library, and a decision-level effect is not a conversation-level effect (plan §3.4).
