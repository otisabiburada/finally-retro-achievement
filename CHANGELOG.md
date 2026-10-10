# Changelog

## 1.3.0
- **Gentler polling.** Checks now reuse one open connection instead of a new one every time, which skips the
  connection and TLS setup on most checks. If that is not possible (a redirect, or Decky's Python lacks TLS), it falls back
  to `curl` as before. The connection is dropped when it has been idle for 25 s, and on unload.
- **Default check interval is 10 s** (was 6 s) while an emulator is open. Rest mode is unchanged. Existing installs keep
  the value they saved; the slider still goes from 3 to 60 s.

## 1.2.0
- **Points badge.** The popup now has its own badge showing the RetroAchievements points ("10 pts", plus "HC" for
  hardcore), no longer cut off by long descriptions. In RetroPoints mode it shows "10 pts (RP 45)".
- **RetroPoints rarity (new, optional).** Rarity can use RetroAchievements' own weighting (TrueRatio / Points) instead of
  the share of players. Setup > Rarity: choose "Players %" or "RetroPoints" and tune the three cutoffs.
  The defaults (3x, 8x, 25x) are guesses; adjust them after looking at real toasts.
- **Fix.** Changing any setting no longer re-baselines achievements (it could swallow an unlock); only a username or
  key change does.

## 1.1.0
- **Faster detection.** Checks run often while an emulator is open and rest (every 20-60 s) when none is. A line about
  achievements in an emulator's log file triggers an immediate check and a burst of 1-second checks. Log paths are
  best-effort guesses and are never required.
- **Offline handling.** A dropped connection shows "offline" and the plugin catches up on the missed unlocks when
  it returns.
- **Game achievements tab.** Progress, locked/unlocked filter, badges, points, rarity and unlock dates for the game you
  played last, plus a switch between your last five games.
- **Recent unlocks tab.** Your newest unlocks from the last 7 days.
- **Import login from file.** `~/Downloads/retroachievements.txt` (username on line 1, key on line 2); the file is
  deleted after import.
- **Steam code removed.** The Steam watchers, tracker, per-game profiles and Steam key code are gone: the backend went
  from about 4,600 to about 2,100 lines.
- **Repo.** Tests (backend, stripped-Python, panel UI), CI workflow, offline build script, `pnpm` scripts.

## 1.0.0
- First release: RetroAchievements polling with the Finally popup engine.
