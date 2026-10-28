"""Pre-specified independent-seed synthetic stress test; not external validation."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import joblib
import numpy as np
import pandas as pd
from backend.app.config import DATA, ARTIFACTS, REPORTS
from ml.data import generate
from ml.features import make_features, partitions
from ml.train import conformal_quantile, interval, predict
NEW_SEEDS = (20261029, 20261030)

def metrics(y, lower, upper, opened, peak):
    y = np.asarray(y)
    lower, upper, opened, peak = map(np.asarray, (lower, upper, opened, peak))
    covered = (y >= lower) & (y <= upper)
    return {'overall_coverage': float(covered.mean()), 'open_coverage': float(covered[opened == 1].mean()), 'closed_coverage': float(covered[opened == 0].mean()), 'open_peak_coverage': float(covered[(opened == 1) & (peak == 1)].mean()), 'open_other_coverage': float(covered[(opened == 1) & (peak == 0)].mean()), 'mean_width': float(np.mean(upper - lower)), 'open_mean_width': float(np.mean((upper - lower)[opened == 1])), 'n': int(len(y)), 'open_n': int((opened == 1).sum())}

def study():
    original = pd.read_csv(DATA / 'synthetic/order_events.csv', parse_dates=['timestamp'])
    bundles = joblib.load(ARTIFACTS / 'demand-v1.joblib')
    report = {'design': 'Independent synthetic seed evaluation; same generator, not external/real-world validation', 'source_seed': 42, 'evaluation_seeds': list(NEW_SEEDS), 'horizons': {}, 'nominal_coverage': 0.9}
    for horizon in (1, 2):
        bundle = bundles[horizon]
        ca = partitions(make_features(original, horizon))['calibration']
        calpred = predict(bundle['model'], bundle['name'], ca)
        residuals = np.abs(ca.y.to_numpy() - calpred)
        group_q = {str(p): conformal_quantile(residuals[(ca.open == 1) & (ca.peak == p)]) for p in (0, 1)}
        legacy_q = {str(p): conformal_quantile(residuals[ca.peak == p]) for p in (0, 1)}
        report['horizons'][str(horizon * 30)] = {'calibration_open_n': int((ca.open == 1).sum()), 'open_only_quantiles': group_q, 'legacy_quantiles': legacy_q, 'by_seed': {}}
    for seed in NEW_SEEDS:
        fresh = generate(seed=seed)['order_events']
        for horizon in (1, 2):
            te = partitions(make_features(fresh, horizon))['test']
            bundle = bundles[horizon]
            pred = predict(bundle['model'], bundle['name'], te)
            group_q = report['horizons'][str(horizon * 30)]['open_only_quantiles']
            legacy_q = report['horizons'][str(horizon * 30)]['legacy_quantiles']
            legacy_l, legacy_u = interval(pred, te.peak, legacy_q, te.open)
            adjusted_l, adjusted_u = interval(pred, te.peak, group_q, te.open)
            report['horizons'][str(horizon * 30)]['by_seed'][str(seed)] = {'baseline': metrics(te.y, legacy_l, legacy_u, te.open, te.peak), 'open_only': metrics(te.y, adjusted_l, adjusted_u, te.open, te.peak)}
    report['caveat'] = 'Seed-shifted synthetic tests were not used to fit quantiles, but share the same simulated mechanism. This is not evidence of coverage on real restaurants; further independent periods or data are needed.'
    (REPORTS / 'independent_coverage_study.json').write_text(json.dumps(report, indent=2, ensure_ascii=False))
    return report
if __name__ == '__main__':
    print(json.dumps(study(), indent=2, ensure_ascii=False))
