"""Exercise source-only bootstrap in a fresh directory using the current interpreter.
This verifies pipeline reproducibility, not a clean dependency installation.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
ROOT = Path(__file__).resolve().parents[1]

def main():
    start = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix='turnolab-repro-') as temp:
        target = Path(temp) / 'turnolab-ai'
        shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns('.data', '.venv', '.git', 'artifacts', 'reports', 'node_modules', 'dist', '__pycache__', '*.log'))
        env = {**os.environ, 'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1'}
        with (ROOT / 'reports/reproduction.log').open('w') as log:
            for command in [[sys.executable, 'scripts/bootstrap.py'], [sys.executable, 'scripts/check.py']]:
                r = subprocess.run(command, cwd=target, env=env, stdout=log, stderr=subprocess.STDOUT, check=False)
                if r.returncode:
                    raise SystemExit('Reproduction failed; inspect reports/reproduction.log')
        original = json.loads((ROOT / 'reports/data_quality.json').read_text())
        regenerated = json.loads((target / 'reports/data_quality.json').read_text())
        d1 = json.loads((ROOT / 'reports/demand.json').read_text())
        d2 = json.loads((target / 'reports/demand.json').read_text())
        selected1 = [{k: r[k] for k in ['model', 'horizon_minutes', 'mae', 'rmse', 'wape']} for r in d1['models'] if r['selected']]
        selected2 = [{k: r[k] for k in ['model', 'horizon_minutes', 'mae', 'rmse', 'wape']} for r in d2['models'] if r['selected']]
        result = dict(passed=original['sha256'] == regenerated['sha256'] and selected1 == selected2, data_hashes_equal=original['sha256'] == regenerated['sha256'], demand_metrics_equal=selected1 == selected2, seconds=time.perf_counter() - start, scope='Source-only copy, empty data/artifacts, current installed Python packages. No fresh pip/container verification.')
        (ROOT / 'reports/reproduction.json').write_text(json.dumps(result, indent=2))
        print(json.dumps(result, indent=2))
        assert result['passed']
if __name__ == '__main__':
    main()
