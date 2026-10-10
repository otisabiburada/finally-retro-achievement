"""Shared test scaffolding: a stub `decky` module, a mock RetroAchievements
server, and a loader that points the plugin at both."""
import http.server, importlib.util, json, logging, os, struct, sys, tempfile, threading, types, urllib.parse, zlib

KEY = "ABCDEF0123456789abcdef0123456789"


def make_png(w=64, h=64):
    raw = b"".join(b"\x00" + b"".join(bytes([(x * 4) % 256, (y * 4) % 256, 120]) for x in range(w)) for y in range(h))

    def chunk(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


PNG = make_png()


class MockRA:
    def __init__(self):
        self.unlocks, self.progress, self.hits, self.fail = [], {}, [], 0
        self.recent_games = []
        self.connections = 0
        mock = self

        class H(http.server.BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *a):
                pass

            def setup(self):
                mock.connections += 1
                super().setup()

            def end_headers(self):
                self.send_header("Content-Length", str(getattr(self, "_len", 0)))
                self._has_len = False
                self._len = 0
                super().end_headers()

            def do_GET(self):
                u = urllib.parse.urlparse(self.path)
                q = urllib.parse.parse_qs(u.query)
                mock.hits.append(u.path)
                if u.path.startswith(("/Badge/", "/Images/")):
                    self.send_response(200); self.send_header("Content-Type", "image/png"); self._len = len(PNG); self.end_headers()
                    self.wfile.write(PNG); return
                if mock.fail:
                    mock.fail -= 1; self.send_response(500); self.end_headers(); return
                if q.get("y", [""])[0] != KEY:
                    self.send_response(401); self._len = 30; self.end_headers(); self.wfile.write(b'{"message":"Unauthenticated."}'); return
                name = u.path.rsplit("/", 1)[-1]
                if name == "API_GetUserRecentAchievements.php":
                    body = mock.unlocks
                elif name == "API_GetGameInfoAndUserProgress.php":
                    body = mock.progress.get(q["g"][0], {})
                elif name == "API_GetUserProfile.php":
                    body = {"User": q["u"][0], "TotalPoints": 1234, "RichPresenceMsg": "Playing Sonic"}
                elif name == "API_GetUserRecentlyPlayedGames.php":
                    body = mock.recent_games
                else:
                    self.send_response(404); self.end_headers(); return
                data = json.dumps(body).encode()
                self.send_response(200); self.send_header("Content-Type", "application/json"); self._len = len(data); self.end_headers()
                self.wfile.write(data)

        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def stop(self):
        self.server.shutdown()


def load_plugin(root, mock, block=()):
    """Import <root>/main.py with a stub decky and constants aimed at tmp dirs and the mock."""
    tmp = tempfile.mkdtemp(prefix="rat_")
    emitted = []
    decky = types.ModuleType("decky")
    logging.basicConfig(level=logging.WARNING)
    decky.logger = logging.getLogger("decky")
    decky.DECKY_PLUGIN_SETTINGS_DIR = decky.DECKY_PLUGIN_RUNTIME_DIR = decky.DECKY_PLUGIN_LOG_DIR = tmp
    decky.DECKY_USER_HOME = os.path.join(tmp, "home")
    os.makedirs(decky.DECKY_USER_HOME, exist_ok=True)
    decky.DECKY_PLUGIN_DIR = root

    async def _emit(name, payload=None):
        emitted.append((name, payload))

    decky.emit = _emit
    sys.modules["decky"] = decky
    for name in block:                       # simulate Decky's stripped Python
        sys.modules[name] = None
    spec = importlib.util.spec_from_file_location("main", os.path.join(root, "main.py"))
    main = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main)
    sdir = os.path.join(tmp, "s")
    main.RA_API_BASE = "http://127.0.0.1:%d/API/" % mock.port
    main.RA_MEDIA_HOSTS = ("http://127.0.0.1:%d" % mock.port,)
    main.FINALLY_SETTINGS_DIR = sdir
    main.FINALLY_SETTINGS_FILE = os.path.join(sdir, "settings.json")
    main.RA_SETTINGS_FILE = os.path.join(sdir, "retro.json")
    main.RA_ICON_CACHE_DIR = os.path.join(sdir, "ra-icons")
    main.FINALLY_USER_SOUNDS_DIR = os.path.join(sdir, "sounds")
    return main, decky, emitted, tmp


def unlock(i, hc=0, gid=11, date=None, title=None):
    return {"Date": date or "2026-10-07 10:00:%02d" % i, "HardcoreMode": hc, "AchievementID": i,
            "Title": title or "Ach %d" % i, "Description": "Do thing %d" % i, "Points": 10, "TrueRatio": 20,
            "BadgeName": "9%d" % i, "BadgeURL": "/Badge/9%d.png" % i, "GameTitle": "Sonic the Hedgehog",
            "GameID": gid, "ConsoleName": "Mega Drive", "GameIcon": "/Images/0001.png"}


def progress(total=3, got=1, players=1000, awarded=None):
    awarded = awarded or {}
    return {"ID": 11, "Title": "Sonic the Hedgehog", "ConsoleName": "Mega Drive", "NumAchievements": total,
            "NumAwardedToUser": got, "NumAwardedToUserHardcore": 0, "NumDistinctPlayers": players,
            "ImageIngame": "/Images/0002.png",
            "Achievements": {str(i): {"ID": i, "Title": "Ach %d" % i, "Description": "Do thing %d" % i, "Points": 10,
                                      "BadgeName": "9%d" % i, "DisplayOrder": i, "NumAwarded": awarded.get(i, 500)}
                             for i in range(1, 10)}}
