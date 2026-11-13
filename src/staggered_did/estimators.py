"""Estimators for a balanced panel with staggered adoption.

- `twfe_static`: y ~ treated + unit FE + time FE (the conventional benchmark).
- `twfe_event_study`: y ~ sum_k 1{e = k} + unit FE + time FE, k != -1, endpoints binned.
- `cs_event_study`: Callaway and Sant'Anna (2021) group-time ATTs with never-treated
  controls, no covariates and a varying base period, aggregated by event time with
  cohort-size weights. Without covariates ATT(g, t) is a difference of mean changes.

TWFE fits use the within transformation, which is exact for a balanced panel, and
CR1 standard errors clustered by unit (same finite-sample factor as statsmodels).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .simulate import NEVER


def _to_matrix(df: pd.DataFrame, col: str) -> np.ndarray:
    """Pivot a balanced panel to an (n_units, n_periods) array ordered by id and t."""
    return df.pivot(index="id", columns="t", values=col).to_numpy(dtype=float)


def _within(x: np.ndarray) -> np.ndarray:
    """Two-way demeaning of an (n, T) array: exact FE residualisation when balanced."""
    return x - x.mean(1, keepdims=True) - x.mean(0, keepdims=True) + x.mean()


def _ols_cluster(Y: np.ndarray, Xs: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    """OLS of demeaned Y on demeaned regressors, CR1 SEs clustered by unit (row)."""
    n, T = Y.shape
    # numpy 2.x with Apple Accelerate emits spurious matmul warnings on finite input;
    # results are checked against statsmodels in tests/.
    with np.errstate(all="ignore"):
        return _ols_cluster_impl(Y, Xs, n, T)


def _ols_cluster_impl(Y, Xs, n, T):
    y = _within(Y).ravel()
    X = np.column_stack([_within(x).ravel() for x in Xs])
    XtX_inv = np.linalg.inv(X.T @ X)
    beta = XtX_inv @ X.T @ y
    u = (y - X @ beta).reshape(n, T)
    scores = np.einsum("itk,it->ik", X.reshape(n, T, -1), u)
    meat = scores.T @ scores
    k = X.shape[1] + n + T - 1  # slopes + unit FE + time FE (with intercept)
    c = n / (n - 1) * (n * T - 1) / (n * T - k)
    V = c * XtX_inv @ meat @ XtX_inv
    return beta, np.sqrt(np.diag(V))


def twfe_static(df: pd.DataFrame, y: str = "y") -> tuple[float, float]:
    beta, se = _ols_cluster(_to_matrix(df, y), [_to_matrix(df, "treated")])
    return float(beta[0]), float(se[0])


def twfe_event_study(df: pd.DataFrame, window: tuple[int, int], y: str = "y") -> pd.DataFrame:
    lo, hi = window
    G = _to_matrix(df, "G")
    t = _to_matrix(df, "t")
    e = np.clip(t - G, lo, hi)
    ever = G != NEVER
    ks = [k for k in range(lo, hi + 1) if k != -1]
    Xs = [((e == k) & ever).astype(float) for k in ks]
    beta, se = _ols_cluster(_to_matrix(df, y), Xs)
    return pd.DataFrame({"e": ks, "estimate": beta, "se": se})


def _cs_components(df: pd.DataFrame, window: tuple[int, int], y: str):
    """Per-unit outcome changes behind each ATT(g, g + e) in the event window."""
    Y = _to_matrix(df, y)
    G = df.groupby("id")["G"].first().to_numpy()
    T = Y.shape[1]
    cohorts = sorted(g for g in np.unique(G) if g != NEVER)
    ctrl = G == NEVER
    out = []  # (e, g, cohort mask, change vector over all units)
    for e in range(window[0], window[1] + 1):
        for g in cohorts:
            t = g + e
            base = g - 1 if e >= 0 else t - 1  # varying base period
            if t > T or base < 1:
                continue
            out.append((e, g, G == g, Y[:, t - 1] - Y[:, base - 1]))
    return out, ctrl, G


def cs_event_study(df: pd.DataFrame, window: tuple[int, int], y: str = "y",
                   n_boot: int = 0, rng: np.random.Generator | None = None) -> pd.DataFrame:
    """ATT(e) with cohort-size weights. With n_boot > 0, adds unit-bootstrap SEs
    (units resampled within cohort, so cohort sizes stay fixed)."""
    comps, ctrl, G = _cs_components(df, window, y)
    n = G.size

    def aggregate(w: np.ndarray) -> dict[int, float]:
        """w: (B, n) unit weights; returns ATT(e) for each replication."""
        num, den = {}, {}
        for e, g, mask, d in comps:
            size = mask.sum()
            att = (w[:, mask] @ d[mask]) / size - (w[:, ctrl] @ d[ctrl]) / ctrl.sum()
            num[e] = num.get(e, 0) + size * att
            den[e] = den.get(e, 0) + size
        return {e: num[e] / den[e] for e in num}

    with np.errstate(all="ignore"):
        point = aggregate(np.ones((1, n)))
    res = pd.DataFrame({"e": list(point), "estimate": [v[0] for v in point.values()]})
    if n_boot:
        rng = rng or np.random.default_rng()
        W = np.zeros((n_boot, n))
        for g in np.unique(G):
            idx = np.flatnonzero(G == g)
            draws = rng.integers(0, idx.size, size=(n_boot, idx.size))
            for b in range(n_boot):
                W[b] += np.bincount(idx[draws[b]], minlength=n)
        with np.errstate(all="ignore"):
            boot = aggregate(W)
        res["se"] = [boot[e].std(ddof=1) for e in res["e"]]
        res.attrs["boot"] = boot  # e -> (n_boot,) draws, for aggregated SEs
    return res


def post_average(es: pd.DataFrame, post: tuple[int, int]) -> tuple[float, float]:
    """Average of ATT(e) over the post window (equal weight per event time), with its
    bootstrap SE when `es` carries bootstrap draws (NaN otherwise)."""
    es_post = es.loc[es["e"].between(*post), "e"]
    est = float(es.loc[es_post.index, "estimate"].mean())
    boot = es.attrs.get("boot")
    if boot is None:
        return est, float("nan")
    draws = np.mean([boot[e] for e in es_post], axis=0)
    return est, float(draws.std(ddof=1))
