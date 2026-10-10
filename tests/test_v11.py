"""v1.1 features: smart polling, log hints, offline handling, game tab data, login import."""
import asyncio, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import KEY, MockRA, load_plugin, unlock, progress

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOCK = tuple(sys.argv[2].split(",")) if len(sys.argv) > 2 else ()
mock = MockRA()
main, decky, emitted, tmp = load_plugin(ROOT, mock, BLOCK)
passed = 0


def check(cond, msg):
    global passed
    if not cond:
        print("FAIL:", msg); sys.exit(1)
    passed += 1


async def run():
    # ---- ra_next_interval -------------------------------------------------
    f = main.ra_next_interval
    check(f(6, True, True, None, 999, 0) == (6.0, "active"), "emulator running = fast")
    check(f(6, True, False, None, 999, 0) == (24.0, "idle") or f(6, True, False, None, 999, 0) == (20.0, "idle"), "idle slows down")
    check(f(6, True, False, None, 999, 0)[0] >= 20, "idle >= 20s")
    check(f(6, True, False, None, 10, 0)[1] == "active", "fast for the first minute")
    check(f(6, True, False, 30, 999, 0)[1] == "active", "fast shortly after an unlock")
    check(f(6, True, False, 999, 999, 0)[1] == "idle", "idle long after an unlock")
    check(f(6, False, False, None, 999, 0) == (6.0, "active"), "smart polling off = always fast")
    check(f(6, True, False, None, 999, 5) == (1.0, "burst"), "burst polls every second")
    check(f(30, True, False, None, 999, 0)[0] == 60.0, "idle capped at 60s")

    # ---- emulator process scan (fake /proc) ------------------------------
    proc = os.path.join(tmp, "proc"); os.makedirs(proc)
    def fake(pid, comm, cmd=""):
        d = os.path.join(proc, str(pid)); os.makedirs(d)
        open(os.path.join(d, "comm"), "w").write(comm + "\n"); open(os.path.join(d, "cmdline"), "wb").write(cmd.encode().replace(b" ", b"\0"))
    fake(1, "systemd"); fake(2, "steam"); fake(3, "bash")
    check(not main.ra_emulator_running(proc), "no emulator -> False")
    fake(4, "pcsx2-qt"); check(main.ra_emulator_running(proc), "pcsx2-qt detected")
    import shutil; shutil.rmtree(os.path.join(proc, "4"))
    fake(5, "bwrap", "bwrap --app /app/bin/retroarch -L core.so"); check(main.ra_emulator_running(proc), "flatpak retroarch via cmdline")
    check(not main.ra_emulator_running(os.path.join(tmp, "nope")), "missing /proc is safe")

    # ---- login file parsing ----------------------------------------------
    P = main.ra_parse_login_text
    check(P("Tester\n%s\n" % KEY) == ("Tester", KEY), "two lines")
    check(P("username=Tester\nkey = %s" % KEY) == ("Tester", KEY), "key=value")
    check(P("# my login\nUser: Tester\nWeb API Key: %s" % KEY) == ("Tester", KEY), "labels with spaces")
    check(P("%s\n" % KEY) == (None, KEY), "key only")
    check(P("Tester\nshort") == ("Tester", None) or P("Tester\nshort")[1] is None, "bad key rejected")
    check(P("bad name!\n%s" % KEY)[0] is None, "bad username rejected")
    check(P("") == (None, None), "empty")

    # ---- game parsing -----------------------------------------------------
    g = main.ra_parse_game({**progress(total=3, got=1), "Achievements": {
        "1": {"ID": 1, "Title": "B", "Description": "d", "Points": 5, "BadgeName": "11", "DisplayOrder": 2, "NumAwarded": 100, "DateEarned": "2026-01-01 10:00:00"},
        "2": {"ID": 2, "Title": "A", "Description": "d", "Points": 10, "BadgeName": "12", "DisplayOrder": 1, "NumAwarded": 10, "DateEarnedHardcore": "2026-01-02 10:00:00", "DateEarned": "2026-01-02 10:00:00"},
        "3": {"ID": 3, "Title": "C", "Description": "d", "Points": 1, "BadgeName": "13", "DisplayOrder": 3, "NumAwarded": 0}}})
    check([a["title"] for a in g["achievements"]] == ["A", "B", "C"], "sorted by display order")
    check([a["unlocked"] for a in g["achievements"]] == [True, True, False] and g["achievements"][0]["hardcore"], "unlocked/hardcore flags")
    check(g["achievements"][0]["percent"] == 1.0 and g["achievements"][2]["percent"] == 0.0, "rarity percent")
    check(main.ra_parse_game({}) is None and main.ra_parse_game([1]) is None, "bad game payload")

    # ---- plugin with mock ---------------------------------------------------
    shown = []
    p = main.Plugin()
    async def fo(payload): shown.append(payload)
    p._show_gamescope_overlay = fo
    r = await p.set_ra_config({"username": "Tester", "api_key": KEY}); check(r["ok"], "saved")
    st = await p.get_ra_state()
    check(st["smart_polling"] is True and st["mode"] == "active", "state has smart polling fields")

    # game tab data
    mock.recent_games = [{"GameID": 11, "Title": "Sonic the Hedgehog", "ConsoleName": "Mega Drive", "NumPossibleAchievements": 9, "NumAchieved": 2},
                         {"GameID": 12, "Title": "Streets of Rage", "ConsoleName": "Mega Drive", "NumPossibleAchievements": 20, "NumAchievedHardcore": 5}]
    mock.progress["11"] = progress(total=9, got=2, awarded={1: 10})
    mock.progress["12"] = {**progress(total=9, got=2), "ID": 12, "Title": "Streets of Rage"}
    r = await p.get_ra_game()
    check(r["ok"] and r["game"]["title"] == "Sonic the Hedgehog" and len(r["game"]["achievements"]) == 9, "game tab: latest game (%r)" % {k: r[k] for k in r if k != "game"})
    check(r["game"]["achievements"][0]["badge_url"].startswith("http://127.0.0.1"), "badge urls present")
    check([x["game_id"] for x in r["recent"]] == [11, 12] and r["recent"][1]["unlocked"] == 5, "recent games list")
    r = await p.get_ra_game(12); check(r["ok"] and r["game"]["title"] == "Streets of Rage", "game tab: chosen game")
    r = await p.get_ra_game("junk; rm -rf"); check(r["ok"], "junk game id falls back safely")
    mock.unlocks = [unlock(1, date="2026-10-07 09:00:00"), unlock(2, date="2026-10-07 09:30:00")]
    r = await p.get_ra_recent(); check(r["ok"] and [i["title"] for i in r["items"]] == ["Ach 2", "Ach 1"], "recent unlocks newest first")

    # login import
    dl = os.path.join(decky.DECKY_USER_HOME, "Downloads"); os.makedirs(dl)
    r = await p.ra_import_login_file(); check(not r["ok"] and "retroachievements.txt" in r["error"], "no file -> helpful message")
    open(os.path.join(dl, "retroachievements.txt"), "w").write("Someone\nnot-a-key\n")
    r = await p.ra_import_login_file(); check(not r["ok"] and "no valid API key" in r["error"], "bad file rejected")
    check(os.path.exists(os.path.join(dl, "retroachievements.txt")), "bad file is left alone")
    open(os.path.join(dl, "retroachievements.txt"), "w").write("Someone\n%s\n" % KEY)
    r = await p.ra_import_login_file()
    check(r["ok"] and r["removed"] and not os.path.exists(os.path.join(dl, "retroachievements.txt")), "import ok and file deleted")
    st = await p.get_ra_state(); check(st["username"] == "Someone" and st["key_saved"] and KEY not in json.dumps(st), "import saved login, key not exposed")
    await p.set_ra_config({"username": "Tester"})

    # ---- log hints ----------------------------------------------------------
    logs = os.path.join(decky.DECKY_USER_HOME, ".config", "retroarch", "logs"); os.makedirs(logs)
    log = os.path.join(logs, "retroarch.log"); open(log, "w").write("old line: achievement unlocked long ago\n")
    off = {}
    check(p._ra_scan_hints(off, True) is False and off[log] > 0, "first scan only records the end of the log")
    check(p._ra_scan_hints(off, False) is False, "nothing new")
    open(log, "a").write("[INFO] frame 100 ok\n"); check(p._ra_scan_hints(off, False) is False, "unrelated line ignored")
    open(log, "a").write("[INFO] [RCHEEVOS] Awarded achievement 123: Foo\n"); check(p._ra_scan_hints(off, False) is True, "achievement line is a hint")
    open(log, "w").write("x\n"); check(p._ra_scan_hints(off, False) is False and off[log] == 2, "rotated log handled")

    # ---- loop: idle mode + hint wakes it, offline recovery ------------------
    p2 = main.Plugin(); shown2 = []
    async def fo2(payload): shown2.append(payload)
    p2._show_gamescope_overlay = fo2
    async def no_emu(): return False
    p2._ra_emulator_cached = no_emu
    p2._ra_started -= 1000                      # long past the startup fast period
    await p2.set_ra_config({"username": "Tester", "api_key": KEY, "poll_seconds": 6})
    mock.unlocks = [unlock(30, date="2026-10-07 08:00:00")]
    t1 = asyncio.create_task(p2._watch_ra()); t2 = asyncio.create_task(p2._watch_ra_hints())
    await asyncio.sleep(1.5)
    check(p2._ra_status == "watching" and p2._ra_mode == "idle", "no emulator -> idle mode (%s/%s)" % (p2._ra_status, p2._ra_mode))
    hits_before = len(mock.hits)
    mock.unlocks.append(unlock(31))             # unlock happens while idle (next poll would be ~24s away)
    open(log, "a").write("[INFO] [RCHEEVOS] Awarded achievement 31\n")
    t0 = time.time()
    while time.time() - t0 < 8 and not shown2:
        await asyncio.sleep(0.2)
    check([s["title"] for s in shown2] == ["Ach 31"], "log hint triggered an immediate poll (%.1fs)" % (time.time() - t0))
    check(time.time() - t0 < 5, "hinted toast arrived within 5s while idle")
    check(p2._ra_hint_count >= 1 and p2._ra_hint_files_seen >= 1, "hint counters")
    await asyncio.sleep(0.3)
    check(p2._ra_mode == "active", "unlock switches back to fast polling")

    real_base = main.RA_API_BASE
    main.RA_API_BASE = "http://127.0.0.1:1/API/"        # nothing listens there
    p2._ra_wake.set(); await asyncio.sleep(1.5)
    check(p2._ra_status == "offline" and "catch up" in (p2._ra_error or ""), "offline state (%s)" % p2._ra_status)
    main.RA_API_BASE = real_base
    mock.unlocks.append(unlock(32))                     # unlocked while offline
    for _ in range(40):
        p2._ra_wake.set(); await asyncio.sleep(0.5)
        if any(s["title"] == "Ach 32" for s in shown2): break
    check(any(s["title"] == "Ach 32" for s in shown2) and p2._ra_status == "watching", "offline unlock shown after reconnect")
    p2._stop_event.set(); p2._ra_wake.set()
    await asyncio.wait_for(asyncio.gather(t1, t2), 6)
    print("V1.1: ALL %d CHECKS PASSED" % passed)


asyncio.run(run())
mock.stop()
