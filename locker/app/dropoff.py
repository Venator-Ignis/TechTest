import argparse
import os

from .models import Package, init_db
from .db import BASE_DIR
from dotenv import load_dotenv

load_dotenv(BASE_DIR / ".env")

LOCKER_ID = os.getenv("LOCKER_ID", "LOCKER-001")


def main() -> None:
    parser = argparse.ArgumentParser(description="Drop off a package into local SQLite")
    parser.add_argument("tracking_id", help="Tracking ID for the package")
    args = parser.parse_args()

    init_db()
    package = Package.create(tracking_id=args.tracking_id, locker_id=LOCKER_ID, status="pending")
    print(f"Package queued: id={package.id}, tracking_id={package.tracking_id}, locker={LOCKER_ID}")


if __name__ == "__main__":
    main()
