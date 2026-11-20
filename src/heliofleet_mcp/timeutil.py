"""UTC time parsing and formatting on Julian dates (UT), as the HelioFleet pages do."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

JD_UNIX = 2440587.5


def jd_from_datetime(dt: datetime) -> float:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp() / 86400.0 + JD_UNIX


def datetime_from_jd(jd: float) -> datetime:
    return datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(days=jd - JD_UNIX)


def parse_time(value) -> float:
    """Julian date (UT) from an ISO 8601 UTC string, a date, 'now', or a Julian date number."""
    if value is None:
        return jd_from_datetime(datetime.now(timezone.utc))
    if isinstance(value, (int, float)):
        if value > 1e6:
            return float(value)
        raise ValueError("numeric times must be Julian dates")
    s = str(value).strip()
    if s.lower() in ("", "now", "today"):
        return jd_from_datetime(datetime.now(timezone.utc))
    if re.fullmatch(r"\d{7}(\.\d*)?", s):
        return float(s)
    s = s.replace(" ", "T").rstrip("Zz")
    s = re.sub(r"(UTC|UT)$", "", s, flags=re.I).rstrip("T")
    if re.search(r"[+-]\d\d:?\d\d$", s) and "T" in s:
        dt = datetime.fromisoformat(s)
    else:
        if re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d", s):
            s += ":00"
        dt = datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
    return jd_from_datetime(dt)


def iso(jd: float) -> str:
    """UTC to the second, as the page's tables (js/tools.js iso)."""
    return datetime_from_jd(jd + 1 / 172800).strftime("%Y-%m-%dT%H:%M:%SZ")


def iso_minute(jd: float) -> str:
    """UTC to the minute without 'Z', as the page's links (js/app.js isoMinute)."""
    return datetime_from_jd(jd + 1 / 2880).strftime("%Y-%m-%dT%H:%M")


def date_str(jd: float) -> str:
    return datetime_from_jd(jd + 1 / 172800).strftime("%Y-%m-%d")
