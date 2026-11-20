"""Links, time parsing, events and the remaining tools."""

from urllib.parse import parse_qs, urlparse

import pytest

from heliofleet_mcp.catalog import resolve
from heliofleet_mcp.links import map_link, sky_link
from heliofleet_mcp.timeutil import iso, parse_time


def q(url):
    return {k: v[0] for k, v in parse_qs(urlparse(url).query).items()}


def test_parse_time():
    assert iso(parse_time("2025-03-22T22:25Z")) == "2025-03-22T22:25:00Z"
    assert iso(parse_time("2025-03-22 22:25")) == "2025-03-22T22:25:00Z"
    assert iso(parse_time("2025-03-22")) == "2025-03-22T00:00:00Z"
    assert iso(parse_time("2025-03-22T23:25+01:00")) == "2025-03-22T22:25:00Z"
    assert parse_time(2451545.0) == 2451545.0
    with pytest.raises(ValueError):
        parse_time(2025)


def test_resolve():
    assert resolve("Parker") == "psp"
    assert resolve("Solar Orbiter") == "solo"
    assert resolve("STEREO-A") == "sta"
    assert resolve("SOLAR-1") == "swfo"
    with pytest.raises(ValueError):
        resolve("voyager")


def test_map_link_matches_page_format():
    jd = parse_time("2025-06-01T00:00Z")
    url = map_link(jd, align={"kind": "radial", "a": "solo", "b": "psp", "tol": 5,
                              "from": "2025-01-01", "to": "2025-12-31"})
    # The example link in llms.txt, parameter for parameter
    assert q(url) == q("https://sr-dash.github.io/heliofleet/?t=2025-06-01T00:00Z&tab=align"
                       "&align=radial,solo,psp,5,2025-01-01,2025-12-31#tools")
    assert url.endswith("#tools")
    assert q(map_link(jd, tab="geom"))["tab"] == "geom"
    assert q(map_link(jd, spot={"sys": "carrington", "lon": 120, "lat": -15}))["spot"] == "c,120,-15"
    assert q(map_link(jd, wind=400)) == {"t": "2025-06-01T00:00Z"}


def test_sky_link():
    jd = parse_time("2024-04-08T18:00Z")
    assert sky_link(jd) == "https://sr-dash.github.io/heliofleet/sky.html?t=2024-04-08T18:00Z"
    assert q(sky_link(jd, "solo"))["obs"] == "solo"


def test_position_and_fleet(fleet):
    row = fleet.position("psp", "2025-03-22T22:25Z")
    assert row["status"] == "ok" and 0.045 < row["r_au"] < 0.047
    assert row["link"] == "https://sr-dash.github.io/heliofleet/?t=2025-03-22T22:25Z"
    state = fleet.fleet_state("2015-06-01T00:00Z")
    keys = {b["body"] for b in state["bodies"]}
    assert {"earth", "sta", "soho", "venus"} <= keys
    assert {"body": "psp", "status": "prelaunch"} in state["not_shown"]
    stb = next(b for b in state["bodies"] if b["body"] == "stb")
    assert stb["status"] == "lost"
    # L1 monitors sit about 0.01 au sunward of Earth
    soho = next(b for b in state["bodies"] if b["body"] == "soho")
    assert 0.98 < soho["r_au"] / next(b for b in state["bodies"] if b["body"] == "earth")["r_au"] < 0.995


def test_viewing_geometry(fleet):
    res = fleet.viewing_geometry("psp", "2025-03-22T22:25Z")
    (row,) = res["observers"]
    assert row["rsun_arcsec"] > 15000  # about 21 times Earth's 960"
    assert row["offset_vs_earth_s"] < -400
    assert row["sky_link"].endswith("obs=psp")
    assert "tab=geom" in res["link"]
    allrows = fleet.viewing_geometry("all", "2025-03-22T22:25Z")["observers"]
    earth = next(r for r in allrows if r["body"] == "earth")
    assert 940 < earth["rsun_arcsec"] < 1000 and earth["scale_vs_earth"] == 1.0


def test_upcoming_events(fleet):
    res = fleet.upcoming_events("2026-11-01", "2027-12-31", kind="perihelion", body="psp")
    assert res["events"] and all(e["kind"] == "perihelion" and "psp" in e["bodies"] for e in res["events"])
    assert all(e["link"].startswith("https://sr-dash.github.io/heliofleet/?t=") for e in res["events"])
    sw = fleet.upcoming_events("2024-05-01", "2024-05-31", include_space_weather=True)["space_weather"]
    assert any(e["type"] == "storm" for e in sw["events"])  # the G5 storm of 10-11 May 2024


def test_outside_range(fleet):
    with pytest.raises(ValueError):
        fleet.position("earth", "2005-01-01")
    assert fleet.position("psp", "2015-01-01")["status"] == "prelaunch"
