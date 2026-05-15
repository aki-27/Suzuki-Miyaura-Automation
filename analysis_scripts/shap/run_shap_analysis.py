#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Standalone SHAP analysis for the Suzuki-Miyaura autonomous optimization data.

This script replaces the order-dependent notebook
    analysis_scripts/shap/shap-formation.ipynb

Default execution from the repository is:

    cd analysis_scripts/shap
    python run_shap_analysis.py

The script reads 2024_0712_0146_candidates.csv, performs the same five-fold
split that was used in the notebook, trains a Gaussian-process regression model
for each fold, calculates SHAP values for the test fold, and writes numerical
tables and figures to the output directory.

The default backend is "auto". PHYSBO is used when it is available, since this
matches the model used in the original optimization workflow. If PHYSBO is not
installed, the script falls back to scikit-learn GaussianProcessRegressor so
that the script remains executable in a clean Python environment with the common
scientific Python stack.

For manuscript-level reproduction of the PHYSBO analysis, install PHYSBO and run:

    python run_shap_analysis.py --backend physbo
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import matplotlib

# The Agg backend allows execution on headless servers.
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, RBF, WhiteKernel
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.preprocessing import StandardScaler


DEFAULT_DESCRIPTOR_COLUMNS = [
    "cone angle",
    "TEP",
    "calc P shift",
    "pKa",
    "Pauling ionic radii",
    "Hansen-dD",
    "Hansen-dP",
    "Hansen-dH",
]

DEFAULT_FEATURE_NAMES = [
    "Angle",
    "TEP",
    "NMR",
    "pKa",
    "ion-R",
    "delta_D",
    "delta_p",
    "delta_H",
]

# Matplotlib/SHAP display labels. These labels are used only in figures.
# The plain DEFAULT_FEATURE_NAMES values are retained for CSV columns and
# machine-readable outputs.
DEFAULT_FEATURE_LABELS = [
    "Angle",
    "TEP",
    "NMR",
    r"p$\mathit{K}_{a}$",
    "ion-R",
    r"$\mathit{\delta}_{d}$",
    r"$\mathit{\delta}_{p}$",
    r"$\mathit{\delta}_{h}$",
]

DEFAULT_OBJECTIVE_COLUMN = "objectives"

# These sample indices are retained from the original notebook.
DEFAULT_WATERFALL_INDICES = [0, 32, 59, 90, 31, 33, 30, 55, 71, 73, 146]

CM_PER_INCH = 2.54
DEFAULT_SHAP_FIG_WIDTH_CM = 7.3
DEFAULT_SHAP_FIG_HEIGHT_CM = 6.0
DEFAULT_SHAP_FONT_SIZE_PT = 8.0



@dataclass
class FoldModelResult:
    fold: int
    train_indices: np.ndarray
    test_indices: np.ndarray
    y_train: np.ndarray
    y_test: np.ndarray
    y_train_pred: np.ndarray
    y_test_pred: np.ndarray
    shap_values: np.ndarray
    base_value: float
    pfi_mse: Optional[np.ndarray]
    pfi_mae: Optional[np.ndarray]


class PhysboGPRegressor:
    """Small prediction wrapper around PHYSBO's Gaussian-process model."""

    def __init__(self) -> None:
        try:
            import physbo  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "PHYSBO is not installed. Install it or run with --backend sklearn."
            ) from exc
        self.physbo = physbo
        self.gp = None
        self.x_train = None
        self.y_train = None

    def fit(self, x_train: np.ndarray, y_train: np.ndarray) -> "PhysboGPRegressor":
        cov = self.physbo.gp.cov.gauss(x_train.shape[1], ard=False)
        mean = self.physbo.gp.mean.const()
        lik = self.physbo.gp.lik.gauss()
        gp = self.physbo.gp.model(lik=lik, mean=mean, cov=cov)
        config = self.physbo.misc.set_config()
        gp.fit(x_train, y_train, config)
        gp.prepare(x_train, y_train)
        self.gp = gp
        self.x_train = x_train
        self.y_train = y_train
        return self

    def predict(self, x: np.ndarray) -> np.ndarray:
        if self.gp is None or self.x_train is None:
            raise RuntimeError("The PHYSBO GP model has not been fitted.")
        return np.asarray(self.gp.get_post_fmean(self.x_train, x), dtype=float)


