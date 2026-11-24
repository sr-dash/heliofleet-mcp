"""Trajectory sampling and the observation-footprint search."""

import pytest

from heliofleet_mcp.observations import Observations, _axes, _carry, earth_view


@pytest.fixture(scope="module")
def obs(fleet):
    return Observations(fleet.store)


def test_trajectory_matches_position(fleet):
    tr = fleet.trajectory("psp", "2025-03-20", "2025-03-25", step_hours=6)
    assert len(tr["rows"]) == 21
    cols = tr["columns"]
    row = dict(zip(cols, tr["rows"][4]))
    p = fleet.position("psp", row["time_utc"])
    for c in ("r_au", "hgs_lon_deg", "carrington_lon_deg", "light_time_s", "footpoint_hgs_lon_deg"):
        assert row[c] == p[c]
    assert [row["hee_x_au"], row["hee_y_au"], row["hee_z_au"]] == p["hee_au"]
    assert tr["extremes"]["closest_to_sun"]["r_au"] == min(r[cols.index("r_au")] for r in tr["rows"])


def test_trajectory_limits_and_gaps(fleet):
    with pytest.raises(ValueError, match="at most"):
        fleet.trajectory("earth", "2010-01-01", "2020-01-01", step_hours=1)
    with pytest.raises(ValueError, match="before start"):
        fleet.trajectory("earth", "2020-01-02", "2020-01-01")
    tr = fleet.trajectory("juice", "2023-03-01", "2023-05-01", step_hours=24 * 10)
    assert tr["rows"][0][1] == "prelaunch" and tr["rows"][0][2] is None
    assert tr["rows"][-1][1] in ("ok", "lost")
    assert "footpoint_hgs_lon_deg" not in fleet.trajectory("mars", "2025-01-01", "2025-01-03")["columns"]


def test_carry_is_identity_for_same_observer():
    a = _axes(*earth_view(2460000.5))
    x, y, hidden = _carry(300.0, -200.0, a, a)
    assert abs(x - 300.0) < 1e-6 and abs(y + 200.0) < 1e-6 and not hidden


def test_search_iris_and_point(obs):
    r = obs.search("2024-03-01T04:00Z", "2024-03-01T06:00Z", "iris")
    first = r["observations"][0]
    assert first["id"] == "20240301_043205_3882010194"
    assert first["field_earth_view"]["center_x_arcsec"] == pytest.approx(0.8, abs=0.1)
    assert set(first["sdo_images_png"]) == {"aia171", "aia193", "hmi"}
    assert first["data_link"].startswith("https://www.lmsal.com/")
    hit = obs.search("2012-07-11T18:00Z", "2012-07-11T20:00Z", None, -130, -450)
    assert [o["id"] for o in hit["observations"]] == ["hic-2012"]
    miss = obs.search("2012-07-11T18:00Z", "2012-07-11T20:00Z", "rocket", 800, 800)
    assert miss["total"] == 0


def test_search_solar_orbiter_is_carried_to_earth(obs):
    r = obs.search("2024-03-01", "2024-03-02", "solo", max_results=5)
    o = r["observations"][0]
    assert o["facility"] == "solo" and "recorded_field" in o
    assert len(o["field_earth_view"]["polygon_x_arcsec"]) > len(o["recorded_field"]["polygon_x_arcsec"])


def test_search_rejects_bad_input(obs):
    with pytest.raises(ValueError, match="unknown instrument"):
        obs.search("2024-03-01", instruments="hubble")
    with pytest.raises(ValueError, match="366 days"):
        obs.search("2020-01-01", "2022-01-01")
    with pytest.raises(ValueError, match="both"):
        obs.search("2024-03-01", x_arcsec=10)


def test_coordinated(obs):
    g = obs.coordinated("2012-01-01", "2020-01-01", "rocket")
    assert g["total"] == 4
    assert all("rocket" in x["facilities"] for x in g["groups"])


def test_list_bodies(fleet):
    d = fleet.list_bodies()
    keys = [b["key"] for b in d["bodies"]]
    from heliofleet_mcp.catalog import BODIES, resolve
    assert keys == list(BODIES)
    for b in d["bodies"]:
        assert b["ephemeris_start_utc"] and b["ephemeris_end_utc"]
        for a in b["aliases"]:
            assert resolve(a) == b["key"]
    stb = next(b for b in d["bodies"] if b["key"] == "stb")
    assert stb["ended_utc"].startswith("2018-10-17") and stb["sky_view_observer"]
    inst = {i["key"]: i for i in d["observation_instruments"]}
    assert inst["iris"]["first_month"] == "2013-07" and inst["hic"]["facility"] == "rocket"
    assert all(i["records"] > 0 for i in inst.values())
    assert "observation_instruments" not in fleet.list_bodies(False)
