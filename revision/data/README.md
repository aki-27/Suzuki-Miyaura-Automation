# Canonical candidate and attempt tables

These UTF-8 CSV files reorganize the supplied `Suzuki-Miyaura-Automation-main_v20` archive into a candidate table and two chronological attempt tables. They preserve recorded experimental values and invalid attempts. They do not execute the robot software, refit a model, infer unmeasured outcomes, or correct historical chemical or quantitative records.

| File | Rows, excluding header | Contents |
|---|---:|---|
| `candidate_space.csv` | 1500 | Candidate ID, three component IDs, and eight chemical descriptors; no response/objective column |
| `preliminary_attempts.csv` | 70 | Preliminary campaign attempts, derived status/identifiers, and all ten original source columns |
| `main_attempts.csv` | 192 | Main campaign attempts in recorded order, explicit cycle/position, all source-log values, full error text, and separately identified valid candidate-table objectives |
| `validation.json` | — | Counts, consistency checks, source/output SHA-256 hashes, and machine-readable column mappings |

The combined datasets contain 262 attempts, 246 valid records, and 233 distinct valid candidate combinations. The preliminary campaign has 68 valid and 2 invalid attempts; the main campaign has 178 valid and 14 invalid attempts. Thirteen valid conditions occur in both campaigns. Within each campaign, valid conditions are unique. The main campaign has 185 distinct attempted candidates because some failed candidates were retried.

## Source and provenance

All paths below are relative to the supplied archive root `Suzuki-Miyaura-Automation-main_v20/`:

- `candidate_space.csv`: `candidates.csv`, excluding its `objectives` column. This source is byte-for-byte identical to `analysis_scripts/shap/2024_0712_0146_candidates.csv`, the candidate snapshot read by the revision's `analysis_revision.py`.
- `preliminary_attempts.csv`: `analysis_scripts/comparison_models/preliminary_campaign_results.csv`.
- `main_attempts.csv`: `results_log.csv`; the additional `candidate_table_log_objective` comes from `candidates.csv` only for valid attempts.
- The interpretation of the main log's fields is checked against `evaluate_objective_2024_06_25.py`, `decision_by_nimsos_2024_06_21.py`, and `settings.txt`, read as text only.

