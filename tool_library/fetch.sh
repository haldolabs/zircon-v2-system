#!/usr/bin/env bash
# Re-download every raw vendor file in this library from its original public URL (for a refresh, or if you prefer
# fetching to unpacking the .xz copies committed here). Writes into raw/ next to this script. Needs curl + xz.
# Sources (all free, no sign-up, 2026-10-22):
#   RobbJack master catalog (ISO 13399)  https://www.robbjack.com/downloads/master-catalog
#   RobbJack Fusion library              https://robbjack.com/downloads/fusion-360
#   Autodesk CAM tool-library index      https://cam.autodesk.com/hsmtools  → https://cam.autodesk.com/tools/tools/tools.json
#                                        each entry: https://cam.autodesk.com/tools/download.php?name=<path>
#   Pocket NC / Penta Machine libraries  https://pentamachine.atlassian.net/wiki/spaces/PNFUR/pages/369131625
set -euo pipefail
cd "$(dirname "$0")/raw"
echo "== RobbJack"
for u in https://robbjack.com/data/robbjack-master-catalog.json https://robbjack.com/data/robbjack-master-catalog.csv \
         https://robbjack.com/data/robbjack-master-catalog.manifest.json https://robbjack.com/data/cam/robbjack-fusion360.tools; do
  curl -sSL -o "robbjack/$(basename "$u")" "$u" && echo "  $(basename "$u")"
done
echo "== Autodesk vendor index"
curl -sSL -o autodesk/tools_index.json "https://cam.autodesk.com/tools/tools/tools.json"
curl -sSL -o autodesk/Tooling_JSON_Schema.zip "https://cam.autodesk.com/tools/tools/Tooling%20Schema/JSON%20Schema.zip"
mkdir -p autodesk/fusion
grep -oE '"path": *"[^"]*"' autodesk/tools_index.json | sed 's/"path": *"//; s/"$//' | while IFS= read -r p; do
  f="autodesk/fusion/$(echo "$p" | tr '/ ' '__').json"
  curl -sSL -G --data-urlencode "name=$p" -o "$f" "https://cam.autodesk.com/tools/download.php"
  if [ "$(stat -c %s "$f")" -lt 1000 ]; then echo "  UNAVAILABLE $p: $(cat "$f")"; rm -f "$f"; else echo "  $p ($(stat -c %s "$f") bytes)"; fi
done
echo "== Pocket NC"
B=https://pentamachine.atlassian.net/wiki/rest/api/content/369131625/child/attachment
curl -sSL -o pocketnc/PentaMachine_Tool_Library_RevC.tools        "$B/att1852899332/download"
curl -sSL -o pocketnc/PocketNC_Tool_Library_for_Fusion360.tools   "$B/att1591935024/download"
curl -sSL -o pocketnc/PocketNC_Tool_Library.tools                 "$B/att452034589/download"
echo "done — now: python3 ../collection.py   (expects raw/autodesk/fusion/*.json, raw/robbjack/*, raw/pocketnc/*)"