class SklearnGPRegressor:
    """Fallback Gaussian-process model with a scikit-learn implementation."""

    def __init__(self, random_seed: int = 123456) -> None:
        kernel = (
            ConstantKernel(1.0, constant_value_bounds=(1.0e-3, 1.0e3))
            * RBF(length_scale=1.0, length_scale_bounds=(1.0e-2, 1.0e3))
            + WhiteKernel(noise_level=1.0e-3, noise_level_bounds=(1.0e-8, 1.0e1))
        )
        self.model = GaussianProcessRegressor(
            kernel=kernel,
            normalize_y=True,
            n_restarts_optimizer=5,
            random_state=random_seed,
        )

    def fit(self, x_train: np.ndarray, y_train: np.ndarray) -> "SklearnGPRegressor":
        self.model.fit(x_train, y_train)
        return self

    def predict(self, x: np.ndarray) -> np.ndarray:
        return np.asarray(self.model.predict(x), dtype=float)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run five-fold Gaussian-process SHAP analysis for the "
            "Suzuki-Miyaura autonomous optimization dataset."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("2024_0712_0146_candidates.csv"),
        help="Input candidates CSV. Default: 2024_0712_0146_candidates.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("shap_results"),
        help="Directory for output tables and figures. Default: shap_results",
    )
    parser.add_argument(
        "--backend",
        choices=["auto", "physbo", "sklearn"],
        default="auto",
        help=(
            "Model backend. 'auto' uses PHYSBO when available and falls back to "
            "scikit-learn otherwise. Default: auto"
        ),
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=123456,
        help="Random seed used for fold splitting, shuffling, and model initialization.",
    )
    parser.add_argument(
        "--folds",
        type=int,
        default=5,
        help="Number of cross-validation folds. Default: 5",
    )
    parser.add_argument(
        "--descriptor-columns",
        type=str,
        default=",".join(DEFAULT_DESCRIPTOR_COLUMNS),
        help=(
            "Comma-separated descriptor columns. Default: "
            + ",".join(DEFAULT_DESCRIPTOR_COLUMNS)
        ),
    )
    parser.add_argument(
        "--feature-names",
        type=str,
        default=",".join(DEFAULT_FEATURE_NAMES),
        help=(
            "Comma-separated machine-readable names for descriptors. These names "
            "are used for CSV columns and summaries. Default: "
            + ",".join(DEFAULT_FEATURE_NAMES)
        ),
    )
    parser.add_argument(
        "--feature-labels",
        type=str,
        default=",".join(DEFAULT_FEATURE_LABELS),
        help=(
            "Comma-separated Matplotlib mathtext labels for descriptor names in figures. "
            "Default: " + ",".join(DEFAULT_FEATURE_LABELS)
        ),
    )
    parser.add_argument(
        "--objective-column",
        type=str,
        default=DEFAULT_OBJECTIVE_COLUMN,
        help="Objective column name. Default: objectives",
    )
    parser.add_argument(
        "--shap-nsamples",
        default="auto",
        help=(
            "nsamples argument passed to shap.KernelExplainer.shap_values. "
            "Use 'auto' or an integer such as 256. Default: auto"
        ),
    )
    parser.add_argument(
        "--background",
        choices=["test", "train", "all"],
        default="test",
        help=(
            "Background data for KernelExplainer. The original notebook used "
            "the test fold. Default: test"
        ),
    )
    parser.add_argument(
        "--pfi-runs",
        type=int,
        default=1000,
        help=(
            "Number of shuffling runs per feature for the prediction-sensitivity "
            "PFI calculation. Default: 1000"
        ),
    )
    parser.add_argument(
        "--no-pfi",
        action="store_true",
        help="Skip the PFI calculation.",
    )
    parser.add_argument(
        "--waterfall-indices",
        type=str,
        default=",".join(str(x) for x in DEFAULT_WATERFALL_INDICES),
        help=(
            "Comma-separated sample indices for SHAP waterfall plots. "
            "Use an empty string to skip these plots."
        ),
    )
    parser.add_argument(
        "--top-waterfall",
        type=int,
        default=5,
        help=(
            "Number of additional waterfall plots for samples with the highest "
            "observed objective values. Default: 5"
        ),
    )
    parser.add_argument(
        "--shap-fig-width-cm",
        type=float,
        default=DEFAULT_SHAP_FIG_WIDTH_CM,
        help="Width of SHAP figures in centimetres. Default: 7.3",
    )
    parser.add_argument(
        "--shap-fig-height-cm",
        type=float,
        default=DEFAULT_SHAP_FIG_HEIGHT_CM,
        help="Height of SHAP figures in centimetres. Default: 6.0",
    )
    parser.add_argument(
        "--shap-font-size",
        type=float,
        default=DEFAULT_SHAP_FONT_SIZE_PT,
        help="Font size for SHAP figures in points. Default: 8",
    )
    parser.add_argument(
        "--no-plots",
        action="store_true",
        help="Write numerical outputs only.",
    )
    parser.add_argument(
        "--strict-metadata",
        action="store_true",
        help=(
            "Fail if expected metadata columns are absent. Without this option, "
            "metadata columns are included only when present."
        ),
    )
    return parser.parse_args()


def set_reproducible_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)


def split_comma_argument(value: str) -> List[str]:
    return [x.strip() for x in value.split(",") if x.strip()]


def parse_integer_list(value: str) -> List[int]:
    if not value.strip():
        return []
    return [int(x.strip()) for x in value.split(",") if x.strip()]


