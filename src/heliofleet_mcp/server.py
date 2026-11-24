"""MCP server (stdio) answering spacecraft-geometry questions from HelioFleet data."""

from __future__ import annotations

import os
from typing import Annotated, Any, Literal

from pydantic import Field

try:  # mcp >= 2
    from mcp.server.mcpserver import MCPServer as _Server
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as _Server

from ._tools import tool
from .geometry import Fleet
from .observations import Observations

INSTRUCTIONS = """\
Positions and viewing geometry of heliophysics spacecraft (SDO, SOHO, Aditya-L1, ACE, Wind,
DSCOVR, IMAP, SOLAR-1, Carruthers, Solar Orbiter, Parker Solar Probe, BepiColombo, STEREO-A/B,
MAVEN, MESSENGER, Venus Express, Juno, Rosetta, JUICE, Europa Clipper, Psyche) and the inner
planets, from HelioFleet's JPL Horizons ephemerides (2010 to about 2030).
Times are UTC (ISO 8601, e.g. 2026-11-19T12:00Z, or 'now'). Body keys: earth, sdo, soho, aditya,
ace, wind, dscovr, imap, swfo, cgo, solo, psp, bepi, sta, stb, maven, messenger, vex, juno,
rosetta, juice, clipper, psyche, mercury, venus, mars
(common names such as 'Parker' or 'Solar Orbiter' also work). Every result carries a HelioFleet
link that reproduces the view in the browser; give it to the user with the numbers.
Which tool: which keys, names and instruments exist -> list_bodies; one body -> get_position;
one body over a date range -> get_trajectory; every body -> get_fleet_state; what an observer
sees of the Sun -> get_viewing_geometry; when a configuration happens -> find_alignments (any
search) or list_upcoming_events (the precomputed calendar); which IRIS, Hinode/EIS, DKIST,
Solar Orbiter or rocket datasets exist -> search_observations, and joint ones ->
find_coordinated_observations; a link only -> build_heliofleet_link.
With the HelioField plugin (on by default), get_magnetic_connection, get_space_weather,
get_coronal_field and build_heliofield_link add the PFSS coronal field and magnetic connectivity
from HelioField's daily products. All tools are read-only."""

mcp = _Server("heliofleet", instructions=INSTRUCTIONS)
fleet = Fleet()
observations = Observations(fleet.store)

# Parameter types shared by several tools
Time = Annotated[str, Field(description="UTC time: ISO 8601 (2026-11-19T12:00Z), a date (2026-11-19), "
                                        "'now', or a Julian date. Data cover 2010 to about 2030.")]
Wind = Annotated[float, Field(description="Solar-wind speed in km/s for the Parker-spiral footpoint "
                                          "longitude (typical 300-800).", ge=100, le=3000)]
BODY_HELP = ("Body key or name: earth, sdo, soho, aditya, ace, wind, dscovr, imap, swfo, cgo, solo, psp, "
             "bepi, sta, stb, maven, messenger, vex, juno, rosetta, juice, clipper, psyche, mercury, venus, "
             "mars; names such as 'Parker' or 'Solar Orbiter' also work.")


@tool(mcp, "Position of one body")
def get_position(body: Annotated[str, Field(description=BODY_HELP)], time: Time = "now",
                 solar_wind_km_s: Wind = 400.0) -> dict[str, Any]:
    """Get where one spacecraft or planet is at a UTC time: distance from the Sun, Stonyhurst and
    Carrington coordinates, ecliptic and HEE vectors, angle and distance from Earth, light time and
    Parker-spiral footpoint, with a HelioFleet map link.

    Use for questions about a single body's location at one time. For a date range use
    get_trajectory; for every body at once use get_fleet_state;
    for what that body sees of the Sun (B0, L0, apparent radius) use get_viewing_geometry; for its
    PFSS magnetic connection to the Sun use get_magnetic_connection. An unknown body name returns an
    error listing the valid keys; a time outside the body's ephemeris returns a status (prelaunch,
    ended, nodata) instead of coordinates."""
    return fleet.position(body, time, solar_wind_km_s)


