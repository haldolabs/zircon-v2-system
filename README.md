# zircon-v2-system

Version 2 of the **agent-environment contract** for an open-source mechanical-engineering benchmark sandbox
(successor to [zircon-v1-system](https://github.com/haldolabs/zircon-v1-system)). Still written in the style of a
`CLAUDE.md`: what is on the machine, which Python to use, which tools the agent may modify and how, verifier recipes
that were actually run, and the one rule that has no exceptions: nothing leaves the machine during a task.

**[Read ZIRCON_V2_SYSTEM.md](ZIRCON_V2_SYSTEM.md)** — §0–§8 are the v1 contract unchanged; §9–§10 are what two full
exercises added.

## What is new in v2
| | |
|---|---|
| `ZIRCON_V2_SYSTEM.md` §9 | tools verified after the first exercise: **CAMotics** (3D material-removal simulation), **Blender** and **POV-Ray** renders, osifont, a GD&T glyph library, and seven lessons that became rules |
| `ZIRCON_V2_SYSTEM.md` §10 | tools and rules from the second exercise: a **machinability gate** on the CAD profile, a **force-loop FEA runner**, a derived-toolpath G-code generator with an 8-check test rig, FEA-deformed STL export for renders, six more rules |
| [`tool_library/`](tool_library/README.md) | an **offline cutting-tool collection**: 148,412 tools from 33 vendors (RobbJack ISO 13399 catalog, 45 Autodesk-hosted vendor libraries, Pocket NC), merged into one normalized ISO 13399-named table, plus **FreeCAD 1.0 CAM tool libraries**: `freecad/basics`, a pared-down 114-tool shop standard (end mills with reach tiers, balls, chamfers, single-profile thread mills, taps 1-72 … 1/2-20 + M1.6 … M12 and their tap / clearance drills; every solid geometry-verified, start there) and two large exports (1,807 + 7,371 bits, load-verified; two known geometry bugs noted in the README) and 1,631 holders as STEP. Raw files committed xz-compressed (19 MB) with a SHA-256 manifest; `fetch.sh` re-downloads them |
| [`tools/`](tools/README.md) | the verified helpers an agent can copy: CAMotics check, POV-Ray / Blender renderers, GD&T glyphs, site builder, a VF-2 travel model for `rs274` |
| [`examples/saft_v2/`](examples/saft_v2/REPORT.md) | the second exercise end to end — a one-piece index-card keeper: brainstorm, parametric FreeCAD CAD with a machinability proof, Gmsh + CalculiX FEA (v1 → v2), A3 release drawing with GD&T + DXF + RFQ, shop quote, one-setup G-code with its test rig, the STEP, the PDF and the program. Every script that produced a number is included |

It remains a thought experiment for demonstrative purposes. Versions and gotchas were verified on a real workstation
in October 2026; the source-checkout layout it describes is intended, not present. No live host is described.
The tool library was fetched by the owner's instruction *outside* a benchmark run; the contract's no-network rule
for agents during a task is unchanged.