def resolve_backend(requested_backend: str) -> str:
    if requested_backend == "sklearn":
        return "sklearn"
    if requested_backend == "physbo":
        try:
            import physbo  # noqa: F401  # type: ignore
        except ImportError as exc:
            raise SystemExit(
                "ERROR: --backend physbo was requested, but PHYSBO is not installed. "
                "Install PHYSBO or use --backend sklearn."
            ) from exc
        return "physbo"

    try:
        import physbo  # noqa: F401  # type: ignore
        return "physbo"
    except ImportError:
        warnings.warn(
            "PHYSBO was not found. The script will use scikit-learn "
            "GaussianProcessRegressor as a fallback. Use --backend physbo after "
            "installing PHYSBO for manuscript-level reproduction.",
            RuntimeWarning,
        )
        return "sklearn"


def load_dataset(
    input_csv: Path,
    descriptor_columns: Sequence[str],
    objective_column: str,
    strict_metadata: bool = False,
) -> Tuple[pd.DataFrame, pd.DataFrame, np.ndarray, np.ndarray]:
    if not input_csv.exists():
        raise FileNotFoundError(f"Input CSV was not found: {input_csv}")

    df = pd.read_csv(input_csv)

    required_columns = list(descriptor_columns) + [objective_column]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(
            "The input CSV lacks required columns: " + ", ".join(missing_columns)
        )

    metadata_candidates = ["expID", "ligand", "base", "solvent"]
    if strict_metadata:
        missing_meta = [col for col in metadata_candidates if col not in df.columns]
        if missing_meta:
            raise ValueError(
                "The input CSV lacks expected metadata columns: "
                + ", ".join(missing_meta)
            )
    metadata_columns = [col for col in metadata_candidates if col in df.columns]

    analysis_df = df[metadata_columns + required_columns].copy()
    analysis_df = analysis_df.dropna(subset=required_columns).reset_index(drop=False)
    analysis_df = analysis_df.rename(columns={"index": "source_row_index"})

    x = analysis_df[list(descriptor_columns)].to_numpy(dtype=float)
    y = analysis_df[objective_column].to_numpy(dtype=float)

    if len(analysis_df) == 0:
        raise ValueError("No complete rows were available after dropna().")

    return df, analysis_df, x, y


def center_descriptors(x: np.ndarray, backend: str) -> Tuple[np.ndarray, Dict[str, object]]:
    # The original notebook centered all complete rows before cross-validation.
    # The same behavior is retained for reproducibility.
    if backend == "physbo":
        import physbo  # type: ignore

        x_centered = np.asarray(physbo.misc.centering(x), dtype=float)
        centering_info = {
            "method": "physbo.misc.centering",
            "note": "All complete rows were centered before fold splitting, as in the notebook.",
        }
    else:
        scaler = StandardScaler()
        x_centered = scaler.fit_transform(x)
        centering_info = {
            "method": "sklearn.preprocessing.StandardScaler",
            "mean": scaler.mean_.tolist(),
            "scale": scaler.scale_.tolist(),
            "note": "All complete rows were centered before fold splitting, as in the notebook.",
        }
    return x_centered, centering_info


