"""Register an actual alternate model without promoting by final-test results."""
import hashlib
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from threadpoolctl import threadpool_limits
from backend.app.config import ARTIFACTS, DATA, REPORTS
from backend.app.db import session
from ml.features import FEATURES, make_features, partitions
from ml.train import conformal_quantile, predict, metrics

def main():
    events = pd.read_csv(DATA / 'synthetic/order_events.csv', parse_dates=['timestamp'])
    bundles = {}
    valid = []
    ncal = 0
    with threadpool_limits(limits=1):
        for h in [1, 2]:
            split = partitions(make_features(events, h))
            tr, va, ca = [split[k] for k in ['train', 'validation', 'calibration']]
            m = RandomForestRegressor(n_estimators=40, max_depth=12, min_samples_leaf=15, random_state=42, n_jobs=1)
            m.fit(tr[FEATURES], tr.y)
            p = predict(m, 'random_forest', ca)
            q = {str(k): conformal_quantile(np.abs(ca.y.to_numpy()[ca.peak == k] - p[ca.peak == k])) for k in [0, 1]}
            valid.append(metrics(va.y, predict(m, 'random_forest', va))['mae'])
            ncal += len(ca)
            bundles[h] = dict(model=m, name='random_forest', quantiles=q, features=FEATURES, nominal_coverage=0.9, train_end='2026-07-25', calibration_end='2026-08-12', reference={c: tr[c].quantile([0.1, 0.25, 0.5, 0.75, 0.9]).tolist() for c in ['lag_0', 'rolling_4', 'capacity']})
    path = ARTIFACTS / 'demand-rf-v1.joblib'
    joblib.dump(bundles, path)
    registry = json.loads((ARTIFACTS / 'registry.json').read_text())
    registry['challenger'] = 'demand-rf-v1'
    registry['history'] = ['demand-v1']
    champion = json.loads((REPORTS / 'demand.json').read_text())
    registry['versions']['demand-v1'].update(validation_mae=float(np.mean([x['validation_mae'] for x in champion['models'] if x['selected']])), features=FEATURES, calibration_n=ncal)
    registry['versions']['demand-rf-v1'] = dict(file=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest(), validation_mae=float(np.mean(valid)), features=FEATURES, calibration_n=ncal)
    (ARTIFACTS / 'registry.json').write_text(json.dumps(registry, indent=2))
    with session() as db:
        db.execute('INSERT OR REPLACE INTO model_versions VALUES(?,?,?,?,?)', ('demand-rf-v1', 'demand', 'challenger', json.dumps({'validation_mae': float(np.mean(valid))}), registry['versions']['demand-rf-v1']['sha256']))
    print(json.dumps({v: r['validation_mae'] for v, r in registry['versions'].items()}, indent=2))
if __name__ == '__main__':
    main()
