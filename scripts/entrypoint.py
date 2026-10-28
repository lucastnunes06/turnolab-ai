import os
import subprocess
import sys
subprocess.run([sys.executable, 'scripts/bootstrap.py'], check=True)
os.execvp(sys.executable, [sys.executable, '-m', 'uvicorn', 'backend.app.main:app', '--host', '0.0.0.0', '--port', '8000'])