def k_fold_split(
    n_samples: int,
    k: int,
    shuffle: bool = True,
    random_seed: Optional[int] = None,
) -> List[Tuple[np.ndarray, np.ndarray]]:
    if k < 2:
        raise ValueError("The number of folds must be at least 2.")
    if k > n_samples:
        raise ValueError("The number of folds cannot exceed the number of samples.")

    indices = np.arange(n_samples)
    rng = np.random.default_rng(random_seed)
    if shuffle:
        rng.shuffle(indices)

    fold_sizes = np.full(k, n_samples // k, dtype=int)
    fold_sizes[: n_samples % k] += 1

    folds: List[Tuple[np.ndarray, np.ndarray]] = []
    current = 0
    for fold_size in fold_sizes:
        start = current
        stop = current + fold_size
        test_indices = indices[start:stop]
        train_indices = np.concatenate([indices[:start], indices[stop:]])
        folds.append((train_indices, test_indices))
        current = stop

    return folds


def make_model(backend: str, seed: int):
    if backend == "physbo":
        return PhysboGPRegressor()
    if backend == "sklearn":
        return SklearnGPRegressor(random_seed=seed)
    raise ValueError(f"Unsupported backend: {backend}")


def safe_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    try:
        return float(r2_score(y_true, y_pred))
    except Exception:
        return float("nan")


def calculate_prediction_sensitivity_pfi(
    predict_fn: Callable[[np.ndarray], np.ndarray],
    x_test: np.ndarray,
    nrun: int,
    rng: np.random.Generator,
) -> Tuple[np.ndarray, np.ndarray]:
    """Reproduce the notebook-style PFI calculation.

    This calculation measures the change in model predictions after shuffling
    each descriptor. It does not measure the drop in predictive score against
    experimental values. The output is therefore labelled as
    prediction-sensitivity PFI.
    """

    y_pred = predict_fn(x_test)
    mse_values = []
    mae_values = []

    for feature_idx in range(x_test.shape[1]):
        shuffled_predictions = []
        for _ in range(nrun):
            x_shuffle = np.array(x_test, copy=True)
            shuffled_column = np.array(x_shuffle[:, feature_idx], copy=True)
            rng.shuffle(shuffled_column)
            x_shuffle[:, feature_idx] = shuffled_column
            shuffled_predictions.append(predict_fn(x_shuffle))

        mean_shuffled_prediction = np.mean(np.vstack(shuffled_predictions), axis=0)
        mse_values.append(mean_squared_error(y_pred, mean_shuffled_prediction))
        mae_values.append(mean_absolute_error(y_pred, mean_shuffled_prediction))

    return np.asarray(mse_values, dtype=float), np.asarray(mae_values, dtype=float)


def get_background_data(
    mode: str,
    x_train: np.ndarray,
    x_test: np.ndarray,
    x_all: np.ndarray,
) -> np.ndarray:
    if mode == "test":
        return x_test
    if mode == "train":
        return x_train
    if mode == "all":
        return x_all
    raise ValueError(f"Unsupported background mode: {mode}")


def calculate_shap_values(
    predict_fn: Callable[[np.ndarray], np.ndarray],
    background_data: np.ndarray,
    x_test: np.ndarray,
    nsamples: str | int,
) -> Tuple[np.ndarray, float]:
    explainer = shap.KernelExplainer(predict_fn, background_data)
    shap_values = explainer.shap_values(x_test, nsamples=nsamples)
    shap_values_array = np.asarray(shap_values, dtype=float)

    expected_value = explainer.expected_value
    if isinstance(expected_value, (list, tuple, np.ndarray)):
        base_value = float(np.ravel(expected_value)[0])
    else:
        base_value = float(expected_value)

    return shap_values_array, base_value


def run_fold_analysis(
    fold: int,
    train_indices: np.ndarray,
    test_indices: np.ndarray,
    x: np.ndarray,
    y: np.ndarray,
    x_all: np.ndarray,
    backend: str,
    seed: int,
    background_mode: str,
    shap_nsamples: str | int,
    pfi_runs: int,
    do_pfi: bool,
) -> FoldModelResult:
    x_train = x[train_indices]
    y_train = y[train_indices]
    x_test = x[test_indices]
    y_test = y[test_indices]

    model = make_model(backend, seed + fold)
    model.fit(x_train, y_train)

    y_train_pred = model.predict(x_train)
    y_test_pred = model.predict(x_test)

    background_data = get_background_data(background_mode, x_train, x_test, x_all)
    shap_values_array, base_value = calculate_shap_values(
        model.predict,
        background_data,
        x_test,
        shap_nsamples,
    )

    pfi_mse = None
    pfi_mae = None
    if do_pfi:
        rng = np.random.default_rng(seed + 1000 + fold)
        pfi_mse, pfi_mae = calculate_prediction_sensitivity_pfi(
            model.predict,
            x_test,
            pfi_runs,
            rng,
        )

    print(
        f"Fold {fold}: "
        f"R2_train={safe_r2(y_train, y_train_pred):.4f}, "
        f"R2_test={safe_r2(y_test, y_test_pred):.4f}, "
        f"n_train={len(train_indices)}, n_test={len(test_indices)}"
    )

    return FoldModelResult(
        fold=fold,
        train_indices=train_indices,
        test_indices=test_indices,
        y_train=y_train,
        y_test=y_test,
        y_train_pred=y_train_pred,
        y_test_pred=y_test_pred,
        shap_values=shap_values_array,
        base_value=base_value,
        pfi_mse=pfi_mse,
        pfi_mae=pfi_mae,
    )


def build_prediction_table(
    analysis_df: pd.DataFrame,
    results: Sequence[FoldModelResult],
    descriptor_columns: Sequence[str],
    feature_names: Sequence[str],
    objective_column: str,
) -> pd.DataFrame:
    rows: List[pd.DataFrame] = []

    for result in results:
        fold_df = analysis_df.iloc[result.test_indices].copy()
        fold_df["fold"] = result.fold
        fold_df["y_observed"] = result.y_test
        fold_df["y_predicted"] = result.y_test_pred
        fold_df["prediction_error"] = result.y_test_pred - result.y_test
        fold_df["shap_base_value"] = result.base_value
        for j, feature_name in enumerate(feature_names):
            fold_df[f"SHAP_{feature_name}"] = result.shap_values[:, j]
        rows.append(fold_df)

    output = pd.concat(rows, axis=0).sort_index()
    ordered_columns = (
        [
            col
            for col in [
                "source_row_index",
                "expID",
                "ligand",
                "base",
                "solvent",
                "fold",
                objective_column,
                "y_observed",
                "y_predicted",
                "prediction_error",
                "shap_base_value",
            ]
            if col in output.columns
        ]
        + list(descriptor_columns)
        + [f"SHAP_{name}" for name in feature_names]
    )
    return output[ordered_columns]


def build_training_prediction_table(
    analysis_df: pd.DataFrame,
    results: Sequence[FoldModelResult],
    objective_column: str,
) -> pd.DataFrame:
    rows: List[pd.DataFrame] = []
    for result in results:
        fold_df = analysis_df.iloc[result.train_indices].copy()
        fold_df["fold"] = result.fold
        fold_df["y_observed"] = result.y_train
        fold_df["y_predicted"] = result.y_train_pred
        fold_df["prediction_error"] = result.y_train_pred - result.y_train
        rows.append(fold_df)

    output = pd.concat(rows, axis=0).reset_index(drop=True)
    ordered_columns = [
        col
        for col in [
            "source_row_index",
            "expID",
            "ligand",
            "base",
            "solvent",
            "fold",
            objective_column,
            "y_observed",
            "y_predicted",
            "prediction_error",
        ]
        if col in output.columns
    ]
    return output[ordered_columns]


def build_metrics_table(results: Sequence[FoldModelResult]) -> pd.DataFrame:
    rows = []
    for result in results:
        rows.append(
            {
                "fold": result.fold,
                "n_train": len(result.train_indices),
                "n_test": len(result.test_indices),
                "r2_train": safe_r2(result.y_train, result.y_train_pred),
                "r2_test": safe_r2(result.y_test, result.y_test_pred),
                "r2_train_reversed_notebook": safe_r2(result.y_train_pred, result.y_train),
                "r2_test_reversed_notebook": safe_r2(result.y_test_pred, result.y_test),
                "rmse_train": float(np.sqrt(mean_squared_error(result.y_train, result.y_train_pred))),
                "rmse_test": float(np.sqrt(mean_squared_error(result.y_test, result.y_test_pred))),
                "mae_train": float(mean_absolute_error(result.y_train, result.y_train_pred)),
                "mae_test": float(mean_absolute_error(result.y_test, result.y_test_pred)),
            }
        )
    return pd.DataFrame(rows)


def build_shap_summary(
    prediction_df: pd.DataFrame,
    feature_names: Sequence[str],
) -> pd.DataFrame:
    rows = []
    for feature_name in feature_names:
        values = prediction_df[f"SHAP_{feature_name}"].to_numpy(dtype=float)
        rows.append(
            {
                "feature": feature_name,
                "sum_abs_shap": float(np.sum(np.abs(values))),
                "mean_abs_shap": float(np.mean(np.abs(values))),
                "mean_signed_shap": float(np.mean(values)),
                "std_signed_shap": float(np.std(values, ddof=1)),
            }
        )
    summary = pd.DataFrame(rows)
    total = summary["sum_abs_shap"].sum()
    if total > 0:
        summary["fraction_abs_shap"] = summary["sum_abs_shap"] / total
    else:
        summary["fraction_abs_shap"] = np.nan
    return summary.sort_values("sum_abs_shap", ascending=False)


def build_pfi_tables(
    results: Sequence[FoldModelResult],
    feature_names: Sequence[str],
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    raw_rows = []
    for result in results:
        if result.pfi_mse is None or result.pfi_mae is None:
            continue
        for j, feature_name in enumerate(feature_names):
            raw_rows.append(
                {
                    "fold": result.fold,
                    "feature": feature_name,
                    "prediction_sensitivity_pfi_mse": float(result.pfi_mse[j]),
                    "prediction_sensitivity_pfi_mae": float(result.pfi_mae[j]),
                }
            )

    raw_df = pd.DataFrame(raw_rows)
    if raw_df.empty:
        return raw_df, raw_df

    summary_df = (
        raw_df.groupby("feature", as_index=False)
        .agg(
            mean_prediction_sensitivity_pfi_mse=(
                "prediction_sensitivity_pfi_mse",
                "mean",
            ),
            sd_prediction_sensitivity_pfi_mse=(
                "prediction_sensitivity_pfi_mse",
                "std",
            ),
            mean_prediction_sensitivity_pfi_mae=(
                "prediction_sensitivity_pfi_mae",
                "mean",
            ),
            sd_prediction_sensitivity_pfi_mae=(
                "prediction_sensitivity_pfi_mae",
                "std",
            ),
        )
        .sort_values("mean_prediction_sensitivity_pfi_mse", ascending=False)
    )
    return raw_df, summary_df


def cm_to_inches(width_cm: float, height_cm: float) -> Tuple[float, float]:
    return width_cm / CM_PER_INCH, height_cm / CM_PER_INCH


def apply_shap_figure_format(
    width_cm: float,
    height_cm: float,
    font_size_pt: float,
) -> None:
    """Apply manuscript-oriented size and typography to the active SHAP figure."""

    fig = plt.gcf()
    fig.set_size_inches(*cm_to_inches(width_cm, height_cm), forward=True)

    for ax in fig.axes:
        ax.title.set_fontsize(font_size_pt)
        ax.xaxis.label.set_fontsize(font_size_pt)
        ax.yaxis.label.set_fontsize(font_size_pt)
        ax.tick_params(axis="both", which="major", labelsize=font_size_pt)
        ax.tick_params(axis="both", which="minor", labelsize=font_size_pt)
        legend = ax.get_legend()
        if legend is not None:
            for text in legend.get_texts():
                text.set_fontsize(font_size_pt)
            legend.get_title().set_fontsize(font_size_pt)
        for text in ax.texts:
            text.set_fontsize(font_size_pt)

    for text in fig.texts:
        text.set_fontsize(font_size_pt)


def save_prediction_plot(
    test_prediction_df: pd.DataFrame,
    train_prediction_df: pd.DataFrame,
    output_path: Path,
) -> None:
    plt.figure(figsize=(3.2, 3.2), dpi=300)
    plt.scatter(
        train_prediction_df["y_observed"],
        train_prediction_df["y_predicted"],
        s=12,
        alpha=0.7,
        label="training",
    )
    plt.scatter(
        test_prediction_df["y_observed"],
        test_prediction_df["y_predicted"],
        s=16,
        alpha=0.8,
        label="test",
    )
    values = np.concatenate(
        [
            train_prediction_df["y_observed"].to_numpy(),
            train_prediction_df["y_predicted"].to_numpy(),
            test_prediction_df["y_observed"].to_numpy(),
            test_prediction_df["y_predicted"].to_numpy(),
        ]
    )
    min_value = float(np.nanmin(values))
    max_value = float(np.nanmax(values))
    plt.plot([min_value, max_value], [min_value, max_value], linewidth=1)
    plt.xlabel("Observed objective")
    plt.ylabel("Predicted objective")
    plt.legend(frameon=False)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def save_shap_abs_bar(
    shap_summary_df: pd.DataFrame,
    feature_label_map: Dict[str, str],
    output_path: Path,
    width_cm: float,
    height_cm: float,
    font_size_pt: float,
) -> None:
    ordered = shap_summary_df.sort_values("sum_abs_shap", ascending=False).copy()
    ordered["feature_label"] = ordered["feature"].map(feature_label_map).fillna(ordered["feature"])
    plt.figure(figsize=cm_to_inches(width_cm, height_cm), dpi=300)
    bars = plt.bar(ordered["feature_label"], ordered["sum_abs_shap"])
    plt.ylabel("Sum of absolute SHAP values", fontsize=font_size_pt)
    plt.xlabel("Descriptor", fontsize=font_size_pt)
    plt.xticks(rotation=45, ha="right", fontsize=font_size_pt)
    plt.yticks(fontsize=font_size_pt)
    for bar in bars:
        height = bar.get_height()
        plt.annotate(
            f"{height:.1f}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 2),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=font_size_pt,
        )
    apply_shap_figure_format(width_cm, height_cm, font_size_pt)
    plt.tight_layout(pad=0.3)
    plt.savefig(output_path, dpi=300)
    plt.close()


def get_ordered_shap_and_x(
    prediction_df: pd.DataFrame,
    x_centered: np.ndarray,
    feature_names: Sequence[str],
) -> Tuple[np.ndarray, np.ndarray]:
    source_indices = prediction_df.index.to_numpy(dtype=int)
    shap_matrix = prediction_df[[f"SHAP_{name}" for name in feature_names]].to_numpy(dtype=float)
    x_matrix = x_centered[source_indices]
    return shap_matrix, x_matrix


def save_shap_summary_plots(
    prediction_df: pd.DataFrame,
    x_centered: np.ndarray,
    feature_names: Sequence[str],
    feature_labels: Sequence[str],
    output_dir: Path,
    width_cm: float,
    height_cm: float,
    font_size_pt: float,
) -> None:
    shap_matrix, x_matrix = get_ordered_shap_and_x(prediction_df, x_centered, feature_names)

    shap.summary_plot(
        shap_matrix,
        x_matrix,
        feature_names=list(feature_labels),
        sort=False,
        show=False,
        plot_size=cm_to_inches(width_cm, height_cm),
    )
    apply_shap_figure_format(width_cm, height_cm, font_size_pt)
    plt.tight_layout(pad=0.3)
    plt.savefig(output_dir / "shap_summary_dots.png", dpi=300)
    plt.close()

    shap.summary_plot(
        shap_matrix,
        x_matrix,
        plot_type="violin",
        feature_names=list(feature_labels),
        sort=False,
        show=False,
        plot_size=cm_to_inches(width_cm, height_cm),
    )
    apply_shap_figure_format(width_cm, height_cm, font_size_pt)
    plt.tight_layout(pad=0.3)
    plt.savefig(output_dir / "shap_summary_violin.png", dpi=300)
    plt.close()


def save_waterfall_plots(
    prediction_df: pd.DataFrame,
    x_centered: np.ndarray,
    feature_names: Sequence[str],
    feature_labels: Sequence[str],
    requested_indices: Sequence[int],
    top_waterfall: int,
    output_dir: Path,
    width_cm: float,
    height_cm: float,
    font_size_pt: float,
) -> None:
    available_indices = set(prediction_df.index.to_list())

    selected_indices: List[int] = []
    for idx in requested_indices:
        if idx in available_indices and idx not in selected_indices:
            selected_indices.append(idx)

    if top_waterfall > 0:
        top_indices = (
            prediction_df.sort_values("y_observed", ascending=False)
            .index.to_list()[:top_waterfall]
        )
        for idx in top_indices:
            if idx not in selected_indices:
                selected_indices.append(idx)

    if not selected_indices:
        return

    shap_columns = [f"SHAP_{name}" for name in feature_names]
    for idx in selected_indices:
        row = prediction_df.loc[idx]
        shap_values = row[shap_columns].to_numpy(dtype=float)
        base_value = float(row["shap_base_value"])
        explanation = shap.Explanation(
            values=shap_values,
            base_values=base_value,
            data=x_centered[idx],
            feature_names=list(feature_labels),
        )
        shap.plots.waterfall(explanation, show=False)
        apply_shap_figure_format(width_cm, height_cm, font_size_pt)
        plt.tight_layout(pad=0.3)
        plt.savefig(
            output_dir / f"shap_waterfall_sample_index_{idx}.png",
            dpi=300,
        )
        plt.close()


def save_pfi_bar(
    pfi_summary_df: pd.DataFrame,
    feature_label_map: Dict[str, str],
    output_path: Path,
) -> None:
    if pfi_summary_df.empty:
        return

    ordered = pfi_summary_df.sort_values(
        "mean_prediction_sensitivity_pfi_mse",
        ascending=False,
    ).copy()
    ordered["feature_label"] = ordered["feature"].map(feature_label_map).fillna(ordered["feature"])
    plt.figure(figsize=(4.2, 2.4), dpi=300)
    plt.bar(
        ordered["feature_label"],
        ordered["mean_prediction_sensitivity_pfi_mse"],
        yerr=ordered["sd_prediction_sensitivity_pfi_mse"].fillna(0),
        capsize=2,
    )
    plt.ylabel("Prediction-sensitivity PFI, MSE")
    plt.xlabel("Descriptor")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def main() -> int:
    args = parse_args()
    set_reproducible_seed(args.seed)

    descriptor_columns = split_comma_argument(args.descriptor_columns)
    feature_names = split_comma_argument(args.feature_names)
    feature_labels = split_comma_argument(args.feature_labels)
    if len(descriptor_columns) != len(feature_names):
        raise ValueError(
            "The numbers of descriptor columns and feature names must be identical."
        )
    if len(feature_names) != len(feature_labels):
        raise ValueError(
            "The numbers of feature names and feature labels must be identical."
        )
    feature_label_map = dict(zip(feature_names, feature_labels))

    if args.shap_nsamples == "auto":
        shap_nsamples: str | int = "auto"
    else:
        shap_nsamples = int(args.shap_nsamples)

    waterfall_indices = parse_integer_list(args.waterfall_indices)

    backend = resolve_backend(args.backend)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    _, analysis_df, x_raw, y = load_dataset(
        args.input,
        descriptor_columns,
        args.objective_column,
        strict_metadata=args.strict_metadata,
    )

    x_centered, centering_info = center_descriptors(x_raw, backend)

    folds = k_fold_split(
        n_samples=x_centered.shape[0],
        k=args.folds,
        shuffle=True,
        random_seed=args.seed,
    )

    print(f"Input CSV: {args.input}")
    print(f"Complete rows used for analysis: {x_centered.shape[0]}")
    print(f"Model backend: {backend}")
    print(f"SHAP background: {args.background}")
    print(f"SHAP nsamples: {shap_nsamples}")
    print(f"PFI calculation: {'skipped' if args.no_pfi else str(args.pfi_runs) + ' shuffles per feature'}")

    results: List[FoldModelResult] = []
    for fold_id, (train_indices, test_indices) in enumerate(folds):
        result = run_fold_analysis(
            fold=fold_id,
            train_indices=train_indices,
            test_indices=test_indices,
            x=x_centered,
            y=y,
            x_all=x_centered,
            backend=backend,
            seed=args.seed,
            background_mode=args.background,
            shap_nsamples=shap_nsamples,
            pfi_runs=args.pfi_runs,
            do_pfi=not args.no_pfi,
        )
        results.append(result)

    test_prediction_df = build_prediction_table(
        analysis_df,
        results,
        descriptor_columns,
        feature_names,
        args.objective_column,
    )
    train_prediction_df = build_training_prediction_table(
        analysis_df,
        results,
        args.objective_column,
    )
    metrics_df = build_metrics_table(results)
    shap_summary_df = build_shap_summary(test_prediction_df, feature_names)
    pfi_raw_df, pfi_summary_df = build_pfi_tables(results, feature_names)

    test_prediction_df.to_csv(args.output_dir / "shap_values_by_sample.csv", index=False)
    train_prediction_df.to_csv(args.output_dir / "training_predictions_by_fold.csv", index=False)
    metrics_df.to_csv(args.output_dir / "cross_validation_metrics.csv", index=False)
    shap_summary_df.to_csv(args.output_dir / "shap_absolute_summary.csv", index=False)
    pfi_raw_df.to_csv(args.output_dir / "pfi_prediction_sensitivity_by_fold.csv", index=False)
    pfi_summary_df.to_csv(args.output_dir / "pfi_prediction_sensitivity_summary.csv", index=False)

    feature_label_df = pd.DataFrame(
        {
            "descriptor_column": descriptor_columns,
            "feature_name": feature_names,
            "figure_label": feature_labels,
        }
    )
    feature_label_df.to_csv(args.output_dir / "feature_label_mapping.csv", index=False)

    # Store the centered descriptors that were used for model fitting and SHAP plotting.
    centered_df = analysis_df[
        [col for col in ["source_row_index", "expID", "ligand", "base", "solvent"] if col in analysis_df.columns]
    ].copy()
    for j, feature_name in enumerate(feature_names):
        centered_df[f"centered_{feature_name}"] = x_centered[:, j]
    centered_df.to_csv(args.output_dir / "centered_descriptor_matrix.csv", index=False)

    y_test_all = np.concatenate([r.y_test for r in results])
    y_test_pred_all = np.concatenate([r.y_test_pred for r in results])
    y_train_all = np.concatenate([r.y_train for r in results])
    y_train_pred_all = np.concatenate([r.y_train_pred for r in results])

    summary = {
        "input_csv": str(args.input),
        "output_dir": str(args.output_dir),
        "backend": backend,
        "requested_backend": args.backend,
        "seed": args.seed,
        "folds": args.folds,
        "n_complete_rows": int(x_centered.shape[0]),
        "descriptor_columns": descriptor_columns,
        "feature_names": feature_names,
        "feature_labels": feature_labels,
        "objective_column": args.objective_column,
        "shap_background": args.background,
        "shap_nsamples": shap_nsamples,
        "pfi_runs": None if args.no_pfi else args.pfi_runs,
        "shap_figure": {
            "width_cm": args.shap_fig_width_cm,
            "height_cm": args.shap_fig_height_cm,
            "font_size_pt": args.shap_font_size,
        },
        "centering": centering_info,
        "overall_metrics": {
            "r2_train": safe_r2(y_train_all, y_train_pred_all),
            "r2_test": safe_r2(y_test_all, y_test_pred_all),
            "r2_train_reversed_notebook": safe_r2(y_train_pred_all, y_train_all),
            "r2_test_reversed_notebook": safe_r2(y_test_pred_all, y_test_all),
            "rmse_train": float(np.sqrt(mean_squared_error(y_train_all, y_train_pred_all))),
            "rmse_test": float(np.sqrt(mean_squared_error(y_test_all, y_test_pred_all))),
            "mae_train": float(mean_absolute_error(y_train_all, y_train_pred_all)),
            "mae_test": float(mean_absolute_error(y_test_all, y_test_pred_all)),
        },
    }

    with open(args.output_dir / "analysis_summary.json", "w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)

    if not args.no_plots:
        save_prediction_plot(
            test_prediction_df,
            train_prediction_df,
            args.output_dir / "prediction_parity.png",
        )
        save_shap_abs_bar(
            shap_summary_df,
            feature_label_map,
            args.output_dir / "shap_absolute_bar.png",
            args.shap_fig_width_cm,
            args.shap_fig_height_cm,
            args.shap_font_size,
        )
        save_shap_summary_plots(
            test_prediction_df,
            x_centered,
            feature_names,
            feature_labels,
            args.output_dir,
            args.shap_fig_width_cm,
            args.shap_fig_height_cm,
            args.shap_font_size,
        )
        save_waterfall_plots(
            test_prediction_df,
            x_centered,
            feature_names,
            feature_labels,
            waterfall_indices,
            args.top_waterfall,
            args.output_dir,
            args.shap_fig_width_cm,
            args.shap_fig_height_cm,
            args.shap_font_size,
        )
        if not pfi_summary_df.empty:
            save_pfi_bar(
                pfi_summary_df,
                feature_label_map,
                args.output_dir / "pfi_prediction_sensitivity_bar.png",
            )

    print("\nOverall metrics")
    print(json.dumps(summary["overall_metrics"], indent=2))
    print(f"\nOutputs were written to: {args.output_dir.resolve()}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit("Interrupted by user.")
