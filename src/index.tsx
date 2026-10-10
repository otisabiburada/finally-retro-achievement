import {
  addEventListener,
  call,
  definePlugin,
  removeEventListener,
} from "@decky/api";
import {
  ButtonItem,
  DialogButton,
  DropdownItem,
  Focusable,
  PanelSection,
  PanelSectionRow,
  SliderField,
  TextField,
  ToggleField,
  ColorPickerModal,
  showModal,
  staticClasses,
} from "@decky/ui";
import { useCallback, useEffect, useMemo, useState } from "react";
import { FaTrophy } from "react-icons/fa";
import {
  DEFAULT_SETTINGS,
  EVENT_NAME,
  FONT_SIZE_RANGES,
  DURATION_RANGE,
  GLOW_INTENSITY_RANGE,
  GRADIENT_DIRECTION_OPTIONS,
  OVERLAY_POSITION_OPTIONS,
  PLACEHOLDER_ICON_OPTIONS,
  COMPLETION_TITLE_OPTIONS,
  SOUND_SLOT_OPTIONS,
  type SoundEntry,
  type SoundsResponse,
  type SoundSlot,
  PERCENT_SIZE_RANGE,
  PERCENT_POSITION_OPTIONS,
  type PercentPosition,
  TIER_CUTOFF_RANGES,
  RING_SIZE_RANGE,
  OVERLAY_TEMPLATE_OPTIONS,
  SETTINGS_EVENT,
  type GradientDirection,
  type NotificationPayload,
  type OverlayPosition,
  type OverlayTemplate,
  type PlaceholderIcon,
  type CompletionTitle,
  type FinallySettings,
} from "./finallyThemes";
type OverlayCheckItem = { name: string; ok: boolean; detail: string; fatal?: boolean };
type OverlayCheckResult = {
  ok: boolean;
  verdict: string;
  checks: OverlayCheckItem[];
  last_status: string;
  last_error: string | null;
};

type BackendStatus = {
  gamescope_overlay_status?: string | null;
  gamescope_overlay_last_error?: string | null;
  settings: FinallySettings;
  last_match_timestamp: string | null;
  last_match_sample: string | null;
  last_match_source: string | null;
};

type DropdownSelection = {
  data: string;
};

type ColorSettingKey =
  | "normal_gradient_start"
  | "normal_gradient_end"
  | "rare_gradient_start"
  | "rare_gradient_end"
  | "normal_circle_color"
  | "rare_circle_color";

const parseHsla = (value: string) => {
  const match = value.match(
    /hsla?\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)%\s*,\s*(\d+(?:\.\d+)?)%\s*(?:,\s*(\d+(?:\.\d+)?)\s*)?\)/i,
  );
  if (!match) {
    return { h: 35, s: 98, l: 38, a: 0.94 };
  }

  return {
    h: Number(match[1]),
    s: Number(match[2]),
    l: Number(match[3]),
    a: match[4] ? Number(match[4]) : 1,
  };
};

const toErrorMessage = (value: unknown): string => {
  if (value instanceof Error) {
    return value.message;
  }
  return String(value);
};

const formatTimestamp = (value: string | null): string => {
  if (!value) {
    return "never";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString();
};


type PanelView = "retro" | "game" | "recent" | "popup" | "style" | "sound" | "advanced";
type ViewDropdownSelection = { data: PanelView };

const VIEW_OPTIONS: { data: PanelView; label: string }[] = [
  { data: "retro", label: "Setup" },
  { data: "game", label: "Game achievements" },
  { data: "recent", label: "Recent unlocks" },
  { data: "popup", label: "Popup" },
  { data: "style", label: "Colors & style" },
  { data: "sound", label: "Sound & tests" },
  { data: "advanced", label: "Advanced" },
];

// ---------------------------------------------------------------------------
// RetroAchievements tab
// ---------------------------------------------------------------------------
type RaState = {
  username: string;
  key_saved: boolean;
  key_hint: string;
  enabled: boolean;
  poll_seconds: number;
  show_points: boolean;
  hardcore_only: boolean;
  smart_polling: boolean;
  rarity_source: "percent" | "weighted";
  ratio_uncommon: number;
  ratio_rare: number;
  ratio_ultra: number;
  ratio_range: number[];
  mode: string;
  hint_files: number;
  hints: number;
  poll_range: number[];
  status: string;
  error: string | null;
  last_check: string | null;
  last_unlock: { title: string; game: string; hardcore: boolean; at: string } | null;
  unlock_count: number;
  log_dir: string;
};
type RaSaveResult = { ok: boolean; error?: string; state?: RaState };
type RaCheckResult = { ok: boolean; lines: { ok: boolean; text: string }[] };

function withTimeout<T>(promise: Promise<T>, ms: number): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    const timer = setTimeout(
      () => reject(new Error("The plugin's background part isn't answering.")),
      ms,
    );
    promise.then(
      (value) => {
        clearTimeout(timer);
        resolve(value);
      },
      (error) => {
        clearTimeout(timer);
        reject(error);
      },
    );
  });
}

function raStatusText(state: RaState): string {
  switch (state.status) {
    case "needs_setup":
      return "Add your RetroAchievements username and API key below.";
    case "watching":
      return `Watching ${state.username} for new unlocks (${
        state.mode === "idle" ? "resting, no emulator open" : state.mode === "burst" ? "checking now" : "checking often"
      }).`;
    case "offline":
      return state.error ?? "No connection. Toasts will catch up when it is back.";
    case "paused":
      return "Paused. Turn toasts on to start watching.";
    case "error":
      return state.error ?? "Could not reach RetroAchievements. Retrying.";
    default:
      return "Starting...";
  }
}

