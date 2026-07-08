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

## Addendum (2026-07-07, Digital Discovery submission)

- Added `analysis_scripts/comparison_models/ohe_vs_descriptor_and_seeding.py`,
  `preliminary_campaign_results.csv` (derived from
  `02_results_of_70_experiments.xlsx`; 70 rows, 68 valid), and the committed
  output `ohe_vs_descriptor_and_seeding_results.txt`. The script is
  deterministic (random_state = 0) and reproduces ESI Table S10:
  descriptors 0.441 +/- 0.132, one-hot 0.576 +/- 0.159,
  descriptors + first-campaign seed 0.583 +/- 0.108 (five-fold test R2).
- README.md: retrospective-analyses section rewritten to be journal-neutral
  (previous version referenced the v18 Communications Chemistry revision and
  reviewer numbers); minor typo fixes.
- Verified against the released data: 192 attempted / 14 failed / 178 valid
  (results_log.csv, log.txt, and the final candidates table are mutually
  consistent). Manuscript wording was aligned to these counts.
- Still pending before the public release: run
  `cd analysis_scripts/shap && python run_shap_analysis.py --backend physbo`
  in an environment with PHYSBO installed (unchanged requirement from the
  previous QC pass), and re-run `ohe_vs_descriptor_and_seeding.py` once in
  the lab environment to confirm the committed output.
