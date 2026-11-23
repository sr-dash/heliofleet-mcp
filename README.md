# heliofleet-mcp

<!-- mcp-name: io.github.sr-dash/heliofleet-mcp -->

[![PyPI](https://img.shields.io/pypi/v/heliofleet-mcp)](https://pypi.org/project/heliofleet-mcp/)
[![MCP Registry](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fregistry.modelcontextprotocol.io%2Fv0%2Fservers%2Fio.github.sr-dash%252Fheliofleet-mcp%2Fversions%2Flatest&query=%24.server.version&label=MCP%20Registry&color=blue)](https://registry.modelcontextprotocol.io/v0/servers/io.github.sr-dash%2Fheliofleet-mcp/versions/latest)
[![API reference](https://img.shields.io/badge/docs-API%20reference-blue)](https://sr-dash.github.io/heliofleet-mcp/)
[![tests](https://github.com/sr-dash/heliofleet-mcp/actions/workflows/tests.yml/badge.svg)](https://github.com/sr-dash/heliofleet-mcp/actions/workflows/tests.yml)
[![release](https://github.com/sr-dash/heliofleet-mcp/actions/workflows/release.yml/badge.svg)](https://github.com/sr-dash/heliofleet-mcp/actions/workflows/release.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://pypi.org/project/heliofleet-mcp/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://github.com/sr-dash/heliofleet-mcp/blob/main/LICENSE)
[![Data: HelioFleet](https://img.shields.io/badge/data-HelioFleet-orange)](https://sr-dash.github.io/heliofleet/)
[![Data: HelioField](https://img.shields.io/badge/data-HelioField-orange)](https://sr-dash.github.io/heliofield/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24409982.svg)](https://doi.org/10.5281/zenodo.24409982)

A small [Model Context Protocol](https://modelcontextprotocol.io) server that answers
spacecraft-geometry questions from [HelioFleet](https://sr-dash.github.io/heliofleet/)'s published
data: where the heliophysics fleet is, what each spacecraft sees of the Sun, and when two of them
line up. It is a thin layer over HelioFleet's static JSON files (JPL Horizons ephemerides,
2010 to about 2030, refreshed monthly). Nothing is recomputed from scratch. The frame and
alignment code is a line-by-line port of the page's own JavaScript, so the numbers match the site.

Every answer carries a HelioFleet link that reproduces the view in the browser. The same answers are
available as an MCP server, as one-shot commands that print JSON, and as a Python API.

![One command finds the next Parker Solar Probe and Solar Orbiter alignment (1 December 2026, 18:00 UTC, 6.2 degrees apart); its link opens the same moment on HelioFleet.](https://raw.githubusercontent.com/sr-dash/heliofleet-mcp/main/docs/demo.gif)

## Tools

| Tool | What it returns |
| --- | --- |
| `get_position(body, time)` | Distance from the Sun; Stonyhurst lon/lat; Carrington longitude seen from Earth; ecliptic J2000 and HEE vectors; angle from Earth and distance to Earth; light time; Parker-spiral footpoint |
| `get_fleet_state(time)` | The same columns for Earth, every spacecraft on the map, and optionally Mercury, Venus and Mars |
| `find_alignments(kind, a, b, tolerance_deg, start, end)` | Windows of `radial` alignment, `quadrature` with Earth, solar `conjunction` (behind the Sun seen from Earth) or magnetic `connection` (Parker-spiral footpoints). Each window has start, end, best time and value, plus a link that reruns the search on the page |
| `list_upcoming_events(start, end)` | HelioFleet's calendar: perihelia, alignments, quadratures, conjunctions and eclipses. Optionally adds DONKI flares, CMEs and storms |
| `viewing_geometry(observer, time)` | Light time and offset from Earth, RSUN_OBS, B0, HGLN_OBS, L0 (CRLN_OBS, the observer's own light time), km per arcsec and scale relative to Earth, with a sky-view link |
| `heliofleet_link(...)` | A map or sky-view URL for a time, frame, zoom, hidden bodies, surface spot, tab or alignment search |
| `data_status()` | Which data release is loaded, where it came from, and each body's span |

### HelioField plugin (on by default)

These tools add the coronal magnetic field from [HelioField](https://sr-dash.github.io/heliofield/)'s
daily PFSS products. They read published files and do not solve the field.

| Tool | What it returns |
| --- | --- |
| `magnetic_connection(body, date, solar_wind_km_s)` | Where Earth, the L1 fleet, Parker, Solar Orbiter, BepiColombo or STEREO-A connects to the Sun: the Parker-spiral point on the source surface, the PFSS footpoint (Carrington), the expansion factor, distance to the coronal-hole boundary and a WSA-type speed. `self_consistent=True` uses each body's own speed estimate |
| `space_weather(date)` | Model wind speed and sector at Earth, the next sector boundary, a −1 to +7 day outlook, an alert level, and that day's solar wind measured at L1 |
| `coronal_field(date)` | Magnetogram, PFSS settings, open flux and Earth's L0/B0, plus solar-cycle context per Carrington rotation (open flux and area, current-sheet tilt, polar fields; any date since 2010) |
| `heliofield_link(...)` | A link to the 3D corona, connectivity, space-weather or observations page |

Daily products cover about the last two months. For older dates the tools return links, because the
HelioField page computes any date since 2010-05-01 in the browser. HelioField's Carrington positions
of the fleet agree with HelioFleet's to 0.002°, and a test checks this. Set
`HELIOFLEET_MCP_PLUGINS=none` to serve the HelioFleet tools alone.

Bodies: `earth sdo soho aditya ace wind dscovr imap swfo cgo solo psp bepi sta stb maven messenger vex juno rosetta juice clipper psyche mercury venus mars`.
Common names also work, such as "Parker", "Solar Orbiter" and "STEREO-A". Times are UTC in ISO 8601
(`2026-11-19T12:00Z`, `2026-11-19`), `now`, or a Julian date.

## Quick start

With [uv](https://docs.astral.sh/uv/) installed, one command downloads and starts the server:

```bash
uvx heliofleet-mcp
```

It speaks MCP over stdio, so on its own it waits silently for a client. Register it with one:

**Claude Code**, for all projects:

```bash
claude mcp add heliofleet --scope user -- uvx heliofleet-mcp
```

**Claude Desktop** and other MCP clients take this `mcpServers` entry. In Claude Desktop it goes in
Settings → Developer → Edit Config, then restart the app. In a project, it can go in `.mcp.json`.

```json
{
  "mcpServers": {
    "heliofleet": {
      "command": "uvx",
      "args": ["heliofleet-mcp"]
    }
  }
}
```

Then ask, for example, "When are Parker and Solar Orbiter next radially aligned?" To work offline
from a heliofleet checkout, add `"env": {"HELIOFLEET_SOURCE": "local", "HELIOFLEET_LOCAL_DATA":
"/path/to/heliofleet/data"}` to the entry.

## Where it is published

| | |
| --- | --- |
| PyPI | [`heliofleet-mcp`](https://pypi.org/project/heliofleet-mcp/), with wheel and source archive (also attached to each [GitHub release](https://github.com/sr-dash/heliofleet-mcp/releases)) |
| MCP Registry | [`io.github.sr-dash/heliofleet-mcp`](https://registry.modelcontextprotocol.io/v0/servers/io.github.sr-dash%2Fheliofleet-mcp/versions/latest) in the [official MCP Registry](https://registry.modelcontextprotocol.io), from which registry-aware clients and directories pick it up |
| Source | [github.com/sr-dash/heliofleet-mcp](https://github.com/sr-dash/heliofleet-mcp) ([changelog](https://github.com/sr-dash/heliofleet-mcp/blob/main/CHANGELOG.md)) |

The Registry entry ([`server.json`](https://github.com/sr-dash/heliofleet-mcp/blob/main/server.json))
declares the PyPI package, `uvx` as the runtime, stdio transport and the optional settings
`HELIOFLEET_SOURCE`, `HELIOFLEET_LOCAL_DATA` and `HELIOFLEET_MCP_PLUGINS`.

## Other ways to install

The only runtime dependency is the `mcp` Python SDK (1.x or 2.x); Python 3.10 or newer.

```bash
pipx install heliofleet-mcp        # or: pip install heliofleet-mcp  (https://pypi.org/project/heliofleet-mcp/)
heliofleet-mcp                     # or: python -m heliofleet_mcp
```

From a clone, for development:

```bash
git clone https://github.com/sr-dash/heliofleet-mcp && cd heliofleet-mcp
python3 -m venv .venv && .venv/bin/pip install -e '.[test]' jplephem
```

## Command line

The same program answers one question and prints the tool's JSON, with no server or client set-up.

```bash
uvx heliofleet-mcp align psp solo --tol 10 --after 2026-11-19 --next   # next Parker-Solar Orbiter alignment
uvx heliofleet-mcp align sta --kind quadrature --after 2027-01-01      # STEREO-A quadratures in 2027
uvx heliofleet-mcp position parker --time 2025-03-22T22:25Z            # coordinates at a moment
uvx heliofleet-mcp geometry solo                                       # B0, L0, solar radius from Solar Orbiter now
uvx heliofleet-mcp events --kind perihelion,alignment                  # the coming year's calendar
uvx heliofleet-mcp connection psp --wind 450                           # where Parker connects to the Sun
uvx heliofleet-mcp spaceweather                                        # HelioField's outlook at Earth
uvx heliofleet-mcp --help
```

Commands: `align`, `position`, `fleet`, `events`, `geometry`, `link`, `status`, `connection`,
`spaceweather`, `field`. Add `--compact` for one-line JSON. An error prints `{"error": ...}` on stderr
and exits with status 2. With no command, the program serves MCP over stdio.

## Python

```python
from heliofleet_mcp import Fleet, HelioField

fleet = Fleet()
fleet.find_alignments("radial", "psp", "solo", 10, "2026-11-19", max_windows=1)
fleet.position("Solar Orbiter", "2026-11-19T12:00Z")
fleet.viewing_geometry("psp", "2025-03-22T22:25Z")
HelioField().magnetic_connection("psp", solar_wind_km_s=450)
```

The methods return the same dictionaries as the MCP tools. `Fleet` and `HelioField` take a
`Store` or `FieldStore` for a different source, cache or offline checkout.

The [API reference](https://sr-dash.github.io/heliofleet-mcp/) documents every public class and function, with parameters, return
values and examples (numpydoc docstrings, built with MkDocs Material and mkdocstrings). The examples
run as doctests in CI.

## For assistants

[`AGENTS.md`](https://github.com/sr-dash/heliofleet-mcp/blob/main/AGENTS.md) tells an assistant how to
answer questions with this package in any environment: MCP, shell commands, Python, or plain web
fetches of the published data. It also lists the conventions to keep, such as UTC times, the
Stonyhurst sign, the alignment sampling and model caveats.
[`llms.txt`](https://github.com/sr-dash/heliofleet-mcp/blob/main/llms.txt) is the short index.

## Skill and plugins

[`skills/heliofleet/SKILL.md`](https://github.com/sr-dash/heliofleet-mcp/blob/main/skills/heliofleet/SKILL.md)
is an [Agent Skill](https://agentskills.io): it teaches an assistant which `heliofleet-mcp` command
answers which question and how to report the result. It needs only a shell and the installed
`heliofleet-mcp` command, no MCP set-up, and works in any assistant that reads Agent Skills.

| Where | Install |
| --- | --- |
| Any assistant that reads Agent Skills ([skills.sh](https://skills.sh)) | `npx skills add sr-dash/heliofleet-mcp` |
| Claude Code (plugin: the skill and the MCP server) | `/plugin marketplace add sr-dash/heliofleet-mcp`, then `/plugin install heliofleet@sr-dash` |
| Cursor (plugin: the skill and the MCP server) | from the Cursor Marketplace once listed, or copy `skills/heliofleet` to `~/.cursor/skills/` |
| Codex | copy `skills/heliofleet` to `~/.agents/skills/` (or `.agents/skills/` in a project) |

The plugin manifests are `.claude-plugin/` (with `marketplace.json`, so this repository is its own
marketplace), `.cursor-plugin/plugin.json`, and the [Agent Plugins](https://agent-plugins.org)
`plugin.json` at the root. `plugins/heliofleet/` is a skill-only edition for plugin directories that
accept only documentation files. CI validates the skill and the Agent Plugins manifest on each push.

## Example

> When is the next Parker Solar Probe and Solar Orbiter radial alignment within 10° after 2026-11-19?

`find_alignments(kind="radial", a="psp", b="solo", tolerance_deg=10, start="2026-11-19", max_windows=1)`:

```json
{
  "start_utc": "2026-12-01T16:00:00Z",
  "end_utc": "2026-12-01T19:00:00Z",
  "duration_days": 0.125,
  "best_time_utc": "2026-12-01T18:00:00Z",
  "best_value_deg": 6.173,
  "a_at_best": {"body": "psp", "r_au": 0.0504, "hgs_lon_deg": 39.551, "hgs_lat_deg": -2.141},
  "b_at_best": {"body": "solo", "r_au": 0.8614, "hgs_lon_deg": 37.749, "hgs_lat_deg": 3.763},
  "link": "https://sr-dash.github.io/heliofleet/?t=2026-12-01T18:00Z&align=radial,psp,solo,10,2026-11-19,2027-11-19&tab=align#tools"
}
```

This is Parker's perihelion pass. Parker sweeps 4 to 5° an hour in Stonyhurst longitude and
passes Solar Orbiter's longitude (37.7°). JPL Horizons gives separations of 8.91°, 6.29°, 6.18°
and 9.07° at 16, 17, 18 and 19 UT.

## Data and caching

Files are fetched from `https://sr-dash.github.io/heliofleet/data/`. They are cached under
`~/.cache/heliofleet-mcp/<release>/`, keyed by the manifest's build time, so a monthly update never
mixes with older files. The manifest is checked again every 6 hours. If the site cannot be reached,
the server uses the cached manifest, then a local heliofleet checkout. A sibling `heliofleet/data`
folder is found automatically.

| Variable | Default | Meaning |
| --- | --- | --- |
| `HELIOFLEET_SOURCE` | `auto` | `auto` (site, then local), `web`, or `local` |
| `HELIOFLEET_LOCAL_DATA` | sibling `heliofleet/data` | local data folder |
| `HELIOFLEET_CACHE` | `~/.cache/heliofleet-mcp` | cache folder |
| `HELIOFLEET_SITE` | `https://sr-dash.github.io/heliofleet/` | site root |
| `HELIOFLEET_MCP_PLUGINS` | `heliofield` | optional tool sets, or `none` |
| `HELIOFIELD_SITE` | `https://sr-dash.github.io/heliofield/` | HelioField site root |
| `HELIOFIELD_LOCAL` | sibling `heliofield` | local HelioField checkout |

HelioField files go in the same cache. Dated products are kept for good, and the index and series
files are refreshed hourly.

## Methods

- Positions are interpolated with HelioFleet's 4-point Lagrange scheme (`js/ephem.js`). L1
  monitors stored as geocentric km are added to Earth's heliocentric position (`js/scene.js`).
- Stonyhurst (HEEQ) and Carrington coordinates use the IAU rotation model, as in SunPy (`js/frames.js`).
  The pole is at RA 286.13°, Dec 63.87°, with W = 84.176° + 14.1844°/day since J2000 TT. Carrington
  longitudes see the Sun one light time in the past: Earth's light time for coordinate tables, the
  observer's own for viewing geometry (CRLN_OBS).
- The alignment search (`js/tools.js` `findAlignments`) samples hourly when Parker is involved and
  every 6 hours otherwise. Windows are runs of samples within the tolerance, so window edges sit on
  that grid. Solar conjunctions follow `scripts/build_calendar.py`.
- Spacecraft status follows the map: `ok`, `lost` (a prediction after loss of contact), or `approx`
  (SDO past the end of its ephemeris, shown at Earth).

Full methods: <https://sr-dash.github.io/heliofleet/methods.html>.

## Tests

```bash
.venv/bin/pip install -e '.[test]' jplephem
.venv/bin/python -m pytest
```

- `test_reference.py`: interpolation against JPL Horizons, and Stonyhurst/Carrington against SunPy,
  using HelioFleet's reference set (`tests/data/reference.json`). The limit is 0.005°. The worst case
  is 0.0004°.
- `test_sunpy.py`: frame conversions against SunPy computed live. It covers Earth's B0 and L0
  against `sunpy.coordinates.sun`, and Venus and Mars end to end against DE432s.
- `test_alignments.py`: windows identical to the page's own `findAlignments` (run live through Node
  when a heliofleet checkout is next to this one, otherwise a stored fixture), and the demo query
  against Horizons.
- `test_server_stdio.py`: the server started over stdio and called through the MCP client.
- `test_data_sources.py`: site fetch and cache (marked `network`), and the local fallback.
- `test_cli.py`: the one-shot commands, JSON errors and the Python API.
- `test_heliofield.py`: the plugin's daily products, links as in HelioField's `llms.txt`, and
  HelioField's fleet positions and L0/B0 against HelioFleet's frames.

`HELIOFLEET_TEST_SOURCE=web` runs the suite on the live sites instead of local checkouts. CI runs it
on Linux (Python 3.10 to 3.14), macOS and Windows, reports coverage (`pytest --cov`), and checks the
code style with ruff (`ruff check src tests scripts`).

## Contributing

Reports, ideas and pull requests are welcome: see [CONTRIBUTING.md](https://github.com/sr-dash/heliofleet-mcp/blob/main/CONTRIBUTING.md),
which also says when a contribution is not accepted, and the
[code of conduct](https://github.com/sr-dash/heliofleet-mcp/blob/main/CODE_OF_CONDUCT.md) (Contributor Covenant 2.1).

## Releasing

1. Set the new version in `src/heliofleet_mcp/__init__.py`, both `version` fields of `server.json`,
   `CITATION.cff`, `.zenodo.json` and the three plugin manifests, and add a section to `CHANGELOG.md`. `python scripts/check_release.py` checks
   that they agree.
2. Commit, push, and publish a GitHub release tagged `vX.Y.Z`.
3. The `release` workflow then runs the tests and builds the package. It publishes to PyPI by
   trusted publishing, attaches the files to the release, waits for PyPI, and publishes
   `server.json` to the MCP Registry under `io.github.sr-dash/heliofleet-mcp`. Zenodo archives the
   release and mints a version DOI.

The `tests` workflow validates the package and `server.json` on every push.

## Licence and citation

MIT. To cite this package: Dash, S. (2026). *heliofleet-mcp: spacecraft geometry and solar magnetic
connectivity from HelioFleet and HelioField data* [Computer software]. Zenodo. <https://doi.org/10.5281/zenodo.24409982>.
That DOI resolves to the latest release; [10.5281/zenodo.24481640](https://doi.org/10.5281/zenodo.24481640) is version 0.3.0, [10.5281/zenodo.24411341](https://doi.org/10.5281/zenodo.24411341) is version 0.2.0,
[10.5281/zenodo.24411004](https://doi.org/10.5281/zenodo.24411004) is version 0.1.2
and [10.5281/zenodo.24409983](https://doi.org/10.5281/zenodo.24409983) is version 0.1.1.
[`CITATION.cff`](https://github.com/sr-dash/heliofleet-mcp/blob/main/CITATION.cff) drives GitHub's
**Cite this repository** button. When you use positions,
please also cite HelioFleet: Dash, S. (2026). *HelioFleet:
an interactive map of heliophysics spacecraft positions* [Computer software]. Zenodo.
<https://doi.org/10.5281/zenodo.23328187>. Ephemerides: JPL Horizons. For coronal-field results,
cite HelioField (<https://doi.org/10.5281/zenodo.23487231>) and the magnetogram (NSO/GONG or SDO/HMI).
