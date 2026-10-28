"""Local CI-equivalent checks. Never claims a remote GitHub Actions run."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def main():
    if not (ROOT / '.data/turnolab.db').exists() or not (ROOT / '.data/synthetic/order_events.csv').exists():
        print('Prerequisite not found: run `python scripts/bootstrap.py` before `python scripts/check.py`.')
        raise SystemExit(2)
    commands = [[sys.executable, 'scripts/style_check.py'], ['python', '-m', 'compileall', '-q', 'backend', 'ml', 'ai', 'simulator', 'scripts'], ['python', '-m', 'unittest', 'discover', '-s', 'backend/tests', '-v'], ['python', 'scripts/ui_fixture.py'], ['npm', '--prefix', 'frontend', 'run', 'check'], ['npm', '--prefix', 'frontend', 'test'], ['npm', '--prefix', 'frontend', 'run', 'build'], ['python', 'scripts/security_check.py']]
    results = []
    for command in commands:
        if command[0] == 'python':
            command[0] = sys.executable
        start = time.perf_counter()
        r = subprocess.run(command, cwd=ROOT, env={**os.environ, 'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1'}, capture_output=True, text=True)
        results.append(dict(command=command, exit_code=r.returncode, seconds=time.perf_counter() - start, output=(r.stdout + r.stderr)[-8000:]))
        print('PASS' if r.returncode == 0 else 'FAIL', ' '.join(command))
        if r.returncode:
            break
    report = dict(passed=all((r['exit_code'] == 0 for r in results)) and len(results) == len(commands), checks=results, remote_ci_executed=False, scope='Local execution of checks corresponding to workflow steps')
    (ROOT / 'reports/checks.json').write_text(json.dumps(report, indent=2))
    if not report['passed']:
        print(results[-1]['output'])
        raise SystemExit(1)
if __name__ == '__main__':
    main()
