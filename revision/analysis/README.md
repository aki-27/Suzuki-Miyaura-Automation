# September 2026 retrospective revision analyses

These analyses use archived experimental data. They do not execute instrument controls or constitute additional wet experiments. The historical online campaign used PHYSBO 2.0.0/NIMS-OS 1.0.1; these new calculations use scikit-learn and do not recreate that executable.

## Reproduce

Use Python 3.12.14 in a separate environment. From this directory:

```bash
python -m pip install -r requirements_revision.txt
python analysis_revision.py models
python analysis_revision.py simulate
python analysis_revision.py figures
python verify_analysis.py
python stats_supplement.py
python export_canonical_data.py
```

The scripts also work when invoked by path from the repository root. `models` reconstructs cross-validation, campaign transfer, ligand holdout, chronological predictions, SHAP, permutation sensitivity and virtual surfaces. `simulate` runs 210 virtual campaigns with a budget of 192 evaluations each. `figures` writes the seven included plots to `../source/images`. `stats_supplement.py` reconstructs additional descriptive statistics in `stats/`; `export_canonical_data.py` reconstructs the canonical tables in `../data/`. The scripts overwrite their corresponding outputs. Floating-point and optimizer differences across platforms may change simulated trajectories; supplied numerical outputs are those used in the revision.

To check supplied outputs without refitting, run `verify_analysis.py`. It loads the bundled, locally generated `analysis_results/cv_descriptor_models.joblib`; deserialize only a trusted copy (verify its package hash before use). The standard-library integrity checker at the repository root does not deserialize model files.

## Inputs and meaning

`data/Suzuki-Miyaura-Automation-main_v20/` is the unchanged supplied repository snapshot (88 files). Its README, requirements and QC note are historical documents, not current instructions.

- Main candidate descriptors and 178 valid log-yield responses: `analysis_scripts/shap/2024_0712_0146_candidates.csv` in that snapshot.
- Preliminary attempts: `analysis_scripts/comparison_models/preliminary_campaign_results.csv`; 68 normal terminations from 70 attempts are used for modeling.
- Main chronology and failure records: `results_log.csv`. Its `batch` field is position 1–4; chronological cycles are groups of four consecutive attempts.
- There are 13 shared valid conditions and 233 distinct valid candidate combinations. The descriptor representation used retrospectively for preliminary measurements does not reconstruct the preliminary online model.
- Historical main input had 12 columns; new descriptor-only models have eight. See [confirmed experimental details](../../docs/EXPERIMENTAL_RECORD.md) and [standard PHYSBO settings](library_audit/STANDARD_SETTINGS.md).
- Simulated responses are deterministic fitted virtual log yields, not unmeasured experimental results. Alternative virtual surfaces test some emulator assumptions but cannot remove sampling bias or establish experimental repeatability, a global optimum or human-expert superiority.

## Outputs and checks

`analysis_results/summary.json` gives predictive metrics. `cv_by_fold.csv` records fold scores and fitted kernels; `cv_assignments.csv` records candidate IDs in each train/test split. NPZ files contain observed targets, predictions, uncertainty, SHAP values and virtual surfaces. CSVs include transfer predictions, paired campaign conditions, chronological predictions, ligand holdouts, permutation sensitivity and candidate scenarios. `methods.json` and `simulation_methods.json` record analysis settings.

`simulation_runs.csv` and `simulation_traces.npy` share row order. Stored seed 0 means RNG seed 7000, through 7009. `n_to95` counts ordered evaluations including initialization, and may fall within a four-proposal batch; the policy updates after a complete batch. **193 means the target was not reached within the 192-evaluation budget**, not an observed 193rd evaluation. `simulation_summary.json` summarizes the four-observation initialization benchmark. `stats/` adds early-budget, initialization, paired-contrast, binomial-interval, random-hit, transfer-sensitivity, chronological-window and batch-denominator summaries.

`verify_analysis.py` checks SHAP additivity, strictly earlier chronological training, paired simulation initialization, monotone best-so-far traces, attainment coding, observation counts and reported metrics. `../data/validation.json` records original-value preservation and full error-field export checks.

## Numerical diagnostics and limits

The diagnostic rerun preserved all 23 original numerical outputs; 22 were byte-identical, while the saved model file changed only by added diagnostic attributes and retained identical learned numerical state. `models_fit_diagnostics.json` records 155 fits and two noise-bound warnings. Internal solver return statuses of the standard optimizer were not separately recorded, so absence of other captured warnings does not prove solver success.

`simulate_fit_diagnostics.json` records 6,990 custom solver returns: 6,971 successful, 18 abnormal and one iteration-limit return. Returned finite estimates were retained without retry. Noise-bound warnings occurred in 1,256 updates and are a distinct quantity from unsuccessful solver returns. The unsuccessful updates affected 14 of 150 GP-policy campaigns. Sensitivity to alternative tolerances, bounds or retry rules was not established.

The supplied figures and numerical results are preserved as used for the revision. Running these scripts does not rewrite manuscript text or tables. The manuscript, reviewer correspondence and internal author-check notes are maintained separately from this public code/data repository.
