# GitHub repository QC note

The repository structure was checked for the files required by the revised manuscript and response letter.

## Syntax check

- `analysis_scripts/shap/run_shap_analysis.py`: ok
- `decision_by_nimsos_2024_06_21.py`: ok
- `evaluate_objective_2024_06_25.py`: ok

## Required files

All expected files listed for SHAP/PFI, batch-average, descriptor-comparison, acquisition-function, and core autonomous-optimization workflows were present.

## Note

The PHYSBO backend was not executed in this container. The repository includes the precomputed SHAP/PFI outputs under `analysis_scripts/shap/shap_results/`. Before final public release, run `cd analysis_scripts/shap && python run_shap_analysis.py --backend physbo` in an environment in which PHYSBO is installed.
