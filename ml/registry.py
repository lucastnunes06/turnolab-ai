"""Local champion/challenger registry with explicit validation gate and rollback history."""
import argparse
import hashlib
import json
from pathlib import Path
from backend.app.config import ARTIFACTS, REPORTS
from ml.inference import load_demand

def transition(registry_path, version, rollback=False):
    path = Path(registry_path)
    registry = json.loads(path.read_text())
    if version not in registry['versions']:
        raise ValueError('Unregistered model')
    meta = registry['versions'][version]
    artifact = path.parent / meta['file']
    if artifact.parent != path.parent or hashlib.sha256(artifact.read_bytes()).hexdigest() != meta['sha256']:
        raise ValueError('Checksum mismatch')
    history = registry.setdefault('history', [registry['champion']])
    if rollback:
        if version not in history:
            raise ValueError('Rollback requires previously promoted version')
    else:
        old = registry['versions'][registry['champion']]
        if meta.get('validation_mae', float('inf')) >= old.get('validation_mae', float('-inf')):
            raise ValueError('Promotion rejected: validation MAE must improve')
        if meta.get('features') != old.get('features'):
            raise ValueError('Feature contract changed')
        if meta.get('calibration_n', 0) < 30:
            raise ValueError('Insufficient calibration observations')
    previous = registry['champion']
    registry['champion'] = version
    history.append(version)
    registry['last_transition'] = dict(previous=previous, current=version, rollback=rollback, criterion='validation MAE, feature contract, checksum, calibration sample size')
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(registry, indent=2))
    temporary.replace(path)
    load_demand.cache_clear()
    return registry['last_transition']

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['list', 'promote', 'rollback'])
    parser.add_argument('version', nargs='?')
    args = parser.parse_args()
    path = ARTIFACTS / 'registry.json'
    if args.operation == 'list':
        print(path.read_text())
        return
    if not args.version:
        parser.error('version required')
    print(json.dumps(transition(path, args.version, args.operation == 'rollback'), indent=2))
if __name__ == '__main__':
    main()
