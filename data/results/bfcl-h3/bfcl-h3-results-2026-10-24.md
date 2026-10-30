# BFCL hand-off 3 (part E): held-out confirmation results, 2026-10-24

Aggregate numbers only. Design and analysis as registered in
[bfcl-plan](bfcl-plan.md) §6.2, §6.4 and §6.5 (empty L\*, B-D9 not adopted). Registered
results come first, then descriptive rows, then the audited sensitivity, then the exploratory
S01 analysis. Success is official BFCL success, with roots weighted equally. Differences are
in points. Intervals are 95% cluster bootstraps over roots (10,000 resamples, seed 20261018).
p-values come from the paired root-level t test.

## 0. Provenance and integrity

- **Run**: kit tag `xp-h3b-v1` (kit commit `5870594`), Qwen3.5-9B on vLLM 0.30.0 with 2×H100,
  offline. The partner reported the run on 2026-10-23: 66 min of server time (2.19 H100-hours),
  no stops and no reruns, and run, score and export all exited 0.
- **Packages**:
  - `package-bfcl-h3`: 24 cells, 5,760 episodes, plan seal `254044ee…4b680`.
  - `package-bfcl-h3-official`: 1 cell, 240 episodes, plan seal `dbadc59e…81216`.
  - Both run identities name these seals, run mode `full`, endpoint `126cb664…`.
- **Delivery**: `heldout-min.tar.xz` matches its `.sha256` (`c40d9ca9…90b6`). It holds 127
  members, all regular files, with no absolute paths, `..` components or links. It was
  unpacked into a new folder and nothing from it was executed.
- **Our scoring**:
  - We staged the raw results only, without the partner's verdicts. We scored them with the
    kit's registered `runner score`, run with the benchmark environment's Python
    (`runner check` ok, `bfcl-eval 2026.3.23`).
  - The repository's registered code files equal the plan's `code` hashes (11/11, the same as
    the kit tree). The B-D8 serialization fix is already in this runner, so no pinned worktree
    or wrapper was needed.
  - **Our verdicts are byte-identical to the partner's in all 25 cells**: 24/24 for H3 and 1/1
    for the official-temperature package. No differences to explain.
- **Export and verify**:
  - We exported with the registered `runner export`.
  - `bfcl_h2 verify` (the generic our-side checks) passed for both packages:
    - the identity is recomputed from plan and endpoint;
    - the cells equal the plan's, with no halt and no torn tail;
    - rows equal units, with system notes matching each unit and `max_tokens` following the
      plan's rule;
    - there is one verdict per row and one outcome per row.
  - Counts: 5,760 rows, verdicts and outcomes for H3, and 240 for the official package.
  - Export manifests: `d4dead28…` (H3) and `c68b4c80…` (official).
- **Coverage gate** (`slh.xp.bfcl.confirm`): passed for both packages. Every registered
  (cell, instance) appears exactly once, seal and identity match, and status is `complete`.
  The design is `registered` and the empty arm is FPRIME.
  `CONFIRM-H3.json` SHA-256: `4805d542…`.
- **Defect list**: `test-defects.json` (`dbe63196…`), checked against registry row
  `bfcl_audit_freeze_test`. It lists 146 defective test instances; 68 roots drop out and 52
  remain, with 94 instances. These match the registered figures.

## 1. Registered primary family (Holm, m = 3, two-sided 0.05)

L\* is empty, so FPRIME is B1 (§6.5).

| Contrast | Diff | 95% CI | p | p (Holm) | Significant |
|---|---:|---|---:|---:|---|
| P1 FPRIME − B1 | 0.00 | [0.00, 0.00] | 1.000 | 1.000 | no (null by construction) |
| P2 FPRIME − SEARCH (= B1 − SEARCH) | +0.31 | [−3.12, +3.65] | 0.859 | 1.000 | no |
| P3 FPRIME − UNGATED (= B1 − UNGATED) | −0.52 | [−4.38, +3.33] | 0.793 | 1.000 | no |

**"Learning beats the standard harness" is not claimed** (`claim_p1` false). P2 and P3 are
both near zero and inconclusive.

## 2. Secondary, descriptive (registered; no multiplicity claim)

Per arm (960 episodes each, 120 roots):

| Arm | Success | Harm (state mismatch) | pass^4 |
|---|---:|---:|---:|
| B1 (= FPRIME) | 47.92 | 36.56 | 30.42 |
| B1P (neutral note) | 52.40 | 33.02 | 36.67 |
| PERSON | 54.79 | 31.98 | 40.00 |
| UNGATED | 48.44 | 35.63 | 32.50 |
| SEARCH ({S01}) | 47.60 | 37.29 | 30.00 |
| MEMORY | 54.58 | 33.13 | 43.33 |

