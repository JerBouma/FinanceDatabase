#!/usr/bin/env bash
# Builds financedatabase.mcpb and places it in dist/.
#
# --local: point the bundle's dependency at this local checkout (unpinned,
# editable via uv) instead of the published PyPI package, so uncommitted
# changes can be tested inside the bundle without cutting a release first.
set -euo pipefail

LOCAL=false
for arg in "$@"; do
  case "$arg" in
    --local) LOCAL=true ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUNDLE_DIR="$SCRIPT_DIR"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
OUTPUT_DIR="$REPO_ROOT/dist"

# Read version from the root pyproject.toml — single source of truth.
VERSION=$(python3 -c "
import tomllib
with open('$REPO_ROOT/pyproject.toml', 'rb') as f:
    print(tomllib.load(f)['project']['version'])
")
echo "Version: $VERSION"

OUTPUT_FILE="$OUTPUT_DIR/financedatabase.mcpb"
if [ "$LOCAL" = true ]; then
  OUTPUT_FILE="$OUTPUT_DIR/financedatabase-local.mcpb"
  echo "Local mode: bundling against local checkout ($REPO_ROOT), unpinned + editable"
fi

# Stamp version into pyproject.toml (package version + pinned dependency).
# In --local mode, point the dependency at the local checkout instead
# (via [tool.uv.sources], editable) so the bundle runs uncommitted code.
LOCAL="$LOCAL" REPO_ROOT="$REPO_ROOT" VERSION="$VERSION" python3 -c "
import os, re, pathlib

p = pathlib.Path('$BUNDLE_DIR/pyproject.toml')
content = p.read_text()
content = re.sub(r'(?m)^version = \".*\"', 'version = \"' + os.environ['VERSION'] + '\"', content)

# Strip any leftover [tool.uv.sources] block from a previous --local build.
content = re.sub(r'\n\[tool\.uv\.sources\]\n.*?(?=\n\[|\Z)', '\n', content, flags=re.S)

if os.environ['LOCAL'] == 'true':
    content = re.sub(r'\"financedatabase\[mcp\](==.*)?\"', '\"financedatabase[mcp]\"', content)
    content = content.rstrip('\n') + (
        '\n\n[tool.uv.sources]\n'
        'financedatabase = { path = \"' + os.environ['REPO_ROOT'] + '\", editable = true }\n'
    )
else:
    content = re.sub(r'\"financedatabase\[mcp\](==.*)?\"', '\"financedatabase[mcp]==' + os.environ['VERSION'] + '\"', content)

p.write_text(content)
"

# Regenerate manifest.json from config.yaml — single source of truth.
# Reads asset_classes and utility_tools; stamps version; writes manifest.json.
echo "Syncing manifest.json from config.yaml..."
CONFIG_YAML="$REPO_ROOT/financedatabase/mcp_server/config.yaml" \
MANIFEST_JSON="$BUNDLE_DIR/manifest.json" \
VERSION="$VERSION" \
uv run --with pyyaml --no-project python3 << 'PYEOF'
import json, os, pathlib, yaml

config  = yaml.safe_load(pathlib.Path(os.environ["CONFIG_YAML"]).read_text())
mpath   = pathlib.Path(os.environ["MANIFEST_JSON"])
manifest = json.loads(mpath.read_text())

def _entry(tool):
    return {
        "name": tool["tool_name"],
        "description": tool.get("summary", tool["description"]),
    }

tools  = [_entry(t) for t in config.get("asset_classes", [])]
tools += [_entry(u) for u in config.get("utility_tools", [])]

manifest["version"] = os.environ["VERSION"]
manifest["tools"]   = tools
mpath.write_text(json.dumps(manifest, indent=2) + "\n")
print(f"  {len(tools)} tools written, version {os.environ['VERSION']}.")
PYEOF

mkdir -p "$OUTPUT_DIR"

cd "$BUNDLE_DIR"
mcpb pack .
BUNDLE_FILE=$(ls "$BUNDLE_DIR"/*.mcpb 2>/dev/null | head -1)
mv "$BUNDLE_FILE" "$OUTPUT_FILE"

echo ""
echo "Bundle written to $OUTPUT_FILE"
echo ""
echo "To install: open $OUTPUT_FILE with Claude Desktop."
if [ "$LOCAL" = true ]; then
  echo "This is a local test build (uncommitted code) — do not publish it."
else
  echo "To publish: attach $OUTPUT_FILE to a GitHub release."
fi
