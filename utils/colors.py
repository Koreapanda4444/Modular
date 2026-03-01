from utils.logger import log

def info(msg):
    print(f"[INFO] {msg}")
    log("INFO", msg)

def warn(msg):
    print(f"[WARN] {msg}")
    log("WARN", msg)

def error(msg):
    print(f"[ERROR] {msg}")
    log("ERROR", msg)
