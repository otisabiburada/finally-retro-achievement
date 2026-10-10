import asyncio, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import KEY, PNG, MockRA, load_plugin, unlock, progress

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOCK = tuple(sys.argv[2].split(",")) if len(sys.argv) > 2 else ()
mock = MockRA()
main, decky, emitted, tmp = load_plugin(ROOT, mock, BLOCK)
state = mock   # compatibility with the checks below
state_unlocks = None

passed = 0
def check(cond, msg):
    global passed
    if not cond: print("FAIL:", msg); sys.exit(1)
    passed += 1

async def main_test():
    shown = []
    async def fake_overlay(payload): shown.append(payload)
    p = main.Plugin()
    p._show_gamescope_overlay = fake_overlay

    # --- pure helpers
    check(main.ra_media_urls("/Badge/1.png")[0].endswith("/Badge/1.png"), "media url")
    check(main.ra_parse_unlocks({"x": 1}) == [] and main.ra_parse_unlocks([1, None, {}]) == [], "parse junk")
    check(main.ra_percent(progress(), "3") == 50.0, "percent")
    check(main.ra_percent({}, "3") is None, "percent none")
    check(main.ra_is_complete(progress(total=3, got=3)) and not main.ra_is_complete(progress(total=3, got=2)), "complete")

    # --- config validation / secrets
    r = await p.set_ra_config({"username": "bad name!", "api_key": KEY}); check(not r["ok"], "bad username rejected")
    r = await p.set_ra_config({"username": "Tester", "api_key": "short"}); check(not r["ok"], "bad key rejected")
    r = await p.set_ra_config({"username": "Tester", "api_key": KEY}); check(r["ok"], "config saved")
    st = await p.get_ra_state()
    check(KEY not in json.dumps(st) and st["key_saved"] and st["key_hint"] == "...6789", "key never returned")
    check(oct(os.stat(main.RA_SETTINGS_FILE).st_mode & 0o777) == "0o600", "key file 0600")
    r = await p.set_ra_config({"username": "Tester"}); check(p._ra_cfg()["api_key"] == KEY, "empty key keeps saved key")

    # --- connection check
    c = await p.ra_check_connection(); check(c["ok"] and "Tester" in c["lines"][0]["text"], "connection ok: %s" % c)

    # --- baseline is silent
    mock.unlocks = [unlock(1, date="2026-10-07 09:00:00")]
    cfg = p._ra_cfg()
    await p._ra_poll_once(cfg); await asyncio.sleep(0.05)
    check(shown == [], "baseline does not toast old unlocks")

    # --- new unlock toasts once, with RA data
    mock.progress["11"] = progress(total=3, got=2, awarded={2: 120})   # 12% -> uncommon
    mock.unlocks = [unlock(1, date="2026-10-07 09:00:00"), unlock(2)]
    await p._ra_poll_once(cfg); await asyncio.sleep(0.05)
    check(len(shown) == 1, "one toast")
    t = shown[0]
    check(t["title"] == "Ach 2" and t["game_name"] == "Sonic the Hedgehog", "title/game")
    check(t["subtitle"] == "Do thing 2" and t["points_text"] == "10 pts", "description only, points in the badge %r / %r" % (t["subtitle"], t.get("points_text")))
    check(abs(t["percent"] - 12.0) < 0.01 and t["tier"] == "uncommon" and t["is_rare"] is False, "rarity from RA %r" % t)
    check(t["icon_path"] and open(t["icon_path"], "rb").read() == PNG, "badge cached")
    check(any(n == "finally_show" for n, _ in emitted), "panel event emitted")
    await p._ra_poll_once(cfg); await p._ra_poll_once(cfg); await asyncio.sleep(0.05)
    check(len(shown) == 1, "no duplicates on later polls")

    # --- softcore + hardcore pair = one toast
    shown.clear()
    mock.unlocks = [unlock(3, hc=0, date="2026-10-07 10:05:00"), unlock(3, hc=1, date="2026-10-07 10:05:01")]
    await p._ra_poll_once(cfg); await asyncio.sleep(0.05)
    check(len(shown) == 1, "hardcore+softcore pair gives one toast (got %d)" % len(shown))

    # --- hardcore only
    shown.clear()
    await p.set_ra_config({"hardcore_only": True}); cfg = p._ra_cfg()
    p._ra_last_ok = time.time(); p._ra_rebaseline = False
    mock.unlocks = [unlock(4, hc=0), unlock(5, hc=1)]
    await p._ra_poll_once(cfg); await asyncio.sleep(0.05)
    check([s["title"] for s in shown] == ["Ach 5"], "hardcore-only skips softcore %r" % [s["title"] for s in shown])
    await p.set_ra_config({"hardcore_only": False}); p._ra_last_ok = time.time(); p._ra_rebaseline = False; cfg = p._ra_cfg()

    # --- mastery toast
    shown.clear()
    mock.progress["11"] = progress(total=3, got=3)
    mock.unlocks = [unlock(6)]
    await p._ra_poll_once(cfg); await asyncio.sleep(2.3)
    check(len(shown) == 2 and shown[1].get("completion") is True and shown[1]["subtitle"] == "Sonic the Hedgehog", "mastery toast after last unlock (%d)" % len(shown))
    shown.clear()
    mock.unlocks = [unlock(7)]
    await p._ra_poll_once(cfg); await asyncio.sleep(2.3)
    check(len(shown) == 1, "mastery toast not repeated within the dedupe window")

    # --- errors: bad key, 500, recovery
    await p.set_ra_config({"username": "Tester", "api_key": "ZZZZZZZZZZZZZZZZZZZZZZZZ"})
    try:
        await p._ra_poll_once(p._ra_cfg()); check(False, "should raise")
    except RuntimeError as e:
        check("refused the username or API key" in str(e), "friendly 401: %s" % e)
    await p.set_ra_config({"api_key": KEY})
    mock.fail = 1
    try:
        await p._ra_poll_once(p._ra_cfg()); check(False, "should raise 500")
    except RuntimeError as e:
        check("HTTP 500" in str(e), "friendly 500")

    # --- test popups use a real recent unlock, tiers follow cutoffs, never touch seen-set
    shown.clear(); seen_before = dict(p._ra_seen)
    mock.unlocks = [unlock(8)]
    for tier in ("common", "uncommon", "rare", "ultra_rare"):
        await p._run_tier_test(tier)
    await asyncio.sleep(0.05)
    check([s["tier"] for s in shown] == [None, "uncommon", "rare", "ultra_rare"] or [s["tier"] for s in shown] == ["common", "uncommon", "rare", "ultra_rare"], "tier tests %r" % [s["tier"] for s in shown])
    check(shown[0]["title"] == "Ach 8" and p._ra_seen == seen_before, "tests use real unlock and don't touch bookkeeping")
    shown.clear(); mock.unlocks = []
    await p.test_popup_rare(); await p.test_completion_popup(); await asyncio.sleep(0.05)
    check(shown[0]["title"] == "Sample Achievement" and shown[1].get("completion"), "sample fallback + completion test")

    # --- the loop itself: needs_setup, then watching, wake on config change
    p2 = main.Plugin(); shown2 = []
    async def fo2(payload): shown2.append(payload)
    p2._show_gamescope_overlay = fo2
    os.remove(main.RA_SETTINGS_FILE)
    task = asyncio.create_task(p2._watch_ra()); await asyncio.sleep(0.3)
    check(p2._ra_status == "needs_setup", "loop waits for setup")
    mock.unlocks = [unlock(20, date="2026-10-07 08:00:00")]
    await p2.set_ra_config({"username": "Tester", "api_key": KEY, "poll_seconds": 3})
    await asyncio.sleep(1.0)
    check(p2._ra_status == "watching" and shown2 == [], "loop starts watching and baselines silently (%s)" % p2._ra_status)
    mock.unlocks.append(unlock(21))
    await asyncio.sleep(3.6)
    check([s["title"] for s in shown2] == ["Ach 21"], "loop shows new unlock within one poll interval %r" % [s["title"] for s in shown2])
    p2._stop_event.set(); p2._ra_wake.set(); await asyncio.wait_for(task, 5)
    print("ALL %d CHECKS PASSED" % passed)

asyncio.run(main_test())
mock.stop()
