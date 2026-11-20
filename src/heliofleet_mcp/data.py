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
    return datetime.fromtimestamp((jd - JD_UNIX) * 86400.0, tz=timezone.utc).year


class DataError(RuntimeError):
    pass


class Store:
    """Loads manifest and per-year chunks, and interpolates positions."""

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
        """A data file (path relative to the site root, e.g. 'data/upcoming.json')."""
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
        self.manifest()
        return self._origin

    def info(self, key: str) -> dict | None:
        return self.manifest()["bodies"].get(key)

    def covers(self, key: str, jd: float) -> bool:
        b = self.info(key)
        return bool(b) and b["start"] <= jd <= b["end"]

    # ---------- chunks and interpolation ----------

    def chunk(self, key: str, year: int) -> dict | None:
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
        """Interpolated (x, y, z), in au (heliocentric) or km (geocentric *_geo), or None."""
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

