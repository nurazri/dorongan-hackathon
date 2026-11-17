"""Deterministic experimental possession model and local inspection cache.

No ground truth is read here. Parameters are engineering assumptions, not fitted scores.
"""
import hashlib
import json
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from games import GAMES, GAME, asset_paths, half_video_blocks
from starter.load_smart_tagging import load as load_tags
from starter.baseline import team_of_each_track, write_submission
from lab.control_v2 import infer_control, PARAMETERS as CONTROL_PARAMETERS

from lab.temporal_v1 import decode, infer_temporal, PARAMETERS

def build():
    paths = asset_paths()
    n = GAMES[GAME]['n_video_frames']
    teams = team_of_each_track(paths['atd_meta'])
    xy = np.full((n, len(teams)+1, 2), np.nan, dtype=np.float32)
    seen = np.zeros(n, dtype=bool)
    with open(paths['atd_raw']) as stream:
        for line in stream:
            index, players, ball = line.strip().split(':')
            i = int(index)-1
            if not 0 <= i < n or seen[i]:
                raise ValueError('Duplicate or invalid tracking frame')
            groups = players.split(';') + [ball]
            if len(groups) != len(teams)+1:
                raise ValueError('Track count disagrees with metadata')
            xy[i] = [[float(v) for v in g.split(',')[:2]] for g in groups]
            seen[i] = True
    if not seen.all():
        raise ValueError('Tracking frames missing')
    ball_present = np.isfinite(xy[:, -1]).all(axis=1)
    scale = np.array(GAMES[GAME]['pitch'])
    delta = (xy[:, :-1] - xy[:, -1:, :]) * scale
    distance = np.sqrt(np.sum(delta**2, axis=2))
    distance[~np.isfinite(distance)] = np.inf
    nearest = np.column_stack([distance[:, teams == team].min(axis=1) for team in (0, 1)])
    events = load_tags()
    labels, emission, velocity = infer_temporal(xy[:, -1], nearest, events, half_video_blocks(GAME),
                                               fps=GAMES[GAME]['fps'], pitch=GAMES[GAME]['pitch'])
    # Published pre-kickoff interval in the second graded half is dead ball.
    labels[110808:113742] = 'D'
    results = ROOT / 'evaluation/results'
    results.mkdir(exist_ok=True)
    destination = results / 'experimental_temporal.csv'
    write_submission(str(destination), labels)
    # Independently specified control/stoppage candidate; v1 is retained unchanged.
    control_labels, control_evidence, audit = infer_control(
        xy[:, -1], nearest, events, half_video_blocks(GAME),
        fps=GAMES[GAME]['fps'], pitch=GAMES[GAME]['pitch'])
    control_labels[110808:113742] = 'D'  # Published pre-kickoff metadata.
    write_submission(str(results/'experimental_control_v2.csv'), control_labels)
    # Frozen calibration from OTHER matches; competition labels are never read.
    config_path = ROOT/'models/possession_control_v5.json'
    if config_path.exists():
        from lab.control_v5 import predict_calibrated
        from lab.synthetic_scenarios import Observation
        config = json.loads(config_path.read_text(encoding='utf-8'))
        calibrated = predict_calibrated(Observation(xy[:, -1], nearest, tuple(events),
            tuple(half_video_blocks(GAME)), GAMES[GAME]['fps'], tuple(GAMES[GAME]['pitch'])), config)
        calibrated[110808:113742] = 'D'
        write_submission(str(results/'experimental_control_v5.csv'), calibrated)
    cache = ROOT / '.local'
    cache.mkdir(exist_ok=True)
    np.savez_compressed(cache/'tracking.pending.npz', xy=xy, teams=teams, ball_present=ball_present,
                        nearest=nearest, velocity=velocity, emission=emission, **control_evidence)
    (cache/'tracking.pending.npz').replace(cache/'tracking.npz')
    models = {}
    for path in sorted(results.glob('*.csv')):
        rows = np.loadtxt(path, delimiter=',', skiprows=1, usecols=1, dtype='<U1')
        if len(rows) != n:
            continue
        starts = np.r_[0, np.flatnonzero(rows[1:] != rows[:-1])+1]
        ends = np.r_[starts[1:], n]
        models[path.stem] = {'segments': [[int(a), int(b), str(rows[a])] for a,b in zip(starts,ends)],
                             'counts': {label: int((rows == label).sum()) for label in 'HADX'},
                             'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    summary = {'frames': n, 'fps': 25, 'ballPresent': int(ball_present.sum()),
               'trackSlots': len(teams), 'models': models, 'events': events,
               'parameters': PARAMETERS, 'controlParameters': CONTROL_PARAMETERS, 'status': 'Experimental; improvement over baseline is unverified.'}
    (cache/'summary.pending.json').write_text(json.dumps(summary), encoding='utf-8')
    (cache/'summary.pending.json').replace(cache/'summary.json')
    diagnostics = {
        'model': 'experimental_control_v2', 'parameters': CONTROL_PARAMETERS,
        'counts': models['experimental_control_v2']['counts'],
        'sha256': models['experimental_control_v2']['sha256'],
        'decisionCounts': {reason: sum(e['reason']==reason for e in audit) for reason in sorted({e['reason'] for e in audit})},
        'decisions': audit,
        'validation': 'Synthetic behavior and CSV contract only. No public ground-truth scoring or parameter tuning.',
    }
    (cache/'control_v2_diagnostics.json').write_text(json.dumps(diagnostics, indent=2), encoding='utf-8')
    print(json.dumps({key:value for key,value in diagnostics.items() if key not in ('decisions','parameters')}, indent=2))
    print(json.dumps({'submission': str(destination), 'sha256': models['experimental_temporal']['sha256'],
                      'frames': n, 'ball_present': int(ball_present.sum())}, indent=2))

if __name__ == '__main__':
    build()
