"""Figure 1 from results/montecarlo*.csv.

    python -m staggered_did.figures   # fig/fig1_did.svg
"""
from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

from .simulate import true_effect

mpl.rcParams.update({
    "font.family": "STIXGeneral", "mathtext.fontset": "stix", "font.size": 9,
    "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6, "svg.fonttype": "none", "svg.hashsalt": "fig1",
})
CFG = yaml.safe_load(Path("config/experiment.yaml").read_text())
INK, BLUE, RED, GREY = "#222222", "#2b5d8a", "#b0413e", "#9a9a9a"
PP = 100  # display in percentage points


def main() -> None:
    mc = pd.read_csv("results/montecarlo.csv")
    es = pd.read_csv("results/montecarlo_event_study.csv")
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 2.8), gridspec_kw={"width_ratios": [1.5, 1]})

    # (a) event-time estimates: Monte Carlo mean +/- 1.96 MC standard errors
    e_grid = np.arange(CFG["event_window"][0], CFG["event_window"][1] + 1)
    a.plot(e_grid, true_effect(e_grid, CFG) * PP, color=INK, lw=1.0, label="True effect")
    for name, color, dx, label in [("cs", BLUE, -0.15, "Callaway–Sant'Anna"),
                                   ("twfe", RED, 0.15, "TWFE event study")]:
        g = es[es["estimator"] == name].set_index("e")
        m, h = g["mean"] * PP, 1.96 * g["std"] / np.sqrt(g["count"]) * PP
        a.vlines(m.index + dx, m - h, m + h, color=color, lw=0.8)
        a.plot(m.index + dx, m, "o", ms=3, color=color, label=label)
    post = np.arange(CFG["post_window"][0], CFG["post_window"][1] + 1)
    a.hlines(mc["twfe_static"].mean() * PP, post[0] - 0.3, post[-1] + 0.3, color=RED, lw=0.9,
             ls="--", label="Static TWFE")
    a.hlines(mc["att_post_window"].mean() * PP, post[0] - 0.3, post[-1] + 0.3, color=INK,
             lw=0.9, ls=":", label="True post-window ATT")
    a.axhline(0, color=GREY, lw=0.5)
    a.axvline(-0.5, color=GREY, lw=0.5, ls=":")
    a.set_xlabel("Months since adoption")
    a.set_ylabel("Effect on monthly event rate (pp)")
    a.set_title("(a) Event-time estimates", loc="left", fontsize=9)
    a.legend(frameon=False, fontsize=7, loc="upper left")

    # (b) estimator bias without outcome noise: estimators applied to the expected
    # outcome p, one point per replication (variation comes from the draw of units)
    cols = [("twfe_static", "Static\nTWFE"), ("twfe_event_study_post", "TWFE event\nstudy"),
            ("cs_post", "Callaway–\nSant'Anna")]
    data = [(mc[f"{c}_p"] - mc["att_post_window"]) * PP for c, _ in cols]
    b.boxplot(data, widths=0.5, showfliers=False, medianprops={"color": INK, "lw": 0.8},
              boxprops={"lw": 0.6}, whiskerprops={"lw": 0.6}, capprops={"lw": 0.6})
    b.axhline(0, color=GREY, lw=0.5)
    b.set_xticks(range(1, 4), [l for _, l in cols])
    b.set_ylabel("Error vs. post-window ATT (pp)")
    b.set_title("(b) Error on the noise-free outcome", loc="left", fontsize=9)

    fig.tight_layout()
    Path("fig").mkdir(exist_ok=True)
    fig.savefig("fig/fig1_did.svg", metadata={"Date": None})
    fig.savefig("fig/fig1_did.png", dpi=200, metadata={"Software": None})


if __name__ == "__main__":
    main()
