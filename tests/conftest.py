import os
from pathlib import Path

import pytest

from heliofleet_mcp.data import Store, _default_local
from heliofleet_mcp.geometry import Fleet

DATA = Path(__file__).parent / "data"


def local_checkout():
    p = _default_local()
    return p if p and (p / "manifest.json").exists() else None


@pytest.fixture(scope="session")
def fleet(tmp_path_factory):
    """Fleet on a local heliofleet checkout when present (offline, reproducible), else the site."""
    local = local_checkout()
    if local and os.environ.get("HELIOFLEET_TEST_SOURCE", "local") == "local":
        return Fleet(Store(source="local", local=local))
    return Fleet(Store(source="web", cache=tmp_path_factory.mktemp("cache")))
