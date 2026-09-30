"""Reproducible retrospective analyses for DD-ART-08-2026-000634.
Run: python analysis_revision.py models | simulate | figures
All new analyses are retrospective, using scikit-learn, not a replay of
the historical PHYSBO executable. See methods.json for exact settings.
"""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']: os.environ[k]='1'
import sys, json, csv, math, warnings, argparse, itertools, time
from pathlib import Path
import numpy as np
from scipy.linalg import solve_triangular
from scipy.optimize import minimize
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, RBF, WhiteKernel
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold, LeaveOneGroupOut
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.exceptions import ConvergenceWarning
from threadpoolctl import threadpool_limits
import joblib
threadpool_limits(limits=1)
FIT_DIAGNOSTICS=[]
ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data'/'Suzuki-Miyaura-Automation-main_v20'
OUT=ROOT/'analysis_results'; OUT.mkdir(exist_ok=True)
FIG=ROOT.parent/'source'/'images';FIG.mkdir(exist_ok=True,parents=True)
COLS=['cone angle','TEP','calc P shift','pKa','Pauling ionic radii','Hansen-dD','Hansen-dP','Hansen-dH']
LABELS=['Cone angle','TEP','31P NMR','pKa','Ion radius','Hansen dD','Hansen dP','Hansen dH']
def read(rel):
 with open(DATA/rel,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,skipinitialspace=True))
def writecsv(name,rows):
 with open(OUT/name,'w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def save(name,obj): (OUT/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf-8')
