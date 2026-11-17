"""Reproducible synthetic scoring harness, isolated from all competition match assets."""
import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from evaluation import possession_metrics as pm
from starter.baseline import smooth
from lab.temporal_v1 import infer_temporal
from lab.control_v2 import infer_control
from lab.synthetic_scenarios import FAMILIES,SPLITS,FRAMES,make_scenario,fingerprint,rle

MODELS=('baseline_raw','baseline_smooth25','baseline_smooth50','baseline_smooth125',
        'experimental_temporal','experimental_control_v2')

def predict(observation,model):
    """Observation deliberately has no reference-label field or filesystem path."""
    o=observation
    if model.startswith('baseline_'):
        codes=np.full(len(o.ball),-1,dtype=np.int8)
        available=np.isfinite(o.ball).all(axis=1)&np.isfinite(o.nearest).any(axis=1)
        codes[available]=o.nearest[available].argmin(axis=1)
        window=0 if model=='baseline_raw' else int(model.removeprefix('baseline_smooth'))
        return smooth(codes,window)
    if model=='experimental_temporal':
        return infer_temporal(o.ball,o.nearest,o.events,o.windows,o.fps,o.pitch)[0]
    if model=='experimental_control_v2':
        return infer_control(o.ball,o.nearest,o.events,o.windows,o.fps,o.pitch)[0]
    raise ValueError(f'Unknown model: {model}')

def score(truth,prediction,fps=25):
    if len(truth)!=len(prediction):
        raise ValueError('Prediction length mismatch')
    metrics=pm.evaluate(pm.label_codes(truth),pm.label_codes(prediction),bootstrap_n=0)
    trans=metrics['transitions'][25]
    graded=truth!='X'
    coverage=float((prediction[graded]!='X').mean())
    return {'spell_f1':metrics['spell_f1_mean'],'macro_f1':metrics['macro_f1'],
            'dead_f1':metrics['per_class']['D']['f1'],'coverage':coverage,
            'transition_f1_12f':metrics['transitions'][12]['f1'],
            'transition_f1_25f':trans['f1'],'matched_transitions':trans['n_matched'],
            'true_transitions':trans['n_gt'],'predicted_transitions':trans['n_pred'],
            'boundary_mae_ms':None if trans['mean_abs_latency'] is None else trans['mean_abs_latency']/fps*1000,
            'signed_latency_ms':None if trans['mean_latency'] is None else trans['mean_latency']/fps*1000,
            'true_possessions':metrics['n_gt_spells'],'predicted_possessions':metrics['n_pred_spells']}

def aggregate(rows):
    out={'cases':len(rows)}
    for key in ('spell_f1','macro_f1','dead_f1','coverage','transition_f1_12f','transition_f1_25f'):
        values=np.array([row[key] for row in rows])
        out[key]=float(values.mean())
        out[key+'_case_sd']=float(values.std())
    matched=sum(row['matched_transitions'] for row in rows)
    out['matched_transitions']=matched
    out['true_transitions']=sum(row['true_transitions'] for row in rows)
    out['predicted_transitions']=sum(row['predicted_transitions'] for row in rows)
    out['boundary_mae_ms']=sum((row['boundary_mae_ms'] or 0)*row['matched_transitions'] for row in rows)/matched if matched else None
    return out

