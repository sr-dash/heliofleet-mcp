"""HelioField plugin: coronal-field context from HelioField's published daily products.

HelioField (https://sr-dash.github.io/heliofield/) publishes, for each recent day, a PFSS model
with the magnetic connection of Earth, the L1 fleet and the deep-space spacecraft to the Sun
(data/<date>/meta.json), a space-weather series (data/spaceweather/daily.json) and a solar-cycle
series per Carrington rotation (data/series/rotations.json). These tools read those files; they
do not solve the field. Dates without a daily product get links, since the page computes any
date since 2010-05-01 in the browser.

Environment variables:
  HELIOFIELD_SITE   site root (default https://sr-dash.github.io/heliofield/)
  HELIOFIELD_LOCAL  path to a heliofield checkout (default: a sibling `heliofield` folder)
"""

from __future__ import annotations

import json
import os
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any, Literal
from urllib.parse import urlencode

from pydantic import Field

from ._tools import tool
from .catalog import resolve
from .data import DataError
from .links import map_link
from .timeutil import parse_time

SITE = os.environ.get("HELIOFIELD_SITE", "https://sr-dash.github.io/heliofield/")
FIRST_DATE = "2010-05-01"
VIEWS = ("earth", "north", "fleet")
LAYERS = ("photo", "foot", "closed", "open", "ext", "ss", "pil", "hcs", "fleet", "spiral", "cloud")
FOCUS = ("psp", "solo", "bepi", "sta", "stb", "earth")
TTL_S = 3600  # index.json and the series change daily; a dated product never changes
CAVEAT = ("PFSS is a current-free model; footpoints and WSA-type speeds are indicative model output, "
          "not observations or an official forecast (that is NOAA SWPC). Cite HelioField and the magnetogram.")


def _default_local() -> Path | None:
    env = os.environ.get("HELIOFIELD_LOCAL")
    cands = [Path(env).expanduser()] if env else [p / "heliofield" for p in Path(__file__).resolve().parents]
    for c in cands:
        if (c / "data" / "index.json").exists():
            return c
    return None


class FieldStore:
    """HelioField's published files, cached on disk, with a local-checkout fallback.

    Dated daily products never change and are cached for good; the index and the series are
    refreshed after ``TTL_S`` seconds.

    Parameters
    ----------
    source : {'auto', 'web', 'local'}, optional
        As for [`Store`][heliofleet_mcp.data.Store]. Default: ``HELIOFLEET_SOURCE``, else ``auto``.
    local : str or pathlib.Path, optional
        A heliofield checkout. Default: ``HELIOFIELD_LOCAL``, else a sibling ``heliofield`` folder.
    cache : str or pathlib.Path, optional
        Cache root; files go in its ``heliofield/`` folder. Default: ``HELIOFLEET_CACHE``, else
        ``~/.cache/heliofleet-mcp``.
    site : str, optional
        Site root. Default: ``HELIOFIELD_SITE``, else https://sr-dash.github.io/heliofield/.
    timeout : float, optional
        Network timeout (s).

    Examples
    --------
    >>> idx = FieldStore().json("data/index.json", ttl=3600)
    >>> idx["dates"] == sorted(idx["dates"])
    True
    """

    def __init__(self, source: str | None = None, local: Path | str | None = None, cache: Path | str | None = None,
                 site: str = SITE, timeout: float = 15.0):
        self.source = (source or os.environ.get("HELIOFLEET_SOURCE", "auto")).lower()
        self.local = Path(local).expanduser() if local else _default_local()
        base = Path(cache or os.environ.get("HELIOFLEET_CACHE", "~/.cache/heliofleet-mcp")).expanduser()
        self.cache = base / "heliofield"
        self.site = site.rstrip("/") + "/"
        self.timeout = timeout
        self._mem: dict[str, tuple[float, object]] = {}

    def json(self, rel: str, ttl: float | None = None):
        """Load a published JSON file.

        Parameters
        ----------
        rel : str
            Path relative to the site root, e.g. ``'data/index.json'``.
        ttl : float, optional
            Seconds before a cached copy is refetched; None (default) keeps it for good, which suits
            dated products.

        Returns
        -------
        dict or list or None
            The parsed file, or None if it does not exist anywhere.

        Raises
        ------
        DataError
            With ``source='web'``, if the site cannot be reached and nothing is cached.

        Examples
        --------
        >>> "dates" in FieldStore().json("data/index.json", ttl=3600)
        True
        """
        hit = self._mem.get(rel)
        if hit and (ttl is None or time.time() - hit[0] < ttl):
            return hit[1]
        val = None
        if self.source != "local":
            cached = self.cache / rel
            fresh = cached.exists() and (ttl is None or time.time() - cached.stat().st_mtime < ttl)
            if fresh:
                val = json.loads(cached.read_text())
            else:
                try:
                    req = urllib.request.Request(self.site + rel, headers={"User-Agent": "heliofleet-mcp/0.1"})
                    with urllib.request.urlopen(req, timeout=self.timeout) as r:
                        raw = r.read()
                    cached.parent.mkdir(parents=True, exist_ok=True)
                    cached.write_bytes(raw)
                    val = json.loads(raw)
                except Exception as err:
                    if getattr(err, "code", None) == 404:
                        val = None
                    elif cached.exists():
                        val = json.loads(cached.read_text())
                    elif self.source == "web":
                        raise DataError(f"could not fetch HelioField {rel}: {err}") from err
        if val is None and self.source != "web" and self.local:
            p = self.local / rel
            val = json.loads(p.read_text()) if p.exists() else None
        self._mem[rel] = (time.time(), val)
        return val


