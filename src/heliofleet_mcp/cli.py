"""Command line: run the MCP server, or answer one question and print JSON.

  heliofleet-mcp                         serve MCP over stdio (what MCP clients launch)
  heliofleet-mcp align psp solo --tol 10 --after 2026-11-19 --next
  heliofleet-mcp position "Solar Orbiter" --time 2026-11-19T12:00Z
  heliofleet-mcp --help                  every command

Each command prints the same JSON as the matching MCP tool, HelioFleet or HelioField link included.
Errors go to stderr as {"error": ...} with exit status 2.
"""

from __future__ import annotations

import argparse
import json
import sys

from . import __version__

EPILOG = """examples:
  heliofleet-mcp align psp solo --tol 10 --after 2026-11-19 --next
  heliofleet-mcp align sta --kind quadrature --after 2027-01-01 --before 2028-01-01
  heliofleet-mcp position parker --time 2025-03-22T22:25Z
  heliofleet-mcp geometry solo --time now
  heliofleet-mcp events --kind perihelion,alignment
  heliofleet-mcp connection psp --wind 450
  heliofleet-mcp spaceweather

Times are UTC (ISO 8601, a date, 'now', or a Julian date). Bodies: earth sdo soho aditya ace wind
dscovr imap swfo cgo solo psp bepi sta stb maven messenger vex juno rosetta juice clipper psyche
mercury venus mars, or names such as "Parker".
With no command, the MCP server runs over stdio."""


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="heliofleet-mcp", formatter_class=argparse.RawDescriptionHelpFormatter, epilog=EPILOG,
        description="Heliophysics spacecraft geometry from HelioFleet and HelioField data: an MCP server, "
                    "and one-shot commands that print JSON.")
    p.add_argument("--version", action="version", version=f"heliofleet-mcp {__version__}")
    p.add_argument("--compact", action="store_true", help="print JSON on one line")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--compact", action="store_true", default=argparse.SUPPRESS, help="print JSON on one line")
    sub = p.add_subparsers(dest="cmd", metavar="COMMAND")

    def add(name, **kw):
        return sub.add_parser(name, parents=[common], **kw)

    add("serve", help="run the MCP server over stdio (the default)")

    c = add("position", help="where one body is (get_position)")
    c.add_argument("body")
    c.add_argument("--time", default="now")
    c.add_argument("--wind", type=float, default=400.0, help="solar wind for the footpoint, km/s")

    c = add("fleet", help="every spacecraft and planet at a time (get_fleet_state)")
    c.add_argument("--time", default="now")
    c.add_argument("--no-planets", action="store_true")
    c.add_argument("--wind", type=float, default=400.0)

    c = add("align", help="alignment windows (find_alignments)")
    c.add_argument("a", help="first body")
    c.add_argument("b", nargs="?", help="second body (radial, connection)")
    c.add_argument("--kind", default="radial", choices=["radial", "quadrature", "conjunction", "connection"])
    c.add_argument("--tol", type=float, help="tolerance in degrees (default depends on kind)")
    c.add_argument("--after", "--start", dest="start", default="now")
    c.add_argument("--before", "--end", dest="end", help="default: one year after the start")
    c.add_argument("--next", action="store_true", help="only the first window")
    c.add_argument("--max", type=int, dest="max_windows", help="at most this many windows")
    c.add_argument("--wind", type=float, default=400.0, help="solar wind for --kind connection, km/s")

    c = add("events", help="HelioFleet's event calendar (list_upcoming_events)")
    c.add_argument("--after", "--start", dest="start", default="now")
    c.add_argument("--before", "--end", dest="end")
    c.add_argument("--kind", help="comma list: perihelion, alignment, quadrature, conjunction, eclipse")
    c.add_argument("--body")
    c.add_argument("--space-weather", action="store_true", help="add DONKI flares, CMEs and storms")

    c = add("geometry", help="what an observer sees of the Sun (viewing_geometry)")
    c.add_argument("observer", nargs="?", default="all")
    c.add_argument("--time", default="now")

    c = add("link", help="a HelioFleet map or sky-view link (heliofleet_link)")
    c.add_argument("--time", default="now")
    c.add_argument("--page", choices=["map", "sky"], default="map")
    c.add_argument("--observer", default="earth", help="sky view observer")
    c.add_argument("--tab", choices=["coords", "geom", "align", "vis", "series", "anim"])

    add("status", help="which data release is loaded (data_status)")

    c = add("connection", help="magnetic connection to the Sun, HelioField (magnetic_connection)")
    c.add_argument("body", nargs="?", default="all")
    c.add_argument("--date", default="latest")
    c.add_argument("--wind", type=float, default=400.0)
    c.add_argument("--self-consistent", action="store_true", help="use each body's own WSA speed")

    c = add("spaceweather", help="HelioField space-weather indicators (space_weather)")
    c.add_argument("--date", default="latest")

    c = add("field", help="coronal field summary, HelioField (coronal_field)")
    c.add_argument("--date", default="latest")
    return p


