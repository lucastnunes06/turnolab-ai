"""Inference reads only observed history and explicitly pre-announced promotions."""
import hashlib
import json
import time
from functools import lru_cache
import joblib
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
from backend.app.config import ARTIFACTS, DEMO_AS_OF, REPORTS
from backend.app.db import rows
from ml.features import make_features, FEATURES
from ml.train import predict, interval

@lru_cache
def load_demand(version=None):
    registry = json.loads((ARTIFACTS / 'registry.json').read_text())
    version = version or registry['champion']
    meta = registry['versions'][version]
    path = ARTIFACTS / meta['file']
    if path.parent != ARTIFACTS or hashlib.sha256(path.read_bytes()).hexdigest() != meta['sha256']:
        raise ValueError('Artifact checksum mismatch')
    return (version, joblib.load(path))

@lru_cache
def load_inventory():
    return joblib.load(ARTIFACTS / 'inventory-v1.joblib')

@lru_cache
def report(name):
    if name not in ['demand', 'stock', 'rag', 'experiments', 'agents', 'load', 'checks', 'data_quality']:
        raise ValueError('Unknown report')
    path = REPORTS / (name + '.json')
    return json.loads(path.read_text()) if path.exists() else {'status': 'not-executed'}

def origin_features(db, rid, origin=DEMO_AS_OF):
    history = rows(db, 'SELECT * FROM order_events WHERE restaurant_id=? AND timestamp<=? ORDER BY timestamp DESC LIMIT 800', (rid, origin))
    if len(history) < 674:
        raise ValueError('Insufficient historical observations')
    data = pd.DataFrame(list(reversed(history)))
    data['timestamp'] = pd.to_datetime(data.timestamp)
    last = data.iloc[-1].to_dict()
    if last['timestamp'] != pd.Timestamp(origin):
        raise ValueError('Replay origin not observed')
    for h in [1, 2]:
        target = pd.Timestamp(origin) + pd.Timedelta(minutes=30 * h)
        ts = target.isoformat()
        scheduled = db.execute('SELECT promotion FROM promotion_calendar WHERE restaurant_id=? AND timestamp=? AND known_at<=?', (rid, ts, origin)).fetchone()
        data = pd.concat([data, pd.DataFrame([{**last, 'timestamp': target, 'orders': np.nan, 'promotion': float(scheduled[0]) if scheduled else 0.0}])], ignore_index=True)
    return ({h: make_features(data, h).loc[lambda f: f.origin == pd.Timestamp(origin)] for h in [1, 2]}, history[0])

def forecast(db, rid, origin=DEMO_AS_OF, persist=True):
    start = time.perf_counter()
    version, bundles = load_demand()
    fs, last = origin_features(db, rid, origin)
    results = []
    with threadpool_limits(limits=1):
        for h in [1, 2]:
            b, f = (bundles[h], fs[h])
            point = predict(b['model'], b['name'], f)
            lo, hi = interval(point, f.peak, b['quantiles'], f.open)
            entry = dict(horizon_minutes=h * 30, target=f.target.iloc[0].isoformat(), point=round(float(point[0]), 2), lower=round(float(lo[0]), 2), upper=round(float(hi[0]), 2), model=b['name'], model_version=version, nominal_coverage=b['nominal_coverage'], empirical_coverage=report('demand')['coverage'][str(h * 30)], feature_values={c: round(float(f[c].iloc[0]), 3) for c in FEATURES}, source_max=origin, promotion_source='calendar announced at least one day earlier')
            results.append(entry)
            if persist:
                db.execute('INSERT OR IGNORE INTO demand_forecasts(restaurant_id,origin,target,model_id,point,lower,upper) VALUES(?,?,?,?,?,?,?)', (rid, origin, entry['target'], version, entry['point'], entry['lower'], entry['upper']))
    elapsed = (time.perf_counter() - start) * 1000
    if persist:
        db.execute('INSERT INTO inference_aggregates(restaurant_id,model_id,count,total_ms) VALUES(?,?,?,?)', (rid, version, 2, elapsed))
    return dict(restaurant_id=rid, origin=origin, forecasts=results, latency_ms=elapsed, current=dict(staff=last['staff'], capacity=last['capacity'], orders=last['orders']), sum_60_minutes=round(sum((r['point'] for r in results)), 2), limitations=['Intervals refer to each future half hour; summing bounds does not give joint 90% coverage.', 'Coverage during open hours is below nominal. Synthetic replay, not a live forecast.'])

