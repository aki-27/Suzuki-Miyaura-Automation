<<<<<<< HEAD
# Repository quality-control record

The September 2026 replacement preserves all 88 supplied baseline paths and includes an unchanged 88-file input snapshot. Original robot control scripts, parameters, data and numerical outputs retain their source bytes. Changes to baseline files are confined to README/QC documentation and the root requirements entry point.

The root SHA-256 manifest covers every distributed file except the manifest itself. Run `python verify_repository.py` before analysis regeneration to check file-set equality, SHA-256 hashes, input-snapshot preservation and Python syntax without running historical controls.

`revision/analysis/verify_analysis.py` checks saved numerical outputs, including SHAP additivity, chronological training, paired simulation initialization, attainment coding and reported metrics. The standard-library canonical exporter validates source values and attempt counts. The packaging check regenerates canonical CSVs and supplementary statistics into a separate directory and compares their contents with the supplied outputs.

This packaging operation does not refit models, rerun the complete simulations, execute PHYSBO/robot programs or perform wet experiments. The full retrospective analyses were already completed for the manuscript revision. Historical binary replay and physical system operation remain outside these checks.
=======
# Repository quality-control record

The September 2026 replacement preserves all 88 supplied baseline paths and includes an unchanged 88-file input snapshot. Original robot control scripts, parameters, data and numerical outputs retain their source bytes. Changes to baseline files are confined to README/QC documentation and the root requirements entry point.

The root SHA-256 manifest covers every distributed file except the manifest itself. Run `python verify_repository.py` before analysis regeneration to check file-set equality, SHA-256 hashes, input-snapshot preservation and Python syntax without running historical controls.

`revision/analysis/verify_analysis.py` checks saved numerical outputs, including SHAP additivity, chronological training, paired simulation initialization, attainment coding and reported metrics. The standard-library canonical exporter validates source values and attempt counts. The packaging check regenerates canonical CSVs and supplementary statistics into a separate directory and compares their contents with the supplied outputs.

This packaging operation does not refit models, rerun the complete simulations, execute PHYSBO/robot programs or perform wet experiments. The full retrospective analyses were already completed for the manuscript revision. Historical binary replay and physical system operation remain outside these checks.
>>>>>>> 3d0d2dcbce1cf236e6e2e8f2527c7b914b89b02b
