<<<<<<< HEAD
> Historical analysis retained for provenance. For the September 2026 revision, use the [current analysis instructions](../../revision/analysis/README.md). Old figure/table references and dependency versions below belong to earlier analyses.

# SHAP and PFI analysis

This directory contains a standalone, order-independent script for reproducing the Gaussian-process regression interpretability analysis used for an earlier manuscript version.

## Files

- `run_shap_analysis.py`: standalone Python script that performs five-fold Gaussian-process regression, SHAP analysis, prediction-sensitivity permutation-feature-importance analysis, and figure generation.
- `2024_0712_0146_candidates.csv`: input table for the SHAP/PFI analysis.
- `shap-formation.ipynb`: original exploratory notebook retained for provenance.
- `shap_results/`: precomputed numerical outputs and figures generated with the PHYSBO backend.
- `requirements.txt`: Python dependencies for this directory.

## Recommended installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell, activation can be performed with:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Reproduce the earlier analysis

The manuscript-level output was generated with PHYSBO. From this directory, run:

```bash
python run_shap_analysis.py --backend physbo
```

The default figure settings for SHAP plots are width 7.3 cm, height 6.0 cm, and font size 8 pt. These values can be changed explicitly:

```bash
python run_shap_analysis.py \
  --backend physbo \
  --shap-fig-width-cm 7.3 \
  --shap-fig-height-cm 6.0 \
  --shap-font-size 8
```

## Fallback execution without PHYSBO

If PHYSBO cannot be installed, the same script can be executed with a scikit-learn Gaussian-process fallback:

```bash
python run_shap_analysis.py --backend sklearn
```

This fallback is useful for testing the script in a clean Python environment, but the resulting numerical values may not exactly match the manuscript-level PHYSBO analysis.

## Main outputs

The default output directory is `shap_results/`. Important files include:

- `analysis_summary.json`: settings, backend information, and aggregate metrics.
- `cross_validation_metrics.csv`: five-fold training and test metrics.
- `training_predictions_by_fold.csv`: predictions, observations, and fold assignments.
- `shap_values_by_sample.csv`: sample-level SHAP values.
- `shap_absolute_summary.csv`: global SHAP importance summary.
- `pfi_prediction_sensitivity_summary.csv`: PFI summary from repeated descriptor shuffling.
- `prediction_parity.png`: observed-versus-predicted yield parity plot.
- `shap_absolute_bar.png`: global absolute SHAP contribution plot.
- `shap_summary_dots.png`: SHAP dot summary plot.
- `shap_summary_violin.png`: SHAP violin summary plot.
- `pfi_prediction_sensitivity_bar.png`: PFI bar plot for Supporting Information.
=======
> Historical analysis retained for provenance. For the September 2026 revision, use the [current analysis instructions](../../revision/analysis/README.md). Old figure/table references and dependency versions below belong to earlier analyses.

# SHAP and PFI analysis

This directory contains a standalone, order-independent script for reproducing the Gaussian-process regression interpretability analysis used for an earlier manuscript version.

## Files

- `run_shap_analysis.py`: standalone Python script that performs five-fold Gaussian-process regression, SHAP analysis, prediction-sensitivity permutation-feature-importance analysis, and figure generation.
- `2024_0712_0146_candidates.csv`: input table for the SHAP/PFI analysis.
- `shap-formation.ipynb`: original exploratory notebook retained for provenance.
- `shap_results/`: precomputed numerical outputs and figures generated with the PHYSBO backend.
- `requirements.txt`: Python dependencies for this directory.

## Recommended installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell, activation can be performed with:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Reproduce the earlier analysis

The manuscript-level output was generated with PHYSBO. From this directory, run:

```bash
python run_shap_analysis.py --backend physbo
```

The default figure settings for SHAP plots are width 7.3 cm, height 6.0 cm, and font size 8 pt. These values can be changed explicitly:

```bash
python run_shap_analysis.py \
  --backend physbo \
  --shap-fig-width-cm 7.3 \
  --shap-fig-height-cm 6.0 \
  --shap-font-size 8
```

## Fallback execution without PHYSBO

If PHYSBO cannot be installed, the same script can be executed with a scikit-learn Gaussian-process fallback:

```bash
python run_shap_analysis.py --backend sklearn
```

This fallback is useful for testing the script in a clean Python environment, but the resulting numerical values may not exactly match the manuscript-level PHYSBO analysis.

## Main outputs

The default output directory is `shap_results/`. Important files include:

- `analysis_summary.json`: settings, backend information, and aggregate metrics.
- `cross_validation_metrics.csv`: five-fold training and test metrics.
- `training_predictions_by_fold.csv`: predictions, observations, and fold assignments.
- `shap_values_by_sample.csv`: sample-level SHAP values.
- `shap_absolute_summary.csv`: global SHAP importance summary.
- `pfi_prediction_sensitivity_summary.csv`: PFI summary from repeated descriptor shuffling.
- `prediction_parity.png`: observed-versus-predicted yield parity plot.
- `shap_absolute_bar.png`: global absolute SHAP contribution plot.
- `shap_summary_dots.png`: SHAP dot summary plot.
- `shap_summary_violin.png`: SHAP violin summary plot.
- `pfi_prediction_sensitivity_bar.png`: PFI bar plot for Supporting Information.
>>>>>>> 3d0d2dcbce1cf236e6e2e8f2527c7b914b89b02b
