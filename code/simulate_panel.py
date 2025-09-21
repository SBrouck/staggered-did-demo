import numpy as np
import pandas as pd
import yaml
from pathlib import Path

def logistic(x):
    return 1.0 / (1.0 + np.exp(-x))

def main():
    cfg = yaml.safe_load(Path("config/experiment.yaml").read_text())
    rng = np.random.default_rng(cfg["seed"])

    n = cfg["n_units"]
    T = cfg["n_periods"]

    # build cohort assignment
    adopt = np.empty(n, dtype=int)
    idx = np.arange(n)
    rng.shuffle(idx)
    start = 0
    for c in cfg["cohorts"]:
        size = c["size"]
        adopt_month = c["adopt_month"]
        adopt[idx[start:start+size]] = adopt_month
        start += size

    # unit heterogeneity
    alpha = rng.normal(0.0, cfg["sigma_alpha"], size=n)
    slope = rng.normal(0.0, cfg["sigma_slope"], size=n)

    rows = []
    for i in range(n):
        for t in range(1, T + 1):
            season = cfg["season_amp"] * np.sin(2 * np.pi * t / 12.0)
            linpred = cfg["base_intercept"] + alpha[i] + slope[i] * (t / T) + season

            treated = 1 if t >= adopt[i] else 0

            # ramp the effect for first effect_ramp_months after adoption
            post_months = max(0, t - adopt[i] + 1) if treated else 0
            ramp = min(post_months, cfg["effect_ramp_months"]) / max(1, cfg["effect_ramp_months"])
            effect = cfg["effect_pp"] * ramp

            p = logistic(linpred) + effect * treated
            p = np.clip(p, 1e-6, 1 - 1e-6)

            y = rng.binomial(1, p)

            rows.append({
                "id": i,
                "t": t,
                "y": y,
                "treated": treated,
                "G": adopt[i],
                "event_time": t - adopt[i] if treated else -999,  # to be used in R
            })

    df = pd.DataFrame(rows)
    Path("out").mkdir(parents=True, exist_ok=True)
    df.to_csv(cfg["output_panel_csv"], index=False)

if __name__ == "__main__":
    main()
