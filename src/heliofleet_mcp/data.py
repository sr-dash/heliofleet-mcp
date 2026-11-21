"""HelioFleet's published ephemerides: fetching, caching and interpolation.

Files come from the public site (https://sr-dash.github.io/heliofleet/) and
are kept in a local cache. When the site cannot be reached, a local checkout
of the heliofleet repository is used instead. Interpolation follows
js/ephem.js: a 4-point Lagrange polynomial on each body's uniform UT grid.

Environment variables:
  HELIOFLEET_SOURCE      auto (default: site, then local), web, or local
  HELIOFLEET_LOCAL_DATA  path to a heliofleet `data/` folder
  HELIOFLEET_CACHE       cache folder (default ~/.cache/heliofleet-mcp)
  HELIOFLEET_SITE        site root (default https://sr-dash.github.io/heliofleet/)
"""

from __future__ import annotations

import json
import math
import os
import re
import threading
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SITE = os.environ.get("HELIOFLEET_SITE", "https://sr-dash.github.io/heliofleet/")
JD_UNIX = 2440587.5
MANIFEST_TTL_S = 6 * 3600
USER_AGENT = "heliofleet-mcp/0.1"


def _default_local() -> Path | None:
    env = os.environ.get("HELIOFLEET_LOCAL_DATA")
    if env:
        p = Path(env).expanduser()
        return p if (p / "manifest.json").exists() else None
    here = Path(__file__).resolve()
    for parent in here.parents:
        cand = parent / "heliofleet" / "data"
        if (cand / "manifest.json").exists():
            return cand
    return None


def year_of(jd: float) -> int:
    """UTC calendar year of a Julian date, which names HelioFleet's per-year data files.

    Parameters
    ----------
    jd : float
        Julian date (UT).

    Returns
    -------
    int
        The year.

    Examples
    --------
    >>> year_of(2451545.0)
    2000
    """
    return datetime.fromtimestamp((jd - JD_UNIX) * 86400.0, tz=timezone.utc).year


class DataError(RuntimeError):
    """HelioFleet or HelioField data could not be loaded from the site, the cache or a local checkout."""


