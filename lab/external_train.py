"""External-only learning; objective is possession spellF1 on development tuning data."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from lab.sportec_adapter import load_match
from lab.synthetic_scenarios import Observation
from lab.synthetic_benchmark import score
from lab.sequence_v3 import features,fit_emissions,transition_model,predict_sequence

SCALES=(.5,1.,2.,4.)

def slice_observation(o,a,b):
    return Observation(o.ball[a:b],o.nearest[a:b],(),((1,0,b-a-1),),o.fps,o.pitch)

def corrupt(o,seed,fraction=.35):
    # Synthetic observation corruption has no access to possession labels.
    rng=np.random.default_rng(seed);mask=np.zeros(len(o.ball),dtype=bool)
    target=int(len(mask)*fraction)
    while int(mask.sum())<target:
        a=int(rng.integers(0,len(mask)));duration=int(rng.integers(max(1,round(.3*o.fps)),round(3*o.fps)+1))
        mask[a:min(len(mask),a+duration)]=True
    ball=o.ball.copy();nearest=o.nearest.copy()
    ball[mask]=np.nan;nearest[mask]=np.inf
    return Observation(ball,nearest,(),o.windows,o.fps,o.pitch)

def train(match='J03WOH'):
    data=load_match(match)
    first=next(w for w in data.observation.windows if w[0]==1)
    _,a,b=first;cut=a+int((b-a+1)*.7)
    native_train=slice_observation(data.observation,a,cut)
    native_tune=slice_observation(data.observation,cut,b+1)
    augmented=corrupt(native_train,2027)
    x=np.concatenate([features(native_train),features(augmented)])
    y=np.tile(data.reference[a:cut],2)
    print(f'Fit external emissions: {len(x)} rows; features use positions only',flush=True)
    model=fit_emissions(x,y)
    transition,prior=transition_model(data.reference[a:cut])
    model.update({'model':'possession_sequence_v3','log_transition':transition.tolist(),'log_prior':prior.tolist(),'transition_scale':1.})
    tuning_variants={'native':native_tune,'masked35':corrupt(native_tune,2028)}
    trials=[]
    for scale in SCALES:
        rows={name:score(data.reference[cut:b+1],predict_sequence(obs,model,scale)) for name,obs in tuning_variants.items()}
        objective=float(np.mean([v['spell_f1'] for v in rows.values()]))
        tie_break=float(np.mean([v['macro_f1'] for v in rows.values()]))
        trials.append({'transition_scale':scale,'mean_spell_f1':objective,'mean_macro_f1':tie_break,'variants':rows})
    chosen=max(trials,key=lambda row:(row['mean_spell_f1'],row['mean_macro_f1'],-row['transition_scale']))
    model['transition_scale']=chosen['transition_scale']
    protocol=json.loads((ROOT/'benchmarks/external/sportec/protocol.json').read_text())
    model['provenance']={
        'source_doi':protocol['source_doi'],'attribution':protocol['attribution'],'license':protocol['license'],
        'external_match':match,'training_period':1,'training_array_range':[a,cut],
        'tuning_array_range':[cut,b+1],'training_native_frames':cut-a,'training_rows_including_corruption':len(x),
        'augmentation':'native + label-independent 35% block occlusion; seed 2027; durations .3..3 s',
        'selection_objective':'mean official spellF1 over native and masked35 first-half tuning region; macroF1 tie-break',
        'candidate_transition_scales':list(SCALES),'tuning_corruption_seed':2028,
        'second_half_used_for_fit_or_selection':False,'competition_data_used_for_fit_or_selection':False,
        'model_source_sha256':hashlib.sha256((ROOT/'lab/sequence_v3.py').read_bytes()).hexdigest(),
        'tracking_md5':next(f['computed_md5'] for f in protocol['files'] if f['match_id']==match and 'positions_raw_observed' in f['name']),
    }
    folder=ROOT/'models';folder.mkdir(exist_ok=True)
    destination=folder/'possession_sequence_v3.json'
    destination.write_text(json.dumps(model,indent=2,allow_nan=False),encoding='utf-8')
    report=ROOT/'benchmarks/reports/external-development';report.mkdir(parents=True,exist_ok=True)
    (report/'selection.json').write_text(json.dumps({'match':match,'trials':trials,'selected':chosen,
        'note':'First-half development selection only. Second half not read for selection.'},indent=2,allow_nan=False),encoding='utf-8')
    print(f'Frozen transition scale {chosen["transition_scale"]}; development tuning spellF1 {chosen["mean_spell_f1"]:.4f}',flush=True)
    print(f'Model: {destination}',flush=True)
    return model

if __name__=='__main__':
    train()
