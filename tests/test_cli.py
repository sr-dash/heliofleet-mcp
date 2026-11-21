"""The one-shot command line prints the same JSON as the tools, and the Python API imports."""

import json
import subprocess
import sys

import pytest

from heliofleet_mcp import __version__
from heliofleet_mcp.cli import main


def run(capsys, *argv):
    code = main(list(argv))
    out, err = capsys.readouterr()
    return code, out, err


def test_align_demo(capsys):
    code, out, _ = run(capsys, "align", "psp", "solo", "--tol", "10", "--after", "2026-11-19", "--next")
    assert code == 0
    (w,) = json.loads(out)["windows"]
    assert (w["start_utc"], w["best_time_utc"]) == ("2026-12-01T16:00:00Z", "2026-12-01T18:00:00Z")


def test_compact_anywhere(capsys):
    for argv in (["--compact", "position", "parker", "--time", "2025-03-22T22:25Z"],
                 ["position", "parker", "--time", "2025-03-22T22:25Z", "--compact"]):
        code, out, _ = run(capsys, *argv)
        assert code == 0 and out.count("\n") == 1
        row = json.loads(out)
        assert row["body"] == "psp" and row["link"].endswith("t=2025-03-22T22:25Z")


def test_geometry_events_link_status(capsys):
    code, out, _ = run(capsys, "geometry", "psp", "--time", "2025-03-22T22:25Z")
    assert code == 0 and json.loads(out)["observers"][0]["sky_link"].endswith("obs=psp")
    code, out, _ = run(capsys, "events", "--after", "2026-11-01", "--before", "2027-12-31", "--kind", "perihelion")
    assert code == 0 and all(e["kind"] == "perihelion" for e in json.loads(out)["events"])
    code, out, _ = run(capsys, "link", "--page", "sky", "--observer", "Solar Orbiter", "--time", "2026-11-19")
    assert json.loads(out) == {"link": "https://sr-dash.github.io/heliofleet/sky.html?t=2026-11-19T00:00Z&obs=solo"}
    code, out, _ = run(capsys, "status")
    assert code == 0 and "psp" in json.loads(out)["bodies"]


def test_heliofield_commands(capsys):
    code, out, _ = run(capsys, "field", "--date", "2014-03-12")
    assert code == 0 and json.loads(out)["daily_product"] is False


def test_errors_are_json_on_stderr(capsys):
    code, out, err = run(capsys, "align", "psp", "psp")
    assert code == 2 and out == ""
    assert json.loads(err)["error"] == "a and b must differ"


def test_version_and_python_api():
    out = subprocess.run([sys.executable, "-m", "heliofleet_mcp", "--version"], capture_output=True, text=True)
    assert out.stdout.strip() == f"heliofleet-mcp {__version__}"
    import heliofleet_mcp
    assert heliofleet_mcp.Fleet.__name__ == "Fleet" and heliofleet_mcp.HelioField.__name__ == "HelioField"
    with pytest.raises(AttributeError):
        heliofleet_mcp.Nope  # noqa: B018
