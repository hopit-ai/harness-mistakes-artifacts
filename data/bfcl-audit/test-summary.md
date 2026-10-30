# BFCL evaluator-defect audit: test part (frozen, round r2, rubric v2)

Pre-registered in docs/xp/bfcl-plan.md §6.4. Frozen 2026-10-22T10:12:39+00:00; `test-defects.json` is hashed in learner_runs/REGISTRY.jsonl. Official scoring stays primary; this list feeds the audited sensitivity only and is never revised. Defective = score-changing **and** severity clear (amendment 2026-10-21).

| Scope | Defective (clear) |
|---|---|
| All test instances | 146/240 = 60.8% (Wilson 95% 54.5–66.8%) |
| family files | 56/78 = 71.8% (Wilson 95% 61.0–80.6%) |
| family finance | 27/52 = 51.9% (Wilson 95% 38.7–64.9%) |
| family travel | 37/54 = 68.5% (Wilson 95% 55.3–79.3%) |
| family vehicle | 26/56 = 46.4% (Wilson 95% 34.0–59.3%) |
| base | 70/120 = 58.3% (Wilson 95% 49.4–66.8%) |
| long_context | 76/120 = 63.3% (Wilson 95% 54.4–71.4%) |
| Epoch AI, multi-turn sample (all four categories) | 8/15 = 53.3% (Wilson 95% 30.1–75.2%) |
| Descriptive: score-changing, any severity | 198/240 = 82.5% (Wilson 95% 77.2–86.8%) |
| Descriptive: arguable only | 52/240 = 21.7% (Wilson 95% 16.9–27.3%) |

Reviewer agreement on the defective (clear) flag: raw 0.925, Cohen's κ 0.836065573770492; on score-changing: raw 0.9208333333333333, Cohen's κ 0.7651905252317198 (240 instances with both labels); escalated 55, decided by the owner 55.

Roots with both instances defective: [1, 2, 4, 6, 8, 10, 13, 16, 18, 19, 21, 22, 25, 26, 28, 31, 32, 34, 35, 36, 38, 48, 49, 55, 58, 59, 60, 65, 68, 69, 70, 74, 75, 79, 84, 86, 87, 94, 104, 106, 108, 114, 120, 121, 125, 133, 135, 139, 143, 145, 149, 154, 155, 159, 161, 165, 171, 173, 174, 178, 179, 183, 184, 185, 188, 189, 193, 194]

## Defective instances

