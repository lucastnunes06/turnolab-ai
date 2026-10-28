"""Run only trusted local artifacts. Execute from this folder: python predict.py."""
import hashlib
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/'manifest.json').read_text())
path=ROOT/manifest['file']
assert hashlib.sha256(path.read_bytes()).hexdigest()==manifest['sha256'],'Checksum mismatch'
bundle=joblib.load(path)[1]
X=pd.DataFrame(json.loads((ROOT/'example_input.json').read_text()))[bundle['features']]
with threadpool_limits(limits=1):point=np.maximum(0,bundle['model'].predict(X))*X.open.to_numpy()
# The example belongs to peak time. Production must derive the peak flag from target time.
q=bundle['quantiles']['1']
print(json.dumps(dict(horizon_minutes=30,point=point.tolist(),lower=np.maximum(0,point-q).tolist(),upper=(point+q).tolist(),nominal_coverage=.9,synthetic=True),indent=2))
