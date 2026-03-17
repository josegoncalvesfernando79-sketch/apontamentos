import os
import shutil
import threading
import time
from datetime import datetime


def _backup_job(db_path):
    while True:
        os.makedirs("backups", exist_ok=True)
        if os.path.exists(db_path):
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            target = os.path.join("backups", f"sigef_{ts}.db")
            shutil.copy2(db_path, target)
            files = sorted(
                [os.path.join("backups", f) for f in os.listdir("backups") if f.endswith(".db")],
                key=os.path.getmtime,
                reverse=True,
            )
            for old in files[10:]:
                os.remove(old)
        time.sleep(3600)


def schedule_backup(db_path):
    thread = threading.Thread(target=_backup_job, args=(db_path,), daemon=True)
    thread.start()
