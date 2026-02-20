import os
import time
from datetime import datetime

import requests

from .db import BASE_DIR
from .models import Package, init_db, utc_now

from dotenv import load_dotenv

load_dotenv(BASE_DIR / ".env")

SYNC_URL = os.getenv("SERVER_SYNC_URL", "http://localhost:8080/sync")
INTERVAL_SECONDS = int(os.getenv("SYNC_INTERVAL_SECONDS", "30"))  # 30s to conserve solar battery
LOCKER_ID = os.getenv("LOCKER_ID", "LOCKER-001")
MAX_RETRIES = 5  # Prevent infinite retry loops on permanent failures


def to_payload(package: Package) -> dict:
    drop_off = package.drop_off_timestamp
    if isinstance(drop_off, str):
        # Convert space-separated format to ISO8601 with T
        drop_off_iso = drop_off.replace(" ", "T")
    else:
        drop_off_iso = drop_off.isoformat()
    
    return {
        "tracking_id": package.tracking_id,
        "locker_id": package.locker_id,
        "status": package.status,
        "drop_off_timestamp": drop_off_iso,
        "sync_attempt_timestamp": utc_now().isoformat(),
        "last_sync_attempt": package.sync_attempt_count,
    }


def sync_once() -> None:
    # Only sync packages that haven't exceeded retry limit
    pending_packages = Package.select().where(
        (Package.status != "synced") & (Package.sync_attempt_count < MAX_RETRIES)
    )

    for package in pending_packages:
        # Increment counter BEFORE sync to handle crash mid-sync (prevents infinite retries)
        package.sync_attempt_count += 1
        package.last_sync_attempt = utc_now()
        package.save()

        try:
            response = requests.post(SYNC_URL, json=to_payload(package), timeout=10)
            
            if response.status_code == 201:
                ack_data = response.json()
                # Two-phase commit: verify server ACK matches our tracking_id before marking synced
                if ack_data.get("ack") and ack_data.get("tracking_id") == package.tracking_id:
                    package.status = "synced"
                    package.save()
                    print(f"✓ Synced {package.tracking_id}")
                else:
                    print(f"✗ Invalid ACK for {package.tracking_id}")
            else:
                print(f"✗ Sync failed {package.tracking_id}: HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            # Network timeout/failure: retry on next poll cycle
            print(f"✗ Network error for {package.tracking_id}: {e}")


def main() -> None:
    init_db()
    print(f"Sync worker started. Target={SYNC_URL}, interval={INTERVAL_SECONDS}s, locker={LOCKER_ID}")

    while True:
        sync_once()
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
