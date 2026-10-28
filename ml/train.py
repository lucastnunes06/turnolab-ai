"""Chronological training, selection, conformal calibration, then isolated final test."""
import hashlib
import importlib.util
import json
import math
import time
import warnings
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.inspection import permutation_importance
from threadpoolctl import threadpool_limits
from backend.app.config import DATA, ARTIFACTS, REPORTS
from backend.app.db import session
from ml.features import FEATURES, START, make_features, partitions
from ml.tracking import log_run

def metrics(y, pred):
    y, pred = (np.asarray(y), np.asarray(pred))
    denominator = float(np.abs(y).sum())
    return dict(mae=float(np.abs(y - pred).mean()), rmse=float(np.sqrt(((y - pred) ** 2).mean())), wape=float(np.abs(y - pred).sum() / denominator) if denominator else None, n=len(y))

def predict(model, name, data):
    if name == 'last':
        p = data.lag_0.to_numpy()
    elif name == 'moving_average':
        p = data.rolling_4.to_numpy()
    elif name == 'seasonal':
        p = data.seasonal_week.to_numpy()
    else:
        p = model.predict(data[FEATURES])
    return np.maximum(0, p) * data.open.to_numpy()

def conformal_quantile(residuals, alpha=0.1):
    n = len(residuals)
    if n < 30:
        raise ValueError('Insufficient calibration data')
    return float(np.quantile(residuals, min(1, math.ceil((n + 1) * (1 - alpha)) / n), method='higher'))

def interval(point, peak, quantiles, opened):
    q = np.array([quantiles[str(int(p))] for p in peak])
    lower = np.maximum(0, point - q) * np.asarray(opened)
    upper = (point + q) * np.asarray(opened)
    return (lower, upper)

