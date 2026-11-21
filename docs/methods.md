---
description: "How heliofleet-mcp computes positions, Stonyhurst and Carrington coordinates, Parker-spiral footpoints and alignment windows, and how it is checked against SunPy and Horizons."
---

# Methods and data

heliofleet-mcp is a thin layer over published files. Nothing is recomputed from scratch: the frame
and alignment code is a line-by-line port of HelioFleet's own JavaScript, so the numbers match the
site. The full methods, with every formula, are on HelioFleet's
[methods page](https://sr-dash.github.io/heliofleet/methods.html).

## Positions

- Heliocentric ecliptic J2000 vectors from [JPL Horizons](https://ssd.jpl.nasa.gov/horizons/), on a
  uniform UT grid (daily for most bodies, every 3 hours for Parker), 2010 to about 2030, refreshed
  monthly.
- Interpolated with HelioFleet's 4-point Lagrange scheme (`js/ephem.js`).
- L1 monitors stored as geocentric km are added to Earth's heliocentric position (`js/scene.js`).
- Spacecraft status follows the map: `ok`, `lost` (a prediction after loss of contact) or `approx`
  (past the end of an ephemeris, shown at Earth).

## Solar coordinates

- Stonyhurst (HEEQ) and Carrington coordinates use the IAU rotation model, as in SunPy
  (`js/frames.js`): pole at RA 286.13°, Dec 63.87°, W = 84.176° + 14.1844°/day since J2000 TT.
- Carrington longitudes see the Sun one light time in the past: Earth's light time in coordinate
  tables, the observer's own in viewing geometry (CRLN_OBS).
- Parker-spiral footpoint: φ_foot = φ + Ω (r − R☉) / v, with the sidereal rate and a constant wind.

## Alignment search

- Samples hourly when Parker is involved and every six hours otherwise (`js/tools.js`
  `findAlignments`). Windows are runs of samples within the tolerance, so their edges sit on that
  grid.
- Solar conjunctions follow `scripts/build_calendar.py`.

## Accuracy

| Check | Result |
| --- | --- |
| Stonyhurst and Carrington coordinates vs SunPy (HelioFleet's reference set) | worst 0.0004°, limit 0.005° |
| Earth's B0 and L0 vs `sunpy.coordinates.sun` | within the same limit |
| Venus and Mars end to end vs DE432s | within the same limit |
| Alignment windows vs HelioFleet's JavaScript, run under Node | identical |
| HelioField's fleet Carrington positions and L0/B0 vs HelioFleet's frames | within 0.002° |

The tests run on every push on Linux, macOS and Windows; see
[Contributing](contributing.md).

## Data and caching

Files come from `https://sr-dash.github.io/heliofleet/data/` and are cached under
`~/.cache/heliofleet-mcp/<release>/`, keyed by the manifest's build time, so a monthly update never
mixes with older files. The manifest is checked again every 6 hours. If the site cannot be reached,
the cached manifest is used, then a local HelioFleet checkout.

HelioField files go in the same cache: dated products are kept for good, and the index and series
are refreshed hourly. Settings are listed in [Getting started](getting-started.md#settings).
