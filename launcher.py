import time
import psutil
from utils.colors import info

TARGET_PROCESSES = [
    "MinecraftLauncher.exe",
    "Minecraft.exe",
    "javaw.exe"
]

def wait_for_minecraft_start():
    info("Minecraft 실행 대기 중...")
    while True:
        for p in psutil.process_iter(["name"]):
            if p.info["name"] in TARGET_PROCESSES:
                info(f"{p.info['name']} 감지됨")
                return
        time.sleep(1)

def wait_for_minecraft_exit():
    info("Minecraft 종료 대기 중...")
    while True:
        running = False
        for p in psutil.process_iter(["name"]):
            if p.info["name"] in TARGET_PROCESSES:
                running = True
                break
        if not running:
            info("Minecraft 종료 감지")
            return
        time.sleep(2)

def launch_minecraft():
    wait_for_minecraft_start()
    return None


def wait_for_exit(_proc=None):
    wait_for_minecraft_exit()
