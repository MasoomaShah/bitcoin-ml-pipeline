"""
Helper: register current root artifacts as a versioned model in `models/manifest.json`.
Usage: from project root run `python scripts/register_model_version.py`
It will copy any of these files if present:
 - reg_model.pkl
 - clf_model.pkl
 - scaler.pkl
 - feature_columns.json
 - training_metadata.json
and create a version like `v20251201T120000Z_reg_model.pkl` under `models/` and update `models/manifest.json`.
"""
import os
import shutil
import json
from datetime import datetime

ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
MODELS_DIR = os.path.join(ROOT, 'models')
MANIFEST_PATH = os.path.join(MODELS_DIR, 'manifest.json')

ARTIFACTS = {
    'reg_model': 'reg_model.pkl',
    'clf_model': 'clf_model.pkl',
    'scaler': 'scaler.pkl',
    'feature_columns': 'feature_columns.json',
    'metadata': 'training_metadata.json'
}

def create_version_tag():
    return 'v' + datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')


def load_manifest():
    if not os.path.exists(MANIFEST_PATH):
        return {'active_version': None, 'versions': {}}
    with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_manifest(manifest):
    os.makedirs(MODELS_DIR, exist_ok=True)
    with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)


def register_version():
    os.makedirs(MODELS_DIR, exist_ok=True)
    version = create_version_tag()
    entry = {}
    any_copied = False

    for key, filename in ARTIFACTS.items():
        src = os.path.join(ROOT, filename)
        if os.path.exists(src):
            dest_name = f"{version}_{filename}"
            dest = os.path.join(MODELS_DIR, dest_name)
            shutil.copy2(src, dest)
            entry[key] = os.path.relpath(dest, ROOT).replace('\\', '/')
            any_copied = True
        else:
            print(f"Warning: artifact not found, skipping: {src}")

    if not any_copied:
        print("No artifacts found in project root to register. Nothing was done.")
        return None

    # try to include training metrics from metadata if present
    metrics = None
    metadata_path = os.path.join(ROOT, ARTIFACTS['metadata'])
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                metrics = metadata.get('metrics') or metadata.get('training_metrics')
        except Exception:
            pass

    manifest = load_manifest()
    manifest['versions'][version] = entry
    manifest['versions'][version]['created_at'] = datetime.utcnow().isoformat() + 'Z'
    if metrics is not None:
        manifest['versions'][version]['training_metrics'] = metrics

    # set as active by default
    manifest['active_version'] = version
    write_manifest(manifest)
    print(f"Registered version {version} with artifacts:")
    for k, v in entry.items():
        print(f" - {k}: {v}")
    print(f"Updated manifest at: {MANIFEST_PATH}")
    return version


if __name__ == '__main__':
    ver = register_version()
    if ver:
        print(f"Done. Active version set to: {ver}")
    else:
        print("No version registered.")
