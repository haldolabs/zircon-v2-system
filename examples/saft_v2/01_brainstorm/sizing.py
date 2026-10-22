"""Quantified pre-design for the V2 card keeper: card data, holding requirement, the zero-gap problem, and the
series-spring model of the offset-tooth ("weave") clip. Writes sizing.json + media/*.png.
Usage: ~/miniconda3/envs/cae/bin/python sizing.py"""
import json, os, math, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); M = os.path.join(HERE, "media"); os.makedirs(M, exist_ok=True)
# ---- card data (owner: 0.005 in thick; 3x5 in index card assumed, ~160 g/m2 for that caliper; estimates flagged) ----
t_card = 0.005 * 25.4                 # 0.127 mm
card = dict(w_mm=76.2, l_mm=127.0, t_mm=round(t_card, 3), gsm_est=160.0)
card["mass_g_est"] = round(card["gsm_est"] * card["w_mm"] * card["l_mm"] * 1e-6, 2)   # 1.55 g
E_card = 3000.0                       # MPa, paperboard, ESTIMATE (2-5 GPa in the literature)
mu = 0.30                             # paper on anodized Al, ESTIMATE
stack24 = 24 * t_card                 # 3.048 mm
W24_N = 24 * card["mass_g_est"] * 9.81e-3
req = dict(stack_min_mm=round(t_card, 3), stack_max_mm=round(stack24, 3), weight_24_N=round(W24_N, 3),
           hold_factor=5.0, hold_req_24_N=round(5 * W24_N, 2), insert_force_max_N=25.0)
# ---- the zero-gap problem: a subtractive one-piece clip cannot have a rest gap below the kerf ----
kerfs = {"1/32 in slitting saw (V1)": 0.8, "1/64 in slitting saw": 0.4, "wire EDM 0.25 wire": 0.33, "1/8 in end mill slot": 3.175, "needed for 1 card": t_card}
zero_gap = {k: dict(kerf_mm=v, min_cards=math.ceil(v / t_card)) for k, v in kerfs.items()}
# ---- arm sizing (E-B cantilever, 6061-T6) ----
E, b = 69000.0, 12.7                   # 1/2 in plate: the 1/8 in end mill's 4xD reach sets the plate width
EXT = 5.7                               # the rigid tooth puts the clamp resultant 5.7 mm beyond the flexible arm's end
def arm(t, Lf, d):   # uniform arm: force and root bending stress for deflection d at the load point (lever Lf + EXT)
    I = b * t**3 / 12; comp = ((Lf + EXT)**3 - EXT**3) / (3 * E * I); F = d / comp; s = F * (Lf + EXT) * (t / 2) / I; return F, s
def arm_taper(t0, t1, Lf, d, n=2000):  # linearly tapered thickness t0 (root) -> t1 (tip), unit-load integration
    x = np.linspace(0, Lf, n); t = t0 + (t1 - t0) * x / Lf; I = b * t**3 / 12
    comp = np.trapezoid((Lf + EXT - x)**2 / (E * I), x)   # deflection at the load point per unit force
    F = d / comp; M = F * (Lf + EXT - x); s = M * (t / 2) / I; return F, float(s.max()), float(x[s.argmax()])
d0 = 0.25                               # tooth overlap below the floor plane (preload)
cases = {"1 card": t_card + d0, "12 cards": 12 * t_card + d0, "24 cards": stack24 + d0, "30 cards (overload)": 30 * t_card + d0}
cands = {}
for name, (t, Lf) in {"t1.2 L42 uniform (v1)": (1.2, 42.0), "t1.5 L42 uniform": (1.5, 42.0), "t1.0 L42 uniform": (1.0, 42.0), "t1.1 L46 uniform (v2)": (1.1, 46.0)}.items():
    F, s = arm(t, Lf, cases["24 cards"]); cands[name] = dict(F24_N=round(F, 1), sigma24_MPa=round(s, 0), SF_6061=round(276 / s, 2), k_N_per_mm=round(F / cases["24 cards"], 2))
for name, (t0, t1, Lf) in {"taper 1.7->1.0 L42": (1.7, 1.0, 42.0), "taper 1.6->1.0 L42": (1.6, 1.0, 42.0), "taper 1.8->1.1 L42": (1.8, 1.1, 42.0)}.items():
    F, s, xs = arm_taper(t0, t1, Lf, cases["24 cards"]); cands[name] = dict(F24_N=round(F, 1), sigma24_MPa=round(s, 0), SF_6061=round(276 / s, 2), k_N_per_mm=round(F / cases["24 cards"], 2), x_sigma_max=round(xs, 1))
# ---- weave model: card stack over a 7 mm notch as a 3-point-bent strip of width b, in series with the arm ----
span = 8.4                              # tooth-notch span: rib 1.6 + 2 x (tool 3.175 + 0.225) — set by the end mill, not by choice
def k_cards(n):  # n cards sliding freely (no interlaminar shear): n x single-card stiffness, simply supported centre load
    I1 = b * t_card**3 / 12; return n * 48 * E_card * I1 / span**3
