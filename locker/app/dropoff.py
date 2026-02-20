import argparse

from .models import Package, init_db


def main() -> None:
    parser = argparse.ArgumentParser(description="Drop off a package into local SQLite")
    parser.add_argument("tracking_id", help="Tracking ID for the package")
    args = parser.parse_args()

    init_db()
    package = Package.create(tracking_id=args.tracking_id, status="pending")
    print(f"Package queued: id={package.id}, tracking_id={package.tracking_id}")


if __name__ == "__main__":
    main()
