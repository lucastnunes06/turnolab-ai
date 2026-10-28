import os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / '.data'
ARTIFACTS = ROOT / 'artifacts'
REPORTS = ROOT / 'reports'
for directory in [DATA, ARTIFACTS, REPORTS]:
    directory.mkdir(exist_ok=True)
DEMO_AS_OF = os.getenv('DEMO_AS_OF', '2026-08-29T18:00:00')
os.environ.setdefault('MPLCONFIGDIR', str(DATA / 'matplotlib'))
