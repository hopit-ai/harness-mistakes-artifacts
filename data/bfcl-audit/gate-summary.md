# BFCL evaluator-defect audit: gate part (frozen, round r2, rubric v2)

Pre-registered in docs/xp/bfcl-plan.md §6.4. Frozen 2026-10-21T15:25:04+00:00; `gate-defects.json` is hashed in learner_runs/REGISTRY.jsonl. Official scoring stays primary; this list feeds the audited sensitivity only and is never revised. Defective = score-changing **and** severity clear (amendment 2026-10-21).

| Scope | Defective (clear) |
|---|---|
| All gate instances | 42/60 = 70.0% (Wilson 95% 57.5–80.1%) |
| family files | 14/18 = 77.8% (Wilson 95% 54.8–91.0%) |
| family finance | 8/14 = 57.1% (Wilson 95% 32.6–78.6%) |
| family travel | 12/16 = 75.0% (Wilson 95% 50.5–89.8%) |
| family vehicle | 8/12 = 66.7% (Wilson 95% 39.1–86.2%) |
| base | 20/30 = 66.7% (Wilson 95% 48.8–80.8%) |
| long_context | 22/30 = 73.3% (Wilson 95% 55.5–85.8%) |
| Epoch AI, multi-turn sample (all four categories) | 8/15 = 53.3% (Wilson 95% 30.1–75.2%) |
| Descriptive: score-changing, any severity | 51/60 = 85.0% (Wilson 95% 73.9–91.9%) |
| Descriptive: arguable only | 9/60 = 15.0% (Wilson 95% 8.1–26.1%) |

Reviewer agreement on the defective (clear) flag: raw 0.9354838709677419, Cohen's κ 0.8442211055276381; on score-changing: raw 0.9354838709677419, Cohen's κ 0.7947019867549666 (62 instances with both labels); escalated 19, decided by the owner 19.

Roots with both instances defective: [7, 12, 14, 24, 39, 45, 52, 72, 78, 81, 95, 103, 123, 141, 146, 152, 162, 168, 195, 199]

## Defective instances

| Instance | Family | Classes | Failing turn | Decided by |
|---|---|---|---|---|
| multi_turn_base_103 | finance | FN | 1 | owner |
| multi_turn_base_12 | files | FN | 2 | agreed |
| multi_turn_base_123 | finance | FN | 1 | agreed |
| multi_turn_base_14 | files | FN | 1 | agreed |
| multi_turn_base_141 | finance | FN | 3 | agreed |
| multi_turn_base_146 | finance | FN | 3 | agreed |
| multi_turn_base_152 | travel | FN, IMP | 1 | owner |
| multi_turn_base_162 | travel | IMP | 3 | agreed |
| multi_turn_base_168 | travel | FN | 4 | agreed |
| multi_turn_base_195 | travel | FN, IMP | 2 | owner |
| multi_turn_base_199 | travel | FN | 4 | agreed |
| multi_turn_base_24 | files | FN | 0 | agreed |
| multi_turn_base_39 | files | FN | 2 | owner |
| multi_turn_base_45 | files | FN | 0 | agreed |
| multi_turn_base_52 | vehicle | FN | 0 | owner |
| multi_turn_base_7 | files | FN | 1 | agreed |
| multi_turn_base_72 | vehicle | FN | 3 | agreed |
| multi_turn_base_78 | vehicle | FN | 0 | agreed |
| multi_turn_base_81 | files | FN | 0 | owner |
| multi_turn_base_95 | vehicle | FN | 3 | agreed |
| multi_turn_long_context_103 | finance | FN | 1 | owner |
| multi_turn_long_context_12 | files | FN | 2 | agreed |
| multi_turn_long_context_123 | finance | FN | 1 | agreed |
| multi_turn_long_context_14 | files | FN | 1 | agreed |
| multi_turn_long_context_141 | finance | FN | 3 | agreed |
| multi_turn_long_context_146 | finance | FN | 3 | agreed |
| multi_turn_long_context_150 | travel | FP, IMP | 0 | owner |
| multi_turn_long_context_151 | travel | IMP | 0 | agreed |
| multi_turn_long_context_152 | travel | FN, IMP | 1 | owner |
| multi_turn_long_context_162 | travel | IMP | 3 | agreed |
| multi_turn_long_context_168 | travel | FN | 4 | agreed |
| multi_turn_long_context_195 | travel | FN, IMP | 2 | owner |
| multi_turn_long_context_199 | travel | FN | 4 | agreed |
| multi_turn_long_context_24 | files | FN | 0 | agreed |
| multi_turn_long_context_39 | files | FN | 2 | owner |
| multi_turn_long_context_45 | files | FN | 0 | agreed |
| multi_turn_long_context_52 | vehicle | FN | 0 | owner |
| multi_turn_long_context_7 | files | FN | 1 | agreed |
| multi_turn_long_context_72 | vehicle | FN | 3 | agreed |
| multi_turn_long_context_78 | vehicle | FN | 0 | agreed |
| multi_turn_long_context_81 | files | FN | 0 | owner |
| multi_turn_long_context_95 | vehicle | FN | 3 | agreed |

## Arguable (score-changing, severity arguable; descriptive only)

- multi_turn_base_102 (finance): FN, failing turn 1, owner
- multi_turn_base_130 (finance): FN, failing turn 3, owner
- multi_turn_base_132 (finance): FN, IMP, failing turn 1, agreed
- multi_turn_base_150 (travel): FP, failing turn 0, owner
- multi_turn_base_71 (vehicle): FN, failing turn 3, agreed
- multi_turn_long_context_102 (finance): FN, failing turn 1, owner
- multi_turn_long_context_130 (finance): FN, failing turn 3, owner
- multi_turn_long_context_132 (finance): FN, IMP, failing turn 1, agreed
- multi_turn_long_context_71 (vehicle): FN, failing turn 3, agreed

## Descriptive extra (not in the rates)

- multi_turn_base_23 (descriptive-extra): none, score-changing no, severity None
- multi_turn_long_context_23 (descriptive-extra): FN, score-changing no, severity None

## Superseded rounds (kept, never used for this list)

- r1 (rubric v1, `gate`, manifest `9d29a3ad9bfe`, 16 result files): score-changing yes A 60, B 60 of 62; κ -0.03333333333333665; superseded (amendment 2026-10-21, docs/xp/bfcl-plan.md §6.4)
