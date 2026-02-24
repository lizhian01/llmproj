from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
KBS_DIR = DATA_DIR / "kbs"
MANIFEST_PATH = KBS_DIR / "manifest.json"
