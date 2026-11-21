"""UTC time parsing and formatting on Julian dates (UT), as the HelioFleet pages do."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

JD_UNIX = 2440587.5


def jd_from_datetime(dt: datetime) -> float:
    """Julian date (UT) of a datetime.

    Parameters
    ----------
    dt : datetime.datetime
        The time; a naive datetime is taken as UTC.

    Returns
    -------
    float
        Julian date (UT).

    Examples
    --------
    >>> from datetime import datetime, timezone
    >>> jd_from_datetime(datetime(2000, 1, 1, 12, tzinfo=timezone.utc))
    2451545.0
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp() / 86400.0 + JD_UNIX


def datetime_from_jd(jd: float) -> datetime:
    """UTC datetime of a Julian date (UT).

    Parameters
    ----------
    jd : float
        Julian date (UT).

    Returns
    -------
    datetime.datetime
        Timezone-aware UTC datetime.

    Examples
    --------
    >>> datetime_from_jd(2451545.0)
    datetime.datetime(2000, 1, 1, 12, 0, tzinfo=datetime.timezone.utc)
    """
    return datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(days=jd - JD_UNIX)


def parse_time(value) -> float:
    """Julian date (UT) from the time formats the tools accept.

    Parameters
    ----------
    value : str, float, int or None
        An ISO 8601 UTC string (``2026-11-19T12:00Z``, a trailing ``Z`` or ``UTC`` is optional,
        an explicit offset is honoured), a date (``2026-11-19``, midnight UTC), ``'now'``,
        ``'today'``, ``''`` or None (the current time), or a Julian date as a number or string.

    Returns
    -------
    float
        Julian date (UT).

    Raises
    ------
    ValueError
        For a number that is not a Julian date, or a string that is not ISO 8601.

    Examples
    --------
    >>> parse_time("2000-01-01T12:00Z")
    2451545.0
    >>> parse_time("2000-01-01")
    2451544.5
    >>> parse_time(2451545.0)
    2451545.0
    """
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
    """UTC time to the second, as in the page's tables (js/tools.js ``iso``).

    Parameters
    ----------
    jd : float
        Julian date (UT).

    Returns
    -------
    str
        ``YYYY-MM-DDTHH:MM:SSZ``, rounded to the nearest second.

    Examples
    --------
    >>> iso(2451545.0)
    '2000-01-01T12:00:00Z'
    """
    return datetime_from_jd(jd + 1 / 172800).strftime("%Y-%m-%dT%H:%M:%SZ")


def iso_minute(jd: float) -> str:
    """UTC time to the minute without ``Z``, as in the page's links (js/app.js ``isoMinute``).

    Parameters
    ----------
    jd : float
        Julian date (UT).

    Returns
    -------
    str
        ``YYYY-MM-DDTHH:MM``, rounded to the nearest minute.

    Examples
    --------
    >>> iso_minute(2451545.0)
    '2000-01-01T12:00'
    """
    return datetime_from_jd(jd + 1 / 2880).strftime("%Y-%m-%dT%H:%M")


def date_str(jd: float) -> str:
    """UTC calendar date.

    Parameters
    ----------
    jd : float
        Julian date (UT).

    Returns
    -------
    str
        ``YYYY-MM-DD``.

    Examples
    --------
    >>> date_str(2451545.0)
    '2000-01-01'
    """
    return datetime_from_jd(jd + 1 / 172800).strftime("%Y-%m-%d")
