"""Execute release checks, retain logs and fail honestly on blocked requirements.
This script never installs dependencies, publishes a repository or sends notifications.
"""
import argparse
import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import re
import socket
import subprocess
import sys
import time
import uuid
import httpx
ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / 'reports'

def command(args, timeout=180, env=None):
    start = time.perf_counter()
    try:
        r = subprocess.run(args, cwd=ROOT, env=env, capture_output=True, text=True, timeout=timeout, check=False)
        output = r.stdout + r.stderr
        restricted = any((word in output.lower() for word in ['operation not permitted', 'permission denied', 'could not bind', 'eacces', 'err_blocked_by_administrator', 'blocked by administrator']))
        status = 'passed' if r.returncode == 0 else 'blocked' if restricted else 'failed'
        return {'status': status, 'command': args, 'exit_code': r.returncode, 'seconds': time.perf_counter() - start, 'output': output[-16000:]}
    except subprocess.TimeoutExpired:
        return {'status': 'failed', 'command': args, 'reason': 'Execution exceeded its explicit time limit', 'seconds': time.perf_counter() - start}
    except (OSError, PermissionError) as exc:
        return {'status': 'blocked', 'command': args, 'reason': str(exc), 'seconds': time.perf_counter() - start}

def tcp_check():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.bind(('127.0.0.1', 0))
            port = listener.getsockname()[1]
    except OSError as exc:
        return {'status': 'blocked', 'reason': str(exc), 'live_http_executed': False}
    log_path = REPORTS / 'tcp-server.log'
    with log_path.open('w') as log:
        process = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'backend.app.main:app', '--host', '127.0.0.1', '--port', str(port)], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        try:
            began = time.perf_counter()
            with httpx.Client(base_url=f'http://127.0.0.1:{port}', trust_env=False, timeout=5.0) as client:
                for _ in range(60):
                    if process.poll() is not None:
                        raise RuntimeError('Owned Uvicorn process exited before readiness')
                    try:
                        if client.get('/ready').status_code == 200:
                            break
                    except httpx.HTTPError:
                        pass
                    time.sleep(0.2)
                else:
                    raise RuntimeError('Uvicorn readiness timed out')
                paths = ['/health', '/ready', '/api/restaurants', '/api/restaurants/1/history', '/api/restaurants/1/forecast', '/api/restaurants/1/inventory', '/openapi.json', '/docs', '/']
                measured = []
                for path in paths:
                    start = time.perf_counter()
                    r = client.get(path, headers={'Authorization': 'Bearer turnolab-demo'})
                    r.raise_for_status()
                    measured.append({'path': path, 'status': r.status_code, 'milliseconds': (time.perf_counter() - start) * 1000})
                assert client.get('/api/restaurants').status_code == 401
            return {'status': 'passed', 'live_http_executed': True, 'port': port, 'requests': measured, 'seconds': time.perf_counter() - began}
        except Exception as exc:
            return {'status': 'failed', 'reason': str(exc), 'live_http_executed': False}
        finally:
            process.terminate()
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

def docker_check():
    binary = shutil.which('docker')
    if not binary:
        return {'status': 'blocked', 'reason': 'Docker CLI not installed'}
    env = {k: v for k, v in os.environ.items() if k not in ['DOCKER_HOST', 'DOCKER_CONTEXT', 'DOCKER_TLS', 'DOCKER_TLS_VERIFY', 'DOCKER_CERT_PATH']}
    docker = [binary, '--host=unix:///var/run/docker.sock']
    preflight = command(docker + ['info', '--format', '{{.ServerVersion}}'], timeout=10, env=env)
    if preflight['status'] != 'passed':
        return {'status': preflight['status'], 'reason': 'Managed Docker socket check failed', 'preflight': preflight}
    image = 'turnolab-release:' + uuid.uuid4().hex[:10]
    build = docker + ['build', '-f', 'backend/Dockerfile', '-t', image]
    cert = os.getenv('CODEX_PROXY_CERT')
    if cert:
        build += ['--secret', 'id=proxy_ca,src=' + cert]
    built = command(build + ['.'], timeout=600, env=env)
    if built['status'] != 'passed':
        return {'status': built['status'], 'build': built}
    name = 'turnolab-release-' + uuid.uuid4().hex[:10]
    created = command(docker + ['run', '-d', '--name', name, '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges:true', '-p', '127.0.0.1::8000', image], timeout=20, env=env)
    if created['status'] != 'passed':
        return {'status': created['status'], 'container': created}
    try:
        inspected = command(docker + ['inspect', '--format', '{{json .NetworkSettings.Ports}}', name], timeout=10, env=env)
        port = json.loads(inspected['output'])['8000/tcp'][0]['HostPort']
        with httpx.Client(base_url='http://127.0.0.1:' + str(port), trust_env=False, timeout=5) as client:
            for _ in range(150):
                try:
                    response = client.get('/ready')
                    if response.status_code == 200:
                        dashboard = client.get('/')
                        overview = client.get('/api/restaurants/1/overview', headers={'Authorization': 'Bearer turnolab-demo'})
                        dashboard.raise_for_status()
                        overview.raise_for_status()
                        return {'status': 'passed', 'image': image, 'readiness': response.json(), 'overview_http_status': overview.status_code, 'build_seconds': built['seconds']}
                except httpx.HTTPError:
                    pass
                time.sleep(1)
        return {'status': 'failed', 'reason': 'Container did not reach readiness', 'logs': command(docker + ['logs', '--tail', '50', name], timeout=10, env=env)}
    except Exception as exc:
        return {'status': 'failed', 'reason': str(exc)}
    finally:
        command(docker + ['rm', '-f', name], timeout=20, env=env)

