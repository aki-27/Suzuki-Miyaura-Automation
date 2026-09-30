"""Export traceable canonical CSVs without executing historical control software.

Standard library only. Source records are never modified. Values are copied as
strings; calculations below validate identifiers, counts and consistency only.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path


HERE = Path(__file__).resolve().parent
DEFAULT_SOURCE = HERE / "data/Suzuki-Miyaura-Automation-main_v20"
DEFAULT_OUTPUT = HERE.parent / "data"
CANDIDATE_MAP = {
    "expID": "candidateID",
    "ligand": "ligandID",
    "base": "baseID",
    "solvent": "solventID",
    "cone angle": "cone_angle",
    "TEP": "TEP",
    "calc P shift": "calculated_31P_shift",
    "pKa": "pKa",
    "Pauling ionic radii": "Pauling_cation_radius",
    "Hansen-dD": "Hansen_dD",
    "Hansen-dP": "Hansen_dP",
    "Hansen-dH": "Hansen_dH",
}
MAIN_MAP = {
    "time": "recorded_timestamp",
    "batch": "source_batch_position",
    "expID": "candidateID",
    "ligand": "ligandID",
    "base": "baseID",
    "solvent": "solventID",
    "notation": "recorded_notation",
    "p1 yield": "recorded_compound1_recovery_fraction",
    "p2 yield": "recorded_compound3_yield_fraction",
    "p3 yield": "recorded_compound4_yield_fraction",
    "total yield": "recorded_total_yield_fraction",
    "objective": "recorded_log_objective",
    "std area": "recorded_STD_area",
    "p1 area": "recorded_compound1_area",
    "p2 area": "recorded_compound3_area",
    "p3 area": "recorded_compound4_area",
    "errors": "source_error_text",
}
PRE_COLUMNS = ["exp_no", "expID", "ligand", "base", "solvent", "compound1_recovery", "compound3_yield", "compound4_yield", "total_yield", "error_detection"]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, skipinitialspace=True)
        rows = list(reader)
    require(all(None not in row for row in rows), f"Unexpected extra CSV fields: {path}")
    return reader.fieldnames, rows


def read_main_log(path):
    # The historical writer did not quote commas inside the final error field.
    # Split only its first 16 commas so ALL error text, not only the first flag,
    # survives. None of the first 16 fields contain quoted commas/newlines.
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    headers = [field.strip() for field in lines[0].split(",")]
    require(headers == list(MAIN_MAP), "Unexpected main-log schema")
    rows = []
    for line_no, line in enumerate(lines[1:], 2):
        if not line:
            continue
        fields = line.split(",", 16)
        require(len(fields) == 17, f"Malformed main-log line {line_no}")
        values = [value.strip() for value in fields[:16]] + [fields[16]]
        rows.append(dict(zip(headers, values)))
    return rows


def status_fields(error_text):
    valid = error_text.strip() == "normal termination"
    pressure = "pressure:" in error_text
    yield_flag = "yield" in error_text and not valid
    area_flag = "negative area of STD" in error_text
    category = ("none" if valid else "pressure_present" if pressure else
                "yield_or_mass_balance_only" if yield_flag else "other_flag")
    return {
        "status": "valid" if valid else "invalid",
        "failure_category": category,
        "pressure_flag": str(int(pressure)),
        "yield_or_mass_balance_flag": str(int(yield_flag)),
        "negative_STD_area_flag": str(int(area_flag)),
    }


def write_csv(path, rows):
    require(bool(rows), f"No records for {path}")
    fields = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    _, reread = read_csv(path)
    require(reread == rows, f"CSV round-trip changed values: {path}")


def run(source, output):
    source = source.resolve()
    output = output.resolve()
    require(source != output and source not in output.parents, "Output must not be inside the source archive")
    candidate_path = source / "candidates.csv"
    analysis_candidate_path = source / "analysis_scripts/shap/2024_0712_0146_candidates.csv"
    prelim_path = source / "analysis_scripts/comparison_models/preliminary_campaign_results.csv"
    main_path = source / "results_log.csv"
    source_paths = [candidate_path, analysis_candidate_path, prelim_path, main_path]
    input_hashes = {str(path.relative_to(source)): sha256(path) for path in source_paths}
    header, original_candidates = read_csv(candidate_path)
    require(header == list(CANDIDATE_MAP) + ["objectives"], "Unexpected candidate schema")
    require(len(original_candidates) == 1500, "Candidate count must be 1500")
    require(sha256(candidate_path) == sha256(analysis_candidate_path), "Candidate source differs from the analysis snapshot")
    candidates = [{target: row[original] for original, target in CANDIDATE_MAP.items()} for row in original_candidates]
    lookup = {row["candidateID"]: row for row in candidates}
    objective_lookup = {row["expID"]: row["objectives"] for row in original_candidates}
    require(len(lookup) == 1500, "Duplicate candidate IDs")
    require([int(row["candidateID"]) for row in candidates] == list(range(1, 1501)), "Candidate IDs must be 1...1500")
    for row in candidates:
        cid, ligand, base, solvent = [int(row[key]) for key in ["candidateID", "ligandID", "baseID", "solventID"]]
        require(1 <= ligand <= 15 and 1 <= base <= 10 and 1 <= solvent <= 10, "Component ID out of range")
        require(cid == ligand + 15 * (base - 1) + 150 * (solvent - 1), "Candidate ID/index formula mismatch")
        require(all(math.isfinite(float(value)) for value in row.values()), "Non-finite candidate feature")
    require(len({(r["ligandID"], r["baseID"], r["solventID"]) for r in candidates}) == 1500, "Duplicate component combination")

    header, original_prelim = read_csv(prelim_path)
    require(header == PRE_COLUMNS, "Unexpected preliminary schema")
    require(len(original_prelim) == 70, "Preliminary count must be 70")
    prelim = []
    for index, row in enumerate(original_prelim, 1):
        require(int(row["exp_no"]) == index, "Preliminary experiment numbering not chronological 1...70")
        candidate = lookup[row["expID"]]
        require(all(row[key] == candidate[key + "ID"] for key in ["ligand", "base", "solvent"]), "Preliminary component/candidate mismatch")
        # All ten source columns are retained unchanged after derived identifiers.
        prelim.append({"attempt": str(index), "candidateID": row["expID"], **status_fields(row["error_detection"]), **row})

    original_main = read_main_log(main_path)
    require(len(original_main) == 192, "Main count must be 192")
    main = []
    timestamps = []
    for index, row in enumerate(original_main, 1):
        position = (index - 1) % 4 + 1
        cycle = (index - 1) // 4 + 1
        require(int(row["batch"]) == position, "Source batch field does not match within-cycle position")
        candidate = lookup[row["expID"]]
        require(all(row[key] == candidate[key + "ID"] for key in ["ligand", "base", "solvent"]), "Main component/candidate mismatch")
        timestamps.append(datetime.fromisoformat(row["time"]))
        derived_status = status_fields(row["errors"])
        valid = derived_status["status"] == "valid"
        training_objective = objective_lookup[row["expID"]] if valid else ""
        if valid:
            require(training_objective != "", "Valid attempt has no candidate-table objective")
            require(abs(float(training_objective) - float(row["objective"])) <= 5.01e-7, "Candidate-table and recorded objectives disagree beyond log rounding")
        main.append({
            "attempt": str(index), "cycle": str(cycle), "position": str(position),
            "phase": "initialization" if cycle == 1 else "closed_loop",
            **{target: row[original] for original, target in MAIN_MAP.items()},
            **derived_status,
            "candidate_table_log_objective": training_objective,
        })
    require(timestamps == sorted(timestamps), "Main timestamps are not chronological")
    main_valid = [row for row in main if row["status"] == "valid"]
    pre_valid = [row for row in prelim if row["status"] == "valid"]
    main_ids = {row["candidateID"] for row in main_valid}
    pre_ids = {row["candidateID"] for row in pre_valid}
    require((len(pre_valid), len(main_valid)) == (68, 178), "Valid counts differ from 68/178")
    require((len(pre_ids), len(main_ids)) == (68, 178), "Unexpected valid within-campaign repeat")
    require(len(pre_ids & main_ids) == 13, "Expected 13 shared valid conditions")
    require(len(pre_ids | main_ids) == 233, "Expected 233 distinct valid conditions")
    require(sum(bool(value) for value in objective_lookup.values()) == 178, "Expected 178 candidate objectives")
    categories = Counter(row["failure_category"] for row in main)
    require(categories == Counter({"none": 178, "pressure_present": 6, "yield_or_mass_balance_only": 8}), "Unexpected main failure counts")
    require(all(sha256(path) == input_hashes[str(path.relative_to(source))] for path in source_paths), "Source archive changed during export")
    output.mkdir(parents=True, exist_ok=True)
    for filename, rows in [("candidate_space.csv", candidates), ("preliminary_attempts.csv", prelim), ("main_attempts.csv", main)]:
        write_csv(output / filename, rows)
    validation = {
        "exporter": Path(__file__).name,
        "source_archive_directory": "Suzuki-Miyaura-Automation-main_v20",
        "source_sha256": input_hashes,
        "candidate_count": len(candidates),
        "candidate_feature_count": len(CANDIDATE_MAP),
        "candidate_objective_excluded": all("objective" not in key.lower() for key in candidates[0]),
        "main_attempts": len(main), "main_valid": len(main_valid), "main_invalid": len(main) - len(main_valid),
        "main_distinct_attempted_candidates": len({row["candidateID"] for row in main}),
        "main_distinct_valid_candidates": len(main_ids),
        "main_failure_categories": dict(categories),
        "main_pressure_flag_count": sum(int(row["pressure_flag"]) for row in main),
        "main_yield_or_mass_balance_flag_count": sum(int(row["yield_or_mass_balance_flag"]) for row in main),
        "main_negative_STD_area_flag_count": sum(int(row["negative_STD_area_flag"]) for row in main),
        "main_both_pressure_and_yield_flags": sum(int(row["pressure_flag"]) * int(row["yield_or_mass_balance_flag"]) for row in main),
        "preliminary_attempts": len(prelim), "preliminary_valid": len(pre_valid), "preliminary_invalid": len(prelim) - len(pre_valid),
        "shared_valid_conditions": len(pre_ids & main_ids), "distinct_valid_conditions_combined": len(pre_ids | main_ids),
        "valid_records_combined": len(pre_valid) + len(main_valid),
        "candidate_source_identical_to_analysis_snapshot": True,
        "main_log_objectives_match_candidate_objectives_within_rounding": True,
        "main_initial_candidateIDs": [row["candidateID"] for row in main[:4]],
        "main_first_recorded_timestamp": main[0]["recorded_timestamp"],
        "main_last_recorded_timestamp": main[-1]["recorded_timestamp"],
        "source_archive_unchanged": True,
        "csv_round_trip_passed": True,
        "output_sha256": {name: sha256(output / name) for name in ["candidate_space.csv", "preliminary_attempts.csv", "main_attempts.csv"]},
        "candidate_column_mapping": CANDIDATE_MAP,
        "main_column_mapping": MAIN_MAP,
        "preliminary_original_columns_retained": PRE_COLUMNS,
    }
    (output / "validation.json").write_text(json.dumps(validation, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in validation.items() if key not in {"source_sha256", "output_sha256", "candidate_column_mapping", "main_column_mapping", "preliminary_original_columns_retained"}}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    run(args.source, args.output)