function RetroView({ onTest }: { onTest: () => void }) {
  const [state, setState] = useState<RaState | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [username, setUsername] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [check, setCheck] = useState<RaCheckResult | null>(null);
  const [usernameLoaded, setUsernameLoaded] = useState(false);

  const load = useCallback(async () => {
    try {
      const next = await withTimeout(call<[], RaState>("get_ra_state"), 8000);
      setState(next);
      setLoadError(null);
      if (!usernameLoaded) {
        setUsername(next.username);
        setUsernameLoaded(true);
      }
    } catch (error) {
      setLoadError(toErrorMessage(error));
    }
  }, [usernameLoaded]);

  useEffect(() => {
    void load();
    const timer = window.setInterval(() => void load(), 4000);
    return () => window.clearInterval(timer);
  }, [load]);

  const save = useCallback(async (patch: Record<string, unknown>, label: string) => {
    setBusy(label);
    setMessage(null);
    try {
      const result = await withTimeout(call<[Record<string, unknown>], RaSaveResult>("set_ra_config", patch), 10000);
      if (result.ok && result.state) {
        setState(result.state);
        return true;
      }
      setMessage(result.error ?? "Could not save.");
      return false;
    } catch (error) {
      setMessage(toErrorMessage(error));
      return false;
    } finally {
      setBusy(null);
    }
  }, []);

  const handleSaveLogin = useCallback(async () => {
    const ok = await save({ username: username.trim(), api_key: apiKey.trim() }, "login");
    if (ok) {
      setApiKey("");
      setMessage("Saved.");
    }
  }, [save, username, apiKey]);

  const handleImport = useCallback(async () => {
    setBusy("import");
    setMessage(null);
    try {
      const result = await withTimeout(
        call<[], { ok: boolean; error?: string; state?: RaState; file?: string; removed?: boolean }>("ra_import_login_file"),
        10000,
      );
      if (result.ok && result.state) {
        setState(result.state);
        setUsername(result.state.username);
        setMessage(`Imported from ${result.file}.${result.removed ? " The file was deleted." : " Please delete that file."}`);
      } else {
        setMessage(result.error ?? "Could not import.");
      }
    } catch (error) {
      setMessage(toErrorMessage(error));
    } finally {
      setBusy(null);
    }
  }, []);

  const handleCheck = useCallback(async () => {
    setBusy("check");
    setCheck(null);
    try {
      setCheck(await withTimeout(call<[], RaCheckResult>("ra_check_connection"), 40000));
    } catch (error) {
      setCheck({ ok: false, lines: [{ ok: false, text: toErrorMessage(error) }] });
    } finally {
      setBusy(null);
    }
  }, []);

  if (!state) {
    return (
      <PanelSection title="RetroAchievements">
        <PanelSectionRow>
          <div style={{ fontSize: 13 }}>
            {loadError
              ? `RetroAchievements Toasts couldn't start: ${loadError} Check ~/homebrew/logs/RetroAchievements Toasts/ and reopen this panel.`
              : "Loading..."}
          </div>
        </PanelSectionRow>
      </PanelSection>
    );
  }

  const range = state.poll_range.length === 3 ? state.poll_range : [10, 3, 60];
  const disabled = busy !== null;

  return (
    <>
      <PanelSection title="RetroAchievements">
        <PanelSectionRow>
          <div style={{ fontSize: 13, color: state.status === "error" || state.status === "offline" ? "#ff8a80" : undefined }}>
            {raStatusText(state)}
          </div>
        </PanelSectionRow>
        <PanelSectionRow>
          <ToggleField
            label="Show RetroAchievements toasts"
            checked={state.enabled}
            disabled={disabled}
            onChange={(value) => void save({ enabled: value }, "enabled")}
          />
        </PanelSectionRow>
        <PanelSectionRow>
          <TextField
            label="RetroAchievements username"
            value={username}
            disabled={disabled}
            onChange={(event) => setUsername(event.target.value)}
          />
        </PanelSectionRow>
        <PanelSectionRow>
          <TextField
            label="Web API key"
            description={
              state.key_saved
                ? `Saved (ends ${state.key_hint}). Leave empty to keep it.`
                : "retroachievements.org > Settings > Keys > Web API Key."
            }
            bIsPassword
            value={apiKey}
            disabled={disabled}
            onChange={(event) => setApiKey(event.target.value)}
          />
        </PanelSectionRow>
        <PanelSectionRow>
          <ButtonItem layout="below" disabled={disabled || username.trim().length === 0} onClick={() => void handleSaveLogin()}>
            {busy === "login" ? "Saving..." : "Save login"}
          </ButtonItem>
        </PanelSectionRow>
        <PanelSectionRow>
          <ButtonItem
            layout="below"
            disabled={disabled}
            onClick={() => void handleImport()}
            description="Easier than typing: put your username on line 1 and your Web API key on line 2 of ~/Downloads/retroachievements.txt. The file is deleted after it is imported."
          >
            {busy === "import" ? "Importing..." : "Import login from file"}
          </ButtonItem>
        </PanelSectionRow>
        <PanelSectionRow>
          <ButtonItem layout="below" disabled={disabled} onClick={() => void handleCheck()}>
            {busy === "check" ? "Checking..." : "Check connection"}
          </ButtonItem>
        </PanelSectionRow>
        {message && (
          <PanelSectionRow>
            <div style={{ fontSize: 12, opacity: 0.85 }}>{message}</div>
          </PanelSectionRow>
        )}
        {check && (
          <PanelSectionRow>
            <div style={{ fontSize: 12 }}>
              {check.lines.map((line, index) => (
                <div key={index} style={{ marginBottom: 3, color: line.ok ? undefined : "#ff8a80" }}>
                  <strong>{line.ok ? "OK" : "FAIL"}</strong> {line.text}
                </div>
              ))}
            </div>
          </PanelSectionRow>
        )}
        <PanelSectionRow>
          <ButtonItem layout="below" disabled={disabled} onClick={onTest}>
            Test toast (uses one of your recent unlocks)
          </ButtonItem>
        </PanelSectionRow>
      </PanelSection>
      <PanelSection title="Rarity">
        <PanelSectionRow>
          <Focusable style={{ display: "flex", gap: 6, width: "100%" }}>
            {([["percent", "Players %"], ["weighted", "RetroPoints"]] as const).map(([value, label]) => (
              <DialogButton
                key={value}
                disabled={disabled}
                onClick={() => void save({ rarity_source: value }, "rarity")}
                style={{
                  flex: 1,
                  minWidth: 0,
                  padding: "8px 4px",
                  fontSize: 12.5,
                  background: state.rarity_source === value ? "#1a9fff" : undefined,
                  color: state.rarity_source === value ? "#fff" : undefined,
                }}
              >
                {label}
              </DialogButton>
            ))}
          </Focusable>
        </PanelSectionRow>
        <PanelSectionRow>
          <div style={{ fontSize: 12, color: "rgba(255,255,255,0.65)" }}>
            {state.rarity_source === "percent"
              ? "Tier from the share of players who have the achievement. Cutoffs are in the Popup tab."
              : "Tier from RetroAchievements' own rarity weighting: RetroPoints divided by points. A common achievement is near 1x, a rare one is many times that. The popup badge also shows the RetroPoints (RP). If an achievement has no RetroPoints, the players % is used."}
          </div>
        </PanelSectionRow>
        {state.rarity_source === "weighted" &&
          ([
            ["ratio_uncommon", "Uncommon from", state.ratio_uncommon],
            ["ratio_rare", "Rare from", state.ratio_rare],
            ["ratio_ultra", "Ultra rare from", state.ratio_ultra],
          ] as const).map(([key, label, value]) => (
            <PanelSectionRow key={key}>
              <SliderField
                label={label}
                value={value}
                min={state.ratio_range[0]}
                max={state.ratio_range[1]}
                step={0.5}
                showValue
                valueSuffix="x"
                disabled={disabled}
                onChange={(next: number) => void save({ [key]: next }, key)}
              />
            </PanelSectionRow>
          ))}
      </PanelSection>
      <PanelSection title="Watching">
        <PanelSectionRow>
          <SliderField
            label="Check every"
            description="Shorter is quicker but asks RetroAchievements more often."
            value={state.poll_seconds}
            min={range[1]}
            max={range[2]}
            step={1}
            showValue
            valueSuffix=" s"
            disabled={disabled}
            onChange={(value) => void save({ poll_seconds: value }, "poll")}
          />
        </PanelSectionRow>
        <PanelSectionRow>
          <ToggleField
            label="Show points on the popup"
            description="A small badge with the points, for example 25 pts, plus HC for hardcore."
            checked={state.show_points}
            disabled={disabled}
            onChange={(value) => void save({ show_points: value }, "points")}
          />
        </PanelSectionRow>
        <PanelSectionRow>
          <ToggleField
            label="Hardcore unlocks only"
            description="Skip softcore unlocks."
            checked={state.hardcore_only}
            disabled={disabled}
            onChange={(value) => void save({ hardcore_only: value }, "hardcore")}
          />
        </PanelSectionRow>
        <PanelSectionRow>
          <ToggleField
            label="Rest when no emulator is open"
            description="Checks every 20 to 60 seconds while no emulator is running and nothing was unlocked lately. Saves battery and data. Turn off if popups ever feel slow."
            checked={state.smart_polling}
            disabled={disabled}
            onChange={(value) => void save({ smart_polling: value }, "smart")}
          />
        </PanelSectionRow>
        <PanelSectionRow>
          <div style={{ fontSize: 12, color: "rgba(255,255,255,0.65)" }}>
            {state.hint_files > 0
              ? `Emulator logs: ${state.hint_files} watched, ${state.hints} unlock hint(s) caught. A hint makes the next check happen at once.`
              : "Emulator logs: none found. That is fine; the plugin then relies on the check interval."}
          </div>
        </PanelSectionRow>
        <PanelSectionRow>
          <div style={{ fontSize: 12, color: "rgba(255,255,255,0.65)" }}>
            Your emulator must be logged in to RetroAchievements (RetroArch, DuckStation, PCSX2, PPSSPP and others
            do this in their own settings). A toast appears a few seconds after the emulator reports the unlock.
          </div>
        </PanelSectionRow>
        <PanelSectionRow>
          <div style={{ fontSize: 12, color: "rgba(255,255,255,0.65)" }}>
            {state.last_unlock
              ? `Last toast: ${state.last_unlock.title} (${state.last_unlock.game}${state.last_unlock.hardcore ? ", hardcore" : ""}). ${state.unlock_count} this session.`
              : "No unlocks seen yet this session."}
          </div>
        </PanelSectionRow>
      </PanelSection>
    </>
  );
}