def run(output,split='all'):
    output=Path(output)
    output.mkdir(parents=True,exist_ok=True)
    chosen=SPLITS if split=='all' else {split:SPLITS[split]}
    rows=[]
    cases=[]
    digest=hashlib.sha256()
    for partition,seeds in chosen.items():
        for family in FAMILIES:
            for seed in seeds:
                scene=make_scenario(family,seed)
                case_id=f'{partition}/{family}/{seed}'
                observation_hash=fingerprint(scene.observation)
                digest.update(case_id.encode()+observation_hash.encode()+scene.truth.tobytes())
                case={'id':case_id,'split':partition,'family':family,'seed':seed,
                      'observation_sha256':observation_hash,'truth':rle(scene.truth),
                      'conditions':{k:int(v.sum()) for k,v in scene.conditions.items()},'predictions':{}}
                for model in MODELS:
                    labels=predict(scene.observation,model)
                    row={'split':partition,'family':family,'seed':seed,'model':model,
                         **score(scene.truth,labels,scene.observation.fps)}
                    rows.append(row)
                    case['predictions'][model]=rle(labels)
                cases.append(case)
    groups={partition:{model:aggregate([r for r in rows if r['split']==partition and r['model']==model])
                       for model in MODELS} for partition in chosen}
    family_groups={partition:{family:{model:aggregate([r for r in rows if r['split']==partition and r['family']==family and r['model']==model])
                                     for model in MODELS} for family in FAMILIES} for partition in chosen}
    manifest={'benchmark':'synthetic-possession-v1','fps':25,'frames_per_case':FRAMES,
              'scenario_families':list(FAMILIES),'splits':{k:list(v) for k,v in chosen.items()},
              'case_count':len(cases),'scored_rows':len(rows),'models':list(MODELS),
              'dataset_sha256':digest.hexdigest(),
              'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in
                  ('lab/synthetic_scenarios.py','lab/synthetic_benchmark.py','lab/temporal_v1.py','lab/control_v2.py','starter/baseline.py','evaluation/possession_metrics.py')},
              'competition_assets_read':False,
              'limitations':['Feature-level stress tests, not realistic match simulation.',
                'Validation seeds are disjoint, but scenario mechanisms are shared.',
                'Both ambiguous-referee cases have identical observations and different labels.',
                'No model parameters were changed in this benchmark run.',
                'Synthetic ordering does not predict competition ranking.']}
    summary={'manifest':manifest,'splits':groups,'families':family_groups}
    (output/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False),encoding='utf-8')
    (output/'cases.json').write_text(json.dumps(cases,allow_nan=False),encoding='utf-8')
    with (output/'scores.csv').open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    report=['# Synthetic possession benchmark v1','',
        f'{len(cases)} generated cases, {len(FAMILIES)} families, 25 fps, six frozen models. No competition assets or labels are loaded.',
        '', 'Scores are arithmetic means over cases, with equal family/seed weighting. spellF1 and frame/class scores use the unchanged official metric implementation.',
        'This benchmark measures behavior on generated feature traces. It does not establish real-match accuracy or justify selecting a competition submission.', '']
    for partition in chosen:
        report += [f'## {partition.title()}', '',
            '| Model | spellF1 | macroF1 | D F1 | Coverage | Transition F1 ±1 s | Matched / true transitions | Matched boundary MAE (ms) |',
            '|---|---:|---:|---:|---:|---:|---:|---:|']
        for model in MODELS:
            g=groups[partition][model]
            latency='—' if g['boundary_mae_ms'] is None else f"{g['boundary_mae_ms']:.1f}"
            report.append(f"| {model} | {g['spell_f1']:.3f} | {g['macro_f1']:.3f} | {g['dead_f1']:.3f} | {g['coverage']:.1%} | {g['transition_f1_25f']:.3f} | {g['matched_transitions']} / {g['true_transitions']} | {latency} |")
        report += ['', 'Boundary errors include only matched transitions within the stated tolerance. Missed transitions do not enter MAE; read the matched/true counts and transition F1 with it.', '']
    focus='validation' if 'validation' in chosen else next(iter(chosen))
    report += ['## Research models by scenario family', '',f'Split: {focus}. These are diagnostic comparisons, not model selection on real match data.', '',
               '| Family | V1 spellF1 | V2 spellF1 | V2 D F1 | V2 coverage |','|---|---:|---:|---:|---:|']
    for family in FAMILIES:
        one=family_groups[focus][family]['experimental_temporal']
        two=family_groups[focus][family]['experimental_control_v2']
        report.append(f"| {family} | {one['spell_f1']:.3f} | {two['spell_f1']:.3f} | {two['dead_f1']:.3f} | {two['coverage']:.1%} |")
    report += ['', '## Failure cases to reproduce','', 'Lowest spellF1 cases for Control v2 in the reported diagnostic split:', '', '| Family | Seed | spellF1 | Coverage |','|---|---:|---:|---:|']
    worst=sorted((r for r in rows if r['split']==focus and r['model']=='experimental_control_v2'),key=lambda r:(r['spell_f1'],r['family'],r['seed']))[:10]
    for row in worst:
        report.append(f"| {row['family']} | {row['seed']} | {row['spell_f1']:.3f} | {row['coverage']:.1%} |")
    report += ['', 'Replay any case with `npm run benchmark -- --case FAMILY --seed SEED`. This prints synthetic truth and prediction segments only.', '',
        '## Protocol and interpretation','',
        '- Development seeds: 0–5. Validation seeds: 100–105. The suite was specified before the first scoring run.',
        '- Both seed sets are reported openly. Further changes based on validation results make this a regression set; use fresh cases and independent matches for later evaluation.',
        '- The paired referee scenarios intentionally cannot both be solved from their identical observations. They reveal missing information rather than a tunable threshold.',
        '- Some passes, duels and restarts include simplified discontinuities. These are feature stress tests, not rendered or physically validated football.',
        '- clean_control means uncorrupted observations, not guaranteed close contact. Its generator permits nearest-team distances up to 3.8 m while prescribing team possession. Zero scores in such a case expose a modeling-assumption mismatch, not proof that close-control thresholds are wrong in real football.',
        '- Case-to-case standard deviations in summary.json are variability measures, not statistical confidence intervals.',
        '- Do not tune on competition public labels. Do not infer real possession counts from these generated schedules.', '',
        f"Dataset fingerprint: `{manifest['dataset_sha256']}`.", '',
        'Source fingerprints, per-case scores, truth/prediction segments and corruption counts are in summary.json, scores.csv and cases.json. No competition frames appear in these files.']
    (output/'report.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    print(f'Synthetic benchmark: {len(cases)} cases / {len(rows)} model-case scores')
    for model,g in groups[focus].items():
        print(f"{model:<26} spellF1 {g['spell_f1']:.3f}  macroF1 {g['macro_f1']:.3f}  coverage {g['coverage']:.1%}")
    print(f'Report: {output.resolve()/"report.md"}')
    return summary

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--split',choices=['all',*SPLITS],default='all')
    parser.add_argument('--output',default=str(ROOT/'benchmarks/reports/synthetic-v1'))
    parser.add_argument('--case',choices=FAMILIES)
    parser.add_argument('--seed',type=int,default=100)
    args=parser.parse_args()
    if args.case:
        case=make_scenario(args.case,args.seed)
        print(json.dumps({'family':args.case,'seed':args.seed,'truth':rle(case.truth),
                          'predictions':{m:rle(predict(case.observation,m)) for m in MODELS}},indent=2))
    else:
        run(args.output,args.split)

if __name__=='__main__':
    main()
