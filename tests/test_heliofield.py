"""HelioField plugin: daily products, links, and agreement with HelioFleet's geometry."""

import os
from urllib.parse import parse_qs, urlparse

import pytest

from heliofleet_mcp.timeutil import parse_time
from heliofleet_mcp.heliofield import FieldStore, HelioField, _default_local, field_link


@pytest.fixture(scope="module")
def hf(tmp_path_factory):
    local = _default_local()
    if local and os.environ.get("HELIOFLEET_TEST_SOURCE", "local") == "local":
        return HelioField(FieldStore(source="local", local=local))
    h = HelioField(FieldStore(source="web", cache=tmp_path_factory.mktemp("hfcache")))
    try:
        h.dates()
    except Exception as err:
        pytest.skip(f"HelioField unavailable: {err}")
    return h


def q(url):
    return {k: v[0] for k, v in parse_qs(urlparse(url).query).items()}


def test_links_match_llms_recipes():
    url = field_link("latest", view="fleet", layers=["photo", "hcs", "fleet", "spiral"], scale=True, rmax=1.2)
    assert q(url) == q("https://sr-dash.github.io/heliofield/?date=latest&view=fleet"
                       "&layers=photo,hcs,fleet,spiral&scale=true&rmax=1.2")
    url = field_link("2025-03-22", "connect", scs=21.5, focus="solo", ins="metis")
    assert url.startswith("https://sr-dash.github.io/heliofield/connect.html?")
    assert q(url) == {"date": "2025-03-22", "scs": "21.5", "focus": "solo", "ins": "metis"}
    with pytest.raises(ValueError):
        field_link("latest", layers=["nonsense"])


def test_connection_latest(hf):
    r = hf.magnetic_connection("all", "latest", 400)
    assert r["daily_product"]
    bodies = {c["body"] for c in r["connections"]}
    assert {"earth", "psp", "solo"} <= bodies
    for c in r["connections"]:
        assert c["wind_used_km_s"] == 400
        assert 0 <= c["source_surface_point_deg"]["lon"] < 360
    assert r["links"]["heliofleet"].startswith("https://sr-dash.github.io/heliofleet/?t=")
    one = hf.magnetic_connection("Solar Orbiter", "latest", 450)
    assert len(one["connections"]) == 1 and "focus=solo" in one["links"]["connect"]
    assert "v=500" in one["links"]["connect"]  # pages offer 300..800 in steps of 100


def test_self_consistent_speed(hf):
    r = hf.magnetic_connection("all", "latest", self_consistent=True)
    for c in r["connections"]:
        if c["wsa_speed_km_s"]:
            assert abs(c["wsa_speed_km_s"] - c["wind_used_km_s"]) <= 150


def test_positions_agree_with_heliofleet(hf, fleet):
    """HelioField's Carrington fleet positions and Earth's L0/B0 match HelioFleet's frames."""
    d = hf.dates()[-1]
    meta = hf.store.json(f"data/{d}/meta.json")
    t = meta["obstime"]
    if fleet.earth(parse_time(t)) is None:
        pytest.skip("date outside the loaded ephemerides")
    g = fleet.viewing_geometry("earth", t)["observers"][0]
    assert abs(g["l0_deg"] - meta["L0"]) < 0.002
    assert abs(g["b0_deg"] - meta["B0"]) < 0.002
    for k in ("psp", "solo", "sta"):
        p = fleet.position(k, t)
        assert abs((p["carrington_lon_deg"] - meta["fleet"][k]["lon"] + 180) % 360 - 180) < 0.002, k
        assert abs(p["hgs_lat_deg"] - meta["fleet"][k]["lat"]) < 0.002, k


def test_space_weather(hf):
    r = hf.space_weather("latest")
    assert r["found"] and "v" in r["model"] and r["links"]["share_card"].endswith(f"sw/{r['date']}.png")
    assert not hf.space_weather("2012-01-01")["found"]


def test_coronal_field_past_date(hf):
    r = hf.coronal_field("2014-03-12")
    assert r["daily_product"] is False
    assert r["solar_cycle"]["carrington_rotation"] in (2147, 2148)
    assert "date=2014-03-12" in r["links"]["model_3d"]
    with pytest.raises(ValueError):
        hf.coronal_field("2009-01-01")
