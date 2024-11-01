# Suzuki-Miyaura-Automation

## File IO in Automatic Experiment
- Chemspeed system
    - Input: `input_for_chemspeed.csv` (suggested 4 experimental conditions)
    - Output: `1st_result.csv`, `1st_profile.csv`, ..., `4th_profile.csv`, `4th_profile.csv` (resulted chromatograph and pressure profile of CO2 pump in SFC system)

- `evaluate_objective` program
    - Input: `1st_result.csv`, `1st_profile.csv`, ..., `4th_profile.csv`, `4th_profile.csv`
    - Output: writing objective to `candidates.csv` (table of all experimental conditions involving descriptors)
    - Setting file: `param.txt` (required parameters of quantitative analysis, e.g., wavelength, integration area, etc.)

- `decision_by_nimsos` program
    - Input: `candidates.csv`, `exp_table.csv` (table of expID, experimental conditions, and, symbolic representation of each conditions)
    - Output: `input_for_chemspeed.csv`
    - Setting file: `settings.txt`

## 1. Input to Chemspeed
An AutoSuite program of Chemspeed can read CSV file as input. The file `input_for_chemspeed.csv` is an actual input to the Chemspeed system. This file has a header in 1 row and 4 experimental conditions in 4 rows. Each row includes 3 integer numbers delimited by a comma, which are the reagent number of ligands (1-15), bases (1-10), and solvents (1-10). Since the second batch, this file is automatically updated by the `decision_by_nimsos.bat` script.

## 2. Execution and Analysis of suggested experiments
Chemspeed system executes the suggested 4 experiments and their analysis. After the analysis, the SFC system outputs 2 files, `1st_result.csv` and `1st_profile.csv` for 1st experiment.
`1st_result.csv` is an actual chromatogram, and `1st_profile.csv` is the pressure profile of a CO2 pump in the SFC system.
`2nd_result.csv` and `2nd_profile.csv`, `3rd_result.csv` and `3rd_profile.csv`, and `4th_result.csv` and `4th_profile.csv` are also outputted as same way.
These 8 files are transferred to `C:\robotcsv` directory by SFC system.

## 3. Integration and Error Detection
An `evaluate_objective` program writes 4 objective values of experiments in `candidates.csv.`
- Parameters of `param.txt`
    - STD_MW: molecular weight of standard
    - SUB_MW: molecular weight of the substrate
    - MV_LEN: wavelength for integration
    - STD_INI: starting point of integration of STD
    - STD_FIN: ending point of integration of STD
    - P1_INI: starting point of integration of p1 (starting material, compound 1)
    - P1_FIN: starting point of integration of p1 (starting material, compound 1)
    - P1_SLP: slope of the calibration curve
    - P2_INI: starting point of integration of p2 (starting material, product 3)
    - P2_FIN: starting point of integration of p2 (starting material, product 3)
    - P2_SLP: slope of the calibration curve
    - P3_INI: starting point of integration of p3 (starting material, by-product 4)
    - P3_FIN: starting point of integration of p3 (starting material, by-product 4)
    - P3_SLP: slope of the calibration curve
    - STD_WT: actual weight of STD
    - SUB_WT: actual weight of the substrate
    - BL_AVE: area of baseline correction
    - LOW_PS: lower limit of pressure of SFC system
    - UPR_PS: upper limit of pressure of SFC system

# Used version for Actual Experiment
`nimsos 1.0.1`

`pyinstaller 5.8.0`

These programs were compiled with pyinstaller to one exe file by below PowerShell command.
```
..\pyinstaller.exe $Args[0] `
    --hidden-import=sklearn.metrics._pairwise_distances_reduction._datasets_pair `
    --hidden-import=sklearn.metrics._pairwise_distances_reduction._middle_term_computer `
    --onefile
Copy-Item -Path .\dist\$Args[0] -Destination .\$Args[0]
```

# License
This program is distributed under the MIT License.
2024 Seiji Akiyama s.aki@icredd.hokudai.ac.jp main developer
