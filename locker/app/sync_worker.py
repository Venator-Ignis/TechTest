import os
import time
from datetime import datetime

import requests

from .db import BASE_DIR
from .models import Package, init_db

from dotenv import load_dotenv

load_dotenv(BASE_DIR / ".env")

SYNC_URL = os.getenv("SERVER_SYNC_URL", "http://localhost:8080/sync")
INTERVAL_SECONDS = int(os.getenv("SYNC_INTERVAL_SECONDS", "5"))


def to_payload(package: Package) -> dict:
    created_at: datetime = package.created_at
    return {
        "tracking_id": package.tracking_id,
        "status": package.status,
        "created_at": created_at.isoformat(),
    }


def sync_once() -> None:
    pending_packages = Package.select().where(Package.status != "synced")

    for package in pending_packages:
        response = requests.post(SYNC_URL, json=to_payload(package), timeout=5)
        if response.status_code == 201:
            package.status = "synced"
            package.save()


def main() -> None:
    init_db()
    print(f"Sync worker started. Target={SYNC_URL}, interval={INTERVAL_SECONDS}s")

    while True:
        sync_once()
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