def _date(value) -> str:
    if value in (None, "", "latest"):
        return "latest"
    return datetime.fromtimestamp((parse_time(value) - 2440587.5) * 86400, tz=timezone.utc).strftime("%Y-%m-%d")


def field_link(date="latest", page="model", *, view=None, layers=None, v=None, rss=None, scs=None, focus=None,
               conn=None, ins=None, embed=False, theme=None, scale=None, rmax=None, site=SITE) -> str:
    """Link to a HelioField page.

    Parameters
    ----------
    date : str, optional
        ``YYYY-MM-DD`` or ``latest`` (default). The page computes dates without a daily product
        in the browser, back to 2010-05-01.
    page : {'model', 'connect', 'spaceweather', 'observations'}, optional
        The 3D corona (default), magnetic connectivity, space weather or observations page.
    view : {'earth', 'north', 'fleet'}, optional
        Camera of the 3D view.
    layers : list of str, optional
        Layers to show, from ``LAYERS``.
    v : float, optional
        Solar-wind speed for the spirals (km/s; the pages offer 300 to 800 in steps of 100).
    rss, scs : float, optional
        Source-surface height (1.5 to 3.5 solar radii) and current-sheet model radius (5, 10 or
        21.5); computed dates only.
    focus : str, optional
        Body followed on the connect page, from ``FOCUS``.
    conn, ins, theme, rmax : optional
        Further page parameters, passed through.
    embed : bool, optional
        Embed mode, which also computes past dates without a confirmation dialog.
    scale : bool, optional
        Show distances to scale.
    site : str, optional
        Site root.

    Returns
    -------
    str
        The URL.

    Raises
    ------
    ValueError
        For an unknown page, view, layer or focus.

    Examples
    --------
    >>> field_link("2026-11-01", "connect", v=500, focus="psp")
    'https://sr-dash.github.io/heliofield/connect.html?date=2026-11-01&v=500&focus=psp'
    """
    pages = {"model": "", "connect": "connect.html", "spaceweather": "spaceweather.html",
             "observations": "observations.html"}
    if page not in pages:
        raise ValueError(f"page must be one of {', '.join(pages)}")
    q: dict[str, str] = {"date": date}
    if view:
        if view not in VIEWS:
            raise ValueError(f"view must be one of {VIEWS}")
        q["view"] = view
    if layers:
        bad = [x for x in layers if x not in LAYERS]
        if bad:
            raise ValueError(f"unknown layers {bad}; choose from {LAYERS}")
        q["layers"] = ",".join(layers)
    for k, val in (("v", v), ("rss", rss), ("scs", scs), ("conn", conn), ("ins", ins), ("theme", theme),
                   ("rmax", rmax)):
        if val is not None:
            q[k] = f"{val:g}" if isinstance(val, float) else str(val)
    if scale:
        q["scale"] = "true"
    if focus:
        if focus not in FOCUS:
            raise ValueError(f"focus must be one of {FOCUS}")
        q["focus"] = focus
    if embed:
        q["embed"] = "1"
    return site.rstrip("/") + "/" + pages[page] + "?" + urlencode(q, safe=",")