// ---------------------------------------------------------------------------
// Game achievements + recent unlocks tabs (fed by RetroAchievements)
// ---------------------------------------------------------------------------
type RaAchievement = {
  id: string;
  title: string;
  description: string;
  points: number;
  true_ratio?: number;
  badge_url: string;
  unlocked: boolean;
  hardcore: boolean;
  earned: string;
  percent: number | null;
};
type RaGame = {
  game_id: number;
  title: string;
  console: string;
  total: number;
  unlocked: number;
  hardcore_unlocked: number;
  achievements: RaAchievement[];
};
type RaRecentGame = { game_id: number; title: string; console: string; total: number; unlocked: number };
type RaGameResult = { ok: boolean; error?: string; game?: RaGame; recent?: RaRecentGame[] };
type RaRecentItem = {
  id: string;
  title: string;
  game_title: string;
  points: number;
  true_ratio?: number;
  hardcore: boolean;
  date: string;
  badge_url: string;
};
type RaRecentResult = { ok: boolean; error?: string; items: RaRecentItem[] };
type GameFilter = "all" | "locked" | "unlocked";

const GAME_PAGE_SIZE = 15;

function formatRaDate(value: string): string {
  if (!value) return "";
  const parsed = new Date(value.replace(" ", "T") + "Z");
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString();
}

function BadgeImage({ url, locked }: { url: string; locked?: boolean }) {
  const [failed, setFailed] = useState(false);
  const box = { width: 48, height: 48, borderRadius: 6, flex: "0 0 48px", background: "rgba(255,255,255,0.08)" };
  if (!url || failed) return <div style={box} />;
  return (
    <img
      src={url}
      width={48}
      height={48}
      onError={() => setFailed(true)}
      style={{ ...box, objectFit: "cover", filter: locked ? "grayscale(1) brightness(0.6)" : "none" }}
    />
  );
}

