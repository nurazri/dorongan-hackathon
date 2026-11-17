"""Choose an abstention-fill gate on first-half external development data only."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from lab.sportec_adapter import load_match
from lab.external_train import slice_observation,corrupt
from lab.sequence_v3 import load_model
from lab.gapfill_v4 import predict_gapfill
from lab.synthetic_benchmark import score

THRESHOLDS=(.55,.70,.85,1.01)  # >1 is unchanged v2; a required no-change control.

def calibrate(match='J03WOH'):
    data=load_match(match);model=load_model(ROOT/'models/possession_sequence_v3.json')
    _,a,b=next(w for w in data.observation.windows if w[0]==1)
    cut=a+int((b-a+1)*.7)
    native=slice_observation(data.observation,cut,b+1)
    variants={'native':native,'masked35':corrupt(native,2028)}
    trials=[]
    for threshold in THRESHOLDS:
        config={'threshold':threshold,'confirmation_s':.4,'emission_model':model}
        rows={name:score(data.reference[cut:b+1],predict_gapfill(obs,config)) for name,obs in variants.items()}
        trials.append({'threshold':threshold,'mean_spell_f1':float(np.mean([r['spell_f1'] for r in rows.values()])),
            'mean_macro_f1':float(np.mean([r['macro_f1'] for r in rows.values()])),'variants':rows})
    winner=max(trials,key=lambda row:(row['mean_spell_f1'],row['mean_macro_f1'],row['threshold']))
    baseline=next(row for row in trials if row['threshold']>1)
    configuration={'model':'possession_gapfill_v4','threshold':winner['threshold'],'confirmation_s':.4,
        'emission_model':model,'provenance':{'external_match':match,'tuning_array_range':[cut,b+1],
            'selection_objective':'mean official spellF1; macroF1 tie-break; unchanged v2 included as control',
            'second_half_used_for_gate_selection':False,'competition_labels_used':False,
            'candidate_thresholds':list(THRESHOLDS),'base_model_source_sha256':hashlib.sha256((ROOT/'lab/control_v2.py').read_bytes()).hexdigest(),
            'development_gain_over_unchanged_v2':winner['mean_spell_f1']-baseline['mean_spell_f1'],
            'caveat':'Designed after viewing development diagnostics; requires independent match-level validation.'}}
    (ROOT/'models/possession_gapfill_v4.json').write_text(json.dumps(configuration,indent=2),encoding='utf-8')
    folder=ROOT/'benchmarks/reports/external-development'
    (folder/'gapfill-selection.json').write_text(json.dumps({'trials':trials,'winner':winner,'control':baseline},indent=2),encoding='utf-8')
    print(json.dumps({'selected_threshold':winner['threshold'],'development_spell_f1':winner['mean_spell_f1'],
        'unchanged_v2_spell_f1':baseline['mean_spell_f1'],'gain':winner['mean_spell_f1']-baseline['mean_spell_f1']},indent=2),flush=True)

if __name__=='__main__':calibrate()
