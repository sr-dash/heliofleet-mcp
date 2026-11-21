"""``python -m heliofleet_mcp``: the same as the ``heliofleet-mcp`` command."""

import sys

from .cli import main

sys.exit(main())
