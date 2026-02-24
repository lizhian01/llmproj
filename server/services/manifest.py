import json
from pathlib import Path
from typing import Dict, List, Optional

from server.services.paths import KBS_DIR, MANIFEST_PATH


DEFAULT_MANIFEST = {"kbs": []}


def ensure_manifest() -> Dict:
    KBS_DIR.mkdir(parents=True, exist_ok=True)
    if not MANIFEST_PATH.exists():
        save_manifest(DEFAULT_MANIFEST)
    return load_manifest()


def load_manifest() -> Dict:
    if not MANIFEST_PATH.exists():
        return DEFAULT_MANIFEST.copy()
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def save_manifest(data: Dict) -> None:
    KBS_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def find_kb(manifest: Dict, kb_id: str) -> Optional[Dict]:
    for kb in manifest.get("kbs", []):
        if kb.get("kb_id") == kb_id:
            return kb
    return None


def upsert_kb(manifest: Dict, entry: Dict) -> None:
    kbs: List[Dict] = manifest.get("kbs", [])
    for i, kb in enumerate(kbs):
        if kb.get("kb_id") == entry.get("kb_id"):
            kbs[i] = entry
            manifest["kbs"] = kbs
            return
    kbs.append(entry)
    manifest["kbs"] = kbs
