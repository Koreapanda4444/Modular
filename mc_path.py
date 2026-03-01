# mc_path.py
from __future__ import annotations

import json
import os
import sys
from typing import Dict, Optional


def app_dir() -> str:
    """
    - PyInstaller(onefile/onedir) 배포 시: exe가 있는 폴더
    - 개발 중: 프로젝트 폴더(현재 파일 기준)
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def config_path() -> str:
    return os.path.join(app_dir(), "config.json")


def load_config() -> Dict:
    path = config_path()
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(cfg: Dict) -> None:
    path = config_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def looks_like_minecraft_dir(p: str) -> bool:
    if not p or not os.path.isdir(p):
        return False

    # 제일 무난한 판별: versions 폴더 존재 여부
    if os.path.isdir(os.path.join(p, "versions")):
        return True

    # 혹시 versions가 아직 없더라도 런처 파일이 있으면 허용
    if os.path.exists(os.path.join(p, "launcher_profiles.json")):
        return True
    if os.path.exists(os.path.join(p, "launcher_accounts.json")):
        return True

    return False


def detect_default_minecraft_path() -> Optional[str]:
    candidates = []

    # Windows: %APPDATA%\.minecraft
    if sys.platform.startswith("win"):
        appdata = os.environ.get("APPDATA")
        if appdata:
            candidates.append(os.path.join(appdata, ".minecraft"))

    # macOS: ~/Library/Application Support/minecraft
    elif sys.platform == "darwin":
        candidates.append(os.path.expanduser("~/Library/Application Support/minecraft"))

    # Linux: ~/.minecraft
    else:
        candidates.append(os.path.expanduser("~/.minecraft"))

    for p in candidates:
        if looks_like_minecraft_dir(p):
            return p
    return None


def ensure_minecraft_path(cfg: Dict, *, prompt_once: bool = True) -> str:
    """
    1) config.json의 minecraft_path가 유효하면 그대로 사용
    2) 아니면 OS 기본 경로 자동 탐색
    3) 그래도 없으면 1회 입력받아서 저장
    """
    cur = cfg.get("minecraft_path")
    if cur and looks_like_minecraft_dir(cur):
        return cur

    auto = detect_default_minecraft_path()
    if auto:
        cfg["minecraft_path"] = auto
        save_config(cfg)
        return auto

    if not prompt_once:
        raise RuntimeError("minecraft_path를 자동으로 찾지 못했습니다.")

    user = input('[SETUP] .minecraft 경로를 입력하세요 (예: C:\\Users\\me\\AppData\\Roaming\\.minecraft): ').strip()
    user = user.strip('"').strip("'")
    if looks_like_minecraft_dir(user):
        cfg["minecraft_path"] = user
        save_config(cfg)
        return user

    raise RuntimeError("minecraft_path가 올바르지 않습니다. 폴더 경로를 다시 확인하세요.")
