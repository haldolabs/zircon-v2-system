# basics — the pared-down, FreeCAD-ready CAM tool library

**114 tools**, chosen from the offline vendor collection (148,412 tools) by `basics_select.py` to the owner's
spec: standards only — square and ball end mills in the common imperial and metric sizes with stub / 4D / 7D reach variants, 90° chamfer mills,
Sandvik single-profile thread mills that cover 56–20 tpi and 0.35–1.0 mm pitch (so every tap below has a thread-mill alternative), and
spiral-flute taps 2-56 … 1/2-20 and M1.6 … M12. The 1-72 tap is **generic** (no vendor has one): ANSI nominal dimensions, flagged `estimated`.
Drills (added 2026-10-23): the tap drill for every tap above and the normal-fit clearance drill for every screw size, deduplicated where one
diameter serves both (#25 = 10-24 tap drill = #6 clearance; #7 = 1/4-20 tap drill = #10 clearance), plus the four drills the 2011 cavity
drawing calls for by size (Ø0.063, 0.070, 0.185 and 0.190 in; the last two with ≥ 51 mm of flute for the 2.0 in deep holes). Max 120 tools.

Library folder: `freecad/basics/` (`Bit/*.fctb`, `Library/basics.fctl`, `Shape/*.fcstd` — self-contained; point FreeCAD CAM's
tool-library path at it or open it in the Tool Bit Library manager). Taps and thread mills use FreeCAD's `thread-mill.fcstd` shape (FreeCAD 1.0 has
no tap shape); the tap pitch is in `attribute.tap_pitch_mm`. Reach = vendor length-below-shank (`LB`) where given, else flute length.

