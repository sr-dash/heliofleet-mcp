---
description: "Install the heliofleet Agent Skill so any assistant that reads Agent Skills answers spacecraft-geometry questions with the heliofleet-mcp command line, no MCP set-up needed."
---

# Skill and plugins

The repository ships an [Agent Skill](https://agentskills.io):
[`skills/heliofleet/SKILL.md`](https://github.com/sr-dash/heliofleet-mcp/blob/main/skills/heliofleet/SKILL.md).
It tells an assistant which `heliofleet-mcp` command answers which question (positions, alignments,
quadratures, conjunctions, viewing geometry, events, magnetic connectivity) and the rules for
reporting the result: UTC times at the sampling resolution, the Stonyhurst sign, spacecraft status
and model caveats, always with the HelioFleet or HelioField link.

It needs only a shell with `uvx` (or the package installed). No MCP server or client configuration
is involved, so it works wherever the assistant can run commands.

## Install the skill

=== "With the skills CLI"

    ```bash
    npx skills add sr-dash/heliofleet-mcp
    ```

    The [skills CLI](https://skills.sh) detects the assistants installed on the machine and copies
    the skill into each one's skills folder.

=== "By hand"

    Copy the `skills/heliofleet` folder into the skills folder your assistant reads, for a single
    project (for example `.agents/skills/` in the repository) or for every project (for example
    `~/.agents/skills/`).

Then ask, for example, "When is STEREO-A next in quadrature with Earth?"; the assistant runs
`uvx heliofleet-mcp align sta --kind quadrature --next --compact` and answers from the JSON.

## Plugins

For assistants with plugin systems, the repository also carries plugin manifests that bundle the
skill with the MCP server: an [Agent Plugins](https://agent-plugins.org) `plugin.json` at the root
(skill only) and client-specific manifests in `.claude-plugin/` (which also makes the repository a
plugin marketplace) and `.cursor-plugin/`. Install commands for each client are in the
[README](https://github.com/sr-dash/heliofleet-mcp#skill-and-plugins).

CI validates the skill with the Agent Skills reference validator and the Agent Plugins manifest
against its schema on each push.