@tool(mcp, "Positions of the whole fleet")
def get_fleet_state(time: Time = "now",
                    include_planets: Annotated[bool, Field(description="Also return Mercury, Venus and Mars.")] = True,
                    solar_wind_km_s: Wind = 400.0) -> dict[str, Any]:
    """Get the positions of Earth, every spacecraft on the HelioFleet map and, optionally, the inner
    planets at one UTC time, in the same columns as get_position, with a map link.

    Use to compare many bodies at one moment (who is where, who is near Earth). Bodies without data
    at that time are listed under not_shown with the reason. For one body use get_position."""
    return fleet.fleet_state(time, include_planets, solar_wind_km_s)


@tool(mcp, "Trajectory of one body over a date range")
def get_trajectory(
        body: Annotated[str, Field(description=BODY_HELP)],
        start: Time = "now",
        end: Annotated[str | None, Field(description="End of the range (UTC); default 30 days after start.")] = None,
        step_hours: Annotated[float, Field(description="Sampling step in hours (default 24). At most 2000 samples "
                                                       "per call; use 1-6 h for Parker near perihelion.",
                                           gt=0, le=8784)] = 24.0,
        solar_wind_km_s: Wind = 400.0) -> dict[str, Any]:
    """Get one spacecraft's or planet's coordinates sampled over a time range, as a table: distance
    from the Sun, Stonyhurst and Carrington coordinates, HEE vector, angle and distance from Earth,
    light time and Parker-spiral footpoint at each step, with the closest and farthest points.

    Use for time series, orbit plots, perihelion passes and "how does X change over this period"
    questions. For one moment use get_position; for every body at one moment use get_fleet_state;
    for the times a configuration holds use find_alignments. Samples outside the body's ephemeris
    keep their time and status with null coordinates."""
    return fleet.trajectory(body, start, end, step_hours, solar_wind_km_s)


@tool(mcp, "Search observation footprints")
def search_observations(
        start: Time = "now",
        end: Annotated[str | None, Field(description="End of the range (UTC); default one day after start. "
                                                     "At most a year.")] = None,
        instruments: Annotated[str | None, Field(
            description="Comma list of instruments (iris, eis, vbi, visp, dlnirsp, euihri, euilya, phihrt, "
                        "spice, hic, clasp; list_bodies gives their coverage) or facilities (dkist, iris, "
                        "eis, solo, rocket). Default: all.")] = None,
        x_arcsec: Annotated[float | None, Field(description="Point on the Sun as seen from Earth: helioprojective "
                                                            "x (arcsec, west positive). Give with y_arcsec.")] = None,
        y_arcsec: Annotated[float | None, Field(description="Helioprojective y (arcsec, north positive).")] = None,
        radius_arcsec: Annotated[float, Field(description="Also keep fields within this distance of the point.",
                                              ge=0, le=3000)] = 0.0,
        max_results: Annotated[int, Field(description="Most observations returned, earliest first; 'total' "
                                                      "counts every match.", ge=1, le=500)] = 50,
        include_images: Annotated[bool, Field(description="Add PNG cutouts of SDO AIA 171, AIA 193 and HMI "
                                                          "around each field (Helioviewer).")] = True,
) -> dict[str, Any]:
    """Search the observation records of high-resolution solar instruments (IRIS, Hinode/EIS, DKIST,
    Solar Orbiter EUI-HRI, PHI-HRT and SPICE, Hi-C and CLASP rockets) that overlap a time range,
    optionally covering a point on the Sun. Each record gives the instrument, dataset id, start and
    end, programme description, field of view in Earth's helioprojective frame (centre, size,
    polygon), the archive data link, SDO image cutout URLs and a sky-view link.

    Use to find which datasets exist for an event, a region or a time, and where each instrument
    pointed. For groups of overlapping observations by different facilities use
    find_coordinated_observations; for full-disk or remote fields of spacecraft use
    get_viewing_geometry. Records come from the public archives' catalogues, refreshed monthly."""
    return observations.search(start, end, instruments, x_arcsec, y_arcsec, radius_arcsec, max_results,
                               include_images)


