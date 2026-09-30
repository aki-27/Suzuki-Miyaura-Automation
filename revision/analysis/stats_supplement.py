"""Additional descriptive statistics from saved predictions and simulation traces.

No model is fitted and no virtual campaign is rerun. When placed in the revision
analysis directory, run: python stats_supplement.py
Optional: --analysis-dir PATH --out-dir PATH
"""
from pathlib import Path
import argparse, csv, json, math, re
from collections import Counter
import numpy as np
from scipy.stats import beta, t


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, skipinitialspace=True))


def write_csv(path, rows):
    with path.open('w', encoding='utf-8', newline='') as f:
        writer=csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def metrics(y, prediction, std=None):
    y=np.asarray(y,float); prediction=np.asarray(prediction,float)
    residual=y-prediction
    total=np.sum((y-y.mean())**2)
    result={'n':len(y), 'r2':float(1-np.sum(residual**2)/total) if total>0 else None,
            'mae':float(np.mean(abs(residual))), 'rmse':float(np.sqrt(np.mean(residual**2))),
            'bias_observed_minus_predicted':float(residual.mean())}
    if std is not None:
        result['coverage95']=float(np.mean(abs(residual)<=1.959964*np.asarray(std,float)))
    return result


def median_iqr(values, prefix):
    q=np.quantile(np.asarray(values,float),[.25,.5,.75])
    return {prefix+'_median':float(q[1]),prefix+'_q25':float(q[0]),prefix+'_q75':float(q[2])}


