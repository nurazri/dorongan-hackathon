"""Checksum-verified download of predeclared external development data only."""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import Request,urlopen

ROOT=Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT))
from lab.external_download import download

def md5(path):
    digest=hashlib.md5()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):
            digest.update(chunk)
    return digest.hexdigest()

def fetch(match,allow_validation=False):
    protocol=json.loads((ROOT/'benchmarks/external/sportec/protocol.json').read_text(encoding='utf-8'))
    allowed=protocol['splits']['development']+(protocol['splits']['validation'] if allow_validation else [])
    if match not in allowed: raise ValueError('Match outside the explicitly allowed development/validation split')
    if allow_validation and not (ROOT/'models/possession_control_v5.json').exists(): raise ValueError('Freeze the candidate before downloading validation matches')
    directory=ROOT/'.local/external/sportec/raw'/match
    directory.mkdir(parents=True,exist_ok=True)
    for entry in protocol['files']:
        if entry['match_id']!=match or not any(role in entry['name'] for role in ('matchinformation','positions_raw_observed')):
            continue
        if Path(entry['name']).name!=entry['name']:
            raise ValueError('Invalid source filename')
        target=directory/entry['name']
        if target.exists() and target.stat().st_size==entry['size'] and md5(target)==entry['computed_md5']:
            print(f'Verified cached {target.name}',flush=True)
            continue
        download(entry,target)
    print(f'External development inputs: {directory}',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--match',default='J03WOH')
    parser.add_argument('--allow-validation',action='store_true')
    args=parser.parse_args()
    fetch(args.match,args.allow_validation)