class HelioField:
    """Coronal-field context from HelioField's daily PFSS products.

    The methods read published files and do not solve the field. Daily products cover roughly
    the last two months; for other dates they return links to the pages, which compute any date
    since 2010-05-01. Results are model output: see ``CAVEAT``.

    Parameters
    ----------
    store : FieldStore, optional
        The data source. Default: a new [`FieldStore`][heliofleet_mcp.heliofield.FieldStore].

    Examples
    --------
    >>> HelioField().magnetic_connection("psp")["daily_product"]
    True
    """

    def __init__(self, store: FieldStore | None = None):
        self.store = store or FieldStore()

    def dates(self) -> list[str]:
        """Dates with a daily product.

        Returns
        -------
        list of str
            ``YYYY-MM-DD`` dates, oldest first.

        Examples
        --------
        >>> d = HelioField().dates()
        >>> len(d) > 10 and d == sorted(d)
        True
        """
        idx = self.store.json("data/index.json", ttl=TTL_S) or {}
        return idx.get("dates", [])

    def _product(self, date: str):
        dates = self.dates()
        if not dates:
            raise DataError("HelioField daily index unavailable")
        d = dates[-1] if date == "latest" else date
        if d not in dates:
            return d, None, dates
        return d, self.store.json(f"data/{d}/meta.json"), dates

    def _no_product(self, d, dates, extra=None):
        if d < FIRST_DATE:
            raise ValueError(f"HelioField starts on {FIRST_DATE}")
        return {
            "date": d, "daily_product": False,
            "note": (f"No daily product for {d} (they cover {dates[0]} to {dates[-1]}). The HelioField page "
                     "computes this date in the browser from the SDO/HMI rotation map; open the link "
                     "(add embed=1 for a screenshot without the confirmation dialog), or run "
                     "compute_corona.py from https://sr-dash.github.io/heliofield/download/."),
            **(extra or {}),
        }

    # ---------- tools ----------

    def magnetic_connection(self, body="all", date="latest", solar_wind_km_s=400.0, self_consistent=False):
        """Where a body connects magnetically to the Sun (the ``get_magnetic_connection`` tool).

        Follows the Parker spiral from the body to the source surface, then the PFSS field line
        down to the photosphere.

        Parameters
        ----------
        body : str, optional
            Body key or name (``earth``, ``psp``, ``solo``, ``bepi``, ``sta``, the L1 fleet), or
            ``all`` (default).
        date : str, optional
            ``YYYY-MM-DD``, any time [`parse_time()`][heliofleet_mcp.timeutil.parse_time] accepts, or
            ``latest`` (default).
        solar_wind_km_s : float, optional
            Wind speed for the spiral; the nearest speed of the product's grid is used.
        self_consistent : bool, optional
            Use, for each body, the grid speed closest to its own WSA-type estimate.

        Returns
        -------
        dict
            With a daily product: ``date``, ``map_time_utc``, ``model``, ``carrington_rotation``,
            Earth's ``L0``/``B0``, ``speed_choice``, ``columns``, ``connections`` (per body: position,
            ``wind_used_km_s``, ``source_surface_point_deg``, ``footpoint_deg``, ``expansion_factor_fs``,
            ``dchb_deg``, ``wsa_speed_km_s``), ``caveat`` and ``links``. Without one: a note and links.

        Raises
        ------
        ValueError
            For an unknown body, a body without a connection, or a date before 2010-05-01.
        DataError
            If the daily index cannot be loaded.

        Examples
        --------
        >>> r = HelioField().magnetic_connection("psp", solar_wind_km_s=450)
        >>> r["connections"][0]["body"], r["connections"][0]["wind_used_km_s"]
        ('psp', 450)
        """
        d, meta, dates = self._product(_date(date))
        keys = None if body in (None, "", "all") else [resolve(body)]
        v_in = float(solar_wind_km_s)
        focus = keys[0] if keys and keys[0] in FOCUS else None
        links = {  # both pages offer 300..800 km/s in steps of 100
            "connect": field_link(d, "connect", v=_grid_speed(v_in), focus=focus),
            "model_3d": field_link(d, view="fleet", v=_grid_speed(v_in)),
        }
        if meta is None:
            return self._no_product(d, dates, {"links": links})
        vgrid = meta["vgrid"]
        v = min(vgrid, key=lambda g: abs(g - v_in))
        by_body: dict[str, list[dict]] = {}
        for c in meta["connect"]:
            by_body.setdefault(c["body"], []).append(c)
        if keys and keys[0] not in by_body:
            raise ValueError(f"{keys[0]} has no connection in HelioField's product; available: {', '.join(by_body)}")
        rows = []
        for k in keys or list(by_body):
            opts = by_body[k]
            if self_consistent:
                c = min(opts, key=lambda o: abs((o.get("vwsa") or 1e9) - o["v"]))
            else:
                c = next(o for o in opts if o["v"] == v)
            f = meta["fleet"].get(k, {})
            rows.append({
                "body": k, "name": f.get("name", k),
                "carrington_lon_deg": f.get("lon"), "carrington_lat_deg": f.get("lat"), "r_au": f.get("r"),
                "wind_used_km_s": c["v"],
                "source_surface_point_deg": {"lon": c["ss"][0], "lat": c["ss"][1]},
                "footpoint_deg": {"lon": c["foot"][0], "lat": c["foot"][1]} if c.get("foot") else None,
                "expansion_factor_fs": c.get("fs"),
                "dchb_deg": c.get("dchb"),
                "wsa_speed_km_s": c.get("vwsa"),
            })
        t = parse_time(meta["obstime"])
        return {
            "date": d, "daily_product": True, "map_time_utc": meta["obstime"],
            "model": {**meta["model"], "magnetogram": meta["source"]["name"]},
            "carrington_rotation": meta["carrington_rotation"], "earth_L0_deg": meta["L0"], "earth_B0_deg": meta["B0"],
            "speed_choice": ("each body at the grid speed closest to its own WSA-type estimate" if self_consistent
                             else f"{v} km/s for every body (nearest grid speed to {v_in:g})"),
            "columns": {
                "source_surface_point_deg": f"where the Parker spiral meets the source surface "
                                            f"({meta['model'].get('rss')} R_sun), Carrington",
                "footpoint_deg": "photospheric end of the PFSS field line from that point, Carrington",
                "expansion_factor_fs": "magnetic expansion factor between photosphere and source surface",
                "dchb_deg": "angular distance of the footpoint from the nearest coronal-hole boundary",
                "wsa_speed_km_s": "WSA-type wind speed: " + meta.get("wsa", {}).get("form", ""),
            },
            "connections": rows,
            "caveat": CAVEAT,
            "links": {**links, "heliofleet": map_link(t, spirals=True, wind=v)},
        }

    def space_weather(self, date="latest"):
        """HelioField's space-weather indicators for a day (the ``get_space_weather`` tool).

        Parameters
        ----------
        date : str, optional
            ``YYYY-MM-DD`` or ``latest`` (default).

        Returns
        -------
        dict
            ``date``, ``found`` and, when found, the day's row (model wind speed and sector at Earth,
            next sector boundary, outlook, alert level, measured L1 wind, ...), ``units``, ``about``,
            ``caveat`` and ``links``; otherwise the available range and a link.

        Raises
        ------
        DataError
            If the series cannot be loaded.

        Examples
        --------
        >>> HelioField().space_weather()["found"]
        True
        """
        d = _date(date)
        data = self.store.json("data/spaceweather/daily.json", ttl=TTL_S) or {}
        rows = data.get("rows", [])
        if not rows:
            raise DataError("HelioField space-weather series unavailable")
        row = rows[-1] if d == "latest" else next((r for r in rows if r["date"] == d), None)
        if row is None:
            return {"date": d, "found": False, "available": [rows[0]["date"], rows[-1]["date"]],
                    "note": "The space-weather series has one row per daily product.",
                    "link": field_link(d, "spaceweather")}
        d = row["date"]
        return {
            "date": d, "found": True, **row, "units": data.get("units"),
            "about": data.get("about"),
            "caveat": "Ambient-wind indicators from a PFSS/WSA model with illustrative coefficients; "
                      "not an official forecast (that is NOAA SWPC).",
            "links": {"page": field_link(d, "spaceweather"), "share_card": f"{SITE}sw/{d}.png",
                      "connect": field_link(d, "connect")},
        }

    def coronal_field(self, date="latest"):
        """Summary of the coronal magnetic field for a day (the ``get_coronal_field`` tool).

        Parameters
        ----------
        date : str, optional
            ``YYYY-MM-DD`` or ``latest`` (default). The solar-cycle context is available for any
            date since 2010; the rest needs a daily product.

        Returns
        -------
        dict
            ``date``, ``daily_product``, ``map_time_utc``, ``magnetogram``, ``model``,
            ``carrington_rotation``, Earth's ``L0``/``B0``, ``open_flux_Mx``, ``field_lines``,
            ``current_sheet_segments``, ``solar_cycle`` (open flux and area, current-sheet tilt and
            polar fields of the nearest rotation), ``caveat`` and ``links``.

        Raises
        ------
        ValueError
            For a date before 2010-05-01.
        DataError
            If the daily index cannot be loaded.

        Examples
        --------
        >>> c = HelioField().coronal_field()
        >>> c["daily_product"], c["open_flux_Mx"] > 0
        (True, True)
        """
        d, meta, dates = self._product(_date(date))
        series = self.store.json("data/series/rotations.json", ttl=TTL_S) or {}
        cycle = None
        if series.get("cr"):
            mids = series["mid"]
            i = min(range(len(mids)), key=lambda j: abs(parse_time(mids[j]) - parse_time(d)))
            cycle = {"carrington_rotation": series["cr"][i], "rotation_mid": mids[i],
                     **{k: series[k][i] for k in ("flux", "area", "tilt_n", "tilt_s", "polar_n", "polar_s")},
                     "units": series.get("units"), "source": series.get("source")}
        links = {"model_3d": field_link(d, view="earth"),
                 "current_sheet_1au": field_link(d, view="fleet", layers=["photo", "hcs", "fleet", "spiral"],
                                                 scale=True, rmax=1.2),
                 "coronal_holes": field_link(d, view="earth", layers=["photo", "foot", "open", "pil"]),
                 "observations": field_link(d, "observations")}
        if meta is None:
            return self._no_product(d, dates, {"solar_cycle": cycle, "links": links})
        return {
            "date": d, "daily_product": True, "map_time_utc": meta["obstime"],
            "magnetogram": meta["source"], "model": meta["model"],
            "carrington_rotation": meta["carrington_rotation"], "earth_L0_deg": meta["L0"], "earth_B0_deg": meta["B0"],
            "open_flux_Mx": meta["open_flux_Mx"],
            "field_lines": meta.get("lines", {}).get("count"),
            "current_sheet_segments": len(meta.get("hcs", [])),
            "solar_cycle": cycle,
            "caveat": CAVEAT,
            "links": links,
        }


