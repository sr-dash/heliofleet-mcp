---
description: "Privacy policy for heliofleet-mcp, its skill and plugins, and this documentation site: what is collected (nothing by the tools), what is downloaded, and what the website measures."
---

# Privacy

*Last updated: 21 November 2026*

This policy covers the heliofleet-mcp software (the MCP server, the command line, the Python
package, the `heliofleet` skill and the plugins built from this repository) and this documentation
website.

## The software collects nothing

heliofleet-mcp runs on your own computer. It has no accounts, no telemetry and no analytics, and it
does not ask for or use personal data, credentials or API keys.

- **What it downloads.** To answer a question it downloads public, read-only data files over HTTPS:
  ephemerides and an event calendar from [HelioFleet](https://sr-dash.github.io/heliofleet/), and
  coronal-field products from [HelioField](https://sr-dash.github.io/heliofield/). These are ordinary
  downloads of static files; your questions, conversation content and results are not sent anywhere.
  Which files are fetched (for example, one year of a spacecraft's positions) follows from the dates
  you ask about.
- **What it stores.** Downloaded files are cached on your computer, by default in
  `~/.cache/heliofleet-mcp` (set `HELIOFLEET_CACHE` to change it). Delete that folder to remove them.
  Nothing is stored anywhere else.
- **No server of ours receives your data.** The data files are served by GitHub Pages. GitHub
  handles those requests as a hosting provider and may log technical information such as IP
  addresses, as described in the
  [GitHub Privacy Statement](https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement).
  The author does not receive these logs.
- **Installing it.** Installing the package from PyPI, or through tools such as uv or pip, involves
  those services and their own privacy policies.

When you use the skill or the MCP server through an assistant, the assistant's provider handles
your conversation under its own privacy policy; heliofleet-mcp only returns JSON to the assistant on
your computer.

## This documentation website

This site (sr-dash.github.io/heliofleet-mcp) is hosted on GitHub Pages and uses Google Analytics to
count page views and understand which pages are useful, including the optional "Was this page
helpful?" buttons. Google Analytics uses cookies and processes information such as your IP address,
browser and pages visited, under
[Google's Privacy Policy](https://policies.google.com/privacy). You can block it with your
browser's privacy settings or an extension; the site works without it. The site does not use
analytics data to identify you, does not sell it, and collects nothing else.

## Children

heliofleet-mcp is a research tool and is not directed at children under 13.

## Changes and contact

Changes to this policy are recorded in the repository's history and in the date above. Questions:
open an [issue](https://github.com/sr-dash/heliofleet-mcp/issues), or write to the maintainer,
Soumyaranjan Dash, at <sdash@nso.edu>.
