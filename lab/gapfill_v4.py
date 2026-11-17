"""Conservative v2 extension: learned evidence may fill observed abstentions only.

Known H/A/D decisions are preserved. No possession label is supplied to inference.
"""
import numpy as np
from lab.control_v2 import infer_control
from lab.sequence_v3 import features,predict_sequence

def predict_gapfill(observation,configuration):
    o=observation
    base=infer_control(o.ball,o.nearest,o.events,o.windows,o.fps,o.pitch)[0]
    threshold=configuration['threshold']
    if threshold>1:return base
    model=configuration['emission_model']
    dense=predict_sequence(o,model)
    x=features(o)
    logits=np.column_stack([np.ones(len(x)),(x-np.array(model['mean']))/np.array(model['std'])])@np.array(model['weights'])
    logits-=logits.max(axis=1,keepdims=True)
    probability=np.exp(logits);probability/=probability.sum(axis=1,keepdims=True)
    result=base.copy();observed=np.isfinite(o.ball).all(axis=1)
    dwell=max(1,round(configuration['confirmation_s']*o.fps))
    states={'H':0,'A':1,'D':2}
    for _,a,b in o.windows:
        candidate=None;start=a;count=0
        for i in range(a,b+1):
            label=str(dense[i]);code=states.get(label)
            eligible=base[i]=='X' and observed[i] and code is not None and probability[i,code]>=threshold
            if not eligible:candidate=None;count=0;continue
            if label!=candidate:candidate=label;start=i;count=1
            else:count+=1
            if count>=dwell:result[start:i+1]=label
    return result
