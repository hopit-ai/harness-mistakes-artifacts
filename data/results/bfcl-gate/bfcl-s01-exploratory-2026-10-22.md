# EXPLORATORY — post hoc, owner-approved 2026-10-22, does not change any registered result

**Question.** Is S01 ("WHEN the user requests a file operation but the current directory is
unknown or ambiguous THEN call pwd ...", the only lesson the BFCL F′ gate advanced, +4.9
points official success on hand-off 2) a scorer artefact rather than better behaviour?

**Verdict: not supported.** The pwd calls S01 adds never change an official verdict.
Removing every pwd call from every trajectory changes 0 of 2,820 verdicts. Adding a
working-directory check changes 9 verdicts, none of which S01 explains, and S01's estimate
stays at +4.9. S01's gain is fewer state mismatches, not filled empty turns. Most of the
gain also appears in task families that have no file system, where no pwd call is
possible. On this evidence, part of the gain is a real behaviour fix: on root 42 S01
avoids creating a wrong nested folder. The rest is not tied to pwd and could be noise or
a non-specific effect of the note (see §4). This analysis cannot tell those two apart.

This is a post-hoc analysis, labelled exploratory. It reads the registered H2 package,
scored run and export, and writes only to `slh-bfcl-h2-work/xp-s01/`. The registered F′
report (`fprime/FPRIME-S.json`, `FPRIME-U.json`), the audited sensitivity and the gate
decision are unchanged.

## 1. Sources

- **arXiv:2610.04429, "Asking Earns Nothing" (Liu & Han, 2026-10-03)**, with its release
  `YangzeLiu/asking-earns-nothing` at commit `7f20cf1`. We read it through the GitHub API
  and installed nothing. `pairs.json` (sha256 `5dac6ba8…`) and `mutator_map.json`
  (`b18810ce…`) match the release `MANIFEST.sha256`. The paper's turn-level measure scores
  one decision per twin pair: on the anchor turn, did the model attempt a world-changing
  call? It credits `act` when the base twin is complete and `hold` when the
  miss_func/miss_param twin lacks the information. Its scorer needs the base, miss_func
  and miss_param result files. **Hand-off 2 ran only base and long_context, so only the
  `act` half applies.** We re-implemented that half: native function-calling records,
  names checked against the item's tool list, `mutate` labels, login excluded, and
  `echo` counted only when it writes a file. We then checked it against the release's own
  `turn_calls` + `Mutators`, run with `python -I` on all 2,820 anchor-turn readings:
  **0 disagreements**.
- **gorilla #1377** (Tokenless "EnvCheck" findings, open, no maintainer reply). Two
  findings matter here:
  - **"Multi-turn state comparison ignores the working directory."**
    `_compare_instances` skips attributes whose names start with `_`, and
    `GorillaFileSystem` keeps the working directory in `_current_dir`. We reproduced it:
    the issue's `ends-in-document` input for `multi_turn_base_0` passes the official
    check and fails our working-directory-aware check.
  - **"Empty-ground-truth turns bypass validation."** This one does not touch S01: base
    and long_context have no empty ground-truth turns.
- The checker logic that matters for S01 (bfcl-eval as installed in `bfcl-venv`):
  - A turn with a non-empty ground truth and no model call fails
    (`empty_turn_model_response`).
  - The state check compares public attributes only.
  - The response check requires each ground-truth execution result to appear somewhere
    in the model's results so far.

  `pwd` is read-only. It can change neither the public state nor `_current_dir`. It can
  therefore change a verdict only by making an otherwise empty turn non-empty, or by
  supplying a ground-truth `pwd` result. Those are the two channels tested below.

## 2. Methods (script: `slh/xp/ourside/bfcl_s01_explore.py`)

1. **Re-score** (`rescore`, run with the benchmark environment's Python, CPU only, about
   10 s). Every H2 episode's stored `result` goes back through the official
   `_evaluate_single_multi_turn_entry`, as `runner.score_cell` does, with a fresh
   backend name for each variant:
   - `official`: unchanged. It reproduces the stored verdicts, **0 / 2,820 mismatches**.
   - `cwd`: the state check also compares the working-directory path.
   - `nopwd`: every `pwd` call removed, official checker.
2. **Turn-level `act`** (above). We scored it on the 25 of 30 gate roots that have scored
   twin pairs:
   - `act_base`: the base instances only, as in the paper.
   - `act_all`: also the long-context sibling at the same turn. This is our extension.

   For each episode, `act` = acted on every distinct anchor turn.
3. **Effects** use the registered F′ estimator with only the outcome swapped:
   `fgate.analysis.fit_outcome`, RD prior 5 points, EB grid, 1,000 draws, seed 0, families
   weighted equally. With the outcome left as is, it reproduces the registered S01 value
   exactly (+0.0493, 90% [0.0190, 0.0795]).
