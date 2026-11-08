"""Artefacts for "Agent Self-Improvement with Frozen Weights: The Added Value and Limits of Failure Traces": the analysis code behind
the paper's registered numbers.

Modules are copies of the project's analysis modules with their imports trimmed so that they
run standalone (numpy only). See README.md, section "Code provenance", for the source of each
file and what changed.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
