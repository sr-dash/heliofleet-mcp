# Changelog

## 0.1.2 (2026-11-20)

- Package metadata only, no code changes: more PyPI and Zenodo keywords (missions, coordinate
  systems, alignment kinds, PFSS), so searches for those terms find the package.
- The PyPI page picks up the current README: demo GIF, citation with the Zenodo DOI, and the
  command-line and assistant sections.
- `glama.json` names the maintainer for the Glama directory.

## 0.1.1 (2026-11-20)

- Command line: `heliofleet-mcp <command>` answers one question and prints the tool's JSON
  (`align`, `position`, `fleet`, `events`, `geometry`, `link`, `status`, `connection`,
  `spaceweather`, `field`). With no command it still serves MCP over stdio.
- Python API: `from heliofleet_mcp import Fleet, HelioField`.
- `AGENTS.md` and `llms.txt` describe how assistants can use the package with or without MCP.
- Citation: `CITATION.cff`, `.zenodo.json` and a Zenodo DOI badge.
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
