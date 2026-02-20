import os
from pathlib import Path

from dotenv import load_dotenv
from peewee import SqliteDatabase

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

db_path = os.getenv("SQLITE_PATH", "./locker.db")
database = SqliteDatabase(db_path)
