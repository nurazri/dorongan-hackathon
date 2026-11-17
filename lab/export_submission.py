"""Reproduce the frozen Control v5 submission without UI caches or external labels."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from games import GAME, GAMES, asset_paths, half_video_blocks, require
from starter.baseline import team_of_each_track
from starter.load_smart_tagging import load as load_tags
from lab.control_v5 import predict_calibrated
from lab.synthetic_scenarios import Observation
from evaluation import possession_metrics as pm

EXPECTED_SHA256 = '0c9d0d83918031d97ba8d557ce863145b585e80894163c6a569c23f234d8969d'


def write_frozen_csv(path, labels):
    """Explicit CRLF reproduces the frozen Windows bytes on every OS."""
    with open(path, 'w', encoding='utf-8', newline='') as stream:
        stream.write('frame,label\r\n')
        stream.writelines(f'{frame},{label}\r\n' for frame, label in enumerate(labels))


def load_tracking(raw_path, teams, n):
    """Preserve build.py's float32 geometry and reject malformed frame contracts."""
    xy = np.full((n, len(teams)+1, 2), np.nan, dtype=np.float32)
    seen = np.zeros(n, dtype=bool)
    with open(raw_path) as stream:
        for line in stream:
            index, players, ball = line.strip().split(':')
            i = int(index)-1
            if not 0 <= i < n or seen[i]:
                raise ValueError('Duplicate or invalid tracking frame')
            groups = players.split(';') + [ball]
            if len(groups) != len(teams)+1:
                raise ValueError('Track count disagrees with metadata')
            xy[i] = [[float(v) for v in group.split(',')[:2]] for group in groups]
            seen[i] = True
    if not seen.all():
        raise ValueError('Tracking frames missing')
    return xy


def generate(output, data_dir=None):
    require(['atd_meta', 'atd_raw', 'smart_tagging'], data_dir=data_dir)
    paths = asset_paths(data_dir=data_dir)
    metadata = GAMES[GAME]
    teams = team_of_each_track(paths['atd_meta'])
    xy = load_tracking(paths['atd_raw'], teams, metadata['n_video_frames'])
    delta = (xy[:, :-1] - xy[:, -1:, :]) * np.array(metadata['pitch'])
    distance = np.sqrt(np.sum(delta**2, axis=2))
    distance[~np.isfinite(distance)] = np.inf
    nearest = np.column_stack([distance[:, teams == team].min(axis=1) for team in (0, 1)])
    configuration = json.loads((ROOT/'models/possession_control_v5.json').read_text(encoding='utf-8'))
    observation = Observation(xy[:, -1], nearest, tuple(load_tags(data_dir=data_dir)),
        tuple(half_video_blocks(GAME)), metadata['fps'], tuple(metadata['pitch']))
    labels = predict_calibrated(observation, configuration)
    labels[110808:113742] = 'D'  # Organiser-published second-half pre-kickoff interval.
    output = Path(output).resolve()
    protected = [Path(paths[key]).resolve() for key in ('atd_meta', 'atd_raw', 'smart_tagging')]
    if output in protected:
        raise ValueError('Output must not overwrite a match input')
    output.parent.mkdir(parents=True, exist_ok=True)
    # Validate and verify a temporary file before replacing any existing submission.
    with tempfile.TemporaryDirectory(prefix='v5-export-') as scratch:
        candidate = Path(scratch)/'submission.csv'
        write_frozen_csv(candidate, labels)
        reason = pm.validate_submission(pm.read_label_csv(str(candidate)), metadata['n_video_frames'])
        if reason:
            raise ValueError(reason)
        payload = candidate.read_bytes()
        digest = hashlib.sha256(payload).hexdigest()
        if digest != EXPECTED_SHA256:
            raise ValueError(f'Frozen submission mismatch: expected {EXPECTED_SHA256}, got {digest}')
        output.write_bytes(payload)
    result = {'model': 'Control v5', 'rows': len(labels), 'sha256': digest,
        'output': str(output), 'official_format_validation': 'passed'}
    print(json.dumps(result, indent=2))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, help='Destination team-named CSV')
    parser.add_argument('--data-dir', help='Bundle root containing tactical/BAR-ATH_tactical_* files')
    args = parser.parse_args()
    generate(args.output, args.data_dir)