Contrasts:

| Contrast | Diff | 95% CI | p |
|---|---:|---|---:|
| B1P − B1 | +4.48 | [+0.73, +8.44] | 0.022 |
| PERSON − B1 | +6.88 | [+2.81, +11.15] | 0.001 |
| UNGATED − B1 | +0.52 | [−3.44, +4.38] | 0.793 |
| SEARCH − B1 | −0.31 | [−3.65, +3.23] | 0.859 |
| MEMORY − B1 | +6.67 | [+1.56, +11.77] | 0.011 |
| FPRIME − MEMORY | −6.67 | [−11.77, −1.56] | 0.011 |
| FPRIME − PERSON | −6.88 | [−11.15, −2.92] | 0.001 |

Primary contrasts by category (descriptive):

| Contrast | Base | Long Context |
|---|---|---|
| FPRIME − SEARCH | −1.25 [−6.04, +3.96] | +1.88 [−2.50, +6.25] |
| FPRIME − UNGATED | +0.21 [−5.00, +5.42] | −1.25 [−6.04, +3.54] |

Per-arm success by category (descriptive):

| Arm | Base | Long Context |
|---|---:|---:|
| B1 | 50.83 | 45.00 |
| B1P | 56.04 | 48.75 |
| PERSON | 58.33 | 51.25 |
| UNGATED | 50.62 | 46.25 |
| SEARCH | 52.08 | 43.12 |
| MEMORY | 57.92 | 51.25 |

## 3. Descriptive only (§6.5; no claim, no multiplicity statement)

- **SEARCH − B1** (the S01 effect, numerically −P2): **−0.31 [−3.65, +3.23]**, p = 0.86.
  - The gate's selected-winner estimate (+4.9 on hand-off 2) does not replicate on the
    held-out test.
  - By category: Base +1.25, Long Context −1.88.
- **UNGATED − B1** (the trace-learned pool, numerically −P3): **+0.52 [−3.44, +4.38]**,
  p = 0.79.
- **Official temperature (B1 at 0.001, one trial, 240 episodes)**:
  - success 45.83 vs sampled B1 47.92: **−2.08 [−6.88, +2.50]**, p = 0.38;
  - harm 39.58 vs 36.56;
  - Base 50.83, Long Context 40.83.
- Not registered, but visible above: the arms that add general guidance (B1P's neutral note,
  PERSON, MEMORY) sit +4.5 to +6.9 above B1. The two learned-lesson arms (SEARCH, UNGATED) do
  not.
  - These are descriptive secondary rows without multiplicity control.
  - B1P's +4.5 means much of any note's gain may be non-specific (any system message at all).

## 4. Audited sensitivity (§6.4; reported beside the primary, never instead)

The analysis is repeated without the 146 frozen defective test instances (rubric v2:
score-changing and clear). That leaves 52 roots and 94 instances; a root that keeps one
instance counts as one root.

Audited defect rate (from the frozen audit, for reference):
- 146/240 = 60.8% (Wilson 95% 54.5–66.8%): Base 70/120, Long Context 76/120;
- Epoch AI's multi-turn sample: 8/15.

| Registered family, audited | Diff | 95% CI | p | p (Holm) | Significant |
|---|---:|---|---:|---:|---|
| P1 FPRIME − B1 | 0.00 | [0.00, 0.00] | 1.000 | 1.000 | no |
| P2 FPRIME − SEARCH | +6.01 | [+0.24, +12.02] | 0.050 | 0.149 | no |
| P3 FPRIME − UNGATED | +6.25 | [−0.48, +13.22] | 0.076 | 0.153 | no |

| Arm (non-defective instances) | Success | Harm | pass^4 |
|---|---:|---:|---:|
| B1 (= FPRIME) | 63.22 | 31.73 | 43.62 |
| B1P | 66.59 | 28.61 | 52.13 |
| PERSON | 68.75 | 27.64 | 54.26 |
| UNGATED | 56.97 | 35.58 | 39.36 |
| SEARCH | 57.21 | 37.98 | 35.11 |
| MEMORY | 65.87 | 31.25 | 54.26 |

Audited secondary contrasts:

