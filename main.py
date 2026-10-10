import asyncio
import datetime as dt
import glob
import json
import os
import random
import re
import socket
import subprocess
import threading
import time
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Set, Tuple

import decky

FINALLY_OVERLAY_HELPER_NAME = "finally_gamescope_overlay.py"
STEAMWORKS_PYTHON = "/usr/bin/python3"
AUDIO_PREROLL_SECONDS = 0.35
FINALLY_SETTINGS_DIR = "/home/deck/homebrew/settings/RetroAchievements Toasts"
FINALLY_SETTINGS_FILE = os.path.join(FINALLY_SETTINGS_DIR, "settings.json")
OVERLAY_SCRIPT_NAME = "finally_gamescope_overlay.py"
DIAGNOSE_SCRIPT_NAME = "finally_diagnose.py"
DRAWING_LAYER_NAME = "finally_cairo_ctypes.py"
SOUNDS_DIR_NAME = "sounds"
# One sound per tier plus the 100%-completion popup. The defaults reproduce
# the old two-sound behaviour: the "normal" sound for common and uncommon, the
# "rare" sound for rare, ultra rare and completion.
SOUND_SLOTS = ("common", "uncommon", "rare", "ultra_rare", "completion")
DEFAULT_NORMAL_SOUND = "unlock_preroll.wav"
DEFAULT_RARE_SOUND = "rare_preroll.wav"
# Where your own sound files go. It lives in the settings folder (not the plugin
# folder) so updating or reinstalling the plugin never deletes them.
FINALLY_USER_SOUNDS_DIR = os.path.join(FINALLY_SETTINGS_DIR, "sounds")
SOUND_EXTENSIONS = (".wav", ".flac", ".ogg", ".oga", ".mp3", ".aiff", ".aif")
SOUND_MAX_BYTES = 10 * 1024 * 1024
SOUND_MAX_PLAY_SECONDS = 20.0         # a long file is cut off after this
DEFAULT_SETTINGS = {
    "sound_common": DEFAULT_NORMAL_SOUND,
    "sound_uncommon": DEFAULT_NORMAL_SOUND,
    "sound_rare": DEFAULT_RARE_SOUND,
    "sound_ultra_rare": DEFAULT_RARE_SOUND,
    "sound_completion": DEFAULT_RARE_SOUND,
    "overlay_size_percent": 50,
    "volume_percent": 50,
    "overlay_position": "bottom_center",
    "overlay_template": "xbox_modern",
    "label_font_size": 13,
    "title_font_size": 26,
    "subtitle_font_size": 18,
    "normal_gradient_start": "hsla(134, 58%, 25%, 0.94)",
    "normal_gradient_end": "hsla(134, 50%, 14%, 0.94)",
    "rare_gradient_start": "hsla(45, 90%, 42%, 0.95)",
    "rare_gradient_end": "hsla(38, 70%, 22%, 0.95)",
    "normal_circle_color": "hsla(134, 62%, 51%, 1)",
    "rare_circle_color": "hsla(45, 95%, 58%, 1)",
    "duration_seconds": 5.8,
    "icon_glow_enabled": True,
    "icon_glow_intensity": 50,
    "ring_size": 50,
    "gradient_direction": "vertical",
    "glow_normal_enabled": False,
    "icon_frame_ring_enabled": True,
    "icon_gradient_enabled": False,
    "show_percent": True,
    "placeholder_icon": "auto",
    "game_art_gradient_enabled": False,
    "completion_toast_enabled": True,
    "completion_title": "completionist",
    "percent_size": 100,
    "percent_position": "bottom_right",
    "rarity_tiers_enabled": True,
    "test_with_game_data": True,
    "template_fx_enabled": True,
    "template_colors_enabled": False,
    "tier_uncommon_cutoff": 25,
    "tier_rare_cutoff": 10,
    "tier_ultra_cutoff": 1.0,
}
# Kept in sync with DURATION_RANGE in src/finallyThemes.ts.
DURATION_RANGE = (5.8, 3.0, 12.0)  # (default, lo, hi), in seconds
GRADIENT_DIRECTIONS = ("vertical", "left_right", "right_left", "solid")
# The 100%-complete ("Mythic") toast. Its template is deliberately not in
# OVERLAY_TEMPLATES / the template picker -- it only ever appears on completion.
COMPLETION_TEMPLATE = "mythic_completion"
# Big-text name for the 100%-complete popup, chosen in the panel.
COMPLETION_TITLES = {
    "completionist": "Completionist",
    "legendary": "Legendary Achievement unlocked",
    "crowned": "Crowned",
}
COMPLETION_TITLE_DEFAULT = "completionist"
# Rarity-tier cutoffs (% of players who have the achievement), each a
# (default, lo, hi). Kept in sync with TIER_CUTOFF_RANGES in src/finallyThemes.ts.
TIER_ULTRA_RANGE = (1.0, 0.5, 5.0)
TIER_RARE_RANGE = (10, 2, 25)
TIER_UNCOMMON_RANGE = (25, 5, 60)
# Kept in sync with PERCENT_SIZE_RANGE in src/finallyThemes.ts (a % of normal).
PERCENT_SIZE_RANGE = (100, 70, 150)  # (default, lo, hi)
# Where the unlock-percentage badge sits; "top_right" also lets descriptions use two lines.
PERCENT_POSITIONS = ("bottom_right", "top_right")
COMPLETION_MIN_SECONDS = 9.0
COMPLETION_DELAY_SECONDS = 2.0
COMPLETION_DEDUPE_SECONDS = 120.0
# "auto" = original behavior (game icon if no achievement icon, else the gear badge).
PLACEHOLDER_ICON_STYLES = ("auto", "trophy", "game_icon")
OVERLAY_POSITIONS = (
    "top_left",
    "top_center",
    "top_right",
    "bottom_left",
    "bottom_center",
    "bottom_right",
)
# Kept in sync with the TEMPLATES dict in finally_gamescope_overlay.py -- these
# are just the valid keys for validation; the actual look of each one lives
# in the renderer.
OVERLAY_TEMPLATES = (
    "xbox_modern",
    "playstation_trophy",
    "switch_bold",
    "steam_flat",
    "material_minimal",
    "retro_arcade",
    "chat_toast",
    "cyber_glass",
    "xbox_360_classic",
    "xbox_360_v2",
    "xbox_360_v2_square",
    "win11_glass",
    "discord_bar",
    "vaporwave",
    "light_card",
    "wood_plaque",
    "terminal_hacker",
    "game_art",
)
# (default, min, max) -- kept in sync with the clamping in
# finally_gamescope_overlay.py's own env-var parsing, which is a second line
# of defense if a stale/edited settings file ever slips past this.
FONT_SIZE_RANGES = {
    "label_font_size": (13, 9, 18),
    "title_font_size": (26, 18, 34),
    "subtitle_font_size": (18, 12, 22),
}


_VDF_DICT, _VDF_STRING, _VDF_INT32, _VDF_FLOAT32, _VDF_COLOR, _VDF_UINT64, _VDF_END = 0x00, 0x01, 0x02, 0x03, 0x06, 0x07, 0x08
_ICON_FILE_RE = re.compile(r"^[0-9a-fA-F]{20,64}\.(?:jpg|jpeg|png)$")


def _vdf_parse(data: bytes, offset: int = 0, depth: int = 0) -> Tuple[Dict[str, Any], int]:
    if depth > 64:
        raise ValueError("binary vdf nesting too deep")
    result: Dict[str, Any] = {}
    while True:
        if offset >= len(data):
            raise ValueError("unexpected end of binary vdf")
        kind = data[offset]
        offset += 1
        if kind == _VDF_END:
            return result, offset
        end = data.index(b"\x00", offset)
        key = data[offset:end].decode("utf-8", errors="ignore")
        offset = end + 1
        if kind == _VDF_DICT:
            value, offset = _vdf_parse(data, offset, depth + 1)
        elif kind == _VDF_STRING:
            end = data.index(b"\x00", offset)
            value = data[offset:end].decode("utf-8", errors="ignore")
            offset = end + 1
        elif kind in (_VDF_INT32, _VDF_COLOR, _VDF_FLOAT32):
            value = int.from_bytes(data[offset:offset + 4], "little", signed=True)
            offset += 4
        elif kind == _VDF_UINT64:
            value = int.from_bytes(data[offset:offset + 8], "little", signed=False)
            offset += 8
        else:
            raise ValueError(f"unknown binary vdf type {kind:#x}")
        result[key] = value


def _schema_icon_files(node: Any, colored: Dict[str, str], gray: Dict[str, str]) -> None:
    """Walks a parsed schema and collects {achievement id: colored icon file}
    (and the gray ones) from every node shaped like
    {"name": "<id>", "display": {"icon": "<hash>.jpg", "icon_gray": "..."}}."""
    if not isinstance(node, dict):
        return
    name = node.get("name")
    display = node.get("display") if isinstance(node.get("display"), dict) else node
    icon, icon_gray = display.get("icon"), display.get("icon_gray")
    if isinstance(name, str) and name and isinstance(icon, str) and _ICON_FILE_RE.match(icon):
        if not (isinstance(icon_gray, str) and icon_gray.lower() == icon.lower()):    # a "colored" icon identical to the gray one is useless
            colored.setdefault(name, icon)
            if isinstance(icon_gray, str) and _ICON_FILE_RE.match(icon_gray):
                gray.setdefault(name, icon_gray)
    for value in node.values():
        if isinstance(value, dict):
            _schema_icon_files(value, colored, gray)


# ---------------------------------------------------------------------------
# RetroAchievements support (pure helpers; no Decky needed to test them)
# ---------------------------------------------------------------------------
RA_API_BASE = "https://retroachievements.org/API/"
RA_MEDIA_HOSTS = ("https://media.retroachievements.org", "https://retroachievements.org")
RA_SETTINGS_FILE = os.path.join(FINALLY_SETTINGS_DIR, "retro.json")
RA_ICON_CACHE_DIR = os.path.join(FINALLY_SETTINGS_DIR, "ra-icons")
RA_POLL_RANGE = (10, 3, 60)  # (default, lo, hi) seconds
RA_HTTP_TIMEOUT_SECONDS = 12
RA_KEEPALIVE_SECONDS = 25  # reuse one connection if the last request was this recent
RA_DEFAULTS = {
    "username": "",
    "api_key": "",
    "enabled": True,
    "poll_seconds": RA_POLL_RANGE[0],
    "show_points": True,
    "hardcore_only": False,
    "smart_polling": True,
    "rarity_source": "percent",       # "percent" (share of players) or "weighted" (RetroPoints ratio)
    "ratio_uncommon": 3.0,
    "ratio_rare": 8.0,
    "ratio_ultra": 25.0,
}
RA_RATIO_RANGE = (1.0, 100.0)         # lo, hi for the three weighted cutoffs
RA_RARITY_SOURCES = ("percent", "weighted")
RA_USERNAME_RE = re.compile(r"^[A-Za-z0-9_.\-]{1,40}$")
RA_KEY_RE = re.compile(r"^[A-Za-z0-9]{16,64}$")
RA_CROSS_MODE_SECONDS = 120.0   # same achievement in softcore+hardcore = one toast
RA_SEEN_LIMIT = 800


def ra_media_urls(path: Any) -> List[str]:
    """Absolute URL candidates for an RA image path like "/Badge/12345.png"."""
    if not isinstance(path, str) or not path.strip():
        return []
    path = path.strip()
    if path.startswith("http://") or path.startswith("https://"):
        return [path]
    if not path.startswith("/"):
        path = "/" + path
    return [host + path for host in RA_MEDIA_HOSTS]


def _ra_int(value: Any, default: int = 0) -> int:
    try:
        if isinstance(value, bool):
            return int(value)
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default


