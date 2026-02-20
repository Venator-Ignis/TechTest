from datetime import datetime, timezone

from peewee import DateTimeField, Model, TextField

from .db import database


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class BaseModel(Model):
    class Meta:
        database = database


class Package(BaseModel):
    tracking_id = TextField(unique=True)
    status = TextField(default="pending")
    created_at = DateTimeField(default=utc_now)


def init_db() -> None:
    database.connect(reuse_if_open=True)
    database.create_tables([Package])
