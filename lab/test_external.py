from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
import numpy as np
from lab.sportec_adapter import parse_sportec,reference_label
from lab.synthetic_scenarios import Observation
from lab.sequence_v3 import features,FEATURE_NAMES,fit_emissions,transition_model,predict_sequence,decode_sequence
from lab.external_train import corrupt

META='<PutDataRequest><MatchInformation><Environment PitchX="105" PitchY="68"/><Teams><Team TeamId="H" Role="home"/><Team TeamId="A" Role="guest"/></Teams></MatchInformation></PutDataRequest>'

def xml_fixture(reference_override=False,duplicate=False,missing=False,bad_time=False):
    groups=[]
    for period,minute in [('firstHalf','00'),('secondHalf','01')]:
        for team,x in [('H',1),('A',3),('BALL',0)]:
            frames=[]
            for i in range(3):
                if missing and team=='BALL' and i==1:continue
                time=i*(.1 if bad_time else .04)
                label='BallStatus="1" BallPossession="1"' if team=='BALL' else 'BallStatus="0" BallPossession="2"'
                if reference_override and team=='BALL':label='BallStatus="0" BallPossession="2"'
                frames.append(f'<Frame N="{10+i}" T="2022-01-01T00:{minute}:{time:06.3f}+00:00" X="{x}" Y="0" {label}/>')
            if duplicate and team=='BALL':frames.append(frames[-1])
            groups.append(f'<FrameSet GameSection="{period}" TeamId="{team}" PersonId="{team}">'+''.join(frames)+'</FrameSet>')
    return '<PutDataRequest><Positions>'+''.join(groups)+'</Positions></PutDataRequest>'

def parse_fixture(content):
    with TemporaryDirectory() as directory:
        meta=Path(directory)/'meta.xml';raw=Path(directory)/'positions.xml'
        meta.write_text(META);raw.write_text(content)
        return parse_sportec(meta,raw)

class ExternalAdapterTests(TestCase):
    def test_period_frame_keys_and_geometry(self):
        data=parse_fixture(xml_fixture())
        self.assertEqual(data.observation.windows,((1,0,2),(2,4,6)))
        np.testing.assert_allclose(data.observation.ball[0],[.5,.5])
        np.testing.assert_allclose(data.observation.nearest[0],[1,3])
        self.assertEqual(data.reference[3],'X')

    def test_reference_changes_do_not_change_features(self):
        a=parse_fixture(xml_fixture());b=parse_fixture(xml_fixture(reference_override=True))
        self.assertFalse(np.array_equal(a.reference,b.reference))
        np.testing.assert_array_equal(features(a.observation),features(b.observation))

    def test_missing_ball_frame_preserved_as_ungraded(self):
        data=parse_fixture(xml_fixture(missing=True))
        self.assertEqual(data.reference[1],'X')
        self.assertTrue(np.isnan(data.observation.ball[1]).all())
        self.assertEqual(data.audit['missing_ball_rows_inserted'],2)

    def test_duplicate_ball_frame_rejected(self):
        with self.assertRaisesRegex(ValueError,'Duplicate ball'):parse_fixture(xml_fixture(duplicate=True))

    def test_wrong_timebase_rejected(self):
        with self.assertRaisesRegex(ValueError,'alignment'):parse_fixture(xml_fixture(bad_time=True))

    def test_dead_ball_ownership_is_discarded(self):
        self.assertEqual(reference_label({'BallStatus':'0','BallPossession':'1'}),'D')
        self.assertEqual(reference_label({'BallStatus':'1','BallPossession':'2'}),'A')
        self.assertEqual(reference_label({'BallStatus':'1','BallPossession':'0'}),'X')

class LearnedSequenceTests(TestCase):
    def observation(self):
        n=90
        ball=np.tile([.5,.5],(n,1));nearest=np.tile([.5,6.],(n,1))
        nearest[30:60]=[6.,.5];nearest[60:]=[8.,8.]
        return Observation(ball,nearest,(),((1,0,n-1),))

    def test_features_finite_through_missing_observations(self):
        obs=self.observation();masked=corrupt(obs,7)
        x=features(masked)
        self.assertEqual(x.shape,(90,len(FEATURE_NAMES)))
        self.assertTrue(np.isfinite(x).all())

    def test_corruption_is_reproducible_and_preserves_inputs(self):
        obs=self.observation();a=corrupt(obs,7);b=corrupt(obs,7)
        np.testing.assert_array_equal(a.ball,b.ball)
        self.assertTrue(np.isfinite(obs.ball).all())
        self.assertTrue(np.isnan(a.ball).any())

    def test_supervised_fit_can_learn_separated_synthetic_states(self):
        obs=self.observation();labels=np.array(list('H'*30+'A'*30+'D'*30))
        model=fit_emissions(features(obs),labels,iterations=80)
        transition,prior=transition_model(labels)
        model.update(log_transition=transition,log_prior=prior,transition_scale=1)
        with patch('builtins.open',side_effect=AssertionError('Inference read a file')):
            prediction=predict_sequence(obs,model)
        self.assertGreater((prediction==labels).mean(),.95)

    def test_state_resets_and_ungraded_separator(self):
        emission=np.tile([0.,3.,0.],(20,1))
        result=decode_sequence(emission,np.log(np.full((3,3),1/3)),np.log(np.full(3,1/3)))
        self.assertTrue((result==1).all())
        obs=self.observation()
        from dataclasses import replace
        obs=replace(obs,windows=((1,0,29),(2,31,89)))
        labels=np.array(list('H'*30+'A'*30+'D'*30))
        model=fit_emissions(features(obs),labels,iterations=20)
        transition,prior=transition_model(labels)
        model.update(log_transition=transition,log_prior=prior,transition_scale=1)
        self.assertEqual(predict_sequence(obs,model)[30],'X')
