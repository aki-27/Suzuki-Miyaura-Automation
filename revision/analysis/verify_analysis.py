import analysis_revision as a
import json, csv, hashlib, sys, platform
from pathlib import Path
import numpy as np
import joblib
out=a.OUT
z=np.load(out/'shap.npz'); cv=np.load(out/'cv_descriptors.npz')
err=[]
for fi,(ms,tr,te) in enumerate(joblib.load(out/'cv_descriptor_models.joblib')):
    bg=a.X[a.obs[np.random.default_rng(300+fi).choice(tr,16,replace=False)]]
    base=a.predict(ms,bg).mean()
    err.extend(abs(z['shap'][te].sum(1)+base-cv['predicted'][te]))
assert max(err)<1e-8,max(err)
fw=list(csv.DictReader((out/'forward_predictions.csv').open()))
for name in ['descriptors','historical_columns']:
    rows=[r for r in fw if r['model']==name]
    assert len(rows)==174
    for r in rows:
        batch=int(r['batch'])
        tr=[q for q in a.log if int(q['batch'])<batch and q['errors']=='normal termination']
        assert int(r['n_train'])==len(tr)
        te=[q for q in a.log if int(q['expID'])==int(r['expID']) and int(q['batch'])==batch]
        assert len(te)==1 and te[0]['errors']=='normal termination'
        assert not any(int(q['expID'])==int(r['expID']) for q in tr)
rr=list(csv.DictReader((out/'simulation_runs.csv').open()));tt=np.load(out/'simulation_traces.npy');land=np.load(out/'landscapes.npz')
assert tt.shape==(210,192)
assert (np.diff(tt,axis=1)>=-1e-12).all()
for row,trace in zip(rr,tt):
    truth=land[row['landscape']];seed=7000+int(row['seed']);n=int(row['initial_n'])
    ix=np.random.default_rng(seed).permutation(len(truth))[:n]
    assert np.allclose(trace[:n],np.maximum.accumulate(np.exp(truth[ix])))
    assert np.max(trace)<=np.exp(truth.max())+1e-10
    assert abs(trace[-1]*100-float(row['best192_pct']))<1e-10
    hit=np.flatnonzero(trace>=.95*np.exp(truth.max()))
    assert int(row['n_to95'])==(int(hit[0]+1) if len(hit) else 193)
assert len(a.obs)==178 and len(a.pre_idx)==68
assert len(set(a.obs)&set(a.pre_idx))==13
assert len(set(a.obs)|set(a.pre_idx))==233
summary=json.loads((out/'summary.json').read_text())
for n in ['descriptors','onehot','historical_columns','seed_all','seed_disjoint']:
    z=np.load(out/f'cv_{n}.npz')
    assert abs(a.metrics(z['observed'],z['predicted'])['r2']-summary[n]['r2'])<1e-12
result={'python':platform.python_version(),'checks':'PASS','main_valid':178,'preliminary_valid':68,'shared_conditions':13,'distinct_valid_conditions':233,'shap_max_additivity_error':float(max(err)),'forward_predictions_per_model':174,'simulation_runs':210,'budget_per_simulation':192,'sequential_training_verified':True,'simulation_initial_pairing_verified':True,'simulation_monotonicity_targets_and_summary_verified':True}
(out/'validation_report.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
