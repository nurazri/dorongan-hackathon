"""Fixed v6 ablations on external development; freeze before validation."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from lab.sportec_adapter import load_match
from lab.external_train import slice_observation,corrupt
from lab.control_v5 import predict_calibrated
from lab.synthetic_benchmark import score
from lab.synthetic_scenarios import Observation,FAMILIES,SPLITS,make_scenario
from evaluation import possession_metrics as pm
from lab.control_v6 import predict_v6
OUT=ROOT/'benchmarks/reports/control-v6'
OUT.mkdir(parents=True,exist_ok=True)
CONFIG=ROOT/'models/possession_control_v6.json'
BASE=json.loads((ROOT/'models/possession_control_v5.json').read_text())
STRATEGIES={
    'motion_only':{'path_motion':True,'neutral_tolerance_s':0.0},
    'tolerant_only':{'path_motion':False,'neutral_tolerance_s':0.08},
    'combined':{'path_motion':True,'neutral_tolerance_s':0.08},
}

def metric(truth,labels):
    values=score(truth,labels)
    detail=pm.evaluate(pm.label_codes(truth),pm.label_codes(labels),bootstrap_n=0)['spell_f1'][.5]
    return {**values,'matched_spells_iou50':detail['n_matched'],
        'false_spells_iou50':detail['n_spurious'],'missed_spells_iou50':detail['n_missed']}

def select():
    data=load_match('J03WOH')
    _,a,b=next(w for w in data.observation.windows if w[0]==1)
    cut=a+int((b-a+1)*.7)
    native=slice_observation(data.observation,cut,b+1)
    variants={'native':native,'masked35':corrupt(native,2028)}
    trials=[]
    for name in ('v5',*STRATEGIES):
        config={'parameters':BASE['parameters'],'strategy':STRATEGIES.get(name,{})}
        rows={variant:metric(data.reference[cut:b+1],predict_calibrated(o,BASE) if name=='v5' else predict_v6(o,config)) for variant,o in variants.items()}
        trial={'name':name,'variants':rows,'mean_spell_f1':float(np.mean([r['spell_f1'] for r in rows.values()])),
               'mean_macro_f1':float(np.mean([r['macro_f1'] for r in rows.values()]))}
        trials.append(trial);print(name,trial['mean_spell_f1'],flush=True)
    # Select an actual experimental strategy; v5 remains the promotion control.
    winner=max(trials[1:],key=lambda t:(t['mean_spell_f1'],t['mean_macro_f1']))
    config={'model':'possession_control_v6','parameters':BASE['parameters'],'strategy':STRATEGIES[winner['name']],
        'provenance':{'development_match':'J03WOH','tuning_array_range':[cut,b+1],
            'selected_ablation':winner['name'],'candidate_count':3,'v5_control_included':True,
            'selection_objective':'mean official spellF1 over native and masked35; macroF1 tie-break',
            'competition_labels_used':False,'validation_matches_used_for_selection':False,'held_out_matches_used':False,
            'existing_validation_results_seen_before_v6_design':True,
            'source_sha256':hashlib.sha256((ROOT/'lab/control_v6.py').read_bytes()).hexdigest(),
            'development_gain_over_v5':winner['mean_spell_f1']-trials[0]['mean_spell_f1']}}
    CONFIG.write_text(json.dumps(config,indent=2))
    (OUT/'selection.json').write_text(json.dumps({'trials':trials,'selected':winner['name']},indent=2))
    print('FROZEN',winner['name'],flush=True)

def variants(o,period):
    yield 'native',o
    yield 'masked35',corrupt(o,2030+period)
    rng=np.random.default_rng(6030+period)
    mask=rng.random(len(o.ball))<.10
    ball=o.ball.copy();near=o.nearest.copy();ball[mask]=np.nan;near[mask]=np.inf
    yield 'dropout10',Observation(ball,near,(),o.windows,o.fps,o.pitch)
    # Isolated geometric spikes; distances are unknown at corrupted locations.
    ball=o.ball.copy();near=o.nearest.copy();spikes=rng.random(len(ball))<.005
    ball[spikes]+=rng.normal(0,.1,(int(spikes.sum()),2));near[spikes]=np.inf
    yield 'spikes005',Observation(ball,near,(),o.windows,o.fps,o.pitch)

def evaluate():
    config=json.loads(CONFIG.read_text())
    assert config['provenance']['source_sha256']==hashlib.sha256((ROOT/'lab/control_v6.py').read_bytes()).hexdigest()
    rows=[]
    for match in ('J03WOH','J03WPY','J03WR9'):
        data=load_match(match,allow_validation=match!='J03WOH')
        predictions={}
        for period,a,b in data.observation.windows:
            if match=='J03WOH' and period!=2:continue
            o=slice_observation(data.observation,a,b+1)
            for variant,obs in variants(o,period):
                for model in ('v5','v6'):
                    labels= predict_calibrated(obs,BASE) if model=='v5' else predict_v6(obs,config)
                    key=(variant,model)
                    if key not in predictions:predictions[key]=np.full(len(data.reference),'X',dtype='<U1')
                    predictions[key][a:b+1]=labels
        truth=data.reference.copy()
        if match=='J03WOH':
            for period,a,b in data.observation.windows:
                if period!=2:truth[a:b+1]='X'
        for (variant,model),labels in predictions.items():
            values=metric(truth,labels)
            rows.append({'match':match,'variant':variant,'model':model,**values})
            print(match,variant,model,f"spellF1={values['spell_f1']:.4f} macroF1={values['macro_f1']:.4f}",flush=True)
    gains=[]
    for match in ('J03WPY','J03WR9'):
        for variant in ('native','masked35'):
            get=lambda model:next(r for r in rows if r['match']==match and r['variant']==variant and r['model']==model)
            gains.append({'match':match,'variant':variant,'spell_f1_gain':get('v6')['spell_f1']-get('v5')['spell_f1']})
    dev=config['provenance']['development_gain_over_v5']
    promote=dev>0 and all(g['spell_f1_gain']>=0 for g in gains) and any(g['spell_f1_gain']>0 for g in gains)
    result={'candidate':config,'rows':rows,'validation_gains':gains,'promote':promote,
        'promotion_rule':'Development gain > 0; no spellF1 regressions in either match under native/masked35; at least one positive validation gain.',
        'held_out_matches_opened':False,'competition_labels_read':False,
        'limitation':'Reused validation matches; conditional evidence, not fresh held-out confirmation. Corruptions are not independent games.'}
    (OUT/'evaluation.json').write_text(json.dumps(result,indent=2))
    print('PROMOTE',promote,flush=True)

def synthetic():
    config=json.loads(CONFIG.read_text());rows=[]
    for family in FAMILIES:
        for seed in SPLITS['validation']:
            scene=make_scenario(family,seed)
            for model in ('v5','v6'):
                labels=predict_calibrated(scene.observation,BASE) if model=='v5' else predict_v6(scene.observation,config)
                rows.append({'family':family,'seed':seed,'model':model,**score(scene.truth,labels)})
    means={m:float(np.mean([r['spell_f1'] for r in rows if r['model']==m])) for m in ('v5','v6')}
    (OUT/'synthetic.json').write_text(json.dumps({'rows':rows,'mean_spell_f1':means},indent=2))
    print('Synthetic validation',means,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['select','evaluate','synthetic']);args=p.parse_args()
    {'select':select,'evaluate':evaluate,'synthetic':synthetic}[args.mode]()
