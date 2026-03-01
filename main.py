from commands import handle_command
from utils.banner import print_banner
from utils.colors import info, error
import json
import os
import sys

CONFIG_PATH = "config.json"

def load_config():
    if not os.path.exists(CONFIG_PATH):
        error("config.json 파일을 찾을 수 없습니다.")
        sys.exit(1)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    print_banner()
    config = load_config()
    info("Modular 시작")

    while True:
        try:
            cmd = input("> ").strip()
            if not cmd:
                continue
            if not handle_command(cmd, config):
                break
        except KeyboardInterrupt:
            info("\n[EXIT] Ctrl+C 감지, Modular 종료")
            break

if __name__ == "__main__":
    main()
