"""Frame conventions against SunPy computed live, on HelioFleet's own positions.

The heliocentric vectors come from HelioFleet's data; SunPy converts them to Stonyhurst and
Carrington, so these checks isolate the frame code (the point of the 0.005 deg budget).
Planets are also checked end to end against SunPy's DE432s positions.
"""

import pytest

sunpy = pytest.importorskip("sunpy")
import astropy.units as u  # noqa: E402
from astropy.coordinates import HeliocentricMeanEcliptic, SkyCoord, solar_system_ephemeris  # noqa: E402
from astropy.time import Time  # noqa: E402
from sunpy.coordinates import frames, get_body_heliographic_stonyhurst, sun  # noqa: E402

from heliofleet_mcp.frames import heliographic, wrap180  # noqa: E402
from heliofleet_mcp.timeutil import iso, parse_time  # noqa: E402

TOL = 0.005
TIMES = ["2011-06-07T06:30Z", "2014-10-01T00:00Z", "2019-04-04T22:40Z", "2021-08-09T12:00Z",
         "2023-11-14T03:15Z", "2025-03-22T22:25Z", "2026-11-19T00:00Z", "2028-12-31T18:00Z"]
BODIES = ["psp", "solo", "sta", "bepi", "venus", "mars", "mercury"]


def sunpy_coords(p_au, t):
    c = SkyCoord(*(v * u.au for v in p_au), frame=HeliocentricMeanEcliptic(obstime=t, equinox="J2000"),
                 representation_type="cartesian")
    hgs = c.transform_to(frames.HeliographicStonyhurst(obstime=t))
    hgc = c.transform_to(frames.HeliographicCarrington(obstime=t, observer="earth"))
    return hgs.lon.deg, hgs.lat.deg, hgs.radius.to_value(u.au), hgc.lon.deg


@pytest.mark.parametrize("when", TIMES)
def test_frames_vs_sunpy(fleet, when):
    jd = parse_time(when)
    t = Time(iso(jd).rstrip("Z"), scale="utc")
    e = fleet.store.position("earth", jd)
    checked = 0
    for key in BODIES:
        st, p = fleet.at(key, jd, e)
        if p is None:
            continue
        g = heliographic(p, e, jd)
        lon, lat, r, carr = sunpy_coords(p, t)
        assert abs(wrap180(g["lon"] - lon)) <= TOL, key
        assert abs(g["lat"] - lat) <= TOL, key
        assert abs(wrap180(g["carr"] - carr)) <= TOL, key
        assert abs(g["dist"] - r) < 1e-9
        checked += 1
    assert checked >= 3


@pytest.mark.parametrize("when", TIMES[:6])
def test_earth_b0_l0(fleet, when):
    """Earth's disk centre: B0 and L0 as sunpy.coordinates.sun."""
    jd = parse_time(when)
    t = Time(iso(jd).rstrip("Z"), scale="utc")
    row = fleet.viewing_geometry("earth", jd)["observers"][0]
    assert abs(row["b0_deg"] - sun.B0(t).deg) <= TOL
    assert abs(wrap180(row["l0_deg"] - sun.L0(t).deg)) <= TOL
    assert abs(row["hgs_lon_deg"]) < 1e-9


@pytest.mark.parametrize("when", TIMES[:7])
@pytest.mark.parametrize("planet", ["venus", "mars"])
def test_planets_end_to_end(fleet, when, planet):
    """HelioFleet (Horizons) positions converted to Stonyhurst against SunPy with DE432s."""
    pytest.importorskip("jplephem")
    jd = parse_time(when)
    t = Time(iso(jd).rstrip("Z"), scale="utc")
    row = fleet.position(planet, jd)
    try:
        with solar_system_ephemeris.set("de432s"):
            ref = get_body_heliographic_stonyhurst(planet, t)
    except Exception as err:  # ephemeris download unavailable
        pytest.skip(f"DE432s unavailable: {err}")
    assert abs(wrap180(row["hgs_lon_deg"] - ref.lon.deg)) <= TOL
    assert abs(row["hgs_lat_deg"] - ref.lat.deg) <= TOL
    assert abs(row["r_au"] - ref.radius.to_value(u.au)) < 2e-6
