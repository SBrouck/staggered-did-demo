import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import yaml

from staggered_did.estimators import cs_event_study, twfe_event_study, twfe_static
from staggered_did.simulate import simulate, true_effect

CFG = yaml.safe_load(open("config/experiment.yaml"))


def _panel(seed=0):
    return simulate(CFG, np.random.default_rng(seed))


def test_twfe_static_matches_statsmodels():
    df = _panel()
    b, se = twfe_static(df)
    ref = smf.ols("y ~ treated + C(id) + C(t)", data=df).fit(
        cov_type="cluster", cov_kwds={"groups": df["id"]})
    assert np.isclose(b, ref.params["treated"])
    assert np.isclose(se, ref.bse["treated"])


def test_twfe_event_study_matches_statsmodels():
    df = _panel(1)
    lo, hi = CFG["event_window"]
    es = twfe_event_study(df, (lo, hi))
    d = df.copy()
    e = np.clip(d["t"] - d["G"], lo, hi)
    names = []
    for k in es["e"]:
        name = f"d_{k + 100}"
        d[name] = ((e == k) & (d["G"] != 0)).astype(float)
        names.append(name)
    ref = smf.ols(f"y ~ {' + '.join(names)} + C(id) + C(t)", data=d).fit(
        cov_type="cluster", cov_kwds={"groups": d["id"]})
    assert np.allclose(es["estimate"], ref.params[names].to_numpy())
    assert np.allclose(es["se"], ref.bse[names].to_numpy())


def test_cs_recovers_dynamic_effect_under_exact_parallel_trends():
    # Outcome = unit effect + common time path + true effect: CS must be exact,
    # while a static TWFE is not when effects grow with event time.
    df = _panel(2)
    rng = np.random.default_rng(3)
    unit = rng.normal(size=df["id"].nunique())
    time = rng.normal(size=df["t"].max() + 1)
    df["y_exact"] = unit[df["id"]] + time[df["t"]] + df["tau"]
    window = tuple(CFG["event_window"])
    es = cs_event_study(df, window, y="y_exact")
    assert np.allclose(es["estimate"], true_effect(es["e"].to_numpy(), CFG), atol=1e-12)
    tw = twfe_event_study(df, window, y="y_exact")
    assert np.allclose(tw.loc[tw["e"].between(-5, 7), "estimate"],
                       true_effect(tw.loc[tw["e"].between(-5, 7), "e"].to_numpy(), CFG), atol=1e-10)
    b, _ = twfe_static(df, y="y_exact")
    assert b < df.loc[df["treated"] == 1, "tau"].mean() - 1e-4
