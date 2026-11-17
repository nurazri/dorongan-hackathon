"""Learned geometry emissions and temporal decoding; inference never reads labels.

Model weights are trained separately on an attributed external development match.
Missing-ball frames have neutral emissions, never automatic D evidence.
"""
import json
from pathlib import Path
import numpy as np
from lab.control_v2 import motion_speed

FEATURE_NAMES=('home_near3','away_near3','home_near8','away_near8','home_logdist','away_logdist',
    'distance_margin','ball_observed','home_observed','away_observed','log_motion','motion_observed',
    'slow_motion','moderate_motion','fast_motion','outside','outside_distance',
    'home_near_slow','away_near_slow','home_near_fast','away_near_fast',
    'home_context_1s','away_context_1s','home_context_3s','away_context_3s','slow_context_1s')

def centered_mean(values,valid,width):
    n=len(values); half=width//2
    a=np.maximum(0,np.arange(n)-half);b=np.minimum(n,np.arange(n)+(width-half))
    total=np.r_[0.,np.cumsum(np.where(valid,values,0.))]
    count=np.r_[0,np.cumsum(valid)]
    return np.divide(total[b]-total[a],count[b]-count[a],out=np.zeros(n),where=(count[b]-count[a])>0)

def features(observation):
    out=np.zeros((len(observation.ball),len(FEATURE_NAMES)),dtype=np.float64)
    for _,a,b in observation.windows:
        ball=observation.ball[a:b+1];nearest=observation.nearest[a:b+1]
        visible=np.isfinite(ball).all(axis=1)
        tracks=np.isfinite(nearest)&visible[:,None]
        distance=np.where(tracks,np.clip(nearest,0,40),40.)
        near3=np.where(tracks,np.exp(-distance/3),0.)
        near8=np.where(tracks,np.exp(-distance/8),0.)
        margin=np.zeros(len(ball));both=tracks.all(axis=1)
        margin[both]=np.clip((distance[both,1]-distance[both,0])/10,-1,1)
        speed=motion_speed(ball,observation.fps,observation.pitch,.48)
        speed_valid=np.isfinite(speed)
        motion=np.where(speed_valid,np.clip(speed,0,60),0.)
        slow=speed_valid&(motion<.5);moderate=speed_valid&(motion<3);fast=speed_valid&(motion>8)
        pitch=np.array(observation.pitch)
        outside_distance=np.where(visible,np.maximum(np.maximum((-ball*pitch).max(axis=1),((ball-1)*pitch).max(axis=1)),0.),0.)
        columns=[near3[:,0],near3[:,1],near8[:,0],near8[:,1],
                 np.log1p(distance[:,0])/np.log(41),np.log1p(distance[:,1])/np.log(41),margin,
                 visible,tracks[:,0],tracks[:,1],np.log1p(motion)/np.log(61),speed_valid,
                 slow,moderate,fast,outside_distance>0,np.clip(outside_distance,0,5)/5,
                 near3[:,0]*slow,near3[:,1]*slow,near3[:,0]*fast,near3[:,1]*fast]
        for seconds in (1,3):
            width=max(1,round(seconds*observation.fps))
            for team in (0,1):columns.append(centered_mean(near3[:,team],visible,width))
        columns.append(centered_mean(slow.astype(float),speed_valid,max(1,round(observation.fps))))
        out[a:b+1]=np.column_stack(columns)
    if not np.isfinite(out).all():raise ValueError('Nonfinite model features')
    return out

def fit_emissions(x,labels,iterations=300):
    # Fixed full-batch Adam and L2; neither is chosen using competition labels.
    valid=labels!='X'; x=x[valid]
    if len(x)==0: raise ValueError('No graded training observations')
    y=np.array([{'H':0,'A':1,'D':2}[str(v)] for v in labels[valid]])
    if len(np.unique(y))!=3:raise ValueError('Training needs all three possession states')
    mean=x.mean(axis=0);std=x.std(axis=0);std[std<1e-6]=1
    design=np.column_stack([np.ones(len(x)),(x-mean)/std])
    weights=np.zeros((design.shape[1],3));first=np.zeros_like(weights);second=np.zeros_like(weights)
    targets=np.eye(3)[y]
    for step in range(1,iterations+1):
        logits=design@weights;logits-=logits.max(axis=1,keepdims=True)
        probability=np.exp(logits);probability/=probability.sum(axis=1,keepdims=True)
        gradient=design.T@(probability-targets)/len(x)
        gradient[1:]+=.001*weights[1:]
        first=.9*first+.1*gradient;second=.999*second+.001*gradient**2
        weights-=.03*(first/(1-.9**step))/(np.sqrt(second/(1-.999**step))+1e-8)
    return {'feature_names':list(FEATURE_NAMES),'mean':mean.tolist(),'std':std.tolist(),'weights':weights.tolist()}

def transition_model(labels):
    counts=np.ones((3,3),dtype=float)
    codes=np.array([{'H':0,'A':1,'D':2}.get(str(v),-1) for v in labels])
    for previous,current in zip(codes[:-1],codes[1:]):
        if previous>=0 and current>=0:counts[previous,current]+=1
    probability=counts/counts.sum(axis=1,keepdims=True)
    prior=np.bincount(codes[codes>=0],minlength=3).astype(float)+1
    prior/=prior.sum()
    return np.log(probability),np.log(prior)

def decode_sequence(emission,log_transition,log_prior,scale=1.):
    n,states=emission.shape
    if n==0:raise ValueError('Cannot decode empty sequence')
    back=np.zeros((n,states),dtype=np.int8)
    score=emission[0]+log_prior
    for i in range(1,n):
        candidates=score[:,None]+scale*log_transition
        back[i]=candidates.argmax(axis=0)
        score=candidates.max(axis=0)+emission[i]
    result=np.zeros(n,dtype=np.int8);result[-1]=score.argmax()
    for i in range(n-1,0,-1):result[i-1]=back[i,result[i]]
    return result

def predict_sequence(observation,model,scale=None):
    if model['feature_names']!=list(FEATURE_NAMES):raise ValueError('Model feature schema mismatch')
    x=features(observation)
    mean=np.array(model['mean']);std=np.array(model['std'])
    weights=np.array(model['weights'])
    logits=np.column_stack([np.ones(len(x)),(x-mean)/std])@weights
    # Unobserved ball is not a stoppage. Sequence context carries state through the gap.
    logits[~np.isfinite(observation.ball).all(axis=1)]=0
    labels=np.full(len(x),'X',dtype='<U1')
    for _,a,b in observation.windows:
        codes=decode_sequence(logits[a:b+1],np.array(model['log_transition']),np.array(model['log_prior']),
                              model['transition_scale'] if scale is None else scale)
        labels[a:b+1]=np.array(['H','A','D'])[codes]
    return labels

def load_model(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))
