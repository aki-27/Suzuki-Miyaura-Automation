# Experimental record and confirmed corrections

## Software

PHYSBO 2.0.0 was used in the 2024 main campaign, as confirmed by co-author Tamura, a NIMS-OS developer. The recorded NIMS-OS version is 1.0.1. The authors confirmed use of standard implementations without manual adjustment of hyperparameters or other algorithm settings. The wrapper's explicit seed, acquisition function and proposal count still apply; standard automatic initialization and learning are not disabled.

The historical executable was built using PyInstaller 5.8.0 on Windows 10. A complete environment lockfile, compiled executables and the learned states from each historical iteration have not been reconstructed. `requirements_historical.txt` records known versions, not a tested complete installation recipe. The 2023 preliminary campaign's exact PHYSBO version remains unassigned.

NIMS-OS 1.0.1 declares PHYSBO as an unpinned dependency. Its version alone cannot identify the installed PHYSBO version; the 2.0.0 assignment is based on the author confirmation. A later legacy requirement `physbo>=3.2.0` concerns retrospective software, not the 2024 run.

The main-campaign NIMS-OS wrapper passed all 12 non-objective columns, including candidate and component IDs, into the model. It centered this matrix, created a fresh policy for each batch, set seed 0, and requested four proposals using Thompson sampling, one probe, interval 0 and 1,000 random basis functions. See [the version-specific settings](../revision/analysis/library_audit/STANDARD_SETTINGS.md).

## Chemical and quantitative documentation

- Base identifiers in the revised descriptions are B5 = KOH and B6 = K3PO4.
- B4 used **55.6 mmol K2CO3**, like the other base stocks. The corresponding formula-mass calculation is approximately **7.68 g**. This is a calculated mass corresponding to the confirmed amount, not a newly recovered balance reading. The nominal stock concentration is 1.11 mol/L; a 0.90 mL dose corresponds to approximately 1.00 mmol (5 equivalents).
- The internal-standard target mass was **16.5 mg**; the actual measured and quantification mass was **16.605 mg**. The supplied `param.txt` already contains `STD_WT=16.605`. Recorded yields and objectives therefore do not require recalculation for this clarification.

These documentation corrections do not modify source experiment records or the revision's numerical outputs. The provenance snapshot deliberately retains historical descriptions; they are superseded by this record for current interpretation.

## Limits of the supplied records

The canonical data retain all attempts, including invalid results and overlapping error flags. Historical logs contain processed integration/quantification values; they are not raw detector traces. No independent repeat experiments, additional temperature experiments, unmeasured yields or complete 2023/2024 executable environments are added by this repository revision.
