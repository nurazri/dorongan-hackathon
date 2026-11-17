"""Submission parsing safeguards; inference remains frozen Control v5."""
from pathlib import Path
import sys
import tempfile
import unittest
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from lab.export_submission import load_tracking,write_frozen_csv


class SubmissionExportTests(unittest.TestCase):
    def test_frozen_csv_bytes_use_explicit_crlf(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'submission.csv'
            write_frozen_csv(path,['H','X','D'])
            self.assertEqual(path.read_bytes(),b'frame,label\r\n0,H\r\n1,X\r\n2,D\r\n')

    def load(self, text, n=2):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'tracking.txt'
            path.write_text(text, encoding='utf-8')
            return load_tracking(path,np.array([0,1]),n)

    def test_out_of_order_tracking_keeps_frame_alignment(self):
        xy=self.load('2:0.2,0.3,0;0.7,0.4,0:0.4,0.5,0\n1:0.1,0.2,0;0.8,0.3,0:0.3,0.4,0\n')
        self.assertEqual(xy.dtype,np.dtype('float32'))
        np.testing.assert_allclose(xy[:, -1],[[.3,.4],[.4,.5]])

    def test_duplicate_frame_rejected(self):
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            self.load('1:0,0,0;0,0,0:0,0,0\n1:0,0,0;0,0,0:0,0,0\n')

    def test_missing_frame_rejected(self):
        with self.assertRaisesRegex(ValueError,'missing'):
            self.load('1:0,0,0;0,0,0:0,0,0\n')

    def test_wrong_track_count_rejected(self):
        with self.assertRaisesRegex(ValueError,'Track count'):
            self.load('1:0,0,0:0,0,0\n')

    def test_frame_outside_contract_rejected(self):
        with self.assertRaisesRegex(ValueError,'invalid'):
            self.load('0:0,0,0;0,0,0:0,0,0\n')

if __name__=='__main__':unittest.main()
