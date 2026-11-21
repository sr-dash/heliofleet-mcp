"""Heliophysics spacecraft geometry from HelioFleet's published data: an MCP server and a Python API.

    from heliofleet_mcp import Fleet
    Fleet().find_alignments("radial", "psp", "solo", 10, "2026-11-19", max_windows=1)

    from heliofleet_mcp import HelioField
    HelioField().magnetic_connection("psp")
"""

__version__ = "0.1.2"
__all__ = ["Fleet", "HelioField", "Store", "FieldStore", "__version__"]


def __getattr__(name):  # import lazily, so the package loads without the MCP SDK
    if name == "Fleet":
        from .geometry import Fleet
        return Fleet
    if name == "Store":
        from .data import Store
        return Store
    if name in ("HelioField", "FieldStore"):
        from . import heliofield
        return getattr(heliofield, name)
    raise AttributeError(f"module 'heliofleet_mcp' has no attribute {name!r}")