Input-file hashes are recorded in `validation.json`. The exporter checked that these files were unchanged after export. The supplied archive is the primary source for these tables; the related public repository is [aki-27/Suzuki-Miyaura-Automation](https://github.com/aki-27/Suzuki-Miyaura-Automation). A public repository URL does not identify the exact historical executable or its complete dependency environment. The README of that repository records NIMS-OS 1.0.1 and PyInstaller 5.8.0 for the actual experiments; the use of PHYSBO 2.0.0 for the main campaign was confirmed by co-author Tamura, a developer of NIMS-OS, as confirmed by the authors. See `../analysis/library_audit/PHYSBO_VERSION_2024-06-21.md` for the confirmation provenance. This supersedes the earlier conditional inference without implying that the full executable environment was recovered. The later `physbo>=3.2.0` requirement must not be treated as the July 2024 runtime version.

## Candidate identity is not chronological experiment number

`candidateID` is the source's `expID`, a fixed row identifier in the 1500-condition candidate space. It is not the order in which a reaction was attempted. All source candidates satisfy

```text
candidateID = ligandID + 15*(baseID - 1) + 150*(solventID - 1)
```

`attempt` identifies a chronological attempt within one campaign and starts at 1 again in the other campaign. The main campaign's attempt 1 is candidate 1282; attempt 102 is candidate 408. Join chemical conditions using `candidateID` or the three component IDs, never by `attempt` across campaigns. Repeated candidate IDs among main attempts must not be silently deduplicated.

For `main_attempts.csv`, `cycle = floor((attempt-1)/4)+1` ranges from 1 to 48, and `position = ((attempt-1) mod 4)+1` ranges from 1 to 4. Cycle 1 is initialization; cycles 2–48 are executed closed-loop batches. The original log column named `batch` is actually position 1–4, and is retained as `source_batch_position`. It is not the cycle number. `recorded_timestamp` is the result-writing timestamp as supplied, without an explicit timezone offset; it is not a reaction start time.

## Candidate column mapping

The first four fields identify the condition. The next eight fields are the chemical descriptors, in the same order used by `analysis_revision.py`.

| Original column | Canonical column | Meaning/unit |
|---|---|---|
| `expID` | `candidateID` | Fixed candidate-table ID, 1–1500 |
| `ligand` | `ligandID` | Ligand category ID, 1–15 |
| `base` | `baseID` | Base category ID, 1–10 |
| `solvent` | `solventID` | Solvent category ID, 1–10 |
| `cone angle` | `cone_angle` | Ligand cone angle, degrees |
| `TEP` | `TEP` | Calculated ligand electronic descriptor as supplied, cm^-1 |
| `calc P shift` | `calculated_31P_shift` | Calculated phosphorus chemical shift, conventionally reported in ppm |
| `pKa` | `pKa` | Conjugate-acid pKa as supplied |
| `Pauling ionic radii` | `Pauling_cation_radius` | Cation radius, pm |
| `Hansen-dD` | `Hansen_dD` | Dispersion Hansen parameter, MPa^0.5 |
| `Hansen-dP` | `Hansen_dP` | Polar Hansen parameter, MPa^0.5 |
| `Hansen-dH` | `Hansen_dH` | Hydrogen-bonding Hansen parameter, MPa^0.5 |

These are the main-campaign descriptor values. The preliminary campaign originally used a different solvent representation. Joining preliminary outcomes to this candidate file creates the common retrospective descriptor representation; it does not reconstruct the preliminary online model. The historical main-campaign wrapper passed all 12 non-objective columns to PHYSBO, including the four numerical identifiers. The candidate export neither removes nor chemically reinterprets those identifiers; an eight-descriptor analysis must explicitly select the eight descriptor fields.

## Preliminary attempt fields

The derived columns `attempt`, `candidateID`, `status`, `failure_category`, and the three Boolean flag columns precede the original source columns. All ten original columns and their values are retained:

```text
exp_no, expID, ligand, base, solvent, compound1_recovery,
compound3_yield, compound4_yield, total_yield, error_detection
```

`exp_no` equals `attempt`; `expID` equals `candidateID`. Recovery and yield values are fractions, so 0.20 denotes 20%. They are copied from the supplied preliminary-results table. No floor, logarithm, clipping, or recomputation of the total is applied. The supplied table contains no historical objective column; this export does not invent one. In particular, the preliminary acquisition objective (mono-product minus bis-product yield) must be distinguished from a retrospective log-mono-yield target. The revision analysis applies `ln(max(compound3_yield, 0.0001))` to valid preliminary data; that transformation is not applied to the preserved CSV fields here. Preprocessing before the supplied preliminary table was produced cannot be fully reconstructed from this table alone.

## Main attempt field mapping

All original main-log values are retained under the following explicit names. Numeric strings retain their source precision; whitespace surrounding numeric fields is normalized.

| Original field | Canonical field |
|---|---|
| `time` | `recorded_timestamp` |
| `batch` | `source_batch_position` |
| `expID` | `candidateID` |
| `ligand`, `base`, `solvent` | `ligandID`, `baseID`, `solventID` |
| `notation` | `recorded_notation` |
| `p1 yield` | `recorded_compound1_recovery_fraction` |
| `p2 yield` | `recorded_compound3_yield_fraction` |
| `p3 yield` | `recorded_compound4_yield_fraction` |
| `total yield` | `recorded_total_yield_fraction` |
| `objective` | `recorded_log_objective` |
| `std area` | `recorded_STD_area` |
| `p1 area` | `recorded_compound1_area` |
| `p2 area` | `recorded_compound3_area` |
| `p3 area` | `recorded_compound4_area` |
| `errors` and its comma-separated continuation | `source_error_text` |

Compound 1 is unreacted starting material, compound 3 is the mono-functionalized target, and compound 4 is the bis-functionalized product. `p1`, `p2`, and `p3` are historical software labels; `p2` does not mean manuscript compound 2. Areas are the numerical integration outputs in the historical software's units; the exporter does not rescale or reintegrate them.

The six-decimal `recorded_log_objective` is copied from each attempt's log, including invalid attempts. It is an observation/objective, not a forecast or acquisition score. Every supplied main attempt has a positive recorded mono yield; the recorded objective corresponds to its natural log of yield fraction, subject to independent rounding of yield and objective. Do not overwrite this field by taking the logarithm of the rounded six-decimal yield.

`candidate_table_log_objective` is the higher-precision final candidate-table value used by the revision's main-campaign cross-validation. It is populated only for the 178 valid attempts and is blank for all invalid attempts, even where that failed candidate later succeeded. All populated values agree with `recorded_log_objective` within six-decimal rounding. It is not a recovered historical model state or a new measurement. The revision's time-ordered analysis instead uses the six-decimal objective from the attempt log.

## Recorded yield values are not pre-clamp raw chromatograms

The source logs have already passed through the historical evaluation script. For main-campaign component yield fractions from -0.05 inclusive to below zero, that script substitutes 0.0001 (0.01%). More negative values trigger failure; some component branches also replace their stored value with zero. Thus `recorded_*` preserves the supplied log values, not the unavailable pre-processing values. For example, a recorded zero can coexist with an error text describing a negative original calculated recovery. Negative values, values above 1, and all invalid-attempt values are retained exactly as supplied; the exporter applies no additional clamp.

Raw detector traces would be needed for independent reintegration and determination of pre-clamp values. No valid main mono yield in this supplied dataset equals the 0.0001 floor. Missing candidate-table objectives remain blank; they are never replaced by zero, and an invalid attempt is never treated as a valid zero-yield observation.

## Status and overlapping error flags

`status` is derived from the recorded error text: exactly `normal termination` after surrounding whitespace is removed gives `valid`; all other strings give `invalid`. The exporter does not retrospectively override the experiment's status by recomputing thresholds from rounded yield columns.

The original main CSV writer did not quote commas in its final `errors` field. A naive CSV reader may therefore retain only the first error. The exporter splits the first 16 commas and preserves the entire remaining error string, including its original trailing comma/spacing, as one properly quoted `source_error_text` field. This retains concurrent pressure, yield, and negative-standard-area flags.

`pressure_flag`, `yield_or_mass_balance_flag`, and `negative_STD_area_flag` contain 0 or 1 and are not mutually exclusive. The main data contain 6 attempts with pressure flags, 11 with yield/mass-balance flags, and 1 with a negative-STD-area flag. Three attempts have both pressure and yield/mass-balance flags. To obtain a disjoint failure summary, `failure_category` gives pressure priority:

- `none`: all 178 valid main attempts (68 preliminary).
- `pressure_present`: 6 main attempts, whether or not other flags coexist.
- `yield_or_mass_balance_only`: 8 main attempts (2 preliminary) with yield/mass-balance errors and no pressure flag.
- `other_flag`: reserved for other invalid source statuses; none occur here.

Therefore the 14 main failures are **6 pressure-flagged attempts plus 8 yield/mass-balance-only attempts**, not 6 pressure flags plus only 8 yield flags overall. Every invalid attempt remains in the CSV. The historical script retained failures in `results_log.csv` but excluded their objectives from `candidates.csv`, leaving those candidates eligible for reselection.

## Historical records and author-confirmed corrections

The original audit identified B5/B6 naming errors in manuscript tables, a B4 K2CO3 mass/mmol inconsistency, and a difference between the stated approximate internal-standard mass and `param.txt`. The revised manuscript maps B5 to KOH and B6 to K3PO4. On 26 September 2026, the authors confirmed that B4 was prepared using 55.6 mmol of K2CO3, matching the other base stocks; the SI mass entry is corrected to the corresponding 7.68 g. The authors also confirmed that the internal-standard target mass was 16.5 mg and the actual measured mass used for quantification was 16.605 mg, matching `STD_WT=16.605` in the original `param.txt`. This documentation clarification does not alter any archived yield. The canonical CSV values and original archive are not changed by these documentation corrections. This export does not independently establish physical reagent identity or weigh-log precision.

## Regeneration and validation

Run the supplied `export_canonical_data.py` using Python 3; it uses the standard library only:

```text
python export_canonical_data.py --source path/to/Suzuki-Miyaura-Automation-main_v20 --output path/to/canonical_data
```

The output directory must be outside the source archive. The script checks candidate/component mappings, complete 1500-condition coverage, main chronological order and within-cycle positions, 70/192 attempt counts, 68/178 valid counts, 2/14 invalid counts, failure categories, 13 shared and 233 distinct valid conditions, objective consistency, source-file hashes before/after, and round-trip preservation of every exported CSV value. `validation.json` records the results and exact hashes. No historical executable or model-training code is run.
