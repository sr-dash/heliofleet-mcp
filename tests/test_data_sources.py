"""Site fetch with cache, and fallback to a local checkout when the site is unreachable."""

import pytest

from heliofleet_mcp.data import Store, _default_local
from heliofleet_mcp.geometry import Fleet


@pytest.mark.network
def test_site_and_cache(tmp_path):
    store = Store(source="web", cache=tmp_path)
    try:
        store.manifest()
    except Exception as err:
        pytest.skip(f"site unreachable: {err}")
    f = Fleet(store)
    row = f.position("psp", "2025-03-22T22:25Z")
    assert row["status"] == "ok"
    assert (tmp_path / "manifest.json").exists()
    assert list(tmp_path.glob("*/data/psp/2025.json"))
    assert store.origin == "site"


def test_fallback_to_local(tmp_path):
    local = _default_local()
    if not local:
        pytest.skip("no local heliofleet checkout")
    store = Store(source="auto", local=local, cache=tmp_path, site="http://127.0.0.1:9/", timeout=1)
    row = Fleet(store).position("solo", "2026-11-19")
    assert row["status"] == "ok"
    assert store.origin.startswith("local")
