# Phase 1 results (xp-p1-2026-10-10)

## Headline

- The T+ learned skill scored +4.0 points against its no-evidence search control, pooled over 3 tasks (95% interval [+2.3, +5.7]): superiority shown; the estimate does not reach the 5-point minimum worthwhile gain.
- Wrong writes changed by -3.1 points [-4.6, -1.7]; non-inferiority (upper bound below 2 points) holds.
- Phase 2 gate: GO.

## Design

- Tasks: address, variant, sequence; test cases per task: address 999 (333 groups), variant 999 (333 groups), sequence 999 (333 groups)
- Writers: T+, S+, T; learning runs per writer and task: 12
- Arms: b0, b1, learned, generic, full_context, search_control, best_of_n, human
- Checker: status ok, mode real, decision rows 267732

## Registered analysis

- Primary: T+ endpoint vs its no-evidence search control, accuracy, pooled over tasks with equal weights. Superiority: lower bound of the two-sided 95% interval above 0 points.
- Secondary (tested only if the primary succeeds): S+ (self-written, advisory self-critic) endpoint vs its search control.
- Unit: per-case paired difference (same case, same run), averaged within scenario group, crossed with learning run. Interval: crossed random-effects model (run x group, task fixed), parametric bootstrap-t, 10000 draws, seed 20261010.
- Wrong-write non-inferiority: upper 95% bound below 2 points.

## Verdicts

| Contrast | Role | Accuracy (points) | 95% interval | Wrong writes (points) | 95% interval |
|---|---|---|---|---|---|
| T+ endpoint vs its search control | confirmatory (primary) | +4.0 | [+2.3, +5.7] | -3.1 | [-4.6, -1.7] |
| S+ (self-written, advisory self-critic) endpoint vs its search control | confirmatory (secondary, gated) | +2.0 | [+0.02*, +4.0] | -1.5 | [-3.6, +0.6] |

## Phase 2 gate

