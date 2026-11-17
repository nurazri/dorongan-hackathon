"""Two-pass XML adapter with separate observation and reference-label paths.

Input: original Sportec open-data metadata and observed tracking, never events.
Only one object's XML frame is retained at a time; player tracks are reduced online.
"""
import argparse
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from lab.synthetic_scenarios import Observation
PERIODS={'firstHalf':1,'secondHalf':2,'firstHalfExtra':3,'secondHalfExtra':4}

@dataclass(frozen=True)
class ExternalMatch:
    observation: Observation
    reference: np.ndarray
    frame_ids: np.ndarray
    periods: np.ndarray
    audit: dict

def local_name(tag):
    return tag.rsplit('}',1)[-1]

def frames(path):
    current=None; parent=None
    for event,element in ET.iterparse(path,events=('start','end')):
        name=local_name(element.tag)
        if event=='start' and name=='FrameSet':
            current=dict(element.attrib); parent=element
            if current.get('GameSection') not in PERIODS:
                raise ValueError('Unknown game section')
        elif event=='end' and name=='Frame':
            if current is None:
                raise ValueError('Frame outside a FrameSet')
            yield current,element.attrib
            parent.remove(element)
        elif event=='end' and name=='FrameSet':
            element.clear();current=None;parent=None

def reference_label(attributes):
    # Only this function sees label attributes; unsupported values remain ungraded.
    if attributes.get('BallStatus')=='0': return 'D'
    if attributes.get('BallStatus')=='1':
        return {'1':'H','2':'A'}.get(attributes.get('BallPossession'),'X')
    return 'X'

def xy(attributes):
    return np.array([float(attributes.get('X','nan')),float(attributes.get('Y','nan'))])

def parse_metadata(path):
    root=ET.parse(path).getroot()
    environments=[e for e in root.iter() if local_name(e.tag)=='Environment']
    if len(environments)!=1: raise ValueError('Missing or ambiguous pitch metadata')
    pitch=(float(environments[0].get('PitchX')),float(environments[0].get('PitchY')))
    if min(pitch)<=0: raise ValueError('Invalid pitch dimensions')
    teams={}
    for e in root.iter():
        if local_name(e.tag)=='Team':
            role=e.get('Role')
            if role=='home': teams[e.get('TeamId')]=0
            elif role in ('guest','away'): teams[e.get('TeamId')]=1
    if sorted(teams.values())!=[0,1]: raise ValueError('Expected exactly one home and one away team')
    return pitch,teams

