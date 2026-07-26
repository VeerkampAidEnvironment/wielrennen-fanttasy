from __future__ import annotations

import calendar
from datetime import datetime, timedelta, timezone, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from flask import current_app, has_app_context


class EuropeAmsterdamFallback(tzinfo):
    """Small CET/CEST fallback for Windows environments without tzdata."""

    def utcoffset(self, dt: datetime | None) -> timedelta:
        return timedelta(hours=2 if self._is_dst_local(dt) else 1)

    def dst(self, dt: datetime | None) -> timedelta:
        return timedelta(hours=1 if self._is_dst_local(dt) else 0)

    def tzname(self, dt: datetime | None) -> str:
        return "CEST" if self._is_dst_local(dt) else "CET"

    def fromutc(self, dt: datetime) -> datetime:
        if dt.tzinfo is not self:
            raise ValueError("fromutc: dt.tzinfo is not self")

        naive_utc = dt.replace(tzinfo=None)
        year = naive_utc.year
        dst_start_utc = datetime(year, 3, _last_sunday(year, 3), 1)
        dst_end_utc = datetime(year, 10, _last_sunday(year, 10), 1)
        offset = timedelta(hours=2 if dst_start_utc <= naive_utc < dst_end_utc else 1)
        return (dt + offset).replace(tzinfo=self)

    def _is_dst_local(self, dt: datetime | None) -> bool:
        if dt is None:
            return False
        local = dt.replace(tzinfo=None)
        year = local.year
        dst_start_local = datetime(year, 3, _last_sunday(year, 3), 2)
        dst_end_local = datetime(year, 10, _last_sunday(year, 10), 3)
        return dst_start_local <= local < dst_end_local


EUROPE_AMSTERDAM_FALLBACK = EuropeAmsterdamFallback()
FALLBACK_TIMEZONES = {
    "Europe/Amsterdam": EUROPE_AMSTERDAM_FALLBACK,
}


def app_timezone_name() -> str:
    if has_app_context():
        return current_app.config.get("APP_TIMEZONE", "Europe/Amsterdam")
    return "Europe/Amsterdam"


def app_timezone(name: str | None = None) -> tzinfo:
    timezone_name = name or app_timezone_name()
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        return FALLBACK_TIMEZONES.get(timezone_name, timezone.utc)


def _last_sunday(year: int, month: int) -> int:
    last_day = calendar.monthrange(year, month)[1]
    weekday = datetime(year, month, last_day).weekday()
    return last_day - ((weekday + 1) % 7)
