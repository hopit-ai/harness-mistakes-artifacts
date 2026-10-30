"""Figure J1 of the paper (identity guard, G1), from the shipped aggregate data only.

Inputs (read-only):
  data/results/g1/analysis.json   diagnostics.trap_per_root, diagnostics.per_set
  the G1 audit's discordant pairs by guard firing (Appendix J.3; copied below:
                                                Summary "paired contrast" bullets; §5 table)
Run from the repository root:  python figures/make_fig2.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
A = json.loads((ROOT / "data/results/g1/analysis.json").read_text())

# G1 audit (Appendix J.3), summary: success-discordant non-trap pairs.
#   never fired (176 pairs): 6 B1-only vs 1 guard-only; fired (198 pairs): 11 vs 8.
SUCCESS_DISC = {"Guard never\nfired (176)": (6, 1), "Guard fired\n(198)": (11, 8)}
# G1 audit (Appendix J.3) table: harm-discordant non-trap pairs (B1-only, guard-only).
#   never fired 1 vs 4; fired, precedence 7 vs 7; fired, simulator-driven write 0 vs 1.
HARM_DISC = {"Guard never\nfired": (1, 4), "Guard fired:\nitems-first": (7, 7),
             "Guard fired:\nsimulator": (0, 1)}

GREY, BLUE, INK, MUTED = "#8a8985", "#2a78d6", "#0b0b0b", "#52514e"
plt.rcParams.update({"font.size": 8.5, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
                     "ytick.color": MUTED, "svg.fonttype": "none"})
fig, axes = plt.subplots(1, 3, figsize=(12.5, 3.8), gridspec_kw={"width_ratios": [1.4, 1, 1.2]})
W = 0.36


def grouped(ax, labels, left, right, names, ylabel, title):
    x = range(len(labels))
    for off, vals, col, name in ((-W / 2, left, GREY, names[0]), (W / 2, right, BLUE, names[1])):
        ax.bar([i + off for i in x], vals, width=W, color=col, edgecolor="white", linewidth=1.5,
               zorder=2, label=name)
        top = max(max(left), max(right))
        for i, v in enumerate(vals):
            ax.text(i + off, v + top * 0.02, f"{v:g}", ha="center", va="bottom", fontsize=7.5,
                    color=INK)
    ax.set_xticks(list(x), labels, fontsize=7.5)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", color="#e4e3df", linewidth=0.6, zorder=0)
    ax.set_title(title, loc="left", fontsize=9.5, color=INK)
    ax.legend(loc="upper right", fontsize=7, frameon=False)


roots = ["AT1", "BT1", "BT2", "CT1", "CT2"]
tp = A["diagnostics"]["trap_per_root"]
pct = lambda r, arm: 100 * tp[r][arm]["success"] / tp[r][arm]["n"]
grouped(axes[0], [f"{r}\n(n={tp[r]['b1']['n']})" for r in roots], [pct(r, "b1") for r in roots],
        [pct(r, "b1_guard") for r in roots], ("B1", "B1 + guard"),
        "Trap success, % of conversations", "(a) Trap roots (by construction)")
axes[0].set_ylim(0, 125)
axes[0].legend(loc="upper center", ncol=2, fontsize=7, frameon=False)
for t in axes[0].texts:
    t.set_text(f"{float(t.get_text()):.0f}")

grouped(axes[1], list(SUCCESS_DISC), [v[0] for v in SUCCESS_DISC.values()],
        [v[1] for v in SUCCESS_DISC.values()], ("only B1 succeeded", "only guard succeeded"),
        "Non-trap discordant pairs", "(b) Success discordance")
axes[1].set_ylim(0, 14)

grouped(axes[2], list(HARM_DISC), [v[0] for v in HARM_DISC.values()],
        [v[1] for v in HARM_DISC.values()], ("only B1 harmful", "only guard harmful"),
        "Non-trap discordant pairs", "(c) Harm discordance")
axes[2].set_ylim(0, 9)

fig.tight_layout()
for ext in ("png", "svg"):
    fig.savefig(OUT / f"fig2.{ext}", dpi=200, bbox_inches="tight", facecolor="white")
print("wrote", OUT / "fig2.png", OUT / "fig2.svg")
