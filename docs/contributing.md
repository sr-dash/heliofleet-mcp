---
description: "Report a wrong number, share what you used heliofleet-mcp for, or contribute code: development set-up, tests, doctests, style checks and the code of conduct."
---

# Contributing

Reports, ideas and pull requests are welcome. Please follow the
[code of conduct](https://github.com/sr-dash/heliofleet-mcp/blob/main/CODE_OF_CONDUCT.md)
(Contributor Covenant 2.1).

- **A number looks wrong?** Open an [issue](https://github.com/sr-dash/heliofleet-mcp/issues) with
  the command or tool call and its output; the `link` in it helps.
- **Used it for something?** Share it in
  [Show and tell](https://github.com/sr-dash/heliofleet-mcp/discussions/1).
- **Want to change the code?** Read
  [CONTRIBUTING.md](https://github.com/sr-dash/heliofleet-mcp/blob/main/CONTRIBUTING.md): set-up,
  tests, style, and when a contribution is not accepted.

## Development

```bash
git clone https://github.com/sr-dash/heliofleet-mcp && cd heliofleet-mcp
python3 -m venv .venv && .venv/bin/pip install -e '.[test,lint,docs]' jplephem
.venv/bin/python -m pytest -q --cov        # tests and doctests
.venv/bin/ruff check src tests scripts     # PEP 8 and docstrings
.venv/bin/mkdocs serve                     # this site, at http://127.0.0.1:8000
```

CI runs the tests on Linux (Python 3.10 to 3.14), macOS and Windows, reports coverage and checks
the style. This site is rebuilt from `docs/` and the docstrings on every push to `main`.
