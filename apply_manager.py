import os
import shutil
import zipfile
import json
from utils.colors import info

DEFAULT_TARGETS = [
    "mods",
    "config",
    "defaultconfigs",
    "kubejs",
    "datapacks",
    "generated_datapacks",
    "resourcepacks",
    "shaderpacks",
    "patchouli_books",
    "moonlight-global-datapacks",
    "fancymenu_data",
    "fancymenu_instance_data",
    "fancymenu_setups",
    "moddata",
    "options.txt",
    "servers.dat",
    "pointblanks",
    "schematics"
]


def _load_manifest(pack_path: str) -> dict:
    manifest_path = os.path.join(pack_path, "manifest.json")
    if not os.path.exists(manifest_path):
        return {}
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _get_copy_targets(pack_meta: dict | None) -> list:
    return list(DEFAULT_TARGETS)


def get_copy_targets(pack_meta: dict | None) -> list:
    return _get_copy_targets(pack_meta)


def _safe_extract_zip(zip_path: str, extract_to: str):
    """Safely extract a zip file into extract_to (prevents zip-slip)."""

    os.makedirs(extract_to, exist_ok=True)
    base = os.path.abspath(extract_to)

    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.infolist():
            if member.filename.endswith("/"):
                continue
            target_path = os.path.abspath(os.path.join(extract_to, member.filename))
            if not target_path.startswith(base + os.sep) and target_path != base:
                raise RuntimeError(f"Unsafe zip entry path: {member.filename}")
        zf.extractall(extract_to)


def _resolve_pack_source_dir(pack_path: str, targets: list[str]) -> str:
    """Return a directory that contains any of the targets.

    If the pack doesn't have e.g. pack_path/mods, but contains a .zip, extract it
    into a cache folder and use that extracted directory as the source.
    """

    for name in targets:
        if os.path.exists(os.path.join(pack_path, name)):
            return pack_path

    zips = [
        os.path.join(pack_path, f)
        for f in os.listdir(pack_path)
        if f.lower().endswith(".zip") and os.path.isfile(os.path.join(pack_path, f))
    ]
    if not zips:
        return pack_path

    # If multiple zips exist, prefer the first in sorted order for determinism.
    zips.sort()
    zip_path = zips[0]
    cache_dir = os.path.join(pack_path, ".cache")
    extracted_dir = os.path.join(cache_dir, os.path.splitext(os.path.basename(zip_path))[0])
    marker_path = os.path.join(extracted_dir, ".extracted.ok")

    zip_mtime = os.path.getmtime(zip_path)
    needs_extract = True
    if os.path.exists(marker_path):
        try:
            with open(marker_path, "r", encoding="utf-8") as f:
                saved = float(f.read().strip() or "0")
            needs_extract = saved != zip_mtime
        except Exception:
            needs_extract = True

    if needs_extract:
        info(f"팩 ZIP 압축 해제 중: {os.path.basename(zip_path)}")
        if os.path.exists(extracted_dir):
            shutil.rmtree(extracted_dir)
        os.makedirs(extracted_dir, exist_ok=True)
        _safe_extract_zip(zip_path, extracted_dir)
        with open(marker_path, "w", encoding="utf-8") as f:
            f.write(str(zip_mtime))

    return extracted_dir

def clear_environment(minecraft_path: str, targets: list[str] | None = None):
    info("기존 모드 환경 정리 중...")
    targets = targets or list(DEFAULT_TARGETS)
    for name in targets:
        path = os.path.join(minecraft_path, name)
        if os.path.isdir(path):
            shutil.rmtree(path)
            os.makedirs(path, exist_ok=True)
        elif os.path.exists(path):
            os.remove(path)

def cleanup_environment(minecraft_path: str, targets: list[str] | None = None):
    info("모드 환경 정리 중...")
    targets = targets or list(DEFAULT_TARGETS)
    for name in targets:
        path = os.path.join(minecraft_path, name)
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.exists(path):
            os.remove(path)

def apply_pack(pack_path: str, minecraft_path: str, pack_meta: dict | None = None):
    if pack_meta is None:
        pack_meta = _load_manifest(pack_path)

    targets = _get_copy_targets(pack_meta)
    src_root = _resolve_pack_source_dir(pack_path, targets)

    for name in targets:
        src = os.path.join(src_root, name)
        if not os.path.exists(src):
            continue

        dst = os.path.join(minecraft_path, name)
        info(f"{name} 적용 중...")

        if os.path.isdir(src):
            os.makedirs(dst, exist_ok=True)
            for item in os.listdir(src):
                s = os.path.join(src, item)
                t = os.path.join(dst, item)
                if os.path.isdir(s):
                    shutil.copytree(s, t, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, t)
        else:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)

    info("모드팩 적용 완료")