- Rule: phase 2 only if the primary succeeds and wrong-write non-inferiority holds (primary and, if tested, secondary writer).
- Primary superiority: yes (estimate +4.0, interval [+2.3, +5.7]); reaches 5 points: no.
- Primary wrong-write non-inferiority: yes (upper bound -1.7).
- Secondary: tested because the primary succeeded; superiority yes [+0.02*, +4.0]; wrong-write non-inferiority yes [-3.6, +0.6].
- **Phase 2: GO** (narrow reading, primary writer's wrong writes only: GO).

## Per task (secondary, descriptive)

| Contrast | Task | Points | 95% interval |
|---|---|---|---|
| T+ endpoint vs its search control | address | +3.9 | [+0.5, +7.1] |
| T+ endpoint vs its search control | variant | +1.7 | [-0.1, +3.5] |
| T+ endpoint vs its search control | sequence | +6.5 | [+3.7, +9.4] |
| S+ (self-written, advisory self-critic) endpoint vs its search control | address | +5.5 | [+1.7, +9.3] |
| S+ (self-written, advisory self-critic) endpoint vs its search control | variant | +2.3 | [-0.1, +4.8] |
| S+ (self-written, advisory self-critic) endpoint vs its search control | sequence | -1.7 | [-8.1, +4.6] |

## Sensitivity of the primary interval (descriptive)

- Percentile parametric bootstrap: [+2.5, +5.6]; closed-form Satterthwaite: [+2.4, +5.7].
- Non-parametric run x group bootstrap: [+2.5, +5.7]
- Non-parametric run x family bootstrap: [+2.1, +6.2]
- Non-parametric run x user bootstrap: [+2.5, +5.7]
- Between-run SD of the pooled run means: 2.5 points.

## Other contrasts (descriptive)

| Contrast | Role | Accuracy (points) | 95% interval | Wrong writes (points) | 95% interval |
|---|---|---|---|---|---|
| T+ endpoint vs B1 (base prompt; = removal) | descriptive | +10.5 | [+8.5, +12.5] | -9.9 | [-11.6, -8.1] |
| T+ endpoint vs B0 (model only) | descriptive | +12.3 | [+10.1, +14.5] | -10.4 | [-12.3, -8.5] |
| T+ endpoint vs Same-length generic note | descriptive | +11.1 | [+9.2, +13.0] | -7.6 | [-9.7, -5.4] |
| T+ endpoint vs Full context (evidence) | descriptive | +4.9 | [+2.4, +7.4] | -2.5 | [-4.3, -0.7] |
| T+ endpoint vs Best-of-N | descriptive | +10.6 | [+8.5, +12.7] | -4.5 | [-6.1, -2.9] |
| T+ endpoint vs Person-written procedure | descriptive | -0.1 | [-1.9, +1.8] | +2.8 | [+1.5, +4.0] |
| S+ endpoint vs B1 (base prompt; = removal) | descriptive | +10.3 | [+8.2, +12.5] | -9.6 | [-11.6, -7.6] |
| S+ endpoint vs B0 (model only) | descriptive | +12.1 | [+9.8, +14.4] | -10.1 | [-12.2, -8.0] |
| S+ endpoint vs Same-length generic note | descriptive | +10.9 | [+8.7, +13.2] | -7.3 | [-9.6, -5.0] |
| S+ endpoint vs Full context (evidence) | descriptive | +4.8 | [+1.8, +7.8] | -2.1 | [-4.0, -0.1] |
| S+ endpoint vs Best-of-N | descriptive | +10.4 | [+8.2, +12.7] | -4.2 | [-6.1, -2.3] |
| S+ endpoint vs Person-written procedure | descriptive | -0.2 | [-2.3, +1.8] | +3.1 | [+1.4, +4.8] |
| T endpoint vs No-evidence search control | descriptive | +4.8 | [+2.5, +7.1] | -5.6 | [-8.1, -3.1] |
| T endpoint vs B1 (base prompt; = removal) | descriptive | +9.1 | [+7.1, +11.1] | -10.7 | [-12.8, -8.5] |
| T endpoint vs B0 (model only) | descriptive | +10.9 | [+8.7, +13.0] | -11.2 | [-13.5, -9.0] |
| T endpoint vs Same-length generic note | descriptive | +8.6 | [+5.9, +11.2] | -5.7 | [-8.7, -2.8] |
| T endpoint vs Full context (evidence) | descriptive | +3.2 | [+0.4, +5.9] | -3.3 | [-5.4, -1.2] |
| T endpoint vs Best-of-N | descriptive | +9.2 | [+7.2, +11.2] | -5.3 | [-7.4, -3.3] |
| T endpoint vs Person-written procedure | descriptive | -1.5 | [-3.1, +0.1] | +2.0 | [+0.2, +3.7] |
| B1 vs B0 | descriptive | +1.8 | [+0.5, +3.0] | -0.5 | [-1.4, +0.3] |

## Arms, pooled over tasks (mean over runs)

| Writer | Arm | Accuracy | Wrong write | Unnecessary question | Missed clarification |
|---|---|---|---|---|---|
| shared | b0 | 68.6% | 15.5% | 8.1% | 6.4% |
| shared | b1 | 70.3% | 15.0% | 7.7% | 5.7% |
| T+ | learned | 80.9% | 5.1% | 7.2% | 4.3% |
| S+ | learned | 80.7% | 5.4% | 7.0% | 3.5% |
| T | learned | 79.4% | 4.3% | 8.1% | 3.7% |
| T+ | generic | 69.7% | 12.7% | 9.2% | 3.5% |
| S+ | generic | 69.7% | 12.7% | 9.4% | 3.8% |
| T | generic | 70.9% | 10.0% | 9.7% | 2.2% |
| T+ | full_context | 75.9% | 7.6% | 11.9% | 1.1% |
| S+ | full_context | 75.8% | 7.5% | 12.4% | 1.0% |
| T | full_context | 76.3% | 7.6% | 11.7% | 1.1% |
| T+ | search_control | 76.8% | 8.2% | 7.9% | 5.5% |
| S+ | search_control | 78.7% | 6.9% | 7.8% | 5.7% |
| T | search_control | 74.6% | 9.9% | 8.0% | 5.2% |
| shared | best_of_n | 70.2% | 9.6% | 11.4% | 3.5% |
| shared | human | 80.9% | 2.3% | 8.5% | 2.6% |

### address

| Writer | Arm | Accuracy | Run SD | Wrong write | Unnecessary question | Missed clarification | Outcomes |
|---|---|---|---|---|---|---|---|
| shared | b0 | 76.4% | n/a | 6.2% | 14.2% | 6.5% | correct 763, missed_clarification 3, missing_confirmation 24, non_question_message 5, unnecessary_question 142, wrong_write 62 |
| shared | b1 | 75.7% | n/a | 8.1% | 13.2% | 8.1% | correct 756, missing_confirmation 22, non_question_message 8, unnecessary_question 132, wrong_write 81 |
| T+ | learned | 79.6% | 5.1 | 5.8% | 11.0% | 5.9% | correct 9538, missed_clarification 9, missing_confirmation 351, non_question_message 71, transfer 6, unnecessary_question 1318, wrong_write 695 |
| S+ | learned | 81.1% | 5.6 | 4.3% | 10.3% | 4.6% | correct 9727, missed_clarification 27, missing_confirmation 398, non_question_message 82, transfer 2, unnecessary_question 1232, wrong_write 520 |
| T | learned | 79.0% | 5.0 | 5.1% | 10.4% | 5.6% | correct 9474, missed_clarification 60, missing_confirmation 488, non_question_message 100, transfer 1, unnecessary_question 1250, wrong_write 615 |
| T+ | generic | 75.3% | 1.2 | 5.1% | 13.7% | 5.4% | correct 9029, missed_clarification 31, missing_confirmation 588, non_question_message 89, transfer 6, unnecessary_question 1639, wrong_write 606 |
| S+ | generic | 75.5% | 0.9 | 5.3% | 14.4% | 5.6% | correct 9045, missed_clarification 18, missing_confirmation 453, non_question_message 90, transfer 23, unnecessary_question 1728, wrong_write 631 |
| T | generic | 75.4% | 1.1 | 2.9% | 14.0% | 3.5% | correct 9043, missed_clarification 62, missing_confirmation 761, no_decision 3, non_question_message 83, transfer 8, unnecessary_question 1684, wrong_write 344 |
| T+ | full_context | 83.2% | 4.0 | 1.8% | 13.4% | 1.9% | correct 9973, missed_clarification 11, missing_confirmation 173, non_question_message 3, unnecessary_question 1610, wrong_write 218 |
| S+ | full_context | 83.4% | 3.9 | 1.2% | 14.2% | 1.3% | correct 9993, missed_clarification 8, missing_confirmation 132, unnecessary_question 1707, wrong_write 148 |
| T | full_context | 84.4% | 3.2 | 1.6% | 12.6% | 1.7% | correct 10114, missed_clarification 6, missing_confirmation 158, non_question_message 4, unnecessary_question 1512, wrong_write 194 |
| T+ | search_control | 75.7% | 0.0 | 7.6% | 13.5% | 7.7% | correct 9072, missed_clarification 1, missing_confirmation 283, non_question_message 94, transfer 1, unnecessary_question 1620, wrong_write 917 |
| S+ | search_control | 75.7% | 0.0 | 8.1% | 13.2% | 8.1% | correct 9072, missing_confirmation 264, non_question_message 96, unnecessary_question 1584, wrong_write 972 |
| T | search_control | 75.7% | 0.3 | 7.3% | 13.6% | 7.4% | correct 9072, missed_clarification 12, missing_confirmation 299, non_question_message 101, transfer 4, unnecessary_question 1630, wrong_write 870 |
| shared | best_of_n | 77.1% | n/a | 3.3% | 16.1% | 3.3% | correct 770, missing_confirmation 27, non_question_message 8, unnecessary_question 161, wrong_write 33 |
| shared | human | 77.8% | n/a | 4.0% | 12.7% | 4.7% | correct 777, missed_clarification 6, missing_confirmation 41, non_question_message 7, transfer 1, unnecessary_question 127, wrong_write 40 |

### variant

| Writer | Arm | Accuracy | Run SD | Wrong write | Unnecessary question | Missed clarification | Outcomes |
|---|---|---|---|---|---|---|---|
| shared | b0 | 62.4% | n/a | 10.6% | 10.1% | 12.7% | correct 623, missed_clarification 17, missing_confirmation 97, non_question_message 51, transfer 4, unnecessary_question 101, wrong_write 106 |
| shared | b1 | 68.1% | n/a | 7.1% | 10.0% | 8.9% | correct 680, missed_clarification 16, missing_confirmation 94, non_question_message 36, transfer 2, unnecessary_question 100, wrong_write 71 |
| T+ | learned | 69.8% | 2.4 | 5.1% | 10.3% | 7.0% | correct 8364, missed_clarification 210, missing_confirmation 1103, non_question_message 446, transfer 18, unnecessary_question 1231, wrong_write 616 |
| S+ | learned | 70.4% | 3.5 | 4.4% | 10.5% | 6.1% | correct 8435, missed_clarification 176, missing_confirmation 1135, non_question_message 429, transfer 18, unnecessary_question 1262, wrong_write 533 |
| T | learned | 68.9% | 2.7 | 3.4% | 11.5% | 5.4% | correct 8260, missed_clarification 222, missing_confirmation 1260, non_question_message 435, transfer 20, unnecessary_question 1382, wrong_write 409 |
| T+ | generic | 66.7% | 1.5 | 3.3% | 13.8% | 5.1% | correct 7991, missed_clarification 202, missing_confirmation 1277, non_question_message 459, transfer 13, unnecessary_question 1653, wrong_write 393 |
| S+ | generic | 66.5% | 2.6 | 3.2% | 13.8% | 5.7% | correct 7971, missed_clarification 158, missing_confirmation 1252, non_question_message 432, transfer 139, unnecessary_question 1649, wrong_write 387 |
| T | generic | 66.8% | 1.8 | 0.9% | 14.9% | 3.2% | correct 8006, missed_clarification 256, missing_confirmation 1250, non_question_message 565, transfer 15, unnecessary_question 1786, wrong_write 110 |
| T+ | full_context | 68.1% | 1.6 | 1.3% | 18.9% | 1.5% | correct 8167, missed_clarification 25, missing_confirmation 1300, non_question_message 72, unnecessary_question 2269, wrong_write 155 |
| S+ | full_context | 67.9% | 1.6 | 1.5% | 19.2% | 1.7% | correct 8141, missed_clarification 25, missing_confirmation 1311, non_question_message 31, unnecessary_question 2301, wrong_write 179 |
| T | full_context | 68.0% | 1.8 | 1.5% | 19.1% | 1.7% | correct 8151, missed_clarification 22, missing_confirmation 1303, non_question_message 48, unnecessary_question 2287, wrong_write 177 |
| T+ | search_control | 68.1% | 0.0 | 7.1% | 10.0% | 8.9% | correct 8160, missed_clarification 192, missing_confirmation 1128, non_question_message 432, transfer 24, unnecessary_question 1200, wrong_write 852 |
| S+ | search_control | 68.1% | 0.0 | 7.1% | 10.0% | 8.9% | correct 8160, missed_clarification 192, missing_confirmation 1128, non_question_message 432, transfer 24, unnecessary_question 1200, wrong_write 852 |
| T | search_control | 67.9% | 0.7 | 6.1% | 10.3% | 8.1% | correct 8142, missed_clarification 217, missing_confirmation 1154, non_question_message 484, transfer 21, unnecessary_question 1240, wrong_write 730 |
| shared | best_of_n | 62.0% | n/a | 4.4% | 17.2% | 7.1% | correct 619, missed_clarification 24, missing_confirmation 94, non_question_message 43, transfer 3, unnecessary_question 172, wrong_write 44 |
| shared | human | 69.6% | n/a | 0.4% | 12.6% | 3.2% | correct 695, missed_clarification 27, missing_confirmation 95, non_question_message 51, transfer 1, unnecessary_question 126, wrong_write 4 |

### sequence

| Writer | Arm | Accuracy | Run SD | Wrong write | Unnecessary question | Missed clarification | Outcomes |
|---|---|---|---|---|---|---|---|
| shared | b0 | 67.0% | n/a | 29.7% | 0.0% | 0.0% | correct 669, missing_confirmation 24, non_question_message 9, wrong_write 297 |
| shared | b1 | 67.3% | n/a | 29.7% | 0.0% | 0.0% | correct 672, missing_confirmation 19, non_question_message 11, wrong_write 297 |
| T+ | learned | 93.3% | 2.9 | 4.4% | 0.4% | 0.0% | correct 11180, missing_confirmation 155, non_question_message 77, unnecessary_question 49, wrong_write 527 |
| S+ | learned | 90.5% | 6.6 | 7.4% | 0.2% | 0.0% | correct 10855, missing_confirmation 166, non_question_message 55, unnecessary_question 21, wrong_write 891 |
| T | learned | 90.4% | 6.7 | 4.3% | 2.5% | 0.0% | correct 10838, missing_confirmation 294, non_question_message 38, unnecessary_question 297, wrong_write 521 |
| T+ | generic | 67.3% | 0.0 | 29.7% | 0.0% | 0.0% | correct 8064, missing_confirmation 228, non_question_message 132, wrong_write 3564 |
| S+ | generic | 67.3% | 0.0 | 29.7% | 0.0% | 0.0% | correct 8064, missing_confirmation 228, non_question_message 132, wrong_write 3564 |
| T | generic | 70.4% | 7.7 | 26.3% | 0.2% | 0.0% | correct 8444, missing_confirmation 254, non_question_message 120, unnecessary_question 23, wrong_write 3147 |
| T+ | full_context | 76.5% | 6.4 | 19.8% | 3.4% | 0.0% | correct 9172, missing_confirmation 8, non_question_message 27, unnecessary_question 413, wrong_write 2368 |
| S+ | full_context | 76.3% | 6.9 | 19.7% | 3.7% | 0.0% | correct 9142, missing_confirmation 19, non_question_message 18, unnecessary_question 442, wrong_write 2367 |
| T | full_context | 76.4% | 6.8 | 19.7% | 3.5% | 0.0% | correct 9160, missing_confirmation 20, non_question_message 23, unnecessary_question 420, wrong_write 2365 |
| T+ | search_control | 86.7% | 4.5 | 9.9% | 0.2% | 0.0% | correct 10397, missing_confirmation 302, non_question_message 74, unnecessary_question 23, wrong_write 1192 |
| S+ | search_control | 92.3% | 8.3 | 5.5% | 0.1% | 0.0% | correct 11059, missing_confirmation 199, non_question_message 53, unnecessary_question 17, wrong_write 660 |
| T | search_control | 80.3% | 8.1 | 16.2% | 0.2% | 0.0% | correct 9631, missing_confirmation 324, non_question_message 61, unnecessary_question 24, wrong_write 1948 |
| shared | best_of_n | 71.7% | n/a | 21.2% | 1.0% | 0.0% | correct 716, missing_confirmation 33, non_question_message 28, unnecessary_question 10, wrong_write 212 |
| shared | human | 95.4% | n/a | 2.6% | 0.2% | 0.0% | correct 953, missing_confirmation 14, non_question_message 4, unnecessary_question 2, wrong_write 26 |

## Endpoint scores per learning run

| Writer | Task | Mean difference | Run SD | Runs above 0 | Reverted on sentinel (learned) | Reverted on sentinel (search control) |
|---|---|---|---|---|---|---|
| T+ | address | +3.9 | 5.1 | 5/12 | 8/12 | 11/12 |
| T+ | variant | +1.7 | 2.4 | 5/12 | 5/12 | 8/12 |
| T+ | sequence | +6.5 | 4.1 | 12/12 | 3/12 | 3/12 |
| S+ | address | +5.5 | 5.6 | 7/12 | 6/12 | 0/12 |
| S+ | variant | +2.3 | 3.5 | 5/12 | 6/12 | 0/12 |
| S+ | sequence | -1.7 | 10.0 | 6/12 | 3/12 | 2/12 |
| T | address | +3.4 | 5.2 | 6/12 | 8/12 | 7/12 |
| T | variant | +1.0 | 2.6 | 5/12 | 7/12 | 8/12 |
| T | sequence | +10.1 | 11.7 | 10/12 | 6/12 | 0/12 |

## Learning curves

Mean over runs; dev accuracy of the current skill after each proposal (lesson loops) or training-stream accuracy per batch (note loop).

| Writer / task | Arm | Start | End | Sentinel reverts |
|---|---|---|---|---|
| S+ / address | learned (dev) | 77.6% | 87.6% | 6/12 |
| S+ / address | search_control (dev) | 76.7% | 76.7% | 0/12 |
| T / address | learned (train stream) | 66.7% | 83.3% | 8/12 |
| T+ / address | learned (dev) | 76.8% | 88.8% | 8/12 |
| T+ / address | search_control (dev) | 76.5% | 81.2% | 11/12 |
| S+ / sequence | learned (dev) | 64.7% | 90.1% | 3/12 |
| S+ / sequence | search_control (dev) | 65.0% | 95.1% | 2/12 |
| T / sequence | learned (train stream) | 62.5% | 93.8% | 6/12 |
| T+ / sequence | learned (dev) | 64.6% | 97.1% | 3/12 |
| T+ / sequence | search_control (dev) | 64.6% | 93.5% | 3/12 |
| S+ / variant | learned (dev) | 67.4% | 73.9% | 6/12 |
| S+ / variant | search_control (dev) | 67.1% | 67.1% | 0/12 |
| T / variant | learned (train stream) | 68.8% | 66.7% | 7/12 |
| T+ / variant | learned (dev) | 67.5% | 78.1% | 5/12 |
| T+ / variant | search_control (dev) | 66.7% | 69.3% | 8/12 |

## Costs

- GPU-hours: 653.4 (from the ledger file)
- Test decisions: 267,732; model calls 274,150; prompt tokens 13,328,448,452; completion tokens 101,661,592; errors 0; time limits 0
- Agent time on test decisions: 482.8 hours (sum of per-case wall time); learning wall time 0.0 hours
- Learning budgets used (all runs): calls 3,713, decisions 75,018, output_tokens 1,896,788

## Training-sample overlap between runs

- address: mean 32%, max 44% (expected 32%)
- variant: mean 13%, max 25% (expected 12%)
- sequence: mean 12%, max 19% (expected 12%)

## Missing arms

- Removal: equals B1 by design (not run separately).

## Deviations

- none

## Ambiguities in the registered text and how they were read

- Gate scope of wrong-write non-inferiority: plan v1.2 defines it 'for the primary and, if tested, the secondary writer' and gates on 'wrong-write non-inferiority holds'. Conservative reading used: the gate needs both when the secondary is tested. The verdict under the narrower reading (primary writer only) is reported alongside.
- Parametric bootstrap form: not specified. Bootstrap-t (studentised draws) is used, which carries the uncertainty of the estimated variance components; the percentile and the closed-form Satterthwaite intervals are reported as sensitivity.
- Older gate wording (plan 'Phases and gates' table: endpoint vs its generic note and best-of-N, lower bound above a registered minimum gain, wrong writes vs B1) is superseded by v1.2 ('where they differ, v1.2 wins'): superiority over the search control at 0, with the 5-point minimum worthwhile gain reported, not gated.
- 'Cluster by request family where groups share a template' and the address-task user-cluster analysis are not part of the registered interval; both are reported as descriptive sensitivity checks (non-parametric run x cluster bootstrap).
- Wrong-write non-inferiority uses the same crossed model on the per-case wrong-write difference (endpoint minus search control) with a two-sided 95% upper bound.

## Caveats

- Single-use test set: the sealed test questions are public in the partner kit and their answers stay with us; this analysis is their one registered use. Any later look at the same cases is exploratory.
- Honest-partner model: the partner ran all GPU work. Our checker verifies hashes, the registered plan, learning provenance and answer-key leakage, but cannot prove how the runs were executed beyond what the export records.
- Synthetic identities: every customer, order and request is generated from the public benchmark database; no real person is involved, and results speak to these generated decision cases only.
- Learning runs share training cases (overlapping 48-case samples from a 150- or 400-case pool), which makes runs less independent than the power simulation assumes; the measured overlap is reported.
- The teacher was self-hosted at the partner (FP8), a recorded deviation from POC 9's hosted endpoint.
- Per-task contrasts, all control arms and the T writer are descriptive; only the pooled primary contrast (and, behind its gate, the secondary) is confirmatory.

* shown to more decimals: one-decimal rounding would meet or cross the decision threshold; results.json keeps the unrounded value the gate used.
