"""Prepare a local Hugging Face folder. Never publishes or creates a remote repository."""
import hashlib
import json
import shutil
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.config import ARTIFACTS, REPORTS

def main():
    output = ARTIFACTS / 'huggingface'
    output.mkdir(exist_ok=True)
    shutil.copy2(ARTIFACTS / 'demand-v1.joblib', output / 'model.joblib')
    shutil.copy2(ROOT / 'docs/MODEL_CARD.md', output / 'README.md')
    shutil.copy2(ROOT / 'LICENSE', output / 'LICENSE')
    shutil.copy2(REPORTS / 'demand.json', output / 'evaluation.json')
    fixture = json.loads((ROOT / '.data/ui_fixture.json').read_text())
    features = fixture['data']['forecast']['forecasts'][0]['feature_values']
    (output / 'example_input.json').write_text(json.dumps([features], indent=2))
    manifest = dict(file='model.joblib', sha256=hashlib.sha256((output / 'model.joblib').read_bytes()).hexdigest(), version='demand-v1', python='3.12.14', published=False)
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    (output / 'requirements.txt').write_text('numpy==2.3.5\npandas==2.2.3\nscikit-learn==1.8.0\njoblib==1.5.3\n')
    print('Local model folder prepared:', output)
if __name__ == '__main__':
    main()