def clopper_pearson(k, n):
    return (0. if k==0 else float(beta.ppf(.025,k,n-k+1)),
            1. if k==n else float(beta.ppf(.975,k+1,n-k)))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--analysis-dir',type=Path)
    parser.add_argument('--out-dir',type=Path)
    args=parser.parse_args()
    here=Path(__file__).resolve().parent
    analysis=args.analysis_dir or (here if (here/'analysis_results').exists() else here.parents[1]/'outputs/revision_package/analysis')
    output=args.out_dir or here/'stats'
    output.mkdir(parents=True,exist_ok=True)
    data=analysis/'data/Suzuki-Miyaura-Automation-main_v20'
    saved=analysis/'analysis_results'
    runs=read_csv(saved/'simulation_runs.csv')
    traces=np.load(saved/'simulation_traces.npy')
    landscapes=np.load(saved/'landscapes.npz')
    assert len(runs)==len(traces) and traces.shape[1]==192
    assert len(set(tuple(r[k] for k in ('landscape','initial_n','method','seed')) for r in runs))==len(runs)
    sim_rows=[]; success_rows=[]; paired_rows=[]
    groups=sorted(set((r['landscape'],int(r['initial_n']),r['method']) for r in runs))
    for surface,n0,method in groups:
        ix=[i for i,r in enumerate(runs) if (r['landscape'],int(r['initial_n']),r['method'])==(surface,n0,method)]
        rr=[runs[i] for i in ix]; tt=traces[ix]*100
        threshold=.95*float(np.exp(landscapes[surface].max()))
        candidate_n=len(landscapes[surface]); target_n=int(np.sum(np.exp(landscapes[surface])>=threshold))
        exact_p=1-math.prod((candidate_n-target_n-i)/(candidate_n-i) for i in range(192))
        hit=sum(r['hit95']=='True' for r in rr); lo,hi=clopper_pearson(hit,len(rr))
        success_rows.append({'landscape':surface,'initial_n':n0,'method':method,'runs':len(rr),
            'target_candidate_n':target_n,'candidate_n':candidate_n,'budget':192,
            'random_exact_success_probability':exact_p,'hits95':hit,'observed_success_fraction':hit/len(rr),
            'clopper_pearson95_low':lo,'clopper_pearson95_high':hi,
            'probability_all_10_random_runs_miss':(1-exact_p)**10})
        row={'landscape':surface,'initial_n':n0,'method':method,'runs':len(rr),'hits95':hit}
        for budget in (24,48,96,192):row.update(median_iqr(tt[:,budget-1],f'best{budget}_pct'))
        row.update(median_iqr(tt.mean(axis=1),'mean_best_curve_pct'))
        row.update(median_iqr([int(r['n_to95']) for r in rr],'n95_censored193'))
        sim_rows.append(row)
    for surface,n0 in sorted(set((r['landscape'],int(r['initial_n'])) for r in runs)):
        grouped={method:{int(r['seed']):i for i,r in enumerate(runs) if r['landscape']==surface and int(r['initial_n'])==n0 and r['method']==method}
                 for method in sorted(set(r['method'] for r in runs if r['landscape']==surface and int(r['initial_n'])==n0))}
        for method_a,method_b in [('onehot','descriptors'),('historical_columns','descriptors'),('descriptors','random'),('onehot','random')]:
            if method_a not in grouped or method_b not in grouped:continue
            seeds=sorted(set(grouped[method_a])&set(grouped[method_b]))
            for metric,budget in [('mean_best_curve_pct',None),('best24_pct',24),('best48_pct',48),('best96_pct',96),('best192_pct',192)]:
                vals=[]
                for seed in seeds:
                    a=traces[grouped[method_a][seed]]*100;b=traces[grouped[method_b][seed]]*100
                    vals.append(float(a.mean()-b.mean()) if budget is None else float(a[budget-1]-b[budget-1]))
                vv=np.asarray(vals)
                paired_rows.append({'landscape':surface,'initial_n':n0,'method_A':method_a,'method_B':method_b,
                    'metric':metric,'n_pairs':len(seeds),'mean_A_minus_B':float(vv.mean()),
                    **median_iqr(vv,'A_minus_B'),'A_greater':int(np.sum(vv>1e-12)),
                    'A_equal':int(np.sum(abs(vv)<=1e-12)),'A_lower':int(np.sum(vv< -1e-12))})
    write_csv(output/'simulation_success_uncertainty.csv',success_rows)
    write_csv(output/'simulation_group_statistics.csv',sim_rows)
    write_csv(output/'simulation_paired_contrasts.csv',paired_rows)

    log=read_csv(data/'results_log.csv')
    for i,r in enumerate(log):r['cycle']=i//4+1
    assert all(int(r['batch'])==i%4+1 for i,r in enumerate(log))
    assert all(a['time']<=b['time'] for a,b in zip(log,log[1:]))
    valid=[r for r in log if r['errors']=='normal termination']
    baseline={cycle:float(np.mean([float(r['objective']) for r in valid if r['cycle']<cycle])) for cycle in range(2,49)}
    fw=read_csv(saved/'forward_predictions.csv')
    kernel_re=re.compile(r'([\d.e+-]+)\*\*2 \* RBF\(length_scale=([\d.e+-]+)\) \+ WhiteKernel\(noise_level=([\d.e+-]+)\)')
    kernel_rows=[]; window_rows=[]; aggregate=[]
    for name in sorted(set(r['model'] for r in fw)):
        rows=[r for r in fw if r['model']==name]
        bycycle={int(r['batch']):r for r in rows}
        parsed={}
        for cycle,r in sorted(bycycle.items()):
            signal_sd,lengthscale,noise=map(float,kernel_re.fullmatch(r['kernel']).groups())
            parsed[cycle]=(signal_sd,lengthscale,noise)
            kernel_rows.append({'model':name,'cycle':cycle,'n_train':int(r['n_train']),
                'signal_sd_rounded':signal_sd,'lengthscale_rounded':lengthscale,'noise_variance_rounded':noise,
                'noise_at_lower_bound_from_rounded_text':noise<=1.0001e-8,
                'noise_within10x_lower_bound':noise<=1e-7})
        for start,stop in [(2,8),(9,16),(17,24),(25,32),(33,40),(41,48),(2,48)]:
            q=[r for r in rows if start<=int(r['batch'])<=stop]
            y=np.array([float(r['observed']) for r in q]);p=np.array([float(r['predicted']) for r in q]);s=np.array([float(r['std']) for r in q])
            base=np.array([baseline[int(r['batch'])] for r in q])
            gp=metrics(y,p,s);bm=metrics(y,base)
            cycles=sorted(set(int(r['batch']) for r in q));pars=np.array([parsed[b] for b in cycles])
            row={'model':name,'cycle_from':start,'cycle_to':stop,'n':len(q),'fitted_updates_with_valid_tests':len(cycles),
                 **{'gpr_'+k:v for k,v in gp.items() if k!='n'},
                 **{'training_mean_baseline_'+k:v for k,v in bm.items() if k!='n'},
                 'gpr_mae_pp':float(np.mean(abs(np.exp(y)-np.exp(p)))*100),
                 'training_mean_baseline_mae_pp':float(np.mean(abs(np.exp(y)-np.exp(base)))*100),
                 'signal_sd_min':float(pars[:,0].min()),'signal_sd_max':float(pars[:,0].max()),
                 'lengthscale_min':float(pars[:,1].min()),'lengthscale_max':float(pars[:,1].max()),
                 'noise_variance_min':float(pars[:,2].min()),'noise_variance_max':float(pars[:,2].max()),
                 'noise_lower_bound_updates_from_rounded_text':int(np.sum(pars[:,2]<=1.0001e-8)),
                 'noise_within10x_lower_bound_updates':int(np.sum(pars[:,2]<=1e-7))}
            (aggregate if (start,stop)==(2,48) else window_rows).append(row)
    write_csv(output/'forward_window_statistics.csv',window_rows)
    write_csv(output/'forward_aggregate_statistics.csv',aggregate)
    write_csv(output/'forward_kernel_diagnostics.csv',kernel_rows)

    prior=read_csv(data/'analysis_scripts/comparison_models/preliminary_campaign_results.csv')
    prior={int(r['expID']):r for r in prior if r['error_detection']=='normal termination'}
    floored={i for i,r in prior.items() if float(r['compound3_yield'])<1e-4}
    transfer=read_csv(saved/'campaign_transfer.csv')
    trstats=[]
    for subset,predicate in [('all',lambda r:True),('shared',lambda r:r['shared']=='True'),('nonshared',lambda r:r['shared']=='False')]:
        for exclude in (False,True):
            q=[r for r in transfer if predicate(r) and (not exclude or int(r['expID']) not in floored)]
            yy=np.array([float(r['observed_log']) for r in q]);pp=np.array([float(r['predicted_log']) for r in q]);ss=np.array([float(r['std']) for r in q])
            actual=np.array([float(prior[int(r['expID'])]['compound3_yield'])*100 for r in q]);pred=np.exp(pp)*100
            trstats.append({'subset':subset,'exclude_floored_prior':exclude,
                **{'log_'+k:v for k,v in metrics(yy,pp,ss).items()},
                **{'raw_yield_pp_'+k:v for k,v in metrics(actual,pred).items() if k!='n'}})
    write_csv(output/'transfer_sensitivity_statistics.csv',trstats)
    write_csv(output/'prior_floored_observations.csv',[{'expID':i,'raw_yield_fraction':float(prior[i]['compound3_yield']),
        'model_floor_fraction':1e-4,'model_log_target':math.log(1e-4)} for i in sorted(floored)])
    pairs=read_csv(saved/'paired_campaign_conditions.csv');diff=np.array([float(r['difference_pp']) for r in pairs])
    paired_t_ci=diff.mean()+t.ppf([.025,.975],len(diff)-1)*diff.std(ddof=1)/math.sqrt(len(diff))
    paired={'n':len(diff),'mean_main_minus_prior_pp':float(diff.mean()),'median_main_minus_prior_pp':float(np.median(diff)),
            'sample_sd_pp':float(diff.std(ddof=1)),'t95_low_pp':float(paired_t_ci[0]),'t95_high_pp':float(paired_t_ci[1]),
            'main_greater':int(np.sum(diff>0)),'equal':int(np.sum(diff==0)),'main_lower':int(np.sum(diff<0)),
            'interpretation':'Selected cross-campaign condition pairs; neither interval method establishes same-protocol repeatability.'}

    batch_rows=[]
    for cycle in range(1,49):
        rows=[r for r in log if r['cycle']==cycle];q=[r for r in rows if r['errors']=='normal termination']
        batch_rows.append({'cycle':cycle,'attempted':len(rows),'valid':len(q),'invalid':len(rows)-len(q),
            'mean_valid_yield_pct':float(np.mean([float(r['p2 yield'])*100 for r in q])) if q else None})
    write_csv(output/'batch_mean_denominators.csv',batch_rows)
    best=max((r for r in batch_rows if r['valid']),key=lambda r:r['mean_valid_yield_pct'])
    batch_summary={'denominator_counts':dict(Counter(r['valid'] for r in batch_rows)),
                   'maximum_mean_batch':best,'definition':'Mean over valid measurements in a scheduled four-attempt batch; invalid measurements are excluded, not set to zero.'}
    result={'scope':'Descriptive supplement calculated from existing outputs; no new fits or simulated campaigns.',
        'simulation':{'runs':len(runs),'budget':192,'success_interval':'Two-sided 95% Clopper-Pearson, conditional on fixed fitted surface and RNG policy.',
            'random_exact_formula':'1 - product((N-K-j)/(N-j), j=0,...,191), N=1500, K=number of target candidates.',
            'AUC_definition':'Arithmetic mean of the 192 best-so-far yield percentages (includes initial evaluations).',
            'quantiles':'NumPy default linear interpolation; medians/IQRs describe between-seed variation, not emulator uncertainty.',
            'n95_censoring':'Nonattainment is encoded as 193 solely for storage. A quantile of 193 must be presented as >192, not as an observed hitting time.',
            'paired_contrasts':'Method A minus B at matched seed; no independent-fold/point inference.'},
        'forward':{'windows':'Noncumulative cycle ranges 2-8,9-16,...,41-48; cycle1 is initial training only, cycle27 has no valid responses.',
            'baseline':'For every held-out cycle, predict mean log response of strictly earlier valid observations.',
            'kernels':'Parameters parsed from rounded saved kernel strings; these cannot recover optimizer convergence status.'},
        'prior_floor_count':len(floored),'transfer':'Raw-scale errors use original analytical yield values including negative measurements; log-scale uses archived floor transformation. Fixed predictions are unchanged when floor points are excluded.',
        'paired_campaign_statistics':paired,'batch_statistics':batch_summary}
    (output/'supplement_summary.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({'output':str(output.resolve()),'simulation_groups':len(sim_rows),'forward_windows':len(window_rows),
                      'transfer_groups':len(trstats),'paired':paired,'batch':batch_summary},indent=2))


if __name__=='__main__':main()