def github_check(run_url=None):
    """Read an existing authorized workflow run; never publish or trigger a run."""
    if not run_url:
        return {'status': 'blocked', 'reason': 'No workflow run URL supplied; code has not been published by this script.'}
    match = re.fullmatch('https://github\\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/actions/runs/([0-9]+)', run_url)
    if not match:
        return {'status': 'failed', 'reason': 'Expected a canonical github.com Actions run URL'}
    head = command(['git', 'rev-parse', 'HEAD'], timeout=5)
    if head['status'] != 'passed':
        return {'status': 'blocked', 'reason': 'A real local source commit is required to match remote CI evidence'}
    dirty = command(['git', 'status', '--porcelain', '--', 'backend', 'ml', 'ai', 'simulator', 'scripts', 'frontend'], timeout=5)
    if dirty['status'] != 'passed' or dirty['output'].strip():
        return {'status': 'blocked', 'reason': 'Local source differs from its commit; remote CI would not verify this snapshot'}
    owner, repo, run_id = match.groups()
    headers = {'Accept': 'application/vnd.github+json'}
    token = os.getenv('GITHUB_TOKEN')
    if token:
        headers['Authorization'] = 'Bearer ' + token
    try:
        with httpx.Client(timeout=12.0, follow_redirects=False) as client:
            response = client.get(f'https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}', headers=headers)
            response.raise_for_status()
            run = response.json()
        if run.get('head_sha') != head['output'].strip():
            return {'status': 'failed', 'reason': 'Remote workflow SHA does not match local source commit', 'url': run_url}
        passed = run.get('status') == 'completed' and run.get('conclusion') == 'success'
        return {'status': 'passed' if passed else 'failed', 'url': run_url, 'head_sha': run['head_sha'], 'workflow_status': run.get('status'), 'conclusion': run.get('conclusion')}
    except (httpx.HTTPError, ValueError, KeyError):
        return {'status': 'blocked', 'reason': 'Could not read the specified workflow run; check network and repository access'}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--skip-demo', action='store_true')
    parser.add_argument('--github-run-url')
    args = parser.parse_args()
    REPORTS.mkdir(exist_ok=True)
    began = time.perf_counter()
    stages = {}
    env = {**os.environ, 'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1'}
    stages['bootstrap'] = command([sys.executable, 'scripts/bootstrap.py'], timeout=900, env=env)
    print('Bootstrap:', stages['bootstrap']['status'], flush=True)
    if stages['bootstrap']['status'] != 'passed':
        stages['local_ci'] = {'status': 'blocked', 'reason': 'Bootstrap did not finish; run python scripts/bootstrap.py and inspect the failure first'}
        result = {'complete': False, 'local_checks_passed': False, 'stages': stages, 'executed_at': datetime.now(timezone.utc).isoformat(), 'seconds': time.perf_counter() - began, 'external_publication_performed': False}
        (REPORTS / 'release.json').write_text(json.dumps(result, indent=2))
        raise SystemExit(2)
    stages['local_ci'] = command([sys.executable, 'scripts/check.py'], env=env)
    print('Local CI:', stages['local_ci']['status'], flush=True)
    stages['data_reproduction'] = command([sys.executable, 'scripts/reproduce_data.py'], timeout=90, env=env)
    print('Data reproduction:', stages['data_reproduction']['status'], flush=True)
    stages['http_tcp'] = tcp_check()
    print('HTTP/TCP:', stages['http_tcp']['status'], flush=True)
    stages['browser'] = command([sys.executable, 'scripts/browser_check.py'], timeout=90, env=env)
    print('Browser:', stages['browser']['status'], flush=True)
    if stages['browser']['status'] == 'passed' and (not args.skip_demo):
        stages['demo'] = command([sys.executable, 'scripts/capture_demo.py'], timeout=180, env=env)
    else:
        stages['demo'] = {'status': 'blocked', 'reason': 'Browser not verified or demo explicitly skipped'}
    stages['mlflow'] = command([sys.executable, 'scripts/mlflow_check.py'], timeout=60, env=env)
    if stages['mlflow'].get('exit_code') == 2:
        stages['mlflow']['status'] = 'blocked'
    print('MLflow:', stages['mlflow']['status'], flush=True)
    stages['docker'] = docker_check()
    print('Docker:', stages['docker']['status'], flush=True)
    stages['github_actions'] = github_check(args.github_run_url)
    stages['external_llm'] = {'status': 'not_configured', 'required': False, 'reason': 'Provider optional; contract tests use MockTransport and are not live-provider validation.'}
    result = {'complete': all((s['status'] == 'passed' for s in stages.values() if s.get('required', True))), 'local_checks_passed': stages['local_ci']['status'] == 'passed', 'stages': stages, 'executed_at': datetime.now(timezone.utc).isoformat(), 'seconds': time.perf_counter() - began, 'external_publication_performed': False}
    (REPORTS / 'release.json').write_text(json.dumps(result, indent=2))
    print(json.dumps({k: v['status'] for k, v in stages.items()}, indent=2))
    raise SystemExit(0 if result['complete'] else 2)
if __name__ == '__main__':
    main()
