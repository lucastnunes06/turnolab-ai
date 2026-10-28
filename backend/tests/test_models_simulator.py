import json
import unittest
import numpy as np
import pandas as pd
from pydantic import ValidationError
from backend.app.config import DATA, REPORTS
from ml.data import generate
from ml.features import FEATURES, START, make_features, partitions
from ml.train import conformal_quantile, metrics
from simulator.engine import Scenario, simulate, compare

class TemporalTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.events = generate(days=20, restaurants=1)['order_events']

    def test_future_orders_do_not_change_features(self):
        a = self.events.copy()
        b = a.copy()
        origin = a.timestamp.iloc[800]
        b.loc[b.timestamp > origin, 'orders'] = 99999
        for h in [1, 2]:
            left = make_features(a, h).query('origin == @origin')[FEATURES]
            right = make_features(b, h).query('origin == @origin')[FEATURES]
            pd.testing.assert_frame_equal(left, right)

    def test_partition_purge(self):
        frame = make_features(pd.read_csv(DATA / 'synthetic/order_events.csv', parse_dates=['timestamp']), 2)
        splits = partitions(frame)
        self.assertLess(splits['train'].target.max(), splits['validation'].origin.min())
        self.assertLess(splits['validation'].target.max(), splits['calibration'].origin.min())
        self.assertLess(splits['calibration'].target.max(), splits['test'].origin.min())
        for data in splits.values():
            self.assertTrue((data.source_max <= data.origin).all())

    def test_conformal_finite_sample(self):
        self.assertEqual(conformal_quantile(np.arange(100)), 91)
        with self.assertRaises(ValueError):
            conformal_quantile([1, 2])

    def test_zero_denominator(self):
        self.assertIsNone(metrics([0, 0], [1, 1])['wape'])

    def test_evaluation_artifacts(self):
        d = json.loads((REPORTS / 'demand.json').read_text())
        self.assertEqual(len(d['models']), 14)
        self.assertEqual(sum((m['selected'] for m in d['models'])), 2)
        for m in d['models']:
            self.assertGreater(m['mae'], 0)
        for c in d['coverage'].values():
            self.assertTrue(0 <= c['empirical'] <= 1)
        s = json.loads((REPORTS / 'stock.json').read_text())
        for m in s['models'].values():
            self.assertEqual(sum((sum(x) for x in m['confusion_matrix'])), m['n'])
            self.assertTrue(0 <= m['pr_auc'] <= 1)

class SimulationTests(unittest.TestCase):

    def test_conservation_and_capacity(self):
        s = Scenario(staff=2, kitchen_capacity=50, demand=[40, 40], stock_orders=1000)
        r = simulate(s)
        self.assertEqual(r['processed'], 48)
        self.assertEqual(r['backlog'], 32)
        self.assertEqual(r['processed'] + r['backlog'], 80)
        self.assertEqual(r['total_cost'], 48 + 48 * 8)

    def test_stock_is_limiting(self):
        r = simulate(Scenario(staff=5, kitchen_capacity=60, demand=[40, 40], stock_orders=20))
        self.assertEqual(r['processed'], 20)
        self.assertEqual(r['backlog'], 60)
        self.assertTrue(r['stock_insufficient'])

    def test_delivery_cannot_arrive_early(self):
        s = Scenario(staff=3, kitchen_capacity=50, demand=[20, 20], stock_orders=0, replenishment_orders=100, replenishment_after=2)
        self.assertEqual(simulate(s)['processed'], 0)
        s.replenishment_after = 1
        self.assertEqual(simulate(s)['timeline'][0]['processed'], 0)
        self.assertEqual(simulate(s)['timeline'][1]['processed'], 36)

    def test_more_staff_cannot_overcome_physical_limit(self):
        a = Scenario(staff=3, kitchen_capacity=25, demand=[40, 40])
        b = a.model_copy(update={'staff': 5})
        r = compare(a, b)
        self.assertEqual(r['delta']['backlog'], 0)
        self.assertGreater(r['delta']['cost'], 0)

    def test_invalid_input(self):
        for change in [{'demand': [-1]}, {'staff': 0}, {'stock_orders': float('nan')}, {'kitchen_capacity': float('inf')}, {'extra': 'shell'}]:
            with self.subTest(change=change), self.assertRaises(ValidationError):
                Scenario.model_validate({'staff': 2, 'kitchen_capacity': 40, 'demand': [20], **change})
