#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
VERSION="4.5.14"
PLATFORM="linux-x64"
BASE="blender-${VERSION}-${PLATFORM}"
URL="https://download.blender.org/release/Blender4.5/${BASE}.tar.xz"
mkdir -p .cache dist
if [[ ! -f ".cache/${BASE}.tar.xz" ]]; then
  curl --fail --location --retry 3 --output ".cache/${BASE}.tar.xz" "$URL"
fi
curl --fail --location --retry 3 --output ".cache/blender-${VERSION}.sha256" \
  "https://download.blender.org/release/Blender4.5/blender-${VERSION}.sha256"
(
  cd .cache
  grep -F "${BASE}.tar.xz" "blender-${VERSION}.sha256" | sed -E 's@[* ]+blender-@  blender-@' | sha256sum --check -
)
rm -rf ".cache/${BASE}" ".cache/agentic-blender"
tar -xJf ".cache/${BASE}.tar.xz" -C .cache
mv ".cache/${BASE}" ".cache/agentic-blender"
ROOT=".cache/agentic-blender"
mkdir -p "$ROOT/agentic" "$ROOT/4.5/scripts/addons/agentic_blender"
cp blender_addon/agentic_blender/__init__.py "$ROOT/4.5/scripts/addons/agentic_blender/__init__.py"
cp distribution/startup.py "$ROOT/agentic/startup.py"
cp distribution/run-linux.sh "$ROOT/run-agentic-blender.sh"
cp distribution/setup-mcp-linux.sh "$ROOT/setup-mcp.sh"
cp -R agentic_blender "$ROOT/agentic/server"
cp pyproject.toml README.md "$ROOT/agentic/"
chmod +x "$ROOT/run-agentic-blender.sh" "$ROOT/setup-mcp.sh"
tar -cJf "dist/agentic-blender-${VERSION}-linux-x64.tar.xz" -C .cache agentic-blender
echo "Created dist/agentic-blender-${VERSION}-linux-x64.tar.xz"
