# Prediction ≠ Causation: designing identification in urban markets

This repo simulates a staggered rollout, estimates modern DiD, compares with TWFE, and exports a two panel figure.

## Quick start

### Prerequisites
- Python 3.8+ with conda
- R 4.0+ with basic packages (dplyr, readr, broom)

### Setup
```bash
# Create and activate conda environment
conda create -n stats python=3.11 -y
conda activate stats

# Install Python dependencies
conda install numpy pandas matplotlib statsmodels pyyaml -y

# Clone and run
git clone <repo-url>
cd urban-id-post
chmod +x run.sh
./run.sh
```

### Outputs
- **Data**: `out/panel.csv` - simulated panel data
- **Results**: `out/twfe_summary.json`, `out/event_study_fixest.csv`, `out/agg_post.json`
- **Figure**: `fig/fig_eventstudy.png` - two-panel event study and comparison plot
- **Paper**: `paper/draft.md` - article skeleton

## Notes
- All data are synthetic with realistic staggered adoption patterns
- Clustered inference at the policy unit level
- Simplified R implementation using available packages (no specialized DiD packages required)
- Sensitivity bounds reported as a simple grid for robustness checks

## Project Structure
```
urban-id-post/
├── config/experiment.yaml    # Simulation parameters
├── code/
│   ├── simulate_panel.py     # Generate synthetic panel data
│   ├── estimate_twfe.py      # Traditional TWFE estimation
│   ├── estimate_sa_cs.R      # Modern DiD (simplified)
│   └── plot_figure.py        # Create two-panel figure
├── out/                      # All outputs (CSV, JSON)
├── fig/                      # Final figure
├── paper/draft.md            # Article skeleton
└── run.sh                    # End-to-end pipeline
```
