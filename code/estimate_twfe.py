import pandas as pd
import statsmodels.formula.api as smf
from pathlib import Path
import json

panel = pd.read_csv("out/panel.csv")
panel["id"] = panel["id"].astype("category")
panel["t"] = panel["t"].astype("category")

# static TWFE with unit and time FE
mod = smf.ols("y ~ treated + C(id) + C(t)", data=panel).fit(
    cov_type="cluster",
    cov_kwds={"groups": panel["id"]}
)

Path("out").mkdir(exist_ok=True)
summary = {
    "coef_treated": mod.params.get("treated", float("nan")),
    "se_treated": mod.bse.get("treated", float("nan")),
    "pvalue_treated": mod.pvalues.get("treated", float("nan")),
    "n_obs": int(mod.nobs),
    "n_units": int(panel["id"].nunique()),
    "n_periods": int(panel["t"].nunique()),
}
Path("out/twfe_summary.json").write_text(json.dumps(summary, indent=2))
panel[["id","t","y","treated","G"]].to_csv("out/twfe_design.csv", index=False)
