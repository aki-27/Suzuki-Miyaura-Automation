<<<<<<< HEAD
# Suzuki-Miyaura-Automation

Code and archived experimental records for automated Suzuki–Miyaura reaction optimization. This repository includes the September 2026 revision analyses and preserves the experimental control scripts and recorded data.

## Start here

| Material | Location |
|---|---|
| Revision analysis instructions and scope | [revision/analysis/README.md](revision/analysis/README.md) |
| Candidate and chronological attempt tables | [revision/data/README.md](revision/data/README.md) |
| Confirmed experimental software and chemical corrections | [docs/EXPERIMENTAL_RECORD.md](docs/EXPERIMENTAL_RECORD.md) |
| Version-specific PHYSBO defaults | [revision/analysis/library_audit/STANDARD_SETTINGS.md](revision/analysis/library_audit/STANDARD_SETTINGS.md) |
| Historical robot/SFC file workflow | [docs/HISTORICAL_WORKFLOW.md](docs/HISTORICAL_WORKFLOW.md) |
| Changes and provenance | [RELEASE_NOTES.md](RELEASE_NOTES.md) |
| Package integrity check | `python verify_repository.py` |

## Reproduce the revision analyses

Use a separate Python 3.12.14 environment. From the repository root:

```bash
python -m pip install -r requirements.txt
python revision/analysis/verify_analysis.py
python revision/analysis/export_canonical_data.py
python revision/analysis/stats_supplement.py
```

To refit models, rerun the virtual campaigns, and regenerate plots:

```bash
python revision/analysis/analysis_revision.py models
python revision/analysis/analysis_revision.py simulate
python revision/analysis/analysis_revision.py figures
python revision/analysis/verify_analysis.py
python revision/analysis/stats_supplement.py
```

The full simulation step performs 6,990 GP updates and may take substantial time. These commands write only revision-analysis outputs; they do not run the robot controls. Supplied numerical outputs and seven generated figures are included. Reruns overwrite outputs, so an integrity check against the delivered SHA-256 manifest is expected to change after regeneration. Full environment and interpretation details are in the analysis README.

## Experimental data and interpretation

The preliminary campaign contains 70 attempts (68 valid); the main campaign contains 192 attempts (178 valid). There are 13 shared valid conditions and 233 distinct valid combinations across campaigns. All invalid attempts remain in the canonical exports with their original error text. Candidate ID is not chronological attempt number.

For the **2024 main campaign**, the authors confirmed PHYSBO **2.0.0**, used through NIMS-OS **1.0.1**, with standard implementations and no manual hyperparameter adjustment. Automatic parameter initialization and fitting still occurred. The historical input had 12 numerical columns: four identifiers and eight chemical descriptors. The revision's descriptor-only models use eight descriptors and scikit-learn; they are retrospective analyses, not a replay of the historical optimizer. The 2023 preliminary campaign is not assigned the 2024 version without evidence.

No additional wet experiments are included in this revision. Virtual responses are emulator predictions, not measurements. The analysis does not establish experimental repeatability, a global experimental optimum, or superiority to human experts. Complete historical executable-build dependencies and learned model states are not supplied.

## Preserved historical materials

Root-level Python scripts, batch files, AutoSuite `.app`, parameter files, candidate tables, and logs retain their supplied bytes. They document the historical installation; the `.bat` wrappers reference compiled `.exe` files that are not included. Raw detector traces and a complete executable environment are also not included. See the historical workflow before using this code with instrument files.

`analysis_scripts/` retains earlier analyses for provenance. Its legacy SHAP and simulation results are not the replacement source for the September 2026 revision figures. The immutable snapshot under `revision/analysis/data/` retains the original README and requirements as historical documents; current instructions are here and in `revision/analysis/README.md`.

## License

Project code is distributed under the [MIT License](LICENSE), retaining the original copyright notice. External libraries retain their own licenses. Dependencies are installed separately; this repository does not vendor NIMS-OS or PHYSBO. Original developer: Seiji Akiyama.
=======
# Suzuki-Miyaura-Automation

