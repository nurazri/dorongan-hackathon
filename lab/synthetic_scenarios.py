"""Versioned feature-level football scenarios; no match files are opened.

Latent schedules define truth. Independent corruption changes observations, never labels.
This is a stress-test generator, not a calibrated simulator of real football or camera physics.
"""
from dataclasses import dataclass
import hashlib
import json
import numpy as np

FPS=25
PITCH=(105.3,68.0)
FRAMES=1250
SPLITS={'development':tuple(range(6)), 'validation':tuple(range(100,106))}
FAMILIES=('clean_control','completed_passes','brief_deflections','contested_loose',
          'aerial_duels','short_occlusions','long_occlusions','boundary_stoppages',
          'tracking_outliers','sparse_tracks','noisy_tagging','stationary_live',
          'ambiguous_referee_live','ambiguous_referee_dead','combined_noise')

@dataclass(frozen=True)
class Observation:
    ball: np.ndarray
    nearest: np.ndarray
    events: tuple
    windows: tuple=((1,0,FRAMES-1),)
    fps: int=FPS
    pitch: tuple=PITCH

@dataclass(frozen=True)
class Scenario:
    family: str
    seed: int
    observation: Observation
    truth: np.ndarray
    conditions: dict

def rle(labels):
    starts=np.r_[0,np.flatnonzero(labels[1:]!=labels[:-1])+1]
    ends=np.r_[starts[1:],len(labels)]
    return [[int(a),int(b),str(labels[a])] for a,b in zip(starts,ends)]

def fingerprint(observation):
    digest=hashlib.sha256()
    for array in (observation.ball,observation.nearest):
        # Fix dtype/NaN encoding for reproducible fingerprints on this pinned runtime.
        digest.update(np.asarray(array,dtype='<f8').tobytes())
    digest.update(json.dumps(observation.events,sort_keys=True).encode())
    return digest.hexdigest()