4. **S01 minimal pairs** compare episodes of the same instance whose inclusion vectors
   differ only in S01 (`1abc` vs `0abc`; `1000` pairs with the shared anchor). That gives
   7 pairs × 60 instances = 420 pairs. Intervals are cluster bootstraps over roots
   (10,000 resamples, seed 20261018). Every episode is a single draw at T = 0.7, so flips
   include sampling noise. The pass→fail count is the noise reference.

## 3. Numbers

### 3a. Failure classes with vs without S01

S01's risk difference on each class indicator (F′ estimator, S pool, 900 episodes, 90%
interval):

| Class | S01 RD | Minimal pairs (on − off), root bootstrap 90% |
|---|---|---|
| success | **+4.9** [+1.9, +8.0] | **+7.4** [+2.6, +12.9] |
| empty turn (mandatory call missing) | −1.4 [−3.8, +1.1] | −0.5 [−3.1, +1.9] |
| state mismatch | **−4.9** [−8.0, −1.8] | **−6.4** [−11.7, −1.7] |
| execution-response mismatch | −0.0 [−3.3, +3.2] | 0.0 [−1.9, +1.9] |
| other (force-terminated) | −0.3 [−1.2, +0.5] | −0.5 [−1.0, 0.0] |

The 63 fail→pass flips started as 44 state mismatches, 9 empty turns, 8 response
mismatches and 2 force-terminations. There were also 32 pass→fail flips. **The gain is
fewer wrong writes, not filled empty turns.**

### 3b. Where S01 actually calls pwd

| | S01 on (420) | matched S01 off (420) | U pool (1,920) |
|---|---|---|---|
| episodes with any pwd | 10.5% | 6.4% | 6.3% |
| pwd calls per episode | 0.15 | 0.10 | 0.10 |
| turns whose only calls are pwd | **0** | 0 | 0 |
| pwd on a turn whose ground truth has pwd | **0** | 0 | 0 |

- pwd was never the only call on a turn. So it never turned an otherwise empty turn into
  a pass, and it never supplied a ground-truth pwd result.
- Only **13 of the 63** fail→pass flips contain any pwd call. All 13 are in the files
  family: root 42 (8), root 45 (2), root 0 (2) and root 7 (1).
- The other 50 are in episodes with no pwd at all.

Minimal-pair net effect by family:

| Family | Net effect | Root bootstrap 90% | pwd calls? |
|---|---|---|---|
| files | +11.1 | [−0.8, +25.4] | some |
| vehicle | +8.3 | [−1.2, +19.0] | none at all |
| travel | +8.9 | [+0.9, +17.0] | none at all |
| finance | 0.0 | — | none at all |

On the F′ estimator, S01 is +3.5 [+0.3, +6.5] in the three families with no file system
and +5.2 [0.0, +10.2] in files only. Leaving out one root at a time, S01 stays between +3.7
(without root 42) and +5.3.

Qualitative notes on flipped pairs (fail→pass):

- **Root 42** ("in my existing folder 'Lectures' create Notes2023.txt"; the agent already
  starts in Lectures). Without S01 the model cds or mkdirs "Lectures" and creates a nested
  folder, which is a state mismatch at turn 0. With S01 it calls pwd, sees it is already
  there and runs `touch` in place. This is a genuine behaviour fix that the tree check
  credits correctly.
- **Root 45 (long context).** The off episodes run `cd ResearchDocs` + `find('.')`. The
  on episodes run `find('ResearchDocs')`, which matches the reference's result string.
  The failing turn has no pwd; pwd appears only later, during a recovery. The off
  failures reflect how strict the response-subset check is about equivalent paths. That
  strictness is not specific to S01.
- **Root 7 and root 0.** These pairs differ in where the model cds before `mkdir`/`grep`.
  pwd sits on both sides or is incidental.
- **Travel and vehicle flips** (roots 52, 95, 150, 152, 167, 195, 199). These are ordinary
  T = 0.7 variation in state-changing calls: cancel vs only look up a booking, a missing
  currency conversion before `set_budget_limit`, engine-start sequencing, a runaway loop
  of calls, a missing `post_tweet`. Nothing involves directories.

### 3c. Re-scored effects (registered estimator structure, labelled exploratory)

**S pool**, RD with 90% interval:

| Outcome | S01 | S02 | S03 | S04 |
|---|---|---|---|---|
| official (registered) | +4.93 [1.90, 7.95] | −0.9 | +1.7 | −1.2 |
| `cwd` (working directory checked) | +4.91 [1.87, 7.95] | −0.7 | +1.7 | −1.4 |
| `nopwd` (pwd calls removed) | +4.93 [1.90, 7.95] (identical: no verdict changes) | | | |
| `act_base` (arXiv:2610.04429 act, base, 375 eps.) | +0.5 [−2.8, +3.5] | +0.5 | −0.4 | +0.3 |
| `act_all` (+ long-context extension, 750 eps.) | +1.0 [−1.5, +3.8] | −1.1 | +0.4 | −0.2 |

