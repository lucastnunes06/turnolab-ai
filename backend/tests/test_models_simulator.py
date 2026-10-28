import json
import unittest
import numpy as np
import pandas as pd
from pydantic import ValidationError
from backend.app.config import DATA, REPORTS
from ml.data import generate
from ml.features import FEATURES, START, make_features, partitions
from ml.train import conformal_quantile, calibrate_open_hours, interval, metrics
from simulator.engine import Scenario, simulate, compare
from ml.experiments import admissible_actions, MAX_ADDITIONAL_STAFF

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

    def test_open_hour_calibration_ignores_closed_zero_residuals(self):
        open_only = pd.DataFrame({'y': [float(v) for v in range(40)] + [float(v) for v in range(40, 80)], 'peak': [0] * 40 + [1] * 40, 'open': [1] * 80})
        expected = calibrate_open_hours(open_only, np.zeros(80))
        combined = pd.concat([open_only, pd.DataFrame({'y': [0.0] * 100, 'peak': [0] * 100, 'open': [0] * 100})], ignore_index=True)
        actual = calibrate_open_hours(combined, np.zeros(180))
        self.assertEqual(expected, actual)
        self.assertGreater(expected['0'], 0)
        self.assertGreater(expected['1'], expected['0'])

    def test_open_calibration_requires_sufficient_each_group(self):
        insufficient = pd.DataFrame({'y': [1.0] * 40, 'peak': [0] * 40, 'open': [1] * 40})
        with self.assertRaises(ValueError):
            calibrate_open_hours(insufficient, np.zeros(40))
        with self.assertRaises(ValueError):
            calibrate_open_hours(insufficient, np.zeros(39))

    def test_closed_intervals_are_zero(self):
        lower, upper = interval(np.array([9.0, 9.0]), np.array([0, 0]), {'0': 3.0}, np.array([0, 1]))
        self.assertEqual((lower[0], upper[0]), (0, 0))
        self.assertEqual((lower[1], upper[1]), (6, 12))

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

class StaffingPolicyTests(unittest.TestCase):

    def test_recorded_experiment_respects_staffing_limit(self):
        report = json.loads((REPORTS / 'experiments.json').read_text())
        self.assertEqual(report['max_additional_staff'], MAX_ADDITIONAL_STAFF)
        self.assertEqual(report['feasible_actions'], 6)
        self.assertTrue(all((r['policy_compliance'] == 1 for r in report['strategies'])))
        recorded = pd.read_csv(REPORTS / 'decision_scenarios.csv', usecols=['extra_staff', 'policy_compliance'])
        self.assertLessEqual(int(recorded.extra_staff.max()), MAX_ADDITIONAL_STAFF)
        self.assertTrue(recorded.policy_compliance.all())

    def test_solver_and_oracle_share_feasible_action_space(self):
        options = admissible_actions()
        self.assertEqual(MAX_ADDITIONAL_STAFF, 2)
        self.assertEqual(len(options), 6)
        self.assertEqual({action[0] for action in options}, {0, 1, 2})
        self.assertEqual({action[1] for action in options}, {0.0, 60.0})
        with self.assertRaises(ValueError):
            admissible_actions(3)
        with self.assertRaises(ValueError):
            admissible_actions(-1)

    def test_constrained_solver_never_chooses_forbidden_staff(self):
        base = dict(staff=3, kitchen_capacity=90, demand=[80, 80], stock_orders=500)
        options = admissible_actions()
        chosen = min(options, key=lambda a: simulate(Scenario(**{**base, 'staff': base['staff'] + a[0], 'replenishment_orders': a[1]}))['total_cost'])
        self.assertLessEqual(chosen[0], 2)
        self.assertLessEqual(base['staff'] + chosen[0], base['staff'] + MAX_ADDITIONAL_STAFF)
