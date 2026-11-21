"""Every public function, class and method of the Python API has a numpydoc docstring with examples.

The MCP tool functions in server.py and heliofield.register are left out: their docstrings are the
tool descriptions that MCP clients show. ruff (pydocstyle, numpy convention) checks the format;
this test checks that the sections the PyHC standards ask for are there. The examples themselves
run as doctests (``--doctest-modules`` in pyproject.toml).
"""

import importlib
import inspect

import pytest

MODULES = ["frames", "timeutil", "catalog", "links", "data", "geometry", "heliofield", "cli"]


def _public(mod):
    for name, obj in vars(mod).items():
        if name.startswith("_") or getattr(obj, "__module__", None) != mod.__name__:
            continue
        if inspect.isfunction(obj) or inspect.isclass(obj):
            yield name, obj


def _members():
    for m in MODULES:
        mod = importlib.import_module(f"heliofleet_mcp.{m}")
        assert inspect.getdoc(mod), f"{m}: module docstring"
        for name, obj in _public(mod):
            yield f"{m}.{name}", obj, inspect.isclass(obj)
            if inspect.isclass(obj):
                for mname, member in vars(obj).items():
                    if mname.startswith("_"):
                        continue
                    if inspect.isfunction(member) or isinstance(member, property):
                        yield f"{m}.{name}.{mname}", member, False


def _params(obj):
    fn = obj.fget if isinstance(obj, property) else obj
    return [p for p in inspect.signature(fn).parameters if p not in ("self", "cls")]


CASES = list(_members())


@pytest.mark.parametrize("qualname,obj,is_class", CASES, ids=[c[0] for c in CASES])
def test_numpydoc_sections(qualname, obj, is_class):
    doc = inspect.getdoc(obj.fget if isinstance(obj, property) else obj)
    assert doc, f"{qualname} has no docstring"
    if is_class and issubclass(obj, Exception):
        return
    assert "Examples\n--------" in doc, f"{qualname}: no Examples section"
    if is_class:
        if _params(obj.__init__):
            assert "Parameters\n----------" in doc, f"{qualname}: constructor parameters undocumented"
        return
    if _params(obj):
        assert "Parameters\n----------" in doc, f"{qualname}: no Parameters section"
    assert "Returns\n-------" in doc, f"{qualname}: no Returns section"


def test_covers_the_public_api():
    names = {c[0] for c in CASES}
    for expected in ("geometry.Fleet.find_alignments", "heliofield.HelioField.magnetic_connection",
                     "data.Store.position", "frames.heliographic", "timeutil.parse_time", "cli.main"):
        assert expected in names
