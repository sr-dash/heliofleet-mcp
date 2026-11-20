"""Alignment search: parity with HelioFleet's page code, and the demo query against Horizons."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from heliofleet_mcp.data import _default_local
from heliofleet_mcp.timeutil import iso, parse_time

HERE = Path(__file__).parent
FIXTURE = json.loads((HERE / "data" / "page_alignments.json").read_text())


def page_windows(cases):
    """Run js/tools.js findAlignments live when node and a heliofleet checkout exist, else the fixture."""
    local = _default_local()
    if shutil.which("node") and local and (local.parent / "js" / "tools.js").exists():
        q = [{k: c[k] for k in ("kind", "a", "b", "tol", "from", "to")} for c in cases]
        out = subprocess.run(["node", str(HERE / "js" / "page_alignments.mjs"), str(local.parent), json.dumps(q)],
                             capture_output=True, text=True, check=True, timeout=300)
        return json.loads(out.stdout), "live"
    return [c["windows"] for c in cases], "fixture"


def test_parity_with_page(fleet):
    expected, how = page_windows(FIXTURE["cases"])
    if how == "fixture" and fleet.store.manifest()["generated"] != FIXTURE["generated_from"].split()[-1]:
        pytest.skip("data release differs from the fixture and the page code is not available")
    for case, want in zip(FIXTURE["cases"], expected):
        res = fleet.find_alignments(case["kind"], case["a"], case["b"], case["tol"], case["from"], case["to"])
        got = [[w["start_utc"], w["end_utc"], w["best_time_utc"], w["best_value_deg"]] for w in res["windows"]]
        assert len(got) == len(want), case
        for g, w in zip(got, want):
            assert g[:3] == w[:3], case
            assert abs(g[3] - w[3]) < 1e-3, case


def test_demo_next_psp_solo_radial(fleet):
    """'Next PSP-Solar Orbiter radial alignment within 10 deg after 2026-11-19'.

    JPL Horizons (via SunPy, hourly) gives Sun-centred separations on 2026-12-01 of
    8.913 deg at 16:00, 6.286 at 17:00, 6.184 at 18:00 and 9.070 at 19:00 UTC, and above 10 deg
    at 15:00 and 20:00: the window is 16:00-19:00 with the minimum at 18:00.
    """
    res = fleet.find_alignments("radial", "Parker", "Solar Orbiter", 10, "2026-11-19", max_windows=1)
    (w,) = res["windows"]
    assert w["start_utc"] == "2026-12-01T16:00:00Z"
    assert w["end_utc"] == "2026-12-01T19:00:00Z"
    assert w["best_time_utc"] == "2026-12-01T18:00:00Z"
    assert abs(w["best_value_deg"] - 6.184) < 0.02
    assert res["step_hours"] == 1.0
    assert w["link"].startswith("https://sr-dash.github.io/heliofleet/?t=2026-12-01T18:00Z")
    assert "align=radial,psp,solo,10,2026-11-19,2027-11-19" in w["link"]


def test_quadrature_and_conjunction_agree_with_calendar(fleet):
    """The calendar's quadratures and conjunctions (build_calendar.py, 3-hour grid) fall in found windows."""
    up = fleet.upcoming_events("2026-11-01", "2028-01-01")["events"]
    events = [e for e in up if e["kind"] in ("quadrature", "conjunction")][:4]
    assert events
    for ev in events:
        tol = 1.0 if ev["kind"] == "quadrature" else 2.0
        t = parse_time(ev["time_utc"])
        res = fleet.find_alignments(ev["kind"], ev["bodies"][0], None, tol, iso(t - 3), iso(t + 3))
        assert res["windows"], ev["title"]
        best = min(res["windows"], key=lambda w: w["best_value_deg"])
        assert abs(parse_time(best["best_time_utc"]) - t) <= 0.5, ev["title"]
        assert best["best_value_deg"] <= tol


def test_errors(fleet):
    with pytest.raises(ValueError):
        fleet.find_alignments("radial", "psp", "psp", 5, "2026-01-01", "2026-02-01")
    with pytest.raises(ValueError):
        fleet.find_alignments("sideways", "psp", "solo")
    with pytest.raises(ValueError):
        fleet.find_alignments("radial", "psp", "solo", 5, "2026-02-01", "2026-01-01")
