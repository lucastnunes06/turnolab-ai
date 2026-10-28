import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from ml.registry import transition

class RegistryTests(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'registry.json'
        for v in ['a', 'b']:
            (self.path.parent / (v + '.joblib')).write_bytes(v.encode())
        self.registry = {'champion': 'a', 'history': ['a'], 'versions': {v: {'file': v + '.joblib', 'sha256': hashlib.sha256(v.encode()).hexdigest(), 'validation_mae': score, 'features': ['lag_0'], 'calibration_n': 100} for v, score in [('a', 3.0), ('b', 2.9)]}}
        self.save()

    def save(self):
        self.path.write_text(json.dumps(self.registry))

    def tearDown(self):
        self.temp.cleanup()

    def test_promotion_then_rollback(self):
        self.assertEqual(transition(self.path, 'b')['current'], 'b')
        self.assertEqual(transition(self.path, 'a', True)['current'], 'a')

    def test_reject_worse_validation(self):
        self.registry['versions']['b']['validation_mae'] = 4.0
        self.save()
        with self.assertRaisesRegex(ValueError, 'MAE'):
            transition(self.path, 'b')

    def test_reject_unverified_checksum(self):
        (self.path.parent / 'b.joblib').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'Checksum'):
            transition(self.path, 'b')

    def test_no_rollback_to_never_promoted(self):
        with self.assertRaisesRegex(ValueError, 'previously'):
            transition(self.path, 'b', True)

    def test_reject_changed_feature_contract(self):
        self.registry['versions']['b']['features'] = ['future_orders']
        self.save()
        with self.assertRaisesRegex(ValueError, 'Feature'):
            transition(self.path, 'b')