| Instance | Family | Classes | Failing turn | Decided by |
|---|---|---|---|---|
| multi_turn_base_1 | files | FP | 0 | agreed |
| multi_turn_base_10 | files | FN | 1 | agreed |
| multi_turn_base_104 | finance | FN | 1 | agreed |
| multi_turn_base_106 | finance | FN | 2 | agreed |
| multi_turn_base_108 | finance | FN | 2 | agreed |
| multi_turn_base_114 | finance | IMP | 3 | agreed |
| multi_turn_base_120 | finance | FP, IMP | 0 | agreed |
| multi_turn_base_121 | finance | FN | 3 | agreed |
| multi_turn_base_125 | finance | FN | 3 | agreed |
| multi_turn_base_13 | files | FN | 1 | agreed |
| multi_turn_base_133 | finance | FN | 0 | agreed |
| multi_turn_base_135 | finance | FN | 0 | agreed |
| multi_turn_base_139 | finance | FN | 1 | agreed |
| multi_turn_base_143 | finance | FN | 3 | agreed |
| multi_turn_base_145 | finance | IMP | 3 | agreed |
| multi_turn_base_149 | finance | FP | 0 | agreed |
| multi_turn_base_154 | travel | FN | 4 | agreed |
| multi_turn_base_155 | travel | FN, FP | 0 | owner |
| multi_turn_base_159 | travel | IMP | 2 | agreed |
| multi_turn_base_16 | files | FN | 0 | agreed |
| multi_turn_base_161 | files | FN, FP | 0 | owner |
| multi_turn_base_165 | travel | IMP | 2 | agreed |
| multi_turn_base_171 | travel | FP, IMP | 0 | agreed |
| multi_turn_base_173 | travel | IMP | 3 | agreed |
| multi_turn_base_174 | travel | FP | 1 | owner |
| multi_turn_base_176 | travel | FN | 1 | agreed |
| multi_turn_base_178 | travel | FN, IMP | 3 | agreed |
| multi_turn_base_179 | travel | FP, IMP | 0 | owner |
| multi_turn_base_18 | files | FN | 2 | agreed |
| multi_turn_base_183 | travel | FP | 0 | agreed |
| multi_turn_base_184 | travel | FN, FP | 0 | owner |
| multi_turn_base_185 | travel | FN | 0 | agreed |
| multi_turn_base_188 | travel | FN | 4 | agreed |
| multi_turn_base_189 | travel | FN, FP | 0 | owner |
| multi_turn_base_19 | files | FN | 1 | agreed |
| multi_turn_base_193 | travel | FP | 1 | agreed |
| multi_turn_base_194 | travel | FN, IMP | 1 | owner |
| multi_turn_base_2 | files | FN | 3 | agreed |
| multi_turn_base_21 | files | FN | 1 | agreed |
| multi_turn_base_22 | files | FN | 2 | owner |
| multi_turn_base_25 | files | FN | 2 | agreed |
| multi_turn_base_26 | files | FN | 2 | agreed |
| multi_turn_base_28 | files | FN | 2 | agreed |
| multi_turn_base_30 | files | FN | 1 | agreed |
| multi_turn_base_31 | files | FN | 0 | owner |
| multi_turn_base_32 | files | FN | 1 | agreed |
| multi_turn_base_34 | files | FN | 1 | agreed |
| multi_turn_base_35 | files | FN | 0 | agreed |
| multi_turn_base_36 | files | FN | 1 | owner |
| multi_turn_base_38 | files | FN | 0 | agreed |
| multi_turn_base_4 | files | FN | 2 | agreed |
| multi_turn_base_48 | files | FP | 0 | agreed |
| multi_turn_base_49 | files | FN | 1 | agreed |
| multi_turn_base_55 | vehicle | FP | 3 | agreed |
| multi_turn_base_58 | vehicle | FN | 1 | agreed |
| multi_turn_base_59 | files | FN | 1 | agreed |
| multi_turn_base_6 | files | FN | 3 | agreed |
| multi_turn_base_60 | vehicle | FP | 3 | agreed |
| multi_turn_base_65 | vehicle | FN | 0 | agreed |
| multi_turn_base_68 | vehicle | FN | 4 | agreed |
| multi_turn_base_69 | vehicle | FN | 0 | agreed |
| multi_turn_base_70 | vehicle | FN | 0 | agreed |
| multi_turn_base_74 | files | FN | 0 | agreed |
| multi_turn_base_75 | vehicle | FN | 3 | agreed |
| multi_turn_base_79 | vehicle | FN | 2 | agreed |
| multi_turn_base_8 | files | FN | 2 | agreed |
| multi_turn_base_84 | vehicle | FN | 0 | agreed |
| multi_turn_base_86 | vehicle | FN, FP | 0 | owner |
| multi_turn_base_87 | vehicle | FN | 2 | agreed |
| multi_turn_base_94 | vehicle | FN | 2 | agreed |
| multi_turn_long_context_1 | files | FP | 0 | agreed |
| multi_turn_long_context_10 | files | FN | 1 | agreed |
| multi_turn_long_context_104 | finance | FN | 1 | agreed |
| multi_turn_long_context_106 | finance | FN | 2 | agreed |
| multi_turn_long_context_108 | finance | FN | 2 | agreed |
| multi_turn_long_context_113 | finance | FN | 1 | agreed |
| multi_turn_long_context_114 | finance | IMP | 3 | agreed |
| multi_turn_long_context_120 | finance | FP, IMP | 0 | agreed |
| multi_turn_long_context_121 | finance | FN | 3 | agreed |
| multi_turn_long_context_125 | finance | FN | 3 | agreed |
| multi_turn_long_context_13 | files | FN | 1 | agreed |
| multi_turn_long_context_133 | finance | FN | 0 | agreed |
| multi_turn_long_context_135 | finance | FN | 0 | agreed |
| multi_turn_long_context_139 | finance | FN | 0 | agreed |
| multi_turn_long_context_143 | finance | FN | 3 | agreed |
| multi_turn_long_context_145 | finance | IMP | 3 | agreed |
| multi_turn_long_context_149 | finance | FP | 0 | agreed |
| multi_turn_long_context_153 | travel | FP | 1 | agreed |
| multi_turn_long_context_154 | travel | FN | 1 | agreed |
| multi_turn_long_context_155 | travel | FN, FP | 0 | owner |
| multi_turn_long_context_159 | travel | IMP | 2 | agreed |
| multi_turn_long_context_16 | files | FN | 0 | agreed |
| multi_turn_long_context_161 | files | FN, FP | 0 | owner |
| multi_turn_long_context_165 | travel | IMP | 2 | agreed |
| multi_turn_long_context_171 | travel | FP, IMP | 0 | agreed |
| multi_turn_long_context_172 | travel | FN | 1 | agreed |
| multi_turn_long_context_173 | travel | FN, IMP | 1 | owner |
| multi_turn_long_context_174 | travel | FP | 1 | owner |
| multi_turn_long_context_178 | travel | FN, IMP | 3 | agreed |
| multi_turn_long_context_179 | travel | FP, IMP | 0 | owner |
| multi_turn_long_context_18 | files | FN | 2 | agreed |
| multi_turn_long_context_183 | travel | FP | 0 | agreed |
| multi_turn_long_context_184 | travel | FN, FP | 0 | owner |
| multi_turn_long_context_185 | travel | FN | 0 | agreed |
| multi_turn_long_context_186 | travel | FP | 3 | agreed |
| multi_turn_long_context_188 | travel | FN | 4 | agreed |
| multi_turn_long_context_189 | travel | FN, FP | 0 | owner |
| multi_turn_long_context_19 | files | FN | 1 | agreed |
| multi_turn_long_context_192 | travel | FP | 1 | agreed |
| multi_turn_long_context_193 | travel | FP | 1 | agreed |
| multi_turn_long_context_194 | travel | FN, IMP | 1 | owner |
| multi_turn_long_context_2 | files | FN | 3 | agreed |
| multi_turn_long_context_21 | files | FN | 1 | agreed |
| multi_turn_long_context_22 | files | FN | 2 | owner |
| multi_turn_long_context_25 | files | FN | 2 | agreed |
| multi_turn_long_context_26 | files | FN | 1 | agreed |
| multi_turn_long_context_27 | files | IMP | 1 | agreed |
| multi_turn_long_context_28 | files | FN | 2 | agreed |
| multi_turn_long_context_31 | files | FN | 0 | owner |
| multi_turn_long_context_32 | files | FN | 1 | agreed |
| multi_turn_long_context_34 | files | FN | 1 | agreed |
| multi_turn_long_context_35 | files | FN | 0 | agreed |
| multi_turn_long_context_36 | files | FN | 1 | owner |
| multi_turn_long_context_38 | files | FN | 0 | agreed |
| multi_turn_long_context_4 | files | FN | 2 | agreed |
| multi_turn_long_context_41 | files | FN | 0 | agreed |
| multi_turn_long_context_43 | files | FN | 3 | agreed |
| multi_turn_long_context_48 | files | FP | 0 | agreed |
| multi_turn_long_context_49 | files | FN | 1 | agreed |
| multi_turn_long_context_55 | vehicle | FP | 3 | agreed |
| multi_turn_long_context_58 | vehicle | FN | 1 | agreed |
| multi_turn_long_context_59 | files | FN | 1 | agreed |
| multi_turn_long_context_6 | files | FN | 3 | agreed |
| multi_turn_long_context_60 | vehicle | FP | 3 | agreed |
| multi_turn_long_context_65 | vehicle | FN | 0 | agreed |
| multi_turn_long_context_68 | vehicle | FN | 4 | agreed |
| multi_turn_long_context_69 | vehicle | FN | 0 | agreed |
| multi_turn_long_context_70 | vehicle | FN | 0 | agreed |
| multi_turn_long_context_74 | files | FN | 0 | agreed |
| multi_turn_long_context_75 | vehicle | FN | 3 | agreed |
| multi_turn_long_context_79 | vehicle | FN | 2 | agreed |
| multi_turn_long_context_8 | files | FN | 2 | agreed |
| multi_turn_long_context_84 | vehicle | FN | 0 | agreed |
| multi_turn_long_context_86 | vehicle | FN, FP | 0 | owner |
| multi_turn_long_context_87 | vehicle | FN | 2 | agreed |
| multi_turn_long_context_94 | vehicle | FN | 2 | agreed |

