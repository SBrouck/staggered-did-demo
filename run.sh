#!/usr/bin/env bash
set -euo pipefail

# Use conda environment Python
which python
R --version

python code/simulate_panel.py
python code/estimate_twfe.py
Rscript code/estimate_sa_cs.R
python code/plot_figure.py

echo "Figure at fig/fig_eventstudy.png"