| Contrast | Diff | 95% CI | p |
|---|---:|---|---:|
| B1P − B1 | +3.37 | [−1.92, +9.13] | 0.228 |
| PERSON − B1 | +5.53 | [−0.72, +12.26] | 0.103 |
| UNGATED − B1 | −6.25 | [−13.22, +0.48] | 0.076 |
| SEARCH − B1 | −6.01 | [−12.02, 0.00] | 0.050 |
| MEMORY − B1 | +2.64 | [−5.29, +9.62] | 0.483 |

Further rows:
- **By category**:
  - FPRIME − SEARCH: Base +4.50 [−4.00, +12.50] (50 roots), Long Context +7.39
    [0.00, +14.77] (44 roots).
  - FPRIME − UNGATED: Base +6.50, Long Context +4.55.
- **Official temperature, non-defective instances**: B1 at 0.001 scores 60.58 vs sampled
  63.22, a difference of −2.64 [−10.10, +4.81].
- **Defective instances alone** (78 roots, 584 episodes per arm; descriptive), success:
  - B1 37.66, B1P 42.31, PERSON 45.83, UNGATED 42.79, SEARCH 41.19, MEMORY 45.51.
- **Disagreement with the primary.** The primary shows no difference between the learned
  arms and B1. The sensitivity points the other way: on non-defective instances, both
  learned-lesson arms are about 6 points *below* B1, though neither contrast is significant
  after Holm. On defective instances alone, both are 3.5–5 points above B1.
  - Per §6.4, the primary stands.
  - The pattern is consistent with the learned lessons shifting success between defective and
    non-defective instances rather than raising it. Nothing here was used to choose anything.

## 5. Exploratory: S01 on H3 (post hoc, owner-approved 2026-10-22; changes no registered result)

Method: `slh/xp/ourside/bfcl_s01_explore.py` (h3-arms design), as in
[bfcl-s01-exploratory-2026-10-22](bfcl-s01-exploratory-2026-10-22.md).
- **Re-score**: all 5,760 episodes were replayed through the official checker. The replay
  reproduces the stored verdicts with **0 mismatches**.
- **Pairs**: trial-matched pairs against B1, with a root bootstrap. The bootstrap's random
  stream differs from `confirm`, so its intervals differ slightly.
- **Turn-level `act`**: uses the "Asking Earns Nothing" release files, `pairs.json`
  `5dac6ba8…` and `mutator_map.json` `b18810ce…`.
- **Outputs**: `rescore-h3.jsonl` `206441b1…`, `report-h3.json` `8359b579…`.

| Arm − B1 (960 pairs) | Official | cwd check | pwd removed | act (base) | Up / down flips |
|---|---:|---:|---:|---:|---|
| SEARCH (S01) | −0.31 [−3.75, +3.23] | −0.10 | −0.31 | +0.28 | 98 / 101 |
| UNGATED | +0.52 | +0.31 | +0.52 | −0.57 | 105 / 100 |
| B1P | +4.48 [+0.73, +8.33] | +4.06 | +4.48 | −0.85 | 115 / 72 |
| PERSON | +6.88 [+2.92, +11.25] | +7.08 | +6.88 | +2.27 | 128 / 62 |
| MEMORY | +6.67 [+1.56, +11.77] | +6.67 | +6.67 | +3.13 | 139 / 75 |

- **S01's pwd behaviour persists without a success gain.**
  - With S01, 15.3% of episodes call pwd (0.20 calls per episode), against 6.3% (0.08) under
    B1.
  - Official success is unchanged.
- **pwd still never changes a verdict.**
  - Removing every pwd call changes 0 of 5,760 verdicts in every arm.
  - No turn's only calls are pwd, and no pwd falls on a turn whose ground truth contains pwd.
- **The working-directory check** turns 32 official passes into fails across all arms, and
  never the reverse. It shifts no arm − B1 contrast by more than 0.5 points.
- **S01's failure classes vs B1** are all near zero:
  - state mismatch +0.73 [−2.92, +4.27];
  - empty turn −0.94 [−2.29, +0.31];
  - response mismatch −0.10.
  - On hand-off 2, S01's state-mismatch reduction was −4.9. It does not recur on the test.
- **Reading.** The H2 conclusion that S01 is not a scorer artefact still holds on H3. But the
  H2 gain, which looked like fewer wrong writes, does not transfer to the held-out roots. The
  +4.9 gate estimate looks like selection on noise, or a gate-specific effect such as root 42,
  rather than a general behaviour fix. The note-carrying arms that do gain (B1P, PERSON,
  MEMORY) gain without extra pwd use (pwd removal changes nothing for them either).