def ra_parse_unlocks(payload: Any) -> List[Dict[str, Any]]:
    """Normalise API_GetUserRecentAchievements output. Anything malformed is
    skipped rather than raising, so one odd row can't stop the watcher."""
    if not isinstance(payload, list):
        return []
    out: List[Dict[str, Any]] = []
    for row in payload:
        if not isinstance(row, dict):
            continue
        ach_id = row.get("AchievementID")
        if ach_id in (None, ""):
            continue
        badge = row.get("BadgeURL")
        if not badge and row.get("BadgeName"):
            badge = "/Badge/%s.png" % row.get("BadgeName")
        out.append(
            {
                "id": str(ach_id),
                "title": str(row.get("Title") or "Achievement Unlocked"),
                "description": str(row.get("Description") or ""),
                "points": _ra_int(row.get("Points")),
                "true_ratio": _ra_int(row.get("TrueRatio")),
                "hardcore": _ra_int(row.get("HardcoreMode")) == 1,
                "game_id": _ra_int(row.get("GameID")),
                "game_title": str(row.get("GameTitle") or ""),
                "console": str(row.get("ConsoleName") or ""),
                "badge": badge if isinstance(badge, str) else "",
                "game_icon": row.get("GameIcon") if isinstance(row.get("GameIcon"), str) else "",
                "date": str(row.get("Date") or ""),
            }
        )
    out.sort(key=lambda item: item["date"])
    return out