| T | role | shape | vendor | tool id | Ø mm | LOC mm | reach mm | OAL mm | flutes | pitch mm | est. |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1/16 in square, stub | endmill | RobbJack | C8-201-02 | 1.587 | 3.17 | 3.175 | 50.8 | 2 |  |  |
| 2 | 1/16 in square, 4D reach | endmill | RobbJack | C8-203-02 | 1.587 | 6.35 | 6.35 | 63.5 | 2 |  |  |
| 3 | 3/32 in square | endmill | RobbJack | S1-201-03 | 2.38 | 4.76 | 4.762 | 38.1 | 2 |  |  |
| 4 | 1/8 in square | endmill | RobbJack | S1-301-04 | 3.175 | 6.35 | 6.35 | 38.1 | 3 |  |  |
| 5 | 1/8 in square, 4D reach | endmill | RobbJack | C1-301-04 | 3.175 | 12.7 | 12.7 | 38.1 | 3 |  |  |
| 6 | 1/8 in square, 7D reach | endmill | SwiftCARB | AC01252BU003S100 | 3.175 | 19.05 | 21.59 | 63.5 | 2 |  |  |
| 7 | 3/16 in square | endmill | RobbJack | S1-301-06 | 4.763 | 9.52 | 9.525 | 50.8 | 3 |  |  |
| 8 | 3/16 in square, 4D reach | endmill | RobbJack | AL3-304-06 | 4.763 | 19.05 | 19.05 | 50.8 | 3 |  |  |
| 9 | 1/4 in square | endmill | HARVEY TOOL | 968816-C4 | 6.35 | 9.52 | 12.7 | 63.5 | 3 |  |  |
| 10 | 1/4 in square, 4D reach | endmill | RobbJack | AL3-304-08 | 6.35 | 25.4 | 25.4 | 76.2 | 3 |  |  |
| 11 | 1/4 in square, 7D reach | endmill | HELICAL SOLUTIONS | 81471 | 6.35 | 9.52 | 44.615 | 76.2 | 3 |  |  |
| 12 | 5/16 in square | endmill | HARVEY TOOL | 957720 | 7.938 | 11.91 | 15.881 | 63.5 | 2 |  |  |
| 13 | 3/8 in square | endmill | HARVEY TOOL | 852024 | 9.525 | 14.3 | 19.063 | 76.2 | 3 |  |  |
| 14 | 3/8 in square, 4D reach | endmill | RobbJack | TL-303-12 | 9.525 | 38.1 | 38.1 | 88.9 | 3 |  |  |
| 15 | 1/2 in square | endmill | HARVEY TOOL | 968832-C8 | 12.7 | 19.05 | 25.4 | 76.2 | 3 |  |  |
| 16 | 1/2 in square, 4D reach | endmill | RobbJack | TL-303-16 | 12.7 | 50.8 | 50.8 | 101.6 | 3 |  |  |
| 17 | 1/16 in ball | ballend | RobbJack | SB-201-02 | 1.587 | 3.17 | 3.175 | 38.1 | 2 |  |  |
| 18 | 1/8 in ball | ballend | RobbJack | SB-201-04 | 3.175 | 6.35 | 6.35 | 38.1 | 2 |  |  |
| 19 | 1/8 in ball, 4D reach | ballend | RobbJack | B-203-04 | 3.175 | 12.7 | 12.7 | 38.1 | 2 |  |  |
| 20 | 3/16 in ball | ballend | RobbJack | DM-202-06 | 4.763 | 4.76 | 9.525 | 76.2 | 2 |  |  |
| 21 | 1/4 in ball | ballend | HARVEY TOOL | 50916-C3 | 6.35 | 9.52 | 12.7 | 63.5 | 2 |  |  |
| 22 | 1/4 in ball, 4D reach | ballend | Haas Automation | 03-0590 | 6.35 | 19.05 | 26.67 | 63.5 | 2 |  |  |
| 23 | 3/8 in ball | ballend | HARVEY TOOL | 962424 | 9.525 | 14.3 | 19.063 | 76.2 | 2 |  |  |
| 24 | 1/2 in ball | ballend | HARVEY TOOL | 962432 | 12.7 | 19.05 | 25.4 | 101.6 | 2 |  |  |
| 25 | 2 mm square | endmill | RobbJack | MNR-204-02 | 2.0 | 5.0 | 5.0 | 38.0 | 2 |  |  |
| 26 | 3 mm square | endmill | RobbJack | MST-341-03 | 3.0 | 6.0 | 6.0 | 38.0 | 3 |  |  |
| 27 | 3 mm square, 4D reach | endmill | RobbJack | MC1-301-03 | 3.0 | 12.0 | 12.0 | 38.0 | 3 |  |  |
| 28 | 4 mm square | endmill | RobbJack | MST-341-04 | 4.0 | 8.0 | 8.0 | 50.0 | 3 |  |  |
| 29 | 6 mm square | endmill | HELICAL SOLUTIONS | 59691 | 6.0 | 9.0 | 12.0 | 63.0 | 3 |  |  |
| 30 | 6 mm square, 4D reach | endmill | RobbJack | MFM-303-06 | 6.0 | 7.0 | 24.0 | 75.0 | 3 |  |  |
| 31 | 8 mm square | endmill | HELICAL SOLUTIONS | 59697 | 8.0 | 12.0 | 16.0 | 63.0 | 3 |  |  |
| 32 | 10 mm square | endmill | HELICAL SOLUTIONS | 59702 | 10.0 | 15.0 | 20.0 | 63.0 | 3 |  |  |
| 33 | 12 mm square | endmill | HELICAL SOLUTIONS | 59708 | 12.0 | 18.0 | 24.0 | 75.0 | 3 |  |  |
| 34 | 2 mm ball | ballend | RobbJack | MSB-201-02 | 2.0 | 5.0 | 5.0 | 38.0 | 2 |  |  |
| 35 | 3 mm ball | ballend | RobbJack | MSB-201-03 | 3.0 | 6.0 | 6.0 | 38.0 | 2 |  |  |
| 36 | 6 mm ball | ballend | RobbJack | MFM-201-06-BN | 6.0 | 7.0 | 12.0 | 75.0 | 2 |  |  |
| 37 | 1/4 in 90° chamfer | chamfer | HARVEY TOOL | 804816 | 6.35 | 19.05 |  | 63.5 | 4 |  |  |
| 38 | 3/8 in 90° chamfer | chamfer | HARVEY TOOL | 804824 | 9.525 | 28.57 |  | 63.5 | 4 |  |  |
| 39 | 1/2 in 90° chamfer | chamfer | HARVEY TOOL | 804832 | 12.7 | 38.1 |  | 76.2 | 4 |  |  |
| 40 | single-profile thread mill, inch, 56 tpi max, Ø1.6 (#2-56) | thread-mill | Sandvik Coromant | R217.33-016560AC06P 1620 | 1.6 | 0.68 |  | 57.0 | 3 |  |  |
| 41 | single-profile thread mill, inch, 40 tpi max, Ø2.1 (#4-40) | thread-mill | Sandvik Coromant | R217.33-021400AC08P 1620 | 2.1 | 1.59 |  | 57.0 | 3 |  |  |
| 42 | single-profile thread mill, inch, 32 tpi max, Ø3.25 (#6/#8/#10-32) | thread-mill | Sandvik Coromant | R217.33-032320AC12P 1620 | 3.25 | 1.98 |  | 57.0 | 3 |  |  |
| 43 | single-profile thread mill, inch, 24 tpi max, Ø3.55 (#10-24, 5/16-24) | thread-mill | Sandvik Coromant | R217.33-035240AC14P 1620 | 3.55 | 2.65 |  | 57.0 | 3 |  |  |
| 44 | single-profile thread mill, inch, 20 tpi max, Ø4.85 (1/4-20 … 1/2-20) | thread-mill | Sandvik Coromant | R217.33-048200AC19P 1620 | 4.85 | 3.17 |  | 57.0 | 3 |  |  |
| 45 | single-profile thread mill, metric, 0.35 pitch max, Ø1.2 (M1.6) | thread-mill | Sandvik Coromant | R217.13-012035AC05P 1620 | 1.2 | 0.53 |  | 38.0 | 3 |  |  |
| 46 | single-profile thread mill, metric, 0.50 pitch max, Ø2.3 (M2.5/M3) | thread-mill | Sandvik Coromant | R217.13-023050AC06P 1620 | 2.3 | 1.25 |  | 57.0 | 3 |  |  |
| 47 | single-profile thread mill, metric, 0.80 pitch max, Ø4.0 (M4/M5) | thread-mill | Sandvik Coromant | R217.13-040080AC15P 1620 | 4.0 | 2.0 |  | 57.0 | 3 |  |  |
| 48 | single-profile thread mill, metric, 1.00 pitch max, Ø4.8 (M6) | thread-mill | Sandvik Coromant | R217.13-048100AC12P 1620 | 4.8 | 2.5 |  | 57.0 | 3 |  |  |
| 49 | tap 1-72 | thread-mill | GENERIC | 1-72 | 1.854 | 9.52 |  | 42.9 | 2 | 0.3528 | yes |
| 50 | tap 2-56 UN | thread-mill | Sandvik Coromant | T300-XM100AE-2-56   C110 | 2.184 | 14.8 |  | 45.8 | 3 | 0.4536 |  |
| 51 | tap 4-40 UN | thread-mill | Sandvik Coromant | T300-XM100AE-4-40   C110 | 2.845 | 15.5 |  | 56.0 | 3 | 0.635 |  |
| 52 | tap 6-32 UN | thread-mill | Sandvik Coromant | T300-NM100AE-6-32   D150 | 3.505 | 20.0 |  | 56.0 | 3 | 0.7937 |  |
| 53 | tap 8-32 UN | thread-mill | Sandvik Coromant | T300-NM100AE-8-32   D150 | 4.166 | 24.0 |  | 63.0 | 3 | 0.7937 |  |
| 54 | tap 10-24 UN | thread-mill | Sandvik Coromant | T300-SD100DH-10-24  D150 | 4.826 | 24.0 |  | 71.9 | 3 | 1.0583 |  |
| 55 | tap 10-32 UN | thread-mill | Sandvik Coromant | T300-NM100AF-10-32  D150 | 4.826 | 24.0 |  | 70.0 | 3 | 0.7937 |  |
| 56 | tap 1/4-20 UN | thread-mill | Sandvik Coromant | T300-NM100AE-1/4    D150 | 6.35 | 25.0 |  | 80.0 | 3 | 1.27 |  |
| 57 | tap 1/4-28 UN | thread-mill | Sandvik Coromant | T300-NM100AF-1/4    D150 | 6.35 | 25.0 |  | 80.0 | 3 | 0.9071 |  |
| 58 | tap 5/16-18 UN | thread-mill | Sandvik Coromant | T300-NM100AE-5/16   D150 | 7.938 | 26.0 |  | 90.0 | 3 | 1.4111 |  |
| 59 | tap 5/16-24 UN | thread-mill | Sandvik Coromant | T300-NM100AF-5/16   D150 | 7.938 | 26.0 |  | 90.0 | 3 | 1.0583 |  |
| 60 | tap 3/8-16 UN | thread-mill | Sandvik Coromant | T300-NM100AE-3/8    D150 | 9.525 | 35.0 |  | 100.0 | 3 | 1.5875 |  |
| 61 | tap 3/8-24 UN | thread-mill | Sandvik Coromant | T300-NM100AF-3/8    D150 | 9.525 | 35.0 |  | 100.0 | 3 | 1.0583 |  |
| 62 | tap 1/2-13 UN | thread-mill | Sandvik Coromant | T300-NM100AE-1/2    D150 | 12.7 | 42.0 |  | 110.0 | 3 | 1.9539 |  |
| 63 | tap 1/2-20 UN | thread-mill | Sandvik Coromant | T300-NM100AF-1/2    D150 | 12.7 | 42.0 |  | 110.0 | 3 | 1.27 |  |
| 64 | tap M1.6x0.35 | thread-mill | Sandvik Coromant | E000M1.6 | 1.6 | 12.0 |  | 41.6 | 2 | 0.35 |  |
| 65 | tap M2x0.4 | thread-mill | Sandvik Coromant | T300-XM100DA-M2     C110 | 2.0 | 8.0 |  | 45.8 | 3 | 0.4 |  |
| 66 | tap M2.5x0.45 | thread-mill | Sandvik Coromant | T300-XM100DA-M2.5   C110 | 2.5 | 10.8 |  | 51.0 | 3 | 0.45 |  |
| 67 | tap M3x0.5 | thread-mill | Sandvik Coromant | T300-NM100DA-M3     B150 | 3.0 | 16.0 |  | 57.2 | 3 | 0.5 |  |
| 68 | tap M4x0.7 | thread-mill | Sandvik Coromant | T300-NM100AA-M4     D150 | 4.0 | 21.0 |  | 63.0 | 3 | 0.7 |  |
| 69 | tap M5x0.8 | thread-mill | Sandvik Coromant | T300-NM100AA-M5     D150 | 5.0 | 25.0 |  | 70.0 | 3 | 0.8 |  |
| 70 | tap M6x1 | thread-mill | Sandvik Coromant | T300-NM100AA-M6     D150 | 6.0 | 25.0 |  | 80.0 | 3 | 1.0 |  |
| 71 | tap M8x1.25 | thread-mill | Sandvik Coromant | T300-NM100AA-M8     D150 | 8.0 | 32.0 |  | 90.0 | 3 | 1.25 |  |
| 72 | tap M10x1.5 | thread-mill | Sandvik Coromant | T300-NM100AA-M10    D150 | 10.0 | 34.0 |  | 100.0 | 3 | 1.5 |  |
| 73 | tap M12x1.75 | thread-mill | Sandvik Coromant | T300-NM101AA-M12    D150 | 12.0 | 42.0 |  | 110.0 | 3 | 1.75 |  |
| 74 | tap drill M1.6 (1.25 mm) | drill | HARVEY TOOL | BVT0492-C3 | 1.25 | 8.73 |  | 50.0 | 2 |  |  |
| 75 | tap drill 1-72 (#53, 0.0595 in) | drill | HARVEY TOOL | BAF0595-C8 | 1.511 | 10.35 |  | 50.0 | 3 |  |  |
| 76 | tap drill M2 (1.6 mm) = drawing Ø0.063 note K, 1.43 in deep | drill | Garr Tool | 00398 | 1.6 | 11.0 |  | 50.0 | 2 |  |  |
| 77 | tap drill 2-56 (#50, 0.07 in) = clearance M1.6 screw, medium fit (1.8 mm) = drawing Ø0.070 note P, through arm | drill | HARVEY TOOL | BAF0700-C8 | 1.778 | 12.41 |  | 50.0 | 3 |  |  |
| 78 | tap drill M2.5 (2.05 mm) = clearance #1 screw, normal fit (#46, 0.081 in) | drill | Garr Tool | 00430 | 2.05 | 14.0 |  | 50.0 | 2 |  |  |
| 79 | tap drill 4-40 (#43, 0.089 in) | drill | Garr Tool | 00446 | 2.261 | 15.88 |  | 50.8 | 2 |  |  |
| 80 | clearance M2 screw, medium fit (2.4 mm) | drill | Garr Tool | 00456 | 2.4 | 17.0 |  | 50.0 | 2 |  |  |
| 81 | clearance #2 screw, normal fit (#41, 0.096 in) | drill | HARVEY TOOL | BAF0960-C8 | 2.438 | 16.57 |  | 63.0 | 3 |  |  |
| 82 | tap drill M3 (2.5 mm) | drill | Garr Tool | 00464 | 2.5 | 17.5 |  | 50.0 | 2 |  |  |
| 83 | tap drill 6-32 (#36, 0.1065 in) | drill | Garr Tool | 00480 | 2.705 | 19.05 |  | 50.8 | 2 |  |  |
| 84 | clearance M2.5 screw, medium fit (2.9 mm) | drill | Haas Automation | 03-1261 | 2.9 | 20.0 |  | 62.0 | 2 |  |  |
| 85 | clearance #4 screw, normal fit (#30, 0.1285 in) | drill | Garr Tool | 19225 | 3.264 | 23.81 |  | 49.2 | 2 |  |  |
| 86 | tap drill M4 (3.3 mm) | drill | ISCAR | 6154601 | 3.3 | 23.0 |  | 66.0 | 2 |  |  |
| 87 | clearance M3 screw, medium fit (3.4 mm) | drill | Guhring | 9007680034000 | 3.4 | 24.0 |  | 66.0 | 2 |  |  |
| 88 | tap drill 8-32 (#29, 0.136 in) | drill | Haas Automation | 03-2371 | 3.454 | 23.83 |  | 49.2 | 2 |  |  |
| 89 | tap drill 10-24 (#25, 0.1495 in) = clearance #6 screw, normal fit (#25, 0.1495 in) | drill | HARVEY TOOL | BVT1495-C3 | 3.797 | 26.69 |  | 75.0 | 2 |  |  |
| 90 | tap drill 10-32 (#21, 0.159 in) | drill | Garr Tool | 59380 | 4.039 | 28.57 |  | 63.5 | 2 |  |  |
| 91 | tap drill M5 (4.2 mm) | drill | ISCAR | 6154826 | 4.2 | 29.0 |  | 74.0 | 2 |  |  |
| 92 | clearance #8 screw, normal fit (#16, 0.177 in) = clearance M4 screw, medium fit (4.5 mm) | drill | Garr Tool | 59410 | 4.496 | 30.16 |  | 63.5 | 2 |  |  |
| 93 | drawing Ø0.185 note M, 8-32 loose, 2.0 in deep | drill | Haas Automation | 03-0296 | 4.699 | 58.75 |  | 88.9 | 2 |  |  |
| 94 | drawing Ø0.190 note L, 2.0 in deep | drill | Guhring | 9002050048300 | 4.83 | 52.0 |  | 86.0 | 2 |  |  |
| 95 | tap drill M6 (5.0 mm) | drill | Guhring | 9006090050000 | 5.0 | 35.0 |  | 62.0 | 3 |  |  |
| 96 | tap drill 1/4-20 (#7, 0.201 in) = clearance #10 screw, normal fit (#7, 0.201 in) | drill | HARVEY TOOL | BAF2009-C8 | 5.105 | 35.19 |  | 75.0 | 3 |  |  |
| 97 | tap drill 1/4-28 (#3, 0.213 in) | drill | HARVEY TOOL | BAF2129-C8 | 5.41 | 37.26 |  | 75.0 | 3 |  |  |
| 98 | clearance M5 screw, medium fit (5.5 mm) | drill | Guhring | 9014520055000 | 5.5 | 39.0 |  | 66.0 | 3 |  |  |
| 99 | tap drill 5/16-18 (F, 0.257 in) | drill | HARVEY TOOL | BAF2570-C8 | 6.528 | 45.52 |  | 100.0 | 3 |  |  |
| 100 | clearance M6 screw, medium fit (6.6 mm) | drill | Guhring | 9012430066000 | 6.6 | 43.0 |  | 83.0 | 2 |  |  |
| 101 | tap drill M8 (6.8 mm) | drill | Guhring | 9006090068000 | 6.8 | 45.0 |  | 74.0 | 3 |  |  |
| 102 | tap drill 5/16-24 (I, 0.272 in) | drill | KYOCERA SGS Precision Tools | 51514 | 6.909 | 52.78 |  | 92.1 | 2 |  |  |
| 103 | clearance 1/4 screw, normal fit (9/32, 0.2813 in) | drill | Haas Automation | 03-0377 | 7.145 | 53.01 |  | 91.0 | 2 |  |  |
| 104 | tap drill 3/8-16 (5/16, 0.3125 in) | drill | Haas Automation | 03-0378 | 7.938 | 53.01 |  | 91.0 | 2 |  |  |
| 105 | tap drill 3/8-24 (Q, 0.332 in) | drill | KYOCERA SGS Precision Tools | 51922 | 8.433 | 61.01 |  | 103.0 | 2 |  |  |
| 106 | tap drill M10 (8.5 mm) | drill | Guhring | 9055150085000 | 8.5 | 61.0 |  | 103.0 | 2 |  |  |
| 107 | clearance 5/16 screw, normal fit (11/32, 0.3438 in) | drill | KYOCERA SGS Precision Tools | 51521 | 8.732 | 61.12 |  | 101.6 | 2 |  |  |
| 108 | clearance M8 screw, medium fit (9.0 mm) | drill | Garr Tool | 56680 | 9.0 | 63.0 |  | 101.0 | 2 |  |  |
| 109 | tap drill M12 (10.2 mm) | drill | Guhring | 9055110102000 | 10.2 | 71.0 |  | 118.0 | 2 |  |  |
| 110 | clearance 3/8 screw, normal fit (13/32, 0.4063 in) | drill | Guhring | 9065010103200 | 10.32 | 71.0 |  | 118.0 | 2 |  |  |
| 111 | tap drill 1/2-13 (27/64, 0.4219 in) | drill | Garr Tool | 56755 | 10.716 | 73.03 |  | 114.3 | 2 |  |  |
| 112 | clearance M10 screw, medium fit (11.0 mm) | drill | Garr Tool | 56761 | 11.0 | 73.0 |  | 114.0 | 2 |  |  |
| 113 | tap drill 1/2-20 (29/64, 0.4531 in) | drill | Garr Tool | 56775 | 11.509 | 76.2 |  | 120.7 | 2 |  |  |
| 114 | clearance 1/2 screw, normal fit (17/32, 0.5313 in) = clearance M12 screw, medium fit (13.5 mm) | drill | Garr Tool | 26881 | 13.492 | 104.78 |  | 155.6 | 2 |  |  |
