"""Tool to retry failed package syncs after network/server issues are resolved."""

from .models import Package, init_db
from .sync_worker import sync_once as base_sync_once, to_payload, SYNC_URL, MAX_RETRIES
import requests


def retry_failed() -> None:
    """Reset failed packages to pending and attempt sync."""
    init_db()
    
    failed_packages = Package.select().where(Package.status == "failed")
    count = failed_packages.count()
    
    if count == 0:
        print("No failed packages to retry")
        return
    
    print(f"Found {count} failed package(s). Resetting and retrying...")
    
    for package in failed_packages:
        # Reset retry counter and status
        package.status = "pending"
        package.sync_attempt_count = 0
        package.last_sync_attempt = None
        package.save()
        
        # Attempt immediate sync
        package.sync_attempt_count = 1
        package.save()
        
        try:
            response = requests.post(SYNC_URL, json=to_payload(package), timeout=10)
            
            if response.status_code == 201:
                ack_data = response.json()
                if ack_data.get("ack") and ack_data.get("tracking_id") == package.tracking_id:
                    package.status = "synced"
                    package.save()
                    print(f"Synced {package.tracking_id}")
                else:
                    print(f"Invalid ACK for {package.tracking_id} - will retry in background")
            else:
                print(f"Sync failed {package.tracking_id}: HTTP {response.status_code} - will retry in background")
                
        except requests.exceptions.RequestException as e:
            print(f"Network error for {package.tracking_id}: {e} - will retry in background")


if __name__ == "__main__":
    retry_failed()