def ra_select_new(
    unlocks: List[Dict[str, Any]],
    seen: Dict[str, float],
    recent_ids: Dict[str, float],
    now: float,
    hardcore_only: bool = False,
) -> List[Dict[str, Any]]:
    """Unlocks that have not been shown yet, oldest first. Updates `seen`
    (exact id+mode keys) and `recent_ids` (cross-mode suppression)."""
    fresh: List[Dict[str, Any]] = []
    for item in unlocks:
        key = "%s:%d" % (item["id"], 1 if item["hardcore"] else 0)
        if key in seen:
            continue
        seen[key] = now
        if hardcore_only and not item["hardcore"]:
            continue
        last = recent_ids.get(item["id"])
        if last is not None and now - last < RA_CROSS_MODE_SECONDS:
            continue
        recent_ids[item["id"]] = now
        fresh.append(item)
    if len(seen) > RA_SEEN_LIMIT:
        for key, _ts in sorted(seen.items(), key=lambda kv: kv[1])[: len(seen) - RA_SEEN_LIMIT // 2]:
            seen.pop(key, None)
    for ach_id in [k for k, ts in recent_ids.items() if now - ts > RA_CROSS_MODE_SECONDS * 3]:
        recent_ids.pop(ach_id, None)
    return fresh


def ra_percent(progress: Any, ach_id: str) -> Optional[float]:
    """Share of players who have the achievement, from
    API_GetGameInfoAndUserProgress; None when it can't be worked out."""
    if not isinstance(progress, dict):
        return None
    players = _ra_int(progress.get("NumDistinctPlayers"))
    if players <= 0:
        players = _ra_int(progress.get("NumDistinctPlayersCasual"))
    achievements = progress.get("Achievements")
    if players <= 0 or not isinstance(achievements, dict):
        return None
    entry = achievements.get(str(ach_id))
    if not isinstance(entry, dict):
        return None
    awarded = _ra_int(entry.get("NumAwarded"))
    return max(0.0, min(100.0, awarded * 100.0 / players))


def ra_is_complete(progress: Any) -> bool:
    if not isinstance(progress, dict):
        return False
    total = _ra_int(progress.get("NumAchievements"))
    got = max(_ra_int(progress.get("NumAwardedToUser")), _ra_int(progress.get("NumAwardedToUserHardcore")))
    return total > 0 and got >= total


def ra_subtitle(item: Dict[str, Any], show_points: bool = False) -> str:
    """The description only. Points live in the badge (ra_points_text), never at
    the end of this line where a long description would cut them off."""
    return item.get("description") or ""


def ra_points_text(item: Dict[str, Any], show_points: bool, weighted: bool) -> str:
    """Badge text such as "25 pts", "25 pts (160 RP)" (RetroPoints, weighted
    mode) and a trailing "HC" for hardcore."""
    points = _ra_int(item.get("points"))
    if not show_points or points <= 0:
        return ""
    text = "%d pts" % points
    if weighted and _ra_int(item.get("true_ratio")) > 0:
        text += " (%d RP)" % _ra_int(item.get("true_ratio"))
    if item.get("hardcore"):
        text += " HC"
    return text


def ra_weighted_tier(item: Dict[str, Any], cfg: Dict[str, Any], enabled: bool = True) -> Optional[str]:
    """Tier from RetroAchievements' own rarity weighting: RetroPoints divided
    by points. None when it can't be worked out (the caller then falls back
    to the share-of-players tier)."""
    points = _ra_int(item.get("points"))
    true_points = _ra_int(item.get("true_ratio"))
    if not enabled or points <= 0 or true_points <= 0:
        return None
    ratio = true_points / float(points)
    if ratio >= float(cfg.get("ratio_ultra", RA_DEFAULTS["ratio_ultra"])):
        return "ultra_rare"
    if ratio >= float(cfg.get("ratio_rare", RA_DEFAULTS["ratio_rare"])):
        return "rare"
    if ratio >= float(cfg.get("ratio_uncommon", RA_DEFAULTS["ratio_uncommon"])):
        return "uncommon"
    return "common"


def ra_friendly_http_error(code: int) -> str:
    if code in (401, 403):
        return "RetroAchievements refused the username or API key (HTTP %d)." % code
    if code == 404:
        return "RetroAchievements could not find that user (HTTP 404)."
    if code == 429:
        return "RetroAchievements says too many requests (HTTP 429). Slow the check interval down."
    if code >= 500:
        return "RetroAchievements server problem (HTTP %d). It will retry." % code
    return "RetroAchievements returned HTTP %d." % code


# ---------------------------------------------------------------------------
# v1.1 helpers: smart polling, local hints, game list, login file import
# ---------------------------------------------------------------------------
class _RaNoKeepalive(Exception):
    pass


def ssl_error_types() -> tuple:
    try:
        import ssl
        return (ssl.SSLError, ssl.CertificateError)
    except Exception:
        return ()


class RaOfflineError(RuntimeError):
    """No route to RetroAchievements (as opposed to an error it returned)."""


RA_IDLE_MIN_SECONDS = 20.0
RA_IDLE_MAX_SECONDS = 60.0
RA_BURST_POLL_SECONDS = 1.0
RA_BURST_LENGTH_SECONDS = 12.0
RA_ACTIVE_GRACE_SECONDS = 180.0      # stay fast this long after the last unlock
RA_STARTUP_FAST_SECONDS = 60.0       # and for a minute after the plugin starts
RA_CURL_OFFLINE_CODES = (5, 6, 7, 28, 35, 52, 56, 60)
# Process names (as in /proc/<pid>/comm, lower case) that mean "a game may be running".
RA_EMULATOR_COMMS = (
    "retroarch", "duckstation", "pcsx2", "ppsspp", "dolphin", "primehack", "melonds", "mgba", "cemu", "rpcs3",
    "citra", "lime3ds", "azahar", "flycast", "redream", "xemu", "mednafen", "snes9x", "bsnes", "mesen", "fceux",
    "nestopia", "ryujinx", "yuzu", "suyu", "vita3k", "xenia", "scummvm", "supermodel", "bizhawk", "emuhawk",
    "ares", "desmume", "vbam", "visualboyadvance", "stella", "hatari", "yabause", "kronos", "mupen64plus",
    "simple64", "rmg", "shadps4", "pcsx-rearmed", "genesis_plus", "gearboy", "gearsystem", "gearcoleco",
    "rpcs3", "ymir", "mame", "fbneo", "flycast", "ppsspp-sdl", "ppssppsdl", "ppssppqt",
)
RA_EMULATOR_CMD_HINTS = ("libretro", "retroarch")
RA_HINT_LINE_RE = re.compile(r"achievement|cheevo|rcheevos|retroachievements", re.IGNORECASE)
RA_LOGIN_FILE_NAMES = ("retroachievements.txt", "ra_key.txt", "ra.txt", "retroachievements_login.txt")
RA_LOGIN_KEYS = {"username": "username", "user": "username", "name": "username",
                 "key": "api_key", "api_key": "api_key", "apikey": "api_key", "webapikey": "api_key",
                 "web_api_key": "api_key", "api": "api_key"}


def ra_emulator_running(proc_dir: str = "/proc") -> bool:
    """True when a known emulator process exists. Cheap: reads /proc/*/comm
    (and the command line only for generic launcher names)."""
    try:
        entries = os.listdir(proc_dir)
    except OSError:
        return False
    for entry in entries:
        if not entry.isdigit():
            continue
        try:
            with open(os.path.join(proc_dir, entry, "comm"), "r", encoding="utf-8", errors="ignore") as stream:
                comm = stream.read().strip().lower()
        except OSError:
            continue
        if not comm:
            continue
        for name in RA_EMULATOR_COMMS:
            if comm == name or comm.startswith(name):
                return True
        if comm in ("appimage", "apprun", "bwrap", "flatpak", "wine", "wine64-preloader", "proton", "reaper"):
            try:
                with open(os.path.join(proc_dir, entry, "cmdline"), "rb") as stream:
                    cmd = stream.read(4096).replace(b"\0", b" ").decode("utf-8", "ignore").lower()
            except OSError:
                continue
            if any(hint in cmd for hint in RA_EMULATOR_CMD_HINTS):
                return True
    return False


def ra_next_interval(
    poll: float, smart: bool, emulator: bool, since_activity: Optional[float],
    since_start: float, burst_left: float,
) -> Tuple[float, str]:
    """(seconds until the next check, mode). Fast while a game is likely
    running or something just happened; slow when the Deck is idle."""
    if burst_left > 0:
        return RA_BURST_POLL_SECONDS, "burst"
    if not smart:
        return float(poll), "active"
    if emulator or since_start < RA_STARTUP_FAST_SECONDS or (
        since_activity is not None and since_activity < RA_ACTIVE_GRACE_SECONDS
    ):
        return float(poll), "active"
    return max(RA_IDLE_MIN_SECONDS, min(RA_IDLE_MAX_SECONDS, float(poll) * 4)), "idle"


def ra_parse_login_text(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Read a username and API key out of a small text file. Accepts two
    lines (username then key) or key=value / key: value lines."""
    username: Optional[str] = None
    key: Optional[str] = None
    loose: List[str] = []
    for raw in (text or "").splitlines():
        line = raw.strip().lstrip("﻿")
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^([A-Za-z_ ]+?)\s*[:=]\s*(.+)$", line)
        if match:
            field = RA_LOGIN_KEYS.get(re.sub(r"[\s]+", "_", match.group(1).strip().lower()))
            value = match.group(2).strip().strip("\"'")
            if field == "username":
                username = value
            elif field == "api_key":
                key = value
                continue
            continue
        loose.append(line.strip("\"'"))
    if username is None and key is None and len(loose) >= 2:
        username, key = loose[0], loose[1]
    elif username is None and key is None and len(loose) == 1 and RA_KEY_RE.match(loose[0]):
        key = loose[0]
    elif username is None and loose and key is not None:
        username = loose[0]
    elif key is None and loose and username is not None:
        key = loose[0]
    if username is not None and not RA_USERNAME_RE.match(username):
        username = None
    if key is not None and not RA_KEY_RE.match(key):
        key = None
    return username, key


def ra_parse_game(payload: Any) -> Optional[Dict[str, Any]]:
    """Normalise API_GetGameInfoAndUserProgress for the Game tab."""
    if not isinstance(payload, dict) or not payload.get("Title"):
        return None
    players = _ra_int(payload.get("NumDistinctPlayers")) or _ra_int(payload.get("NumDistinctPlayersCasual"))
    items: List[Dict[str, Any]] = []
    achievements = payload.get("Achievements")
    if isinstance(achievements, dict):
        for ach_id, row in achievements.items():
            if not isinstance(row, dict):
                continue
            earned_hc = row.get("DateEarnedHardcore")
            earned = row.get("DateEarned") or earned_hc
            percent = None
            if players > 0:
                percent = round(max(0.0, min(100.0, _ra_int(row.get("NumAwarded")) * 100.0 / players)), 1)
            badge = str(row.get("BadgeName") or "")
            items.append(
                {
                    "id": str(row.get("ID") or ach_id),
                    "title": str(row.get("Title") or ""),
                    "description": str(row.get("Description") or ""),
                    "points": _ra_int(row.get("Points")),
                    "true_ratio": _ra_int(row.get("TrueRatio")),
                    "badge": "/Badge/%s.png" % badge if badge else "",
                    "unlocked": bool(earned),
                    "hardcore": bool(earned_hc),
                    "earned": str(earned or ""),
                    "percent": percent,
                    "order": _ra_int(row.get("DisplayOrder")),
                }
            )
    items.sort(key=lambda it: (it["order"], it["title"].lower()))
    total = _ra_int(payload.get("NumAchievements")) or len(items)
    got = max(_ra_int(payload.get("NumAwardedToUser")), _ra_int(payload.get("NumAwardedToUserHardcore")))
    return {
        "game_id": _ra_int(payload.get("ID")),
        "title": str(payload.get("Title")),
        "console": str(payload.get("ConsoleName") or ""),
        "total": total,
        "unlocked": got,
        "hardcore_unlocked": _ra_int(payload.get("NumAwardedToUserHardcore")),
        "achievements": items,
    }


def ra_parse_recent_games(payload: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not isinstance(payload, list):
        return out
    for row in payload:
        if not isinstance(row, dict) or not _ra_int(row.get("GameID")):
            continue
        out.append(
            {
                "game_id": _ra_int(row.get("GameID")),
                "title": str(row.get("Title") or ""),
                "console": str(row.get("ConsoleName") or ""),
                "total": _ra_int(row.get("NumPossibleAchievements")),
                "unlocked": max(_ra_int(row.get("NumAchieved")), _ra_int(row.get("NumAchievedHardcore"))),
            }
        )
    return out


class Plugin:
    def __init__(self) -> None:
        self._ra_conn: Dict[Any, Tuple[Any, float]] = {}
        self._ra_conn_lock = threading.Lock()
        self._ra_keepalive_ok = True
        self._inotify_fd: Optional[int] = None
        self._inotify_watches: Dict[int, Tuple[str, str]] = {}
        self._stop_event = asyncio.Event()
        self._last_match_timestamp: Optional[str] = None
        self._last_match_sample: Optional[str] = None
        self._last_match_source: Optional[str] = None
        # Overlay session detection (see _x_display_candidates).
        self._overlay_display: Optional[str] = None
        self._overlay_xauth: Optional[str] = None
        self._steam_xauth_cache: Optional[Tuple[Optional[str], float]] = None
        self._steam_display_cache: Optional[Tuple[Optional[str], float]] = None
        self._slot_lock: asyncio.Lock = asyncio.Lock()
        self._slot_holders: Set[str] = set()
        self._gamescope_overlay_lock = asyncio.Lock()
        self._gamescope_overlay_status: Optional[str] = None
        # RetroAchievements watcher state
        self._ra_task: Optional[asyncio.Task] = None
        self._ra_wake: asyncio.Event = asyncio.Event()
        self._ra_status = "starting"
        self._ra_error: Optional[str] = None
        self._ra_last_check: Optional[str] = None
        self._ra_last_ok: Optional[float] = None
        self._ra_last_unlock: Optional[Dict[str, Any]] = None
        self._ra_unlock_count = 0
        self._ra_rebaseline = True
        self._ra_seen: Dict[str, float] = {}
        self._ra_recent_ids: Dict[str, float] = {}
        self._ra_completion_last: Dict[int, float] = {}
        self._ra_hint_task: Optional[asyncio.Task] = None
        self._ra_burst_until = 0.0
        self._ra_hint_count = 0
        self._ra_hint_files_seen = 0
        self._ra_emu_checked = -1e9
        self._ra_emu_running = False
        self._ra_last_game_id = 0
        self._ra_last_activity: Optional[float] = None
        self._ra_mode = "active"
        self._ra_started = time.monotonic()
        self._gamescope_overlay_last_error: Optional[str] = None

    async def _main(self) -> None:
        self._stop_event.clear()
        self._save_settings(self._load_settings())
        self._ensure_user_sounds_dir()
        self._ra_task = asyncio.create_task(self._watch_ra(), name="ra-toasts-watch")
        self._ra_hint_task = asyncio.create_task(self._watch_ra_hints(), name="ra-toasts-hints")
        decky.logger.info("RetroAchievements Toasts backend started")

    async def _unload(self) -> None:
        self._stop_event.set()
        self._ra_wake.set()
        for task in (self._ra_task, self._ra_hint_task):
            if task is not None and not task.done():
                task.cancel()
        with self._ra_conn_lock:
            for key in list(self._ra_conn):
                self._ra_close_conn(key)
        decky.logger.info("RetroAchievements Toasts backend stopped")

    async def get_status(self) -> dict:
        return {
            "gamescope_overlay_status": self._gamescope_overlay_status,
            "gamescope_overlay_last_error": self._gamescope_overlay_last_error,
            "settings": self._effective_settings(),
            "last_match_timestamp": self._last_match_timestamp,
            "last_match_sample": self._last_match_sample,
            "last_match_source": self._last_match_source,
        }

    async def get_settings(self) -> dict:
        self._save_settings(self._load_settings())
        return self._effective_settings()

    async def set_settings(self, settings: dict) -> dict:
        merged = self._sanitize_settings({**self._load_settings(), **settings})
        self._save_settings(merged)
        return merged

    # ------------------------------------------------------------------
    # Per-game settings profiles
    #
    # A profile is a full snapshot of the settings for one game, stored in
    # game_profiles.json as {"<appid>": {"enabled", "name", "settings"}}.
    # Switching it off keeps the saved values, so switching it back on
    # restores them. Unlock toasts and sounds use the profile of the game
    # the unlock belongs to; everything else uses the global settings.
    # ------------------------------------------------------------------

    def _settings_for(self, appid: Optional[int] = None) -> Dict[str, Any]:
        return self._load_settings()

    def _effective_settings(self) -> Dict[str, Any]:
        return self._load_settings()


    async def list_sounds(self) -> List[str]:
        return self._list_sound_files()

    async def get_sounds(self) -> Dict[str, Any]:
        """Selectable sounds (with whether each is built in or yours) and the
        folder to drop your own files into."""
        self._ensure_user_sounds_dir()
        return {
            "folder": self._user_sounds_dir(),
            "extensions": list(SOUND_EXTENSIONS),
            "sounds": self._sound_entries(),
        }

    @staticmethod
    def _rarity_tier(percent: Any, settings: Dict[str, Any]) -> Optional[str]:
        """"ultra_rare" / "rare" / "uncommon" / "common" from the global
        unlock percentage and the user's cutoffs; None when tiers are off or
        the percentage isn't known (never a guess)."""
        if not settings.get("rarity_tiers_enabled", True):
            return None
        if isinstance(percent, bool) or not isinstance(percent, (int, float)):
            return None
        if percent <= float(settings.get("tier_ultra_cutoff", TIER_ULTRA_RANGE[0])):
            return "ultra_rare"
        if percent <= float(settings.get("tier_rare_cutoff", TIER_RARE_RANGE[0])):
            return "rare"
        if percent <= float(settings.get("tier_uncommon_cutoff", TIER_UNCOMMON_RANGE[0])):
            return "uncommon"
        return "common"

    # ------------------------------------------------------------------
    # Test popups
    #
    # One test per tier. When a game is running (and the setting allows) the
    # test shows a RANDOM achievement from that game -- locked or unlocked --
    # with its real name, description and icon, plus the game's artwork for
    # the gradient/placeholder options. It is display-only: `test=True`
    # keeps it out of the "already shown" bookkeeping, so testing a locked
    # achievement can never suppress its real popup later.
    # ------------------------------------------------------------------


    @staticmethod
    def _sample_percent_for_tier(tier: str, settings: Dict[str, Any]) -> float:
        """A percentage that lands squarely inside the tier for the user's
        current cutoffs (so the test shows the tier no matter how they set
        the sliders)."""
        ultra = float(settings.get("tier_ultra_cutoff", TIER_ULTRA_RANGE[0]))
        rare = float(settings.get("tier_rare_cutoff", TIER_RARE_RANGE[0]))
        uncommon = float(settings.get("tier_uncommon_cutoff", TIER_UNCOMMON_RANGE[0]))
        if tier == "ultra_rare":
            return round(max(ultra / 2.0, 0.05), 2)
        if tier == "rare":
            return round((ultra + rare) / 2.0, 1)
        if tier == "uncommon":
            return round((rare + uncommon) / 2.0, 1)
        return round(min((uncommon + 100.0) / 2.0, 95.0), 1)

    async def test_popup_common(self) -> None:
        await self._run_tier_test("common")

    async def test_popup_uncommon(self) -> None:
        await self._run_tier_test("uncommon")

    async def test_popup_rare(self) -> None:
        await self._run_tier_test("rare")

    async def test_popup_ultra_rare(self) -> None:
        await self._run_tier_test("ultra_rare")

    # Older names, kept so a panel built before these buttons existed still works.
    def _settings_dir(self) -> str:
        return FINALLY_SETTINGS_DIR

    def _sound_dir(self) -> str:
        return os.path.join(decky.DECKY_PLUGIN_DIR, "assets", SOUNDS_DIR_NAME)

    def _user_sounds_dir(self) -> str:
        return FINALLY_USER_SOUNDS_DIR

    def _ensure_user_sounds_dir(self) -> None:
        """Creates the "drop your sounds here" folder (with a short note)."""
        try:
            os.makedirs(self._user_sounds_dir(), exist_ok=True)
            note = os.path.join(self._user_sounds_dir(), "PUT YOUR SOUNDS HERE.txt")
            if not os.path.exists(note) and not any(
                e.lower().endswith(SOUND_EXTENSIONS) for e in os.listdir(self._user_sounds_dir())
            ):
                with open(note, "w", encoding="utf-8") as stream:
                    stream.write(
                        "Drop your own short sound files in this folder (.wav, .flac, .ogg, .mp3, .aiff; "
                        "10 MB or less; anything longer than ~20 seconds is cut off), then open the RetroAchievements Toasts panel "
                        "-> Sound & tests -> Refresh sound list and pick them for each popup type.\n"
                        "This folder is kept when the plugin is updated.\n"
                    )
        except OSError as err:
            decky.logger.warning("Couldn't create the user sounds folder: %s", err)

    @staticmethod
    def _is_sound_file(directory: str, entry: str, allowed: Tuple[str, ...]) -> bool:
        if entry.startswith(".") or not entry.lower().endswith(allowed):
            return False
        path = os.path.join(directory, entry)
        try:
            return os.path.isfile(path) and 0 < os.path.getsize(path) <= SOUND_MAX_BYTES
        except OSError:
            return False

    def _sound_entries(self) -> List[Dict[str, str]]:
        """Every selectable sound as {"name", "source"} ("builtin" or "user").
        Bundled sounds are .wav only; your own can be any of SOUND_EXTENSIONS.
        A file of yours with the same name as a bundled one replaces it."""
        found: Dict[str, str] = {}
        for sound_dir in (self._sound_dir(), os.path.join(decky.DECKY_PLUGIN_DIR, "assets")):
            try:
                for entry in os.listdir(sound_dir):
                    if self._is_sound_file(sound_dir, entry, (".wav",)):
                        found.setdefault(entry, "builtin")
            except OSError:
                continue
        try:
            for entry in os.listdir(self._user_sounds_dir()):
                if self._is_sound_file(self._user_sounds_dir(), entry, SOUND_EXTENSIONS):
                    found[entry] = "user"
        except OSError:
            pass
        return [{"name": n, "source": found[n]} for n in sorted(found, key=str.lower)]

    def _list_sound_files(self) -> List[str]:
        return [entry["name"] for entry in self._sound_entries()]

    def _coerce_percent(self, value: Any, default: int, step: int = 10) -> int:
        """0-100, rounded to the nearest `step` (10 for volume; the popup
        size slider uses 5)."""
        try:
            percent = int(round(float(value)))
        except (TypeError, ValueError):
            return default
        return max(0, min(100, int(round(percent / step) * step)))

    def _coerce_int_range(self, value: Any, default: int, lo: int, hi: int) -> int:
        try:
            number = int(round(float(value)))
        except (TypeError, ValueError):
            return default
        return max(lo, min(hi, number))

    def _coerce_float_range(
        self, value: Any, default: float, lo: float, hi: float, step: float = 0.5
    ) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return default
        number = max(lo, min(hi, number))
        # Snap to the same step the slider moves in, avoiding float drift
        # (e.g. 5.7999999999999998) from repeated round-trips through JSON.
        return round(round(number / step) * step, 2)

    def _sanitize_settings(self, raw_settings: Dict[str, Any]) -> Dict[str, Any]:
        settings = dict(DEFAULT_SETTINGS)
        # Older saved settings had one "normal" and one "rare" sound; carry
        # those over to the new per-tier slots when a slot hasn't been set yet.
        legacy = {
            "common": raw_settings.get("normal_sound"),
            "uncommon": raw_settings.get("normal_sound"),
            "rare": raw_settings.get("rare_sound"),
            "ultra_rare": raw_settings.get("rare_sound"),
            "completion": raw_settings.get("rare_sound"),
        }
        for slot in SOUND_SLOTS:
            key = f"sound_{slot}"
            value = raw_settings.get(key)
            if not isinstance(value, str):
                value = legacy[slot]
            if isinstance(value, str):
                settings[key] = value

        # Popup size moves in steps of 5; volume stays in steps of 10.
        for key, step in (("overlay_size_percent", 5), ("volume_percent", 10)):
            settings[key] = self._coerce_percent(raw_settings.get(key), int(settings[key]), step)

        position = raw_settings.get("overlay_position")
        if isinstance(position, str) and position.strip().lower() in OVERLAY_POSITIONS:
            settings["overlay_position"] = position.strip().lower()
        else:
            settings["overlay_position"] = DEFAULT_SETTINGS["overlay_position"]

        template = raw_settings.get("overlay_template")
        if isinstance(template, str) and template.strip().lower() in OVERLAY_TEMPLATES:
            settings["overlay_template"] = template.strip().lower()
        else:
            settings["overlay_template"] = DEFAULT_SETTINGS["overlay_template"]

        for key, (default, lo, hi) in FONT_SIZE_RANGES.items():
            settings[key] = self._coerce_int_range(raw_settings.get(key), default, lo, hi)

        duration_default, duration_lo, duration_hi = DURATION_RANGE
        settings["duration_seconds"] = self._coerce_float_range(
            raw_settings.get("duration_seconds"), duration_default, duration_lo, duration_hi
        )

        settings["icon_glow_enabled"] = bool(
            raw_settings.get("icon_glow_enabled", DEFAULT_SETTINGS["icon_glow_enabled"])
        )
        settings["ring_size"] = self._coerce_int_range(
            raw_settings.get("ring_size"), DEFAULT_SETTINGS["ring_size"], 0, 100
        )
        settings["icon_glow_intensity"] = self._coerce_int_range(
            raw_settings.get("icon_glow_intensity"), DEFAULT_SETTINGS["icon_glow_intensity"], 0, 100
        )

        gradient_direction = raw_settings.get("gradient_direction")
        if isinstance(gradient_direction, str) and gradient_direction.strip().lower() in GRADIENT_DIRECTIONS:
            settings["gradient_direction"] = gradient_direction.strip().lower()
        else:
            settings["gradient_direction"] = DEFAULT_SETTINGS["gradient_direction"]

        settings["glow_normal_enabled"] = bool(
            raw_settings.get("glow_normal_enabled", DEFAULT_SETTINGS["glow_normal_enabled"])
        )
        settings["icon_frame_ring_enabled"] = bool(
            raw_settings.get("icon_frame_ring_enabled", DEFAULT_SETTINGS["icon_frame_ring_enabled"])
        )
        settings["show_percent"] = bool(
            raw_settings.get("show_percent", DEFAULT_SETTINGS["show_percent"])
        )
        placeholder_icon = raw_settings.get("placeholder_icon")
        if isinstance(placeholder_icon, str) and placeholder_icon.strip().lower() in PLACEHOLDER_ICON_STYLES:
            settings["placeholder_icon"] = placeholder_icon.strip().lower()
        else:
            settings["placeholder_icon"] = DEFAULT_SETTINGS["placeholder_icon"]
        settings["icon_gradient_enabled"] = bool(
            raw_settings.get("icon_gradient_enabled", DEFAULT_SETTINGS["icon_gradient_enabled"])
        )
        completion_title = raw_settings.get("completion_title")
        if isinstance(completion_title, str) and completion_title.strip().lower() in COMPLETION_TITLES:
            settings["completion_title"] = completion_title.strip().lower()
        else:
            settings["completion_title"] = DEFAULT_SETTINGS["completion_title"]
        percent_position = raw_settings.get("percent_position")
        settings["percent_position"] = (
            percent_position if percent_position in PERCENT_POSITIONS else DEFAULT_SETTINGS["percent_position"]
        )
        settings["percent_size"] = self._coerce_int_range(
            raw_settings.get("percent_size"), PERCENT_SIZE_RANGE[0], PERCENT_SIZE_RANGE[1], PERCENT_SIZE_RANGE[2]
        )
        return settings

    def _load_settings(self) -> Dict[str, Any]:
        try:
            with open(FINALLY_SETTINGS_FILE, "r", encoding="utf-8") as stream:
                raw_settings = json.load(stream)
        except OSError:
            return dict(DEFAULT_SETTINGS)
        except Exception as err:
            decky.logger.warning("Unable to parse RetroAchievements Toasts settings: %s", err)
            return dict(DEFAULT_SETTINGS)

        if not isinstance(raw_settings, dict):
            return dict(DEFAULT_SETTINGS)
        return self._sanitize_settings(raw_settings)

    def _save_settings(self, settings: Dict[str, Any]) -> None:
        try:
            os.makedirs(self._settings_dir(), exist_ok=True)
            with open(FINALLY_SETTINGS_FILE, "w", encoding="utf-8") as stream:
                json.dump(settings, stream, indent=2, sort_keys=True)
        except OSError as err:
            decky.logger.warning("Unable to save RetroAchievements Toasts settings: %s", err)

    @staticmethod
    def _sound_slot(is_rare: bool, tier: Optional[str] = None, completion: bool = False) -> str:
        """Which sound slot a popup uses: the completion popup has its own;
        otherwise the rarity tier when it's known; otherwise (tiers off or no
        percentage) the old rare / normal split."""
        if completion:
            return "completion"
        if tier in ("common", "uncommon", "rare", "ultra_rare"):
            return str(tier)
        return "rare" if is_rare else "common"

    def _sound_path(
        self,
        is_rare: bool,
        settings: Optional[Dict[str, Any]] = None,
        tier: Optional[str] = None,
        completion: bool = False,
    ) -> str:
        settings = settings if settings is not None else self._load_settings()
        key = f"sound_{self._sound_slot(is_rare, tier, completion)}"
        filename = str(settings.get(key) or DEFAULT_SETTINGS[key])
        candidates = [
            os.path.join(self._user_sounds_dir(), filename),     # yours first (replaces a built-in of the same name)
            os.path.join(self._sound_dir(), filename),
            os.path.join(decky.DECKY_PLUGIN_DIR, "assets", filename),
            os.path.join(decky.DECKY_PLUGIN_DIR, "assets", DEFAULT_SETTINGS[key]),
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return candidates[-1]

    def _build_audio_env(self) -> Dict[str, str]:
        env = os.environ.copy()
        runtime_dir = env.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
        env["XDG_RUNTIME_DIR"] = runtime_dir

        pulse_socket = os.path.join(runtime_dir, "pulse", "native")
        if os.path.exists(pulse_socket):
            env.setdefault("PULSE_SERVER", f"unix:{pulse_socket}")

        return env

    def _looks_like_image(self, data: Optional[bytes]) -> bool:
        """Minimal sanity check on downloaded/cached icon bytes: real
        image files start with a recognizable signature and are more than
        a trivial handful of bytes. Catches the case where a URL returns
        200 OK with something that isn't actually an image (an HTML error
        page, an empty/near-empty response, etc.) before we ever cache or
        show it -- rather than caching a broken file forever."""
        if not data or len(data) < 256:
            return False
        return (
            data.startswith(b"\xff\xd8\xff")  # JPEG
            or data.startswith(b"\x89PNG\r\n\x1a\n")  # PNG
            or data.startswith(b"GIF87a")
            or data.startswith(b"GIF89a")
            or (data[:4] == b"RIFF" and data[8:12] == b"WEBP")
        )


    async def _play_sound(
        self,
        is_rare: bool,
        settings: Optional[Dict[str, Any]] = None,
        tier: Optional[str] = None,
        completion: bool = False,
    ) -> Optional[str]:
        """Starts the sound; returns its path (None if nothing played)."""
        settings = settings if settings is not None else self._load_settings()
        sound_path = self._sound_path(is_rare, settings, tier, completion)
        if not os.path.exists(sound_path):
            decky.logger.warning("Sound file missing: %s", sound_path)
            return None

        volume_percent = int(settings.get("volume_percent", DEFAULT_SETTINGS["volume_percent"]))
        if volume_percent <= 0:
            return None

        pulse_volume = max(0, min(131072, int(round((volume_percent / 50.0) * 65536))))
        env = self._build_audio_env()

        try:
            player = subprocess.Popen(
                [
                    "paplay",
                    "--stream-name",
                    "RetroAchievements Toasts",
                    "--property=media.role=event",
                    f"--volume={pulse_volume}",
                    sound_path,
                ],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            # Your own files can be any length; never let one play on forever.
            try:
                asyncio.get_running_loop().call_later(SOUND_MAX_PLAY_SECONDS, self._stop_player, player)
            except RuntimeError:
                pass
            return sound_path
        except Exception as err:
            decky.logger.error("Audio playback failed: %s", err)
            return None

    @staticmethod
    def _stop_player(player: Any) -> None:
        try:
            if player.poll() is None:
                player.terminate()
        except Exception:
            pass

    async def _systemctl_user(self, action: str, unit: str) -> None:
        process = await asyncio.create_subprocess_exec(
            "systemctl",
            "--user",
            action,
            unit,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await process.wait()

    # ------------------------------------------------------------------
    # Display / session detection for the overlay processes
    #
    # The popup and tracker windows are opened by helper processes that need
    # to be told which X display and runtime folder to use. These used to be
    # hard-coded (":0" and /run/user/1000, right for a Steam Deck), which
    # silently fails on a device where either differs: sound still plays but
    # no popup appears. They're detected now, with the old values as the
    # fallback.
    # ------------------------------------------------------------------

    def _user_uid(self) -> int:
        """UID of the desktop/gaming user (the plugin itself usually runs as root)."""
        try:
            import pwd
            name = getattr(decky, "DECKY_USER", None)
            if name:
                return pwd.getpwnam(str(name)).pw_uid
        except Exception:
            pass
        try:
            home = str(getattr(decky, "DECKY_USER_HOME", "") or "")
            if home and os.path.isdir(home):
                uid = os.stat(home).st_uid
                if uid > 0:
                    return uid
        except OSError:
            pass
        if os.getuid() > 0:
            return os.getuid()
        candidates = sorted(
            int(os.path.basename(p)) for p in glob.glob("/run/user/[0-9]*") if int(os.path.basename(p)) > 0
        )
        return candidates[0] if candidates else 1000

    def _runtime_dir(self) -> str:
        preferred = f"/run/user/{self._user_uid()}"
        if os.path.isdir(preferred):
            return preferred
        others = sorted(p for p in glob.glob("/run/user/[0-9]*") if os.path.basename(p) != "0")
        return others[0] if others else preferred

    def _steam_client_display(self) -> Optional[str]:
        """DISPLAY of the running Steam client: the X server gamescope shows
        overlays from. Cached briefly (the scan reads /proc)."""
        cached = self._steam_display_cache
        if cached is not None and time.monotonic() - cached[1] < 60.0:
            return cached[0]
        found: Optional[str] = None
        found_auth: Optional[str] = None
        try:
            for comm_path in glob.glob("/proc/[0-9]*/comm"):
                try:
                    with open(comm_path, "r", encoding="utf-8", errors="ignore") as stream:
                        if stream.read().strip() not in ("steam", "steamwebhelper"):
                            continue
                    with open(os.path.join(os.path.dirname(comm_path), "environ"), "rb") as stream:
                        env = stream.read().split(b"\0")
                except OSError:
                    continue
                for item in env:
                    if item.startswith(b"DISPLAY="):
                        value = item[8:].decode("utf-8", errors="ignore").strip()
                        if re.fullmatch(r":\d+(\.\d+)?", value):
                            found = value.split(".")[0]
                    elif item.startswith(b"XAUTHORITY="):
                        value = item[11:].decode("utf-8", errors="ignore").strip()
                        if value.startswith("/"):
                            found_auth = value
                if found:
                    break
        except Exception:
            found = None
        self._steam_display_cache = (found, time.monotonic())
        self._steam_xauth_cache = (found_auth, time.monotonic())
        return found

    def _xauthority_candidates(self) -> List[str]:
        """X authority (cookie) files that may let the overlay helper talk to
        the display, best first: the one the Steam client itself uses, one
        that worked before, then the usual places. Only files that exist."""
        self._steam_client_display()                      # refreshes the Steam client's XAUTHORITY too
        ordered: List[str] = []
        steam_auth = self._steam_xauth_cache[0] if self._steam_xauth_cache else None
        for candidate in (self._overlay_xauth, steam_auth, os.environ.get("XAUTHORITY")):
            if candidate:
                ordered.append(candidate)
        runtime = self._runtime_dir()
        home = str(getattr(decky, "DECKY_USER_HOME", "") or "")
        patterns = [
            os.path.join(runtime, "xauth_*"),
            os.path.join(runtime, ".mutter-Xwaylandauth.*"),
            os.path.join(runtime, "Xauthority"),
            os.path.join(runtime, "gdm", "Xauthority"),
            os.path.join(home, ".Xauthority") if home else "",
            "/home/*/.Xauthority",
            "/tmp/xauth_*",
        ]
        for pattern in patterns:
            if pattern:
                ordered.extend(sorted(glob.glob(pattern)))
        result: List[str] = []
        for path in ordered:
            if path not in result and os.path.isfile(path):
                result.append(path)
        return result[:4]

    def _overlay_attempts(self) -> List[Tuple[str, Optional[str]]]:
        """(display, X authority file or None) combinations to try, best
        first. With no authority files found this is just the displays."""
        displays = self._x_display_candidates()[:3]
        authorities = self._xauthority_candidates()[:2]
        pairs: List[Tuple[str, Optional[str]]] = []
        if self._overlay_display:
            pairs.append((self._overlay_display, self._overlay_xauth))
        for display in displays:
            for authority in authorities + [None]:
                pairs.append((display, authority))
        unique: List[Tuple[str, Optional[str]]] = []
        for pair in pairs:
            if pair not in unique:
                unique.append(pair)
        return unique[:5]

    def _x_display_candidates(self) -> List[str]:
        """Displays to try, best first: the one that worked before, the Steam
        client's, the historical ":0", then any other X socket present."""
        ordered: List[str] = []
        if self._overlay_display:
            ordered.append(self._overlay_display)
        steam = self._steam_client_display()
        if steam:
            ordered.append(steam)
        ordered.append(":0")
        for path in sorted(glob.glob("/tmp/.X11-unix/X[0-9]*")):
            ordered.append(":" + os.path.basename(path)[1:])
        seen: List[str] = []
        for display in ordered:
            if display not in seen:
                seen.append(display)
        return seen

    def _overlay_session_env(self) -> Dict[str, str]:
        """DISPLAY + XDG_RUNTIME_DIR (+ XAUTHORITY when one is found) for overlay helper processes."""
        env = {"DISPLAY": self._x_display_candidates()[0], "XDG_RUNTIME_DIR": self._runtime_dir()}
        authorities = self._xauthority_candidates()
        if authorities:
            env["XAUTHORITY"] = authorities[0]
        return env

    @staticmethod
    def _looks_like_display_failure(stderr_text: str) -> bool:
        lowered = stderr_text.lower()
        return any(
            marker in lowered
            for marker in (
                "glfwinit failed", "cannot open display", "can't open display", "could not open x display",
                "failed to open display", "no display", "authorization required", "no authorization protocol",
            )
        )

    async def run_overlay_check(self) -> Dict[str, Any]:
        """Self-test for "the sound plays but no popup shows": runs the
        overlay's requirements check under the same interpreter and
        environment the popup uses and turns it into a plain-English report."""
        env = os.environ.copy()
        env.pop("LD_LIBRARY_PATH", None)
        env.pop("LD_PRELOAD", None)
        env.update(self._overlay_session_env())
        checks: List[Dict[str, Any]] = []
        uid = self._user_uid()
        checks.append({"name": "User", "ok": True, "detail": f"uid {uid}, runtime dir {env['XDG_RUNTIME_DIR']}", "fatal": False})
        checks.append({
            "name": "Display candidates", "ok": True, "fatal": False,
            "detail": ", ".join(self._x_display_candidates()) + f" (using {env['DISPLAY']})",
        })
        authority = env.get("XAUTHORITY")
        checks.append({
            "name": "X authority", "ok": True, "fatal": False,
            "detail": authority if authority else "none found (fine when the display allows local connections)",
        })
        gamescope_running = any(
            self._proc_comm_contains(pid_dir, "gamescope") for pid_dir in glob.glob("/proc/[0-9]*")
        )
        checks.append({
            "name": "Gamescope running", "ok": gamescope_running, "fatal": False,
            "detail": "found" if gamescope_running else "no gamescope process found (popups only show in Game Mode)",
        })
        checks.append({
            "name": "Overlay helper files", "fatal": True,
            "ok": all(os.path.exists(os.path.join(decky.DECKY_PLUGIN_DIR, n)) for n in (OVERLAY_SCRIPT_NAME, DIAGNOSE_SCRIPT_NAME, DRAWING_LAYER_NAME)),
            "detail": f"{OVERLAY_SCRIPT_NAME}, {DIAGNOSE_SCRIPT_NAME}, {DRAWING_LAYER_NAME} in the plugin folder",
        })
        helper = os.path.join(decky.DECKY_PLUGIN_DIR, DIAGNOSE_SCRIPT_NAME)
        if os.path.exists(helper):
            try:
                process = await asyncio.create_subprocess_exec(
                    STEAMWORKS_PYTHON, helper, env=env,
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=20.0)
                report = json.loads(stdout.decode("utf-8", errors="replace").strip().splitlines()[-1])
                checks.extend(report.get("checks", []))
            except asyncio.TimeoutError:
                checks.append({"name": "Self-check", "ok": False, "fatal": True, "detail": "timed out after 20 seconds"})
            except Exception as err:
                checks.append({"name": "Self-check", "ok": False, "fatal": True, "detail": f"could not run: {err}"})
        failed = [c for c in checks if not c.get("ok") and c.get("fatal", True)]
        if failed:
            first = failed[0]
            verdict = f"Problem found: {first['name']} - {first['detail']}"
        elif not gamescope_running:
            verdict = "The popup's requirements are all present, but Game Mode (gamescope) isn't running right now."
        else:
            verdict = (
                "Everything the popup needs is present. If popups still don't show, send the last popup status below."
            )
        return {
            "ok": not failed,
            "verdict": verdict,
            "checks": checks,
            "last_status": self._gamescope_overlay_status,
            "last_error": self._gamescope_overlay_last_error,
        }

    @staticmethod
    def _proc_comm_contains(pid_dir: str, needle: str) -> bool:
        try:
            with open(os.path.join(pid_dir, "comm"), "r", encoding="utf-8", errors="ignore") as stream:
                return needle in stream.read()
        except OSError:
            return False

    # ------------------------------------------------------------------
    # Achievement browser + tracker (merged in from the old standalone achievements
    # plugin)
    #
    # * The browser lists every achievement of the running game (locked and
    #   unlocked) using a one-shot Steamworks probe. Icons come from the Web
    #   API schema first (colored), then Steam's local cache.
    # * One achievement can be pinned. A small persistent overlay
    #   (tracker_overlay.py) shows it, drawn with the toast plugin's own
    #   template and colors. Game detection is the toast watcher's
    #   (_active_appid) -- there is no second /proc scan.
    # * Only one gamescope overlay window can be shown at a time, so this
    #   class is the single owner of it: while a toast plays the tracker
    #   slides away and its window is destroyed, and it returns afterwards.
    #   MangoApp is stopped once and restarted only when nobody needs the
    #   slot any more.
    # ------------------------------------------------------------------

    # --- public API used by the panel ---------------------------------------

    # --- overlay slot / MangoApp ownership ------------------------------------

    async def _acquire_overlay_slot(self, holder: str) -> None:
        """Marks `holder` ("toast" or "tracker") as needing the gamescope
        overlay slot; MangoApp is stopped when the first holder arrives."""
        async with self._slot_lock:
            first = not self._slot_holders
            self._slot_holders.add(holder)
            if first:
                try:
                    await self._systemctl_user("stop", "gamescope-mangoapp.service")
                except Exception as err:
                    decky.logger.warning("Couldn't stop MangoApp: %s", err)

    async def _release_overlay_slot(self, holder: str) -> None:
        """MangoApp is restarted only when the last holder lets go."""
        async with self._slot_lock:
            self._slot_holders.discard(holder)
            if not self._slot_holders:
                try:
                    await self._systemctl_user("start", "gamescope-mangoapp.service")
                except Exception as err:
                    decky.logger.warning("Couldn't restart MangoApp: %s", err)

    async def _show_gamescope_overlay(self, payload: Dict[str, Any]) -> None:
        helper_path = os.path.join(decky.DECKY_PLUGIN_DIR, FINALLY_OVERLAY_HELPER_NAME)
        if not os.path.exists(helper_path):
            self._gamescope_overlay_last_error = f"missing helper: {helper_path}"
            return

        # Counted from the moment it's queued, so the tracker stays hidden
        # through a whole burst of toasts instead of flickering between them.
        await self._show_gamescope_overlay_locked(payload, helper_path)

    async def _show_gamescope_overlay_locked(self, payload: Dict[str, Any], helper_path: str) -> None:
        async with self._gamescope_overlay_lock:
            settings = self._settings_for(payload.get("settings_appid"))
            if int(settings.get("overlay_size_percent", DEFAULT_SETTINGS["overlay_size_percent"])) <= 0:
                self._gamescope_overlay_status = "hidden_size_zero"
                self._gamescope_overlay_last_error = None
                return

            # Sound plays here, inside the same lock that serializes the
            # visual overlay, so a burst of achievements unlocking at once
            # gets a sound+visual pair *per item, in turn* -- rather than
            # every sound firing all at once the moment each was detected
            # while only the first item's visual (and, it turned out, only
            # the first item's sound) actually made it to the screen/speakers.
            # The tracker starts sliding away while the sound's lead-in plays.
            played = await self._play_sound(
                bool(payload.get("is_rare")),
                settings,
                tier=payload.get("tier"),
                completion=bool(payload.get("completion")),
            )
            # The bundled "*_preroll" sounds start with a short silence so the
            # audible part lines up with the popup, hence the wait. A sound
            # without that lead-in (yours, or the plain bundled ones) starts
            # at once, so the popup shouldn't be held back for it.
            if not (played and "preroll" not in os.path.basename(played).lower()):
                await asyncio.sleep(AUDIO_PREROLL_SECONDS)
            env = os.environ.copy()
            # Decky's bundled libs (LD_LIBRARY_PATH/LD_PRELOAD) can shadow the
            # system GL/EGL drivers and break GLFW window creation.
            env.pop("LD_LIBRARY_PATH", None)
            env.pop("LD_PRELOAD", None)
            env.update(
                {
                    **self._overlay_session_env(),
                    "FINALLY_TITLE": str(payload.get("title") or "Achievement Unlocked"),
                    "FINALLY_SUBTITLE": str(payload.get("subtitle") or ""),
                    "FINALLY_RARE": "1" if payload.get("is_rare") else "0",
                    "FINALLY_POINTS": str(payload.get("points_text") or ""),
                    "FINALLY_TEMPLATE_COLORS": "1" if settings.get(
                        "template_colors_enabled", DEFAULT_SETTINGS["template_colors_enabled"]
                    ) else "0",
                    "FINALLY_TEMPLATE_FX": "1" if settings.get(
                        "template_fx_enabled", DEFAULT_SETTINGS["template_fx_enabled"]
                    ) else "0",
                    "FINALLY_GAME_NAME": str(payload.get("game_name") or ""),
                    "FINALLY_TIER": (
                        str(payload.get("tier"))
                        if payload.get("tier") in ("uncommon", "rare", "ultra_rare")
                        else ""
                    ),
                    "FINALLY_ICON_PATH": str(payload.get("icon_path") or ""),
                    "FINALLY_PLACEHOLDER_STYLE": str(
                        settings.get("placeholder_icon", DEFAULT_SETTINGS["placeholder_icon"])
                    ),
                    "FINALLY_GAME_ART_GRADIENT_ENABLED": "1" if settings.get(
                        "game_art_gradient_enabled", DEFAULT_SETTINGS["game_art_gradient_enabled"]
                    ) else "0",
                    "FINALLY_GAME_ART_PATH": str(payload.get("game_art_path") or ""),
                    "FINALLY_PLACEHOLDER_ICON_PATH": str(payload.get("placeholder_icon_path") or ""),
                    "FINALLY_PERCENT": (
                        f"{payload['percent']:.2f}" if isinstance(payload.get("percent"), (int, float)) else ""
                    ),
                    "FINALLY_PERCENT_POSITION": str(
                        settings.get("percent_position", DEFAULT_SETTINGS["percent_position"])
                    ),
                    "FINALLY_PERCENT_SIZE": str(
                        settings.get("percent_size", DEFAULT_SETTINGS["percent_size"])
                    ),
                    "FINALLY_PERCENT_ENABLED": "1" if settings.get(
                        "show_percent", DEFAULT_SETTINGS["show_percent"]
                    ) else "0",
                    "FINALLY_SIZE_PERCENT": str(settings.get("overlay_size_percent", 50)),
                    "FINALLY_POSITION": str(settings.get("overlay_position", DEFAULT_SETTINGS["overlay_position"])),
                    "FINALLY_TEMPLATE": str(
                        payload.get("template_override")
                        or settings.get("overlay_template", DEFAULT_SETTINGS["overlay_template"])
                    ),
                    "FINALLY_LABEL_SIZE": str(settings.get("label_font_size", DEFAULT_SETTINGS["label_font_size"])),
                    "FINALLY_TITLE_SIZE": str(settings.get("title_font_size", DEFAULT_SETTINGS["title_font_size"])),
                    "FINALLY_SUBTITLE_SIZE": str(settings.get("subtitle_font_size", DEFAULT_SETTINGS["subtitle_font_size"])),
                    "FINALLY_NORMAL_GRADIENT_START": str(settings.get("normal_gradient_start")),
                    "FINALLY_NORMAL_GRADIENT_END": str(settings.get("normal_gradient_end")),
                    "FINALLY_RARE_GRADIENT_START": str(settings.get("rare_gradient_start")),
                    "FINALLY_RARE_GRADIENT_END": str(settings.get("rare_gradient_end")),
                    "FINALLY_NORMAL_CIRCLE_COLOR": str(settings.get("normal_circle_color")),
                    "FINALLY_RARE_CIRCLE_COLOR": str(settings.get("rare_circle_color")),
                    "FINALLY_SECONDS": str(
                        max(
                            float(settings.get("duration_seconds", DEFAULT_SETTINGS["duration_seconds"])),
                            float(payload.get("min_seconds") or 0.0),
                        )
                    ),
                    "FINALLY_GLOW_ENABLED": "1" if settings.get(
                        "icon_glow_enabled", DEFAULT_SETTINGS["icon_glow_enabled"]
                    ) else "0",
                    "FINALLY_RING_SIZE": str(
                        settings.get("ring_size", DEFAULT_SETTINGS["ring_size"])
                    ),
                    "FINALLY_GLOW_INTENSITY": str(
                        settings.get("icon_glow_intensity", DEFAULT_SETTINGS["icon_glow_intensity"])
                    ),
                    "FINALLY_GRADIENT_DIRECTION": str(
                        settings.get("gradient_direction", DEFAULT_SETTINGS["gradient_direction"])
                    ),
                    "FINALLY_GLOW_NORMAL": "1" if settings.get(
                        "glow_normal_enabled", DEFAULT_SETTINGS["glow_normal_enabled"]
                    ) else "0",
                    "FINALLY_FRAME_RING_ENABLED": "1" if settings.get(
                        "icon_frame_ring_enabled", DEFAULT_SETTINGS["icon_frame_ring_enabled"]
                    ) else "0",
                    "FINALLY_ICON_GRADIENT_ENABLED": "1" if settings.get(
                        "icon_gradient_enabled", DEFAULT_SETTINGS["icon_gradient_enabled"]
                    ) else "0",
                }
            )
            self._gamescope_overlay_status = "starting"
            try:
                await self._acquire_overlay_slot("toast")
                # Try the detected display first; if the helper couldn't reach
                # it, try the next candidate (at most three). The one that
                # works is remembered for next time.
                for display, authority in self._overlay_attempts():
                    env["DISPLAY"] = display
                    if authority:
                        env["XAUTHORITY"] = authority
                    else:
                        env.pop("XAUTHORITY", None)
                    process = await asyncio.create_subprocess_exec(
                        STEAMWORKS_PYTHON,
                        helper_path,
                        env=env,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    stdout, stderr = await process.communicate()
                    if process.returncode == 0:
                        self._gamescope_overlay_status = "shown"
                        self._gamescope_overlay_last_error = None
                        self._overlay_display = display
                        self._overlay_xauth = authority
                        break
                    stderr_text = stderr.decode("utf-8", errors="replace").strip()
                    self._gamescope_overlay_status = f"failed:{process.returncode}"
                    self._gamescope_overlay_last_error = (
                        f"[DISPLAY={display}{' XAUTHORITY=' + os.path.basename(authority) if authority else ''}] "
                        + (stderr_text[-440:] or "unknown overlay helper error")
                    )
                    decky.logger.warning(
                        "Gamescope overlay failed on %s rc=%s stdout=%s stderr=%s",
                        display,
                        process.returncode,
                        stdout.decode("utf-8", errors="replace")[-500:],
                        stderr_text[-500:],
                    )
                    if not self._looks_like_display_failure(stderr_text):
                        break                     # not a display problem: another display won't help
            except Exception as err:
                self._gamescope_overlay_status = "failed"
                self._gamescope_overlay_last_error = str(err)
                decky.logger.warning("Gamescope overlay failed: %s", err)
            finally:
                # MangoApp comes back only if the tracker isn't holding the slot.
                await self._release_overlay_slot("toast")

    # ------------------------------------------------------------------
    # RetroAchievements: config, polling and popups
    # ------------------------------------------------------------------

    def _ra_cfg(self) -> Dict[str, Any]:
        cfg = dict(RA_DEFAULTS)
        try:
            with open(RA_SETTINGS_FILE, "r", encoding="utf-8") as stream:
                raw = json.load(stream)
            if isinstance(raw, dict):
                cfg.update({k: raw[k] for k in RA_DEFAULTS if k in raw})
        except FileNotFoundError:
            pass
        except Exception as err:
            decky.logger.warning("RetroAchievements settings unreadable, using defaults: %s", err)
        cfg["username"] = str(cfg.get("username") or "").strip()
        cfg["api_key"] = str(cfg.get("api_key") or "").strip()
        cfg["enabled"] = bool(cfg.get("enabled"))
        cfg["show_points"] = bool(cfg.get("show_points"))
        cfg["hardcore_only"] = bool(cfg.get("hardcore_only"))
        cfg["smart_polling"] = bool(cfg.get("smart_polling"))
        if cfg.get("rarity_source") not in RA_RARITY_SOURCES:
            cfg["rarity_source"] = "percent"
        lo, hi = RA_RATIO_RANGE
        ratios = []
        for name in ("ratio_uncommon", "ratio_rare", "ratio_ultra"):
            try:
                value = float(cfg.get(name))
            except (TypeError, ValueError):
                value = RA_DEFAULTS[name]
            ratios.append(max(lo, min(hi, value)))
        ratios.sort()                      # uncommon <= rare <= ultra, whatever was saved
        cfg["ratio_uncommon"], cfg["ratio_rare"], cfg["ratio_ultra"] = ratios
        default, lo, hi = RA_POLL_RANGE
        cfg["poll_seconds"] = max(lo, min(hi, _ra_int(cfg.get("poll_seconds"), default)))
        return cfg

    def _ra_save_cfg(self, cfg: Dict[str, Any]) -> None:
        os.makedirs(os.path.dirname(RA_SETTINGS_FILE), exist_ok=True)
        tmp = RA_SETTINGS_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as stream:
            json.dump({k: cfg.get(k, RA_DEFAULTS[k]) for k in RA_DEFAULTS}, stream, indent=2)
        try:
            os.chmod(tmp, 0o600)
        except OSError:
            pass
        os.replace(tmp, RA_SETTINGS_FILE)

    async def get_ra_state(self) -> Dict[str, Any]:
        cfg = self._ra_cfg()
        key = cfg["api_key"]
        return {
            "username": cfg["username"],
            "key_saved": bool(key),
            "key_hint": ("..." + key[-4:]) if len(key) >= 4 else "",
            "enabled": cfg["enabled"],
            "poll_seconds": cfg["poll_seconds"],
            "show_points": cfg["show_points"],
            "hardcore_only": cfg["hardcore_only"],
            "smart_polling": cfg["smart_polling"],
            "rarity_source": cfg["rarity_source"],
            "ratio_uncommon": cfg["ratio_uncommon"],
            "ratio_rare": cfg["ratio_rare"],
            "ratio_ultra": cfg["ratio_ultra"],
            "ratio_range": list(RA_RATIO_RANGE),
            "mode": self._ra_mode,
            "hint_files": self._ra_hint_files_seen,
            "hints": self._ra_hint_count,
            "poll_range": list(RA_POLL_RANGE),
            "status": self._ra_status,
            "error": self._ra_error,
            "last_check": self._ra_last_check,
            "last_unlock": self._ra_last_unlock,
            "unlock_count": self._ra_unlock_count,
            "log_dir": getattr(decky, "DECKY_PLUGIN_LOG_DIR", ""),
        }

    async def set_ra_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(config, dict):
            return {"ok": False, "error": "Bad request."}
        cfg = self._ra_cfg()
        login_before = (cfg["username"], cfg["api_key"])
        if "username" in config:
            name = str(config.get("username") or "").strip()
            if name and not RA_USERNAME_RE.match(name):
                return {"ok": False, "error": "Usernames only use letters, numbers, dot, dash and underscore."}
            cfg["username"] = name
        if "api_key" in config:
            key = str(config.get("api_key") or "").strip()
            if key:                      # empty = keep the saved key
                if not RA_KEY_RE.match(key):
                    return {"ok": False, "error": "That doesn't look like an API key (letters and numbers, 16+ characters)."}
                cfg["api_key"] = key
        if config.get("clear_key"):
            cfg["api_key"] = ""
        for flag in ("enabled", "show_points", "hardcore_only", "smart_polling"):
            if flag in config:
                cfg[flag] = bool(config[flag])
        if config.get("rarity_source") in RA_RARITY_SOURCES:
            cfg["rarity_source"] = config["rarity_source"]
        for name in ("ratio_uncommon", "ratio_rare", "ratio_ultra"):
            if name in config:
                try:
                    cfg[name] = float(config[name])
                except (TypeError, ValueError):
                    pass
        if "poll_seconds" in config:
            _d, lo, hi = RA_POLL_RANGE
            cfg["poll_seconds"] = max(lo, min(hi, _ra_int(config["poll_seconds"], RA_POLL_RANGE[0])))
        await asyncio.to_thread(self._ra_save_cfg, cfg)
        if (cfg["username"], cfg["api_key"]) != login_before:
            self._ra_rebaseline = True   # different account/key: don't toast its old unlocks
        self._ra_wake.set()
        return {"ok": True, "state": await self.get_ra_state()}

    async def _ra_api(self, endpoint: str, params: Dict[str, Any], cfg: Optional[Dict[str, Any]] = None) -> Any:
        cfg = cfg or self._ra_cfg()
        if not cfg["api_key"]:
            raise RuntimeError("No RetroAchievements API key saved.")
        query = dict(params)
        query["y"] = cfg["api_key"]
        url = "%s%s?%s" % (RA_API_BASE, endpoint, urllib.parse.urlencode(query))

        def _request() -> Any:
            if self._ra_keepalive_ok:
                try:
                    return self._ra_request_keepalive(url)
                except _RaNoKeepalive:
                    pass
            return self._ra_request_curl(url)

        return await asyncio.to_thread(_request)

    def _ra_request_keepalive(self, url: str) -> Any:
        """One GET over a connection that is kept open between checks, so
        most checks skip the TCP/TLS handshake. Anything unusual (no
        http.client/ssl, a redirect) falls back to the curl path."""
        try:
            import http.client as hc
        except Exception:
            self._ra_keepalive_ok = False
            raise _RaNoKeepalive()
        parts = urllib.parse.urlsplit(url)
        path = parts.path + ("?" + parts.query if parts.query else "")
        key = (parts.scheme, parts.netloc)
        headers = {"User-Agent": "RetroAchievementsToasts/1.0 (Decky)", "Accept": "application/json"}
        with self._ra_conn_lock:
            for attempt in (0, 1):
                conn, stamp = self._ra_conn.get(key, (None, 0.0))
                if conn is not None and time.monotonic() - stamp > RA_KEEPALIVE_SECONDS:
                    self._ra_close_conn(key)
                    conn = None
                fresh = conn is None
                try:
                    if conn is None:
                        cls = hc.HTTPSConnection if parts.scheme == "https" else hc.HTTPConnection
                        conn = cls(parts.netloc, timeout=RA_HTTP_TIMEOUT_SECONDS)
                    conn.request("GET", path, headers=headers)
                    resp = conn.getresponse()
                    body = resp.read()
                    code = resp.status
                    if resp.will_close:
                        conn.close()
                        self._ra_conn.pop(key, None)
                    else:
                        self._ra_conn[key] = (conn, time.monotonic())
                    break
                except (hc.HTTPException, OSError) as err:
                    self._ra_close_conn(key)
                    if conn is not None:
                        try:
                            conn.close()
                        except Exception:
                            pass
                    if not fresh and attempt == 0:
                        continue  # stale connection the server closed: retry once on a new one
                    if isinstance(err, ssl_error_types()):
                        self._ra_keepalive_ok = False
                        raise _RaNoKeepalive()
                    if isinstance(err, (socket.timeout, TimeoutError, ConnectionError, socket.gaierror, OSError)):
                        raise RaOfflineError("No connection to RetroAchievements (%s). Toasts will catch up when it is back." % (err.__class__.__name__))
                    raise RuntimeError("Could not reach RetroAchievements (%s)" % err)
        if 300 <= code < 400:
            raise _RaNoKeepalive()
        if code != 200:
            raise RuntimeError(ra_friendly_http_error(code))
        try:
            return json.loads(body.decode("utf-8", "replace"))
        except ValueError:
            raise RuntimeError("RetroAchievements sent something that isn't JSON.")

    def _ra_close_conn(self, key: Any) -> None:
        conn, _stamp = self._ra_conn.pop(key, (None, 0.0))
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass

    def _ra_request_curl(self, url: str) -> Any:
        if True:
            env = os.environ.copy()
            env.pop("LD_LIBRARY_PATH", None)
            env.pop("LD_PRELOAD", None)
            # The API key goes in the URL, so keep it out of `ps` by passing
            # the URL through a curl config on stdin.
            conf = 'url = "%s"\n' % url.replace("\\", "\\\\").replace('"', '\\"')
            result = subprocess.run(
                [
                    "curl", "--silent", "--show-error", "--location",
                    "--max-time", str(RA_HTTP_TIMEOUT_SECONDS),
                    "--user-agent", "RetroAchievementsToasts/1.0 (Decky)",
                    "--write-out", "\n%{http_code}",
                    "--config", "-",
                ],
                input=conf, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                env=env, check=False,
            )
            if result.returncode in RA_CURL_OFFLINE_CODES:
                raise RaOfflineError("No connection to RetroAchievements (curl %d). Toasts will catch up when it is back." % result.returncode)
            if result.returncode != 0:
                raise RuntimeError("Could not reach RetroAchievements (curl %d: %s)" % (
                    result.returncode, (result.stderr or "").strip()[-160:]))
            body, _sep, code_text = (result.stdout or "").rpartition("\n")
            code = _ra_int(code_text)
            if code != 200:
                raise RuntimeError(ra_friendly_http_error(code))
            try:
                return json.loads(body)
            except ValueError:
                raise RuntimeError("RetroAchievements sent something that isn't JSON.")

    async def _ra_progress(self, game_id: int, cfg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if game_id <= 0:
            return None
        try:
            data = await self._ra_api(
                "API_GetGameInfoAndUserProgress.php", {"u": cfg["username"], "g": game_id}, cfg
            )
            return data if isinstance(data, dict) else None
        except Exception as err:
            decky.logger.warning("RetroAchievements game info failed for %s: %s", game_id, err)
            return None

    def _ra_cache_image(self, path: Any, name: str) -> Optional[str]:
        urls = ra_media_urls(path)
        if not urls:
            return None
        safe = re.sub(r"[^A-Za-z0-9_.-]", "_", name)[:80] or "img"
        target = os.path.join(RA_ICON_CACHE_DIR, safe + ".png")
        try:
            with open(target, "rb") as stream:
                if self._looks_like_image(stream.read()):
                    return target
        except OSError:
            pass
        try:
            os.makedirs(RA_ICON_CACHE_DIR, exist_ok=True)
        except OSError:
            return None
        env = os.environ.copy()
        env.pop("LD_LIBRARY_PATH", None)
        env.pop("LD_PRELOAD", None)
        for url in urls:
            try:
                result = subprocess.run(
                    ["curl", "--fail", "--silent", "--location", "--max-time", "8",
                     "--user-agent", "RetroAchievementsToasts/1.0 (Decky)", url],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, check=False,
                )
            except Exception as err:
                decky.logger.warning("RA image download failed %s: %s", url, err)
                continue
            if result.returncode == 0 and self._looks_like_image(result.stdout):
                tmp = target + ".tmp"
                try:
                    with open(tmp, "wb") as stream:
                        stream.write(result.stdout)
                    os.replace(tmp, target)
                    return target
                except OSError as err:
                    decky.logger.warning("RA image store failed %s: %s", target, err)
                    return None
        return None

    async def _emit_ra_unlock(
        self,
        item: Dict[str, Any],
        progress: Optional[Dict[str, Any]],
        cfg: Dict[str, Any],
        test_tier: Optional[str] = None,
    ) -> None:
        """Show one RetroAchievements unlock with the Finally popup engine."""
        settings = self._load_settings()
        weighted = cfg.get("rarity_source") == "weighted"
        if test_tier:
            percent = self._sample_percent_for_tier(test_tier, settings)      # forces the tier shown
            tier = self._rarity_tier(percent, settings)
        else:
            percent = ra_percent(progress, item["id"])
            tier = None
            if weighted:
                tier = ra_weighted_tier(item, cfg, bool(settings.get("rarity_tiers_enabled", True)))
            if tier is None:
                tier = self._rarity_tier(percent, settings)
        is_rare = tier in ("rare", "ultra_rare")

        badge_name = os.path.splitext(os.path.basename(item.get("badge") or ""))[0] or ("ach_" + item["id"])
        icon_path = await asyncio.to_thread(self._ra_cache_image, item.get("badge"), "badge_" + badge_name)
        placeholder_path = None
        if (not icon_path) or settings.get("placeholder_icon") == "game_icon":
            icon_name = os.path.splitext(os.path.basename(item.get("game_icon") or ""))[0] or str(item.get("game_id"))
            placeholder_path = await asyncio.to_thread(self._ra_cache_image, item.get("game_icon"), "game_" + icon_name)
            if not icon_path and settings.get("placeholder_icon") != "trophy":
                icon_path = placeholder_path
        game_art_path = None
        needs_art = settings.get("overlay_template") == "game_art" or (
            settings.get("game_art_gradient_enabled") and not settings.get("template_colors_enabled")
        )
        if needs_art and isinstance(progress, dict):
            art = progress.get("ImageIngame") or progress.get("ImageTitle") or progress.get("ImageBoxArt")
            if art:
                game_art_path = await asyncio.to_thread(
                    self._ra_cache_image, art, "art_%s" % (item.get("game_id") or "x")
                )

        timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
        payload = {
            "title": item["title"],
            "subtitle": ra_subtitle(item),
            "points_text": ra_points_text(item, cfg["show_points"], weighted),
            "is_rare": is_rare,
            "tier": tier,
            "game_name": item.get("game_title") or "",
            "percent": float(percent) if isinstance(percent, (int, float)) else None,
            "timestamp": timestamp,
            "appid": None,
            "achievement_id": item["id"],
            "icon_url": (ra_media_urls(item.get("badge")) or [None])[0],
            "icon_path": icon_path,
            "placeholder_icon_path": placeholder_path,
            "game_art_path": game_art_path,
            "settings_appid": None,
        }
        asyncio.create_task(self._show_gamescope_overlay(payload))
        await decky.emit("finally_show", payload)
        self._last_match_timestamp = timestamp
        self._last_match_sample = "%s / %s" % (item.get("game_title"), item["title"])
        self._last_match_source = "retroachievements-test" if test_tier else "retroachievements"
        if not test_tier:
            self._ra_unlock_count += 1
            self._ra_last_activity = time.monotonic()
            self._ra_burst_until = 0.0
            self._ra_last_unlock = {
                "title": item["title"], "game": item.get("game_title") or "",
                "hardcore": bool(item.get("hardcore")), "at": timestamp,
            }
        decky.logger.info("RetroAchievements toast: %s - %s (%s)", item.get("game_title"), item["title"], tier)

    async def _emit_ra_completion(self, game_title: str, delay: float = COMPLETION_DELAY_SECONDS) -> None:
        try:
            if delay > 0:
                await asyncio.sleep(delay)
            settings = self._load_settings()
            title_key = str(settings.get("completion_title", COMPLETION_TITLE_DEFAULT))
            timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
            payload = {
                "title": COMPLETION_TITLES.get(title_key, COMPLETION_TITLES[COMPLETION_TITLE_DEFAULT]),
                "subtitle": game_title or "Mastery",
                "is_rare": True, "percent": None, "timestamp": timestamp, "appid": None,
                "achievement_id": None, "icon_url": None, "icon_path": None,
                "placeholder_icon_path": None, "game_art_path": None, "settings_appid": None,
                "template_override": COMPLETION_TEMPLATE, "min_seconds": COMPLETION_MIN_SECONDS,
                "completion": True,
            }
            asyncio.create_task(self._show_gamescope_overlay(payload))
            await decky.emit("finally_show", payload)
        except Exception as err:
            decky.logger.warning("RetroAchievements completion toast failed: %s", err)

    async def _ra_poll_once(self, cfg: Dict[str, Any]) -> None:
        now_wall = time.time()
        if self._ra_rebaseline or self._ra_last_ok is None:
            minutes = 10
        else:
            minutes = max(3, min(120, int((now_wall - self._ra_last_ok) / 60) + 3))
        data = await self._ra_api("API_GetUserRecentAchievements.php", {"u": cfg["username"], "m": minutes}, cfg)
        unlocks = ra_parse_unlocks(data)
        fresh = ra_select_new(
            unlocks, self._ra_seen, self._ra_recent_ids, time.monotonic(), cfg["hardcore_only"]
        )
        if unlocks:
            self._ra_last_game_id = unlocks[-1]["game_id"] or self._ra_last_game_id
        first_pass = self._ra_rebaseline or self._ra_last_ok is None
        self._ra_rebaseline = False
        self._ra_last_ok = now_wall
        self._ra_last_check = dt.datetime.now(dt.timezone.utc).isoformat()
        if first_pass:
            return          # first look only records what is already unlocked
        progress_by_game: Dict[int, Optional[Dict[str, Any]]] = {}
        for item in fresh:
            gid = item["game_id"]
            if gid not in progress_by_game:
                progress_by_game[gid] = await self._ra_progress(gid, cfg)
            await self._emit_ra_unlock(item, progress_by_game[gid], cfg)
        done = set()
        for item in fresh:
            gid = item["game_id"]
            if gid in done:
                continue
            done.add(gid)
            if ra_is_complete(progress_by_game.get(gid)) and self._load_settings().get("completion_toast_enabled", True):
                last = self._ra_completion_last.get(gid)
                if last is None or time.monotonic() - last > COMPLETION_DEDUPE_SECONDS:
                    self._ra_completion_last[gid] = time.monotonic()
                    asyncio.create_task(self._emit_ra_completion(item.get("game_title") or ""))

    async def _watch_ra(self) -> None:
        failures = 0
        while not self._stop_event.is_set():
            cfg = self._ra_cfg()
            wait = float(cfg["poll_seconds"])
            if not cfg["enabled"]:
                self._ra_status, self._ra_error = "paused", None
                wait = 3.0
            elif not cfg["username"] or not cfg["api_key"]:
                self._ra_status, self._ra_error = "needs_setup", None
                wait = 3.0
            else:
                try:
                    await self._ra_poll_once(cfg)
                    self._ra_status, self._ra_error = "watching", None
                    failures = 0
                    now = time.monotonic()
                    since = None if self._ra_last_activity is None else now - self._ra_last_activity
                    wait, self._ra_mode = ra_next_interval(
                        cfg["poll_seconds"], cfg["smart_polling"], await self._ra_emulator_cached(),
                        since, now - self._ra_started, self._ra_burst_until - now,
                    )
                except asyncio.CancelledError:
                    raise
                except RaOfflineError as err:
                    failures += 1
                    self._ra_status, self._ra_error = "offline", str(err)[:240]
                    wait = min(30.0, 4.0 * failures)
                except Exception as err:
                    failures += 1
                    self._ra_status = "error"
                    self._ra_error = str(err)[:240]
                    decky.logger.warning("RetroAchievements poll failed (%d): %s", failures, err)
                    wait = min(120.0, wait * (1 + failures))
            try:
                await asyncio.wait_for(self._ra_wake.wait(), timeout=wait)
            except asyncio.TimeoutError:
                pass
            self._ra_wake.clear()

    async def ra_check_connection(self) -> Dict[str, Any]:
        cfg = self._ra_cfg()
        lines: List[Dict[str, Any]] = []
        if not cfg["username"]:
            return {"ok": False, "lines": [{"ok": False, "text": "No username saved."}]}
        if not cfg["api_key"]:
            return {"ok": False, "lines": [{"ok": False, "text": "No API key saved."}]}
        ok = True
        try:
            profile = await self._ra_api("API_GetUserProfile.php", {"u": cfg["username"]}, cfg)
            if not isinstance(profile, dict) or not profile.get("User"):
                raise RuntimeError("RetroAchievements didn't return a profile for that name.")
            lines.append({"ok": True, "text": "Logged in as %s (%s points)." % (
                profile.get("User"), profile.get("TotalPoints", "?"))})
            presence = str(profile.get("RichPresenceMsg") or "").strip()
            if presence:
                lines.append({"ok": True, "text": "Now: %s" % presence[:90]})
        except Exception as err:
            ok = False
            lines.append({"ok": False, "text": str(err)})
        if ok:
            try:
                data = await self._ra_api(
                    "API_GetUserRecentAchievements.php", {"u": cfg["username"], "m": 1440}, cfg
                )
                count = len(ra_parse_unlocks(data))
                lines.append({"ok": True, "text": "Unlock feed works (%d in the last day)." % count})
            except Exception as err:
                ok = False
                lines.append({"ok": False, "text": "Unlock feed failed: %s" % err})
        helper = os.path.join(decky.DECKY_PLUGIN_DIR, FINALLY_OVERLAY_HELPER_NAME)
        lines.append({"ok": os.path.exists(helper), "text": "Popup helper %s." % ("found" if os.path.exists(helper) else "missing")})
        return {"ok": ok, "lines": lines}

    async def _ra_test_item(self) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]], Dict[str, Any]]:
        """A real recent unlock to preview with (real badge and game), or a sample."""
        cfg = self._ra_cfg()
        item: Optional[Dict[str, Any]] = None
        if cfg["username"] and cfg["api_key"]:
            try:
                data = await self._ra_api(
                    "API_GetUserRecentAchievements.php", {"u": cfg["username"], "m": 60 * 24 * 30}, cfg
                )
                unlocks = ra_parse_unlocks(data)
                if unlocks:
                    item = random.choice(unlocks)
            except Exception as err:
                decky.logger.warning("RA test: could not fetch a real unlock: %s", err)
        if item is None:
            item = {
                "id": "0", "title": "Sample Achievement", "description": "Preview of a RetroAchievements toast",
                "points": 10, "hardcore": False, "game_id": 0, "game_title": "Sample Game", "console": "",
                "badge": "", "game_icon": "", "date": "",
            }
        return item, None, cfg

    async def _run_tier_test(self, tier: str) -> None:       # replaces the Steam-based test
        item, progress, cfg = await self._ra_test_item()
        await self._emit_ra_unlock(item, progress, cfg, test_tier=tier)

    async def test_completion_popup(self) -> None:
        item, _progress, _cfg = await self._ra_test_item()
        await self._emit_ra_completion(item.get("game_title") or "Sample Game", delay=0.0)

    # ------------------------------------------------------------------
    # v1.1: smart polling, local hints, game list, login import
    # ------------------------------------------------------------------

    def _ra_hint_files(self) -> List[str]:
        home = getattr(decky, "DECKY_USER_HOME", "") or "/home/deck"
        patterns = [
            ".config/retroarch/logs/*.log",
            ".var/app/org.libretro.RetroArch/config/retroarch/logs/*.log",
            ".config/PCSX2/logs/*.txt",
            ".var/app/net.pcsx2.PCSX2/config/PCSX2/logs/*.txt",
            ".local/share/duckstation/*.log",
            ".var/app/org.duckstation.DuckStation/data/duckstation/*.log",
            ".var/app/org.ppsspp.PPSSPP/config/ppsspp/*.log",
            "Emulation/saves/retroarch/logs/*.log",
        ]
        found: List[str] = []
        cutoff = time.time() - 6 * 3600
        for pattern in patterns:
            for path in glob.glob(os.path.join(home, pattern)):
                try:
                    if os.path.isfile(path) and os.path.getmtime(path) > cutoff:
                        found.append(path)
                except OSError:
                    continue
        return sorted(set(found))[:12]

    def _ra_scan_hints(self, offsets: Dict[str, int], first: bool) -> bool:
        """Reads what was appended to the emulator logs since last time.
        True when any new line mentions achievements. Never raises."""
        hit = False
        for path in self._ra_hint_files():
            try:
                size = os.path.getsize(path)
            except OSError:
                continue
            if path not in offsets or first:
                offsets[path] = size          # start at the end: only new lines count
                continue
            if size < offsets[path]:
                offsets[path] = 0              # log was rotated or truncated
            if size == offsets[path]:
                continue
            try:
                with open(path, "rb") as stream:
                    stream.seek(offsets[path])
                    chunk = stream.read(min(size - offsets[path], 65536))
                offsets[path] = size
            except OSError:
                continue
            if RA_HINT_LINE_RE.search(chunk.decode("utf-8", "ignore")):
                hit = True
        self._ra_hint_files_seen = len(offsets)
        return hit

    async def _watch_ra_hints(self) -> None:
        """Wake the poller the moment an emulator log mentions an achievement.
        The log text is only a nudge: what is shown always comes from the API."""
        offsets: Dict[str, int] = {}
        first = True
        while not self._stop_event.is_set():
            try:
                if await asyncio.to_thread(self._ra_scan_hints, offsets, first):
                    self._ra_burst_until = time.monotonic() + RA_BURST_LENGTH_SECONDS
                    self._ra_hint_count += 1
                    self._ra_wake.set()
            except asyncio.CancelledError:
                raise
            except Exception as err:
                decky.logger.warning("RetroAchievements log hints: %s", err)
            first = False
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=2.0)
            except asyncio.TimeoutError:
                pass

    async def _ra_emulator_cached(self) -> bool:
        now = time.monotonic()
        if now - self._ra_emu_checked > 5.0:
            self._ra_emu_checked = now
            self._ra_emu_running = await asyncio.to_thread(ra_emulator_running)
        return self._ra_emu_running

    async def get_ra_game(self, game_id: Any = None) -> Dict[str, Any]:
        """Achievements of one game (the one you played last unless a game id
        is given), with your progress. Used by the Game tab."""
        cfg = self._ra_cfg()
        if not cfg["username"] or not cfg["api_key"]:
            return {"ok": False, "error": "Save your RetroAchievements login first."}
        try:
            gid = _ra_int(game_id)
            if gid <= 0:
                gid = self._ra_last_game_id
            recent: List[Dict[str, Any]] = []
            try:
                recent = ra_parse_recent_games(await self._ra_api(
                    "API_GetUserRecentlyPlayedGames.php", {"u": cfg["username"], "c": 6}, cfg))
            except RaOfflineError:
                raise
            except Exception as err:
                decky.logger.warning("RetroAchievements recent games failed: %s", err)
            if gid <= 0 and recent:
                gid = recent[0]["game_id"]
            if gid <= 0:
                return {"ok": False, "error": "No games found on your profile yet. Play one first.", "recent": recent}
            data = await self._ra_api("API_GetGameInfoAndUserProgress.php", {"u": cfg["username"], "g": gid}, cfg)
            game = ra_parse_game(data)
            if game is None:
                return {"ok": False, "error": "RetroAchievements has no achievement data for that game.", "recent": recent}
            game["game_id"] = gid
            for item in game["achievements"]:
                item["badge_url"] = (ra_media_urls(item["badge"]) or [""])[0]
            return {"ok": True, "game": game, "recent": recent}
        except Exception as err:
            return {"ok": False, "error": str(err)[:240]}

    async def get_ra_recent(self) -> Dict[str, Any]:
        """Your newest unlocks (last 7 days), newest first."""
        cfg = self._ra_cfg()
        if not cfg["username"] or not cfg["api_key"]:
            return {"ok": False, "error": "Save your RetroAchievements login first.", "items": []}
        try:
            data = await self._ra_api(
                "API_GetUserRecentAchievements.php", {"u": cfg["username"], "m": 60 * 24 * 7}, cfg)
            items = list(reversed(ra_parse_unlocks(data)))[:12]
            for item in items:
                item["badge_url"] = (ra_media_urls(item["badge"]) or [""])[0]
            return {"ok": True, "items": items}
        except Exception as err:
            return {"ok": False, "error": str(err)[:240], "items": []}

    def _ra_login_files(self) -> List[str]:
        home = getattr(decky, "DECKY_USER_HOME", "") or "/home/deck"
        folders = [os.path.join(home, "Downloads"), home, os.path.dirname(RA_SETTINGS_FILE)]
        return [os.path.join(folder, name) for folder in folders for name in RA_LOGIN_FILE_NAMES]

    async def ra_import_login_file(self) -> Dict[str, Any]:
        """Takes the username and API key from a small text file in Downloads
        (typing 32 characters on the Deck is painful), saves them, then
        deletes that file so the key doesn't sit around in plain text."""
        for path in self._ra_login_files():
            if not os.path.isfile(path):
                continue
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as stream:
                    text = stream.read(4096)
            except OSError as err:
                return {"ok": False, "error": "Could not read %s: %s" % (os.path.basename(path), err)}
            username, key = ra_parse_login_text(text)
            if not key:
                return {"ok": False, "error": "%s has no valid API key. Put the username on line 1 and the key on line 2." % os.path.basename(path)}
            patch: Dict[str, Any] = {"api_key": key}
            if username:
                patch["username"] = username
            result = await self.set_ra_config(patch)
            if not result.get("ok"):
                return result
            removed = False
            try:
                os.remove(path)
                removed = True
            except OSError:
                pass
            return {"ok": True, "state": result.get("state"), "file": os.path.basename(path), "removed": removed,
                    "username_found": bool(username)}
        return {"ok": False, "error": "No login file found. Create ~/Downloads/retroachievements.txt with your username on line 1 and your Web API key on line 2."}

    # --- local schema: colored icons with no key and no network ---------------

    # ------------------------------------------------------------------
    # Colored-icon guarantee (no API key needed)
    #
    # Steam's local librarycache JSON keeps ONE `strImage` per achievement
    # and it reflects the state when Steam last wrote the file. The fast
    # Steamworks poll often fires before Steam rewrites it, so the entry can
    # still point at the GRAY (locked) icon -- most visible on newly
    # released games whose cache has only ever been written in the locked
    # state. The old retry only ran when the icon was *missing*, never when
    # it was present-but-gray. The methods below detect a gray icon and try,
    # in order: the public Steam Community achievements page (keyless,
    # colored icons, matched by title), then short re-reads of the local
    # cache waiting for Steam to swap in the colored hash.
    # ------------------------------------------------------------------
