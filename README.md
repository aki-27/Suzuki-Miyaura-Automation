# Suzuki-Miyaura-Automation

## 1. Input to Chemspeed
An AutoSuite program of Chemspeed can read CSV file as input. The file `input_for_chemspeed.csv` in `\:C\robotcsv` is an actual input to the Chemspeed system. This file has a header in 1 row and 4 experimental conditions in 4 rows. Each row includes 3 integer numbers delimited by a comma, which are the reagent number of ligands (1-15), bases (1-10), and solvents (1-10). Since the second batch, this file is automatically updated by the `decision_by_nimsos.bat` script.

## 2. Execution and Analysis of suggested experiments
Chemspeed system executes the suggested 4 experiments and their analysis. After the analysis, the SFC system outputs 2 files, `1st_result.csv` and `1st_profile.csv` for 1st experiment.
`1st_result.csv` is the actual chromatogram of an experiment, and `1st_profile.csv` is the pressure profile of a CO2 pump in the SFC system.
`2nd_result.csv` and `2nd_profile.csv`, `3rd_result.csv` and `3rd_profile.csv`, and `4th_result.csv` and `4th_profile.csv` are also outputted as same way.
