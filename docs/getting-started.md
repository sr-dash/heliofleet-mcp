---
description: "Install heliofleet-mcp with uvx or pip, connect it to any MCP client with one mcpServers entry, and set the data source, cache and plugins with environment variables."
---

# Getting started

## Run it

With [uv](https://docs.astral.sh/uv/) installed, one command downloads and starts the server:

```bash
uvx heliofleet-mcp
```

It speaks the Model Context Protocol over stdio, so on its own it waits silently for a client. The
same program also answers single questions from the [command line](command-line.md).

!!! tip "Without uv"

    ```bash
    pipx install heliofleet-mcp      # or: pip install heliofleet-mcp
    heliofleet-mcp                   # or: python -m heliofleet_mcp
    ```

    Python 3.10 or newer. The only runtime dependency is the `mcp` Python SDK (1.x or 2.x).

## Connect an MCP client

Most clients read an `mcpServers` entry from their configuration file, or from `.mcp.json` in a
project:

```json
{
  "mcpServers": {
    "heliofleet": {
      "command": "uvx",
      "args": ["heliofleet-mcp"]
    }
  }
}
```

Clients with a command line usually have an `mcp add` command that writes the same entry:

```bash
<client> mcp add heliofleet -- uvx heliofleet-mcp
```

Registry-aware clients and directories find it in the
[official MCP Registry](https://registry.modelcontextprotocol.io) as
`io.github.sr-dash/heliofleet-mcp`. Step-by-step set-up for specific desktop and command-line
clients is in the
[README](https://github.com/sr-dash/heliofleet-mcp#quick-start).

Then ask, for example:

- "When are Parker and Solar Orbiter next radially aligned?"
- "What is Solar Orbiter's B0 and L0 right now, and how big does the Sun look from there?"
- "Which spacecraft are in quadrature with Earth next spring?"
- "Where does Parker connect magnetically to the Sun today?"

## Settings

All settings are environment variables, which an MCP client entry can set with `"env": {...}`.

| Variable | Default | Meaning |
| --- | --- | --- |
| `HELIOFLEET_SOURCE` | `auto` | `auto` (site, then cache, then local), `web`, or `local` |
| `HELIOFLEET_LOCAL_DATA` | sibling `heliofleet/data` | a local HelioFleet data folder |
| `HELIOFLEET_CACHE` | `~/.cache/heliofleet-mcp` | cache folder |
| `HELIOFLEET_SITE` | `https://sr-dash.github.io/heliofleet/` | HelioFleet site root |
| `HELIOFLEET_MCP_PLUGINS` | `heliofield` | optional tool sets, or `none` |
| `HELIOFIELD_SITE` | `https://sr-dash.github.io/heliofield/` | HelioField site root |
| `HELIOFIELD_LOCAL` | sibling `heliofield` | a local HelioField checkout |

??? example "Working offline from a HelioFleet checkout"

    ```json
    {
      "mcpServers": {
        "heliofleet": {
          "command": "uvx",
          "args": ["heliofleet-mcp"],
          "env": {
            "HELIOFLEET_SOURCE": "local",
            "HELIOFLEET_LOCAL_DATA": "/path/to/heliofleet/data"
          }
        }
      }
    }
    ```

## Bodies and times

Bodies: `earth sdo soho aditya ace wind dscovr imap swfo cgo solo psp bepi sta stb maven mercury
venus mars`. Common names also work, such as "Parker", "Solar Orbiter" and "STEREO-A".

Times are UTC: ISO 8601 (`2026-11-19T12:00Z`, `2026-11-19`), `now`, or a Julian date.

## For assistants and automated tools

[`AGENTS.md`](https://github.com/sr-dash/heliofleet-mcp/blob/main/AGENTS.md) explains how to answer
questions with this package in any environment (MCP, shell commands, Python, or plain web fetches
of the published data) and the conventions to keep: UTC times, the Stonyhurst sign, the alignment
sampling grid, spacecraft status values and model caveats.
[`llms.txt`](https://github.com/sr-dash/heliofleet-mcp/blob/main/llms.txt) is the short index.