def clamp(n, k_arm):
    inter = n * t_card + d0; kc = k_cards(n); F = inter / (1 / k_arm + 1 / kc); return F, F / kc, F / k_arm
k_arm = cands["t1.2 L42 uniform (v1)"]["k_N_per_mm"]
table = []
for n in (1, 2, 4, 8, 12, 16, 20, 24, 30):
    F, xc, xa = clamp(n, k_arm); hold = 2 * mu * F; weight = n * card["mass_g_est"] * 9.81e-3
    # card bending strain at the loaded centre of the 3-point span (per card; cards bend as independent plies)
    kappa = 12 * xc / span**2; strain = kappa * t_card / 2
    table.append(dict(cards=n, interference_mm=round(n * t_card + d0, 3), clamp_N=round(F, 2), card_dip_mm=round(xc, 3), arm_lift_mm=round(xa, 3),
                      hold_N=round(hold, 2), weight_N=round(weight, 3), hold_over_weight=round(hold / weight, 0), card_strain_pct=round(100 * strain, 2)))
out = dict(card=card, E_card_MPa_est=E_card, mu_est=mu, requirements=req, zero_gap=zero_gap, d0_mm=d0, arm_candidates=cands, cases_mm=cases, weave_table=table)
json.dump(out, open(os.path.join(HERE, "sizing.json"), "w"), indent=1)
for k, v in cands.items(): print(k, v)
for r in table: print(r)
# ---- figure 1: the weave principle (schematic) ----
fig, ax = plt.subplots(figsize=(8, 3.6), dpi=130)
ax.add_patch(plt.Rectangle((0, 0), 64, 4, fc="#c9ced6", ec="k")); ax.add_patch(plt.Rectangle((50.5, 2), 7, 2.01, fc="white", ec="none"))
ax.plot([50.5, 50.5, 57.5, 57.5], [4, 2, 2, 4], "k")
ax.add_patch(plt.Rectangle((0, 0), 10, 13.5, fc="#c9ced6", ec="k")); ax.add_patch(plt.Rectangle((10, 12.3), 42, 1.2, fc="#c9ced6", ec="k"))
tooth = [(52, 12.3), (61.2, 12.3), (61.2, 7.6), (54.5, 3.75), (53.5, 3.75), (52, 4.3)]
ax.add_patch(plt.Polygon(tooth, fc="#9aa3b2", ec="k")); ax.add_patch(plt.Rectangle((10, 4), 37.5, 3.6, fc="#c9ced6", ec="k"))
xs = np.linspace(47.5, 70, 100); yc = np.where((xs > 50.5) & (xs < 57.5), 4.15 - 0.4 * np.sin(np.pi * (xs - 50.5) / 7) ** 1, 4.15)
ax.plot(xs, yc, color="#d9534f", lw=2.5, label="card (bent into the notch)")
ax.annotate("tooth land\n0.25 below floor", (54, 3.75), (40, -1.5), arrowprops=dict(arrowstyle="->"), fontsize=8, ha="center")
ax.annotate("notch 7 wide", (54, 2), (54, -3), arrowprops=dict(arrowstyle="->"), fontsize=8, ha="center")
ax.annotate("arm flexes up\nfor thick stacks", (30, 12.9), (30, 16.5), arrowprops=dict(arrowstyle="->"), fontsize=8, ha="center")
ax.annotate("30° lead-in", (58, 5.8), (66, 2), arrowprops=dict(arrowstyle="->"), fontsize=8)
ax.annotate("stop", (47.5, 6), (44, 9.5), arrowprops=dict(arrowstyle="->"), fontsize=8)
ax.set_xlim(-2, 72); ax.set_ylim(-4, 18); ax.set_aspect("equal"); ax.axis("off"); ax.legend(loc="upper right", fontsize=8)
ax.set_title("Offset-tooth weave, FIRST SKETCH: a one-piece 2D profile with NO slit — one card is held by its own bending\n(the released part inverts it: rib on the floor, notch in the tooth — see 02_design)", fontsize=8.5)
fig.savefig(os.path.join(M, "weave_principle.png"), bbox_inches="tight"); plt.close(fig)
# ---- figure 2: clamp / hold vs card count ----
fig, ax = plt.subplots(figsize=(6.4, 3.8), dpi=130)
n = [r["cards"] for r in table]
ax.plot(n, [r["clamp_N"] for r in table], "o-", color="#4c72b0", label="clamp force (series model)")
ax.plot(n, [r["hold_N"] for r in table], "s-", color="#55a868", label="holding force 2·μ·F (μ=0.3 est.)")
ax.plot(n, [5 * r["weight_N"] for r in table], "--", color="#c44e52", label="required: 5× stack weight")
ax.set_xlabel("cards in the stack"); ax.set_ylabel("N"); ax.set_yscale("log"); ax.grid(alpha=.3); ax.legend(fontsize=8)
ax.set_title("Holding margin vs stack size (v1 arm t1.2 L42, 12.7 wide, 6061; strip model)", fontsize=9)
fig.savefig(os.path.join(M, "hold_vs_cards.png"), bbox_inches="tight"); plt.close(fig)
print("ok")