@tool(mcp, "Find coordinated observations")
def find_coordinated_observations(
        start: Time = "now",
        end: Annotated[str | None, Field(description="End of the range (UTC); default one year after start.")] = None,
        facilities: Annotated[str | None, Field(
            description="Comma list; keep groups that include all of them: dkist, iris, eis, solo, rocket. "
                        "Default: any group.")] = None,
        max_results: Annotated[int, Field(description="Most groups returned, earliest first.", ge=1, le=500)] = 50,
) -> dict[str, Any]:
    """Find groups of observations by different facilities (DKIST, IRIS, Hinode/EIS, Solar Orbiter,
    sounding rockets) that overlap in time and on the Sun as seen from Earth, from HelioFleet's
    precomputed list. Each group gives the start, duration, shared point on the disk, facilities,
    the number of observations per instrument and a sky-view link.

    Use to find joint datasets for a study, e.g. "when did DKIST and IRIS observe the same target".
    Then call search_observations with the group's time and point to get each observation's field,
    archive link and images."""
    return observations.coordinated(start, end, facilities, max_results)


@tool(mcp, "Find alignments, quadratures, conjunctions and connections")
def find_alignments(
        kind: Annotated[Literal["radial", "quadrature", "conjunction", "connection"], Field(
            description="radial: a and b within tolerance of the same Sun-centred direction; quadrature: a "
                        "90 deg from Earth seen from the Sun; conjunction: a behind the Sun seen from Earth; "
                        "connection: Parker-spiral footpoints of a and b close in longitude.")] = "radial",
        a: Annotated[str, Field(description="First body (key or name). " + BODY_HELP)] = "psp",
        b: Annotated[str | None, Field(description="Second body for radial and connection; default Earth. "
                                                   "Ignored for quadrature and conjunction.")] = None,
        tolerance_deg: Annotated[float | None, Field(
            description="Window threshold in degrees; defaults: radial 5, quadrature 5, conjunction 2, "
                        "connection 10.", gt=0, le=90)] = None,
        start: Time = "now",
        end: Annotated[str | None, Field(description="End of the search (UTC); default one year after start.")] = None,
        max_windows: Annotated[int | None, Field(description="Stop after this many windows; 1 answers "
                                                             "'when is the next ...'.", ge=1)] = None,
        solar_wind_km_s: Wind = 400.0) -> dict[str, Any]:
    """Find the time windows when a geometric configuration holds between two bodies, searching
    hourly when Parker is involved and every 6 hours otherwise (HelioFleet's alignment method).

    Use for any custom search: a pair, a tolerance or a date range of your choice, including the
    past. For the precomputed calendar of notable upcoming events use list_upcoming_events. Each
    window gives start, end, best time and value, positions at the best time, and a link that
    reruns the search on the page."""
    return fleet.find_alignments(kind, a, b, tolerance_deg, start, end, solar_wind_km_s, max_windows)


@tool(mcp, "Upcoming events calendar")
def list_upcoming_events(
        start: Time = "now",
        end: Annotated[str | None, Field(description="End of the range (UTC); default one year after start.")] = None,
        kind: Annotated[str | None, Field(description="Comma list to keep: perihelion, alignment, quadrature, "
                                                      "conjunction, eclipse.")] = None,
        body: Annotated[str | None, Field(description="Keep only events involving this body (key or name).")] = None,
        include_space_weather: Annotated[bool, Field(description="Add NASA DONKI flares (M1+), CMEs (500 km/s+) "
                                                                 "and geomagnetic storms (G1+) in the range.")] = False,
) -> dict[str, Any]:
    """List HelioFleet's precomputed event calendar between two UTC times: perihelia, radial
    alignments, quadratures, solar conjunctions and total solar eclipses, each with a link.

    Use for "what is coming up" questions. The calendar covers the future only and uses fixed
    thresholds; for past dates, other pairs or other tolerances use find_alignments."""
    return fleet.upcoming_events(start, end, kind, body, include_space_weather)


@tool(mcp, "Viewing geometry of an observer")
def get_viewing_geometry(
        observer: Annotated[str, Field(description="Earth, a spacecraft key or name, or 'all' for every "
                                                   "observer with data.")] = "all",
        time: Time = "now") -> dict[str, Any]:
    """Get what an observer sees of the Sun at a UTC time: light time and offset from Earth,
    apparent solar radius (RSUN_OBS), B0 (HGLT_OBS), Stonyhurst longitude (HGLN_OBS), L0 with its
    own light time (CRLN_OBS), km per arcsec and scale relative to Earth.

    Use to co-align or time-align images from different observers (the values match the FITS
    keywords). For where the observer is use get_position. Includes the map's viewing-geometry link
    and, for observers the sky view supports, a sky-view link."""
    return fleet.viewing_geometry(observer, time)