class Store:
    """HelioFleet's ephemerides: loads the manifest and per-year files, and interpolates positions.

    Files come from the site and are cached on disk, per data release; when the site cannot be
    reached, the cache or a local heliofleet checkout is used (``source='auto'``).

    Parameters
    ----------
    source : {'auto', 'web', 'local'}, optional
        Where to read: the site with cache and local fallbacks (``auto``), the site only (``web``),
        or a local checkout only (``local``). Default: ``HELIOFLEET_SOURCE``, else ``auto``.
    local : str or pathlib.Path, optional
        A heliofleet ``data/`` folder. Default: ``HELIOFLEET_LOCAL_DATA``, else a sibling
        ``heliofleet/data`` checkout if one exists.
    cache : str or pathlib.Path, optional
        Cache folder. Default: ``HELIOFLEET_CACHE``, else ``~/.cache/heliofleet-mcp``.
    site : str, optional
        Site root. Default: ``HELIOFLEET_SITE``, else https://sr-dash.github.io/heliofleet/.
    timeout : float, optional
        Network timeout (s).

    Examples
    --------
    Earth's heliocentric ecliptic position (au) at Parker's perihelion of 22 March 2025:

    >>> from heliofleet_mcp.timeutil import parse_time
    >>> store = Store()
    >>> [round(c, 3) for c in store.position("earth", parse_time("2025-03-22T22:25Z"))]
    [-0.996, -0.038, 0.0]
    """

    def __init__(self, source: str | None = None, local: Path | str | None = None,
                 cache: Path | str | None = None, site: str = SITE, timeout: float = 15.0):
        self.source = (source or os.environ.get("HELIOFLEET_SOURCE", "auto")).lower()
        self.local = Path(local).expanduser() if local else _default_local()
        self.cache = Path(cache or os.environ.get("HELIOFLEET_CACHE", "~/.cache/heliofleet-mcp")).expanduser()
        self.site = site.rstrip("/") + "/"
        self.timeout = timeout
        self._manifest: dict | None = None
        self._manifest_at = 0.0
        self._origin = None
        self._chunks: dict[str, dict | None] = {}
        self._lock = threading.Lock()

    # ---------- raw files ----------

    def _fetch(self, rel: str) -> bytes:
        req = urllib.request.Request(self.site + rel, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            return r.read()

    def _local_json(self, rel: str):
        if not self.local:
            return None
        p = self.local / rel.removeprefix("data/")
        return json.loads(p.read_text()) if p.exists() else None

    def _version_dir(self) -> Path:
        gen = (self._manifest or {}).get("generated", "unknown")
        return self.cache / re.sub(r"[^0-9A-Za-z]+", "", gen)

    def json(self, rel: str, versioned: bool = True):
        """Load a published JSON data file.

        Parameters
        ----------
        rel : str
            Path relative to the site root, e.g. ``'data/upcoming.json'``.
        versioned : bool, optional
            Cache the file under the current data release (default), so a new monthly release
            is fetched afresh.

        Returns
        -------
        dict or list or None
            The parsed file, or None if it does not exist.

        Raises
        ------
        DataError
            With ``source='web'``, if the site cannot be reached.

        Examples
        --------
        >>> cal = Store().json("data/upcoming.json")
        >>> sorted(cal)[:2]
        ['events', 'generated']
        """
        if self.source != "local":
            cached = (self._version_dir() if versioned else self.cache) / rel
            if cached.exists():
                return json.loads(cached.read_text())
            try:
                raw = self._fetch(rel)
                cached.parent.mkdir(parents=True, exist_ok=True)
                cached.write_bytes(raw)
                return json.loads(raw)
            except Exception as err:  # network or HTTP error
                if self.source == "web":
                    if getattr(err, "code", None) == 404:
                        return None
                    raise DataError(f"could not fetch {rel}: {err}") from err
        return self._local_json(rel)

    # ---------- manifest ----------

    def manifest(self) -> dict:
        """The data release's manifest: each body's span, step and years, and the timeline.

        Fetched from the site at most every six hours; falls back to the cached copy, then to a
        local checkout. A new release clears the in-memory position chunks.

        Returns
        -------
        dict
            ``generated``, ``next_update``, ``source``, ``timeline`` (``start``, ``end`` as Julian
            dates) and ``bodies`` (per key: ``start``, ``end``, ``step`` in days, ``units``,
            ``center``, ``years``).

        Raises
        ------
        DataError
            If no source is available.

        Examples
        --------
        >>> Store().manifest()["timeline"]["start"]
        2455197.5
        """
        with self._lock:
            if self._manifest and time.time() - self._manifest_at < MANIFEST_TTL_S:
                return self._manifest
            m, origin = None, None
            path = self.cache / "manifest.json"
            if self.source != "local":
                try:
                    raw = self._fetch("data/manifest.json")
                    m, origin = json.loads(raw), "site"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(raw)
                except Exception:
                    if path.exists():
                        m, origin = json.loads(path.read_text()), "cache"
            if m is None and self.source != "web":
                m = self._local_json("data/manifest.json")
                origin = f"local ({self.local})" if m else None
            if m is None:
                raise DataError("HelioFleet data unavailable: site unreachable and no local checkout "
                                "(set HELIOFLEET_LOCAL_DATA to a heliofleet/data folder)")
            if self._manifest and self._manifest.get("generated") != m.get("generated"):
                self._chunks.clear()
            self._manifest, self._manifest_at, self._origin = m, time.time(), origin
            return m

    @property
    def origin(self) -> str:
        """Where the loaded manifest came from: ``site``, ``cache`` or ``local (<path>)``.

        Returns
        -------
        str
            The origin of the current data release.

        Examples
        --------
        >>> Store().origin in ("site", "cache") or Store().origin.startswith("local")
        True
        """
        self.manifest()
        return self._origin

    def info(self, key: str) -> dict | None:
        """Manifest entry of one data series.

        Parameters
        ----------
        key : str
            Series key: a body key (``psp``) or a geocentric series (``ace_geo``).

        Returns
        -------
        dict or None
            ``start``, ``end`` (Julian dates), ``step`` (days), ``units``, ``center`` and ``years``,
            or None for an unknown key.

        Examples
        --------
        >>> Store().info("psp")["step"]
        0.125
        """
        return self.manifest()["bodies"].get(key)

    def covers(self, key: str, jd: float) -> bool:
        """Whether a series has data at a time.

        Parameters
        ----------
        key : str
            Series key.
        jd : float
            Julian date (UT).

        Returns
        -------
        bool
            True if ``jd`` is within the series' span.

        Examples
        --------
        >>> from heliofleet_mcp.timeutil import parse_time
        >>> Store().covers("psp", parse_time("2025-03-22"))
        True
        """
        b = self.info(key)
        return bool(b) and b["start"] <= jd <= b["end"]

    # ---------- chunks and interpolation ----------

    def chunk(self, key: str, year: int) -> dict | None:
        """One year of samples of a series, cached in memory.

        Parameters
        ----------
        key : str
            Series key.
        year : int
            UTC year.

        Returns
        -------
        dict or None
            ``t0`` (Julian date of the first sample), ``step`` (days), ``n`` and ``d`` (flat
            x, y, z list in au, or km for geocentric series), or None if the year has no data.

        Examples
        --------
        >>> Store().chunk("psp", 2025)["t0"]
        2460676.5
        """
        cid = f"{key}/{year}"
        if cid in self._chunks:
            return self._chunks[cid]
        b = self.info(key)
        c = None
        if b and year in b["years"]:
            c = self.json(f"data/{cid}.json")
        self._chunks[cid] = c
        return c

    def _sample(self, key: str, g: float, step: float):
        y0 = year_of(g + 1e-6)
        for y in (y0, y0 - 1, y0 + 1):
            c = self.chunk(key, y)
            if not c:
                continue
            k = round((g - c["t0"]) / step)
            if 0 <= k < c["n"]:
                d = c["d"]
                return (d[3 * k], d[3 * k + 1], d[3 * k + 2])
        return None

    def position(self, key: str, jd: float):
        """Interpolated position of a series at a time.

        Uses a 4-point Lagrange polynomial on the series' uniform UT grid (js/ephem.js), linear
        interpolation next to a data gap, and the nearest sample at the very ends.

        Parameters
        ----------
        key : str
            Series key: a body key (heliocentric ecliptic J2000, au) or a ``*_geo`` series
            (geocentric, km).
        jd : float
            Julian date (UT).

        Returns
        -------
        tuple of float or None
            ``(x, y, z)``, or None outside the series' span.

        Examples
        --------
        >>> from heliofleet_mcp.timeutil import parse_time
        >>> [round(c, 4) for c in Store().position("psp", parse_time("2025-03-22T22:25Z"))]
        [-0.0375, 0.0262, 0.0025]
        """
        b = self.info(key)
        if not b or jd < b["start"] - 1e-9 or jd > b["end"] + 1e-9:
            return None
        c0 = self.chunk(key, year_of(jd))
        anchor = c0["t0"] if c0 else b["start"]
        h = b["step"]
        i = math.floor((jd - anchor) / h + 1e-9)
        g0 = anchor + i * h
        u = (jd - g0) / h
        p0 = self._sample(key, g0, h)
        if p0 is None:
            return None
        if u < 1e-9:
            return p0
        p1 = self._sample(key, g0 + h, h)
        if p1 is None:
            return p0 if u < 0.5 else None
        pm = self._sample(key, g0 - h, h)
        p2 = self._sample(key, g0 + 2 * h, h)
        if pm is None or p2 is None:
            return tuple(a + (b_ - a) * u for a, b_ in zip(p0, p1))
        wm = -u * (u - 1) * (u - 2) / 6
        w0 = (u + 1) * (u - 1) * (u - 2) / 2
        w1 = -(u + 1) * u * (u - 2) / 2
        w2 = (u + 1) * u * (u - 1) / 6
        return tuple(wm * a + w0 * b_ + w1 * c + w2 * d for a, b_, c, d in zip(pm, p0, p1, p2))

