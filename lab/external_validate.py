"""One predeclared match-level validation comparison; never fits or retunes a model."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from lab.sportec_adapter import load_match
from lab.control_v5 import predict_calibrated
from lab.synthetic_benchmark import predict,score
from lab.external_train import slice_observation,corrupt
from evaluation import possession_metrics as pm

def validate(match='J03WPY'):
    protocol=json.loads((ROOT/'benchmarks/external/sportec/protocol.json').read_text())
    if match not in protocol['splits']['validation']:raise ValueError('This evaluator accepts only predeclared validation matches')
    configuration_path=ROOT/'models/possession_control_v5.json'
    configuration=json.loads(configuration_path.read_text())
    if configuration['provenance']['validation_matches_used']:raise ValueError('Candidate was not selected on development data alone')
    data=load_match(match,allow_validation=True)
    rows=[]
    for variant in ('native','masked35'):
        predictions={name:np.full(len(data.reference),'X',dtype='<U1') for name in ('baseline_smooth50','experimental_control_v2','possession_control_v5')}
        for period,a,b in data.observation.windows:
            observation=slice_observation(data.observation,a,b+1)
            if variant=='masked35':observation=corrupt(observation,2030+period)
            for name in predictions:
                labels=predict_calibrated(observation,configuration) if name=='possession_control_v5' else predict(observation,name)
                predictions[name][a:b+1]=labels
        for name,labels in predictions.items():
            values=score(data.reference,labels)
            metric=pm.evaluate(pm.label_codes(data.reference),pm.label_codes(labels),bootstrap_n=0)
            spells=metric['spell_f1'][.5]
            rows.append({'variant':variant,'model':name,**values,'matched_spells_iou50':spells['n_matched'],
                'false_spells_iou50':spells['n_spurious'],'missed_spells_iou50':spells['n_missed']})
            print(f'Validation {match} {variant:<8} {name:<26} spellF1 {values["spell_f1"]:.4f} macroF1 {values["macro_f1"]:.4f}',flush=True)
    gains={variant:next(r['spell_f1'] for r in rows if r['variant']==variant and r['model']=='possession_control_v5')-
                   next(r['spell_f1'] for r in rows if r['variant']==variant and r['model']=='experimental_control_v2') for variant in ('native','masked35')}
    supported=all(gain>=0 for gain in gains.values()) and any(gain>0 for gain in gains.values())
    verdict='Small validation-supported candidate; further match-level confirmation required.' if supported else 'Calibration did not consistently improve validation spellF1; retain unchanged v2.'
    folder=ROOT/'benchmarks/reports/external-validation'/match;folder.mkdir(parents=True,exist_ok=True)
    result={'match':match,'split':'predeclared validation','candidate_sha256':hashlib.sha256(configuration_path.read_bytes()).hexdigest(),
        'candidate':configuration,'audit':data.audit,'rows':rows,'spell_f1_gains_over_v2':gains,
        'candidate_nonregressing_on_both_variants':supported,'verdict':verdict,
        'held_out_matches_opened':False,'competition_ground_truth_used':False,
        'limitations':['One validation match, with a team also present in development.',
            'DFL reference and corrected tracking differ from competition data; scores are not comparable across datasets.',
            'Masked35 is a synthetic corruption condition, not a second independent match.',
            'Small gains on a single match do not establish statistical significance or competition improvement.']}
    (folder/'evaluation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    lines=['# Hackathon-aligned external validation','',f'Validation match: {match}. Candidate frozen before its tracking and labels were downloaded.',
        'Primary criterion: unchanged official possession spellF1. macroF1 is secondary. No parameters are fit or selected by this evaluator.', '',
        '| Input | Model | spellF1 | macroF1 | D F1 | Matched spells @ IoU .5 | False spells | Missed spells |',
        '|---|---|---:|---:|---:|---:|---:|---:|']
    for r in rows:
        lines.append(f"| {r['variant']} | {r['model']} | {r['spell_f1']:.4f} | {r['macro_f1']:.4f} | {r['dead_f1']:.4f} | {r['matched_spells_iou50']} | {r['false_spells_iou50']} | {r['missed_spells_iou50']} |")
    lines+=['','## Decision','',verdict,'',*['- '+v for v in result['limitations']], '',
        'The sequence-emission v3 candidate and learned gap-fill v4 experiment remain research artifacts; neither is presented as a gain over v2 in the hackathon ranking metric.',
        'The v5 calibration changes only the settled-far-ball confirmation duration. It was selected from a fixed, bounded set of single-parameter alternatives on a different development match.',
        'Final held-out matches remain untouched. No competition public labels were used for training, calibration or selection.']
    (folder/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(verdict,flush=True)
    return result

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--match',default='J03WPY')
    validate(parser.parse_args().match)