def _grid_speed(v: float) -> int:
    """The pages' speed menus: 300..800 km/s in steps of 100."""
    return int(min(800, max(300, int(v / 100 + 0.5) * 100)))


# The date parameter of the HelioField tools (module level: annotations are resolved here)
Day = Annotated[str, Field(description="UTC date (2026-11-19, or a full ISO time) or 'latest' for the "
                                       "newest daily product.")]


def register(server, store: FieldStore | None = None) -> HelioField:
    """Add the HelioField tools to an MCP server.

    Registers ``get_magnetic_connection``, ``get_space_weather``, ``get_coronal_field`` and
    ``build_heliofield_link``.
    Their docstrings are the tool descriptions MCP clients show.

    Parameters
    ----------
    server : mcp.server.fastmcp.FastMCP or mcp.server.mcpserver.MCPServer
        The server to extend.
    store : FieldStore, optional
        The data source.

    Returns
    -------
    HelioField
        The instance behind the tools.

    Examples
    --------
    >>> from mcp.server.fastmcp import FastMCP  # doctest: +SKIP
    >>> register(FastMCP("demo"))  # doctest: +SKIP
    <heliofleet_mcp.heliofield.HelioField object at ...>
    """
    hf = HelioField(store)

    @tool(server, "Magnetic connection to the Sun")
    def get_magnetic_connection(
            body: Annotated[str, Field(description="earth, psp, solo, bepi, sta, aditya, ace, wind, imap, swfo, "
                                                   "or 'all'; names such as 'Parker' also work.")] = "all",
            date: Day = "latest",
            solar_wind_km_s: Annotated[float, Field(
                description="Wind speed for the Parker spiral (km/s); ignored when self_consistent is true.",
                ge=100, le=3000)] = 400.0,
            self_consistent: Annotated[bool, Field(description="Pick, per body, the wind speed that matches its "
                                                               "own WSA estimate.")] = False,
    ) -> dict[str, Any]:
        """Get where a spacecraft or Earth connects magnetically to the Sun, from HelioField's daily
        PFSS product: Parker spiral to the source surface, then the field line down to its
        photospheric footpoint (Carrington lon/lat), with expansion factor, distance to the
        coronal-hole boundary and a WSA-type speed.

        Use for source-region and solar-energetic-particle connectivity questions. The plain
        Parker-spiral footpoint, without the coronal field, is in get_position. Daily products
        cover roughly the last two months; other dates return links to the page, which computes
        any date since 2010-05-01. Model output, not an observation."""
        return hf.magnetic_connection(body, date, solar_wind_km_s, self_consistent)

    @tool(server, "Space-weather indicators")
    def get_space_weather(date: Day = "latest") -> dict[str, Any]:
        """Get HelioField's space-weather indicators for a day: model wind speed and magnetic sector
        at Earth, next sector boundary, 7-day peak, a -1..+7 day outlook, IMF estimate,
        Russell-McPherron factor, Earth-facing coronal holes, an alert level, and the solar wind
        measured at L1 that day.

        Use for conditions at Earth on a recent day. Dates older than the daily series return
        found=false. Flares, CMEs and storms from NASA DONKI are in list_upcoming_events with
        include_space_weather. Model indicators, not an official forecast (that is NOAA SWPC)."""
        return hf.space_weather(date)

    @tool(server, "Coronal field summary")
    def get_coronal_field(date: Day = "latest") -> dict[str, Any]:
        """Get a summary of the coronal magnetic field for a day: magnetogram, PFSS settings, open
        flux, Earth's L0/B0, and the solar-cycle context of the Carrington rotation (open flux and
        area, current-sheet tilt, polar fields), with HelioField links to the 3D corona, the
        current sheet to 1 au, coronal holes and observations.

        Use for the state of the corona or the solar cycle on a date; the rotation context exists
        for any date since 2010. For one body's connection use get_magnetic_connection."""
        return hf.coronal_field(date)

    @tool(server, "Build a HelioField link")
    def build_heliofield_link(
            date: Day = "latest",
            page: Annotated[Literal["model", "connect", "spaceweather", "observations"], Field(
                description="model: 3D corona; connect: magnetic connectivity; spaceweather; observations.")] = "model",
            view: Annotated[Literal["earth", "north", "fleet"] | None, Field(
                description="Camera of the 3D view.")] = None,
            layers: Annotated[list[str] | None, Field(description="Layers to show: photo, foot, closed, open, ext, "
                                                                  "ss, pil, hcs, fleet, spiral, cloud.")] = None,
            solar_wind_km_s: Annotated[int | None, Field(description="Wind speed for spirals (km/s).")] = None,
            rss: Annotated[float | None, Field(description="Source-surface radius (1.5-3.5 solar radii); "
                                                           "computed dates only.", ge=1.5, le=3.5)] = None,
            scs: Annotated[float | None, Field(description="Current-sheet model outer radius: 5, 10 or 21.5 "
                                                           "solar radii; computed dates only.")] = None,
            focus: Annotated[str | None, Field(description="Connect page: body to focus (psp, solo, bepi, sta, "
                                                           "stb, earth).")] = None,
            embed: Annotated[bool, Field(description="Compute past dates without the confirmation dialog.")] = False,
            theme: Annotated[str | None, Field(description="Page colour theme.")] = None,
    ) -> dict[str, Any]:
        """Build a HelioField URL for a date and page, with no computation.

        Use when the user wants a link to the 3D corona, the connectivity page, space weather or
        observations with specific settings. The HelioField data tools already return links to
        their views. For HelioFleet's spacecraft map or sky view use build_heliofleet_link."""
        return {"link": field_link(_date(date), page, view=view, layers=layers, v=solar_wind_km_s, rss=rss,
                                   scs=scs, focus=focus, embed=embed, theme=theme)}

    return hf
