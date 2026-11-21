# Contributing to heliofleet-mcp

Thank you for helping. Reports, ideas and code are all welcome. Everyone taking part is asked to
follow the [code of conduct](CODE_OF_CONDUCT.md).

## Ways to help

- **Report a number that looks wrong.** A position, angle, alignment window or footpoint that
  disagrees with JPL Horizons, SunPy or HelioFleet's page is the most valuable report there is.
  Open an [issue](https://github.com/sr-dash/heliofleet-mcp/issues) with the command or tool call,
  its output (the `link` in it helps), and what you expected.
- **Suggest a feature or a new tool** in an issue. Say what question it would answer.
- **Share what you used it for** in [Show and tell](https://github.com/sr-dash/heliofleet-mcp/discussions/1).
- **Send a pull request** for a fix or a feature. For anything larger than a small fix, please open
  an issue first, so we can agree on the approach before you spend time on it.

Missing spacecraft, wrong ephemerides and page problems belong to
[HelioFleet](https://github.com/sr-dash/heliofleet/issues); coronal-field products belong to
[HelioField](https://github.com/sr-dash/heliofield/issues). This package reads their published data.

## When a contribution is not accepted

To keep the package small and its numbers identical to HelioFleet's and HelioField's pages, pull
requests are not merged when they:

- change the geometry or alignment results without the same change in HelioFleet's page code, or
  without updating the comparison tests and saying why;
- add a computation that belongs in HelioFleet or HelioField (new ephemerides, models or data
  products); propose those there instead;
- add a runtime dependency that the change does not clearly need (the package depends only on `mcp`);
- break a tool's or command's output format without a version bump and a changelog entry;
- lack tests for new behaviour, or fail the tests or the lint check;
- add large binary files or notebooks to the repository.

## Development setup

```bash
git clone https://github.com/sr-dash/heliofleet-mcp
cd heliofleet-mcp
python3 -m venv .venv
.venv/bin/pip install -e '.[test,lint,docs]' jplephem
```

Run the tests and the lint check before opening a pull request:

```bash
.venv/bin/python -m pytest -q --cov
.venv/bin/ruff check src tests scripts
```

The tests compare positions and angles with SunPy (and through it JPL Horizons) and the alignment
windows with HelioFleet's own JavaScript. They use local `heliofleet/` and `heliofield/` checkouts
next to this one when present; set `HELIOFLEET_TEST_SOURCE=web` to use the live sites instead, as CI
does. CI runs them on Linux (Python 3.10 to 3.14), macOS and Windows.

## Code style

- PEP 8, checked with ruff (pycodestyle and pyflakes rules, 120-character lines; settings in
  `pyproject.toml`).
- Public functions, classes and methods get a numpydoc docstring with Parameters, Returns and
  Examples sections; ruff checks the format and `tests/test_docstrings.py` checks the sections.
  Examples run as doctests, so give them stable output (fixed past dates, rounded numbers). The
  [API reference](https://sr-dash.github.io/heliofleet-mcp/) is built from these docstrings and the pages in `docs/`
  by the `docs` workflow (MkDocs Material); preview it with `mkdocs serve`.
- The docstrings of the MCP tools (in `server.py` and `heliofield.register`) are the descriptions
  MCP clients show; keep them as plain prose for clients, not numpydoc.
- Times are UTC; angles are degrees; distances are au unless the name says otherwise.
- Keep the MCP tools, the command line and the Python API in step: they return the same JSON.

## Commits, pull requests and releases

- One topic per pull request, with a short description of what changed and why.
- Commit messages in the imperative, brief.
- Pull requests are reviewed by the maintainer. Contributions are released under the project's
  [MIT licence](LICENSE).
- Releases follow semantic versioning (0.x while the interface may still change) and are published
  to PyPI, the MCP Registry and Zenodo by the release workflow; see "Releasing" in the README.