def inventory(db, rid, origin=DEMO_AS_OF):
    stocks = rows(db, 'SELECT s.*,i.name,i.safety_stock FROM inventory_snapshots s JOIN ingredients i ON i.id=s.ingredient_id\n    WHERE s.restaurant_id=? AND s.timestamp=(SELECT MAX(timestamp) FROM inventory_snapshots WHERE restaurant_id=? AND timestamp<=?)\n    ORDER BY s.ingredient_id', (rid, rid, origin))
    rates = {r['ingredient_id']: r['rate'] for r in rows(db, 'SELECT ingredient_id,SUM(quantity*mix_weight) rate FROM recipes JOIN products ON products.id=recipes.product_id GROUP BY ingredient_id')}
    bundle = load_inventory()
    features, _ = origin_features(db, rid, origin)
    f = features[1]
    with threadpool_limits(limits=1):
        demand = float(predict(bundle['forecaster'], 'gradient', f)[0])
        for s in stocks:
            elapsed_orders = db.execute('SELECT COALESCE(SUM(orders),0) FROM order_events WHERE restaurant_id=? AND timestamp>? AND timestamp<=?', (rid, s['timestamp'], origin)).fetchone()[0]
            s['on_hand'] = max(0, s['on_hand'] - elapsed_orders * rates[s['ingredient_id']])
            s.update(consumption_rate=rates[s['ingredient_id']], demand_forecast=demand, rolling_4=float(f.rolling_4.iloc[0]), hour=float(f.hour.iloc[0]))
            s['forecast_consumption'] = demand * s['lead_intervals'] * s['consumption_rate']
            X = pd.DataFrame([s])[bundle['features']]
            raw = bundle['model'].predict_proba(X)[:, 1].reshape(-1, 1)
            p = float(bundle['calibrator'].predict_proba(raw)[0, 1])
            s.update(probability=p, threshold=bundle['threshold'], rule_critical=s['on_hand'] + s['supply'] - s['forecast_consumption'] < s['safety_stock'], critical=p >= bundle['threshold'], model_version='inventory-v1', snapshot_age_minutes=(pd.Timestamp(origin) - pd.Timestamp(s['timestamp'])).total_seconds() / 60, projected_balance=s['on_hand'] + s['supply'] - s['forecast_consumption'], lead_minutes=s['lead_intervals'] * 30)
    return dict(items=stocks, origin=origin, method='Frozen day-30 demand forecaster + calibrated classifier; no future observations.')

def drift(db, rid):
    _, bundles = load_demand()
    reference = bundles[1]['reference']
    f, _ = origin_features(db, rid)
    data = pd.DataFrame(rows(db, 'SELECT timestamp,orders,capacity FROM order_events WHERE restaurant_id=? AND timestamp<=? ORDER BY timestamp', (rid, DEMO_AS_OF)))
    data['timestamp'] = pd.to_datetime(data.timestamp)
    data['lag_0'] = data.orders
    data['rolling_4'] = data.orders.rolling(4).mean()
    baseline = data[data.timestamp < pd.Timestamp('2026-07-25')]
    recent = data[data.timestamp > pd.Timestamp(DEMO_AS_OF) - pd.Timedelta(days=7)]
    out = []
    for c in reference:
        bins = np.unique(np.r_[-np.inf, baseline[c].quantile([0.1, 0.25, 0.5, 0.75, 0.9]).to_numpy(), np.inf])
        a = np.histogram(baseline[c].dropna(), bins)[0].astype(float)
        b = np.histogram(recent[c].dropna(), bins)[0].astype(float)
        a = np.maximum(a / max(a.sum(), 1), 1e-05)
        b = np.maximum(b / max(b.sum(), 1), 1e-05)
        value = float(((b - a) * np.log(b / a)).sum())
        out.append(dict(feature=c, psi=value, alert=value > 0.2, threshold=0.2))
    return dict(features=out, method='Population Stability Index, per restaurant, training reference vs recent 7 days; heuristic alert threshold 0.2.', performance_alert=report('demand')['coverage']['30']['open_coverage'] < 0.9, performance_message='Open-hour interval coverage below nominal; recalibration needs a fresh holdout.')
