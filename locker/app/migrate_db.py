import os
import shutil
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

SQLITE_PATH = os.getenv("SQLITE_PATH", "./locker.db")
db_path = BASE_DIR / SQLITE_PATH

if db_path.exists():
    print(f"Database already exists at {db_path}")
    backup_path = db_path.with_suffix(".db.bak")

    shutil.copy(db_path, backup_path)
    print(f"Backup created at: {backup_path}")

    db_path.unlink()
    print(f"Removed old Database")

from app.models import init_db
init_db()
print(f"Initialized new database at {db_path}")
