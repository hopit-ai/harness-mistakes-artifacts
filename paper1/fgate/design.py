"""The parts of the F' design module that the analysis needs (trimmed copy).

The full design module builds hand-off packages from the private task pool; it is not
needed to analyse a scored table. Kept here, unchanged in value: the registered sizes and
thresholds of the synthetic-difficulty check (``analysis.difficulty_check`` defaults) and
the inclusion-vector generator (``inclusion_vectors``, ``bits``) used by the BFCL F' design.
"""

from __future__ import annotations

import hashlib
import random
from typing import Any

TASK_ORDER = ("address", "variant", "sequence")
DRAWS = 16         # randomized vectors per fit prefix (8 antithetic pairs) + 1 anchor

# Synthetic-difficulty check (plan section 3.6, revised 2026-10-19 after the power
# simulation): the primary question is a difficulty SHIFT, two-sided, powered for a large
# one (|synthetic - original| >= 10 points success); ``no large shift`` = 90% CI inside
# +-10 points. +-5-point equivalence is reported only when the 90% CI happens to lie
# inside +-5 (it is not powered at 180 pairs).
DIFFICULTY_ROLE = "difficulty"
DIFFICULTY_SIZES = {"address": 40, "variant": 70, "sequence": 70}
DIFFICULTY_PHRASINGS = 3
DIFFICULTY_LARGE_SHIFT = 0.10
DIFFICULTY_EQUIVALENCE = 0.05
DIFFICULTY_ARMS = ("original", "synthetic")


def _rng(*parts: Any) -> random.Random:
    text = "|".join(map(str, parts))
    return random.Random(int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16))


def inclusion_vectors(case_id: str, n_lessons: int, draws: int, *, salt: str = "fgate-incl-v1"
                      ) -> list[tuple[int, ...]]:
    """Anchor (all zero) first, then ``draws`` vectors in antithetic pairs."""
    if draws % 2:
        raise ValueError("draws must be even (antithetic pairs)")
    if n_lessons < 2:
        raise ValueError("the pool needs at least two lessons")
    r = _rng(salt, case_id)
    zero = tuple([0] * n_lessons)
    ones = tuple([1] * n_lessons)
    seen = {zero}
    out = [zero]
    attempts = 0
    while len(out) < draws + 1:
        attempts += 1
        if attempts > 10_000:
            raise RuntimeError("could not draw distinct inclusion vectors")
        v = tuple(int(r.random() < 0.5) for _ in range(n_lessons))
        w = tuple(1 - x for x in v)
        if v in (zero, ones) or v in seen or w in seen:
            continue
        seen.update((v, w))
        out.extend((v, w))
    return out


def bits(x: tuple[int, ...] | list[int]) -> str:
    return "".join(str(int(b)) for b in x)