## Arguable (score-changing, severity arguable; descriptive only)

- multi_turn_base_110 (finance): FN, failing turn 2, agreed
- multi_turn_base_117 (finance): FN, failing turn 1, owner
- multi_turn_base_118 (finance): FN, failing turn 3, owner
- multi_turn_base_127 (finance): FN, failing turn 3, owner
- multi_turn_base_131 (finance): IMP, failing turn 3, agreed
- multi_turn_base_153 (travel): FP, failing turn 1, owner
- multi_turn_base_156 (travel): FN, failing turn 0, owner
- multi_turn_base_157 (files): FP, failing turn 2, owner
- multi_turn_base_158 (travel): FN, failing turn 1, agreed
- multi_turn_base_164 (travel): FN, failing turn 2, owner
- multi_turn_base_172 (travel): FN, failing turn 2, agreed
- multi_turn_base_186 (travel): FN, failing turn 5, owner
- multi_turn_base_190 (travel): IMP, failing turn 2, owner
- multi_turn_base_41 (files): FN, IMP, failing turn 1, owner
- multi_turn_base_56 (vehicle): FN, failing turn 2, owner
- multi_turn_base_64 (vehicle): FN, failing turn 1, owner
- multi_turn_base_66 (vehicle): FN, failing turn 2, owner
- multi_turn_base_80 (files): FN, failing turn 3, agreed
- multi_turn_base_82 (vehicle): IMP, failing turn 0, owner
- multi_turn_base_85 (vehicle): FN, failing turn 1, owner
- multi_turn_base_88 (vehicle): FN, failing turn 2, agreed
- multi_turn_base_90 (vehicle): FN, failing turn 0, owner
- multi_turn_base_92 (vehicle): FN, failing turn 4, owner
- multi_turn_base_93 (vehicle): FN, failing turn 1, agreed
- multi_turn_base_96 (vehicle): FN, failing turn 0, agreed
- multi_turn_base_97 (vehicle): FN, failing turn 3, agreed
- multi_turn_base_99 (vehicle): FN, failing turn 1, agreed
- multi_turn_long_context_110 (finance): FN, failing turn 2, agreed
- multi_turn_long_context_117 (finance): FN, failing turn 1, owner
- multi_turn_long_context_118 (finance): FN, failing turn 3, owner
- multi_turn_long_context_127 (finance): FN, failing turn 3, owner
- multi_turn_long_context_131 (finance): IMP, failing turn 3, agreed
- multi_turn_long_context_156 (travel): FN, failing turn 4, agreed
- multi_turn_long_context_157 (files): FP, failing turn 2, owner
- multi_turn_long_context_158 (travel): FN, failing turn 1, agreed
- multi_turn_long_context_160 (travel): FN, IMP, failing turn 1, owner
- multi_turn_long_context_164 (travel): FN, failing turn 2, owner
- multi_turn_long_context_190 (travel): IMP, failing turn 2, owner
- multi_turn_long_context_30 (files): FN, failing turn 1, owner
- multi_turn_long_context_56 (vehicle): FN, failing turn 2, owner
- multi_turn_long_context_64 (vehicle): FN, failing turn 1, owner
- multi_turn_long_context_66 (vehicle): FN, failing turn 2, owner
- multi_turn_long_context_80 (files): FN, failing turn 3, agreed
- multi_turn_long_context_82 (vehicle): IMP, failing turn 0, owner
- multi_turn_long_context_85 (vehicle): FN, failing turn 1, owner
- multi_turn_long_context_88 (vehicle): FN, failing turn 2, agreed
- multi_turn_long_context_90 (vehicle): FN, failing turn 0, owner
- multi_turn_long_context_92 (vehicle): FN, failing turn 4, owner
- multi_turn_long_context_93 (vehicle): FN, failing turn 1, agreed
- multi_turn_long_context_96 (vehicle): FN, failing turn 0, agreed
- multi_turn_long_context_97 (vehicle): FN, failing turn 3, agreed
- multi_turn_long_context_99 (vehicle): FN, failing turn 1, agreed
