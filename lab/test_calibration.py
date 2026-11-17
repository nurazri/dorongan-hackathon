from unittest import TestCase
import numpy as np
from lab.control_v2 import infer_control,PARAMETERS
from lab.sportec_adapter import load_match

class CalibrationIsolationTests(TestCase):
    def test_parameter_override_preserves_original_defaults(self):
        original=PARAMETERS.copy()
        ball=np.tile([.5,.5],(100,1));near=np.tile([.5,6.],(100,1))
        before=infer_control(ball,near,[],[(1,0,99)])[0]
        infer_control(ball,near,[],[(1,0,99)],parameters={'control_dwell_s':2.})
        after=infer_control(ball,near,[],[(1,0,99)])[0]
        self.assertEqual(PARAMETERS,original)
        np.testing.assert_array_equal(before,after)

    def test_validation_match_is_not_opened_by_training_loader(self):
        with self.assertRaisesRegex(ValueError,'allowed'):load_match('J03WPY')

    def test_final_held_out_remains_blocked_even_with_validation_flag(self):
        for match in ('J03WN1','J03WOY'):
            with self.assertRaisesRegex(ValueError,'allowed'):load_match(match,allow_validation=True)