function GameView() {
  const [result, setResult] = useState<RaGameResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [filter, setFilter] = useState<GameFilter>("all");
  const [shown, setShown] = useState(GAME_PAGE_SIZE);

  const load = useCallback(async (gameId: number | null) => {
    setLoading(true);
    setLoadError(null);
    try {
      const next = await withTimeout(call<[number | null], RaGameResult>("get_ra_game", gameId), 30000);
      setResult(next);
      setShown(GAME_PAGE_SIZE);
    } catch (error) {
      setLoadError(toErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load(null);
  }, [load]);

  const game = result?.game;
  const list = useMemo(() => {
    const all = game?.achievements ?? [];
    if (filter === "locked") return all.filter((item) => !item.unlocked);
    if (filter === "unlocked") return all.filter((item) => item.unlocked);
    return all;
  }, [game, filter]);
  const percent = game && game.total > 0 ? Math.round((game.unlocked / game.total) * 100) : 0;

  return (
    <>
      <PanelSection title={game ? game.title : "Game achievements"}>
        {loading && (
          <PanelSectionRow>
            <div style={{ fontSize: 13 }}>Loading...</div>
          </PanelSectionRow>
        )}
        {(loadError || (result && !result.ok)) && (
          <PanelSectionRow>
            <div style={{ fontSize: 13, color: "#ff8a80" }}>{loadError ?? result?.error}</div>
          </PanelSectionRow>
        )}
        {game && (
          <PanelSectionRow>
            <div style={{ width: "100%" }}>
              <div style={{ fontSize: 12, opacity: 0.7 }}>{game.console}</div>
              <div style={{ fontSize: 13, margin: "4px 0" }}>
                {game.unlocked} of {game.total} unlocked ({percent}%)
                {game.hardcore_unlocked > 0 ? `, ${game.hardcore_unlocked} in hardcore` : ""}
              </div>
              <div style={{ height: 6, borderRadius: 3, background: "rgba(255,255,255,0.12)", overflow: "hidden" }}>
                <div style={{ width: `${percent}%`, height: "100%", background: "#1a9fff" }} />
              </div>
            </div>
          </PanelSectionRow>
        )}
        <PanelSectionRow>
          <ButtonItem layout="below" disabled={loading} onClick={() => void load(game ? game.game_id : null)}>
            Refresh
          </ButtonItem>
        </PanelSectionRow>
      </PanelSection>

      {result?.recent && result.recent.length > 1 && (
        <PanelSection title="Switch game">
          {result.recent.slice(0, 5).map((item) => (
            <PanelSectionRow key={item.game_id}>
              <ButtonItem
                layout="below"
                disabled={loading || (game !== undefined && game.game_id === item.game_id)}
                onClick={() => void load(item.game_id)}
                description={`${item.console}, ${item.unlocked} of ${item.total}`}
              >
                {item.title}
              </ButtonItem>
            </PanelSectionRow>
          ))}
        </PanelSection>
      )}

      {game && (
        <PanelSection title="Achievements">
          <PanelSectionRow>
            <Focusable style={{ display: "flex", gap: 6, width: "100%" }}>
              {(["all", "locked", "unlocked"] as GameFilter[]).map((name) => (
                <DialogButton
                  key={name}
                  onClick={() => {
                    setFilter(name);
                    setShown(GAME_PAGE_SIZE);
                  }}
                  style={{
                    flex: 1,
                    minWidth: 0,
                    padding: "8px 4px",
                    fontSize: 12.5,
                    background: filter === name ? "#1a9fff" : undefined,
                    color: filter === name ? "#fff" : undefined,
                  }}
                >
                  {name === "all" ? "All" : name === "locked" ? "Locked" : "Unlocked"}
                </DialogButton>
              ))}
            </Focusable>
          </PanelSectionRow>
          {list.slice(0, shown).map((item) => (
            <PanelSectionRow key={item.id}>
              <Focusable style={{ display: "flex", gap: 10, width: "100%", padding: "4px 0" }}>
                <BadgeImage url={item.badge_url} locked={!item.unlocked} />
                <div style={{ minWidth: 0, opacity: item.unlocked ? 1 : 0.75 }}>
                  <div style={{ fontSize: 13, fontWeight: "bold" }}>{item.title}</div>
                  <div style={{ fontSize: 12, opacity: 0.8 }}>{item.description}</div>
                  <div style={{ fontSize: 11, opacity: 0.6, marginTop: 2 }}>
                    {item.points} pts{item.true_ratio ? ` (${item.true_ratio} RP)` : ""}
                    {item.percent !== null ? `, ${item.percent}% of players` : ""}
                    {item.unlocked
                      ? `, unlocked ${formatRaDate(item.earned)}${item.hardcore ? " (hardcore)" : ""}`
                      : ""}
                  </div>
                </div>
              </Focusable>
            </PanelSectionRow>
          ))}
          {list.length === 0 && (
            <PanelSectionRow>
              <div style={{ fontSize: 13 }}>Nothing here.</div>
            </PanelSectionRow>
          )}
          {list.length > shown && (
            <PanelSectionRow>
              <ButtonItem layout="below" onClick={() => setShown(shown + GAME_PAGE_SIZE)}>
                Show more ({list.length - shown} left)
              </ButtonItem>
            </PanelSectionRow>
          )}
        </PanelSection>
      )}
    </>
  );
}

function RecentView() {
  const [result, setResult] = useState<RaRecentResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      setResult(await withTimeout(call<[], RaRecentResult>("get_ra_recent"), 30000));
    } catch (error) {
      setLoadError(toErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <PanelSection title="Recent unlocks">
      {loading && (
        <PanelSectionRow>
          <div style={{ fontSize: 13 }}>Loading...</div>
        </PanelSectionRow>
      )}
      {(loadError || (result && !result.ok)) && (
        <PanelSectionRow>
          <div style={{ fontSize: 13, color: "#ff8a80" }}>{loadError ?? result?.error}</div>
        </PanelSectionRow>
      )}
      {result?.ok && result.items.length === 0 && (
        <PanelSectionRow>
          <div style={{ fontSize: 13 }}>No unlocks in the last 7 days.</div>
        </PanelSectionRow>
      )}
      {result?.items.map((item, index) => (
        <PanelSectionRow key={`${item.id}-${index}`}>
          <Focusable style={{ display: "flex", gap: 10, width: "100%", padding: "4px 0" }}>
            <BadgeImage url={item.badge_url} />
            <div style={{ minWidth: 0 }}>
              <div style={{ fontSize: 13, fontWeight: "bold" }}>{item.title}</div>
              <div style={{ fontSize: 12, opacity: 0.8 }}>{item.game_title}</div>
              <div style={{ fontSize: 11, opacity: 0.6, marginTop: 2 }}>
                {item.points} pts{item.true_ratio ? ` (${item.true_ratio} RP)` : ""}{item.hardcore ? ", hardcore" : ""}, {formatRaDate(item.date)}
              </div>
            </div>
          </Focusable>
        </PanelSectionRow>
      ))}
      <PanelSectionRow>
        <ButtonItem layout="below" disabled={loading} onClick={() => void load()}>
          Refresh
        </ButtonItem>
      </PanelSectionRow>
    </PanelSection>
  );
}

function StatusPanel() {
  const [status, setStatus] = useState<BackendStatus | null>(null);
  const [settings, setSettings] = useState<FinallySettings>(DEFAULT_SETTINGS);
  const [sounds, setSounds] = useState<SoundEntry[]>([]);
  const [soundFolder, setSoundFolder] = useState<string>("");
  const [statusError, setStatusError] = useState<string | null>(null);
  const [lastEvent, setLastEvent] = useState<NotificationPayload | null>(null);
  const [pendingAction, setPendingAction] = useState<string | null>(null);
  const [view, setView] = useState<PanelView>("retro");
  const [overlayCheck, setOverlayCheck] = useState<OverlayCheckResult | null>(null);
  const refreshStatus = useCallback(async () => {
    try {
      const next = await call<[], BackendStatus>("get_status");
      setStatus(next);
      setSettings(next.settings ?? DEFAULT_SETTINGS);
      setStatusError(null);
    } catch (error) {
      setStatusError(toErrorMessage(error));
    }
  }, []);

  const refreshSettings = useCallback(async () => {
    try {
      const [nextSettings, nextSounds] = await Promise.all([
        call<[], FinallySettings>("get_settings"),
        call<[], SoundsResponse>("get_sounds"),
      ]);
      setSettings(nextSettings);
      setSounds(nextSounds.sounds);
      setSoundFolder(nextSounds.folder);
      window.dispatchEvent(new CustomEvent(SETTINGS_EVENT, { detail: nextSettings }));
    } catch (error) {
      setStatusError(toErrorMessage(error));
    }
  }, []);

  useEffect(() => {
    const listener = addEventListener<[NotificationPayload]>(
      EVENT_NAME,
      (payload) => {
        if (payload) {
          setLastEvent(payload);
        }
      },
    );

    void refreshStatus();
    void refreshSettings();
    const interval = window.setInterval(() => {
      void refreshStatus();
    }, 5000);

    return () => {
      window.clearInterval(interval);
      removeEventListener(EVENT_NAME, listener);
    };
  }, [refreshSettings, refreshStatus]);

  const handleOverlayCheck = useCallback(async () => {
    setPendingAction("overlay_check");
    try {
      setOverlayCheck(await call<[], OverlayCheckResult>("run_overlay_check"));
    } catch (error) {
      setOverlayCheck({
        ok: false,
        verdict: `The check itself failed: ${toErrorMessage(error)}`,
        checks: [],
        last_status: "",
        last_error: null,
      });
    } finally {
      setPendingAction(null);
    }
  }, []);

  const updateSettings = useCallback(
    async (patch: Partial<FinallySettings>) => {
      setPendingAction("settings");
      try {
        const next = await call<[Partial<FinallySettings>], FinallySettings>(
          "set_settings",
          patch,
        );
        setSettings(next);
        window.dispatchEvent(new CustomEvent(SETTINGS_EVENT, { detail: next }));
        await refreshStatus();
      } finally {
        setPendingAction(null);
      }
    },
    [refreshStatus],
  );

  const openColorPicker = useCallback(
    (key: ColorSettingKey, title: string) => {
      const color = parseHsla(settings[key]);
      let modal: { Close: () => void } | undefined;
      modal = showModal(
        <ColorPickerModal
          closeModal={() => modal?.Close()}
          title={title}
          defaultH={color.h}
          defaultS={color.s}
          defaultL={color.l}
          defaultA={color.a}
          onConfirm={(nextColor) => {
            void updateSettings({ [key]: nextColor } as Partial<FinallySettings>);
          }}
        />,
      );
    },
    [settings, updateSettings],
  );

  const colorsLocked = settings.template_colors_enabled;
  const colorButton = (key: ColorSettingKey, label: string) => (
    <ButtonItem
      disabled={pendingAction !== null || colorsLocked}
      onClick={() => openColorPicker(key, label)}
      layout="below"
      description={settings[key]}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
        <span>{label}</span>
        <span
          style={{
            width: "42px",
            height: "18px",
            borderRadius: "999px",
            background: settings[key],
            border: "1px solid rgba(255,255,255,0.5)",
            display: "inline-block",
          }}
        />
      </div>
    </ButtonItem>
  );

  const soundOptions = sounds.map((sound) => ({
    data: sound.name,
    label: sound.source === "user" ? `${sound.name} (yours)` : sound.name,
  }));

  const trigger = useCallback(
    async (
      method:
        | "test_popup_common"
        | "test_popup_uncommon"
        | "test_popup_rare"
        | "test_popup_ultra_rare"
        | "test_completion_popup",
    ) => {
      setPendingAction(method);
      try {
        await call<[], void>(method);
        await refreshStatus();
      } finally {
        setPendingAction(null);
      }
    },
    [refreshStatus],
  );

  return (
    <>
      <PanelSection title="RetroAchievements Toasts">
        <PanelSectionRow>
          <DropdownItem
            label="Show"
            rgOptions={VIEW_OPTIONS}
            selectedOption={view}
            onChange={(selection: ViewDropdownSelection) => setView(selection.data)}
          />
        </PanelSectionRow>
      </PanelSection>

      {view === "retro" && <RetroView onTest={() => void trigger("test_popup_uncommon")} />}
      {view === "game" && <GameView />}
      {view === "recent" && <RecentView />}

      {view === "popup" && (
        <>
      <PanelSection title="Appearance">
        <PanelSectionRow>
          <DropdownItem
            label="Popup template"
            description="The overall card design/style."
            rgOptions={OVERLAY_TEMPLATE_OPTIONS}
            selectedOption={settings.overlay_template}
            disabled={pendingAction !== null}
            onChange={(selection: { data: OverlayTemplate }) =>
              void updateSettings({ overlay_template: selection.data })
            }
          />
        </PanelSectionRow>
        <PanelSectionRow>
          <DropdownItem
            label="Popup position"
            description="Where the banner appears on screen."
            rgOptions={OVERLAY_POSITION_OPTIONS}
            selectedOption={settings.overlay_position}
            disabled={pendingAction !== null}
            onChange={(selection: { data: OverlayPosition }) =>
              void updateSettings({ overlay_position: selection.data })
            }
          />
        </PanelSectionRow>
        <PanelSectionRow>
          <SliderField
            label="Popup size"
            description="0% hides the banner; 50% is the default size."
            value={settings.overlay_size_percent}
            min={0}
            max={100}
            step={5}
            notchCount={21}
            showValue
            valueSuffix="%"
            disabled={pendingAction !== null}
            onChange={(value) =>
              void updateSettings({ overlay_size_percent: value })
            }
          />
        </PanelSectionRow>
        <PanelSectionRow>
          <SliderField
            label="Popup duration"
            description="How long the toast stays on screen before it slides away."
            value={settings.duration_seconds}
            min={DURATION_RANGE.min}
            max={DURATION_RANGE.max}
            step={DURATION_RANGE.step}
            notchCount={DURATION_RANGE.max - DURATION_RANGE.min + 1}
            showValue
            valueSuffix="s"
            disabled={pendingAction !== null}
            onChange={(value) =>
              void updateSettings({ duration_seconds: value })
            }
          />
        </PanelSectionRow>
        <PanelSectionRow>
          <ToggleField
            label="Show unlock percentage"
            description="Shows what percentage of players have the achievement, e.g. 4.7% of players."
            checked={settings.show_percent}
            disabled={pendingAction !== null}
            onChange={(value) => void updateSettings({ show_percent: value })}
          />
        </PanelSectionRow>
        <PanelSectionRow>
          <DropdownItem
            label="Percentage badge position"
            description="Top right gives the description the full width, so short descriptions don't end in ... and long ones can use two lines."
            rgOptions={PERCENT_POSITION_OPTIONS}
            selectedOption={settings.percent_position}
            disabled={pendingAction !== null}
            onChange={(selection: { data: PercentPosition }) =>
              void updateSettings({ percent_position: selection.data })
            }
          />
        </PanelSectionRow>
        {settings.show_percent && (
          <PanelSectionRow>
            <SliderField
              label="Unlock percentage size"
              description="Size of the small '4.7% of players' badge. 100% is the default."
              value={settings.percent_size}
              min={PERCENT_SIZE_RANGE.min}
              max={PERCENT_SIZE_RANGE.max}
              step={PERCENT_SIZE_RANGE.step}
              notchCount={(PERCENT_SIZE_RANGE.max - PERCENT_SIZE_RANGE.min) / PERCENT_SIZE_RANGE.step + 1}
              showValue
              valueSuffix="%"
              disabled={pendingAction !== null}
              onChange={(value) => void updateSettings({ percent_size: value })}
            />
          </PanelSectionRow>
        )}
        <PanelSectionRow>
          <ToggleField
            label="Template effects"
            description="Extra touches on some templates: typing text, animated backgrounds, glitches, screws, a game-name header and more. Turn off for the plain look."
            checked={settings.template_fx_enabled}
            disabled={pendingAction !== null}
            onChange={(value) => void updateSettings({ template_fx_enabled: value })}
          />
        </PanelSectionRow>
        <PanelSectionRow>
          <ToggleField
            label="Completion popup at 100%"
            description="When you unlock the very last achievement in any game, shows a special emerald completion popup after that achievement's own popup."
            checked={settings.completion_toast_enabled}
            disabled={pendingAction !== null}
            onChange={(value) => void updateSettings({ completion_toast_enabled: value })}
          />
        </PanelSectionRow>
        {settings.completion_toast_enabled && (
          <PanelSectionRow>
            <DropdownItem
              label="Completion popup name"
              description="The big text on the 100% completion popup."
              rgOptions={COMPLETION_TITLE_OPTIONS}
              selectedOption={settings.completion_title}
              disabled={pendingAction !== null}
              onChange={(selection: { data: CompletionTitle }) =>
                void updateSettings({ completion_title: selection.data })
              }
            />
          </PanelSectionRow>
        )}
        <PanelSectionRow>
          <DropdownItem
            label="Placeholder icon"
            description="Shown when an achievement has no icon yet (and as the starting icon on Xbox 360 v2)."
            rgOptions={PLACEHOLDER_ICON_OPTIONS}
            selectedOption={settings.placeholder_icon}
            disabled={pendingAction !== null}
            onChange={(selection: { data: PlaceholderIcon }) =>
              void updateSettings({ placeholder_icon: selection.data })
            }
          />
        </PanelSectionRow>
      </PanelSection>
      <PanelSection title="Rarity Tiers">
        <PanelSectionRow>
          <ToggleField
            label="Rarity tiers"
            description="Names each unlock by how few players have it (Uncommon, Rare, Ultra rare) in the popup label. Ultra rare also gets extra sparkles and a longer shine. Rare keeps the gold look and sound."
            checked={settings.rarity_tiers_enabled}
            disabled={pendingAction !== null}
            onChange={(value) => void updateSettings({ rarity_tiers_enabled: value })}
          />
        </PanelSectionRow>
        {settings.rarity_tiers_enabled && (
          <>
            <PanelSectionRow>
              <SliderField
                label="Ultra rare: this % or lower"
                value={settings.tier_ultra_cutoff}
                min={TIER_CUTOFF_RANGES.ultra.min}
                max={TIER_CUTOFF_RANGES.ultra.max}
                step={TIER_CUTOFF_RANGES.ultra.step}
                showValue
                valueSuffix="%"
                disabled={pendingAction !== null}
                onChange={(value) => void updateSettings({ tier_ultra_cutoff: value })}
              />
            </PanelSectionRow>
            <PanelSectionRow>
              <SliderField
                label="Rare: this % or lower"
                value={settings.tier_rare_cutoff}
                min={TIER_CUTOFF_RANGES.rare.min}
                max={TIER_CUTOFF_RANGES.rare.max}
                step={TIER_CUTOFF_RANGES.rare.step}
                showValue
                valueSuffix="%"
                disabled={pendingAction !== null}
                onChange={(value) => void updateSettings({ tier_rare_cutoff: value })}
              />
            </PanelSectionRow>
            <PanelSectionRow>
              <SliderField
                label="Uncommon: this % or lower"
                value={settings.tier_uncommon_cutoff}
                min={TIER_CUTOFF_RANGES.uncommon.min}
                max={TIER_CUTOFF_RANGES.uncommon.max}
                step={TIER_CUTOFF_RANGES.uncommon.step}
                showValue
                valueSuffix="%"
                disabled={pendingAction !== null}
                onChange={(value) => void updateSettings({ tier_uncommon_cutoff: value })}
              />
            </PanelSectionRow>
            <PanelSectionRow>
              <div style={{ fontSize: "12px", opacity: 0.8 }}>
                {`Ultra rare ≤ ${settings.tier_ultra_cutoff}%, Rare ≤ ${settings.tier_rare_cutoff}%, Uncommon ≤ ${settings.tier_uncommon_cutoff}%, anything higher is common (no tier label). The cutoffs stay in order automatically.`}
              </div>
            </PanelSectionRow>
          </>
        )}
      </PanelSection>
        </>
      )}

      {view === "style" && (
        <>
      <PanelSection title="Colors">
        <PanelSectionRow>
          <ToggleField
            label="Use each template's own colors"
            description="The simple way: every template uses its own built-in palette (for example Xbox green, PlayStation blue, Steam blue). While this is on, all the color options below are greyed out and ignored."
            checked={settings.template_colors_enabled}
            disabled={pendingAction !== null}
            onChange={(value) => void updateSettings({ template_colors_enabled: value })}
          />
        </PanelSectionRow>
        <PanelSectionRow>
          <ToggleField
            label="Gradient from icon colors"
            description="Pull the card's background gradient from the achievement icon's own colors instead of the fixed colors below. Works on every template except Paper Light. Falls back to the fixed colors if the icon has no clear dominant colors (or no icon is available)."
            checked={settings.icon_gradient_enabled}
            disabled={pendingAction !== null || colorsLocked}
            onChange={(value) =>
              void updateSettings(
                value
                  ? { icon_gradient_enabled: true, game_art_gradient_enabled: false }
                  : { icon_gradient_enabled: false },
              )
            }
          />
        </PanelSectionRow>
        <PanelSectionRow>
          <ToggleField
            label="Gradient from game artwork colors"
            description="Pull the gradient from the game's own artwork instead, so every toast in a game shares one palette. Turning this on turns off the icon option above (they're one or the other). Falls back to the icon's colors if the artwork can't be read."
            checked={settings.game_art_gradient_enabled}
            disabled={pendingAction !== null || colorsLocked}
            onChange={(value) =>
              void updateSettings(
                value
                  ? { game_art_gradient_enabled: true, icon_gradient_enabled: false }
                  : { game_art_gradient_enabled: false },
              )
            }
          />
        </PanelSectionRow>
        <PanelSectionRow>
          <DropdownItem
            label="Gradient direction"
            description="Direction of the card's background gradient, or a flat solid color."
            rgOptions={GRADIENT_DIRECTION_OPTIONS}
            selectedOption={settings.gradient_direction}
            disabled={pendingAction !== null || colorsLocked}
            onChange={(selection: { data: GradientDirection }) =>
              void updateSettings({ gradient_direction: selection.data })
            }
          />
        </PanelSectionRow>
        <PanelSectionRow>
          <div
            style={{
              height: "18px",
              borderRadius: "999px",
              background: `linear-gradient(90deg, ${settings.normal_gradient_start}, ${settings.normal_gradient_end})`,
              border: "1px solid rgba(255,255,255,0.35)",
              opacity: colorsLocked ? 0.35 : 1,
            }}
          />
        </PanelSectionRow>
        <PanelSectionRow>
          {colorButton("normal_gradient_start", "Normal gradient start")}
        </PanelSectionRow>
        <PanelSectionRow>
          {colorButton("normal_gradient_end", "Normal gradient end")}
        </PanelSectionRow>
        <PanelSectionRow>
          <div
            style={{
              height: "18px",
              borderRadius: "999px",
              background: `linear-gradient(90deg, ${settings.rare_gradient_start}, ${settings.rare_gradient_end})`,
              border: "1px solid rgba(255,255,255,0.35)",
              opacity: colorsLocked ? 0.35 : 1,
            }}
          />
        </PanelSectionRow>
        <PanelSectionRow>
          {colorButton("rare_gradient_start", "Rare gradient start")}
        </PanelSectionRow>
        <PanelSectionRow>
          {colorButton("rare_gradient_end", "Rare gradient end")}
        </PanelSectionRow>
        <PanelSectionRow>
          {colorButton("normal_circle_color", "Normal circle color")}
        </PanelSectionRow>
        <PanelSectionRow>
          {colorButton("rare_circle_color", "Rare circle color")}
        </PanelSectionRow>
      </PanelSection>
      <PanelSection title="Glow">
        <PanelSectionRow>
          <ToggleField
            label="Icon glow"
            description="The soft glow around the icon, and the pulsing glow ring (rare achievements, or normal ones too if enabled below)."
            checked={settings.icon_glow_enabled}
            disabled={pendingAction !== null}
            onChange={(value) => void updateSettings({ icon_glow_enabled: value })}
          />
        </PanelSectionRow>
        {settings.icon_glow_enabled && (
          <>
            <PanelSectionRow>
              <SliderField
                label="Glow intensity"
                description="50 is the default look; 0 is basically off, 100 doubles it."
                value={settings.icon_glow_intensity}
                min={GLOW_INTENSITY_RANGE.min}
                max={GLOW_INTENSITY_RANGE.max}
                step={GLOW_INTENSITY_RANGE.step}
                notchCount={11}
                showValue
                disabled={pendingAction !== null}
                onChange={(value) =>
                  void updateSettings({ icon_glow_intensity: value })
                }
              />
            </PanelSectionRow>
            <PanelSectionRow>
              <SliderField
                label="Ring size"
                description="How far the glow rings spread. 50 is the default look; 0 hides them, 100 doubles it."
                value={settings.ring_size}
                min={RING_SIZE_RANGE.min}
                max={RING_SIZE_RANGE.max}
                step={RING_SIZE_RANGE.step}
                notchCount={11}
                showValue
                disabled={pendingAction !== null}
                onChange={(value) => void updateSettings({ ring_size: value })}
              />
            </PanelSectionRow>
            <PanelSectionRow>
              <ToggleField
                label="Glow for normal achievements"
                description="The pulsing glow ring normally only plays for rare unlocks -- turn this on to also play it for regular ones. (The rare corner ribbon and sparkles stay rare-only, since those specifically mean 'this one's rare'.)"
                checked={settings.glow_normal_enabled}
                disabled={pendingAction !== null}
                onChange={(value) => void updateSettings({ glow_normal_enabled: value })}
              />
            </PanelSectionRow>
          </>
        )}
        <PanelSectionRow>
          <ToggleField
            label="Icon frame ring"
            description="The colored ring framing the icon, separate from the glow above. With it off, the icon just sits on a plain dark backing."
            checked={settings.icon_frame_ring_enabled}
            disabled={pendingAction !== null}
            onChange={(value) => void updateSettings({ icon_frame_ring_enabled: value })}
          />
        </PanelSectionRow>
      </PanelSection>
      <PanelSection title="Text">
        <PanelSectionRow>
          <SliderField
            label="Title font size"
            description="Font size of the achievement name."
            value={settings.title_font_size}
            min={FONT_SIZE_RANGES.title_font_size.min}
            max={FONT_SIZE_RANGES.title_font_size.max}
            step={1}
            showValue
            disabled={pendingAction !== null}
            onChange={(value) => void updateSettings({ title_font_size: value })}
          />
        </PanelSectionRow>
        <PanelSectionRow>
          <SliderField
            label="Description font size"
            description="Font size of the subtitle/description line."
            value={settings.subtitle_font_size}
            min={FONT_SIZE_RANGES.subtitle_font_size.min}
            max={FONT_SIZE_RANGES.subtitle_font_size.max}
            step={1}
            showValue
            disabled={pendingAction !== null}
            onChange={(value) =>
              void updateSettings({ subtitle_font_size: value })
            }
          />
        </PanelSectionRow>
        <PanelSectionRow>
          <SliderField
            label="Label font size"
            description="Font size of the small eyebrow label above the title."
            value={settings.label_font_size}
            min={FONT_SIZE_RANGES.label_font_size.min}
            max={FONT_SIZE_RANGES.label_font_size.max}
            step={1}
            showValue
            disabled={pendingAction !== null}
            onChange={(value) => void updateSettings({ label_font_size: value })}
          />
        </PanelSectionRow>
      </PanelSection>
        </>
      )}

      {view === "sound" && (
        <>
      <PanelSection title="Sound">
        <PanelSectionRow>
          <SliderField
            label="Volume"
            description="50% is the default volume; 0% is silent."
            value={settings.volume_percent}
            min={0}
            max={100}
            step={10}
            notchCount={11}
            showValue
            valueSuffix="%"
            disabled={pendingAction !== null}
            onChange={(value) => void updateSettings({ volume_percent: value })}
          />
        </PanelSectionRow>
        {SOUND_SLOT_OPTIONS.map(({ slot, label, description }) => {
          const key = `sound_${slot}` as `sound_${SoundSlot}`;
          return (
            <PanelSectionRow key={slot}>
              <DropdownItem
                label={label}
                description={description}
                rgOptions={soundOptions}
                selectedOption={settings[key]}
                disabled={pendingAction !== null || soundOptions.length === 0}
                onChange={(selection: DropdownSelection) =>
                  void updateSettings({ [key]: selection.data } as Partial<FinallySettings>)
                }
              />
            </PanelSectionRow>
          );
        })}
        <PanelSectionRow>
          <div style={{ fontSize: "12px", opacity: 0.8 }}>
            Your own sounds: put .wav, .flac, .ogg or .mp3 files (10 MB or less, kept short) in{" "}
            <b>{soundFolder || "the Finally Achievement Plugin settings folder, sounds"}</b>, then press Refresh. They show up with "(yours)"
            after their name, and updating the plugin never deletes them. Use the test buttons below to hear each
            one.
          </div>
        </PanelSectionRow>
        <PanelSectionRow>
          <ButtonItem
            layout="below"
            disabled={pendingAction !== null}
            onClick={() => void refreshSettings()}
          >
            Refresh sound list
          </ButtonItem>
        </PanelSectionRow>
      </PanelSection>
      <PanelSection title="Popup Tests">
        <PanelSectionRow>
          <ToggleField
            label="Use my recent unlocks for tests"
            description="Tests show one of your recent RetroAchievements unlocks with its real badge. Tests never count as unlocks. With no login saved, tests use a sample."
            checked={settings.test_with_game_data}
            disabled={pendingAction !== null}
            onChange={(value) => void updateSettings({ test_with_game_data: value })}
          />
        </PanelSectionRow>
        <PanelSectionRow>
          <ButtonItem
            disabled={pendingAction !== null}
            onClick={() => void trigger("test_popup_common")}
            layout="below"
            description="A common unlock (above the Uncommon cutoff): no tier label."
          >
            Test Common
          </ButtonItem>
        </PanelSectionRow>
        <PanelSectionRow>
          <ButtonItem
            disabled={pendingAction !== null}
            onClick={() => void trigger("test_popup_uncommon")}
            layout="below"
            description="An uncommon unlock: tier label only."
          >
            Test Uncommon
          </ButtonItem>
        </PanelSectionRow>
        <PanelSectionRow>
          <ButtonItem
            disabled={pendingAction !== null}
            onClick={() => void trigger("test_popup_rare")}
            layout="below"
            description="A rare unlock: gold look, rare sound and glow."
          >
            Test Rare
          </ButtonItem>
        </PanelSectionRow>
        <PanelSectionRow>
          <ButtonItem
            disabled={pendingAction !== null}
            onClick={() => void trigger("test_popup_ultra_rare")}
            layout="below"
            description="An ultra rare unlock: extra sparkles and a longer shine."
          >
            Test Ultra Rare
          </ButtonItem>
        </PanelSectionRow>
        <PanelSectionRow>
          <ButtonItem
            disabled={pendingAction !== null}
            onClick={() => void trigger("test_completion_popup")}
            layout="below"
            description="The special popup for unlocking every achievement in a game, using the running game's name."
          >
            Test Completionist
          </ButtonItem>
        </PanelSectionRow>
      </PanelSection>
        </>
      )}

      {view === "advanced" && (
        <>
      <PanelSection title="Popup Not Showing?">
        <PanelSectionRow>
          <div style={{ fontSize: "12px", opacity: 0.8 }}>
            If you hear the sound but no popup appears (for example on a different handheld), run this check. It tests
            the Python packages, graphics libraries, display and window creation the popup needs, and tells you what's
            missing.
          </div>
        </PanelSectionRow>
        <PanelSectionRow>
          <ButtonItem
            layout="below"
            disabled={pendingAction !== null}
            onClick={() => void handleOverlayCheck()}
          >
            {pendingAction === "overlay_check" ? "Checking..." : "Run overlay check"}
          </ButtonItem>
        </PanelSectionRow>
        {overlayCheck && (
          <>
            <PanelSectionRow>
              <div style={{ fontSize: "13px", fontWeight: 600, color: overlayCheck.ok ? "#5cc35c" : "#ff8a5c" }}>
                {overlayCheck.verdict}
              </div>
            </PanelSectionRow>
            {overlayCheck.checks.map((check, index) => (
              <PanelSectionRow key={`${check.name}-${index}`}>
                <div style={{ fontSize: "12px", display: "flex", gap: 6 }}>
                  <span style={{ color: check.ok ? "#5cc35c" : check.fatal === false ? "#d8c25c" : "#ff8a5c", flexShrink: 0 }}>
                    {check.ok ? "\u2713" : check.fatal === false ? "!" : "\u2717"}
                  </span>
                  <span style={{ opacity: 0.9 }}>
                    <b>{check.name}</b>
                    {check.detail ? ` \u2014 ${check.detail}` : ""}
                  </span>
                </div>
              </PanelSectionRow>
            ))}
            {(overlayCheck.last_status || overlayCheck.last_error) && (
              <PanelSectionRow>
                <div style={{ fontSize: "12px", opacity: 0.8 }}>
                  Last popup: {overlayCheck.last_status || "none yet"}
                  {overlayCheck.last_error ? ` \u2014 ${overlayCheck.last_error}` : ""}
                </div>
              </PanelSectionRow>
            )}
          </>
        )}
      </PanelSection>

      <PanelSection title="Status">
        <PanelSectionRow>
          <ButtonItem
            disabled={pendingAction !== null}
            onClick={() => void refreshStatus()}
            description="Manually refresh backend status."
          >
            Refresh Status
          </ButtonItem>
        </PanelSectionRow>
        <PanelSectionRow>
          <div style={{ fontSize: 13 }}>
            <div>Popup helper: {status?.gamescope_overlay_status ?? "-"}</div>
            {status?.gamescope_overlay_last_error ? (
              <div style={{ color: "#ff8a80" }}>Popup error: {status.gamescope_overlay_last_error}</div>
            ) : null}
            <div>Last toast: {formatTimestamp(status?.last_match_timestamp ?? null)}</div>
            <div>Last source: {status?.last_match_source ?? "-"}</div>
            <div>Last: {status?.last_match_sample ?? "-"}</div>
            <div>
              Last event:{" "}
              {lastEvent ? `${lastEvent.title} @ ${formatTimestamp(lastEvent.timestamp)}` : "none"}
            </div>
            {statusError ? <div style={{ color: "#ff8a80" }}>Status error: {statusError}</div> : null}
          </div>
        </PanelSectionRow>
      </PanelSection>
        </>
      )}
    </>
  );
}

export default definePlugin(() => {
  return {
    name: "RetroAchievements Toasts",
    icon: <FaTrophy />,
    alwaysRender: true,
    titleView: <div className={staticClasses.Title}>RetroAchievements Toasts</div>,
    content: <StatusPanel />,
  };
});
