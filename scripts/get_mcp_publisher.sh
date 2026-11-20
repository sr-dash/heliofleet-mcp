#!/usr/bin/env bash
# Download a pinned mcp-publisher release and verify its Sigstore bundle before extracting it.
# Usage: scripts/get_mcp_publisher.sh [version]   (needs curl and cosign)
set -euo pipefail
version="${1:-${MCP_PUBLISHER_VERSION:-v1.8.9}}"
os="$(uname -s | tr '[:upper:]' '[:lower:]')"
arch="$(uname -m | sed 's/x86_64/amd64/;s/aarch64/arm64/')"
archive="mcp-publisher_${os}_${arch}.tar.gz"
base="https://github.com/modelcontextprotocol/registry/releases/download/${version}"
curl --fail --location --silent --show-error --output "$archive" "$base/$archive"
curl --fail --location --silent --show-error --output "$archive.sigstore.json" "$base/$archive.sigstore.json"
cosign verify-blob \
  --bundle "$archive.sigstore.json" \
  --certificate-identity "https://github.com/modelcontextprotocol/registry/.github/workflows/release.yml@refs/tags/${version}" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  "$archive"
tar xzf "$archive" mcp-publisher
rm -f "$archive" "$archive.sigstore.json"
./mcp-publisher --version || true
