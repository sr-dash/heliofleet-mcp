"""Start an installed server over stdio, list its tools and make one call.

Usage: python scripts/smoke_stdio.py /path/to/heliofleet-mcp   (needs the mcp package)
"""

import sys

import anyio
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

EXPECTED = {"get_position", "get_fleet_state", "find_alignments", "list_upcoming_events",
            "get_viewing_geometry", "build_heliofleet_link", "get_data_status",
            "get_magnetic_connection", "get_space_weather", "get_coronal_field", "build_heliofield_link"}


async def run(cmd: str) -> None:
    async with stdio_client(StdioServerParameters(command=cmd, args=sys.argv[2:])) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            names = {t.name for t in (await s.list_tools()).tools}
            missing = EXPECTED - names
            if missing:
                raise SystemExit(f"missing tools: {sorted(missing)}")
            res = await s.call_tool("build_heliofleet_link", {"time": "2026-11-19T00:00Z"})
            if getattr(res, "is_error", False) or getattr(res, "isError", False):
                raise SystemExit(f"tool call failed: {res}")
            print(f"ok: {len(names)} tools")


anyio.run(run, sys.argv[1])
