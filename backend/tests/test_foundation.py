import copy
import tempfile
import unittest
from pathlib import Path
import pandas as pd
from backend.app.db import migrate, session
from ml.data import generate, ingest, validate
from scripts.bootstrap import register_models

class FoundationTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tables = generate(days=3, restaurants=2)

    def test_reproducible(self):
        self.assertTrue(self.tables['order_events'].equals(generate(days=3, restaurants=2)['order_events']))
        self.assertTrue(validate(self.tables)['valid'])

    def test_quality_failures(self):
        for problem in ['negative', 'duplicate', 'foreign', 'unit', 'order', 'missing', 'time', 'gap']:
            with self.subTest(problem=problem):
                data = copy.deepcopy(self.tables)
                events = data['order_events']
                if problem == 'negative':
                    events.loc[0, 'orders'] = -1
                elif problem == 'duplicate':
                    events.loc[1, 'id'] = events.loc[0, 'id']
                elif problem == 'foreign':
                    events.loc[0, 'restaurant_id'] = 100
                elif problem == 'unit':
                    data['inventory_snapshots'].loc[0, 'unit'] = 'g'
                elif problem == 'order':
                    data['order_events'] = events.iloc[::-1]
                elif problem == 'missing':
                    events.loc[0, 'orders'] = float('nan')
                elif problem == 'time':
                    events.loc[0, 'timestamp'] += pd.Timedelta(minutes=1)
                else:
                    data['order_events'] = events.drop(2)
                self.assertFalse(validate(data)['valid'])

    def test_migration_and_ingest(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'test.db'
            migrate(path)
            migrate(path)
            with session(path) as db:
                ingest(self.tables, db)
                self.assertEqual(db.execute('SELECT COUNT(*) FROM order_events').fetchone()[0], 288)
                register_models(db)
                self.assertEqual(db.execute('SELECT COUNT(*) FROM model_versions').fetchone()[0], 3)
                with self.assertRaises(ValueError):
                    ingest(self.tables, db)
