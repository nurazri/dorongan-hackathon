import unittest
import numpy as np
from lab.control_v2 import infer_control, motion_speed

class ControlScenarios(unittest.TestCase):
    def scene(self,n=200):
        # A steadily moving ball and persistent close home control.
        ball=np.column_stack([.25+np.arange(n)*.001,np.full(n,.5)])
        nearest=np.tile([.5,5.],(n,1))
        return ball,nearest

    def infer(self,ball,nearest,events=None,windows=None):
        return infer_control(ball,nearest,events or [],windows or [(1,0,len(ball)-1)])

    def test_brief_opponent_touch_retains_control(self):
        ball,near=self.scene()
        near[60:65]=[5.,.5]
        labels,_,_=self.infer(ball,near)
        self.assertTrue((labels=='H').all())

    def test_sustained_control_changes_team_at_candidate_onset(self):
        ball,near=self.scene()
        near[60:]=[5.,.5]
        labels,_,audit=self.infer(ball,near)
        np.testing.assert_array_equal(labels,np.array(['H']*60+['A']*140))
        change=next(e for e in audit if e['to']=='A')
        self.assertEqual(change['frame'],60)
        self.assertEqual(change['confirmed_frame'],69)

    def test_contested_or_loose_ball_keeps_last_team(self):
        ball,near=self.scene()
        near[40:80]=[1.,1.]
        near[80:120]=[9.,8.]
        labels,_,_=self.infer(ball,near)
        self.assertTrue((labels=='H').all())

    def test_missing_ball_is_not_dead_and_long_gap_abstains(self):
        ball,near=self.scene()
        ball[40:110]=np.nan
        near[40:110]=np.inf
        labels,_,_=self.infer(ball,near)
        self.assertFalse((labels=='D').any())
        self.assertTrue((labels[40:89]=='H').all())
        self.assertTrue((labels[89:110]=='X').all())

    def test_missing_data_does_not_create_interpolated_motion(self):
        ball,_=self.scene()
        ball[50]=np.nan
        speed=motion_speed(ball,25,(105.3,68),.48)
        self.assertTrue(np.isnan(speed[50:63]).all())

    def test_control_confirmation_does_not_span_a_missing_gap(self):
        ball,near=self.scene()
        near[60:65]=[5.,.5]
        ball[65:70]=np.nan
        near[65:70]=np.inf
        near[70:75]=[5.,.5]
        labels,_,_=self.infer(ball,near)
        self.assertFalse((labels=='A').any())

    def test_stationary_dribbler_during_live_play_is_not_dead(self):
        ball,near=self.scene()
        ball[40:140]=ball[40]
        labels,_,_=self.infer(ball,near)
        self.assertFalse((labels=='D').any())

    def test_one_bad_outside_observation_is_not_a_stoppage(self):
        ball,near=self.scene()
        ball[60]=[-.02,.5]
        labels,_,_=self.infer(ball,near)
        self.assertFalse((labels=='D').any())

    def test_outside_stoppage_persists_until_observed_restart(self):
        ball,near=self.scene()
        ball[40:80]=[-.02,.5]
        ball[80:120]=[.1,.5]
        near[80:100]=[8.,9.]
        # No restart just because a player stands next to the settled ball.
        ball[120:,0]=.1+np.arange(80)*.002
        labels,evidence,audit=self.infer(ball,near)
        self.assertTrue((labels[40:120]=='D').all())
        self.assertTrue((evidence['stoppage_evidence'][40:45]==1).all())
        self.assertTrue(any(e['reason']=='observed_restart_motion' for e in audit))

    def test_stationary_ball_far_from_visible_players_is_stoppage_evidence(self):
        ball,near=self.scene()
        ball[:100]=[.25,.5]
        near[:100]=[8.,9.]
        labels,_,audit=self.infer(ball,near)
        self.assertTrue((labels[20:100]=='D').all())
        self.assertTrue(any(e['reason']=='settled_far_from_players' for e in audit))

    def test_set_piece_static_ball_then_motion_infers_restart_from_observations(self):
        ball,near=self.scene()
        ball[:80]=[.25,.5]
        ball[80:,0]=.25+np.arange(120)*.002
        events=[{'code':'SET PIECES','start_frame':10,'end_frame':110}]
        labels,evidence,audit=self.infer(ball,near,events)
        self.assertTrue((labels[30:80]=='D').all())
        restart=next(e for e in audit if e['reason']=='observed_restart_motion')
        self.assertGreaterEqual(restart['frame'],80)
        self.assertLess(restart['frame'],95)
        self.assertTrue((labels[100:]=='H').all())
        self.assertNotEqual(restart['frame'],events[0]['end_frame'])

    def test_set_piece_tag_alone_does_not_label_moving_play_dead(self):
        ball,near=self.scene()
        labels,_,_=self.infer(ball,near,[{'code':'SET PIECES','start_frame':30,'end_frame':90}])
        self.assertFalse((labels=='D').any())

    def test_fully_unobserved_scene_stays_unknown(self):
        labels,_,_=self.infer(np.full((150,2),np.nan),np.full((150,2),np.inf))
        self.assertTrue((labels=='X').all())

    def test_halves_reset_state_and_ungraded_frames_stay_unknown(self):
        ball,near=self.scene()
        ball[120:]=np.nan
        near[120:]=np.inf
        labels,_,_=self.infer(ball,near,windows=[(1,10,70),(2,120,180)])
        self.assertTrue((labels[:10]=='X').all())
        self.assertTrue((labels[71:]=='X').all())

    def test_absent_opposing_team_does_not_prove_control(self):
        ball,near=self.scene()
        near[:,1]=np.inf
        labels,_,_=self.infer(ball,near)
        self.assertTrue((labels=='X').all())

if __name__=='__main__':
    unittest.main()
