"""Verify the optional real MLflow SDK with locally measured metrics and artifacts.
No provider request or remote tracking service is used.
"""
import importlib.util
import json
from pathlib import Path
import sys
import time
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def main():
    report_path = ROOT / 'reports/mlflow.json'
    if not importlib.util.find_spec('mlflow'):
        result = {'status': 'blocked', 'reason': 'mlflow package is not installed in this Python environment. Install the documented optional tracking dependencies, then rerun the check', 'live_tracking_executed': False}
        report_path.write_text(json.dumps(result, indent=2))
        print(json.dumps(result))
        raise SystemExit(2)
    import mlflow
    from mlflow import MlflowClient
    began = time.perf_counter()
    tracking_uri = (ROOT / '.data/mlflow').resolve().as_uri()
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment('turnolab-verified-evidence')
    demand = json.loads((ROOT / 'reports/demand.json').read_text())
    selected = [row for row in demand['models'] if row['selected']]
    with mlflow.start_run(run_name='locally-verified-demand-artifacts') as run:
        mlflow.log_params({'model_version': 'demand-v1', 'seed': 42, 'evidence_source': 'previously executed chronological evaluation', 'synthetic_data': True})
        for row in selected:
            h = str(row['horizon_minutes'])
            mlflow.log_metrics({f'{metric}_{h}min': row[metric] for metric in ['mae', 'rmse', 'wape']})
        for path in ['reports/demand.json', 'reports/stock.json', 'reports/demand_comparison.csv', 'reports/experiments.json', 'artifacts/registry.json', 'artifacts/demand-v1.joblib']:
            mlflow.log_artifact(str(ROOT / path))
        run_id = run.info.run_id
    client = MlflowClient(tracking_uri=tracking_uri)
    stored = client.get_run(run_id)
    assert stored.info.status == 'FINISHED'
    for row in selected:
        assert stored.data.metrics[f"mae_{row['horizon_minutes']}min"] == row['mae']
    artifacts = [a.path for a in client.list_artifacts(run_id)]
    assert 'demand-v1.joblib' in artifacts
    result = {'status': 'passed', 'live_tracking_executed': True, 'mlflow_version': mlflow.__version__, 'tracking_uri': tracking_uri, 'run_id': run_id, 'artifact_paths': artifacts, 'seconds': time.perf_counter() - began, 'scope': 'Real local MLflow SDK; imported measured evaluation and trained model artifact, not a claim that the original training occurred inside this run.'}
    report_path.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
if __name__ == '__main__':
    main()
