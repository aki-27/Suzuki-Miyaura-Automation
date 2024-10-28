# Suzuki-Miyaura-Automation

## 1. Input to Chemspeed
An AutoSuite program of Chemspeed can read CSV file as input. The file `input_for_chemspeed.csv` is an actual input to the Chemspeed system. This file has a header in 1 row and 4 experimental conditions in 4 rows. Each row includes 3 integer numbers delimited by a comma, which are the reagent number of ligands (1-15), bases (1-10), and solvents (1-10). Since the second batch, this file is automatically updated by the `decision_by_nimsos.bat` script.

## 2. Execution of suggested experiments
Chemspeed
