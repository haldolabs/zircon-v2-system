# tool_library — an offline, vendor-neutral cutting-tool collection (148,412 tools, 33 vendors)

A one-time download of public vendor tool data, merged into one normalized table with ISO 13399 field names, plus
ready-made **FreeCAD 1.0 CAM tool libraries** generated from it. Everything is on disk; nothing needs the cloud again.
Assembled 2026-10-22.

```
raw/           the vendor files as downloaded, xz-compressed (19 MB; 590 MB unpacked) + MANIFEST.sha256 of the originals
collection.py  merge every raw file → collection.csv/.json (148,412 rows), summary.md, FreeCAD libraries, holders.json
catalog.py     query the RobbJack ISO 13399 catalog on its own; export single FreeCAD .fctb bits
holders_export.py  holders.json → revolved STEP solids (freecadcmd)
freecad/       V3_starter_quarter_eighth (1,807 bits) and V3_chamfer_tap_threadmill (7,371 bits): Bit/ + Library/*.fctl
collection.csv.xz, holders.json.xz   prebuilt outputs
fetch.sh / unpack.sh                 re-download from the original URLs / decompress the committed copies
```

## Sources and terms
| Source | What | Tools | Terms |
|---|---|---|---|
| RobbJack master catalog, schema 1.1, 2026-10-13 — https://www.robbjack.com/downloads/master-catalog | **ISO 13399-coded** JSON + CSV (DC, DCX, DMM, APMX, OAL, RE, ND, LN, NOF, FHA, KCH …) in inches and mm, STEP/DXF link templates, SHA-256 manifest | 7,106 | "free to import into CAM/CAD/tool-management systems and to redistribute unmodified with attribution to RobbJack Corporation" |
| RobbJack Fusion library — https://robbjack.com/downloads/fusion-360 | Fusion `.tools` with 12,310 cutting presets | 6,746 | same |
| Autodesk CAM tool-library index — https://cam.autodesk.com/hsmtools (index JSON at `tools/tools/tools.json`, files at `tools/download.php?name=<path>`) | raw Fusion `tools.json` for 45 vendor libraries (Harvey Tool, Helical, Haas, Sandvik Coromant, ISCAR, Mitsubishi, OSG, Garr, Guhring, IMCO, Kyocera SGS, SwiftCARB, DATRON, Destiny, Delta, M.A. Ford, NexGen, Valor, Bits & Bits, Fraiser, XEBEC, Haimer, Schunk, Renishaw, Blum, Tormach, Kennametal turning); 7 index entries fail on Autodesk's server and are listed in `raw/autodesk/unavailable_2026-10-22.txt` | 133,000+ | Autodesk's free vendor directory; each record carries its vendor name and product link |
| Autodesk Tooling JSON Schema (2026-08) | `FusionToolLibrarySchemas.html`, Excel notes, sample 3D turning holder | — | reference |
| Pocket NC / Penta Machine wiki attachments | three small Fusion `.tools` starter libraries | 62 | public wiki attachments |

**Carbide 3D** is not included: its libraries are not published as files. Treat every row as vendor data: check geometry
and cutting data against the product page before cutting.

## Get started
```bash
./unpack.sh                               # or ./fetch.sh to re-download the originals into raw/
python3 collection.py                     # ~1 min, stdlib only → collection.csv/json, summary.md, freecad/*, holders.json
python3 collection.py --full              # also one FreeCAD library per vendor with every exportable tool (~125k bits)
python3 catalog.py find --dia 0.125 --flutes 2 --loc-min 0.6     # RobbJack ISO catalog queries
QT_QPA_PLATFORM=offscreen freecadcmd holders_export.py           # 1,630 holder STEP solids (58 MB, not committed)
```

## The normalized table
`collection.csv` columns: `vendor, library, tool_id, type, description, unit, DC, DMM, APMX, OAL, LB, NOF, RE, ND, LN, TA,
BMC, coating, n_presets, has_3d, product_link, guid, source_file, DC_mm, DMM_mm, APMX_mm, OAL_mm, RE_mm`.
Fusion geometry keys map DC→DC, SFDM→DMM, LCF→APMX, OAL→OAL, LB→LB, NOF→NOF, RE→RE, shoulder-length→ND, TA→TA.
139,663 rows carry cutting presets (per-material rpm/feed tables in the raw Fusion records); 7,061 flag a 3D model.

## FreeCAD 1.0 Tool Bit Library manager
FreeCAD reads only its own `.fctb` bits and `.fctl` lists — no Fusion or ISO 13399 import — so `collection.py` writes
libraries laid out like FreeCAD's `Tools/` folder. Copy FreeCAD's stock `Tools/Shape/*.fcstd` next to them (or point
the manager at a folder that has it) and open the `.fctl`:

| Library | Bits | Content | Verified |
|---|---|---|---|
| `freecad/V3_starter_quarter_eighth` | 1,807 | every 1/4 in and 1/8 in flat / ball / bull-nose end mill and drill with ≥ 19 mm (1/4) or ≥ 16 mm (1/8) flute length | every bit loads in `freecadcmd` via `Path.Tool.Bit.Factory.CreateFrom` and builds a valid solid |
| `freecad/V3_chamfer_tap_threadmill` | 7,371 | all chamfer mills (2,202), taps (2,676), thread mills (176), dovetail mills (625), spot / centre drills and countersinks (1,695) | all 7,371 load, 0 failures (501 s) |

Shape mapping: endmill / ballend / bullnose (`FlatRadius` = DC/2 − RE) / drill (`TipAngle` from the record, else 118°) /
chamfer (`CuttingEdgeAngle` = 2 × Fusion's per-side TA, `TipDiameter`) / thread-mill / dovetail. **Taps use FreeCAD's
thread-mill shape** (FreeCAD 1.0 has no tap shape): the envelope is right, the pitch is kept in `attribute.tap_pitch_mm`
and the bit says so in `attribute.note`. **Holders** have no FreeCAD bit type; `holders.json` keeps every holder's
segment stack in mm and `holders_export.py` revolves them into STEP solids for collision checks. `Chipload` is left 0:
the vendor presets belong in a ToolController, not on the bit. The ISO 13399 record, vendor, library and product link
ride along under `attribute` on every bit.