**U pool**:

- Official vs `cwd`: every U lesson moves by ≤0.4 points. U08 is −2.1 [−4.2, −0.1]
  official and −2.3 `cwd`.
- `nopwd`: identical to official.
- `act_base`:
  - U03 −3.8 [−7.0, −1.1] and U08 −3.7 [−6.9, −0.9]. Both are "inform the user"
    lessons, which slightly lower acting on complete turns.
  - The others lie within ±2.3 and their intervals cover 0.

`act` sits near its ceiling: 96% of base anchor turns attempt the world-changing call. On
these items the turn-level decision measure cannot separate the arms, and S01 neither
raises nor lowers it. The `hold` half, which is the paper's main signal, needs should-ask
twins that we have not run.

### 3d. Can the working-directory gap explain S01?

**No.**

- pwd cannot write `_current_dir`. The only way the gap could help S01 is if S01 made the
  model end turns in a wrong directory that the official check misses.
- Across all 2,820 episodes, **9** pass officially and fail the working-directory-aware
  check. All 9 are on root 0 (`multi_turn_base_0` / `_long_context_0`, the issue's own
  example task): 2 in the S pool (one with S01, `1001`, and one without, `0011`) and 7 in
  the U pool.
- The rate is 0.24% with S01 and 0.24% without (matched). S01's estimate moves by 0.02
  points.

## 4. Reading

- The artefact hypothesis predicted three things. None of them shows up:
  - gains through filled empty turns: empty-turn failures did not fall significantly, and
    no turn contained pwd alone;
  - gains through matching ground-truth pwd results: there were 0 such turns;
  - gains through unchecked working directories: 9 episodes in total, the same rate in
    both arms.
- What remains is a reduction in wrong writes:
  - one clear mechanism on root 42, where pwd prevents a nested-folder mistake;
  - a similar-sized effect in families where S01's instruction cannot fire.
- The second point weakens the lesson-specific reading of +4.9. Its interval is wide
  (minimal pairs: travel +8.9 [+0.9, +17.0], vehicle +8.3 [−1.2, +19.0]). It could be
  noise across 4 lessons, which the gate's multiplicity handling already prices in. It
  could also be a non-specific effect of having a short procedural note in the system
  message, although S02–S04 show no such effect. The held-out H3 run shows whether it holds:
  under the registered design (B-D9 not adopted) this is P2 = B1 − SEARCH in the Holm family,
  with SEARCH − B1 reported descriptively.

## 5. Applying the same analysis to H3 (on arrival)

The script detects the design from the package. For H3 (fixed arms × 4 trials, no
randomized inclusion) it:

- compares every arm with B1, root-weighted and paired by root, with a cluster bootstrap
  over roots (10,000, seed 20261018, as `slh.xp.bfcl.confirm`);
- reports that comparison for each outcome (`official`, `cwd`, `nopwd`, `act_base`,
  `act_all`);
- reports failure-class transitions and flip samples on trial-matched episode pairs;
- reports pwd statistics for each arm, and flags the arms whose notes contain S01
  (SEARCH, and UNGATED if it carries S01).

```bash
W=../slh-bfcl-h3-work; BPY=$W/bfcl-venv/bin/python
PYTHONPATH=. $BPY -m slh.xp.ourside.bfcl_s01_explore rescore --package $W/package-bfcl-h3 \
    --run $W/runs/bfcl-h3 --out $W/xp-s01/rescore-h3.jsonl
PYTHONPATH=. $BPY -m slh.xp.ourside.bfcl_s01_explore analyse --package $W/package-bfcl-h3 \
    --run $W/runs/bfcl-h3 --export $W/export-bfcl-h3 --rescore $W/xp-s01/rescore-h3.jsonl \
    --aen-pairs $W/xp-s01/aen-7f20cf1/pairs.json --aen-mutators $W/xp-s01/aen-7f20cf1/mutator_map.json \
    --out $W/xp-s01/report-h3.json
```

Rules for the H3 run:

- It runs only after the registered confirmation (`slh.xp.bfcl.confirm`) has been
  computed and recorded. Its output is reported beside the confirmation, never instead of
  it.
- A `rescore` `official_vs_stored_mismatch` other than 0 stops the analysis.

## 6. Reproduction (H2)

Inputs are in `slh-bfcl-h2-work`:

- `package-bfcl-h2/`
- `runs/bfcl-h2/`
- `export-bfcl-h2/`
- `xp-s01/aen-7f20cf1/{pairs.json,mutator_map.json}`

Outputs are `xp-s01/rescore-h2.jsonl` and `xp-s01/report-h2.json`. Use the commands in
§5 with `h2` in place of `h3`. Each step takes under 15 s on the CPU with
`OMP_NUM_THREADS=2`. Tests are in `tests/test_xp_bfcl_s01_explore.py`.
