"""MCP server (stdio) answering spacecraft-geometry questions from HelioFleet data."""

from __future__ import annotations

import os
from typing import Any, Literal

try:  # mcp >= 2
    from mcp.server.mcpserver import MCPServer as _Server
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as _Server

from .geometry import Fleet

INSTRUCTIONS = """\
Positions and viewing geometry of heliophysics spacecraft (SDO, SOHO, Aditya-L1, ACE, Wind,
DSCOVR, IMAP, SOLAR-1, Carruthers, Solar Orbiter, Parker Solar Probe, BepiColombo, STEREO-A/B,
MAVEN, MESSENGER, Venus Express, Juno, Rosetta, JUICE, Europa Clipper, Psyche) and the inner planets, from HelioFleet's JPL Horizons ephemerides (2010 to about 2030).
Times are UTC (ISO 8601, e.g. 2026-11-19T12:00Z, or 'now'). Body keys: earth, sdo, soho, aditya,
ace, wind, dscovr, imap, swfo, cgo, solo, psp, bepi, sta, stb, maven, messenger, vex, juno,
rosetta, juice, clipper, psyche, mercury, venus, mars
(common names such as 'Parker' or 'Solar Orbiter' also work). Every result carries a HelioFleet
link that reproduces the view in the browser; give it to the user with the numbers.
With the HelioField plugin (on by default), magnetic_connection, space_weather, coronal_field and
heliofield_link add the PFSS coronal field and magnetic connectivity from HelioField's daily products."""

mcp = _Server("heliofleet", instructions=INSTRUCTIONS)
fleet = Fleet()


@mcp.tool()
def get_position(body: str, time: str = "now", solar_wind_km_s: float = 400.0) -> dict[str, Any]:
    """Where one body is at a UTC time: distance from the Sun (au), Stonyhurst lon/lat, Carrington
    longitude as seen from Earth, heliocentric ecliptic J2000 and HEE vectors (au), angle from Earth,
    distance to Earth, light time and Parker-spiral footpoint longitude, with a HelioFleet link."""
    return fleet.position(body, time, solar_wind_km_s)


@mcp.tool()
def get_fleet_state(time: str = "now", include_planets: bool = True,
                    solar_wind_km_s: float = 400.0) -> dict[str, Any]:
    """Positions of Earth, every spacecraft on the HelioFleet map and (optionally) Mercury, Venus and
    Mars at a UTC time, in the same columns as get_position, with a link to the map at that moment."""
    return fleet.fleet_state(time, include_planets, solar_wind_km_s)


@mcp.tool()
def find_alignments(kind: Literal["radial", "quadrature", "conjunction", "connection"] = "radial",
                    a: str = "psp", b: str | None = None, tolerance_deg: float | None = None,
                    start: str = "now", end: str | None = None, max_windows: int | None = None,
                    solar_wind_km_s: float = 400.0) -> dict[str, Any]:
    """Time windows when a geometric condition holds, sampled hourly when Parker is involved and
    every 6 hours otherwise (the HelioFleet alignment tool's method).

    kind: radial (Sun-centred angle between a and b <= tolerance, default 5 deg),
    quadrature (a is 90 deg from Earth seen from the Sun, within tolerance, default 5),
    conjunction (a behind the Sun seen from Earth, within tolerance of Sun centre, default 2),
    connection (Parker-spiral footpoints of a and b within tolerance in longitude, default 10).
    end defaults to one year after start; max_windows=1 answers "when is the next ...".
    Each window gives start, end, best time and value, positions at best, and a link that reruns
    the search on the page."""
    return fleet.find_alignments(kind, a, b, tolerance_deg, start, end, solar_wind_km_s, max_windows)


@mcp.tool()
def list_upcoming_events(start: str = "now", end: str | None = None, kind: str | None = None,
                         body: str | None = None, include_space_weather: bool = False) -> dict[str, Any]:
    """HelioFleet's event calendar between two UTC times (default: the next year): perihelia,
    alignments, quadratures, solar conjunctions and total solar eclipses, each with a link.
    kind filters by a comma list (perihelion, alignment, quadrature, conjunction, eclipse); body
    keeps events involving that body. include_space_weather adds NASA DONKI flares (M1+), CMEs
    (500 km/s+) and geomagnetic storms (G1+) in the range."""
    return fleet.upcoming_events(start, end, kind, body, include_space_weather)


@mcp.tool()
def viewing_geometry(observer: str = "all", time: str = "now") -> dict[str, Any]:
    """What an observer (Earth or a spacecraft, or 'all') sees of the Sun at a UTC time: light time
    and offset from Earth, apparent solar radius (RSUN_OBS), B0 (HGLT_OBS), Stonyhurst longitude
    (HGLN_OBS), L0 with its own light time (CRLN_OBS), km per arcsec and scale relative to Earth.
    Includes the map's viewing-geometry link and, where available, a sky-view link from that observer."""
    return fleet.viewing_geometry(observer, time)


@mcp.tool()
def heliofleet_link(time: str = "now", page: Literal["map", "sky"] = "map", tab: str | None = None,
                    observer: str = "earth", frame: Literal["hee", "hae"] | None = None,
                    view: Literal["top", "side"] | None = None, zoom: float | None = None,
                    hide: list[str] | None = None, spirals: bool | None = None,
                    solar_wind_km_s: float | None = None,
                    spot_system: Literal["carrington", "stonyhurst"] | None = None,
                    spot_lon: float | None = None, spot_lat: float | None = None,
                    align_kind: Literal["radial", "quadrature", "connection"] | None = None,
                    align_a: str | None = None, align_b: str | None = None, align_tolerance_deg: float | None = None,
                    align_from: str | None = None, align_to: str | None = None) -> dict[str, Any]:
    """Build a HelioFleet URL that reproduces a view. page=map: frame (hee Earth-fixed, hae inertial),
    view, zoom (au), hide (body keys), spirals, wind, a marked surface spot, a tab (coords, geom,
    align, vis, series, anim) and an alignment search to rerun. page=sky: the plane of the sky seen
    from observer (earth, solo, psp, bepi, sta, stb, maven), zoom in solar radii."""
    return fleet.link(time, page, tab=tab, observer=observer, frame=frame, view=view, zoom=zoom, hide=hide,
                      spirals=spirals, solar_wind_km_s=solar_wind_km_s, spot_system=spot_system,
                      spot_lon=spot_lon, spot_lat=spot_lat, align_kind=align_kind, align_a=align_a,
                      align_b=align_b, align_tolerance_deg=align_tolerance_deg, align_from=align_from,
                      align_to=align_to)


@mcp.tool()
def data_status() -> dict[str, Any]:
    """Which HelioFleet data release is loaded (build time, next monthly update, where it came from)
    and each body's ephemeris span."""
    return fleet.data_status()


def _load_plugins() -> list[str]:
    """Optional tool sets, chosen with HELIOFLEET_MCP_PLUGINS (comma list; default 'heliofield'; 'none')."""
    names = [n.strip() for n in os.environ.get("HELIOFLEET_MCP_PLUGINS", "heliofield").split(",") if n.strip()]
    loaded = []
    for name in names:
        if name == "none":
            return []
        if name == "heliofield":
            from . import heliofield
            heliofield.register(mcp)
            loaded.append(name)
        else:
            raise SystemExit(f"unknown plugin {name!r} (available: heliofield)")
    return loaded


PLUGINS = _load_plugins()


def main() -> None:
    """Serve MCP over stdio (what MCP clients launch)."""
    mcp.run("stdio")


if __name__ == "__main__":
    main()
