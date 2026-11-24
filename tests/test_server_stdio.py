"""The server runs over stdio and answers the demo query through the MCP protocol."""

import json
import os
import sys

import anyio
import pytest

mcp = pytest.importorskip("mcp")
from mcp import ClientSession  # noqa: E402
from mcp.client.stdio import StdioServerParameters, stdio_client  # noqa: E402

from heliofleet_mcp.data import _default_local  # noqa: E402

EXPECTED = {"get_position", "get_fleet_state", "find_alignments", "list_upcoming_events",
            "get_viewing_geometry", "build_heliofleet_link", "get_data_status",
            "get_trajectory", "search_observations", "find_coordinated_observations", "list_bodies",
            "get_magnetic_connection", "get_space_weather", "get_coronal_field", "build_heliofield_link"}


def _payload(result):
    if getattr(result, "structuredContent", None):
        sc = result.structuredContent
        return sc.get("result", sc) if set(sc) == {"result"} else sc
    return json.loads(result.content[0].text)


async def _session_run():
    env = dict(os.environ)
    local = _default_local()
    if local:
        env.update(HELIOFLEET_SOURCE="local", HELIOFLEET_LOCAL_DATA=str(local))
    params = StdioServerParameters(command=sys.executable, args=["-m", "heliofleet_mcp"], env=env)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = {t.name for t in (await session.list_tools()).tools}
            demo = await session.call_tool("find_alignments", {
                "kind": "radial", "a": "psp", "b": "solo", "tolerance_deg": 10,
                "start": "2026-11-19", "max_windows": 1})
            pos = await session.call_tool("get_position", {"body": "Solar Orbiter", "time": "2026-11-19T00:00Z"})
            link = await session.call_tool("build_heliofleet_link", {"time": "2026-11-19T00:00Z", "page": "sky",
                                                               "observer": "solo"})
            return tools, _payload(demo), _payload(pos), _payload(link)


def test_stdio_roundtrip():
    tools, demo, pos, link = anyio.run(_session_run)
    assert EXPECTED <= tools
    w = demo["windows"][0]
    assert (w["start_utc"], w["end_utc"], w["best_time_utc"]) == (
        "2026-12-01T16:00:00Z", "2026-12-01T19:00:00Z", "2026-12-01T18:00:00Z")
    assert pos["body"] == "solo" and pos["link"].startswith("https://sr-dash.github.io/heliofleet/")
    assert link["link"] == "https://sr-dash.github.io/heliofleet/sky.html?t=2026-11-19T00:00Z&obs=solo"
