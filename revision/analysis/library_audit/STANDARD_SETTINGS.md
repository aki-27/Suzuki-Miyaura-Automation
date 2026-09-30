# Author-confirmed standard PHYSBO 2.0.0 / NIMS-OS 1.0.1 settings

The authors confirmed that the standard implementations were used and no hyperparameters or other algorithm settings were manually adjusted. The existing NIMS-OS wrapper still supplies its explicit seed/proposal/acquisition settings. This confirmation means no author customization; it does not mean that learned hyperparameters were fixed.

## Source and scope

Official PyPI source: https://pypi.org/project/physbo/2.0.0/
Archive SHA-256: `ed8e6dcf5b47bba87f15596b6111a4d1ec671ac3af452b884332778e27855d66`.
The source archive hash matched the official PyPI metadata. The audited source archive is identified in `physbo_source_provenance.json`; selected files were read statically, not installed or executed. Third-party source is not vendored in this repository; obtain the original archive from its recorded official URL. These settings describe the confirmed 2024 main campaign; they are not assigned to the December 2023 preliminary campaign.

## Code path and defaults

- NIMS-OS `ai_tool_physbo.py`: centers the candidate matrix; creates a new policy; sets seed 0; requests one probe with four selections, TS, `interval=0`, and 1000 random basis functions. No custom config/model is supplied.
- `search/discrete/policy.py`: missing config creates `set_config()`; 1000 random bases select the BLM predictor, whose fit calls the underlying GP model's fit before exporting the random-feature model.
- `predictor.py`: constant mean, Gaussian covariance with `ard=False`, Gaussian observation likelihood. The kernel is isotropic.
- `misc/set_config.py`: default method Adam, 20 initial-parameter trials, 50 epochs per initial trial, then 500 epochs; minibatch size 64; evaluation cap 5000; Adam step 0.001, moment factors 0.9/0.999, epsilon 1e-6. Batch size is reduced to N when fewer than 64 observations are available. `search.alpha=1.0`, `multi_probe_num_sampling=20`.
- `gp/core/learning.py`: each trial draws data-dependent candidate parameters and performs 50 epochs. The lowest negative log marginal likelihood trial is selected and trained for a further 500 epochs. A fresh policy at each batch repeats this procedure.
- Candidate constant mean is `median(t)`; signal scale is `std(t)` and noise standard deviation is `std(t)/10`. The isotropic kernel draws M=max(2000,floor(N/5)) pairs of training rows with replacement, sorts their Euclidean distances, selects an index corresponding to the 10th, 30th, 50th, 70th or 90th percentile (using the code's integer index), and adds 1e-8 before taking the log width. These are initialization candidates, not final learned values.
- Gaussian width/signal-scale and likelihood-standard-deviation support limits are 1e-6 to 1e6; constant-mean support is -1e12 to 1e12. The constructor's width=3, scale=1, mean=0 and noise SD=1 are placeholders; the default nonzero initial search replaces them with data-dependent candidates, so they are not reported as the optimizer's effective fixed starting values.

The source-defined algorithm can now be documented from the author confirmation and version-specific code. Individual historical learned numerical states and the complete executable build environment were not recovered; no exact replay is claimed. No new wet experiment or statistical rerun was performed for this documentation update.
