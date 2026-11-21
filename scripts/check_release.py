"""Release consistency checks for the package and its MCP Registry entry.

  python scripts/check_release.py                  # versions, names, README marker
  python scripts/check_release.py --tag v0.1.0     # also: the tag matches the version
  python scripts/check_release.py --dist dist      # also: built files carry the README marker

Exits non-zero with one line per problem.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tarfile
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME = "io.github.sr-dash/heliofleet-mcp"
REPO = "https://github.com/sr-dash/heliofleet-mcp"


def marker(name: str) -> re.Pattern:
    # The registry requires a boundary after the name: whitespace, a tag or the comment close.
    return re.compile(r"mcp-name:\s*" + re.escape(name) + r"(?=\s|<|-->|$)", re.M)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag")
    ap.add_argument("--dist", type=Path)
    a = ap.parse_args()
    bad: list[str] = []

    init = (ROOT / "src/heliofleet_mcp/__init__.py").read_text()
    version = re.search(r'__version__ = "([^"]+)"', init).group(1)
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        bad.append(f"__version__ {version!r} is not MAJOR.MINOR.PATCH")
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    server = json.loads((ROOT / "server.json").read_text())

    if server.get("name") != NAME:
        bad.append(f"server.json name is {server.get('name')!r}, expected {NAME!r}")
    if server.get("version") != version:
        bad.append(f"server.json version {server.get('version')} != package {version}")
    if len(server.get("description", "")) > 100:
        bad.append("server.json description is longer than 100 characters")
    if server.get("repository", {}).get("url") != REPO:
        bad.append("server.json repository.url does not point at the GitHub repository")
    pkgs = [p for p in server.get("packages", []) if p.get("registryType") == "pypi"]
    if len(pkgs) != 1:
        bad.append("server.json needs exactly one pypi package")
    else:
        p = pkgs[0]
        if p.get("identifier") != project["name"]:
            bad.append(f"package identifier {p.get('identifier')!r} != project name {project['name']!r}")
        if p.get("version") != version:
            bad.append(f"server.json package version {p.get('version')} != {version}")
        if p.get("transport", {}).get("type") != "stdio":
            bad.append("package transport must be stdio")
    if "dynamic" not in project or "version" not in project["dynamic"]:
        bad.append("pyproject.toml should take the version from heliofleet_mcp.__version__")

    cff = re.search(r"^version:\s*(\S+)", (ROOT / "CITATION.cff").read_text(), re.M)
    if not cff or cff.group(1) != version:
        bad.append(f"CITATION.cff version {cff and cff.group(1)} != {version}")
    zen = json.loads((ROOT / ".zenodo.json").read_text())
    if zen.get("version") != version:
        bad.append(f".zenodo.json version {zen.get('version')} != {version}")
    for f in ("AGENTS.md", "llms.txt"):
        if not (ROOT / f).exists():
            bad.append(f"{f} is missing")

    # Skill and plugin manifests: same name and version as the package
    for f in (".claude-plugin/plugin.json", ".cursor-plugin/plugin.json", "plugin.json"):
        m = json.loads((ROOT / f).read_text())
        if m.get("name") != "heliofleet":
            bad.append(f"{f} name {m.get('name')!r} != 'heliofleet'")
        if m.get("version") != version:
            bad.append(f"{f} version {m.get('version')} != {version}")
    mkt = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
    if [p.get("name") for p in mkt.get("plugins", [])] != ["heliofleet"]:
        bad.append(".claude-plugin/marketplace.json should list the heliofleet plugin")
    if "heliofleet" not in json.loads((ROOT / ".mcp.json").read_text()).get("mcpServers", {}):
        bad.append(".mcp.json should define the heliofleet server")
    skill = (ROOT / "skills/heliofleet/SKILL.md").read_text()
    front = re.match(r"---\n(.*?)\n---\n", skill, re.S)
    if not front or not re.search(r"^name: heliofleet$", front.group(1), re.M):
        bad.append("skills/heliofleet/SKILL.md: frontmatter name must be 'heliofleet' (the folder name)")
    elif len(skill.splitlines()) > 500:
        bad.append("skills/heliofleet/SKILL.md is over 500 lines")

    readme = (ROOT / "README.md").read_text()
    if not marker(NAME).search(readme):
        bad.append(f"README.md lacks the line 'mcp-name: {NAME}' (PyPI ownership check)")
    if f"## {version} " not in (ROOT / "CHANGELOG.md").read_text():
        bad.append(f"CHANGELOG.md has no '## {version} ' section")

    if a.tag and a.tag.removeprefix("refs/tags/") != f"v{version}":
        bad.append(f"tag {a.tag} != v{version}")

    if a.dist:
        files = sorted(a.dist.glob("*"))
        wheel = [f for f in files if f.name == f"{project['name'].replace('-', '_')}-{version}-py3-none-any.whl"]
        sdist = [f for f in files if f.name == f"{project['name'].replace('-', '_')}-{version}.tar.gz"]
        if not wheel or not sdist:
            bad.append(f"dist/ should hold the {version} wheel and sdist; found {[f.name for f in files]}")
        for w in wheel:
            with zipfile.ZipFile(w) as z:
                meta = z.read(f"{project['name'].replace('-', '_')}-{version}.dist-info/METADATA").decode()
            if not marker(NAME).search(meta):
                bad.append(f"{w.name}: long description lacks the mcp-name marker")
        for s in sdist:
            with tarfile.open(s) as t:
                names = t.getnames()
            for need in ("README.md", "LICENSE", "pyproject.toml"):
                if not any(n.endswith("/" + need) for n in names):
                    bad.append(f"{s.name} lacks {need}")

    for b in bad:
        print(f"FAIL {b}")
    if not bad:
        print(f"ok {NAME} {version}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
