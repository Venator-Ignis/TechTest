from datetime import datetime, timezone
import uuid

from peewee import DateTimeField, IntegerField, Model, TextField

from .db import database


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def generate_tracking_id() -> str:
    # UUID4 prevents collision across 2000 lockers generating IDs independently
    return str(uuid.uuid4())


class BaseModel(Model):
    class Meta:
        database = database


class Package(BaseModel):
    tracking_id = TextField(unique=True, default=generate_tracking_id)
    locker_id = TextField(default="LOCKER-UNKNOWN")  # Identify source locker for audit trail
    status = TextField(default="pending")
    drop_off_timestamp = DateTimeField(default=utc_now)  # When package physically arrived
    sync_attempt_count = IntegerField(default=0)  # Track retries for exponential backoff
    last_sync_attempt = DateTimeField(null=True)  # Last attempt timestamp (debugging)


def init_db() -> None:
    database.connect(reuse_if_open=True)
    database.create_tables([Package])
