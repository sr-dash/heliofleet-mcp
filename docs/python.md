---
description: "Use heliofleet-mcp from Python: Fleet and HelioField return positions, alignment windows, viewing geometry and magnetic connectivity as plain dictionaries with links."
---

# Python

```bash
pip install heliofleet-mcp
```

```python
from heliofleet_mcp import Fleet, HelioField

fleet = Fleet()
fleet.find_alignments("radial", "psp", "solo", 10, "2026-11-19", max_windows=1)
fleet.position("Solar Orbiter", "2026-11-19T12:00Z")
fleet.viewing_geometry("psp", "2025-03-22T22:25Z")
HelioField().magnetic_connection("psp", solar_wind_km_s=450)
```

The methods return the same dictionaries as the [MCP tools](tools.md). Importing the package does
not load the MCP SDK.

## Main classes

<div class="grid cards" markdown>

-   [`Fleet`][heliofleet_mcp.geometry.Fleet]

    ---

    Positions, fleet state, viewing geometry, alignment search, the event calendar and links.

-   [`HelioField`][heliofleet_mcp.heliofield.HelioField]

    ---

    PFSS magnetic connectivity, space-weather indicators and the coronal-field summary.

-   [`Store`][heliofleet_mcp.data.Store]

    ---

    HelioFleet's ephemerides: fetching, caching and Lagrange interpolation.

-   [`FieldStore`][heliofleet_mcp.heliofield.FieldStore]

    ---

    HelioField's daily products, cached on disk.

</div>

## Choosing the data source

`Fleet` and `HelioField` take a `Store` or `FieldStore`, for a different source, cache or an
offline checkout:

```python
from heliofleet_mcp import Fleet, Store

offline = Fleet(Store(source="local", local="/path/to/heliofleet/data"))
offline.position("psp", "2025-03-22T22:25Z")["r_au"]
```

## Lower-level helpers

The solar frames ([`heliographic`][heliofleet_mcp.frames.heliographic],
[`footpoint_lon`][heliofleet_mcp.frames.footpoint_lon]), time parsing
([`parse_time`][heliofleet_mcp.timeutil.parse_time]) and page links
([`map_link`][heliofleet_mcp.links.map_link], [`field_link`][heliofleet_mcp.heliofield.field_link])
use only the standard library and work on plain tuples and Julian dates.

Every public function and class is documented in the [API reference](api/index.md), with
parameters, return values and examples. The examples run as doctests in CI.
