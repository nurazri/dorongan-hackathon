"""Original temporal-v1 inference shared by match processing and synthetic evaluation."""
import numpy as np

PARAMETERS = {'switch_cost': 4.0, 'tag_weight': 0.45}

def decode(emission, switch_cost=4.0):
    count, states = emission.shape
    costs = np.full((states,states),switch_cost)
    np.fill_diagonal(costs,0)
    back = np.zeros((count,states),dtype=np.int8)
    score = emission[0].copy()
    for i in range(1,count):
        candidate=score[:,None]-costs
        back[i]=candidate.argmax(axis=0)
        score=candidate.max(axis=0)+emission[i]
    out=np.zeros(count,dtype=np.int8)
    out[-1]=score.argmax()
    for i in range(count-1,0,-1):
        out[i-1]=back[i,out[i]]
    return out

def infer_temporal(ball, nearest, events, windows, fps=25, pitch=(105.3,68.0)):
    n=len(ball)
    observed=np.isfinite(ball).all(axis=1)
    emission=np.zeros((n,3),dtype=np.float32)
    for team in (0,1):
        own,other=nearest[:,team],nearest[:,1-team]
        available=np.isfinite(own)&np.isfinite(other)
        margin=np.zeros(n)
        margin[available]=np.clip((other[available]-own[available])/2,-2,2)
        emission[:,team]=np.where(np.isfinite(own),np.exp(-own/3)*2,0)+margin
    emission[:,2]=-.5
    emission[~observed]=0
    outside=observed&((ball<0).any(axis=1)|(ball>1).any(axis=1))
    emission[outside,2]+=3
    velocity=np.full(n,np.nan)
    velocity[1:]=np.linalg.norm(np.diff(ball,axis=0)*np.array(pitch),axis=1)*fps
    still=(velocity<.2)&(nearest.min(axis=1)>3)&observed
    emission[still,2]+=.8
    attacking={'BUILD UP','PROGRESSION','CREATING CHANCES','ATTACKING TRANSITION','LONG BALL'}
    for event in events:
        team={'Barcelona':0,'Atletic Club':1}.get(event.get('tags',{}).get('Team'))
        if team is not None and event['code'] in attacking:
            a,b=max(0,event['start_frame']),min(n,event['end_frame'])
            emission[a:b,team]+=PARAMETERS['tag_weight']
    labels=np.full(n,'X',dtype='<U1')
    for _,a,b in windows:
        labels[a:b+1]=np.array(['H','A','D'])[decode(emission[a:b+1],PARAMETERS['switch_cost'])]
    return labels,emission,velocity