def parse_sportec(metadata,positions):
    pitch,teams=parse_metadata(metadata)
    ball_records={}; statuses=Counter(); possessions=Counter()
    for group,attributes in frames(positions):
        if group.get('TeamId')!='BALL': continue
        key=(PERIODS[group['GameSection']],int(attributes['N']))
        if key in ball_records: raise ValueError('Duplicate ball frame key')
        timestamp=datetime.fromisoformat(attributes['T']).timestamp()
        ball_records[key]=(xy(attributes),timestamp,reference_label(attributes))
        statuses[attributes.get('BallStatus','missing')]+=1
        possessions[attributes.get('BallPossession','missing')]+=1
    if not ball_records: raise ValueError('No ball frames found')
    print(f'External ball/reference pass: {len(ball_records)} records',flush=True)
    ball=[]; truth=[]; frame_ids=[]; periods=[]; windows=[]; index={}; times=[]
    for period in sorted({key[0] for key in ball_records}):
        keys=sorted(key for key in ball_records if key[0]==period)
        if ball:
            ball.append([np.nan,np.nan]);truth.append('X');frame_ids.append(-1);periods.append(0)
        first=len(ball)
        samples=[]
        for frame in range(keys[0][1],keys[-1][1]+1):
            key=(period,frame);index[key]=len(ball)
            record=ball_records.get(key)
            if record:
                coordinate,timestamp,label=record
                ball.append(coordinate);truth.append(label);samples.append((frame,timestamp))
            else:
                ball.append([np.nan,np.nan]);truth.append('X')
            frame_ids.append(frame);periods.append(period)
        windows.append((period,first,len(ball)-1))
        samples=np.asarray(samples,dtype=float)
        if len(samples)>1:
            dt=np.diff(samples[:,1]);df=np.diff(samples[:,0])
            if (dt<=0).any(): raise ValueError('Nonmonotonic ball timestamps')
            rates=df/dt
            if not np.allclose(rates,25,atol=.02,rtol=0): raise ValueError('Unexpected frame/time alignment; native 25 fps required')
            times.append(float(np.median(rates)))
    ball_m=np.asarray(ball,dtype=np.float64)
    nearest=np.full((len(ball),2),np.inf)
    missing=0; player_frames=0; skipped=Counter(); previous={}
    for group,attributes in frames(positions):
        team=teams.get(group.get('TeamId'))
        if team is None:
            if group.get('TeamId')!='BALL': skipped[group.get('TeamId','missing')]+=1
            continue
        period=PERIODS[group['GameSection']]; frame=int(attributes['N'])
        person=group.get('PersonId')
        if not person: raise ValueError('Player track without identifier')
        identity=(period,person)
        if frame<=previous.get(identity,-1): raise ValueError('Repeated or unordered player frame')
        previous[identity]=frame
        i=index.get((period,frame))
        if i is None:
            missing+=1;continue
        position=xy(attributes)
        if np.isfinite(position).all() and np.isfinite(ball_m[i]).all():
            distance=float(np.linalg.norm(position-ball_m[i]))
            nearest[i,team]=min(nearest[i,team],distance)
        player_frames+=1
    normalized=ball_m/np.array(pitch)+.5
    labels=np.array(truth,dtype='<U1'); frame_ids=np.array(frame_ids,dtype=np.int64);periods=np.array(periods,dtype=np.int8)
    observed=np.isfinite(normalized).all(axis=1)
    audit={'pitch_m':list(pitch),'fps':25,'periods':[list(w) for w in windows],
        'ball_records':len(ball_records),'array_rows_including_period_separators':len(ball),
        'player_frames':player_frames,'player_frames_outside_ball_span':missing,'skipped_team_frames':dict(skipped),
        'ball_status_values':dict(statuses),'ball_possession_values':dict(possessions),
        'reference_counts':{label:int((labels==label).sum()) for label in 'HADX'},
        'ball_observed':int(observed.sum()),'native_fps_by_period':times,
        'feature_fields':['X','Y','TeamId','GameSection','N','pitch dimensions'],
        'reference_only_fields':['BallStatus','BallPossession'],
        'events_used':False,'coordinate_conversion':'center-based metres to normalized 0..1',
        'missing_ball_rows_inserted':len(ball)-len(ball_records)-(len(windows)-1)}
    for array in (normalized,nearest,labels,frame_ids,periods): array.setflags(write=False)
    observation=Observation(normalized,nearest,(),tuple(windows),25,pitch)
    return ExternalMatch(observation,labels,frame_ids,periods,audit)

def prepare(match='J03WOH',allow_validation=False):
    protocol=json.loads((ROOT/'benchmarks/external/sportec/protocol.json').read_text(encoding='utf-8'))
    allowed=protocol['splits']['development']+(protocol['splits']['validation'] if allow_validation else [])
    if match not in allowed: raise ValueError('Match outside the explicitly allowed development/validation split')
    if allow_validation and not (ROOT/'models/possession_control_v5.json').exists(): raise ValueError('Candidate must be frozen before validation preparation')
    raw=ROOT/'.local/external/sportec/raw'/match
    metadata=list(raw.glob('*matchinformation*.xml'));positions=list(raw.glob('*positions_raw_observed*.xml'))
    if len(metadata)!=1 or len(positions)!=1: raise ValueError('Download verified external inputs first')
    data=parse_sportec(metadata[0],positions[0])
    destination=ROOT/'.local/external/sportec'/match
    np.savez_compressed(destination.with_suffix('.npz'),ball=data.observation.ball,nearest=data.observation.nearest,
        reference=data.reference,frame_ids=data.frame_ids,periods=data.periods,
        windows=np.array(data.observation.windows),pitch=np.array(data.observation.pitch))
    destination.with_suffix('.audit.json').write_text(json.dumps(data.audit,indent=2),encoding='utf-8')
    print(json.dumps(data.audit,indent=2),flush=True)
    return data

def load_match(match='J03WOH',allow_validation=False):
    protocol=json.loads((ROOT/'benchmarks/external/sportec/protocol.json').read_text(encoding='utf-8'))
    allowed=protocol['splits']['development']+(protocol['splits']['validation'] if allow_validation else [])
    if match not in allowed: raise ValueError('Match outside the explicitly allowed development/validation split')
    source=ROOT/'.local/external/sportec'/match
    with np.load(source.with_suffix('.npz'),allow_pickle=False) as arrays:
        observation=Observation(arrays['ball'],arrays['nearest'],(),tuple(map(tuple,arrays['windows'].tolist())),25,tuple(arrays['pitch'].tolist()))
        return ExternalMatch(observation,arrays['reference'],arrays['frame_ids'],arrays['periods'],json.loads(source.with_suffix('.audit.json').read_text()))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--match',default='J03WOH')
    parser.add_argument('--allow-validation',action='store_true')
    args=parser.parse_args()
    prepare(args.match,args.allow_validation)
