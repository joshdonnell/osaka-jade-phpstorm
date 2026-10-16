#!/bin/bash

# Regenerates the Osaka Jade theme, packs it into a plugin jar and installs it
# into the newest PhpStorm Light (EAP) config folder, falling back to PhpStorm.
#   ./build.sh               build and install
#   ./build.sh --no-install  only build dist/osaka-jade-theme.jar
#
# Without PhpStorm installed, the committed files in src/themes are packed as they are.

set -e

cd "$(dirname "$0")"

if [ -n "$IDE_APP" ] || compgen -G "$HOME/Applications/PhpStorm*.app" >/dev/null || compgen -G "/Applications/PhpStorm*.app" >/dev/null; then
  python3 generate.py "$IDE_APP"
else
  echo "No PhpStorm found, packing the committed theme files."
fi

rm -rf dist
mkdir -p dist
(cd src && zip -qr ../dist/osaka-jade-theme.jar META-INF themes)
echo "Built dist/osaka-jade-theme.jar"

[ "$1" = "--no-install" ] && exit 0

IDE_DIR=$(ls -d "$HOME/Library/Application Support/JetBrains/PhpStormLight20"* 2>/dev/null | sort -V | tail -1)
[ -z "$IDE_DIR" ] && IDE_DIR=$(ls -d "$HOME/Library/Application Support/JetBrains/PhpStorm20"* 2>/dev/null | sort -V | tail -1)

if [ -z "$IDE_DIR" ]; then
  echo "No PhpStorm config folder found. Open PhpStorm once first."
  exit 1
fi

mkdir -p "$IDE_DIR/plugins"
# Swap the jar in with a rename, so a running PhpStorm keeps reading the old file.
cp dist/osaka-jade-theme.jar "$IDE_DIR/plugins/.osaka-jade-theme.jar.tmp"
mv "$IDE_DIR/plugins/.osaka-jade-theme.jar.tmp" "$IDE_DIR/plugins/osaka-jade-theme.jar"
echo "Installed into $IDE_DIR/plugins. Restart PhpStorm, then pick Osaka Jade under Settings, Appearance, Theme."
