"""Compare frozen possession models on external development data, ranking by spellF1."""
import csv
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from lab.sportec_adapter import load_match
from lab.synthetic_benchmark import MODELS,predict,score
from lab.external_train import slice_observation,corrupt
from lab.sequence_v3 import predict_sequence,load_model
from evaluation import possession_metrics as pm

def evaluate(match='J03WOH'):
    data=load_match(match)
    model_path=ROOT/'models/possession_sequence_v3.json'
    learned=load_model(model_path)
    # Model was frozen on a first-half split before this second-half diagnostic.
    if learned['provenance']['external_match']!=match:raise ValueError('Unexpected trained-match provenance')
    folder=ROOT/'benchmarks/reports/external-development';folder.mkdir(parents=True,exist_ok=True)
    rows=[]
    for period,a,b in data.observation.windows:
        native=slice_observation(data.observation,a,b+1)
        truth=data.reference[a:b+1]
        for variant,observation in {'native':native,'masked35':corrupt(native,2029+period)}.items():
            for name in (*MODELS,'possession_sequence_v3'):
                prediction=predict_sequence(observation,learned) if name=='possession_sequence_v3' else predict(observation,name)
                values=score(truth,prediction)
                metric=pm.evaluate(pm.label_codes(truth),pm.label_codes(prediction),bootstrap_n=0)
                spells=metric['spell_f1'][.5]
                row={'match':match,'period':period,'variant':variant,'model':name,**values,
                    'matched_spells_iou50':spells['n_matched'],'false_spells_iou50':spells['n_spurious'],
                    'missed_spells_iou50':spells['n_missed'],'spell_precision_iou50':spells['precision'],
                    'spell_recall_iou50':spells['recall']}
                rows.append(row)
                print(f'External half {period} {variant:<8} {name:<26} spellF1 {row["spell_f1"]:.4f} macroF1 {row["macro_f1"]:.4f}',flush=True)
    summary={'dataset':'Sportec/IDSSE external development match','match':match,'source_doi':learned['provenance']['source_doi'],
        'audit':data.audit,'model_sha256':hashlib.sha256(model_path.read_bytes()).hexdigest(),
        'selection':'Only first-half training/tuning. No second-half refit or reselection.',
        'limitations':['One external development match; not the predeclared match-level validation or held-out split.',
            'Corrected external tracking and label semantics differ from automatic competition tracking.',
            'Masked35 is label-independent synthetic observation corruption, not proof of competition robustness.'],
        'rows':rows}
    (folder/'evaluation.json').write_text(json.dumps(summary,indent=2,allow_nan=False),encoding='utf-8')
    with (folder/'scores.csv').open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    report=['# External development evaluation: possession recovery','',
        f'Match {match}, other than the competition match. The objective is official spellF1; macroF1 is secondary.',
        'The first half supplies training/tuning for v3. Its second half was withheld from fitting and transition-penalty selection.',
        'This is a within-development-match temporal diagnostic, not independent match-level confirmation.', '',
        '## Second-half diagnostic', '',
        '| Input | Model | spellF1 | macroF1 | D F1 | Coverage | Matched spells / true @ IoU .5 | False spells | Missed spells |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for row in rows:
        if row['period']!=2:continue
        report.append(f"| {row['variant']} | {row['model']} | {row['spell_f1']:.4f} | {row['macro_f1']:.4f} | {row['dead_f1']:.4f} | {row['coverage']:.1%} | {row['matched_spells_iou50']} / {row['true_possessions']} | {row['false_spells_iou50']} | {row['missed_spells_iou50']} |")
    report+=['', '## Alignment with the hackathon','',
        '- Predictions concern H/A/D possession states. The metric implementation is the unchanged official scorer.',
        '- Training inputs are ball/player geometry and temporal context only. BallStatus and BallPossession are reference-only fields.',
        '- Candidate transition scales were fixed before scoring and selected by first-half tuning spellF1, with macroF1 as a tie-break.',
        '- No competition public/private ground truth is loaded, and no labels or corrections are written by hand.',
        '- Competition CSV generation remains deterministic and goes through the official file validator.', '',
        '## Interpretation limits','',*['- '+s for s in summary['limitations']],
        '- V3 is a candidate until confirmed on predeclared validation matches. The published baseline remains the application default.',
        '- Masked35 removes blocks of ball observations without changing the external reference labels. Native and corrupted results must not be conflated.', '',
        f"Frozen model SHA-256: `{summary['model_sha256']}`.", '',
        'Reproduce: `npm run external:fetch`, `npm run external:prepare`, `npm run external:train`, `npm run external:evaluate`.',
        'Raw downloads and prepared arrays remain in ignored .local/. Weights and attributed provenance are in models/possession_sequence_v3.json.']
    (folder/'report.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    print(f'External report: {folder/"report.md"}',flush=True)
    return summary

if __name__=='__main__':evaluate()
