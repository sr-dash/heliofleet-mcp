"""Interpolation and heliographic coordinates against JPL Horizons and SunPy reference values.

tests/data/reference.json is HelioFleet's own reference set (scripts/make_reference.py): Horizons
vectors at times between samples, and SunPy Stonyhurst/Carrington coordinates.
"""

import json

import pytest

from heliofleet_mcp.frames import AU_KM, heliographic, norm, sub, wrap180

from pathlib import Path

DATA = Path(__file__).parent / "data"

REF = json.loads((DATA / "reference.json").read_text())
# Interpolation limits (km) from HelioFleet's tests/validate.mjs
INTERP_KM = {"default": 50, "psp": 700, "solo": 450, "stb": 130, "bepi": 2800, "maven": 11000}
ANGLE_DEG = 0.005


@pytest.mark.parametrize("case", REF["interp"], ids=lambda c: f"{c['key']}@{c['jd']:.3f}")
def test_interpolation_vs_horizons(fleet, case):
    p = fleet.store.position(case["key"], case["jd"])
    assert p is not None
    k = AU_KM if case["units"] == "au" else 1.0
    err_km = norm(sub(p, case["p"])) * k
    assert err_km <= INTERP_KM.get(case["key"], INTERP_KM["default"])


@pytest.mark.parametrize("case", REF["helio"], ids=lambda c: f"{c['key']}@{c['jd']:.3f}")
def test_heliographic_vs_sunpy(fleet, case):
    jd = case["jd"]
    p = fleet.store.position(case["key"], jd)
    e = fleet.store.position("earth", jd)
    g = heliographic(p, e, jd)
    assert abs(wrap180(g["lon"] - case["lon"])) <= ANGLE_DEG
    assert abs(g["lat"] - case["lat"]) <= ANGLE_DEG
    assert abs(wrap180(g["carr"] - case["carr"])) <= ANGLE_DEG


def test_get_position_tool_matches_reference(fleet):
    """The tool's rounded output agrees with SunPy as well."""
    for case in REF["helio"]:
        if case["key"] not in ("psp", "solo", "sta", "stb", "bepi", "maven", "earth"):
            continue
        row = fleet.position(case["key"], case["jd"])
        assert abs(wrap180(row["hgs_lon_deg"] - case["lon"])) <= ANGLE_DEG
        assert abs(row["hgs_lat_deg"] - case["lat"]) <= ANGLE_DEG
        assert abs(wrap180(row["carrington_lon_deg"] - case["carr"])) <= ANGLE_DEG
