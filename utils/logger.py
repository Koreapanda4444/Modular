import os
from datetime import datetime

LOG_DIR = "logs"
LOG_FILE = "session.log"

def log(level: str, message: str):
    os.makedirs(LOG_DIR, exist_ok=True)
    path = os.path.join(LOG_DIR, LOG_FILE)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [{level}] {message}\n"

    with open(path, "a", encoding="utf-8") as f:
        f.write(line)
