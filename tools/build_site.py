"""Convert every .md under the project to a styled .html twin (same folder), so an auto-indexed folder browses
cleanly. Also writes a top-level index.html linking everything. Run: /usr/bin/python3 build_site.py"""
import os, subprocess, re, html
ROOT = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(ROOT) == "tools": ROOT = os.path.dirname(ROOT)   # when kept in tools/, the project root is the parent
STYLE = """<style>
:root{--bg:#fff;--fg:#1f1f1f;--muted:#666;--rule:#d0d0d0;--box:#f5f5f5;--link:#0b57d0;--code:#f0f0f0}
@media (prefers-color-scheme:dark){:root{--bg:#121416;--fg:#e2e2e2;--muted:#9a9a9a;--rule:#3a3f45;--box:#1b1f23;--link:#8ab4f8;--code:#1e2328}}
html,body{margin:0;background:var(--bg);color:var(--fg)}
body{font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;padding:0 16px 64px;max-width:1000px;margin:0 auto}
h1{font-size:28px;line-height:1.2;border-bottom:1px solid var(--rule);padding-bottom:8px;margin:32px 0 16px}
h2{font-size:21px;border-bottom:1px solid var(--rule);padding-bottom:4px;margin:36px 0 12px} h3{font-size:17px;margin:24px 0 8px}
a{color:var(--link)} p{margin:0 0 12px} img,video{max-width:100%;height:auto;border:1px solid var(--rule);border-radius:4px;margin:6px 0}
blockquote{margin:0 0 16px;padding:8px 16px;border-left:4px solid var(--rule);background:var(--box);color:var(--muted)}
table{border-collapse:collapse;width:100%;margin:0 0 20px;font-size:14.5px;display:block;overflow-x:auto}
th,td{border:1px solid var(--rule);padding:6px 10px;text-align:left;vertical-align:top} th{background:var(--box)}
code{font:13.5px/1.4 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;background:var(--code);padding:1px 4px;border-radius:3px}
pre{background:var(--code);padding:12px 14px;overflow-x:auto;border-radius:4px;margin:0 0 16px} pre code{background:none;padding:0}
li{margin:3px 0} hr{border:0;border-top:1px solid var(--rule);margin:28px 0}
nav.crumb{font-size:13px;color:var(--muted);margin:14px 0 0} nav.crumb a{color:var(--muted)}
</style>"""
hdr = os.path.join(ROOT, ".pandoc_header.html"); open(hdr, "w").write(STYLE)
built = []
for dp, dn, fn in os.walk(ROOT):
    dn[:] = [d for d in dn if not d.startswith(".") and d != "__pycache__"]
    for f in sorted(fn):
        if not f.endswith(".md"): continue
        src = os.path.join(dp, f); dst = src[:-3] + ".html"
        rel = os.path.relpath(dp, ROOT); depth = 0 if rel == "." else rel.count(os.sep) + 1
        up = "../" * depth
        title = next((l[2:].strip() for l in open(src) if l.startswith("# ")), f[:-3])
        crumb = f'<nav class="crumb"><a href="{up}index.html">Automatic Factory Testing V2</a>' + (f' / {html.escape(rel)}' if rel != "." else "") + f' / {html.escape(f)}</nav>'
        bf = os.path.join(dp, ".crumb.html"); open(bf, "w").write(crumb)
        subprocess.run(["pandoc", "-f", "gfm", "-t", "html5", "-s", "--metadata", f"title={title}", "-H", hdr, "-B", bf, "-o", dst, src], check=True)
        os.remove(bf); built.append(os.path.relpath(dst, ROOT))
os.remove(hdr)
# top-level index: README first, then everything by folder, with media thumbnails
links = []
for dp, dn, fn in os.walk(ROOT):
    dn[:] = sorted(d for d in dn if not d.startswith(".") and d != "__pycache__")
    rel = os.path.relpath(dp, ROOT)
    files = sorted(f for f in fn if not f.startswith(".") and f != "index.html")
    if rel == ".": continue
    items = []
    for f in files:
        p = os.path.join(rel, f)
        if f.endswith((".png", ".gif")): items.append(f'<div><a href="{p}"><img src="{p}" alt="{f}" style="max-width:300px"></a><br><code>{f}</code></div>')
        elif f.endswith(".mp4"): items.append(f'<div><video src="{p}" controls style="max-width:300px"></video><br><code>{f}</code></div>')
        else: items.append(f'<div><a href="{p}">{f}</a></div>')
    links.append(f"<h2>{rel}/</h2><div style='display:flex;flex-wrap:wrap;gap:12px'>" + "".join(items) + "</div>")
readme = "README.html" if os.path.exists(os.path.join(ROOT, "README.html")) else None
idx = f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Automatic Factory Testing V2</title>{STYLE}</head><body><h1>Automatic Factory Testing V2</h1>"
idx += (f"<p><b><a href='{readme}'>Start with the README (end-to-end narrative)</a></b></p>" if readme else "") + "".join(links) + "</body></html>"
open(os.path.join(ROOT, "index.html"), "w").write(idx)
print("built", len(built), "html files + index.html")
