import builtins
from dataclasses import replace
import unittest
from unittest.mock import patch
import numpy as np
from lab.synthetic_scenarios import FAMILIES,SPLITS,FRAMES,make_scenario,fingerprint
from lab.synthetic_benchmark import MODELS,predict,score

class SyntheticBenchmarkTests(unittest.TestCase):
    def test_every_family_has_valid_truth_and_observations(self):
        for family in FAMILIES:
            with self.subTest(family=family):
                case=make_scenario(family,100)
                self.assertEqual(case.observation.ball.shape,(FRAMES,2))
                self.assertEqual(case.observation.nearest.shape,(FRAMES,2))
                self.assertEqual(set(case.truth),set('HAD'))
                self.assertFalse(case.truth.flags.writeable)
                self.assertTrue(np.isfinite(case.observation.nearest[np.isfinite(case.observation.nearest)]).all())

    def test_seed_splits_are_disjoint(self):
        self.assertFalse(set(SPLITS['development'])&set(SPLITS['validation']))

    def test_generation_is_deterministic_and_seeds_vary(self):
        a=make_scenario('combined_noise',100)
        b=make_scenario('combined_noise',100)
        c=make_scenario('combined_noise',101)
        self.assertEqual(fingerprint(a.observation),fingerprint(b.observation))
        self.assertNotEqual(fingerprint(a.observation),fingerprint(c.observation))

    def test_ambiguous_referee_pair_is_observationally_identical(self):
        a=make_scenario('ambiguous_referee_live',100)
        b=make_scenario('ambiguous_referee_dead',100)
        self.assertEqual(fingerprint(a.observation),fingerprint(b.observation))
        self.assertFalse(np.array_equal(a.truth,b.truth))
        for model in MODELS:
            np.testing.assert_array_equal(predict(a.observation,model),predict(b.observation,model))

    def test_reference_labels_do_not_enter_model_input(self):
        case=make_scenario('completed_passes',100)
        changed=replace(case,truth=np.full(FRAMES,'D'))
        self.assertFalse(hasattr(case.observation,'truth'))
        self.assertFalse(hasattr(case.observation,'labels'))
        for model in MODELS:
            np.testing.assert_array_equal(predict(case.observation,model),predict(changed.observation,model))

    def test_prediction_does_not_open_files(self):
        case=make_scenario('long_occlusions',100)
        with patch.object(builtins,'open',side_effect=AssertionError('Unexpected file access')):
            for model in MODELS:
                labels=predict(case.observation,model)
                self.assertEqual(len(labels),FRAMES)
                self.assertTrue(set(labels)<=set('HADX'))

    def test_perfect_oracle_scores_one(self):
        truth=make_scenario('clean_control',100).truth
        result=score(truth,truth)
        for key in ('spell_f1','macro_f1','dead_f1','coverage','transition_f1_25f'):
            self.assertAlmostEqual(result[key],1)
        self.assertEqual(result['boundary_mae_ms'],0)

    def test_all_abstention_is_not_reported_as_accurate(self):
        truth=make_scenario('clean_control',100).truth
        result=score(truth,np.full(len(truth),'X'))
        self.assertEqual(result['coverage'],0)
        self.assertEqual(result['macro_f1'],0)
        self.assertEqual(result['spell_f1'],0)
        self.assertIsNone(result['boundary_mae_ms'])

    def test_known_transition_delay_is_measured_in_milliseconds(self):
        truth=np.array(list('H'*100+'A'*100+'D'*100+'H'*100))
        delayed=np.r_[np.repeat(truth[0],10),truth[:-10]]
        result=score(truth,delayed)
        self.assertEqual(result['matched_transitions'],3)
        self.assertAlmostEqual(result['boundary_mae_ms'],400)
        self.assertAlmostEqual(result['signed_latency_ms'],400)

if __name__=='__main__':
    unittest.main()