def train():
    began = time.perf_counter()
    events = pd.read_csv(DATA / 'synthetic/order_events.csv', parse_dates=['timestamp'])
    all_metrics, predictions, bundles, importances = ([], [], {}, {})
    walk = []
    with threadpool_limits(limits=1):
        for horizon in [1, 2]:
            f = make_features(events, horizon)
            split = partitions(f)
            tr, va, ca, te = [split[k] for k in ['train', 'validation', 'calibration', 'test']]
            candidates = {'last': None, 'moving_average': None, 'seasonal': None, 'ridge': make_pipeline(StandardScaler(), Ridge(alpha=10)), 'random_forest': RandomForestRegressor(n_estimators=40, max_depth=12, min_samples_leaf=15, random_state=42, n_jobs=1), 'gradient_boosting_15': HistGradientBoostingRegressor(max_iter=120, max_leaf_nodes=15, learning_rate=0.08, l2_regularization=5, random_state=42), 'gradient_boosting_31': HistGradientBoostingRegressor(max_iter=120, max_leaf_nodes=31, learning_rate=0.08, l2_regularization=5, random_state=42)}
            validation = {}
            for name, model in candidates.items():
                started = time.perf_counter()
                if model is not None:
                    model.fit(tr[FEATURES], tr.y)
                validation[name] = metrics(va.y, predict(model, name, va))
                validation[name]['fit_seconds'] = time.perf_counter() - started
            champion = min(validation, key=lambda n: validation[n]['mae'])
            model = candidates[champion]
            calpred = predict(model, champion, ca)
            q = {str(p): conformal_quantile(np.abs(ca.y.to_numpy()[ca.peak == p] - calpred[ca.peak == p])) for p in [0, 1]}
            for name, candidate in candidates.items():
                pred = predict(candidate, name, te)
                row = dict(horizon_minutes=horizon * 30, model=name, selected=name == champion, validation_mae=validation[name]['mae'], fit_seconds=validation[name]['fit_seconds'], **metrics(te.y, pred))
                all_metrics.append(row)
                log_run('demand', dict(horizon=horizon, model=name, seed=42, train_end='2026-07-25', selected=name == champion), row, '')
            pred = predict(model, champion, te)
            lower, upper = interval(pred, te.peak, q, te.open)
            result = te[['restaurant_id', 'origin', 'target', 'hour', 'peak', 'y']].copy()
            result['prediction'], result['lower'], result['upper'] = (pred, lower, upper)
            result['covered'] = (result.y >= lower) & (result.y <= upper)
            result['horizon_minutes'] = horizon * 30
            result['model'] = champion
            predictions.append(result)
            for end in [40, 47, 54]:
                trainfold = f[f.target < START + pd.Timedelta(days=end)].dropna(subset=FEATURES + ['y'])
                vfold = f[(f.origin >= START + pd.Timedelta(days=end)) & (f.target < START + pd.Timedelta(days=end + 7))].dropna(subset=FEATURES + ['y'])
                m = HistGradientBoostingRegressor(max_iter=80, max_leaf_nodes=15, l2_regularization=5, random_state=42)
                m.fit(trainfold[FEATURES], trainfold.y)
                walk.append(dict(horizon_minutes=horizon * 30, train_end_day=end, **metrics(vfold.y, predict(m, 'gradient', vfold))))
            sample = va[va.open == 1].sample(min(800, int((va.open == 1).sum())), random_state=42)
            if model is not None:
                importance = permutation_importance(model, sample[FEATURES], sample.y, n_repeats=2, random_state=42, scoring='neg_mean_absolute_error')
                importances[str(horizon * 30)] = sorted([dict(feature=n, mae_increase=float(v)) for n, v in zip(FEATURES, importance.importances_mean)], key=lambda x: -x['mae_increase'])
            else:
                importances[str(horizon * 30)] = []
            bundles[horizon] = dict(model=model, name=champion, quantiles=q, features=FEATURES, nominal_coverage=0.9, train_end='2026-07-25', calibration_end='2026-08-12', reference={c: tr[c].quantile([0.1, 0.25, 0.5, 0.75, 0.9]).tolist() for c in ['lag_0', 'rolling_4', 'capacity']})
    artifact = ARTIFACTS / 'demand-v1.joblib'
    joblib.dump(bundles, artifact)
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    registry = dict(champion='demand-v1', challenger=None, versions={'demand-v1': dict(file=artifact.name, sha256=digest)}, promotion_rule='Lower validation MAE; then calibration and frozen final evaluation. Manual registry update; no automatic test-based promotion.')
    (ARTIFACTS / 'registry.json').write_text(json.dumps(registry, indent=2))
    pred = pd.concat(predictions, ignore_index=True)
    pred.to_csv(REPORTS / 'demand_predictions.csv', index=False)
    pd.DataFrame(all_metrics).to_csv(REPORTS / 'demand_comparison.csv', index=False)
    segments = []
    for (h, r), g in pred.groupby(['horizon_minutes', 'restaurant_id']):
        segments.append(dict(horizon_minutes=int(h), segment=f'restaurant_{r}', coverage=float(g.covered.mean()), **metrics(g.y, g.prediction)))
    for (h, hour), g in pred.groupby(['horizon_minutes', 'hour']):
        segments.append(dict(horizon_minutes=int(h), segment=f'hour_{hour}', coverage=float(g.covered.mean()), **metrics(g.y, g.prediction)))
    for (h, peak), g in pred.groupby(['horizon_minutes', 'peak']):
        segments.append(dict(horizon_minutes=int(h), segment=f'peak_{peak}', coverage=float(g.covered.mean()), **metrics(g.y, g.prediction)))
    pd.DataFrame(segments).to_csv(REPORTS / 'demand_segments.csv', index=False)
    coverage = {str(h): dict(nominal=0.9, empirical=float(g.covered.mean()), mean_width=float((g.upper - g.lower).mean()), peak_coverage=float(g[g.peak == 1].covered.mean()), open_coverage=float(g[g.hour.between(10, 23)].covered.mean())) for h, g in pred.groupby('horizon_minutes')}
    fig, axs = plt.subplots(1, 2, figsize=(12, 4), layout='constrained')
    for h, g in pred.groupby('horizon_minutes'):
        axs[0].hist(g.y - g.prediction, bins=70, alpha=0.5, label=f'{h} min')
    axs[0].set(title='Residuals on isolated synthetic test', xlabel='Observed minus forecast', ylabel='Intervals')
    axs[0].legend()
    comp = pd.DataFrame(all_metrics)
    c = comp[comp.horizon_minutes == 30]
    axs[1].barh(c.model, c.mae, color=['#20a87a' if s else '#8b9bba' for s in c.selected])
    axs[1].set(xlabel='MAE (orders / 30 min)', title='Same chronological test, all candidates')
    fig.savefig(REPORTS / 'demand_evaluation.png', dpi=160)
    plt.close(fig)
    report = dict(seed=42, models=all_metrics, coverage=coverage, walk_forward=walk, feature_importance=importances, split={k: dict(rows=len(v), origin_min=str(v.origin.min()), origin_max=str(v.origin.max()), target_max=str(v.target.max())) for k, v in split.items()}, seconds=time.perf_counter() - began, artifact_sha256=digest, mlflow_available=bool(importlib.util.find_spec('mlflow')), caveat='Synthetic data; conformal exchangeability is not guaranteed under temporal drift. Closed-hour zeros inflate overall coverage.')
    (REPORTS / 'demand.json').write_text(json.dumps(report, indent=2))
    with session() as db:
        db.execute('INSERT OR REPLACE INTO model_versions VALUES(?,?,?,?,?)', ('demand-v1', 'demand', 'champion', json.dumps(report), digest))
    print(json.dumps(dict(champions={h: b['name'] for h, b in bundles.items()}, coverage=coverage, seconds=report['seconds']), indent=2))
if __name__ == '__main__':
    warnings.filterwarnings('ignore', category=FutureWarning)
    train()
