"""Quote builder: pulls the OP10 cycle time from the G-code tests, applies the shop profile, prices qty 24 and 100 with
finish options. Writes quote.md + quote.csv. Usage: /usr/bin/python3 build_quote.py"""
import json, os, csv
HERE = os.path.dirname(os.path.abspath(__file__))
T = json.load(open(os.path.join(HERE, "..", "06_cam", "tests", "test_results.json")))["tests"]
op10 = T["T5_cycle_time"]["total_s"]; per_tool = T["T5_cycle_time"]["feed_s_per_tool"]
R = dict(vmc=95.0, setup=95.0, prog=110.0, bench=65.0)
LOAD10, DEBURR = 60.0, 120.0                     # s per part: load/unload; bench deburr + tab blend + functional check
MATL_BAR_PER_IN = 0.48; CUT_LEN_IN = 3.4; MATL_MARKUP = 1.15   # 6061-T6 1/2 x 1-1/4 flat bar, $/inch incl. kerf
MATL_7075_PER_IN = 0.92
SETUP_H = dict(op10=1.0, first_article=0.75); PROG_H = 0.75    # one setup; first article includes the thin-wall prove-out
TOOLING = dict(em_quarter=28.0, em_eighth=18.0, ball_eighth=22.0)
ANOD = dict(lot_min=85.0, per_pc_over=0.60, markup=1.20)
def quote(qty, colours, alloy="6061"):
    run_s = op10 + LOAD10; rows = []
    rows.append(("Setup (one op) + first article incl. 1.1 mm arm prove-out", SETUP_H["op10"] + SETUP_H["first_article"], "h", R["setup"]))
    rows.append(("Programming / prove-out (post, offsets, tabs)", PROG_H, "h", R["prog"]))
    rows.append((f"Machine run {run_s:.0f} s/pc (OP10 {op10:.0f} s + load {LOAD10:.0f} s)", qty * run_s / 3600, "h", R["vmc"]))
    rows.append((f"Bench: break 2 tabs, deburr card edges, functional check {DEBURR:.0f} s/pc", qty * DEBURR / 3600, "h", R["bench"]))
    per_in = MATL_BAR_PER_IN if alloy == "6061" else MATL_7075_PER_IN
    rows.append((f"Material {alloy}-T6 1/2 x 1-1/4 bar, {CUT_LEN_IN} in/pc, +15%", qty, "pc", per_in * CUT_LEN_IN * MATL_MARKUP))
    rows.append(("Tooling consumables (1/4 EM, 1/8 EM, 1/8 ball)", 1, "lot", sum(TOOLING.values()) * (1 if qty <= 50 else 1.5)))
    per_colour = max(ANOD["lot_min"], ANOD["per_pc_over"] * qty / colours) * ANOD["markup"]
    rows.append((f"Anodize Type II, {colours} colour lot(s), min $85/lot, +20%", colours, "lot", per_colour))
    total = sum(q * rate for _, q, _, rate in rows); return rows, total
out = ["# 05 · Shop quote — SAFT-V2-TAB v2", "",
       f"Cycle time is taken from the verified G-code (06_cam/tests/test_results.json): **OP10 {op10:.0f} s** — T1 1/4 in contour {float(per_tool['1']):.0f} s, "
       f"T2 1/8 in rest + pocket {float(per_tool['2']):.0f} s, T3 dimples {float(per_tool['3']):.0f} s, plus rapids and 3 tool changes. One setup, no saw op. Rates from shop_profile.md.", ""]
csvrows = [["qty", "alloy", "colours", "line", "qty_units", "unit", "rate", "ext"]]; totals = {}
for qty, colours, alloy in [(24, 1, "6061"), (24, 4, "6061"), (100, 1, "6061"), (100, 6, "6061"), (24, 4, "7075"), (100, 6, "7075")]:
    rows, total = quote(qty, colours, alloy); totals[(qty, colours, alloy)] = total
    out += [f"## Qty {qty} · {alloy}-T6 · {colours} anodize colour{'s' if colours > 1 else ''}", "", "| Line | Qty | Unit | Rate | Ext |", "|---|---|---|---|---|"]
    for name, q, u, rate in rows:
        out.append(f"| {name} | {q:.2f} | {u} | ${rate:,.2f} | ${q * rate:,.2f} |"); csvrows.append([qty, alloy, colours, name, round(q, 3), u, round(rate, 2), round(q * rate, 2)])
    out += ["", f"**Total ${total:,.2f}  →  ${total / qty:,.2f} per part**", ""]; csvrows.append([qty, alloy, colours, "TOTAL", "", "", "", round(total, 2)])
out += ["## Reading the quote",
f"- **One setup instead of two is the V2 story.** V1's clip needed Op10 + Op20 (saw + chamfer) and 2.75 h of setup; this part needs {SETUP_H['op10'] + SETUP_H['first_article']:.2f} h of setup and one fixture. Setup + programming is ~${(SETUP_H['op10'] + SETUP_H['first_article']) * R['setup'] + PROG_H * R['prog']:.0f} before a chip is cut, against ~$370 in V1.",
f"- **Machine time is the largest per-part line** at ~${(op10 + LOAD10) / 3600 * R['vmc']:.2f}/part: the 1/8 in end mill does 2.4 m of slotting through 12.7 mm plate at 480 mm/min. A 3/16 in tool for the 3.8 mm channel and a lighter 1/8 in pass only where the 3.4 mm features are would roughly halve T2; it is the first thing to try on the second lot.",
"- **Anodize colour lots** are the second driver at small quantity, exactly as in V1: every colour is a separate $85 minimum.",
f"- **R10 (≤ $20 at 24 pcs, ≤ $10 at 100):** {'met' if totals[(24, 1, '6061')] / 24 <= 20 else 'missed'} at 24 pcs / 1 colour (${totals[(24, 1, '6061')] / 24:.2f}); {'met' if totals[(100, 1, '6061')] / 100 <= 10 else 'missed'} at 100 pcs / 1 colour (${totals[(100, 1, '6061')] / 100:.2f}). With 4 colours at 24 pcs: ${totals[(24, 4, '6061')] / 24:.2f}.",
"- **7075-T6** adds about $1.50/part and takes the 30-card overload safety factor from 1.4 to 2.5 (03_fea). Recommended if the keepers will be over-stuffed.",
"- Not priced: a waterjet-cut lot. The drawing allows it only if the 0.25 rib height holds through the thickness; a 12.7 mm waterjet taper of ~0.1 mm would consume most of that tolerance, so it is not recommended without a trial."]
open(os.path.join(HERE, "quote.md"), "w").write("\n".join(out) + "\n")
csv.writer(open(os.path.join(HERE, "quote.csv"), "w", newline="")).writerows(csvrows)
for k, v in totals.items(): print(k, f"${v:,.2f}", f"${v / k[0]:,.2f}/pc")
