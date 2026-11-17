"""Contract tests with synthetic model evidence and local HTTP integration checks."""
import hashlib
import json
import sys
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from http.server import ThreadingHTTPServer
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lab.build import decode
from lab.server import create_handler

class ModelTests(unittest.TestCase):
    def test_missing_observation_preserves_possession(self):
        evidence = np.zeros((40, 3))
        evidence[:10, 0] = 3
        evidence[30:, 0] = 3
        self.assertTrue((decode(evidence) == 0).all())

    def test_sustained_change_overcomes_transition_penalty(self):
        evidence = np.zeros((40, 3))
        evidence[:20, 0] = 3
        evidence[20:, 1] = 3
        np.testing.assert_array_equal(decode(evidence), [0]*20+[1]*20)

    def test_isolated_outlier_does_not_split_possession(self):
        evidence = np.zeros((40, 3))
        evidence[:, 0] = 3
        evidence[20] = [0, 3, 0]
        self.assertTrue((decode(evidence) == 0).all())

class LocalServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), create_handler())
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_summary_and_bounded_windows(self):
        with urlopen(self.base+'/api/summary') as response:
            summary = json.load(response)
        self.assertEqual(summary['frames'], 199319)
        for frame in [0,11185,100000,113742,199318]:
            with urlopen(self.base+f'/api/window?frame={frame}') as response:
                chunk = json.load(response)
            self.assertEqual(len(chunk['rows']), chunk['end']-chunk['start'])
            self.assertLessEqual(len(chunk['rows']), 625)
            self.assertLessEqual(chunk['start'],frame)
            self.assertGreater(chunk['end'],frame)

    def test_video_byte_range_matches_original(self):
        request = Request(self.base+'/media/tactical.mp4', headers={'Range':'bytes=100-199'})
        with urlopen(request) as response:
            self.assertEqual(response.status,206)
            self.assertEqual(response.headers['Content-Length'],'100')
            actual = response.read()
        paths = json.loads((ROOT/'local_paths.json').read_text())
        with open(paths['BAR-ATH_tactical.mp4'],'rb') as source:
            source.seek(100)
            self.assertEqual(actual,source.read(100))
        with self.assertRaises(HTTPError) as err:
            urlopen(Request(self.base+'/media/tactical.mp4',headers={'Range':'bytes=999999999999-'}))
        self.assertEqual(err.exception.code,416)

    def test_export_matches_generated_csv(self):
        with urlopen(self.base+'/api/export?model=experimental_temporal') as response:
            actual=response.read()
        expected=(ROOT/'evaluation/results/experimental_temporal.csv').read_bytes()
        self.assertEqual(hashlib.sha256(actual).digest(), hashlib.sha256(expected).digest())
        self.assertEqual(len(actual.splitlines()),199320)

    def test_control_v2_export_and_evidence(self):
        with urlopen(self.base+'/api/export?model=experimental_control_v2') as response:
            actual=response.read()
        self.assertEqual(actual,(ROOT/'evaluation/results/experimental_control_v2.csv').read_bytes())
        with urlopen(self.base+'/api/window?frame=11185') as response:
            data=json.load(response)
        for row in data['rows']:
            evidence=row['control']
            self.assertIn(evidence['candidate'], ('H','A',None))
            self.assertIsInstance(evidence['restartContext'], bool)
            self.assertIsInstance(evidence['restartMotion'], bool)

    def test_calibrated_candidate_export(self):
        with urlopen(self.base+'/api/export?model=experimental_control_v5') as response:
            self.assertEqual(response.headers['Content-Disposition'], 'attachment; filename="dorongan.csv"')
            data=response.read()
        self.assertEqual(data,(ROOT/'evaluation/results/experimental_control_v5.csv').read_bytes())
        self.assertEqual(len(data.splitlines()),199320)

    def test_unknown_export_cannot_read_arbitrary_files(self):
        with self.assertRaises(HTTPError) as err:
            urlopen(self.base+'/api/export?model=../../local_paths')
        self.assertEqual(err.exception.code,404)

    def test_external_host_is_rejected(self):
        with self.assertRaises(HTTPError) as err:
            urlopen(Request(self.base+'/api/summary', headers={'Host':'external.example'}))
        self.assertEqual(err.exception.code,403)

if __name__ == '__main__':
    unittest.main()
