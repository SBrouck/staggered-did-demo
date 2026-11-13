"""Single simulated run and Monte Carlo study.

    python -m staggered_did.run single   # results/single_run.json, results/event_study.csv
    python -m staggered_did.run mc       # results/montecarlo*.csv
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from .estimators import cs_event_study, post_average, twfe_event_study, twfe_static
from .simulate import simulate, true_effect

CFG = yaml.safe_load(Path("config/experiment.yaml").read_text())
WIN, POST = tuple(CFG["event_window"]), tuple(CFG["post_window"])
OUT = Path("results")


def truths(df: pd.DataFrame) -> dict:
    post_e = np.arange(POST[0], POST[1] + 1)
    return {
        # estimand of the CS post average: equal-weight mean of tau(e) over the window
        "att_post_window": float(true_effect(post_e, CFG).mean()),
        # mean effect over all treated unit-months (what a static TWFE is often read as)
        "att_treated_cells": float(df.loc[df["treated"] == 1, "tau"].mean()),
    }


def single() -> None:
    rng = np.random.default_rng(CFG["seed"])
    df = simulate(CFG, rng)
    OUT.mkdir(exist_ok=True)
    df.to_csv(OUT / "panel.csv", index=False)  # input of checks/did_crosscheck.R

    cs = cs_event_study(df, WIN, n_boot=CFG["n_boot"], rng=np.random.default_rng(CFG["seed"] + 1))
    tw = twfe_event_study(df, WIN)
    es = cs.rename(columns={"estimate": "cs", "se": "cs_se"}).merge(
        tw.rename(columns={"estimate": "twfe", "se": "twfe_se"}), on="e", how="outer")
    es["true"] = true_effect(es["e"].to_numpy(), CFG)
    es.sort_values("e").to_csv(OUT / "event_study.csv", index=False, float_format="%.6f")

    b, se = twfe_static(df)
    cs_post, cs_post_se = post_average(cs, POST)
    tw_post, _ = post_average(tw, POST)
    # Same estimators applied to the expected outcome p: no sampling noise, so the
    # gap to the truth is the estimator's bias for this draw of units.
    b_p, _ = twfe_static(df, y="p")
    cs_p, _ = post_average(cs_event_study(df, WIN, y="p"), POST)
    tw_p, _ = post_average(twfe_event_study(df, WIN, y="p"), POST)

    summary = {
        "n_units": int(df["id"].nunique()), "n_periods": int(df["t"].nunique()),
        "n_obs": len(df), "baseline_rate": float(df.loc[df["treated"] == 0, "y"].mean()),
        "truth": truths(df),
        "estimates": {
            "twfe_static": {"estimate": b, "se": se},
            "twfe_event_study_post": {"estimate": tw_post},
            "cs_post": {"estimate": cs_post, "se": cs_post_se},
        },
        "noise_free": {"twfe_static": b_p, "twfe_event_study_post": tw_p, "cs_post": cs_p},
    }
    (OUT / "single_run.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


def mc() -> None:
    rng = np.random.default_rng(CFG["seed"] + 2)
    rows, es_rows = [], []
    for r in range(CFG["n_mc"]):
        df = simulate(CFG, rng)
        tr = truths(df)
        b, se = twfe_static(df)
        cs = cs_event_study(df, WIN, n_boot=199, rng=rng)
        tw = twfe_event_study(df, WIN)
        cs_post, cs_se = post_average(cs, POST)
        tw_post, _ = post_average(tw, POST)
        noise_free = {  # same estimators on the expected outcome p (no Bernoulli noise)
            "twfe_static_p": twfe_static(df, y="p")[0],
            "twfe_event_study_post_p": post_average(twfe_event_study(df, WIN, y="p"), POST)[0],
            "cs_post_p": post_average(cs_event_study(df, WIN, y="p"), POST)[0],
        }
        rows.append({"rep": r, **tr, "twfe_static": b, "twfe_static_se": se,
                     "twfe_event_study_post": tw_post, "cs_post": cs_post, "cs_post_se": cs_se,
                     **noise_free})
        es_rows += [{"rep": r, "estimator": "cs", "e": e, "estimate": v}
                    for e, v in zip(cs["e"], cs["estimate"])]
        es_rows += [{"rep": r, "estimator": "twfe", "e": e, "estimate": v}
                    for e, v in zip(tw["e"], tw["estimate"])]
    res = pd.DataFrame(rows)
    OUT.mkdir(exist_ok=True)
    res.to_csv(OUT / "montecarlo.csv", index=False, float_format="%.6f")
    (pd.DataFrame(es_rows).groupby(["estimator", "e"])["estimate"]
     .agg(["mean", "std", "count"]).reset_index()
     .to_csv(OUT / "montecarlo_event_study.csv", index=False, float_format="%.6f"))
    summarise_mc(res).to_csv(OUT / "montecarlo_summary.csv", float_format="%.6f")
    print(summarise_mc(res).to_string(float_format=lambda v: f"{v:.5f}"))


def summarise_mc(res: pd.DataFrame) -> pd.DataFrame:
    """Bias, its Monte Carlo SE, sd and RMSE against the post-window ATT; 95% coverage
    where an SE exists; bias of the same estimator on the noise-free outcome p."""
    target = res["att_post_window"]
    out = {}
    for col in ["twfe_static", "twfe_event_study_post", "cs_post"]:
        err = res[col] - target
        err_p = res[f"{col}_p"] - target
        row = {"mean": res[col].mean(), "bias": err.mean(),
               "bias_mcse": err.std() / np.sqrt(len(res)), "sd": res[col].std(),
               "rmse": np.sqrt((err ** 2).mean()),
               "bias_noise_free": err_p.mean(),
               "bias_noise_free_mcse": err_p.std() / np.sqrt(len(res))}
        if f"{col}_se" in res:
            row["coverage95"] = (err.abs() <= 1.96 * res[f"{col}_se"]).mean()
        out[col] = row
    return pd.DataFrame(out).T


if __name__ == "__main__":
    {"single": single, "mc": mc}[sys.argv[1]]()
