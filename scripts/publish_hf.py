"""Publish an explicitly authorized and locally trained synthetic model to Hugging Face.

Requires HF_TOKEN, HF_REPO_ID and HF_PUBLISH_CONFIRM=publish.
Run bootstrap and scripts/export_hf.py first. Never commits credentials to Git.
"""
import hashlib
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "artifacts" / "huggingface"

def check_manifest():
    manifest = json.loads((FOLDER / "manifest.json").read_text(encoding="utf-8"))
    model = FOLDER / "model.joblib"
    if not model.is_file():
        raise FileNotFoundError("Run python scripts/bootstrap.py and python scripts/export_hf.py first")
    if hashlib.sha256(model.read_bytes()).hexdigest() != manifest["sha256"]:
        raise ValueError("Model checksum mismatch; refusing to publish")
    for required in ("README.md", "predict.py", "evaluation.json", "requirements.txt", "LICENSE"):
        if not (FOLDER / required).is_file():
            raise FileNotFoundError(f"Missing required export: {required}")
    return manifest

def main():
    repo_id = os.getenv("HF_REPO_ID", "")
    token = os.getenv("HF_TOKEN", "")
    if not re.fullmatch(r"[A-Za-z0-9][\w.-]{0,60}/[A-Za-z0-9][\w.-]{0,90}", repo_id):
        raise SystemExit("HF_REPO_ID must be set to YOUR Hugging Face namespace/model")
    if os.getenv("HF_PUBLISH_CONFIRM") != "publish":
        raise SystemExit("Refusing to publish: set HF_PUBLISH_CONFIRM=publish deliberately")
    if not token:
        raise SystemExit("HF_TOKEN is required; use a fine-grained token or GitHub Actions secret")
    manifest = check_manifest()
    from huggingface_hub import HfApi
    api = HfApi(token=token)
    api.create_repo(repo_id=repo_id, repo_type="model", private=False, exist_ok=True)
    info = api.upload_folder(
        repo_id=repo_id,
        repo_type="model",
        folder_path=str(FOLDER),
        allow_patterns=["README.md", "LICENSE", "evaluation.json", "example_input.json", "manifest.json", "model.joblib", "predict.py", "requirements.txt"],
        commit_message="Publish synthetic TurnoLab demand forecasting model and evaluation",
    )
    published = set(api.list_repo_files(repo_id, repo_type="model"))
    required = {"README.md", "model.joblib", "evaluation.json", "manifest.json", "predict.py"}
    if not required.issubset(published):
        raise SystemExit("Upload returned but required files not all visible on Hugging Face")
    print(json.dumps({"published": True, "model_url": "https://huggingface.co/" + repo_id,
                      "sha256": manifest["sha256"], "commit_url": str(getattr(info, "commit_url", ""))},
                     indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
