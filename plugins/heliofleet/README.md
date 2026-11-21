# HelioFleet plugin

A skill that answers questions about heliophysics spacecraft geometry from JPL Horizons ephemerides:
where Parker Solar Probe, Solar Orbiter, STEREO-A and the rest of the fleet are, when two of them
line up (radial alignment, quadrature, solar conjunction, magnetic connection), what each sees of the
Sun (B0, L0, apparent solar radius, light time), upcoming perihelia, and where each connects
magnetically to the Sun (PFSS footpoints, space-weather outlook).

The skill uses the open-source `heliofleet-mcp` command line, which prints JSON with a HelioFleet or
HelioField link for every answer. Install it by following the getting-started guide:
https://sr-dash.github.io/heliofleet-mcp/getting-started/

## Data and network use

- The command line downloads public, read-only data files from https://sr-dash.github.io/heliofleet/
  (JPL Horizons ephemerides and an event calendar) and https://sr-dash.github.io/heliofield/ (PFSS
  model products), and caches them on your computer.
- It sends no personal data, no conversation content and no credentials: the only requests are
  ordinary downloads of those static files. Nothing is retained on any server.

- Documentation: https://sr-dash.github.io/heliofleet-mcp/
- Source and issues: https://github.com/sr-dash/heliofleet-mcp
- Licence: MIT
- Author: Soumyaranjan Dash, National Solar Observatory
