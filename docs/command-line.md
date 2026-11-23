---
description: "Ask one question from the shell and get JSON: next Parker and Solar Orbiter alignment, positions, B0 and L0, events and magnetic connectivity with uvx heliofleet-mcp."
---

# Command line

The same program answers one question and prints the matching tool's JSON, with no server or
client set-up. With no command, it serves MCP over stdio.

```bash
uvx heliofleet-mcp align psp solo --tol 10 --after 2026-11-19 --next   # (1)!
uvx heliofleet-mcp align sta --kind quadrature --after 2027-01-01      # (2)!
uvx heliofleet-mcp position parker --time 2025-03-22T22:25Z            # (3)!
uvx heliofleet-mcp geometry solo                                       # (4)!
uvx heliofleet-mcp events --kind perihelion,alignment                  # (5)!
uvx heliofleet-mcp connection psp --wind 450                           # (6)!
uvx heliofleet-mcp spaceweather                                        # (7)!
```

1. The next Parker–Solar Orbiter radial alignment within 10°.
2. STEREO-A quadratures with Earth during the year after 1 January 2027.
3. Coordinates of Parker at its perihelion of 22 March 2025.
4. B0, L0, light time and the Sun's apparent radius from Solar Orbiter now.
5. The coming year's perihelia and alignments from HelioFleet's calendar.
6. Where Parker connects magnetically to the Sun, for a 450 km/s wind.
7. HelioField's space-weather indicators at Earth.

## Commands

| Command | MCP tool | Main options |
| --- | --- | --- |
| `position BODY` | `get_position` | `--time`, `--wind` |
| `fleet` | `get_fleet_state` | `--time`, `--no-planets`, `--wind` |
| `align A [B]` | `find_alignments` | `--kind`, `--tol`, `--after`, `--before`, `--next`, `--max`, `--wind` |
| `events` | `list_upcoming_events` | `--after`, `--before`, `--kind`, `--body`, `--space-weather` |
| `geometry [OBSERVER]` | `get_viewing_geometry` | `--time` |
| `link` | `build_heliofleet_link` | `--time`, `--page map\|sky`, `--observer`, `--tab` |
| `status` | `get_data_status` | |
| `connection [BODY]` | `get_magnetic_connection` | `--date`, `--wind`, `--self-consistent` |
| `spaceweather` | `get_space_weather` | `--date` |
| `field` | `get_coronal_field` | `--date` |
| `serve` | (the MCP server) | |

`--compact` prints one-line JSON, before or after the command. `uvx heliofleet-mcp --help` and
`uvx heliofleet-mcp COMMAND --help` list every option.

## Errors

A bad body, time or range prints one JSON line on stderr and exits with status 2:

```console
$ uvx heliofleet-mcp position voyager
{"error": "unknown body 'voyager'; known: earth, sdo, soho, ...", "type": "ValueError"}
```
