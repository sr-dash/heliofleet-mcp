---
description: "The eleven heliofleet-mcp tools: spacecraft positions, fleet state, radial alignments, quadratures, conjunctions, events, viewing geometry and PFSS magnetic connectivity."
---

# MCP tools

Every tool returns JSON with a `link` (or `links`) that reproduces the view on HelioFleet or
HelioField; give it to the user with the numbers. The Python methods behind the tools are in the
[API reference](api/index.md).

## HelioFleet: positions and geometry

| Tool | What it returns |
| --- | --- |
| `get_position(body, time)` | Distance from the Sun; Stonyhurst lon/lat; Carrington longitude seen from Earth; ecliptic J2000 and HEE vectors; angle from Earth and distance to Earth; light time; Parker-spiral footpoint |
| `get_trajectory(body, start, end, step_hours)` | One body's coordinates sampled over a date range (up to 2000 samples) as a table with the same columns as `get_position`, plus the closest and farthest points from the Sun and the closest approach to Earth |
| `get_fleet_state(time)` | The same columns for Earth, every spacecraft on the map, and optionally Mercury, Venus and Mars |
| `find_alignments(kind, a, b, tolerance_deg, start, end)` | Windows of `radial` alignment, `quadrature` with Earth, solar `conjunction` or magnetic `connection`, each with start, end, best time and value, and a link that reruns the search |
| `list_upcoming_events(start, end)` | HelioFleet's calendar: perihelia, alignments, quadratures, conjunctions and eclipses; optionally DONKI flares, CMEs and storms |
| `get_viewing_geometry(observer, time)` | Light time and offset from Earth, RSUN_OBS, B0, HGLN_OBS, L0 (CRLN_OBS), km per arcsec and scale relative to Earth, with a sky-view link |
| `search_observations(start, end, instruments, x_arcsec, y_arcsec)` | IRIS, Hinode/EIS, DKIST, Solar Orbiter (EUI-HRI, PHI-HRT, SPICE), Hi-C and CLASP observations in a time range, optionally covering a point on the disk: dataset id, times, programme, field of view in Earth's helioprojective frame (centre, size, polygon), archive link, and SDO AIA 171, AIA 193 and HMI PNG cutouts around the field |
| `find_coordinated_observations(start, end, facilities)` | Groups of observations by different facilities that overlap in time and on the Sun: start, duration, shared point, facilities and counts, with a sky-view link |
| `build_heliofleet_link(...)` | A map or sky-view URL for a time, frame, zoom, hidden bodies, surface spot, tab or alignment search |
| `get_data_status()` | Which data release is loaded, where it came from, and each body's span |

### Alignment kinds

| Kind | Condition | Default tolerance |
| --- | --- | --- |
| `radial` | Sun-centred angle between `a` and `b` | 5° |
| `quadrature` | `a` is 90° from Earth seen from the Sun | 5° |
| `conjunction` | `a` behind the Sun seen from Earth, angle from Sun centre | 2° |
| `connection` | Parker-spiral footpoints of `a` and `b`, in longitude | 10° |

Windows are sampled hourly when Parker is involved and every six hours otherwise, as on
HelioFleet's alignment tool, so window edges sit on that grid. `max_windows=1` answers "when is
the next ...".

## HelioField: the coronal magnetic field

On by default (`HELIOFLEET_MCP_PLUGINS=none` turns it off). These tools read
[HelioField](https://sr-dash.github.io/heliofield/)'s daily PFSS products; they do not solve the
field.

| Tool | What it returns |
| --- | --- |
| `get_magnetic_connection(body, date, solar_wind_km_s)` | Where Earth, the L1 fleet, Parker, Solar Orbiter, BepiColombo or STEREO-A connects to the Sun: the Parker-spiral point on the source surface, the PFSS footpoint (Carrington), the expansion factor, distance to the coronal-hole boundary and a WSA-type speed |
| `get_space_weather(date)` | Model wind speed and sector at Earth, the next sector boundary, a −1 to +7 day outlook, an alert level, and that day's solar wind measured at L1 |
| `get_coronal_field(date)` | Magnetogram, PFSS settings, open flux and Earth's L0/B0, plus solar-cycle context per Carrington rotation |
| `build_heliofield_link(...)` | A link to the 3D corona, connectivity, space-weather or observations page |

!!! warning "Model output"

    HelioField results are PFSS model output with indicative WSA-type speeds. They are not
    observations or an official forecast; NOAA SWPC issues those. Daily products cover about the
    last two months; for older dates the tools return links to the page, which computes any date
    since 2010-05-01 in the browser.