def key(r):return tuple(int(r[c]) for c in ['ligand','base','solvent'])
allrows=read('analysis_scripts/shap/2024_0712_0146_candidates.csv')
X=np.array([[float(r[c]) for c in COLS] for r in allrows]); keys=[key(r) for r in allrows]
ids=np.array([int(r['expID']) for r in allrows]); idmap={v:i for i,v in enumerate(ids)};keymap={v:i for i,v in enumerate(keys)}
X12=np.array([[float(r[c]) for c in ['expID','ligand','base','solvent']+COLS] for r in allrows])
cat=np.array(keys); Xoh=np.concatenate([np.eye(n)[cat[:,i]-1] for i,n in enumerate([15,10,10])],axis=1)
obs=np.array([i for i,r in enumerate(allrows) if r['objectives'].strip()]); y=np.array([float(allrows[i]['objectives']) for i in obs])
pre=[r for r in read('analysis_scripts/comparison_models/preliminary_campaign_results.csv') if r['error_detection']=='normal termination']
pre_idx=np.array([keymap[key(r)] for r in pre]); pre_y=np.log([max(float(r['compound3_yield']),1e-4) for r in pre])
log=read('results_log.csv')
for j,r in enumerate(log):
 r['position_in_batch']=r['batch']
 r['batch']=str(j//4+1)  # archived 'batch' is position 1-4, not cycle number
def gp(seed=0,restarts=5,fast=False):
 k=ConstantKernel(1.,(1e-3,1e3))*RBF(1.,(1e-2,1e3))+WhiteKernel(1e-3,(1e-8,10.))
 opt_records=[]
 def opt(obj,theta,bounds):
  r=minimize(obj,theta,jac=True,bounds=bounds,method='L-BFGS-B',options={'maxiter':40,'ftol':1e-8})
  opt_records.append({'success':bool(r.success),'status':int(r.status),'message':str(r.message),'iterations':int(r.nit),'objective':float(r.fun)})
  return r.x,r.fun
 m=GaussianProcessRegressor(kernel=k,normalize_y=True,n_restarts_optimizer=restarts,random_state=seed,optimizer=opt if fast else 'fmin_l_bfgs_b',alpha=1e-10)
 m._revision_optimizer_records=opt_records
 return m
def fit(raw,yy,seed=0,restarts=5,scale=True,fast=False):
 sc=StandardScaler().fit(raw) if scale else None
 with warnings.catch_warnings(record=True) as captured:
  warnings.simplefilter('always',ConvergenceWarning)
  m=gp(seed,restarts,fast).fit(sc.transform(raw) if sc else raw,yy)
 theta=m.kernel_.theta; bounds=m.kernel_.bounds
 FIT_DIAGNOSTICS.append({'fit_index':len(FIT_DIAGNOSTICS)+1,'n_train':len(yy),'n_features':raw.shape[1],'scaled':bool(scale),'seed':seed,'restarts':restarts,'fast':bool(fast),'kernel':str(m.kernel_),'theta':theta.tolist(),'near_lower_bound':np.isclose(theta,bounds[:,0],atol=1e-6,rtol=0).tolist(),'near_upper_bound':np.isclose(theta,bounds[:,1],atol=1e-6,rtol=0).tolist(),'warnings':[str(w.message) for w in captured],'optimizer_results':m._revision_optimizer_records})
 return m,sc
def predict(ms,raw,std=False):
 m,sc=ms;return m.predict(sc.transform(raw) if sc else raw,return_std=std)
def metrics(a,b,std=None):
 d={'n':len(a),'r2':float(r2_score(a,b)),'rmse_log':float(np.sqrt(mean_squared_error(a,b))),'mae_log':float(mean_absolute_error(a,b)),
 'bias_log_observed_minus_predicted':float(np.mean(a-b)), 'mae_yield_pp':float(100*mean_absolute_error(np.exp(a),np.exp(b)))}
 if std is not None:d['coverage95']=float(np.mean(abs(a-b)<=1.959964*std))
 return d
def models():
 summary={}; folds=list(KFold(5,shuffle=True,random_state=0).split(obs)); outpred={};cvrows=[];shap=np.zeros((len(obs),8)); pfis=[]
 writecsv('cv_assignments.csv',[{'fold':fi+1,'role':role,'candidate_id':int(ids[obs[i]])} for fi,(tr,te) in enumerate(folds) for role,idx in [('train',tr),('test',te)] for i in idx])
 for name,raw in [('descriptors',X),('onehot',Xoh),('historical_columns',X12),('seed_all',X),('seed_disjoint',X)]:
  pred=np.zeros(len(obs));ss=np.zeros(len(obs));trainr=[];foldr=[];models8=[]
  for fi,(tr,te) in enumerate(folds):
   tridx=obs[tr];yy=y[tr];rawtr=raw[tridx]
   if name.startswith('seed'):
    use=np.ones(len(pre_idx),dtype=bool) if name=='seed_all' else ~np.isin(pre_idx,obs[te])
    rawtr=np.vstack([rawtr,raw[pre_idx[use]]]);yy=np.r_[yy,pre_y[use]]
   ms=fit(rawtr,yy,scale=name!='onehot');pred[te],ss[te]=predict(ms,raw[obs[te]],True)
   trainr.append(r2_score(yy,predict(ms,rawtr)));foldr.append(r2_score(y[te],pred[te]))
   cvrows.append({'model':name,'fold':fi+1,'training_n':len(yy),'test_n':len(te),'test_r2':foldr[-1],'train_r2':trainr[-1],'kernel':str(ms[0].kernel_)})
   if name=='descriptors':models8.append((ms,tr,te))
  summary[name]={**metrics(y,pred,ss),'fold_r2_mean':float(np.mean(foldr)),'fold_r2_sd':float(np.std(foldr)),'train_r2_mean':float(np.mean(trainr))}
  outpred[name]=pred;np.savez(OUT/f'cv_{name}.npz',observed=y,predicted=pred,std=ss,obs=obs)
  if name=='descriptors':joblib.dump(models8,OUT/'cv_descriptor_models.joblib')
  print('CV',name,summary[name],flush=True)
 writecsv('cv_by_fold.csv',cvrows)
 pre_pred=np.zeros(len(pre_y));pre_train=[];pre_fold=[]
 for tr,te in KFold(5,shuffle=True,random_state=0).split(pre_idx):
  ms=fit(X[pre_idx[tr]],pre_y[tr]);pre_pred[te]=predict(ms,X[pre_idx[te]])
  pre_train.append(r2_score(pre_y[tr],predict(ms,X[pre_idx[tr]])));pre_fold.append(r2_score(pre_y[te],pre_pred[te]))
 summary['first_campaign_cv']={**metrics(pre_y,pre_pred),'train_r2_mean':float(np.mean(pre_train)),'fold_r2_mean':float(np.mean(pre_fold)),'fold_r2_sd':float(np.std(pre_fold))}
 np.savez(OUT/'cv_first_campaign.npz',observed=pre_y,predicted=pre_pred)
 # Direct paired comparison; sample conditions, not individual observations.
 common=sorted(set(obs)&set(pre_idx));pairs=[]
 for i in common:
  a=pre_y[np.flatnonzero(pre_idx==i)[0]];b=y[np.flatnonzero(obs==i)[0]]
  pairs.append({'expID':int(ids[i]),'ligand':keys[i][0],'base':keys[i][1],'solvent':keys[i][2],'pre_yield':float(np.exp(a)),'main_yield':float(np.exp(b)),'difference_pp':float(100*(np.exp(b)-np.exp(a)))})
 diff=np.array([r['difference_pp'] for r in pairs]);rng=np.random.default_rng(9125);boots=rng.choice(diff,(10000,len(diff)),replace=True).mean(axis=1)
 summary['paired']={'n':len(diff),'mean_difference_pp':float(diff.mean()),'median_difference_pp':float(np.median(diff)),'bootstrap95_mean_pp':np.quantile(boots,[.025,.975]).tolist(),'sd_difference_pp':float(diff.std(ddof=1))}
 writecsv('paired_campaign_conditions.csv',pairs)
 ms=fit(X[obs],y); p,s=predict(ms,X[pre_idx],True);mask=np.isin(pre_idx,common)
 for name,sel in [('all',np.ones(len(pre_idx),bool)),('shared',mask),('nonshared',~mask)]:summary['transfer_'+name]=metrics(pre_y[sel],p[sel],s[sel])
 writecsv('campaign_transfer.csv',[{'expID':int(ids[i]),'shared':bool(sh),'observed_log':float(a),'predicted_log':float(b),'std':float(c)} for i,sh,a,b,c in zip(pre_idx,mask,pre_y,p,s)])
 print('TRANSFER',summary['paired'],summary['transfer_nonshared'],flush=True)
 # Ligand-disjoint extrapolation; deterministic, train-only standardization.
 lorows=[]
 for name,raw in [('descriptors',X),('onehot',Xoh)]:
  pred=np.zeros(len(y));sd=np.zeros(len(y))
  for ligand in sorted(set(cat[obs,0])):
   te=np.flatnonzero(cat[obs,0]==ligand);tr=np.flatnonzero(cat[obs,0]!=ligand)
   ms=fit(raw[obs[tr]],y[tr],scale=name!='onehot');pred[te],sd[te]=predict(ms,raw[obs[te]],True)
   lorows.append({'model':name,'ligand':int(ligand),**metrics(y[te],pred[te],sd[te])})
  summary['ligand_holdout_'+name]=metrics(y,pred,sd)
 writecsv('ligand_holdout.csv',lorows);print('LIGAND HOLDOUT done',flush=True)
 # Forward prediction based only on earlier valid batches, retrospective sklearn reconstruction.
 frows=[]
 for name,raw in [('descriptors',X),('historical_columns',X12)]:
  for batch in range(2,49):
   tr=[r for r in log if int(r['batch'])<batch and r['errors']=='normal termination'];te=[r for r in log if int(r['batch'])==batch and r['errors']=='normal termination']
   if not te:continue
   a=np.array([idmap[int(r['expID'])] for r in tr]); yy=np.array([float(r['objective']) for r in tr]); b=np.array([idmap[int(r['expID'])] for r in te])
   ms=fit(raw[a],yy,restarts=1);p,s=predict(ms,raw[b],True)
   for r,pr,st in zip(te,p,s):frows.append({'model':name,'batch':batch,'n_train':len(tr),'expID':int(r['expID']),'observed':float(r['objective']),'predicted':float(pr),'std':float(st),'kernel':str(ms[0].kernel_)})
  q=[r for r in frows if r['model']==name];summary['forward_'+name]=metrics(np.array([r['observed'] for r in q]),np.array([r['predicted'] for r in q]),np.array([r['std'] for r in q]))
  print('FORWARD',name,summary['forward_'+name],flush=True)
 writecsv('forward_predictions.csv',frows)
 # Exact eight-feature coalition enumeration, finite training-background expectation.
 masks=np.array([[bool(j&(1<<i)) for i in range(8)] for j in range(256)])
 pf=[]
 for fi,(ms,tr,te) in enumerate(joblib.load(OUT/'cv_descriptor_models.joblib')):
  rng=np.random.default_rng(300+fi);bg=X[obs[rng.choice(tr,16,replace=False)]]
  for ii in te:
   xx=np.where(masks[:,None,:],X[obs[ii]][None,None,:],bg[None,:,:]).reshape(-1,8)
   val=predict(ms,xx).reshape(256,16).mean(axis=1)
   for j in range(8):
    jj=[a for a in range(256) if not a&(1<<j)]
    shap[ii,j]=sum((val[a|(1<<j)]-val[a])/(8*math.comb(7,int(masks[a].sum()))) for a in jj)
  baseline=predict(ms,X[obs[te]])
  for j in range(8):
   vv=[]
   for rep in range(50):
    xx=X[obs[te]].copy();xx[:,j]=rng.permutation(xx[:,j]);vv.append(np.mean((predict(ms,xx)-baseline)**2))
   pf.append({'fold':fi+1,'feature':COLS[j],'sensitivity':float(np.mean(vv))})
  print('SHAP fold',fi+1,flush=True)
 np.savez(OUT/'shap.npz',shap=shap,X=X[obs],observed=y,obs=obs)
 writecsv('pfi.csv',pf);summary['shap_mean_abs']=dict(zip(COLS,np.abs(shap).mean(axis=0).tolist()))
 # Candidate-table scenarios from a full-data post hoc descriptor model.
 ms=fit(X[obs],y);p,s=predict(ms,X,True)
 scen=[]
 for label,i in [('highest_predicted',int(np.argmax(p))),('lowest_predicted',int(np.argmin(p)))]:
  scen.append({'scenario':label,'expID':int(ids[i]),'ligand':keys[i][0],'base':keys[i][1],'solvent':keys[i][2],'predicted_log':float(p[i]),'predictive_sd_log':float(s[i]),'predicted_median_yield_pct':float(100*np.exp(p[i])),'lower95_pct':float(100*np.exp(p[i]-1.96*s[i])),'upper95_pct':float(100*np.exp(p[i]+1.96*s[i])),'measured_yield_pct':float(100*np.exp(y[np.flatnonzero(obs==i)[0]])) if i in obs else None})
 summary['scenarios']=scen;writecsv('candidate_scenarios.csv',scen)
 # Three fitted, noise-free virtual response landscapes; no claim of known unmeasured yields.
 em={}; em['descriptor_GP']=np.clip(p,np.log(1e-4),0)
 mso=fit(Xoh[obs],y,scale=False);em['onehot_GP']=np.clip(predict(mso,Xoh),np.log(1e-4),0)
 rf=RandomForestRegressor(n_estimators=300,min_samples_leaf=2,max_features=1.,random_state=9125,n_jobs=1).fit(Xoh[obs],y)
 em['onehot_RF']=np.clip(rf.predict(Xoh),np.log(1e-4),0)
 np.savez(OUT/'landscapes.npz',**em)
 summary['landscape_best_yield_pct']={k:float(100*np.exp(v.max())) for k,v in em.items()}
 summary['versions']={k:__import__(k).__version__ for k in ['numpy','scipy','sklearn','matplotlib']}
 save('summary.json',summary)
 save('methods.json',{'cv_folds':5,'split_seed':0,'gpr':'Constant(1,[1e-3,1e3])*RBF(1,[1e-2,1e3])+White(1e-3,[1e-8,10])','normalize_y':True,'restarts_cv':5,'forward_restarts':1,'shap_background_per_fold':16,'shap_coalitions':256,'pfi_shuffles':50,'bootstrap_resamples':10000,'historical_nimsos':'1.0.1','historical_physbo':'2.0.0','historical_physbo_evidence':'Author confirmation via co-author Tamura; 2024 main campaign only','historical_implementation':'Standard PHYSBO/NIMS-OS; no manual hyperparameter adjustment','online_input_columns':['expID','ligand','base','solvent']+COLS})
 print('MODELS FINISHED',flush=True)
def campaign(raw,truth,initial,seed,random=False):
 rng=np.random.default_rng(seed);order=rng.permutation(len(raw));sel=list(order[:initial]);ys=list(truth[sel]);trace=list(np.maximum.accumulate(np.exp(ys)))
 if random:return np.maximum.accumulate(np.exp(truth[order[:192]]))
 xx=raw if raw.shape[1]==35 else StandardScaler().fit_transform(raw)
 while len(sel)<192:
  ms=fit(xx[sel],np.array(ys),seed=seed,restarts=0,scale=False,fast=True);m=ms[0];b=min(4,192-len(sel))
  # Joint posterior function draws via a 256-feature prior and exact GP correction.
  amp=m.kernel_.k1.k1.constant_value;ell=m.kernel_.k1.k2.length_scale;noise=m.kernel_.k2.noise_level
  w=rng.normal(size=(xx.shape[1],256))/ell;phase=rng.uniform(0,2*np.pi,256)
  phi=np.sqrt(2*amp/256)*np.cos(xx@w+phase)
  prior=phi@rng.normal(size=(256,b));eps=rng.normal(scale=np.sqrt(noise),size=(len(sel),b))
  norm=(np.array(ys)-m._y_train_mean)/m._y_train_std
  rhs=norm[:,None]-prior[sel]-eps
  coef=solve_triangular(m.L_.T,solve_triangular(m.L_,rhs,lower=True),lower=False)
  post=prior+m.kernel_.k1(xx,xx[sel])@coef
  post[sel,:]=-np.inf;new=[]
  for j in range(b):
   a=int(np.argmax(post[:,j]));new.append(a);post[a,:]=-np.inf
  sel.extend(new);ys.extend(truth[new]);trace.extend(list(np.maximum.accumulate(np.r_[trace[-1],np.exp(truth[new])]))[1:])
 return np.array(trace)
def simulate():
 landscapes=np.load(OUT/'landscapes.npz'); records=[];traces=[];start=time.time()
 # Main benchmark: 10 paired seeds, n0=4, three alternative response models.
 # Initialization sensitivity: n0=2/8/16 on the RF surface, 10 paired seeds each.
 for name in landscapes.files:
  truth=landscapes[name];inits=[2,4,8,16] if name=='onehot_RF' else [4]
  for n0 in inits:
   methods=[('descriptors',X),('onehot',Xoh),('random',X)]
   if n0==4:methods.insert(2,('historical_columns',X12))
   for seed in range(10):
    for method,raw in methods:
     trace=campaign(raw,truth,n0,7000+seed,method=='random');traces.append(trace)
     # Absolute target additionally reported; landscape-relative target is always defined.
     target=.95*np.exp(truth.max());hit=np.flatnonzero(trace>=target);hit40=np.flatnonzero(trace>=.40)
     records.append({'landscape':name,'initial_n':n0,'seed':seed,'method':method,'best192_pct':float(100*trace[-1]),'mean_best_curve_pct':float(100*trace.mean()),'hit95':bool(len(hit)),'n_to95':int(hit[0]+1) if len(hit) else 193,'hit40':bool(len(hit40)),'n_to40':int(hit40[0]+1) if len(hit40) else 193,'virtual_best_pct':float(100*np.exp(truth.max()))})
    print('SIM',name,n0,seed+1,'/10','elapsed',round(time.time()-start),flush=True)
    writecsv('simulation_runs.csv',records);np.save(OUT/'simulation_traces.npy',np.array(traces))
 save('simulation_methods.json',{'seeds':list(range(7000,7010)),'budget':192,'batch_size_after_initial':4,'main_initial_n':4,'sensitivity_initial_n':[2,4,8,16],'sensitivity_landscape':'onehot_RF','surrogate':'sklearn GPR, kernel as CV, target normalized, refit after each batch, zero restarts, L-BFGS-B maxiter40 ftol1e-8','candidate_scaling':'all known candidate X, no objective values','joint_TS':'Matheron correction with 256 Fourier prior features, independent draw per batch proposal','observations':'deterministic fitted virtual log-yield, no added physical noise','targets':['40% yield','95% of virtual landscape maximum yield'],'nonattainment_code':193,'interpretation':'conditional simulator benchmark, not a historical PHYSBO replay or experimental comparison'})
 print('SIMULATION FINISHED',flush=True)
def figures():
 import matplotlib;matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
 def export(fig,name):fig.savefig(FIG/name,bbox_inches='tight');plt.close(fig)
 summary=json.loads((OUT/'summary.json').read_text());z=np.load(OUT/'cv_descriptors.npz');sh=np.load(OUT/'shap.npz')
 zz=np.load(OUT/'cv_first_campaign.npz');fig,ax=plt.subplots(figsize=(4.4,3.5));ax.scatter(zz['observed'],zz['predicted'],s=18,color='#d47b16');lim=[min(zz['observed'].min(),zz['predicted'].min()),max(zz['observed'].max(),zz['predicted'].max())];ax.plot(lim,lim,ls='--',color='gray');ax.set(xlabel='Observed ln(yield fraction)',ylabel='Out-of-fold prediction',title='First campaign: 68 valid measurements');ax.text(.04,.96,f"Pooled test R² = {summary['first_campaign_cv']['r2']:.2f}",transform=ax.transAxes,va='top');fig.tight_layout();export(fig,'Fig3_revision.pdf')
 plt.rcParams.update({'font.size':11});fig,ax=plt.subplots(1,3,figsize=(11,3.8),gridspec_kw={'width_ratios':[1,1,1.25]})
 vv=np.array([float(r['p2 yield']) if r['errors']=='normal termination' else np.nan for r in log])*100
 ax[0].scatter(np.arange(1,193),vv,s=9,c='#167ac6');ax[0].plot(np.arange(1,193),np.maximum.accumulate(np.nan_to_num(vv)),c='#d47b16');ax[0].set(xlabel='Attempted experiment',ylabel='Yield of 3 (%)',title='a  Experimental campaign')
 ax[1].scatter(z['observed'],z['predicted'],s=12,alpha=.7,c='#d47b16');lo=min(z['observed'].min(),z['predicted'].min());hi=max(z['observed'].max(),z['predicted'].max());ax[1].plot([lo,hi],[lo,hi],c='gray',ls='--');ax[1].set(xlabel='Observed ln(yield fraction)',ylabel='Out-of-fold prediction',title='b  Eight-descriptor GPR');ax[1].text(.03,.97,f"Pooled test R² = {summary['descriptors']['r2']:.2f}",transform=ax[1].transAxes,va='top')
 order=np.argsort(abs(sh['shap']).mean(axis=0));rng=np.random.default_rng(0)
 for j,k in enumerate(order):
  v=sh['X'][:,k];color=(v-v.min())/(np.ptp(v) or 1);sc=ax[2].scatter(sh['shap'][:,k],j+rng.uniform(-.23,.23,len(v)),c=color,cmap='coolwarm',s=5,alpha=.7,vmin=0,vmax=1)
 ax[2].set(yticks=range(8),yticklabels=[LABELS[k] for k in order],xlabel='SHAP value (ln yield)',title='c  Post hoc model interpretation');ax[2].axvline(0,color='gray',lw=.5);fig.colorbar(sc,ax=ax[2],label='Relative feature value',fraction=.04);fig.tight_layout();export(fig,'Fig4_revision.pdf')
 plt.rcParams.update({'font.size':9});pfi=list(csv.DictReader(open(OUT/'pfi.csv')));vals=[np.mean([float(r['sensitivity']) for r in pfi if r['feature']==c]) for c in COLS];fig,ax=plt.subplots(figsize=(6,3.5));order=np.argsort(vals);ax.barh(np.array(LABELS)[order],np.array(vals)[order],color='#167ac6');ax.set(xlabel='Mean squared change in predicted ln(yield)',title='Held-out prediction sensitivity');fig.tight_layout();export(fig,'PFI_revision.pdf')
 tr=list(csv.DictReader(open(OUT/'campaign_transfer.csv')));pairs=list(csv.DictReader(open(OUT/'paired_campaign_conditions.csv')));fig,ax=plt.subplots(1,2,figsize=(9,3.6))
 for label,color in [('True','#d47b16'),('False','#167ac6')]:
  q=[r for r in tr if r['shared']==label];ax[0].scatter([float(r['observed_log']) for r in q],[float(r['predicted_log']) for r in q],s=18,label='Shared conditions' if label=='True' else 'Nonshared conditions',color=color)
 ax[0].plot([-9.3,0],[-9.3,0],c='gray',ls='--');ax[0].set(xlabel='First-campaign observed ln(yield)',ylabel='Prediction from main campaign');ax[0].legend(fontsize=7)
 a=np.array([float(r['pre_yield']) for r in pairs])*100;b=np.array([float(r['main_yield']) for r in pairs])*100;ax[1].scatter((a+b)/2,b-a,color='#167ac6');ax[1].axhline(0,color='gray',ls='--');ax[1].axhline((b-a).mean(),color='#d47b16');ax[1].set(xlabel='Mean yield of paired measurements (%)',ylabel='Main minus first campaign (pp)',title='13 shared conditions');fig.tight_layout();export(fig,'campaign_transfer.pdf')
 fw=list(csv.DictReader(open(OUT/'forward_predictions.csv')));fig,ax=plt.subplots(1,2,figsize=(9,3.5))
 for name,color in [('descriptors','#167ac6'),('historical_columns','#d47b16')]:
  q=[r for r in fw if r['model']==name];b=np.array([int(r['batch']) for r in q]);e=np.abs(np.array([float(r['observed'])-float(r['predicted']) for r in q]));ns=[8,16,24,32,40,48];ax[0].plot(ns,[e[b<=n].mean() for n in ns],marker='o',label=name.replace('_',' '),color=color)
  if name=='historical_columns':ax[1].scatter([float(r['observed']) for r in q],[float(r['predicted']) for r in q],s=12,color=color,alpha=.7)
 ax[0].set(xlabel='Batch included',ylabel='Cumulative next-batch MAE (ln yield)');ax[0].legend(fontsize=7);ax[1].plot([-9.3,0],[-9.3,0],ls='--',color='gray');ax[1].set(xlabel='Observed ln(yield)',ylabel='Next-batch prediction (12 columns)');fig.tight_layout();export(fig,'forward_prediction.pdf')
 if (OUT/'simulation_runs.csv').exists():
  rec=list(csv.DictReader(open(OUT/'simulation_runs.csv')));tt=np.load(OUT/'simulation_traces.npy')*100;colors={'descriptors':'#167ac6','onehot':'#cc5c1e','historical_columns':'#75479c','random':'#777777'}
  fig,ax=plt.subplots(1,3,figsize=(12,3.5))
  for a,land in zip(ax,['descriptor_GP','onehot_GP','onehot_RF']):
   for method,color in colors.items():
    q=[i for i,r in enumerate(rec) if r['landscape']==land and r['method']==method and r['initial_n']=='4'];v=tt[q];a.plot(np.arange(1,193),np.median(v,axis=0),label=method.replace('_',' '),color=color);a.fill_between(np.arange(1,193),np.quantile(v,.25,axis=0),np.quantile(v,.75,axis=0),color=color,alpha=.12)
   a.set(title=land.replace('_',' '),xlabel='Virtual evaluations',ylabel='Best virtual yield (%)')
  ax[0].legend(fontsize=6);fig.tight_layout();export(fig,'simulation_encodings.pdf')
  fig,ax=plt.subplots(1,2,figsize=(9,3.5))
  for a,method in zip(ax,['descriptors','onehot']):
   for n0 in [2,4,8,16]:
    q=[i for i,r in enumerate(rec) if r['landscape']=='onehot_RF' and r['method']==method and r['initial_n']==str(n0)];v=tt[q];a.plot(np.arange(1,193),np.median(v,axis=0),label=f'n0 = {n0}');a.fill_between(np.arange(1,193),np.quantile(v,.25,axis=0),np.quantile(v,.75,axis=0),alpha=.08)
   a.set(title=method,xlabel='Virtual evaluations',ylabel='Best virtual yield (%)');a.legend(fontsize=7)
  fig.tight_layout();export(fig,'simulation_initialization.pdf')
  sim_summary=[]
  for land in ['descriptor_GP','onehot_GP','onehot_RF']:
   for method in colors:
    rows=[r for r in rec if r['landscape']==land and r['method']==method and r['initial_n']=='4']
    sim_summary.append({'landscape':land,'method':method,'median_best192':float(np.median([float(r['best192_pct']) for r in rows])),'hit95':sum(r['hit95']=='True' for r in rows),'median_n95':float(np.median([int(r['n_to95']) for r in rows]))})
  save('simulation_summary.json',sim_summary)
 print('FIGURES FINISHED',flush=True)
if __name__=='__main__':
 mode=sys.argv[1]
 try:
  {'models':models,'simulate':simulate,'figures':figures}[mode]()
 finally:
  if FIT_DIAGNOSTICS:save(mode+'_fit_diagnostics.json',FIT_DIAGNOSTICS)
