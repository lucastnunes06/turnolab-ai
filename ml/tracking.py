"""Always-on SQLite experiment ledger; optional MLflow integration, explicitly reported."""
import importlib.util
import json
import uuid
from backend.app.db import session

def log_run(kind, params, metrics, artifact):
    run_id = str(uuid.uuid4())
    with session() as db:
        db.execute('INSERT INTO experiment_runs(id,kind,params,metrics,artifact) VALUES(?,?,?,?,?)', (run_id, kind, json.dumps(params), json.dumps(metrics), str(artifact)))
    if importlib.util.find_spec('mlflow'):
        import mlflow
        mlflow.set_tracking_uri('sqlite:///mlflow.db')
        mlflow.set_experiment('turnolab-' + kind)
        with mlflow.start_run(run_name=run_id):
            mlflow.log_params(params)
            mlflow.log_metrics({k: v for k, v in metrics.items() if isinstance(v, (int, float)) and v is not None})
            if artifact:
                mlflow.log_artifact(str(artifact))
    return run_id
