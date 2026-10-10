"""v1.2: points badge text and RetroPoints-weighted rarity."""
import asyncio, os, sys
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


def u(i, points=10, true_points=20, hc=0):
    row = unlock(i, hc=hc); row["Points"] = points; row["TrueRatio"] = true_points
    return row


async def run():
    # ---- pure helpers
    item = {"points": 25, "true_ratio": 160, "hardcore": False}
    check(main.ra_points_text(item, True, False) == "25 pts", "points only")
    check(main.ra_points_text(item, True, True) == "25 pts (160 RP)", "points with RetroPoints in weighted mode")
    check(main.ra_points_text({**item, "hardcore": True}, True, True) == "25 pts (160 RP) HC", "hardcore marker")
    check(main.ra_points_text({**item, "hardcore": True}, True, False) == "25 pts HC", "hardcore marker, percent mode")
    check(main.ra_points_text(item, False, True) == "" and main.ra_points_text({"points": 0}, True, False) == "", "off / zero points -> nothing")
    check(main.ra_points_text({"points": 25, "true_ratio": 0}, True, True) == "25 pts", "no RP known -> plain")
    cfg = {"ratio_uncommon": 3.0, "ratio_rare": 8.0, "ratio_ultra": 25.0}
    W = lambda pts, tp, en=True: main.ra_weighted_tier({"points": pts, "true_ratio": tp}, cfg, en)
    check(W(10, 20) == "common" and W(10, 30) == "uncommon" and W(10, 79) == "uncommon", "common/uncommon boundary")
    check(W(10, 80) == "rare" and W(10, 249) == "rare" and W(10, 250) == "ultra_rare", "rare/ultra boundaries")
    check(W(10, 0) is None and W(0, 50) is None and W(10, 300, False) is None, "unknown / disabled -> None (fall back)")

    # ---- config
    p = main.Plugin(); shown = []
    async def fo(payload): shown.append(payload)
    p._show_gamescope_overlay = fo
    await p.set_ra_config({"username": "Tester", "api_key": KEY})
    st = await p.get_ra_state()
    check(st["rarity_source"] == "percent" and st["ratio_uncommon"] == 3.0, "defaults")
    r = await p.set_ra_config({"rarity_source": "weighted", "ratio_uncommon": 9, "ratio_rare": 4, "ratio_ultra": 1000})
    st = r["state"]
    check(st["rarity_source"] == "weighted" and (st["ratio_uncommon"], st["ratio_rare"], st["ratio_ultra"]) == (4.0, 9.0, 100.0),
          "cutoffs sorted and clamped %r" % [st["ratio_uncommon"], st["ratio_rare"], st["ratio_ultra"]])
    await p.set_ra_config({"rarity_source": "nonsense", "ratio_rare": "abc"})
    check((await p.get_ra_state())["rarity_source"] == "weighted", "bad values ignored")
    await p.set_ra_config({"ratio_uncommon": 3, "ratio_rare": 8, "ratio_ultra": 25})

    # ---- weighted tiers end to end (progress says 50% for everything, so percent mode would say "common")
    mock.progress["11"] = progress(total=9, got=1, awarded={i: 500 for i in range(1, 10)})
    cfg = p._ra_cfg(); mock.unlocks = []
    await p._ra_poll_once(cfg)                       # baseline
    mock.unlocks = [u(1, 10, 20), u(2, 10, 40), u(3, 10, 120), u(4, 10, 400)]
    await p._ra_poll_once(cfg); await asyncio.sleep(0.05)
    check([s["tier"] for s in shown] == ["common", "uncommon", "rare", "ultra_rare"], "weighted tiers %r" % [s["tier"] for s in shown])
    check([s["is_rare"] for s in shown] == [False, False, True, True], "is_rare follows the tier")
    check(shown[2]["points_text"] == "10 pts (120 RP)", "badge shows RetroPoints %r" % shown[2]["points_text"])
    check(shown[0]["subtitle"] == "Do thing 1", "subtitle is the description only")

    # ---- missing TrueRatio falls back to the players-% tier
    shown.clear()
    mock.progress["11"] = progress(total=9, got=1, awarded={5: 5})       # 0.5% of 1000 players -> ultra rare by percent
    mock.unlocks.append(u(5, 10, 0))
    await p._ra_poll_once(cfg); await asyncio.sleep(0.05)
    check(len(shown) == 1 and shown[0]["tier"] == "ultra_rare" and shown[0]["points_text"] == "10 pts", "fallback to percent tier")

    # ---- percent mode ignores TrueRatio
    shown.clear()
    await p.set_ra_config({"rarity_source": "percent"}); cfg = p._ra_cfg()
    mock.progress["11"] = progress(total=9, got=1, awarded={6: 500})
    mock.unlocks.append(u(6, 10, 400))
    await p._ra_poll_once(cfg); await asyncio.sleep(0.05)
    check(shown[0]["tier"] == "common" and shown[0]["points_text"] == "10 pts", "percent mode: tier from players %, no RP in badge")

    # ---- show_points off
    shown.clear()
    await p.set_ra_config({"show_points": False}); cfg = p._ra_cfg()
    mock.unlocks.append(u(7, 10, 20)); await p._ra_poll_once(cfg); await asyncio.sleep(0.05)
    check(shown[0]["points_text"] == "", "no points text when switched off")
    await p.set_ra_config({"show_points": True}); cfg = p._ra_cfg()

    # ---- test popups: forced tier, badge still shows points
    shown.clear(); mock.unlocks = [u(8, 25, 160)]
    await p.set_ra_config({"rarity_source": "weighted"})
    for tier in ("common", "uncommon", "rare", "ultra_rare"):
        await p._run_tier_test(tier)
    await asyncio.sleep(0.05)
    check([s["tier"] for s in shown] == ["common", "uncommon", "rare", "ultra_rare"], "tests force each tier in weighted mode")
    check(all(s["points_text"] == "25 pts (160 RP)" for s in shown), "tests show the badge")

    # ---- the overlay helper really receives the points (env passed to the subprocess)
    captured = {}
    class FakeProc:
        returncode = 0
        async def communicate(self): return b"", b""
    async def fake_exec(*args, **kwargs):
        captured["env"] = kwargs.get("env"); return FakeProc()
    async def noop(*a, **k): return None
    real_exec = asyncio.create_subprocess_exec
    p3 = main.Plugin(); p3._play_sound = noop; p3._systemctl_user = noop
    asyncio.create_subprocess_exec = fake_exec
    try:
        await p3._show_gamescope_overlay({"title": "T", "subtitle": "A long description", "is_rare": False, "tier": None, "points_text": "25 pts HC",
                                          "percent": 3.2, "icon_path": None, "game_name": "G", "settings_appid": None})
    finally:
        asyncio.create_subprocess_exec = real_exec
    env = captured.get("env") or {}
    check(env.get("FINALLY_POINTS") == "25 pts HC" and env.get("FINALLY_SUBTITLE") == "A long description" and env.get("FINALLY_PERCENT") == "3.20",
          "overlay env has points, description and percent: %r" % {k: v for k, v in env.items() if k.startswith("FINALLY_P") or k == "FINALLY_SUBTITLE"})
    print("V1.2: ALL %d CHECKS PASSED" % passed)


asyncio.run(run())
mock.stop()
