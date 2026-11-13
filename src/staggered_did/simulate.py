"""Simulated staggered rollout with a binary monthly outcome.

Each unit i has a logit-scale intercept, a linear trend and a shared seasonality.
After adoption the event probability rises by `effect_pp * min(e + 1, ramp) / ramp`,
where e = t - G is event time. The effect is the same for every cohort, so the only
source of heterogeneity is its dynamics, which is enough to bias a static TWFE.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

NEVER = 0  # cohort code for never-treated units (convention of the R `did` package)


def true_effect(e: np.ndarray, cfg: dict) -> np.ndarray:
    """Effect on the event probability at event time e (0 before adoption)."""
    ramp = cfg["effect_ramp_months"]
    e = np.asarray(e)
    return np.where(e >= 0, cfg["effect_pp"] * np.minimum(e + 1, ramp) / ramp, 0.0)


def simulate(cfg: dict, rng: np.random.Generator) -> pd.DataFrame:
    """Return a balanced panel with columns id, t, G, treated, tau, p, y."""
    T = cfg["n_periods"]
    G = np.concatenate([
        np.full(c["size"], NEVER if c["adopt_month"] is None else c["adopt_month"])
        for c in cfg["cohorts"]
    ])
    rng.shuffle(G)
    n = G.size

    alpha = rng.normal(0.0, cfg["sigma_alpha"], n)
    slope = rng.normal(0.0, cfg["sigma_slope"], n)

    t = np.arange(1, T + 1)
    ids, tt = np.meshgrid(np.arange(n), t, indexing="ij")
    Gi = G[ids]
    treated = (Gi != NEVER) & (tt >= Gi)
    e = np.where(Gi != NEVER, tt - Gi, -10_000)

    season = cfg["season_amp"] * np.sin(2 * np.pi * tt / 12.0)
    lin = cfg["base_intercept"] + alpha[ids] + slope[ids] * (tt / T) + season
    tau = true_effect(e, cfg) * treated
    p = np.clip(1.0 / (1.0 + np.exp(-lin)) + tau, 1e-6, 1 - 1e-6)
    y = rng.binomial(1, p)

    return pd.DataFrame({
        "id": ids.ravel(), "t": tt.ravel(), "G": Gi.ravel(),
        "treated": treated.ravel().astype(int), "tau": tau.ravel(),
        "p": p.ravel(), "y": y.ravel(),
    })
