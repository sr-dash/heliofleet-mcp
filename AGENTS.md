# Using heliofleet-mcp to answer questions

This file is for assistants and automated tools that answer questions about where heliophysics
spacecraft are, what they see of the Sun, when they line up, and how they connect magnetically to
the Sun. It covers using this repository to answer such questions and working on its code.

## Pick the route your environment allows

1. **You can launch MCP servers** (stdio): run `uvx heliofleet-mcp` (or `heliofleet-mcp` after
   `pip install heliofleet-mcp`) and call its tools. It is listed in the MCP Registry as
   `io.github.sr-dash/heliofleet-mcp`.
2. **You can run shell commands** but not MCP: use the same program's one-shot commands, which print
   JSON. No server or configuration is needed.

   ```bash
   uvx heliofleet-mcp align psp solo --tol 10 --after 2026-11-19 --next
   uvx heliofleet-mcp position "Solar Orbiter" --time 2026-11-19T12:00Z
   uvx heliofleet-mcp geometry psp --time 2025-03-22T22:25Z
   uvx heliofleet-mcp events --kind perihelion,alignment,quadrature
   uvx heliofleet-mcp connection psp --wind 450
   uvx heliofleet-mcp spaceweather
   uvx heliofleet-mcp --help
   ```

   With pip instead of uv: `pip install heliofleet-mcp`, then the same commands without `uvx`.
3. **You can run Python**:

   ```python
   from heliofleet_mcp import Fleet, HelioField
   f = Fleet()
   f.find_alignments("radial", "psp", "solo", 10, "2026-11-19", max_windows=1)
   f.position("psp", "2025-03-22T22:25Z")
   HelioField().magnetic_connection("solo")
   ```

   The API reference is at https://sr-dash.github.io/heliofleet-mcp/.

4. **You can only fetch web pages**: read the data directly. HelioFleet's guide for automated readers
   is https://sr-dash.github.io/heliofleet/llms.txt, and the formulas are on
   https://sr-dash.github.io/heliofleet/methods.html. Positions are in
   `https://sr-dash.github.io/heliofleet/data/<body>/<year>.json`. The calendar of perihelia,
   alignments, quadratures and conjunctions is `https://sr-dash.github.io/heliofleet/data/upcoming.json`.
   HelioField's guide is https://sr-dash.github.io/heliofield/llms.txt.

To install these instructions as a reusable skill, use
[`skills/heliofleet/SKILL.md`](https://github.com/sr-dash/heliofleet-mcp/blob/main/skills/heliofleet/SKILL.md)
(an [Agent Skill](https://agentskills.io): `npx skills add sr-dash/heliofleet-mcp`).

## Commands and tools

| Question | Command | MCP tool |
| --- | --- | --- |
| Where is a spacecraft or planet? | `position BODY --time T` | `get_position` |
| Where is everything? | `fleet --time T` | `get_fleet_state` |
| When are two bodies aligned, or one in quadrature or conjunction? | `align A [B] --kind K --tol DEG --after T [--before T] [--next]` | `find_alignments` |
| What is coming up (perihelia, alignments, eclipses)? | `events [--kind ...] [--body B]` | `list_upcoming_events` |
| What does an observer see of the Sun (B0, L0, solar radius, light time)? | `geometry OBSERVER --time T` | `viewing_geometry` |
| A link to show the user | `link --time T [--page sky --observer B]` | `heliofleet_link` |
| Where does a spacecraft connect to the Sun? | `connection BODY [--wind V]` | `magnetic_connection` |
| Solar-wind and sector outlook at Earth | `spaceweather [--date D]` | `space_weather` |
| Coronal field, open flux, solar-cycle context | `field [--date D]` | `coronal_field` |
| Which data release is loaded | `status` | `data_status` |

Alignment kinds:
- `radial`: the Sun-centred angle between A and B is within the tolerance (default 5°).
- `quadrature`: A is 90° from Earth seen from the Sun (default 5°).
- `conjunction`: A is behind the Sun seen from Earth (default 2°).
- `connection`: the Parker-spiral footpoints of A and B are within the tolerance (default 10°).

## Conventions to keep when you answer

- Times are UTC. Inputs may be ISO 8601 (`2026-11-19T12:00Z`), a date, `now`, or a Julian date.
- Bodies: `earth sdo soho aditya ace wind dscovr imap swfo cgo solo psp bepi sta stb maven messenger vex juno rosetta juice clipper psyche mercury
  venus mars`. Names such as "Parker", "Solar Orbiter" and "STEREO-A" also work.
- Stonyhurst longitude is measured from the Sun–Earth line, positive to the west. Carrington
  longitude is as seen from Earth, one light time in the past, as in SunPy. Viewing geometry uses the
  observer's own light time (CRLN_OBS).
- Alignment windows are sampled hourly when Parker is involved and every 6 hours otherwise. Report
  window edges at that resolution.
- Every result has a `link` (or `links`). Give it to the user with the numbers, so they can see the
  configuration on HelioFleet or HelioField.
- A `status` of `lost` means the position is a prediction after contact was lost. `approx` means the
  body is shown at Earth's position past the end of its ephemeris. `prelaunch` and `ended` mean
  there is no position.
- HelioField results are PFSS model output with indicative WSA-type speeds. They are not observations
  or an official forecast; NOAA SWPC issues those. Say so when you report them.
- Ephemerides run from 2010 to about 2030 and are refreshed monthly from JPL Horizons. HelioField's
  daily products cover about the last two months. For older dates its tools return links to pages
  that compute any date since 2010-05-01.

## Citing

Cite HelioFleet (https://doi.org/10.5281/zenodo.23328187) for positions and geometry. Cite
HelioField (https://doi.org/10.5281/zenodo.23487231) and the magnetogram (NSO/GONG or SDO/HMI) for
coronal-field results. Cite this package as https://doi.org/10.5281/zenodo.24409982 (see `CITATION.cff`).

## Working on the code

- Install: `python3 -m venv .venv && .venv/bin/pip install -e '.[test]' jplephem`.
- Test: `.venv/bin/python -m pytest -q`. The tests compare with SunPy and with HelioFleet's page code.
  With `HELIOFLEET_TEST_SOURCE=web` they use the live sites instead of local checkouts.
- Geometry is a port of HelioFleet's `js/frames.js`, `js/ephem.js` and `js/tools.js`. A change there
  should keep `tests/test_reference.py` and `tests/test_alignments.py` passing.
- Release: see "Releasing" in `README.md`. `python scripts/check_release.py` must pass. Commits are
  authored by Soumyaranjan Dash, with messages of at most 120 characters and no trailers.
