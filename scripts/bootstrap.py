"""Idempotent local bootstrap: migrate, generate if absent, train if absent, evaluate."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.config import DATA, ARTIFACTS, REPORTS
from backend.app.db import migrate, session
from ml.data import generate, ingest, save

def run(module):
    result = subprocess.run([sys.executable, '-m', module], cwd=ROOT, check=False, env={**os.environ, 'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1'})
    if result.returncode:
        raise SystemExit(result.returncode)

def register_models(db):
    """Synchronize bundled artifacts into a newly-created database without retraining."""
    registry = json.loads((ARTIFACTS / 'registry.json').read_text())
    specs = [('demand-v1', 'demand', 'demand.json'), ('demand-rf-v1', 'demand', None), ('inventory-v1', 'inventory', 'stock.json')]
    for version, kind, report_name in specs:
        artifact = ARTIFACTS / (version + '.joblib')
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        if version in registry['versions'] and digest != registry['versions'][version]['sha256']:
            raise ValueError('Bundled artifact checksum mismatch')
        metrics = json.loads((REPORTS / report_name).read_text()) if report_name else {'validation_mae': registry['versions'][version]['validation_mae']}
        status = 'champion' if kind == 'inventory' or version == registry['champion'] else 'challenger'
        db.execute('INSERT INTO model_versions(id,kind,status,metrics,artifact_hash) VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET kind=excluded.kind,status=excluded.status,metrics=excluded.metrics,artifact_hash=excluded.artifact_hash', (version, kind, status, json.dumps(metrics), digest))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--retrain', action='store_true')
    args = parser.parse_args()
    migrate()
    with session() as db:
        populated = db.execute('SELECT COUNT(*) FROM restaurants').fetchone()[0]
        if not populated:
            tables = generate()
            save(tables, DATA / 'synthetic')
            ingest(tables, db)
        db.execute("INSERT OR IGNORE INTO promotion_calendar SELECT restaurant_id,timestamp,promotion,strftime('%Y-%m-%dT%H:%M:%S',timestamp,'-1 day') FROM order_events")
    if args.retrain or not (ARTIFACTS / 'demand-v1.joblib').exists() or (not (ARTIFACTS / 'registry.json').exists()) or (not (REPORTS / 'demand.json').exists()):
        run('ml.train')
    if args.retrain or not (ARTIFACTS / 'inventory-v1.joblib').exists() or (not (REPORTS / 'stock.json').exists()):
        run('ml.stock')
    if args.retrain or not (ARTIFACTS / 'demand-rf-v1.joblib').exists():
        run('ml.challenger')
    with session() as db:
        register_models(db)
    run('ai.rag')
    run('ml.experiments')
    run('ai.evaluate_agents')
    print('Bootstrap complete. Start: python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000')
if __name__ == '__main__':
    main()
