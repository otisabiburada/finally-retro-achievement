"""Drives the real built panel (dist/index.js) against the real Python backend and a mock RetroAchievements."""
import asyncio, json, os, sys, threading, time, http.server
SCR = os.path.dirname(os.path.abspath(__file__))
ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(SCR))
SHOTS = os.environ.get("SHOTS_DIR")      # set to save screenshots
sys.path.insert(0, os.path.dirname(SCR))
from common import KEY, MockRA, load_plugin, unlock, progress

mock = MockRA()
main, decky, emitted, tmp = load_plugin(ROOT, mock)
shown = []
loop = asyncio.new_event_loop(); threading.Thread(target=loop.run_forever, daemon=True).start()
def run(c): return asyncio.run_coroutine_threadsafe(c, loop).result(60)
async def make():
    p = main.Plugin()
    async def fake(payload): shown.append(payload)
    p._show_gamescope_overlay = fake
    await p._main()
    return p
plugin = run(make())

class App(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        path = self.path.split("?")[0]
        files = {"/": os.path.join(SCR, "index.html"), "/harness.js": os.path.join(SCR, "harness.js"), "/dist/index.js": os.path.join(ROOT, "dist", "index.js")}
        f = files.get(path)
        if not f: self.send_response(404); self.end_headers(); return
        d = open(f, "rb").read(); self.send_response(200); self.send_header("Content-Type", "text/html" if f.endswith(".html") else "text/javascript"); self.end_headers(); self.wfile.write(d)
    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        try: out = {"result": run(getattr(plugin, req["name"])(*req["args"]))}
        except Exception as e: out = {"error": repr(e)}
        d = json.dumps(out, default=str).encode(); self.send_response(200); self.end_headers(); self.wfile.write(d)
app = http.server.ThreadingHTTPServer(("127.0.0.1", 0), App); threading.Thread(target=app.serve_forever, daemon=True).start()
url = "http://127.0.0.1:%d/" % app.server_address[1]

# 20 achievements so paging shows up; two recent games
big = progress(total=20, got=2)
big["Achievements"] = {str(i): {"ID": i, "Title": "Ach %d" % i, "Description": "Do thing %d" % i, "Points": 5 * i, "BadgeName": "9%d" % i,
    "DisplayOrder": i, "NumAwarded": 50 * i, **({"DateEarned": "2026-10-0%d 10:00:00" % (1 + i % 5)} if i in (1, 2) else {})} for i in range(1, 21)}
mock.progress["11"] = big
mock.progress["12"] = {**progress(total=9, got=0), "ID": 12, "Title": "Streets of Rage"}
mock.recent_games = [{"GameID": 11, "Title": "Sonic the Hedgehog", "ConsoleName": "Mega Drive", "NumPossibleAchievements": 20, "NumAchieved": 2},
                     {"GameID": 12, "Title": "Streets of Rage", "ConsoleName": "Mega Drive", "NumPossibleAchievements": 9, "NumAchieved": 0}]

from playwright.sync_api import sync_playwright
errors = []; ok = 0
def check(c, m):
    global ok
    if not c: print("FAIL:", m); os._exit(1)
    ok += 1
with sync_playwright() as pw:
    exe = os.environ.get("CHROMIUM")
    if not exe:
        base = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
        found = [os.path.join(base, d, "chrome-linux", "chrome") for d in sorted(os.listdir(base)) if d.startswith("chromium-")] if os.path.isdir(base) else []
        exe = found[0] if found else None
    b = pw.chromium.launch(executable_path=exe, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width": 420, "height": 1000})
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("console", lambda m: errors.append("console:" + m.text) if m.type == "error" and "404" not in m.text else None)
    pg.goto(url); pg.wait_for_function("window.__ready===true", timeout=15000)
    pg.wait_for_selector("text=Add your RetroAchievements username")
    check(pg.locator("select[aria-label=Show]").input_value() == "retro", "opens on Setup")
    check("Finally" not in pg.inner_text("#qam") and "Steam" not in pg.inner_text("#qam"), "no Finally/Steam wording")
    # import login from file (the shortcut)
    dl = os.path.join(decky.DECKY_USER_HOME, "Downloads"); os.makedirs(dl, exist_ok=True)
    open(os.path.join(dl, "retroachievements.txt"), "w").write("Tester\n%s\n" % KEY)
    pg.click("text=Import login from file"); pg.wait_for_selector("text=The file was deleted.")
    check(not os.path.exists(os.path.join(dl, "retroachievements.txt")), "login file removed after import")
    pg.wait_for_selector("text=Watching Tester", timeout=10000)
    check(pg.locator("input[aria-label='RetroAchievements username']").input_value() == "Tester", "username filled from import")
    check(KEY not in pg.inner_text("#qam"), "key not shown")
    pg.click("text=Check connection"); pg.wait_for_selector("text=Logged in as Tester")
    check("OK Logged in as Tester (1234 points)" in pg.inner_text("#qam"), "connection check")
    check("Rest when no emulator is open" in pg.inner_text("#qam") and "Emulator logs:" in pg.inner_text("#qam"), "new switches and hint info shown")
    (pg.screenshot(path=os.path.join(SHOTS, "setup_tab.png")) if SHOTS else None)
    # live unlock
    time.sleep(1.2); n0 = len(shown)
    mock.unlocks = [unlock(7, hc=1, date="2026-10-07 11:00:00", title="Green Hill Master")]
    deadline = time.time() + 14
    while time.time() < deadline and len(shown) == n0: time.sleep(0.3)
    check(len(shown) == n0 + 1 and shown[-1]["title"] == "Green Hill Master", "toast after unlock")
    # game tab
    pg.select_option("select[aria-label=Show]", "game")
    try: pg.wait_for_selector("h3:text-is('Sonic the Hedgehog')", timeout=15000)
    except Exception: print("ERRORS:", errors); os._exit(1)
    t = pg.inner_text("#qam")
    check("2 of 20 unlocked (10%)" in t, "progress text")
    check(pg.locator("img").count() == 15, "first page shows 15 badges (%d)" % pg.locator("img").count())
    check(pg.evaluate("document.querySelector('img').complete && document.querySelector('img').naturalWidth > 0"), "badge image loads")
    check("Show more (5 left)" in t, "paging")
    pg.click("text=Show more"); check(pg.locator("img").count() == 20, "show more reveals the rest")
    pg.click("button:text-is('Locked')"); check(pg.locator("img").count() == 15 and "Show more (3 left)" in pg.inner_text("#qam"), "locked filter (18 locked, first page of 15)")
    pg.click("button:text-is('Unlocked')"); check(pg.locator("img").count() == 2, "unlocked filter")
    check(pg.evaluate("document.querySelector('img').style.filter") in ("none", ""), "unlocked badge is in colour")
    pg.click("button:text-is('Locked')"); check("grayscale" in pg.evaluate("document.querySelector('img').style.filter"), "locked badge is greyed")
    (pg.screenshot(path=os.path.join(SHOTS, "game_tab.png")) if SHOTS else None)
    pg.click("text=Streets of Rage"); pg.wait_for_selector("h3:text-is('Streets of Rage')", timeout=15000)
    check("0 of 9 unlocked (0%)" in pg.inner_text("#qam"), "switch game")
    # recent tab
    pg.select_option("select[aria-label=Show]", "recent"); pg.wait_for_selector("text=Green Hill Master", timeout=15000)
    check("hardcore" in pg.inner_text("#qam") and pg.locator("img").count() >= 1, "recent unlocks listed with badge")
    (pg.screenshot(path=os.path.join(SHOTS, "recent_tab.png")) if SHOTS else None)
    # other tabs + test button
    for v, exp in (("popup", "Appearance"), ("style", "Colors"), ("sound", "Popup Tests"), ("advanced", "Status")):
        pg.select_option("select[aria-label=Show]", v); pg.wait_for_selector("h3:text-is(\"%s\")" % exp, timeout=5000)
    pg.select_option("select[aria-label=Show]", "sound"); n1 = len(shown); pg.click("text=Test Rare"); time.sleep(1.5)
    check(len(shown) == n1 + 1 and shown[-1]["tier"] == "rare", "test popup button")
    b.close()
check(not errors, "no page errors: %r" % errors)
print("UI HARNESS OK (%d checks), page errors: %d" % (ok, len(errors)))
os._exit(0)
