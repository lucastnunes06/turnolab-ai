"""Second ML task: critical ingredient level before replenishment. Forecasts are OOS."""
import hashlib
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score, f1_score, average_precision_score, brier_score_loss, confusion_matrix
from threadpoolctl import threadpool_limits
from backend.app.config import DATA, ARTIFACTS, REPORTS
from backend.app.db import session
from ml.features import FEATURES, START, make_features
from ml.train import predict
from ml.tracking import log_run
STOCK_FEATURES = ['on_hand', 'supply', 'lead_intervals', 'forecast_consumption', 'safety_stock', 'consumption_rate', 'demand_forecast', 'rolling_4', 'hour']

def assess(y, prob, decision):
    matrix = confusion_matrix(y, decision, labels=[0, 1]).tolist()
    return dict(precision=float(precision_score(y, decision, zero_division=0)), recall=float(recall_score(y, decision, zero_division=0)), f1=float(f1_score(y, decision, zero_division=0)), pr_auc=float(average_precision_score(y, prob)), brier=float(brier_score_loss(y, prob)), confusion_matrix=matrix, hypothetical_error_cost=matrix[1][0] * 60 + matrix[0][1] * 12, n=len(y))

def build_dataset():
    events = pd.read_csv(DATA / 'synthetic/order_events.csv', parse_dates=['timestamp'])
    f = make_features(events, 1).dropna(subset=FEATURES)
    training = f[f.target < START + pd.Timedelta(days=30)].dropna(subset=['y'])
    forecaster = HistGradientBoostingRegressor(max_iter=100, max_leaf_nodes=15, l2_regularization=5, random_state=43)
    forecaster.fit(training[FEATURES], training.y)
    f = f[f.day >= 30].copy()
    f['demand_forecast'] = predict(forecaster, 'gradient', f)
    inventory = pd.read_csv(DATA / 'synthetic/inventory_snapshots.csv', parse_dates=['timestamp'])
    products = pd.read_csv(DATA / 'synthetic/products.csv')
    recipes = pd.read_csv(DATA / 'synthetic/recipes.csv').merge(products, left_on='product_id', right_on='id')
    recipes['consumption_rate'] = recipes.quantity * recipes.mix_weight
    rates = recipes.groupby('ingredient_id').consumption_rate.sum()
    ingredients = pd.read_csv(DATA / 'synthetic/ingredients.csv')
    inventory = inventory.merge(ingredients[['id', 'safety_stock']], left_on='ingredient_id', right_on='id', suffixes=('', '_ingredient'))
    inventory['consumption_rate'] = inventory.ingredient_id.map(rates)
    d = inventory.merge(f[['restaurant_id', 'origin', 'demand_forecast', 'rolling_4', 'hour', 'day']], left_on=['restaurant_id', 'timestamp'], right_on=['restaurant_id', 'origin'])
    d['forecast_consumption'] = d.demand_forecast * d.lead_intervals * d.consumption_rate
    rng = np.random.default_rng(4242)
    labels = []
    for r, g in d.groupby('restaurant_id', sort=True):
        timeline = events[events.restaurant_id == r].set_index('timestamp').orders
        for row in g.itertuples():
            future = pd.date_range(row.timestamp + pd.Timedelta(minutes=30), periods=row.lead_intervals, freq='30min')
            obs = timeline.reindex(future)
            if obs.isna().any():
                labels.append((row.Index, np.nan))
                continue
            consumed = float(obs.sum()) * row.consumption_rate * rng.lognormal(-0.01, 0.12)
            supplied = row.supply * int(rng.random() < 0.82)
            labels.append((row.Index, int(row.on_hand + supplied - consumed < row.safety_stock)))
    d['y'] = pd.Series(dict(labels))
    return (d.dropna(subset=['y']), forecaster)

def train():
    with threadpool_limits(limits=1):
        d, forecaster = build_dataset()
        tr = d[d.day < 58]
        va = d[(d.day >= 58) & (d.day < 65)]
        ca = d[(d.day >= 65) & (d.day < 69)]
        th = d[(d.day >= 69) & (d.day < 72)]
        te = d[d.day >= 72]
        candidates = {n: HistGradientBoostingClassifier(max_iter=100, max_leaf_nodes=n, l2_regularization=10, random_state=42) for n in [7, 15]}
        scores = {}
        for n, m in candidates.items():
            m.fit(tr[STOCK_FEATURES], tr.y)
            scores[n] = float(average_precision_score(va.y, m.predict_proba(va[STOCK_FEATURES])[:, 1]))
        selected = max(scores, key=scores.get)
        model = candidates[selected]
        calibrator = LogisticRegression(C=1.0)
        calibrator.fit(model.predict_proba(ca[STOCK_FEATURES])[:, 1].reshape(-1, 1), ca.y)

        def probability(x):
            return calibrator.predict_proba(model.predict_proba(x[STOCK_FEATURES])[:, 1].reshape(-1, 1))[:, 1]
        pv = probability(th)
        thresholds = np.arange(0.15, 0.81, 0.05)
        threshold = float(min(thresholds, key=lambda t: assess(th.y, pv, pv >= t)['hypothetical_error_cost']))
        p = probability(te)
        score = (te.forecast_consumption + te.safety_stock - te.on_hand - te.supply) / np.maximum(te.forecast_consumption, 1)
        rp = 1 / (1 + np.exp(np.clip(-4 * score, -500, 500)))
        rule = (score >= 0).to_numpy()
        hybrid = (p >= threshold) | rule
        result = {'rule': assess(te.y, rp, rule), 'classifier': assess(te.y, p, p >= threshold), 'hybrid': assess(te.y, np.maximum(p, rp), hybrid)}
        bins = []
        for lo in np.arange(0, 1, 0.1):
            mask = (p >= lo) & (p < lo + 0.1)
            if mask.any():
                bins.append(dict(lower=float(lo), mean_probability=float(p[mask].mean()), observed=float(te.y.to_numpy()[mask].mean()), n=int(mask.sum())))
        report = dict(models=result, selected_leaf_nodes=selected, validation_pr_auc=scores, threshold=threshold, calibration=bins, positive_rate=float(te.y.mean()), splits={k: len(x) for k, x in [('train', tr), ('validation', va), ('calibration', ca), ('threshold', th), ('test', te)]}, feature_contract='Frozen demand model trained on days <30. Stock features at origin; future orders used only as labels.', label_limit='Snapshots are synthetic independent operational states, not a continuous replenishment policy evaluation.')
        (REPORTS / 'stock.json').write_text(json.dumps(report, indent=2))
        artifact = ARTIFACTS / 'inventory-v1.joblib'
        joblib.dump(dict(model=model, calibrator=calibrator, forecaster=forecaster, threshold=threshold, features=STOCK_FEATURES), artifact)
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        with session() as db:
            db.execute('INSERT OR REPLACE INTO model_versions VALUES(?,?,?,?,?)', ('inventory-v1', 'inventory', 'champion', json.dumps(report), digest))
        for n, m in result.items():
            log_run('inventory', dict(strategy=n, threshold=threshold, seed=4242), m, REPORTS / 'stock.json')
        te = te.copy()
        te['probability'] = p
        te['rule'] = rule
        te.to_csv(REPORTS / 'stock_predictions.csv', index=False)
        print(json.dumps(result, indent=2))
if __name__ == '__main__':
    train()
