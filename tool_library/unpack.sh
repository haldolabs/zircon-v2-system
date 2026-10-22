#!/usr/bin/env bash
# Decompress the committed .xz copies in place (raw/**.json.xz → .json etc.) so collection.py / catalog.py can read them.
set -euo pipefail; cd "$(dirname "$0")"
find raw -name "*.xz" -print0 | xargs -0 -n1 -P8 xz -dk -f
[ -f collection.csv.xz ] && xz -dk -f collection.csv.xz; [ -f holders.json.xz ] && xz -dk -f holders.json.xz
echo "unpacked; verify with: (cd raw && sha256sum -c ../MANIFEST.sha256 2>/dev/null | grep -c OK)"