def run(args: argparse.Namespace):
    """Answer one parsed command.

    Parameters
    ----------
    args : argparse.Namespace
        Arguments from the command-line parser.

    Returns
    -------
    dict
        The JSON-ready result, the same as the matching MCP tool's.

    Raises
    ------
    ValueError
        For an unknown command, or bad input passed on from the tool.

    Examples
    --------
    >>> run(_parser().parse_args(["link", "--time", "2025-03-22T22:25Z", "--tab", "geom"]))
    {'link': 'https://sr-dash.github.io/heliofleet/?t=2025-03-22T22:25Z&tab=geom#tools'}
    """
    if args.cmd in ("connection", "spaceweather", "field"):
        from .heliofield import HelioField
        hf = HelioField()
        if args.cmd == "connection":
            return hf.magnetic_connection(args.body, args.date, args.wind, args.self_consistent)
        if args.cmd == "spaceweather":
            return hf.space_weather(args.date)
        return hf.coronal_field(args.date)

    from .geometry import Fleet
    f = Fleet()
    if args.cmd == "position":
        return f.position(args.body, args.time, args.wind)
    if args.cmd == "fleet":
        return f.fleet_state(args.time, not args.no_planets, args.wind)
    if args.cmd == "align":
        return f.find_alignments(args.kind, args.a, args.b, args.tol, args.start, args.end, args.wind,
                                 1 if args.next else args.max_windows)
    if args.cmd == "events":
        return f.upcoming_events(args.start, args.end, args.kind, args.body, args.space_weather)
    if args.cmd == "geometry":
        return f.viewing_geometry(args.observer, args.time)
    if args.cmd == "link":
        return f.link(args.time, args.page, tab=args.tab, observer=args.observer)
    if args.cmd == "status":
        return f.data_status()
    raise ValueError(f"unknown command {args.cmd}")


def main(argv: list[str] | None = None) -> int:
    """Entry point of the ``heliofleet-mcp`` command.

    With no command (or ``serve``), runs the MCP server over stdio. Otherwise answers one
    command and prints its JSON to stdout; errors go to stderr as ``{"error", "type"}``.

    Parameters
    ----------
    argv : list of str, optional
        Arguments without the program name. Default: ``sys.argv[1:]``.

    Returns
    -------
    int
        Exit status: 0 on success, 2 on an error.

    Examples
    --------
    >>> main(["link", "--time", "2025-03-22T22:25Z", "--compact"])
    {"link":"https://sr-dash.github.io/heliofleet/?t=2025-03-22T22:25Z"}
    0
    """
    args = _parser().parse_args(argv)
    if args.cmd in (None, "serve"):
        from .server import main as serve
        serve()
        return 0
    try:
        result = run(args)
    except Exception as err:  # bad input or data unavailable: one JSON line on stderr
        print(json.dumps({"error": str(err), "type": type(err).__name__}), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":") if args.compact else None,
                     indent=None if args.compact else 2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
