from datetime import datetime, timedelta
from zoneinfo import ZoneInfoNotFoundError

from tour_femmes.timezones import app_timezone


def test_amsterdam_timezone_falls_back_when_tzdata_is_missing(monkeypatch):
    def missing_zoneinfo(_name):
        raise ZoneInfoNotFoundError("missing test tzdata")

    monkeypatch.setattr("tour_femmes.timezones.ZoneInfo", missing_zoneinfo)

    timezone = app_timezone("Europe/Amsterdam")

    assert datetime(2026, 1, 26, 12, tzinfo=timezone).utcoffset() == timedelta(hours=1)
    assert datetime(2026, 7, 26, 12, tzinfo=timezone).utcoffset() == timedelta(hours=2)
    assert datetime(2026, 7, 26, 12, tzinfo=timezone).tzname() == "CEST"
