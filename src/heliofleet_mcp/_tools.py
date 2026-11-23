"""Shared MCP tool settings: every tool only reads published data."""

from __future__ import annotations

from typing import Any


def tool(server: Any, title: str):
    """``server.tool`` with a title and read-only annotations.

    Every tool reads HelioFleet's or HelioField's published files (over the network unless a
    local checkout is used) and changes nothing, so all are marked read-only, non-destructive,
    idempotent and open-world. SDKs older than mcp 1.9 take no annotations; there the tool is
    registered without them.

    Parameters
    ----------
    server : mcp.server.fastmcp.FastMCP or mcp.server.mcpserver.MCPServer
        The server to register the tool on.
    title : str
        Human-readable tool title.

    Returns
    -------
    callable
        The decorator ``server.tool`` returns.
    """
    try:
        from mcp.types import ToolAnnotations
    except ImportError:  # pragma: no cover - very old SDK
        return server.tool()
    hints = ToolAnnotations(title=title, readOnlyHint=True, destructiveHint=False,
                            idempotentHint=True, openWorldHint=True)
    try:
        return server.tool(title=title, annotations=hints)
    except TypeError:  # pragma: no cover - SDKs without title or annotations
        try:
            return server.tool(annotations=hints)
        except TypeError:
            return server.tool()
