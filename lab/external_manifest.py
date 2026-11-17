"""Fetch public metadata only; never downloads match tracking or reads competition data."""
import json
import re
from pathlib import Path
from urllib.request import urlopen, Request

ROOT=Path(__file__).resolve().parents[1]
ARTICLE='https://api.figshare.com/v2/articles/28196177'
SPLITS={'development':['J03WOH','J03WQQ','J03WMX'],
        'validation':['J03WPY','J03WR9'],
        'held_out':['J03WN1','J03WOY']}

def create_protocol(article):
    if article.get('version')!=1:
        raise ValueError('The dataset version changed; review it before updating the fixed protocol.')
    license_url=article.get('license',{}).get('url','')
    if license_url!='https://creativecommons.org/licenses/by/4.0/':
        raise ValueError('Unexpected license metadata; review the dataset terms.')
    ids={match for values in SPLITS.values() for match in values}
    files=[]
    for entry in article['files']:
        match=re.search(r'DFL-MAT-(J[A-Z0-9]+)\.xml$',entry['name'])
        if match and match.group(1) in ids:
            files.append({'match_id':match.group(1),**{key:entry[key] for key in ('name','size','download_url','computed_md5')}})
    if len(files)!=21 or any(sum(f['match_id']==match for f in files)!=3 for match in ids):
        raise ValueError('Expected metadata, events and positions files for all seven matches.')
    return {
        'protocol':'sportec-external-validation-v1',
        'status':'Research and metadata manifest only. No external match has been downloaded, parsed or scored.',
        'source_article':ARTICLE,'source_doi':article.get('doi'),
        'paper':'https://doi.org/10.1038/s41597-025-04505-y',
        'attribution': {'authors':['Manuel Bassek','Robert Rein','Hendrik Weber','Daniel Memmert'], 'title':article['title'],'doi':article.get('doi')},
        'license':article['license'],'splits':SPLITS,'files':files,
        'total_download_bytes':sum(file['size'] for file in files),
        'reference_mapping':{'BallStatus=0':'D','BallStatus=1 and BallPossession=1':'H',
            'BallStatus=1 and BallPossession=2':'A','missing/unsupported reference values':'X; ungraded, never guessed'},
        'feature_allowlist':['player x/y','ball x/y','team membership','period','frame/timestamp','pitch dimensions'],
        'label_only_fields':['BallStatus','BallPossession'],
        'excluded_model_inputs':['reference labels','events XML','ball-owning-team fields','human event-derived restart tags'],
        'protocol_rules':[
            'Split by complete matches before labels or evaluation are inspected.',
            'Same teams appear across matches: this is not an unseen-team benchmark.',
            'First audit raw schema, timebase, semantics, duplicate frame keys and missing frames.',
            'Construct references separately from model observations. Never feed status/ownership to prediction.',
            'Use a (period, frame) key; reset model state and abstention filling across period boundaries.',
            'Normalize metres using each match pitch dimensions; never assume video frame counters match.',
            'Report native data first; optionally evaluate predeclared corruption variants separately.',
            'Develop only on development matches. Validation is for limited model selection, held_out only after freezing.',
            'No competition match inputs, labels, or published sample scores participate in this protocol.',
            'Preserve attribution, DOI, license notice, file checksums and any preprocessing decisions.',
        ],
    }

def main():
    with urlopen(Request(ARTICLE,headers={'User-Agent':'PossessionLab-Metadata/0.1'}),timeout=30) as response:
        article=json.load(response)
    protocol=create_protocol(article)
    directory=ROOT/'benchmarks/external/sportec'
    directory.mkdir(parents=True,exist_ok=True)
    (directory/'protocol.json').write_text(json.dumps(protocol,indent=2),encoding='utf-8')
    print(f"External metadata: {len(protocol['files'])} files; {protocol['total_download_bytes']/1e9:.2f} GB for all seven matches.")
    print('Fetched only public metadata. No external match downloaded or evaluated.')
    print(f'Protocol: {directory/"protocol.json"}')

if __name__=='__main__':
    main()
