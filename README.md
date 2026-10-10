# RetroAchievements Toasts

Achievement popups for **RetroAchievements** on Steam Deck (Decky Loader). When your emulator unlocks an
achievement, a popup appears over the game, with sound, the real badge, points and rarity.

It reuses the popup engine of the [Finally Achievement Plugin](https://github.com/otisabi/finally-achievement-plugin)
by otisabi (BSD-3-Clause): 18 templates, colors, glow, size, position, rarity tiers and sounds. The Steam
detection was replaced with a RetroAchievements watcher, so it only reacts to RetroAchievements unlocks.

## Install

You do not need to build anything. Download `retroachievements-toasts-<version>.zip` from the **Releases** page of
this repository, then on the Deck:

1. Decky Loader settings, General: turn on **Developer mode**.
2. Developer tab: **Install plugin from ZIP file**, pick the downloaded zip (or paste the zip's direct URL).
3. Decky reloads. Open the Quick Access menu, then RetroAchievements Toasts.

To update, install the newer zip the same way. Your login and settings are kept.

## How it works

The emulator (RetroArch, DuckStation, PCSX2, PPSSPP, Dolphin, ...) reports each unlock to retroachievements.org.
This plugin asks the RetroAchievements Web API for your newest unlocks and shows a popup for each new one. Nothing is
hooked into the emulator, so it works with any emulator that is logged in to RetroAchievements, including ones
launched from EmuDeck or as non-Steam games.

- **Fast while you play.** Checks run every few seconds (default 10) while an emulator is open. When none is open and
  nothing was unlocked lately, they slow to every 20-60 seconds ("Rest when no emulator is open", on by default).
- **Log hints.** If an emulator writes a line about achievements to its log file, the next check happens immediately,
  then once a second for 12 seconds. This only speeds things up: what you see always comes from the website. Emulator
  logs are only found when the emulator writes one to a known place, so this is a bonus, not a requirement.
- **Offline.** If the Deck loses its connection the panel says so, and the missed unlocks are shown when it returns.

## Setup

1. Open the Quick Access menu, then RetroAchievements Toasts.
2. Enter your RetroAchievements username and your **Web API key**
   (retroachievements.org, Settings, Keys, "Web API Key"), then press Save login.
   Typing 32 characters is slow, so you can instead create `~/Downloads/retroachievements.txt` with the username on
   line 1 and the key on line 2 and press "Import login from file" (the file is deleted afterwards).
3. Press Check connection. You should see four lines starting with OK.
4. Press "Test toast". Then play a game with achievements.

Your emulator must be logged in to RetroAchievements itself (a separate login, in the emulator's settings).

## Tabs

- **Setup**: login, on/off, check interval, points on the toast, hardcore only, rest mode.
- **Game achievements**: the game you played last, with progress, badges and a Locked/Unlocked filter. Press another
  game under "Switch game" to look at it.
- **Recent unlocks**: your newest unlocks.
- **Popup, Colors & style, Sound & tests, Advanced**: how the popup looks and sounds, from the Finally engine.

## Notes

- The first look after saving a login only records what is already unlocked, so old unlocks do not pop up.
- Softcore and hardcore unlocks of the same achievement show one popup. There is a "Hardcore only" switch.
- Rarity: either the share of players who have it (cutoffs in the Popup tab) or RetroPoints, RetroAchievements' own
  TrueRatio/Points weighting (Setup > Rarity; cutoffs 3x/8x/25x are untested guesses).
- The popup shows a points badge ("10 pts", "HC" for hardcore).
- Mastering a game (every achievement) shows the special completion popup.
- The API key is stored in `~/homebrew/settings/RetroAchievements Toasts/retro.json` (owner-only) and is never sent to the panel.

## Troubleshooting

- Panel says it couldn't start: look in `~/homebrew/logs/RetroAchievements Toasts/`.
- "refused the username or API key": re-enter the key. It is the Web API key, not your password.
- Sound but no popup: Advanced tab, "Popup Not Showing?".
- No popup for an unlock: confirm it appears on your RetroAchievements profile first. The plugin only shows what the website reports.

## Install (Deck)

    unzip retroachievements-toasts-1.1.0.zip
    sudo cp -r retroachievements-toasts ~/homebrew/plugins/ && sudo systemctl restart plugin_loader

## Development

    pnpm install && pnpm run build        # official build (rollup, @decky/rollup)
    pnpm run typecheck
    sh tests/run_all.sh                   # backend, stripped-Python and (optionally) panel UI tests

Without network access to the npm registry, `NODE_TOOLS=/path/to/node_modules node tools/build-offline.mjs` builds an
equivalent `dist/index.js` with esbuild. `tests/` holds a mock RetroAchievements server and a stand-in Decky, so
everything except the real popup overlay can be tested off the Deck.

## Building from source (developers only)

```
pnpm install && pnpm build        # or: node tools/build-offline.mjs (needs esbuild)
sh tests/run_all.sh
sh tools/package.sh out           # makes out/retroachievements-toasts-<version>.zip
```

Releasing: bump `version` in `plugin.json` and `package.json`, add a section to `CHANGELOG.md`, commit, then
`git tag v<version> && git push --tags`. The Release workflow tests, builds and attaches the zip.
