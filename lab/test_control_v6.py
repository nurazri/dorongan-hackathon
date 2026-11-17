import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import unittest
import numpy as np
from lab import test_control_v2 as v2_tests
from lab.control_v6 import infer_control, motion_speed


class V6InheritedScenarios(v2_tests.ControlScenarios):
    def infer(self, ball, nearest, events=None, windows=None):
        return infer_control(ball, nearest, events or [], windows or [(1,0,len(ball)-1)])


class V6EvidenceTests(unittest.TestCase):
    def scene(self):
        ball=np.column_stack([.2+np.arange(200)*.001,np.full(200,.5)])
        return ball,np.tile([.5,5.],(200,1))

    def test_short_dropout_does_not_erase_supported_turnover(self):
        ball,near=self.scene();near[60:]=[5.,.5]
        ball[65:67]=np.nan;near[65:67]=np.inf
        labels,_,audit=infer_control(ball,near,[],[(1,0,199)])
        change=next(e for e in audit if e['to']=='A')
        self.assertEqual((change['frame'],change['confirmed_frame']),(60,71))
        self.assertTrue((labels[60:]=='A').all())

    def test_neutral_frames_never_count_as_support(self):
        ball,near=self.scene();near[60:65]=[5.,.5];near[65:67]=[1.,1.]
        labels,_,audit=infer_control(ball,near,[],[(1,0,199)])
        self.assertFalse(any(e['to']=='A' for e in audit))

    def test_contrary_control_resets_pending_turnover(self):
        ball,near=self.scene();near[60:65]=[5.,.5];near[66:71]=[5.,.5]
        labels,_,audit=infer_control(ball,near,[],[(1,0,199)])
        self.assertFalse(any(e['to']=='A' for e in audit))

    def test_motion_detects_out_and_back_path(self):
        # Endpoints after 12 frames coincide despite substantial continuous motion.
        t=np.arange(60);ball=np.column_stack([.5+.02*np.sin(2*np.pi*t/12),np.full(60,.5)])
        speed=motion_speed(ball,25,(105.3,68),.48)
        self.assertGreater(speed[24],5.)

    def test_motion_does_not_bridge_missing_data(self):
        ball,_=self.scene();ball[50]=np.nan
        self.assertTrue(np.isnan(motion_speed(ball,25,(105.3,68),.48)[50:63]).all())

    def test_isolated_spike_does_not_make_a_stationary_ball_move(self):
        ball=np.tile([.5,.5],(80,1));ball[40]=[.95,.9]
        speed=motion_speed(ball,25,(105.3,68),.48)
        self.assertTrue((speed[12:]==0).all())

    def test_no_evidence_leaks_between_halves(self):
        ball,near=self.scene()
        near[100:]=[2.,6.]
        labels,_,_=infer_control(ball,near,[],[(1,0,99),(2,100,199)])
        self.assertTrue((labels[100:112]=='X').all())

if __name__=='__main__':unittest.main()