@tool(mcp, "Build a HelioFleet link")
def build_heliofleet_link(
        time: Time = "now",
        page: Annotated[Literal["map", "sky"], Field(description="map: positions around the Sun; sky: the "
                                                                 "plane of the sky seen from an observer.")] = "map",
        tab: Annotated[str | None, Field(
            description="Map tool tab to open: coords, geom, align, vis, series, anim.")] = None,
        observer: Annotated[str, Field(
            description="Sky-view observer: earth, solo, psp, bepi, sta, stb, maven.")] = "earth",
        frame: Annotated[Literal["hee", "hae"] | None, Field(
            description="Map frame: hee Earth-fixed, hae inertial.")] = None,
        view: Annotated[Literal["top", "side"] | None, Field(
            description="Map view: top (from ecliptic north) or side.")] = None,
        zoom: Annotated[float | None, Field(description="Map half-width in au, or sky-view half-width in solar radii.",
                                            gt=0)] = None,
        hide: Annotated[list[str] | None, Field(description="Body keys to hide.")] = None,
        spirals: Annotated[bool | None, Field(description="Draw Parker spirals on the map.")] = None,
        solar_wind_km_s: Annotated[float | None, Field(
            description="Wind speed for spirals and footpoints (km/s).")] = None,
        spot_system: Annotated[Literal["carrington", "stonyhurst"] | None, Field(
            description="Coordinate system of a surface spot to mark.")] = None,
        spot_lon: Annotated[float | None, Field(description="Spot longitude (deg).")] = None,
        spot_lat: Annotated[float | None, Field(description="Spot latitude (deg).", ge=-90, le=90)] = None,
        align_kind: Annotated[Literal["radial", "quadrature", "connection"] | None, Field(
            description="Alignment search to rerun on the page.")] = None,
        align_a: Annotated[str | None, Field(description="First body of that search.")] = None,
        align_b: Annotated[str | None, Field(description="Second body of that search.")] = None,
        align_tolerance_deg: Annotated[float | None, Field(description="Tolerance of that search (deg).")] = None,
        align_from: Annotated[str | None, Field(description="Start of that search (UTC date).")] = None,
        align_to: Annotated[str | None, Field(description="End of that search (UTC date).")] = None,
) -> dict[str, Any]:
    """Build a HelioFleet URL that opens a chosen view of the spacecraft map or the sky view, with
    no computation.

    Use when the user wants a link to share or open, with settings the other tools do not set
    (frame, zoom, hidden bodies, a marked spot, a tab, an alignment search). Every data tool
    already returns a link to its own view. For HelioField pages (3D corona, connectivity, space
    weather) use build_heliofield_link."""
    return fleet.link(time, page, tab=tab, observer=observer, frame=frame, view=view, zoom=zoom, hide=hide,
                      spirals=spirals, solar_wind_km_s=solar_wind_km_s, spot_system=spot_system,
                      spot_lon=spot_lon, spot_lat=spot_lat, align_kind=align_kind, align_a=align_a,
                      align_b=align_b, align_tolerance_deg=align_tolerance_deg, align_from=align_from,
                      align_to=align_to)


@tool(mcp, "Bodies and instruments available")
def list_bodies(
        include_instruments: Annotated[bool, Field(
            description="Also list the observation instruments of search_observations with the months "
                        "they cover.")] = True,
) -> dict[str, Any]:
    """List every body the tools accept (Earth, the spacecraft and the inner planets) with its key,
    full and short names, accepted aliases, kind, launch, loss-of-contact and end dates, ephemeris
    span and whether it can be a sky-view observer; and, optionally, the observation instruments
    with their facility, first and last month and number of records.

    Use first when unsure which key or name to pass, whether a body has data at a date, or which
    instruments search_observations covers. For the data release and per-series spans use
    get_data_status; for positions use get_position or get_trajectory."""
    return fleet.list_bodies(include_instruments)


@tool(mcp, "Loaded data release")
def get_data_status() -> dict[str, Any]:
    """Get which HelioFleet data release is loaded (build time, next monthly update, source) and
    each body's ephemeris span.

    Use to check how far the data reach before asking about distant dates, or to report the data
    version with results. Takes no parameters."""
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
