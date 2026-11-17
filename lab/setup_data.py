"""Locate the enrolled participant's local download; never uploads match assets."""
import argparse
import json
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def setup(source):
    files = list(Path(source).rglob('*'))
    paths = {}
    for camera in ('tactical', 'broadcast'):
        for suffix in ('.mp4', '_atd.xml', '_atd.txt', '_homography.csv') + (('_smart_tagging.xml',) if camera == 'tactical' else ()):
            stem = 'BAR-ATH_' + camera
            matches = [p for p in files if p.is_file() and
                       (p.name.startswith(stem) and p.suffix == '.mp4' if suffix == '.mp4' else p.name == stem + suffix)]
            if len(matches) != 1:
                raise ValueError(f'Expected one {stem}{suffix}, found {len(matches)}')
            src = matches[0].resolve()
            dst = ROOT / 'data' / camera / (stem + suffix)
            dst.parent.mkdir(parents=True, exist_ok=True)
            if not dst.exists():
                try:
                    os.link(src, dst)
                except OSError:
                    # The video remains at its original location if hard links are unavailable.
                    if suffix != '.mp4':
                        shutil.copy2(src, dst)
            paths[stem + suffix] = str(dst if dst.exists() else src)
    (ROOT / 'local_paths.json').write_text(json.dumps(paths, indent=2), encoding='utf-8')
    print('Configured nine local assets. Originals preserved; local_paths.json is ignored by Git.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source')
    setup(parser.parse_args().source)
