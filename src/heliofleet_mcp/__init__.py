"""Heliophysics spacecraft geometry from HelioFleet's and HelioField's published data.

heliofleet-mcp answers where heliophysics spacecraft are, what each sees of the Sun, when two
line up, and where each connects magnetically to the Sun. The same answers are available as an
MCP server (``heliofleet-mcp``), a command line that prints JSON (``heliofleet-mcp <command>``) and
this Python API. Every result is a JSON-ready dict with a HelioFleet or HelioField link.

Main classes
------------
Fleet
    Positions, viewing geometry, alignment search and the event calendar
    (:mod:`heliofleet_mcp.geometry`).
HelioField
    PFSS magnetic connectivity, space-weather indicators and the coronal-field summary
    (:mod:`heliofleet_mcp.heliofield`).
Store, FieldStore
    The data sources: the sites, with a disk cache and a local-checkout fallback.

Lower-level modules: :mod:`heliofleet_mcp.frames` (solar coordinate frames),
:mod:`heliofleet_mcp.timeutil` (time parsing), :mod:`heliofleet_mcp.links` (page links) and
:mod:`heliofleet_mcp.catalog` (bodies and names).

Examples
--------
>>> from heliofleet_mcp import Fleet
>>> w = Fleet().find_alignments("radial", "solo", "psp", 5, "2025-01-01", "2025-12-31", max_windows=1)
>>> w["windows"][0]["best_value_deg"]
1.837
"""

__version__ = "0.2.0"

# These modules use only the standard library; the MCP SDK is imported by server.py alone.
from .data import Store  # noqa: E402
from .geometry import Fleet  # noqa: E402
from .heliofield import FieldStore, HelioField  # noqa: E402

__all__ = ["Fleet", "HelioField", "Store", "FieldStore", "__version__"]
