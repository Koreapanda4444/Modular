import os
import json
from utils.colors import warn

PACKS_DIR = "packs"

def scan_packs():
    packs = {}

    if not os.path.exists(PACKS_DIR):
        return packs

    for name in os.listdir(PACKS_DIR):
        path = os.path.join(PACKS_DIR, name)
        manifest = os.path.join(path, "manifest.json")

        if not os.path.isdir(path) or not os.path.exists(manifest):
            continue

        try:
            with open(manifest, "r", encoding="utf-8") as f:
                data = json.load(f)

            packs[name] = {
                "id": name,
                "path": path,
                "meta": data
            }
        except:
            warn(f"{name}: manifest 로딩 실패")

    return packs

def get_pack(pack_id: str):
    return scan_packs().get(pack_id)
