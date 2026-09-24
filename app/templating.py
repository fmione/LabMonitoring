import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from fastapi.templating import Jinja2Templates

from app import config

templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(__file__), "templates")
)


def _local_tz() -> ZoneInfo:
    return ZoneInfo(config.TIMEZONE)


def format_dt(value):
    if not value:
        return "-"
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(_local_tz()).strftime("%d/%m/%Y %H:%M:%S")


templates.env.filters["dth"] = format_dt


def now_utc() -> datetime:
    return datetime.now(timezone.utc)