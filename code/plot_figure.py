import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import json

es = pd.read_csv("out/event_study_fixest.csv")
agg = json.loads(Path("out/agg_post.json").read_text())
twfe = json.loads(Path("out/twfe_summary.json").read_text())

fig = plt.figure(figsize=(10, 4.5))

# Panel A
ax1 = fig.add_subplot(1, 2, 1)
ax1.axhline(0.0, linewidth=1)
ax1.scatter(es["event_time"], es["estimate"])
# simple 1.96*se bands
ax1.vlines(es["event_time"],
           es["estimate"] - 1.96 * es["std.error"],
           es["estimate"] + 1.96 * es["std.error"])
ax1.set_title("Event study by event time")
ax1.set_xlabel("Event time")
ax1.set_ylabel("ATT")

# Panel B
ax2 = fig.add_subplot(1, 2, 2)
labels = ["TWFE", "Cohort ATT (+1..+6)"]
vals = [twfe["coef_treated"], agg["agg_att_post_1_to_6"]]
ax2.scatter(labels, vals)
for i, v in enumerate(vals):
    ax2.annotate(f"{v:.3f}", (labels[i], vals[i]), textcoords="offset points", xytext=(0,8), ha="center")
ax2.set_ylim(min(vals) - 0.01, max(vals) + 0.01)
ax2.set_title("Estimator comparison")
ax2.set_ylabel("Effect")

Path("fig").mkdir(exist_ok=True, parents=True)
plt.tight_layout()
plt.savefig("fig/fig_eventstudy.png", dpi=200)
