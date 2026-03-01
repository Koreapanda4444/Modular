
from utils.colors import info, warn, error
from pack_manager import get_pack
from apply_manager import apply_pack, clear_environment, cleanup_environment, get_copy_targets
from loader_manager import ensure_loader, cleanup_loader
from launcher import launch_minecraft, wait_for_exit
import os

from mc_path import load_config, ensure_minecraft_path
cfg = load_config()
mc_path = ensure_minecraft_path(cfg)


def handle_command(command: str, config: dict) -> bool:
    parts = command.split()
    cmd = parts[0]

    if cmd == "!exit":
        info("Modular 종료")
        return False

    elif cmd == "!list":
        from pack_manager import scan_packs
        print("[PACKS]")
        for pid in scan_packs():
            print(f"- {pid}")
        return True

    elif cmd == "!clear":
        if len(parts) < 2:
            warn("사용법: !clear <팩이름>")
            return True

        pack_id = parts[1]
        pack = get_pack(pack_id)

        if not pack:
            error(f"모드팩 '{pack_id}' 을(를) 찾을 수 없습니다.")
            return True

        if not mc_path or not os.path.exists(mc_path):
            error("minecraft_path 설정이 올바르지 않습니다.")
            return True

        info("기존 모드 환경 정리 중...")
        targets = get_copy_targets(pack["meta"])
        clear_environment(mc_path, targets)
        cleanup_loader(pack["meta"], mc_path)
        info("정리 완료")
        return True

    elif cmd == "!run":
        if len(parts) < 2:
            warn("사용법: !run <팩이름>")
            return True

        pack_id = parts[1]
        pack = get_pack(pack_id)

        if not pack:
            error(f"모드팩 '{pack_id}' 을(를) 찾을 수 없습니다.")
            return True

        if not mc_path or not os.path.exists(mc_path):
            error("minecraft_path 설정이 올바르지 않습니다.")
            return True

        info(f"{pack_id} 팩 적용 시작")
        targets = get_copy_targets(pack["meta"])
        clear_environment(mc_path, targets)
        apply_pack(pack["path"], mc_path, pack["meta"])

        ensure_loader(pack["meta"], mc_path)

        proc = launch_minecraft()
        wait_for_exit(proc)

        cleanup_after_run = config.get("cleanup_after_run", True)
        if cleanup_after_run:
            cleanup_loader(pack["meta"], mc_path)
            cleanup_environment(mc_path, targets)
        else:
            info("cleanup_after_run=false: 모드/로더 정리 생략")

        info("세션 종료")
        return True

    else:
        warn(f"알 수 없는 명령어: {cmd}")
        return True
