#!/usr/bin/env python3
"""Retrospective encoding and seeding analyses (ESI, Section "Additional
analyses"; Table S10 of the Digital Discovery manuscript).

Analysis 1 -- encoding comparison:
    Five-fold cross-validation of Gaussian process regression (GPR) yield
    prediction on the 178 valid measurements of the autonomous campaign,
    comparing (a) the eight expert descriptors used in the campaign with
    (b) a 35-dimensional one-hot encoding of the ligand (15), base (10),
    and solvent (10) identities, on identical splits.

Analysis 2 -- seeding analysis:
    The same cross-validation of the descriptor model, with the training
    folds augmented by the 68 valid results of the first (descriptor-
    screening) campaign expressed on the same objective scale, testing
    on autonomous-campaign folds only.

The GPR specification matches analysis_scripts/shap/run_shap_analysis.py:
constant x RBF kernel + white-noise term, normalize_y=True, five restarts
of the hyperparameter optimizer. The analysis is deterministic
(random_state = 0 for the model and the fold splits).

Inputs (relative to this directory):
    ../shap/2024_0712_0146_candidates.csv   final candidates table of the
                                            autonomous campaign (objectives
                                            filled for the 178 valid
                                            measurements; natural-log scale)
    ./preliminary_campaign_results.csv      results of the 70 experiments of
                                            the first campaign (68 valid)

Output:
    ./ohe_vs_descriptor_and_seeding_results.txt (also printed to stdout)

Requirements: numpy, scikit-learn (no PHYSBO dependency).

Usage:
    cd analysis_scripts/comparison_models
    python ohe_vs_descriptor_and_seeding.py
"""
import csv
import os
import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel, ConstantKernel
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score

HERE = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.join(HERE, '..', 'shap', '2024_0712_0146_candidates.csv')
PRELIM = os.path.join(HERE, 'preliminary_campaign_results.csv')
OUT = os.path.join(HERE, 'ohe_vs_descriptor_and_seeding_results.txt')

RNG = 0
YIELD_FLOOR = 1.0e-4  # 0.01 %, as applied in the autonomous campaign
DESC_COLS = ['cone angle', 'TEP', 'calc P shift', 'pKa', 'Pauling ionic radii',
             'Hansen-dD', 'Hansen-dP', 'Hansen-dH']
N_LIG, N_BASE, N_SOLV = 15, 10, 10


def gpr():
    kernel = (ConstantKernel(1.0, (1.0e-3, 1.0e3))
              * RBF(1.0, (1.0e-2, 1.0e3))
              + WhiteKernel(1.0e-3, (1.0e-8, 1.0e1)))
    return GaussianProcessRegressor(kernel=kernel, normalize_y=True,
                                    n_restarts_optimizer=5, random_state=RNG)


def onehot(lig, base, solv):
    x = np.zeros((len(lig), N_LIG + N_BASE + N_SOLV))
    for i, (l, b, s) in enumerate(zip(lig, base, solv)):
        x[i, int(l) - 1] = 1.0
        x[i, N_LIG + int(b) - 1] = 1.0
        x[i, N_LIG + N_BASE + int(s) - 1] = 1.0
    return x


def main():
    lines = []

    def log(msg=''):
        print(msg)
        lines.append(msg)

    # ---- autonomous campaign: 178 valid measurements ----
    with open(CAND) as f:
        rows = list(csv.DictReader(f))
    desc_by_key = {(int(r['ligand']), int(r['base']), int(r['solvent'])):
                   [float(r[c]) for c in DESC_COLS] for r in rows}
    meas = [r for r in rows if r['objectives'].strip() != '']
    lig = np.array([int(r['ligand']) for r in meas])
    base = np.array([int(r['base']) for r in meas])
    solv = np.array([int(r['solvent']) for r in meas])
    x_desc = np.array([[float(r[c]) for c in DESC_COLS] for r in meas])
    x_ohe = onehot(lig, base, solv)
    y = np.array([float(r['objectives']) for r in meas])
    log(f'autonomous campaign: N = {len(y)} valid measurements '
        f'(objective = ln(yield of 3); best yield = {np.exp(y.max()):.3f})')

    # ---- first campaign: 68 valid results as potential seed data ----
    with open(PRELIM) as f:
        prows = list(csv.DictReader(f))
    valid = [r for r in prows
             if r['error_detection'].strip() == 'normal termination']
    x_pre = np.array([desc_by_key[(int(r['ligand']), int(r['base']),
                                   int(r['solvent']))] for r in valid])
    y_pre = np.log([max(float(r['compound3_yield']), YIELD_FLOOR)
                    for r in valid])
    log(f'first campaign: N = {len(valid)} valid results used as seed data')
    log()

    # ---- five-fold CV, identical splits across all settings ----
    kf = KFold(n_splits=5, shuffle=True, random_state=RNG)
    results = {'expert descriptors (8 dims)': [],
               'one-hot encoding (35 dims)': [],
               'descriptors + first-campaign seed': []}
    for tr, te in kf.split(x_desc):
        sc = StandardScaler().fit(x_desc[tr])
        m = gpr().fit(sc.transform(x_desc[tr]), y[tr])
        results['expert descriptors (8 dims)'].append(
            r2_score(y[te], m.predict(sc.transform(x_desc[te]))))

        m = gpr().fit(x_ohe[tr], y[tr])
        results['one-hot encoding (35 dims)'].append(
            r2_score(y[te], m.predict(x_ohe[te])))

        x_tr = np.vstack([x_desc[tr], x_pre])
        y_tr = np.concatenate([y[tr], y_pre])
        sc = StandardScaler().fit(x_tr)
        m = gpr().fit(sc.transform(x_tr), y_tr)
        results['descriptors + first-campaign seed'].append(
            r2_score(y[te], m.predict(sc.transform(x_desc[te]))))

    for name, vals in results.items():
        log(f'{name:36s} test R2 = {np.mean(vals):.3f} +/- {np.std(vals):.3f}'
            f'  (folds: {", ".join(f"{v:.2f}" for v in vals)})')

    with open(OUT, 'w') as f:
        f.write('\n'.join(lines) + '\n')
    print(f'\nresults written to {os.path.relpath(OUT, os.getcwd())}')


if __name__ == '__main__':
    main()
