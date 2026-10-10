"""Makes the README images (illustrative mockups, not real screenshots). Needs python playwright + chromium.
Usage: python3 tools/make_images.py"""
import os
from playwright.sync_api import sync_playwright

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "images")
TROPHY = '<svg viewBox="0 0 64 64" width="{s}" height="{s}"><path d="M18 8h28v14c0 9-6 16-14 16S18 31 18 22z" fill="{c}"/><path d="M18 12H8c0 10 4 16 12 17M46 12h10c0 10-4 16-12 17" fill="none" stroke="{c}" stroke-width="4"/><rect x="28" y="38" width="8" height="10" fill="{c}"/><rect x="20" y="48" width="24" height="7" rx="2" fill="{c}"/></svg>'
CSS = """
*{box-sizing:border-box;margin:0}body{font-family:'DejaVu Sans',Arial,sans-serif;color:#fff}
.toast{display:flex;align-items:center;gap:18px;padding:16px 26px 16px 16px;border-radius:18px;background:linear-gradient(135deg,#1b2433,#0f141d);border:2px solid var(--c);box-shadow:0 0 28px var(--g),0 8px 24px #0009;width:640px}
.badge{width:84px;height:84px;border-radius:14px;background:linear-gradient(135deg,var(--c),#0008);display:flex;align-items:center;justify-content:center;flex:none}
.t{flex:1;min-width:0}.k{font-size:13px;letter-spacing:2px;color:var(--c);font-weight:700}
.n{font-size:24px;font-weight:700;margin:3px 0}.d{font-size:15px;color:#b9c4d6;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pill{display:inline-block;margin-top:9px;padding:4px 12px;border-radius:99px;background:var(--c);color:#0b0f16;font-size:13px;font-weight:700}
"""
def toast(kind, name, desc, pill, c, g):
    return f'<div class="toast" style="--c:{c};--g:{g}"><div class="badge">{TROPHY.format(s=54,c="#fff")}</div><div class="t"><div class="k">{kind}</div><div class="n">{name}</div><div class="d">{desc}</div><span class="pill">{pill}</span></div></div>'
TOASTS = [
 ("ACHIEVEMENT UNLOCKED","First Steps","Finish the first level","10 pts · 61% of players","#5aa9ff","#5aa9ff55"),
 ("RARE ACHIEVEMENT","No Damage Run","Beat stage 3 without losing a ring","25 pts (RP 310) · 4.2%","#c78bff","#c78bff66"),
 ("ULTRA RARE · HARDCORE","Perfect Champion","Win every race on gold","50 pts (RP 1480) HC · 0.6%","#ffc233","#ffc23377"),
]
def page(body, w, h, bg):
    return f'<html><head><style>{CSS}body{{width:{w}px;height:{h}px;background:{bg};display:flex;flex-direction:column;align-items:center;justify-content:center;gap:22px}}</style></head><body>{body}</body></html>'
GAME = "radial-gradient(circle at 30% 20%,#2d4a7a,#101828 70%)"
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    def shot(html, name, w, h):
        pg.set_viewport_size({"width": w, "height": h}); pg.set_content(html)
        pg.screenshot(path=os.path.join(OUT, name))
    for i, t in enumerate(TOASTS):
        shot(page(toast(*t), 760, 170, GAME), "toast-%d.png" % (i + 1), 760, 170)
    shot(page("".join(toast(*t) for t in TOASTS), 900, 640, GAME), "tiers.png", 900, 640)
    banner = (f'<div style="display:flex;align-items:center;gap:36px">{TROPHY.format(s=170,c="#ffc233")}'
              '<div><div style="font-size:54px;font-weight:800">RetroAchievements Toasts</div>'
              '<div style="font-size:28px;color:#b9c4d6;margin-top:10px">Achievement popups for emulators on Steam Deck</div>'
              '<div style="font-size:20px;color:#7e8aa0;margin-top:14px">Decky Loader plugin · 18 styles · rarity tiers · sounds</div></div></div>'
              + '<div style="transform:scale(.8)">' + toast(*TOASTS[1]) + '</div>')
    shot(page(banner, 1280, 640, GAME), "banner.png", 1280, 640)
    b.close()
print("ok")
