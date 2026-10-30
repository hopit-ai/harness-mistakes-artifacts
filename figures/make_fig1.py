"""Figure 1 of the paper, from the shipped aggregate data only.

Inputs (read-only):
  data/results/stage1/results.json        arms[].pooled / per_task, gate.primary
  data/results/official-tau2/score.json   variants.tau2.all.{b1,learned}.pass_hat_k
  per-trial pass^1 of the official run (the paper's Appendix C table; copied below)
Run from the repository root:  python figures/make_fig1.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
R = json.loads((ROOT / "data/results/stage1/results.json").read_text())
S = json.loads((ROOT / "data/results/official-tau2/score.json").read_text())
# Official run, per-trial pass^1 (paired seed), B1 and learned, trials t0..t3 (Appendix C)
TRIAL_PASS1 = {"B1": [82.5, 85.1, 80.7, 83.3], "Learned": [79.8, 82.5, 84.2, 79.8]}

arms = {(a["arm"], a["writer"]): a for a in R["arms"]}
order = [(("b0", None), "B0\nmodel only"), (("b1", None), "B1\nstandard\nharness"),
         (("search_control", "T+"), "T+ search\ncontrol\n(no episodes)"),
         (("learned", "T+"), "T+ learned\nlibrary"), (("human", None), "Person-\nwritten\n(reference)")]
GREY, ORANGE, BLUE, INK, MUTED = "#8a8985", "#eb6834", "#2a78d6", "#0b0b0b", "#52514e"
colors = [GREY, GREY, ORANGE, BLUE, "#c3c2b7"]
tasks = [("address", "o"), ("variant", "s"), ("sequence", "^")]

plt.rcParams.update({"font.size": 8.5, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
                     "ytick.color": MUTED, "svg.fonttype": "none"})
fig, axes = plt.subplots(1, 3, figsize=(12.5, 4.0), gridspec_kw={"width_ratios": [1.25, 1.25, 1]})


def bars(ax, metric, ylabel, ylim):
    x = list(range(len(order)))
    vals = [arms[k]["pooled"][metric] for k, _ in order]
    ax.bar(x, vals, width=0.62, color=colors, edgecolor="white", linewidth=1.5, zorder=2)
    for i, v in enumerate(vals):
        ax.text(i, v + (ylim[1] - ylim[0]) * 0.015, f"{v:.1f}", ha="center", va="bottom",
                color=INK, fontsize=8.5, fontweight="bold")
    for j, (t, m) in enumerate(tasks):
        ys = [arms[k]["per_task"][t][metric] for k, _ in order]
        ax.scatter([i + (j - 1) * 0.17 for i in x], ys, marker=m, s=18, facecolor="white",
                   edgecolor=INK, linewidth=0.8, zorder=3, label=f"{t} (per task)")
    ax.set_xticks(x, [l for _, l in order], fontsize=7.5)
    ax.set_ylabel(ylabel)
    ax.set_ylim(*ylim)
    ax.grid(axis="y", color="#e4e3df", linewidth=0.6, zorder=0)


ax = axes[0]
bars(ax, "correct", "Next-decision accuracy, % (2,997 sealed cases)", (55, 100))
g = R["gate"]["primary"]
lo, hi = g["interval"]
ax.annotate("", xy=(3, 82.6), xytext=(2, 78.6),
            arrowprops=dict(arrowstyle="->", color=INK, lw=0.9))
ax.text(3.0, 97.0, f"+{g['estimate']:.1f} [+{lo:.1f}, +{hi:.1f}]\nregistered primary",
        ha="center", fontsize=7.5, color=INK)
ax.text(1.5, 83.0, "+6.5 over B1\n(arithmetic\non arm means)", ha="center", fontsize=7, color=MUTED)
ax.set_title("(a) Stage 1: accuracy", loc="left", fontsize=9.5, color=INK)
ax.legend(loc="upper left", fontsize=7, frameon=False, bbox_to_anchor=(0.0, 1.0))

ax = axes[1]
bars(ax, "wrong_write", "Wrong writes, % of decisions", (0, 34))
w = R["gate"]["primary_wrong_write"]
ax.text(2.5, 17.0, f"{w['estimate']:.1f} [{w['interval'][0]:.1f}, {w['interval'][1]:.1f}]\n"
        "non-inferiority holds", ha="center", fontsize=7.5, color=INK)
ax.set_title("(b) Stage 1: wrong writes (lower is better)", loc="left", fontsize=9.5, color=INK)

ax = axes[2]
a = S["variants"]["tau2"]["all"]
ks = [1, 2, 3, 4]
for arm, lab, col in (("b1", "B1", GREY), ("learned", "Learned (T+ libraries)", BLUE)):
    ys = [100 * a[arm]["pass_hat_k"][str(k)] for k in ks]
    ax.plot(ks, ys, color=col, lw=2, marker="o", ms=5, label=lab, zorder=3)
    for k, y in zip(ks, ys):
        ax.text(k + (0.22 if k == 1 else 0.1), y + (1.0 if arm == "b1" else -2.6), f"{y:.1f}", fontsize=7.5, color=INK)
for lab, col, dx in (("B1", GREY, -0.12), ("Learned", BLUE, 0.12)):
    ax.scatter([1 + dx] * 4, TRIAL_PASS1[lab], s=14, color=col, alpha=0.75, zorder=4,
               edgecolor="white", linewidth=0.6)
ax.text(0.65, 88.6, "dots: per-trial pass^1", fontsize=7, color=MUTED, ha="left")
d4 = a["learned_minus_b1"][3]
ax.text(1.75, 51.8, f"learned − B1, pass^4: {100*d4['diff']:+.1f} [{100*d4['ci95'][0]:+.1f}, "
        f"{100*d4['ci95'][1]:+.1f}]", fontsize=7.5, color=INK)
d1 = a["learned_minus_b1"][0]
ax.text(1.35, 85.6, f"learned − B1, pass^1: {100*d1['diff']:+.1f} [{100*d1['ci95'][0]:+.1f}, "
        f"{100*d1['ci95'][1]:+.1f}]", fontsize=7.5, color=INK)
ax.set_xticks(ks, [f"pass^{k}" for k in ks])
ax.set_xlim(0.6, 4.6)
ax.set_ylim(50, 90)
ax.set_ylabel("Official τ² retail, % (114 tasks × 4 trials)")
ax.grid(axis="y", color="#e4e3df", linewidth=0.6, zorder=0)
ax.legend(loc="lower left", fontsize=7.5, frameon=False, bbox_to_anchor=(0.0, 0.08))
ax.set_title("(c) Stage 2: official τ² retail", loc="left", fontsize=9.5, color=INK)

fig.tight_layout()
for ext in ("png", "svg"):
    fig.savefig(OUT / f"fig1.{ext}", dpi=200, bbox_inches="tight", facecolor="white")
print("wrote", OUT / "fig1.png", OUT / "fig1.svg")
