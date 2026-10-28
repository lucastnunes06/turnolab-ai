"""Create a compact, measured evidence index. Never infers execution from file existence."""
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def main():
    files = {}
    for directory in ['backend', 'ml', 'ai', 'simulator', 'scripts', 'frontend', 'docs']:
        for path in (ROOT / directory).rglob('*'):
            if not path.is_file() or any((x in path.parts for x in ['__pycache__', 'dist', 'node_modules'])):
                continue
            files[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    release_path = ROOT / 'reports/release.json'
    release = json.loads(release_path.read_text()) if release_path.exists() else {}
    verified = lambda name: release.get('stages', {}).get(name, {}).get('status') == 'passed'
    result = dict(release=release, source_sha256=files, checks=json.loads((ROOT / 'reports/checks.json').read_text()), reproduction=json.loads((ROOT / 'reports/reproduction.json').read_text()), browser_verified=verified('browser'), docker_verified=verified('docker'), remote_ci_executed=verified('github_actions'), external_llm_executed=verified('external_llm'), mlflow_executed=verified('mlflow'), note='Source hashes bind the evidence index to this delivered snapshot. No remote publication or production claim.')
    (ROOT / 'reports/evidence.json').write_text(json.dumps(result, indent=2))
    print('Evidence index written for', len(files), 'files')
if __name__ == '__main__':
    main()
