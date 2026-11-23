---
name: heliofleet
description: >-
  Answer questions about heliophysics spacecraft geometry from JPL Horizons ephemerides: where Parker
  Solar Probe, Solar Orbiter, STEREO-A, BepiColombo, SDO, SOHO, ACE, Wind, DSCOVR, Aditya-L1, IMAP and
  the planets are; when two of them line up (radial alignment, quadrature with Earth, solar
  conjunction, Parker-spiral magnetic connection); what each sees of the Sun (B0, L0/CRLN_OBS,
  apparent solar radius, light time); upcoming perihelia and events; and where each connects
  magnetically to the Sun (PFSS footpoints, expansion factor, space-weather outlook). Use when the user
  asks about spacecraft positions, alignments, conjunctions, quadratures, perihelia, viewing geometry,
  Carrington or Stonyhurst coordinates, or solar magnetic connectivity. Runs the heliofleet-mcp
  command line, which prints JSON with a HelioFleet or HelioField link for every answer.
license: MIT
compatibility: >-
  Needs the heliofleet-mcp command (a Python 3.10+ package; install guide at
  https://sr-dash.github.io/heliofleet-mcp/getting-started/) and internet access to sr-dash.github.io,
  or a local HelioFleet checkout set with HELIOFLEET_LOCAL_DATA.
metadata:
  author: Soumyaranjan Dash
  homepage: https://sr-dash.github.io/heliofleet-mcp/
  repository: https://github.com/sr-dash/heliofleet-mcp
---

# HelioFleet: heliophysics spacecraft geometry

Answer with the `heliofleet-mcp` command line. Every command prints JSON (use `--compact` for one
line) and every result carries a `link` (or `links`) to HelioFleet or HelioField that reproduces the
view. Report the numbers and give the user the link.

## Running it

```bash
heliofleet-mcp <command> [options] --compact
```

- If the command is not found, the package is not installed. Point the user to the install guide,
  https://sr-dash.github.io/heliofleet-mcp/getting-started/, and continue once it is installed.
- If the heliofleet MCP tools are already available in this session (`find_alignments`,
  `get_position`, ...), call those instead: they return the same JSON.
- Errors print `{"error": ..., "type": ...}` on stderr with exit status 2. Read the message, fix the
  body name, time or range, and retry.

## Which command answers which question

| Question | Command |
| --- | --- |
| When are A and B next aligned (seen from the Sun)? | `align A B --tol 10 --after T --next` |
| When is A in quadrature with Earth (90° from Earth)? | `align A --kind quadrature --after T` |
| When is A behind the Sun seen from Earth (solar conjunction)? | `align A --kind conjunction --after T` |
| When are A and B magnetically connected (Parker-spiral footpoints)? | `align A B --kind connection --wind 400 --after T` |
| Where is A at a time? | `position A --time T` |
| Where is everything? | `fleet --time T` |
| What does an observer see of the Sun (B0, L0, solar radius, light time)? | `geometry OBSERVER --time T` |
| What is coming up (perihelia, alignments, eclipses)? | `events --kind perihelion,alignment --body A` |
| Flares, CMEs, storms in a period? | `events --after T1 --before T2 --space-weather` |
| Where does A connect to the Sun today (PFSS footpoint)? | `connection A --wind 450` |
| Solar-wind and sector outlook at Earth? | `spaceweather` |
| Coronal field, open flux, solar-cycle context? | `field --date D` |
| A link to show the user | `link --time T` or `link --time T --page sky --observer solo` |
| Which data release is loaded? | `status` |

Options: `--after`/`--before` (aliases `--start`/`--end`) bound a search; the default range is one
year from `--after` (default now). `--next` returns only the first window; `--max N` at most N.
`--tol` is in degrees; defaults are radial 5, quadrature 5, conjunction 2, connection 10.

## Bodies and times

- Bodies: `earth sdo soho aditya ace wind dscovr imap swfo cgo solo psp bepi sta stb maven messenger vex juno rosetta juice clipper psyche mercury
  venus mars`. Names also work: "Parker", "Solar Orbiter", "STEREO-A", "BepiColombo".
- Times are UTC: ISO 8601 (`2026-11-19T12:00Z`), a date (`2026-11-19`, midnight UTC), `now`, or a
  Julian date. Convert the user's local time to UTC first and say so.
- Ephemerides cover 2010 to about 2030 and are refreshed monthly from JPL Horizons. HelioField's daily
  products cover about the last two months; for older dates its commands return links to pages that
  compute any date since 2010-05-01.

## Rules for the answer

1. Give times in UTC, to the precision of the result. Alignment windows are sampled hourly when
   Parker is involved and every six hours otherwise: report window edges and best times at that
   resolution, not more precisely.
2. Stonyhurst longitude (`hgs_lon_deg`) is measured from the Sun–Earth line, positive to the west.
   Carrington longitude is as seen from Earth one light time earlier, as in SunPy; viewing geometry
   uses the observer's own light time (`l0_deg`, CRLN_OBS).
3. Check `status`: `lost` means a prediction after contact was lost (STEREO-B, MAVEN, Venus Express); `approx` means
   shown at Earth past the end of its ephemeris; `prelaunch` and `ended` have no position. Say so.
4. HelioField results (`connection`, `spaceweather`, `field`) are PFSS model output with indicative
   WSA-type speeds, not observations or an official forecast (NOAA SWPC issues those). Say so.
5. If `windows` is empty, say none was found in the range and offer a wider tolerance or range.
   If `touches_range_edge` is true, the window may extend past the searched range.
6. Always include the `link` from the result.
7. For citations: HelioFleet https://doi.org/10.5281/zenodo.23328187 (positions), HelioField
   https://doi.org/10.5281/zenodo.23487231 (coronal field), heliofleet-mcp
   https://doi.org/10.5281/zenodo.24409982.

## Example

User: "When are Parker Solar Probe and Solar Orbiter next radially aligned within 10° after
19 November 2026?"

```bash
heliofleet-mcp align psp solo --tol 10 --after 2026-11-19 --next --compact
```

The first window is 2026-12-01 16:00 to 19:00 UTC, closest at 18:00 UTC with the two 6.2° apart seen
from the Sun (`best_value_deg` 6.173; Parker at 0.050 au, Solar Orbiter at 0.861 au). Answer with
those values, note the hourly sampling, and give the window's `link`.

More detail on each command's output fields: [references/output-fields.md](references/output-fields.md).
