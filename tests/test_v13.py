"""v1.3: keep-alive connection reuse, curl fallback, offline classification."""
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import KEY, MockRA, load_plugin

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
    check(main.RA_POLL_RANGE[0] == 10, "default poll is 10 s")
    p = main.Plugin()
    cfg = {"username": "Tester", "api_key": KEY}
    call = lambda: p._ra_api("API_GetUserRecentAchievements.php", {"u": "Tester", "m": 5}, cfg)
    for _ in range(4):
        await call()
    check(p._ra_keepalive_ok, "keep-alive stays on")
    check(mock.connections == 1, "4 requests over %d connection(s)" % mock.connections)
    for conn, _s in list(p._ra_conn.values()):
        conn.sock.close()
    check(await call() is not None, "recovers from a dead connection")
    p._ra_keepalive_ok = False
    before = mock.connections
    check(await call() is not None and mock.connections == before + 1, "curl fallback works")
    p._ra_keepalive_ok = True
    mock.fail = 1
    try:
        await call(); check(False, "500 should raise")
    except main.RaOfflineError:
        check(False, "500 is not offline")
    except RuntimeError:
        check(True, "server error raises RuntimeError")
    check(await call() is not None, "connection still usable after an error status")
    real = main.RA_API_BASE
    main.RA_API_BASE = "http://127.0.0.1:1/API/"
    try:
        await call(); check(False, "should be offline")
    except main.RaOfflineError:
        check(True, "refused connection = offline")
    main.RA_API_BASE = real
    await p._unload()
    check(not p._ra_conn, "unload closes the connection")
    print("V1.3: ALL %d CHECKS PASSED" % passed)


asyncio.run(run())
