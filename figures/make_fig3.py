"""Figure 2 of the paper (B1 feasibility on BFCL multi-turn and ALFWorld).

Inputs: the hand-off 1a baseline counts reported in Section 7.1 (copied below).
Feasibility bands: BFCL 20-80% (the pre-specified H2 rule), ALFWorld
25-80% (the pre-specified ALFWorld GO rule).
Run from the repository root:  python figures/make_fig3.py
"""
from math import sqrt
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent
# BFCL B1, row "All": Base 60/98, Long Context 51/100, All 111/198
BFCL = [("Base", 60, 98), ("Long\nContext", 51, 100), ("All", 111, 198)]
# ALFWorld B1 by type, 8 games each; total 10/48
ALF = [("pick &\nplace", 7, 8), ("look at\nin light", 0, 8), ("clean", 1, 8), ("heat", 1, 8),
       ("cool", 0, 8), ("pick\ntwo", 1, 8), ("All", 10, 48)]

GREY, BLUE, INK, MUTED, BAND = "#8a8985", "#2a78d6", "#0b0b0b", "#52514e", "#e8f0fb"
plt.rcParams.update({"font.size": 8.5, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
                     "ytick.color": MUTED, "svg.fonttype": "none"})


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return 100 * (c - h), 100 * (c + h)


def panel(ax, rows, band, title, verdict):
    ax.axhspan(*band, color=BAND, zorder=0)
    ax.text(len(rows) - 0.5, band[1] - 1, f"feasibility band {band[0]}–{band[1]}%", ha="right",
            va="top", fontsize=7, color=MUTED)
    for i, (lab, k, n) in enumerate(rows):
        lo, hi = wilson(k, n)
        p = 100 * k / n
        col = BLUE if lab == "All" else GREY
        ax.plot([i, i], [lo, hi], color=col, lw=2, zorder=2)
        ax.scatter([i], [p], s=40, color=col, edgecolor="white", linewidth=1.2, zorder=3)
        ax.text(i + 0.12, p, f"{k}/{n}", fontsize=7.5, color=INK, va="center")
    ax.set_xticks(range(len(rows)), [r[0] for r in rows], fontsize=7.5)
    ax.set_ylim(0, 105)
    ax.set_xlim(-0.5, len(rows) - 0.3)
    ax.set_ylabel("B1 success, % (Wilson 95%)")
    ax.grid(axis="y", color="#e4e3df", linewidth=0.6, zorder=0)
    ax.set_title(f"{title}: {verdict}", loc="left", fontsize=9.5, color=INK)


fig, axes = plt.subplots(1, 2, figsize=(10.5, 3.6), gridspec_kw={"width_ratios": [1, 2]})
panel(axes[0], BFCL, (20, 80), "(a) BFCL multi-turn, 198 episodes", "GO")
panel(axes[1], ALF, (25, 80), "(b) ALFWorld, 48 valid_train games", "NO-GO (20.8% < 25%)")
fig.tight_layout()
for ext in ("png", "svg"):
    fig.savefig(OUT / f"fig3.{ext}", dpi=200, bbox_inches="tight", facecolor="white")
print("wrote", OUT / "fig3.png", OUT / "fig3.svg")