Code and archived experimental records for automated Suzuki–Miyaura reaction optimization. This repository includes the September 2026 revision analyses and preserves the experimental control scripts and recorded data.

## Start here

| Material | Location |
|---|---|
| Revision analysis instructions and scope | [revision/analysis/README.md](revision/analysis/README.md) |
| Candidate and chronological attempt tables | [revision/data/README.md](revision/data/README.md) |
| Confirmed experimental software and chemical corrections | [docs/EXPERIMENTAL_RECORD.md](docs/EXPERIMENTAL_RECORD.md) |
| Version-specific PHYSBO defaults | [revision/analysis/library_audit/STANDARD_SETTINGS.md](revision/analysis/library_audit/STANDARD_SETTINGS.md) |
| Historical robot/SFC file workflow | [docs/HISTORICAL_WORKFLOW.md](docs/HISTORICAL_WORKFLOW.md) |
| Changes and provenance | [RELEASE_NOTES.md](RELEASE_NOTES.md) |
| Package integrity check | `python verify_repository.py` |

## Reproduce the revision analyses

Use a separate Python 3.12.14 environment. From the repository root:

```bash
python -m pip install -r requirements.txt
python revision/analysis/verify_analysis.py
python revision/analysis/export_canonical_data.py
python revision/analysis/stats_supplement.py
```

To refit models, rerun the virtual campaigns, and regenerate plots:

```bash
python revision/analysis/analysis_revision.py models
python revision/analysis/analysis_revision.py simulate
python revision/analysis/analysis_revision.py figures
python revision/analysis/verify_analysis.py
python revision/analysis/stats_supplement.py
```

The full simulation step performs 6,990 GP updates and may take substantial time. These commands write only revision-analysis outputs; they do not run the robot controls. Supplied numerical outputs and seven generated figures are included. Reruns overwrite outputs, so an integrity check against the delivered SHA-256 manifest is expected to change after regeneration. Full environment and interpretation details are in the analysis README.

## Experimental data and interpretation

The preliminary campaign contains 70 attempts (68 valid); the main campaign contains 192 attempts (178 valid). There are 13 shared valid conditions and 233 distinct valid combinations across campaigns. All invalid attempts remain in the canonical exports with their original error text. Candidate ID is not chronological attempt number.

For the **2024 main campaign**, the authors confirmed PHYSBO **2.0.0**, used through NIMS-OS **1.0.1**, with standard implementations and no manual hyperparameter adjustment. Automatic parameter initialization and fitting still occurred. The historical input had 12 numerical columns: four identifiers and eight chemical descriptors. The revision's descriptor-only models use eight descriptors and scikit-learn; they are retrospective analyses, not a replay of the historical optimizer. The 2023 preliminary campaign is not assigned the 2024 version without evidence.

No additional wet experiments are included in this revision. Virtual responses are emulator predictions, not measurements. The analysis does not establish experimental repeatability, a global experimental optimum, or superiority to human experts. Complete historical executable-build dependencies and learned model states are not supplied.

## Preserved historical materials

Root-level Python scripts, batch files, AutoSuite `.app`, parameter files, candidate tables, and logs retain their supplied bytes. They document the historical installation; the `.bat` wrappers reference compiled `.exe` files that are not included. Raw detector traces and a complete executable environment are also not included. See the historical workflow before using this code with instrument files.

`analysis_scripts/` retains earlier analyses for provenance. Its legacy SHAP and simulation results are not the replacement source for the September 2026 revision figures. The immutable snapshot under `revision/analysis/data/` retains the original README and requirements as historical documents; current instructions are here and in `revision/analysis/README.md`.

## License

Project code is distributed under the [MIT License](LICENSE), retaining the original copyright notice. External libraries retain their own licenses. Dependencies are installed separately; this repository does not vendor NIMS-OS or PHYSBO. Original developer: Seiji Akiyama.
>>>>>>> 3d0d2dcbce1cf236e6e2e8f2527c7b914b89b02b
