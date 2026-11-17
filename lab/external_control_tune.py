"""Bounded single-parameter calibration of v2, using external development spellF1."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from lab.control_v2 import infer_control,PARAMETERS
from lab.external_train import slice_observation,corrupt
from lab.sportec_adapter import load_match
from lab.synthetic_benchmark import score

CANDIDATES=[('unchanged_v2',{})]+[(f'{name}={value}',{name:value}) for name,values in (
    ('control_dwell_s',(.2,.6)),('control_advantage_m',(.4,1.2)),('restart_speed_mps',(.5,3.)),
    ('settled_far_dwell_s',(.75,2.5)),('outside_dwell_s',(.12,.4))) for value in values]

from lab.control_v5 import predict_calibrated

def tune(match='J03WOH'):
    data=load_match(match)
    _,a,b=next(w for w in data.observation.windows if w[0]==1)
    cut=a+int((b-a+1)*.7)
    native=slice_observation(data.observation,cut,b+1)
    variants={'native':native,'masked35':corrupt(native,2028)}
    trials=[]
    for index,(name,overrides) in enumerate(CANDIDATES):
        parameters={**PARAMETERS,**overrides}
        rows={key:score(data.reference[cut:b+1],predict_calibrated(obs,{'parameters':parameters})) for key,obs in variants.items()}
        trial={'candidate':name,'index':index,'overrides':overrides,'variants':rows,
               'mean_spell_f1':float(np.mean([r['spell_f1'] for r in rows.values()])),
               'mean_macro_f1':float(np.mean([r['macro_f1'] for r in rows.values()]))}
        trials.append(trial)
        print(f'External development {name:<30} spellF1 {trial["mean_spell_f1"]:.4f}',flush=True)
    selected=max(trials,key=lambda r:(r['mean_spell_f1'],r['mean_macro_f1'],-r['index']))
    model={'model':'possession_control_v5','parameters':{**PARAMETERS,**selected['overrides']},
        'provenance':{'external_match':match,'tuning_array_range':[cut,b+1],
            'selection_objective':'mean official spellF1 over native and masked35 development tuning; macroF1 tie-break',
            'candidate_count':len(CANDIDATES),'single_parameter_changes_only':True,
            'selected_candidate':selected['candidate'],'development_spell_f1':selected['mean_spell_f1'],
            'unchanged_v2_development_spell_f1':trials[0]['mean_spell_f1'],
            'competition_labels_used':False,'validation_matches_used':False,'held_out_matches_used':False,
            'external_protocol_sha256':hashlib.sha256((ROOT/'benchmarks/external/sportec/protocol.json').read_bytes()).hexdigest(),
            'source_doi':'10.6084/m9.figshare.28196177.v1',
            'attribution':json.loads((ROOT/'benchmarks/external/sportec/protocol.json').read_text())['attribution']}}
    folder=ROOT/'benchmarks/reports/external-development'
    (folder/'control-selection.json').write_text(json.dumps({'candidates':trials,'selected':selected},indent=2),encoding='utf-8')
    (ROOT/'models/possession_control_v5.json').write_text(json.dumps(model,indent=2),encoding='utf-8')
    print('Frozen control calibration: '+selected['candidate'],flush=True)

if __name__=='__main__':tune()
