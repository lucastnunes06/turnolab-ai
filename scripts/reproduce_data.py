"""Verify synthetic CSV determinism in a fresh temporary directory, without retraining ML.

This check is independent of the already generated database and model artifacts.
It does not assert that a complete ML training run has been repeated.
"""
import hashlib
import json
import tempfile
import time
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ml.data import generate, validate

def main():
    began = time.perf_counter()
    expected_path = ROOT / 'reports/data_quality.json'
    if not expected_path.exists():
        raise SystemExit('Missing recorded baseline; run `python scripts/bootstrap.py` first')
    baseline = json.loads(expected_path.read_text(encoding='utf-8'))
    tables = generate()
    validation = validate(tables)
    with tempfile.TemporaryDirectory(prefix='turnolab-data-repro-') as directory:
        hashes = {}
        for name, table in tables.items():
            path = Path(directory) / (name + '.csv')
            table.to_csv(path, index=False)
            hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    ok = bool(validation['valid']) and hashes == baseline['sha256']
    result = {'status': 'passed' if ok else 'failed', 'rows': validation['rows'], 'schema_valid': validation['valid'], 'dataset_hashes_match': hashes == baseline['sha256'], 'fresh_training_reproduced': False, 'scope': 'Independent regeneration of all six synthetic CSVs; compares SHA-256 with recorded baseline', 'seconds': round(time.perf_counter() - began, 3)}
    (ROOT / 'reports/data_reproduction.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if ok else 1)
if __name__ == '__main__':
    main()
