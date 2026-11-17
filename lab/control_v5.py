"""Inference-only calibrated control model. No external or competition labels are loaded."""
from lab.control_v2 import infer_control

def predict_calibrated(observation,configuration):
    o=observation
    return infer_control(o.ball,o.nearest,o.events,o.windows,o.fps,o.pitch,
                         parameters=configuration['parameters'])[0]
