# Changelog

## Unreleased

- README: badges, and where the package is published (PyPI, MCP Registry, GitHub releases).
- Package classifiers for Python 3.10 to 3.13.

## 0.1.0 (2026-11-20)

First release.

- Tools on HelioFleet data: `get_position`, `get_fleet_state`, `find_alignments` (radial,
  quadrature, conjunction, connection), `list_upcoming_events`, `viewing_geometry`,
  `heliofleet_link` and `data_status`. Every result carries a link that reproduces the view.
- HelioField plugin: `magnetic_connection`, `space_weather`, `coronal_field` and `heliofield_link`.
- Stonyhurst and Carrington coordinates agree with SunPy to 0.0004° (limit 0.005°). Alignment
  windows are identical to HelioFleet's page code.
- Data are read from the public sites with a local cache, or from local checkouts offline.
