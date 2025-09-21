# Complete Package for ChatGPT Article Redaction

## Project Overview
This is a reproducible pipeline for "Prediction ≠ Causation: designing identification in urban markets" - a Substack article about modern difference-in-differences methods for staggered policy rollouts.

## Key Results Summary

### TWFE Results (Traditional Method)
- **Coefficient**: -0.0105 (1.85 percentage points)
- **Standard Error**: 0.0185
- **P-value**: 0.571 (not significant)
- **Sample**: 1,920 observations, 80 units, 24 periods

### Modern DiD Results (Cohort-Robust)
- **Aggregated ATT (+1 to +6 months)**: -0.0026 (0.26 percentage points)
- **Standard Error**: 0.0431
- **Bootstrap P-value**: 0.05 (significant)

### Event Study Coefficients
| Event Time | Estimate | Std Error |
|------------|----------|-----------|
| 0 (adoption) | -0.0154 | 0.0633 |
| +1 month | 0.0078 | 0.0525 |
| +2 months | -0.0395 | 0.0522 |
| +3 months | 0.0069 | 0.0419 |
| +4 months | -0.0069 | 0.0418 |
| +5 months | 0.0381 | 0.0330 |
| +6 months | -0.0221 | 0.0329 |

## Key Findings for Article

1. **TWFE vs Modern DiD**: Traditional TWFE shows no significant effect (-0.0105, p=0.571), while cohort-robust methods show a small but significant effect (-0.0026, p=0.05).

2. **Event Study Pattern**: The event study shows some variation in post-treatment effects, with the largest effect at +5 months (0.0381) and some negative effects in other periods.

3. **Pre-treatment**: No pre-treatment effects visible (coefficients around zero before adoption).

4. **Sample Size**: 80 units across 24 periods with staggered adoption at months 10, 12, 14, and 16.

## Files to Include in ChatGPT Prompt

### 1. Main Figure
- `fig/fig_eventstudy.png` - Two-panel figure showing event study and estimator comparison

### 2. Data Files
- `out/panel.csv` - Full simulated dataset (1,920 observations)
- `out/event_study_fixest.csv` - Event study coefficients
- `out/twfe_summary.json` - TWFE results
- `out/agg_post.json` - Aggregated post-treatment effects

### 3. Article Draft
- `paper/draft.md` - Complete article skeleton with structure

### 4. Technical Details
- `config/experiment.yaml` - Simulation parameters
- `code/simulate_panel.py` - Data generation code
- `code/estimate_twfe.py` - TWFE estimation
- `code/estimate_sa_cs.R` - Modern DiD estimation
- `code/plot_figure.py` - Figure generation

## Article Writing Instructions

### Style Guidelines
- Human and clear writing
- Short sentences
- Light technical humor
- No em dashes
- No semicolons
- Concise and accessible

### Key Messages
1. **Problem**: Traditional TWFE can be biased in staggered designs
2. **Solution**: Use cohort-robust methods that respect timing heterogeneity
3. **Evidence**: Show the difference between TWFE and modern methods
4. **Policy**: Pre-register designs and report uncertainty properly

### Structure to Follow
1. Hook: Risk scores vs policy effects
2. Claim: Staggered rollouts need proper identification
3. Evidence: Figure and results comparison
4. Methods: Technical approach
5. Limitations: Spillovers, selection, pre-testing
6. Policy: Best practices for implementation
7. CTA: Links and engagement

## Technical Context
- Simulated data with realistic staggered adoption
- 4 cohorts adopting at different times
- Binary outcome with logistic link
- Clustered standard errors
- Wild cluster bootstrap for inference
- Sensitivity analysis for robustness

## References to Include
- Sun and Abraham 2021 (Journal of Econometrics)
- Callaway and Sant'Anna 2021 (Journal of Econometrics)  
- Goodman-Bacon 2021 (Journal of Econometrics)
- Borusyak Jaravel Spiess 2024 (Review of Economic Studies)
- Cameron Gelbach Miller 2008 (Review of Economics and Statistics)
- Rambachan Roth 2023 (Review of Economic Studies)
