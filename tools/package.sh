#!/bin/sh
# Builds the Decky install zip from the files in this folder (uses the prebuilt dist/index.js; no pnpm needed).
# Usage: sh tools/package.sh [output-dir]      ->  <output-dir>/retroachievements-toasts-<version>.zip
set -e
cd "$(dirname "$0")/.."
OUT="${1:-.}"
VERSION=$(python3 -c "import json;print(json.load(open('plugin.json'))['version'])")
[ -s dist/index.js ] || { echo "dist/index.js missing: run pnpm build (or node tools/build-offline.mjs) first"; exit 1; }
NAME=retroachievements-toasts
STAGE=$(mktemp -d)
mkdir -p "$STAGE/$NAME" "$OUT"
cp -r dist assets main.py plugin.json package.json LICENSE README.md CHANGELOG.md \
      finally_cairo_ctypes.py finally_diagnose.py finally_gamescope_overlay.py "$STAGE/$NAME/"
find "$STAGE" -name __pycache__ -prune -exec rm -rf {} +
find "$STAGE" -name '*.map' -delete
OUTABS=$(cd "$OUT" && pwd)
rm -f "$OUTABS/$NAME-$VERSION.zip"
(cd "$STAGE" && python3 -c "
import os, sys, zipfile
z = zipfile.ZipFile(sys.argv[1], 'w', zipfile.ZIP_DEFLATED)
for root, _d, files in os.walk('$NAME'):
    for f in sorted(files):
        z.write(os.path.join(root, f))
z.close()" "$OUTABS/$NAME-$VERSION.zip")
rm -rf "$STAGE"
echo "$OUTABS/$NAME-$VERSION.zip"