def make_scenario(family,seed):
    if family not in FAMILIES:
        raise ValueError(f'Unknown scenario family: {family}')
    # Shared seeds intentionally make the ambiguous pair's observations identical.
    rng=np.random.default_rng(seed)
    truth=np.array(list('H'*200+'A'*200+'D'*100+'H'*250+'A'*200+'D'*100+'H'*200))
    n=len(truth)
    ball=np.zeros((n,2),dtype=np.float64)
    nearest=np.empty((n,2),dtype=np.float64)
    events=[]
    labels=rle(truth)
    direction=rng.uniform(-.25,.25)
    position=np.array([35.,34.])
    # Vary geometry well beyond any single model's thresholds; do not import model constants.
    control_distance=rng.uniform(.35,3.8)
    opponent_distance=rng.uniform(3.8,11.5)
    for a,b,state in labels:
        if state=='D':
            ball[a:b]=position/np.array(PITCH)
            nearest[a:b]=[rng.uniform(4,10),rng.uniform(4,10)]
            # A kicker approaches during the final second but the ball remains dead.
            following=truth[b] if b<n else 'H'
            nearest[max(a,b-25):b,0 if following=='H' else 1]=.8
            events.append({'code':'SET PIECES','start_frame':max(0,a-20),
                           'end_frame':min(n,b+40),'tags':{'Team':'N/A'}})
        else:
            team=0 if state=='H' else 1
            for i in range(a,b):
                direction+=rng.normal(0,.004)
                position+=np.array([np.cos(direction),np.sin(direction)])*rng.uniform(.8,2.5)/FPS
                position=np.clip(position,[4,4],np.array(PITCH)-4)
                ball[i]=position/np.array(PITCH)
            near=np.maximum(.15,control_distance+rng.normal(0,.15,b-a))
            far=np.maximum(near+.2,opponent_distance+rng.normal(0,.5,b-a))
            nearest[a:b,team]=near
            nearest[a:b,1-team]=far
            events.append({'code':'BUILD UP','start_frame':a+10,'end_frame':max(a+10,b-10),
                           'tags':{'Team':'Barcelona' if team==0 else 'Atletic Club'}})
    masks={name:np.zeros(n,dtype=bool) for name in ('flight','touch','contested','missing','outlier','sparse','stationary')}
    alive_segments=[(a,b,state) for a,b,state in labels if state!='D']

    def passing(aerial=False):
        for a,b,state in alive_segments:
            start=a+45
            duration=int(rng.integers(18,45))
            end=min(b-15,start+duration)
            ball[start:end]=ball[start]+np.column_stack([np.arange(end-start)*rng.uniform(8,19)/FPS/PITCH[0],np.zeros(end-start)])
            nearest[start:end]=rng.uniform(4,12,(end-start,2))
            masks['flight'][start:end]=True
            if aerial:
                other=1-(0 if state=='H' else 1)
                for i in range(start,end,7):
                    nearest[i:i+2,other]=.6
    def touches():
        for a,b,state in alive_segments:
            start=a+80
            end=min(b-10,start+int(rng.integers(1,7)))
            other=1-(0 if state=='H' else 1)
            nearest[start:end,other]=.3
            nearest[start:end,1-other]=4
            masks['touch'][start:end]=True
    def contested():
        for a,b,_ in alive_segments:
            start,end=a+35,min(b-10,a+85)
            nearest[start:end]=rng.uniform(.6,1.3,(end-start,2))
            nearest[end:min(b,end+25)]=rng.uniform(6,10,(min(b,end+25)-end,2))
            masks['contested'][start:min(b,end+25)]=True
    def gaps(long=False):
        for start in (85,180,560,720,1080):
            duration=int(rng.integers(65,126) if long else rng.integers(4,21))
            end=min(n,start+duration)
            ball[start:end]=np.nan
            nearest[start:end]=np.inf
            masks['missing'][start:end]=True
    def outliers():
        indices=rng.choice(np.flatnonzero(truth!='D'),size=18,replace=False)
        ball[indices]=np.column_stack([rng.choice([-.08,1.08],len(indices)),rng.uniform(0,1,len(indices))])
        masks['outlier'][indices]=True
    def sparse():
        for start in (50,220,620,820,1100):
            end=min(n,start+int(rng.integers(15,55)))
            nearest[start:end,int(rng.integers(0,2))]=np.inf
            masks['sparse'][start:end]=True
    def stationary():
        for a,b,_ in alive_segments:
            start,end=a+30,min(b-5,a+100)
            ball[start:end]=ball[start]
            masks['stationary'][start:end]=True

    if family in ('completed_passes','aerial_duels','combined_noise'):
        passing(aerial=family=='aerial_duels')
    if family in ('brief_deflections','combined_noise'): touches()
    if family in ('contested_loose','combined_noise'): contested()
    if family=='short_occlusions': gaps()
    if family in ('long_occlusions','combined_noise'): gaps(long=True)
    if family in ('tracking_outliers','combined_noise'): outliers()
    if family in ('sparse_tracks','combined_noise'): sparse()
    if family in ('stationary_live','noisy_tagging'): stationary()
    if family=='boundary_stoppages':
        for a,b,state in labels:
            if state=='D':
                ball[a:b-30]=[-.015,.5]
                nearest[a:b-30]=[6,8]
                # Reposition before the restart while no player is close enough to control.
                ball[b-30:b]=[.05,.5]
                nearest[b-30:b-15]=[6,8]
    if family in ('noisy_tagging','combined_noise'):
        for event in events:
            if event['code']=='BUILD UP' and rng.random()<.5:
                team=event['tags']['Team']
                event['tags']['Team']='Atletic Club' if team=='Barcelona' else 'Barcelona'
        events=[e for e in events if rng.random()>.3]
        for a,b,_ in alive_segments[:3]:
            events.append({'code':'SET PIECES','start_frame':a+20,'end_frame':min(b,a+120),'tags':{'Team':'N/A'}})
    if family.startswith('ambiguous_referee_'):
        ball[40:160]=ball[40]
        nearest[40:160]=[.7,5.]
        masks['stationary'][40:160]=True
        if family.endswith('_dead'):
            truth[40:160]='D'
        # No whistle or referee signal is represented in either observation.
    masks['missing']=~np.isfinite(ball).all(axis=1)
    for array in (ball,nearest,truth,*masks.values()):
        array.setflags(write=False)
    return Scenario(family,seed,Observation(ball,nearest,tuple(events)),truth,masks)
