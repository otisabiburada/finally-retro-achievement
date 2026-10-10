// tools/shims/api.js
var manifest = { name: "RetroAchievements Toasts" };
var conn = window.__DECKY_SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED_deckyLoaderAPIInit;
if (!conn) throw new Error("[@decky/api]: Failed to connect to the loader as the loader API was not initialized.");
var api;
try {
  api = conn.connect(2, manifest.name);
} catch {
  api = conn.connect(1, manifest.name);
}
var callable = api.callable;
var call = api.call || ((name, ...args) => api.callable(name)(...args));
var routerHook = api.routerHook;
var toaster = api.toaster;
var addEventListener = api.addEventListener;
var removeEventListener = api.removeEventListener;
var definePlugin = (fn) => (...args) => fn(...args);

// tools/shims/ui.js
var D = window.DFL;
var ButtonItem = D.ButtonItem;
var DialogButton = D.DialogButton;
var DropdownItem = D.DropdownItem;
var Focusable = D.Focusable;
var PanelSection = D.PanelSection;
var PanelSectionRow = D.PanelSectionRow;
var SliderField = D.SliderField;
var TextField = D.TextField;
var ToggleField = D.ToggleField;
var ColorPickerModal = D.ColorPickerModal;
var showModal = D.showModal;
var staticClasses = D.staticClasses;

// tools/shims/react.js
var R = window.SP_REACT;
var useState = R.useState;
var useEffect = R.useEffect;
var useRef = R.useRef;
var useCallback = R.useCallback;
var useMemo = R.useMemo;
var useLayoutEffect = R.useLayoutEffect;
var useContext = R.useContext;
var createContext = R.createContext;
var Fragment = R.Fragment;
var createElement = R.createElement;
var react_default = R;

// ../../../../../../opt/npm-tools/node_modules/react-icons/lib/iconContext.mjs
var DefaultContext = {
  color: void 0,
  size: void 0,
  className: void 0,
  style: void 0,
  attr: void 0
};
var IconContext = react_default.createContext && /* @__PURE__ */ react_default.createContext(DefaultContext);

// ../../../../../../opt/npm-tools/node_modules/react-icons/lib/iconBase.mjs
var _excluded = ["attr", "size", "title"];
function _objectWithoutProperties(e, t) {
  if (null == e) return {};
  var o, r, i = _objectWithoutPropertiesLoose(e, t);
  if (Object.getOwnPropertySymbols) {
    var n = Object.getOwnPropertySymbols(e);
    for (r = 0; r < n.length; r++) o = n[r], -1 === t.indexOf(o) && {}.propertyIsEnumerable.call(e, o) && (i[o] = e[o]);
  }
  return i;
}
function _objectWithoutPropertiesLoose(r, e) {
  if (null == r) return {};
  var t = {};
  for (var n in r) if ({}.hasOwnProperty.call(r, n)) {
    if (-1 !== e.indexOf(n)) continue;
    t[n] = r[n];
  }
  return t;
}
function _extends() {
  return _extends = Object.assign ? Object.assign.bind() : function(n) {
    for (var e = 1; e < arguments.length; e++) {
      var t = arguments[e];
      for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]);
    }
    return n;
  }, _extends.apply(null, arguments);
}
function ownKeys(e, r) {
  var t = Object.keys(e);
  if (Object.getOwnPropertySymbols) {
    var o = Object.getOwnPropertySymbols(e);
    r && (o = o.filter(function(r2) {
      return Object.getOwnPropertyDescriptor(e, r2).enumerable;
    })), t.push.apply(t, o);
  }
  return t;
}
function _objectSpread(e) {
  for (var r = 1; r < arguments.length; r++) {
    var t = null != arguments[r] ? arguments[r] : {};
    r % 2 ? ownKeys(Object(t), true).forEach(function(r2) {
      _defineProperty(e, r2, t[r2]);
    }) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(t)) : ownKeys(Object(t)).forEach(function(r2) {
      Object.defineProperty(e, r2, Object.getOwnPropertyDescriptor(t, r2));
    });
  }
  return e;
}
function _defineProperty(e, r, t) {
  return (r = _toPropertyKey(r)) in e ? Object.defineProperty(e, r, { value: t, enumerable: true, configurable: true, writable: true }) : e[r] = t, e;
}
function _toPropertyKey(t) {
  var i = _toPrimitive(t, "string");
  return "symbol" == typeof i ? i : i + "";
}
function _toPrimitive(t, r) {
  if ("object" != typeof t || !t) return t;
  var e = t[Symbol.toPrimitive];
  if (void 0 !== e) {
    var i = e.call(t, r || "default");
    if ("object" != typeof i) return i;
    throw new TypeError("@@toPrimitive must return a primitive value.");
  }
  return ("string" === r ? String : Number)(t);
}
function Tree2Element(tree) {
  return tree && tree.map((node, i) => /* @__PURE__ */ react_default.createElement(node.tag, _objectSpread({
    key: i
  }, node.attr), Tree2Element(node.child)));
}
function GenIcon(data) {
  return (props) => /* @__PURE__ */ react_default.createElement(IconBase, _extends({
    attr: _objectSpread({}, data.attr)
  }, props), Tree2Element(data.child));
}
function IconBase(props) {
  var elem = (conf) => {
    var attr = props.attr, size = props.size, title = props.title, svgProps = _objectWithoutProperties(props, _excluded);
    var computedSize = size || conf.size || "1em";
    var className;
    if (conf.className) className = conf.className;
    if (props.className) className = (className ? className + " " : "") + props.className;
    return /* @__PURE__ */ react_default.createElement("svg", _extends({
      stroke: "currentColor",
      fill: "currentColor",
      strokeWidth: "0"
    }, conf.attr, attr, svgProps, {
      className,
      style: _objectSpread(_objectSpread({
        color: props.color || conf.color
      }, conf.style), props.style),
      height: computedSize,
      width: computedSize,
      xmlns: "http://www.w3.org/2000/svg"
    }), title && /* @__PURE__ */ react_default.createElement("title", null, title), props.children);
  };
  return IconContext !== void 0 ? /* @__PURE__ */ react_default.createElement(IconContext.Consumer, null, (conf) => elem(conf)) : elem(DefaultContext);
}

// ../../../../../../opt/npm-tools/node_modules/react-icons/fa/index.mjs
function FaTrophy(props) {
  return GenIcon({ "tag": "svg", "attr": { "viewBox": "0 0 576 512" }, "child": [{ "tag": "path", "attr": { "d": "M552 64H448V24c0-13.3-10.7-24-24-24H152c-13.3 0-24 10.7-24 24v40H24C10.7 64 0 74.7 0 88v56c0 35.7 22.5 72.4 61.9 100.7 31.5 22.7 69.8 37.1 110 41.7C203.3 338.5 240 360 240 360v72h-48c-35.3 0-64 20.7-64 56v12c0 6.6 5.4 12 12 12h296c6.6 0 12-5.4 12-12v-12c0-35.3-28.7-56-64-56h-48v-72s36.7-21.5 68.1-73.6c40.3-4.6 78.6-19 110-41.7 39.3-28.3 61.9-65 61.9-100.7V88c0-13.3-10.7-24-24-24zM99.3 192.8C74.9 175.2 64 155.6 64 144v-16h64.2c1 32.6 5.8 61.2 12.8 86.2-15.1-5.2-29.2-12.4-41.7-21.4zM512 144c0 16.1-17.7 36.1-35.3 48.8-12.5 9-26.7 16.2-41.8 21.4 7-25 11.8-53.6 12.8-86.2H512v16z" }, "child": [] }] })(props);
}

// src/finallyThemes.ts
var EVENT_NAME = "finally_show";
var SETTINGS_EVENT = "finally_settings_changed";
var DEFAULT_NORMAL_SOUND = "unlock_preroll.wav";
var DEFAULT_RARE_SOUND = "rare_preroll.wav";
var FONT_SIZE_RANGES = {
  label_font_size: { min: 9, max: 18, default: 13 },
  title_font_size: { min: 18, max: 34, default: 26 },
  subtitle_font_size: { min: 12, max: 22, default: 18 }
};
var DURATION_RANGE = { min: 3, max: 12, step: 0.5, default: 5.8 };
var GLOW_INTENSITY_RANGE = { min: 0, max: 100, step: 10, default: 50 };
var RING_SIZE_RANGE = { min: 0, max: 100, step: 10, default: 50 };
var GRADIENT_DIRECTION_OPTIONS = [
  { data: "vertical", label: "Vertical (default)" },
  { data: "left_right", label: "Left to right" },
  { data: "right_left", label: "Right to left" },
  { data: "solid", label: "Solid color" }
];
var TIER_CUTOFF_RANGES = {
  ultra: { min: 0.5, max: 5, step: 0.5 },
  rare: { min: 2, max: 25, step: 1 },
  uncommon: { min: 5, max: 60, step: 1 }
};
var SOUND_SLOT_OPTIONS = [
  { slot: "common", label: "Common sound", description: "Everyday unlocks (above the Uncommon cutoff)." },
  { slot: "uncommon", label: "Uncommon sound", description: "Needs Rarity Tiers on; otherwise common sounds play." },
  { slot: "rare", label: "Rare sound", description: "Rare unlocks." },
  { slot: "ultra_rare", label: "Ultra rare sound", description: "Needs Rarity Tiers on; otherwise the rare sound plays." },
  { slot: "completion", label: "Completionist sound", description: "The popup for unlocking every achievement in a game." }
];
var PERCENT_POSITION_OPTIONS = [
  { data: "bottom_right", label: "Bottom right (default)" },
  { data: "top_right", label: "Top right (descriptions can use 2 lines)" }
];
var COMPLETION_TITLE_OPTIONS = [
  { data: "completionist", label: "Completionist" },
  { data: "legendary", label: "Legendary Achievement unlocked" },
  { data: "crowned", label: "Crowned" }
];
var PERCENT_SIZE_RANGE = { min: 70, max: 150, step: 5, default: 100 };
var PLACEHOLDER_ICON_OPTIONS = [
  { data: "auto", label: "Default (game icon, else badge)" },
  { data: "trophy", label: "Trophy" },
  { data: "game_icon", label: "Game icon" }
];
var OVERLAY_POSITION_OPTIONS = [
  { data: "top_left", label: "Top left" },
  { data: "top_center", label: "Top middle" },
  { data: "top_right", label: "Top right" },
  { data: "bottom_left", label: "Bottom left" },
  { data: "bottom_center", label: "Bottom middle" },
  { data: "bottom_right", label: "Bottom right" }
];
var OVERLAY_TEMPLATE_OPTIONS = [
  { data: "xbox_modern", label: "Xbox Modern" },
  { data: "playstation_trophy", label: "Trophy Case" },
  { data: "switch_bold", label: "Handheld Bold" },
  { data: "steam_flat", label: "Steam Flat" },
  { data: "material_minimal", label: "Material Minimal" },
  { data: "retro_arcade", label: "Retro Arcade" },
  { data: "chat_toast", label: "Chat Toast" },
  { data: "cyber_glass", label: "Cyber Glass" },
  { data: "xbox_360_classic", label: "Xbox 360 Classic" },
  { data: "xbox_360_v2", label: "Xbox 360 Classic v2" },
  { data: "xbox_360_v2_square", label: "Xbox 360 Classic v2 (Square)" },
  { data: "win11_glass", label: "Fluent Glass" },
  { data: "discord_bar", label: "Chat Bar" },
  { data: "vaporwave", label: "Vaporwave" },
  { data: "light_card", label: "Paper Light" },
  { data: "wood_plaque", label: "Trophy Plaque" },
  { data: "terminal_hacker", label: "Terminal" },
  { data: "game_art", label: "Game Art Blur" }
];
var DEFAULT_SETTINGS = {
  sound_common: DEFAULT_NORMAL_SOUND,
  sound_uncommon: DEFAULT_NORMAL_SOUND,
  sound_rare: DEFAULT_RARE_SOUND,
  sound_ultra_rare: DEFAULT_RARE_SOUND,
  sound_completion: DEFAULT_RARE_SOUND,
  overlay_size_percent: 50,
  volume_percent: 50,
  overlay_position: "bottom_center",
  overlay_template: "xbox_modern",
  label_font_size: 13,
  title_font_size: 26,
  subtitle_font_size: 18,
  duration_seconds: 5.8,
  icon_glow_enabled: true,
  icon_glow_intensity: 50,
  ring_size: 50,
  gradient_direction: "vertical",
  glow_normal_enabled: false,
  icon_frame_ring_enabled: true,
  icon_gradient_enabled: false,
  show_percent: true,
  placeholder_icon: "auto",
  game_art_gradient_enabled: false,
  completion_toast_enabled: true,
  completion_title: "completionist",
  percent_size: 100,
  percent_position: "bottom_right",
  rarity_tiers_enabled: true,
  test_with_game_data: true,
  template_fx_enabled: true,
  template_colors_enabled: false,
  tier_uncommon_cutoff: 25,
  tier_rare_cutoff: 10,
  tier_ultra_cutoff: 1,
  rarity_enabled: true,
  normal_gradient_start: "hsla(134, 58%, 25%, 0.94)",
  normal_gradient_end: "hsla(134, 50%, 14%, 0.94)",
  rare_gradient_start: "hsla(45, 90%, 42%, 0.95)",
  rare_gradient_end: "hsla(38, 70%, 22%, 0.95)",
  normal_circle_color: "hsla(134, 62%, 51%, 1)",
  rare_circle_color: "hsla(45, 95%, 58%, 1)"
};

// tools/shims/jsx.js
var J = window.SP_JSX;
var jsx = J.jsx;
var jsxs = J.jsxs;
var Fragment2 = J.Fragment;

// src/index.tsx
var parseHsla = (value) => {
  const match = value.match(
    /hsla?\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)%\s*,\s*(\d+(?:\.\d+)?)%\s*(?:,\s*(\d+(?:\.\d+)?)\s*)?\)/i
  );
  if (!match) {
    return { h: 35, s: 98, l: 38, a: 0.94 };
  }
  return {
    h: Number(match[1]),
    s: Number(match[2]),
    l: Number(match[3]),
    a: match[4] ? Number(match[4]) : 1
  };
};
var toErrorMessage = (value) => {
  if (value instanceof Error) {
    return value.message;
  }
  return String(value);
};
var formatTimestamp = (value) => {
  if (!value) {
    return "never";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString();
};
var VIEW_OPTIONS = [
  { data: "retro", label: "Setup" },
  { data: "game", label: "Game achievements" },
  { data: "recent", label: "Recent unlocks" },
  { data: "popup", label: "Popup" },
  { data: "style", label: "Colors & style" },
  { data: "sound", label: "Sound & tests" },
  { data: "advanced", label: "Advanced" }
];
function withTimeout(promise, ms) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(
      () => reject(new Error("The plugin's background part isn't answering.")),
      ms
    );
    promise.then(
      (value) => {
        clearTimeout(timer);
        resolve(value);
      },
      (error) => {
        clearTimeout(timer);
        reject(error);
      }
    );
  });
}
function raStatusText(state) {
  switch (state.status) {
    case "needs_setup":
      return "Add your RetroAchievements username and API key below.";
    case "watching":
      return `Watching ${state.username} for new unlocks (${state.mode === "idle" ? "resting, no emulator open" : state.mode === "burst" ? "checking now" : "checking often"}).`;
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
function RetroView({ onTest }) {
  const [state, setState] = useState(null);
  const [loadError, setLoadError] = useState(null);
  const [username, setUsername] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [busy, setBusy] = useState(null);
  const [message, setMessage] = useState(null);
  const [check, setCheck] = useState(null);
  const [usernameLoaded, setUsernameLoaded] = useState(false);
  const load = useCallback(async () => {
    try {
      const next = await withTimeout(call("get_ra_state"), 8e3);
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
    const timer = window.setInterval(() => void load(), 4e3);
    return () => window.clearInterval(timer);
  }, [load]);
  const save = useCallback(async (patch, label) => {
    setBusy(label);
    setMessage(null);
    try {
      const result = await withTimeout(call("set_ra_config", patch), 1e4);
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
        call("ra_import_login_file"),
        1e4
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
      setCheck(await withTimeout(call("ra_check_connection"), 4e4));
    } catch (error) {
      setCheck({ ok: false, lines: [{ ok: false, text: toErrorMessage(error) }] });
    } finally {
      setBusy(null);
    }
  }, []);
  if (!state) {
    return /* @__PURE__ */ jsx(PanelSection, { title: "RetroAchievements", children: /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx("div", { style: { fontSize: 13 }, children: loadError ? `RetroAchievements Toasts couldn't start: ${loadError} Check ~/homebrew/logs/RetroAchievements Toasts/ and reopen this panel.` : "Loading..." }) }) });
  }
  const range = state.poll_range.length === 3 ? state.poll_range : [10, 3, 60];
  const disabled = busy !== null;
  return /* @__PURE__ */ jsxs(Fragment2, { children: [
    /* @__PURE__ */ jsxs(PanelSection, { title: "RetroAchievements", children: [
      /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx("div", { style: { fontSize: 13, color: state.status === "error" || state.status === "offline" ? "#ff8a80" : void 0 }, children: raStatusText(state) }) }),
      /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
        ToggleField,
        {
          label: "Show RetroAchievements toasts",
          checked: state.enabled,
          disabled,
          onChange: (value) => void save({ enabled: value }, "enabled")
        }
      ) }),
      /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
        TextField,
        {
          label: "RetroAchievements username",
          value: username,
          disabled,
          onChange: (event) => setUsername(event.target.value)
        }
      ) }),
      /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
        TextField,
        {
          label: "Web API key",
          description: state.key_saved ? `Saved (ends ${state.key_hint}). Leave empty to keep it.` : "retroachievements.org > Settings > Keys > Web API Key.",
          bIsPassword: true,
          value: apiKey,
          disabled,
          onChange: (event) => setApiKey(event.target.value)
        }
      ) }),
      /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(ButtonItem, { layout: "below", disabled: disabled || username.trim().length === 0, onClick: () => void handleSaveLogin(), children: busy === "login" ? "Saving..." : "Save login" }) }),
      /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
        ButtonItem,
        {
          layout: "below",
          disabled,
          onClick: () => void handleImport(),
          description: "Easier than typing: put your username on line 1 and your Web API key on line 2 of ~/Downloads/retroachievements.txt. The file is deleted after it is imported.",
          children: busy === "import" ? "Importing..." : "Import login from file"
        }
      ) }),
      /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(ButtonItem, { layout: "below", disabled, onClick: () => void handleCheck(), children: busy === "check" ? "Checking..." : "Check connection" }) }),
      message && /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx("div", { style: { fontSize: 12, opacity: 0.85 }, children: message }) }),
      check && /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx("div", { style: { fontSize: 12 }, children: check.lines.map((line, index) => /* @__PURE__ */ jsxs("div", { style: { marginBottom: 3, color: line.ok ? void 0 : "#ff8a80" }, children: [
        /* @__PURE__ */ jsx("strong", { children: line.ok ? "OK" : "FAIL" }),
        " ",
        line.text
      ] }, index)) }) }),
      /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(ButtonItem, { layout: "below", disabled, onClick: onTest, children: "Test toast (uses one of your recent unlocks)" }) })
    ] }),
    /* @__PURE__ */ jsxs(PanelSection, { title: "Rarity", children: [
      /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(Focusable, { style: { display: "flex", gap: 6, width: "100%" }, children: [["percent", "Players %"], ["weighted", "RetroPoints"]].map(([value, label]) => /* @__PURE__ */ jsx(
        DialogButton,
        {
          disabled,
          onClick: () => void save({ rarity_source: value }, "rarity"),
          style: {
            flex: 1,
            minWidth: 0,
            padding: "8px 4px",
            fontSize: 12.5,
            background: state.rarity_source === value ? "#1a9fff" : void 0,
            color: state.rarity_source === value ? "#fff" : void 0
          },
          children: label
        },
        value
      )) }) }),
      /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx("div", { style: { fontSize: 12, color: "rgba(255,255,255,0.65)" }, children: state.rarity_source === "percent" ? "Tier from the share of players who have the achievement. Cutoffs are in the Popup tab." : "Tier from RetroAchievements' own rarity weighting: RetroPoints divided by points. A common achievement is near 1x, a rare one is many times that. The popup badge also shows the RetroPoints (RP). If an achievement has no RetroPoints, the players % is used." }) }),
      state.rarity_source === "weighted" && [
        ["ratio_uncommon", "Uncommon from", state.ratio_uncommon],
        ["ratio_rare", "Rare from", state.ratio_rare],
        ["ratio_ultra", "Ultra rare from", state.ratio_ultra]
      ].map(([key, label, value]) => /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
        SliderField,
        {
          label,
          value,
          min: state.ratio_range[0],
          max: state.ratio_range[1],
          step: 0.5,
          showValue: true,
          valueSuffix: "x",
          disabled,
          onChange: (next) => void save({ [key]: next }, key)
        }
      ) }, key))
    ] }),
    /* @__PURE__ */ jsxs(PanelSection, { title: "Watching", children: [
      /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
        SliderField,
        {
          label: "Check every",
          description: "Shorter is quicker but asks RetroAchievements more often.",
          value: state.poll_seconds,
          min: range[1],
          max: range[2],
          step: 1,
          showValue: true,
          valueSuffix: " s",
          disabled,
          onChange: (value) => void save({ poll_seconds: value }, "poll")
        }
      ) }),
      /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
        ToggleField,
        {
          label: "Show points on the popup",
          description: "A small badge with the points, for example 25 pts, plus HC for hardcore.",
          checked: state.show_points,
          disabled,
          onChange: (value) => void save({ show_points: value }, "points")
        }
      ) }),
      /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
        ToggleField,
        {
          label: "Hardcore unlocks only",
          description: "Skip softcore unlocks.",
          checked: state.hardcore_only,
          disabled,
          onChange: (value) => void save({ hardcore_only: value }, "hardcore")
        }
      ) }),
      /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
        ToggleField,
        {
          label: "Rest when no emulator is open",
          description: "Checks every 20 to 60 seconds while no emulator is running and nothing was unlocked lately. Saves battery and data. Turn off if popups ever feel slow.",
          checked: state.smart_polling,
          disabled,
          onChange: (value) => void save({ smart_polling: value }, "smart")
        }
      ) }),
      /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx("div", { style: { fontSize: 12, color: "rgba(255,255,255,0.65)" }, children: state.hint_files > 0 ? `Emulator logs: ${state.hint_files} watched, ${state.hints} unlock hint(s) caught. A hint makes the next check happen at once.` : "Emulator logs: none found. That is fine; the plugin then relies on the check interval." }) }),
      /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx("div", { style: { fontSize: 12, color: "rgba(255,255,255,0.65)" }, children: "Your emulator must be logged in to RetroAchievements (RetroArch, DuckStation, PCSX2, PPSSPP and others do this in their own settings). A toast appears a few seconds after the emulator reports the unlock." }) }),
      /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx("div", { style: { fontSize: 12, color: "rgba(255,255,255,0.65)" }, children: state.last_unlock ? `Last toast: ${state.last_unlock.title} (${state.last_unlock.game}${state.last_unlock.hardcore ? ", hardcore" : ""}). ${state.unlock_count} this session.` : "No unlocks seen yet this session." }) })
    ] })
  ] });
}
var GAME_PAGE_SIZE = 15;
function formatRaDate(value) {
  if (!value) return "";
  const parsed = /* @__PURE__ */ new Date(value.replace(" ", "T") + "Z");
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString();
}
function BadgeImage({ url, locked }) {
  const [failed, setFailed] = useState(false);
  const box = { width: 48, height: 48, borderRadius: 6, flex: "0 0 48px", background: "rgba(255,255,255,0.08)" };
  if (!url || failed) return /* @__PURE__ */ jsx("div", { style: box });
  return /* @__PURE__ */ jsx(
    "img",
    {
      src: url,
      width: 48,
      height: 48,
      onError: () => setFailed(true),
      style: { ...box, objectFit: "cover", filter: locked ? "grayscale(1) brightness(0.6)" : "none" }
    }
  );
}
function GameView() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);
  const [filter, setFilter] = useState("all");
  const [shown, setShown] = useState(GAME_PAGE_SIZE);
  const load = useCallback(async (gameId) => {
    setLoading(true);
    setLoadError(null);
    try {
      const next = await withTimeout(call("get_ra_game", gameId), 3e4);
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
  const percent = game && game.total > 0 ? Math.round(game.unlocked / game.total * 100) : 0;
  return /* @__PURE__ */ jsxs(Fragment2, { children: [
    /* @__PURE__ */ jsxs(PanelSection, { title: game ? game.title : "Game achievements", children: [
      loading && /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx("div", { style: { fontSize: 13 }, children: "Loading..." }) }),
      (loadError || result && !result.ok) && /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx("div", { style: { fontSize: 13, color: "#ff8a80" }, children: loadError ?? result?.error }) }),
      game && /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsxs("div", { style: { width: "100%" }, children: [
        /* @__PURE__ */ jsx("div", { style: { fontSize: 12, opacity: 0.7 }, children: game.console }),
        /* @__PURE__ */ jsxs("div", { style: { fontSize: 13, margin: "4px 0" }, children: [
          game.unlocked,
          " of ",
          game.total,
          " unlocked (",
          percent,
          "%)",
          game.hardcore_unlocked > 0 ? `, ${game.hardcore_unlocked} in hardcore` : ""
        ] }),
        /* @__PURE__ */ jsx("div", { style: { height: 6, borderRadius: 3, background: "rgba(255,255,255,0.12)", overflow: "hidden" }, children: /* @__PURE__ */ jsx("div", { style: { width: `${percent}%`, height: "100%", background: "#1a9fff" } }) })
      ] }) }),
      /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(ButtonItem, { layout: "below", disabled: loading, onClick: () => void load(game ? game.game_id : null), children: "Refresh" }) })
    ] }),
    result?.recent && result.recent.length > 1 && /* @__PURE__ */ jsx(PanelSection, { title: "Switch game", children: result.recent.slice(0, 5).map((item) => /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
      ButtonItem,
      {
        layout: "below",
        disabled: loading || game !== void 0 && game.game_id === item.game_id,
        onClick: () => void load(item.game_id),
        description: `${item.console}, ${item.unlocked} of ${item.total}`,
        children: item.title
      }
    ) }, item.game_id)) }),
    game && /* @__PURE__ */ jsxs(PanelSection, { title: "Achievements", children: [
      /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(Focusable, { style: { display: "flex", gap: 6, width: "100%" }, children: ["all", "locked", "unlocked"].map((name) => /* @__PURE__ */ jsx(
        DialogButton,
        {
          onClick: () => {
            setFilter(name);
            setShown(GAME_PAGE_SIZE);
          },
          style: {
            flex: 1,
            minWidth: 0,
            padding: "8px 4px",
            fontSize: 12.5,
            background: filter === name ? "#1a9fff" : void 0,
            color: filter === name ? "#fff" : void 0
          },
          children: name === "all" ? "All" : name === "locked" ? "Locked" : "Unlocked"
        },
        name
      )) }) }),
      list.slice(0, shown).map((item) => /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsxs(Focusable, { style: { display: "flex", gap: 10, width: "100%", padding: "4px 0" }, children: [
        /* @__PURE__ */ jsx(BadgeImage, { url: item.badge_url, locked: !item.unlocked }),
        /* @__PURE__ */ jsxs("div", { style: { minWidth: 0, opacity: item.unlocked ? 1 : 0.75 }, children: [
          /* @__PURE__ */ jsx("div", { style: { fontSize: 13, fontWeight: "bold" }, children: item.title }),
          /* @__PURE__ */ jsx("div", { style: { fontSize: 12, opacity: 0.8 }, children: item.description }),
          /* @__PURE__ */ jsxs("div", { style: { fontSize: 11, opacity: 0.6, marginTop: 2 }, children: [
            item.points,
            " pts",
            item.true_ratio ? ` (${item.true_ratio} RP)` : "",
            item.percent !== null ? `, ${item.percent}% of players` : "",
            item.unlocked ? `, unlocked ${formatRaDate(item.earned)}${item.hardcore ? " (hardcore)" : ""}` : ""
          ] })
        ] })
      ] }) }, item.id)),
      list.length === 0 && /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx("div", { style: { fontSize: 13 }, children: "Nothing here." }) }),
      list.length > shown && /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsxs(ButtonItem, { layout: "below", onClick: () => setShown(shown + GAME_PAGE_SIZE), children: [
        "Show more (",
        list.length - shown,
        " left)"
      ] }) })
    ] })
  ] });
}
function RecentView() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);
  const load = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      setResult(await withTimeout(call("get_ra_recent"), 3e4));
    } catch (error) {
      setLoadError(toErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => {
    void load();
  }, [load]);
  return /* @__PURE__ */ jsxs(PanelSection, { title: "Recent unlocks", children: [
    loading && /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx("div", { style: { fontSize: 13 }, children: "Loading..." }) }),
    (loadError || result && !result.ok) && /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx("div", { style: { fontSize: 13, color: "#ff8a80" }, children: loadError ?? result?.error }) }),
    result?.ok && result.items.length === 0 && /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx("div", { style: { fontSize: 13 }, children: "No unlocks in the last 7 days." }) }),
    result?.items.map((item, index) => /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsxs(Focusable, { style: { display: "flex", gap: 10, width: "100%", padding: "4px 0" }, children: [
      /* @__PURE__ */ jsx(BadgeImage, { url: item.badge_url }),
      /* @__PURE__ */ jsxs("div", { style: { minWidth: 0 }, children: [
        /* @__PURE__ */ jsx("div", { style: { fontSize: 13, fontWeight: "bold" }, children: item.title }),
        /* @__PURE__ */ jsx("div", { style: { fontSize: 12, opacity: 0.8 }, children: item.game_title }),
        /* @__PURE__ */ jsxs("div", { style: { fontSize: 11, opacity: 0.6, marginTop: 2 }, children: [
          item.points,
          " pts",
          item.true_ratio ? ` (${item.true_ratio} RP)` : "",
          item.hardcore ? ", hardcore" : "",
          ", ",
          formatRaDate(item.date)
        ] })
      ] })
    ] }) }, `${item.id}-${index}`)),
    /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(ButtonItem, { layout: "below", disabled: loading, onClick: () => void load(), children: "Refresh" }) })
  ] });
}
function StatusPanel() {
  const [status, setStatus] = useState(null);
  const [settings, setSettings] = useState(DEFAULT_SETTINGS);
  const [sounds, setSounds] = useState([]);
  const [soundFolder, setSoundFolder] = useState("");
  const [statusError, setStatusError] = useState(null);
  const [lastEvent, setLastEvent] = useState(null);
  const [pendingAction, setPendingAction] = useState(null);
  const [view, setView] = useState("retro");
  const [overlayCheck, setOverlayCheck] = useState(null);
  const refreshStatus = useCallback(async () => {
    try {
      const next = await call("get_status");
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
        call("get_settings"),
        call("get_sounds")
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
    const listener = addEventListener(
      EVENT_NAME,
      (payload) => {
        if (payload) {
          setLastEvent(payload);
        }
      }
    );
    void refreshStatus();
    void refreshSettings();
    const interval = window.setInterval(() => {
      void refreshStatus();
    }, 5e3);
    return () => {
      window.clearInterval(interval);
      removeEventListener(EVENT_NAME, listener);
    };
  }, [refreshSettings, refreshStatus]);
  const handleOverlayCheck = useCallback(async () => {
    setPendingAction("overlay_check");
    try {
      setOverlayCheck(await call("run_overlay_check"));
    } catch (error) {
      setOverlayCheck({
        ok: false,
        verdict: `The check itself failed: ${toErrorMessage(error)}`,
        checks: [],
        last_status: "",
        last_error: null
      });
    } finally {
      setPendingAction(null);
    }
  }, []);
  const updateSettings = useCallback(
    async (patch) => {
      setPendingAction("settings");
      try {
        const next = await call(
          "set_settings",
          patch
        );
        setSettings(next);
        window.dispatchEvent(new CustomEvent(SETTINGS_EVENT, { detail: next }));
        await refreshStatus();
      } finally {
        setPendingAction(null);
      }
    },
    [refreshStatus]
  );
  const openColorPicker = useCallback(
    (key, title) => {
      const color = parseHsla(settings[key]);
      let modal;
      modal = showModal(
        /* @__PURE__ */ jsx(
          ColorPickerModal,
          {
            closeModal: () => modal?.Close(),
            title,
            defaultH: color.h,
            defaultS: color.s,
            defaultL: color.l,
            defaultA: color.a,
            onConfirm: (nextColor) => {
              void updateSettings({ [key]: nextColor });
            }
          }
        )
      );
    },
    [settings, updateSettings]
  );
  const colorsLocked = settings.template_colors_enabled;
  const colorButton = (key, label) => /* @__PURE__ */ jsx(
    ButtonItem,
    {
      disabled: pendingAction !== null || colorsLocked,
      onClick: () => openColorPicker(key, label),
      layout: "below",
      description: settings[key],
      children: /* @__PURE__ */ jsxs("div", { style: { display: "flex", alignItems: "center", gap: "10px" }, children: [
        /* @__PURE__ */ jsx("span", { children: label }),
        /* @__PURE__ */ jsx(
          "span",
          {
            style: {
              width: "42px",
              height: "18px",
              borderRadius: "999px",
              background: settings[key],
              border: "1px solid rgba(255,255,255,0.5)",
              display: "inline-block"
            }
          }
        )
      ] })
    }
  );
  const soundOptions = sounds.map((sound) => ({
    data: sound.name,
    label: sound.source === "user" ? `${sound.name} (yours)` : sound.name
  }));
  const trigger = useCallback(
    async (method) => {
      setPendingAction(method);
      try {
        await call(method);
        await refreshStatus();
      } finally {
        setPendingAction(null);
      }
    },
    [refreshStatus]
  );
  return /* @__PURE__ */ jsxs(Fragment2, { children: [
    /* @__PURE__ */ jsx(PanelSection, { title: "RetroAchievements Toasts", children: /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
      DropdownItem,
      {
        label: "Show",
        rgOptions: VIEW_OPTIONS,
        selectedOption: view,
        onChange: (selection) => setView(selection.data)
      }
    ) }) }),
    view === "retro" && /* @__PURE__ */ jsx(RetroView, { onTest: () => void trigger("test_popup_uncommon") }),
    view === "game" && /* @__PURE__ */ jsx(GameView, {}),
    view === "recent" && /* @__PURE__ */ jsx(RecentView, {}),
    view === "popup" && /* @__PURE__ */ jsxs(Fragment2, { children: [
      /* @__PURE__ */ jsxs(PanelSection, { title: "Appearance", children: [
        /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
          DropdownItem,
          {
            label: "Popup template",
            description: "The overall card design/style.",
            rgOptions: OVERLAY_TEMPLATE_OPTIONS,
            selectedOption: settings.overlay_template,
            disabled: pendingAction !== null,
            onChange: (selection) => void updateSettings({ overlay_template: selection.data })
          }
        ) }),
        /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
          DropdownItem,
          {
            label: "Popup position",
            description: "Where the banner appears on screen.",
            rgOptions: OVERLAY_POSITION_OPTIONS,
            selectedOption: settings.overlay_position,
            disabled: pendingAction !== null,
            onChange: (selection) => void updateSettings({ overlay_position: selection.data })
          }
        ) }),
        /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
          SliderField,
          {
            label: "Popup size",
            description: "0% hides the banner; 50% is the default size.",
            value: settings.overlay_size_percent,
            min: 0,
            max: 100,
            step: 5,
            notchCount: 21,
            showValue: true,
            valueSuffix: "%",
            disabled: pendingAction !== null,
            onChange: (value) => void updateSettings({ overlay_size_percent: value })
          }
        ) }),
        /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
          SliderField,
          {
            label: "Popup duration",
            description: "How long the toast stays on screen before it slides away.",
            value: settings.duration_seconds,
            min: DURATION_RANGE.min,
            max: DURATION_RANGE.max,
            step: DURATION_RANGE.step,
            notchCount: DURATION_RANGE.max - DURATION_RANGE.min + 1,
            showValue: true,
            valueSuffix: "s",
            disabled: pendingAction !== null,
            onChange: (value) => void updateSettings({ duration_seconds: value })
          }
        ) }),
        /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
          ToggleField,
          {
            label: "Show unlock percentage",
            description: "Shows what percentage of players have the achievement, e.g. 4.7% of players.",
            checked: settings.show_percent,
            disabled: pendingAction !== null,
            onChange: (value) => void updateSettings({ show_percent: value })
          }
        ) }),
        /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
          DropdownItem,
          {
            label: "Percentage badge position",
            description: "Top right gives the description the full width, so short descriptions don't end in ... and long ones can use two lines.",
            rgOptions: PERCENT_POSITION_OPTIONS,
            selectedOption: settings.percent_position,
            disabled: pendingAction !== null,
            onChange: (selection) => void updateSettings({ percent_position: selection.data })
          }
        ) }),
        settings.show_percent && /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
          SliderField,
          {
            label: "Unlock percentage size",
            description: "Size of the small '4.7% of players' badge. 100% is the default.",
            value: settings.percent_size,
            min: PERCENT_SIZE_RANGE.min,
            max: PERCENT_SIZE_RANGE.max,
            step: PERCENT_SIZE_RANGE.step,
            notchCount: (PERCENT_SIZE_RANGE.max - PERCENT_SIZE_RANGE.min) / PERCENT_SIZE_RANGE.step + 1,
            showValue: true,
            valueSuffix: "%",
            disabled: pendingAction !== null,
            onChange: (value) => void updateSettings({ percent_size: value })
          }
        ) }),
        /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
          ToggleField,
          {
            label: "Template effects",
            description: "Extra touches on some templates: typing text, animated backgrounds, glitches, screws, a game-name header and more. Turn off for the plain look.",
            checked: settings.template_fx_enabled,
            disabled: pendingAction !== null,
            onChange: (value) => void updateSettings({ template_fx_enabled: value })
          }
        ) }),
        /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
          ToggleField,
          {
            label: "Completion popup at 100%",
            description: "When you unlock the very last achievement in any game, shows a special emerald completion popup after that achievement's own popup.",
            checked: settings.completion_toast_enabled,
            disabled: pendingAction !== null,
            onChange: (value) => void updateSettings({ completion_toast_enabled: value })
          }
        ) }),
        settings.completion_toast_enabled && /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
          DropdownItem,
          {
            label: "Completion popup name",
            description: "The big text on the 100% completion popup.",
            rgOptions: COMPLETION_TITLE_OPTIONS,
            selectedOption: settings.completion_title,
            disabled: pendingAction !== null,
            onChange: (selection) => void updateSettings({ completion_title: selection.data })
          }
        ) }),
        /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
          DropdownItem,
          {
            label: "Placeholder icon",
            description: "Shown when an achievement has no icon yet (and as the starting icon on Xbox 360 v2).",
            rgOptions: PLACEHOLDER_ICON_OPTIONS,
            selectedOption: settings.placeholder_icon,
            disabled: pendingAction !== null,
            onChange: (selection) => void updateSettings({ placeholder_icon: selection.data })
          }
        ) })
      ] }),
      /* @__PURE__ */ jsxs(PanelSection, { title: "Rarity Tiers", children: [
        /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
          ToggleField,
          {
            label: "Rarity tiers",
            description: "Names each unlock by how few players have it (Uncommon, Rare, Ultra rare) in the popup label. Ultra rare also gets extra sparkles and a longer shine. Rare keeps the gold look and sound.",
            checked: settings.rarity_tiers_enabled,
            disabled: pendingAction !== null,
            onChange: (value) => void updateSettings({ rarity_tiers_enabled: value })
          }
        ) }),
        settings.rarity_tiers_enabled && /* @__PURE__ */ jsxs(Fragment2, { children: [
          /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
            SliderField,
            {
              label: "Ultra rare: this % or lower",
              value: settings.tier_ultra_cutoff,
              min: TIER_CUTOFF_RANGES.ultra.min,
              max: TIER_CUTOFF_RANGES.ultra.max,
              step: TIER_CUTOFF_RANGES.ultra.step,
              showValue: true,
              valueSuffix: "%",
              disabled: pendingAction !== null,
              onChange: (value) => void updateSettings({ tier_ultra_cutoff: value })
            }
          ) }),
          /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
            SliderField,
            {
              label: "Rare: this % or lower",
              value: settings.tier_rare_cutoff,
              min: TIER_CUTOFF_RANGES.rare.min,
              max: TIER_CUTOFF_RANGES.rare.max,
              step: TIER_CUTOFF_RANGES.rare.step,
              showValue: true,
              valueSuffix: "%",
              disabled: pendingAction !== null,
              onChange: (value) => void updateSettings({ tier_rare_cutoff: value })
            }
          ) }),
          /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
            SliderField,
            {
              label: "Uncommon: this % or lower",
              value: settings.tier_uncommon_cutoff,
              min: TIER_CUTOFF_RANGES.uncommon.min,
              max: TIER_CUTOFF_RANGES.uncommon.max,
              step: TIER_CUTOFF_RANGES.uncommon.step,
              showValue: true,
              valueSuffix: "%",
              disabled: pendingAction !== null,
              onChange: (value) => void updateSettings({ tier_uncommon_cutoff: value })
            }
          ) }),
          /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx("div", { style: { fontSize: "12px", opacity: 0.8 }, children: `Ultra rare ≤ ${settings.tier_ultra_cutoff}%, Rare ≤ ${settings.tier_rare_cutoff}%, Uncommon ≤ ${settings.tier_uncommon_cutoff}%, anything higher is common (no tier label). The cutoffs stay in order automatically.` }) })
        ] })
      ] })
    ] }),
    view === "style" && /* @__PURE__ */ jsxs(Fragment2, { children: [
      /* @__PURE__ */ jsxs(PanelSection, { title: "Colors", children: [
        /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
          ToggleField,
          {
            label: "Use each template's own colors",
            description: "The simple way: every template uses its own built-in palette (for example Xbox green, PlayStation blue, Steam blue). While this is on, all the color options below are greyed out and ignored.",
            checked: settings.template_colors_enabled,
            disabled: pendingAction !== null,
            onChange: (value) => void updateSettings({ template_colors_enabled: value })
          }
        ) }),
        /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
          ToggleField,
          {
            label: "Gradient from icon colors",
            description: "Pull the card's background gradient from the achievement icon's own colors instead of the fixed colors below. Works on every template except Paper Light. Falls back to the fixed colors if the icon has no clear dominant colors (or no icon is available).",
            checked: settings.icon_gradient_enabled,
            disabled: pendingAction !== null || colorsLocked,
            onChange: (value) => void updateSettings(
              value ? { icon_gradient_enabled: true, game_art_gradient_enabled: false } : { icon_gradient_enabled: false }
            )
          }
        ) }),
        /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
          ToggleField,
          {
            label: "Gradient from game artwork colors",
            description: "Pull the gradient from the game's own artwork instead, so every toast in a game shares one palette. Turning this on turns off the icon option above (they're one or the other). Falls back to the icon's colors if the artwork can't be read.",
            checked: settings.game_art_gradient_enabled,
            disabled: pendingAction !== null || colorsLocked,
            onChange: (value) => void updateSettings(
              value ? { game_art_gradient_enabled: true, icon_gradient_enabled: false } : { game_art_gradient_enabled: false }
            )
          }
        ) }),
        /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
          DropdownItem,
          {
            label: "Gradient direction",
            description: "Direction of the card's background gradient, or a flat solid color.",
            rgOptions: GRADIENT_DIRECTION_OPTIONS,
            selectedOption: settings.gradient_direction,
            disabled: pendingAction !== null || colorsLocked,
            onChange: (selection) => void updateSettings({ gradient_direction: selection.data })
          }
        ) }),
        /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
          "div",
          {
            style: {
              height: "18px",
              borderRadius: "999px",
              background: `linear-gradient(90deg, ${settings.normal_gradient_start}, ${settings.normal_gradient_end})`,
              border: "1px solid rgba(255,255,255,0.35)",
              opacity: colorsLocked ? 0.35 : 1
            }
          }
        ) }),
        /* @__PURE__ */ jsx(PanelSectionRow, { children: colorButton("normal_gradient_start", "Normal gradient start") }),
        /* @__PURE__ */ jsx(PanelSectionRow, { children: colorButton("normal_gradient_end", "Normal gradient end") }),
        /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
          "div",
          {
            style: {
              height: "18px",
              borderRadius: "999px",
              background: `linear-gradient(90deg, ${settings.rare_gradient_start}, ${settings.rare_gradient_end})`,
              border: "1px solid rgba(255,255,255,0.35)",
              opacity: colorsLocked ? 0.35 : 1
            }
          }
        ) }),
        /* @__PURE__ */ jsx(PanelSectionRow, { children: colorButton("rare_gradient_start", "Rare gradient start") }),
        /* @__PURE__ */ jsx(PanelSectionRow, { children: colorButton("rare_gradient_end", "Rare gradient end") }),
        /* @__PURE__ */ jsx(PanelSectionRow, { children: colorButton("normal_circle_color", "Normal circle color") }),
        /* @__PURE__ */ jsx(PanelSectionRow, { children: colorButton("rare_circle_color", "Rare circle color") })
      ] }),
      /* @__PURE__ */ jsxs(PanelSection, { title: "Glow", children: [
        /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
          ToggleField,
          {
            label: "Icon glow",
            description: "The soft glow around the icon, and the pulsing glow ring (rare achievements, or normal ones too if enabled below).",
            checked: settings.icon_glow_enabled,
            disabled: pendingAction !== null,
            onChange: (value) => void updateSettings({ icon_glow_enabled: value })
          }
        ) }),
        settings.icon_glow_enabled && /* @__PURE__ */ jsxs(Fragment2, { children: [
          /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
            SliderField,
            {
              label: "Glow intensity",
              description: "50 is the default look; 0 is basically off, 100 doubles it.",
              value: settings.icon_glow_intensity,
              min: GLOW_INTENSITY_RANGE.min,
              max: GLOW_INTENSITY_RANGE.max,
              step: GLOW_INTENSITY_RANGE.step,
              notchCount: 11,
              showValue: true,
              disabled: pendingAction !== null,
              onChange: (value) => void updateSettings({ icon_glow_intensity: value })
            }
          ) }),
          /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
            SliderField,
            {
              label: "Ring size",
              description: "How far the glow rings spread. 50 is the default look; 0 hides them, 100 doubles it.",
              value: settings.ring_size,
              min: RING_SIZE_RANGE.min,
              max: RING_SIZE_RANGE.max,
              step: RING_SIZE_RANGE.step,
              notchCount: 11,
              showValue: true,
              disabled: pendingAction !== null,
              onChange: (value) => void updateSettings({ ring_size: value })
            }
          ) }),
          /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
            ToggleField,
            {
              label: "Glow for normal achievements",
              description: "The pulsing glow ring normally only plays for rare unlocks -- turn this on to also play it for regular ones. (The rare corner ribbon and sparkles stay rare-only, since those specifically mean 'this one's rare'.)",
              checked: settings.glow_normal_enabled,
              disabled: pendingAction !== null,
              onChange: (value) => void updateSettings({ glow_normal_enabled: value })
            }
          ) })
        ] }),
        /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
          ToggleField,
          {
            label: "Icon frame ring",
            description: "The colored ring framing the icon, separate from the glow above. With it off, the icon just sits on a plain dark backing.",
            checked: settings.icon_frame_ring_enabled,
            disabled: pendingAction !== null,
            onChange: (value) => void updateSettings({ icon_frame_ring_enabled: value })
          }
        ) })
      ] }),
      /* @__PURE__ */ jsxs(PanelSection, { title: "Text", children: [
        /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
          SliderField,
          {
            label: "Title font size",
            description: "Font size of the achievement name.",
            value: settings.title_font_size,
            min: FONT_SIZE_RANGES.title_font_size.min,
            max: FONT_SIZE_RANGES.title_font_size.max,
            step: 1,
            showValue: true,
            disabled: pendingAction !== null,
            onChange: (value) => void updateSettings({ title_font_size: value })
          }
        ) }),
        /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
          SliderField,
          {
            label: "Description font size",
            description: "Font size of the subtitle/description line.",
            value: settings.subtitle_font_size,
            min: FONT_SIZE_RANGES.subtitle_font_size.min,
            max: FONT_SIZE_RANGES.subtitle_font_size.max,
            step: 1,
            showValue: true,
            disabled: pendingAction !== null,
            onChange: (value) => void updateSettings({ subtitle_font_size: value })
          }
        ) }),
        /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
          SliderField,
          {
            label: "Label font size",
            description: "Font size of the small eyebrow label above the title.",
            value: settings.label_font_size,
            min: FONT_SIZE_RANGES.label_font_size.min,
            max: FONT_SIZE_RANGES.label_font_size.max,
            step: 1,
            showValue: true,
            disabled: pendingAction !== null,
            onChange: (value) => void updateSettings({ label_font_size: value })
          }
        ) })
      ] })
    ] }),
    view === "sound" && /* @__PURE__ */ jsxs(Fragment2, { children: [
      /* @__PURE__ */ jsxs(PanelSection, { title: "Sound", children: [
        /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
          SliderField,
          {
            label: "Volume",
            description: "50% is the default volume; 0% is silent.",
            value: settings.volume_percent,
            min: 0,
            max: 100,
            step: 10,
            notchCount: 11,
            showValue: true,
            valueSuffix: "%",
            disabled: pendingAction !== null,
            onChange: (value) => void updateSettings({ volume_percent: value })
          }
        ) }),
        SOUND_SLOT_OPTIONS.map(({ slot, label, description }) => {
          const key = `sound_${slot}`;
          return /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
            DropdownItem,
            {
              label,
              description,
              rgOptions: soundOptions,
              selectedOption: settings[key],
              disabled: pendingAction !== null || soundOptions.length === 0,
              onChange: (selection) => void updateSettings({ [key]: selection.data })
            }
          ) }, slot);
        }),
        /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsxs("div", { style: { fontSize: "12px", opacity: 0.8 }, children: [
          "Your own sounds: put .wav, .flac, .ogg or .mp3 files (10 MB or less, kept short) in",
          " ",
          /* @__PURE__ */ jsx("b", { children: soundFolder || "the Finally Achievement Plugin settings folder, sounds" }),
          ', then press Refresh. They show up with "(yours)" after their name, and updating the plugin never deletes them. Use the test buttons below to hear each one.'
        ] }) }),
        /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
          ButtonItem,
          {
            layout: "below",
            disabled: pendingAction !== null,
            onClick: () => void refreshSettings(),
            children: "Refresh sound list"
          }
        ) })
      ] }),
      /* @__PURE__ */ jsxs(PanelSection, { title: "Popup Tests", children: [
        /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
          ToggleField,
          {
            label: "Use my recent unlocks for tests",
            description: "Tests show one of your recent RetroAchievements unlocks with its real badge. Tests never count as unlocks. With no login saved, tests use a sample.",
            checked: settings.test_with_game_data,
            disabled: pendingAction !== null,
            onChange: (value) => void updateSettings({ test_with_game_data: value })
          }
        ) }),
        /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
          ButtonItem,
          {
            disabled: pendingAction !== null,
            onClick: () => void trigger("test_popup_common"),
            layout: "below",
            description: "A common unlock (above the Uncommon cutoff): no tier label.",
            children: "Test Common"
          }
        ) }),
        /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
          ButtonItem,
          {
            disabled: pendingAction !== null,
            onClick: () => void trigger("test_popup_uncommon"),
            layout: "below",
            description: "An uncommon unlock: tier label only.",
            children: "Test Uncommon"
          }
        ) }),
        /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
          ButtonItem,
          {
            disabled: pendingAction !== null,
            onClick: () => void trigger("test_popup_rare"),
            layout: "below",
            description: "A rare unlock: gold look, rare sound and glow.",
            children: "Test Rare"
          }
        ) }),
        /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
          ButtonItem,
          {
            disabled: pendingAction !== null,
            onClick: () => void trigger("test_popup_ultra_rare"),
            layout: "below",
            description: "An ultra rare unlock: extra sparkles and a longer shine.",
            children: "Test Ultra Rare"
          }
        ) }),
        /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
          ButtonItem,
          {
            disabled: pendingAction !== null,
            onClick: () => void trigger("test_completion_popup"),
            layout: "below",
            description: "The special popup for unlocking every achievement in a game, using the running game's name.",
            children: "Test Completionist"
          }
        ) })
      ] })
    ] }),
    view === "advanced" && /* @__PURE__ */ jsxs(Fragment2, { children: [
      /* @__PURE__ */ jsxs(PanelSection, { title: "Popup Not Showing?", children: [
        /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx("div", { style: { fontSize: "12px", opacity: 0.8 }, children: "If you hear the sound but no popup appears (for example on a different handheld), run this check. It tests the Python packages, graphics libraries, display and window creation the popup needs, and tells you what's missing." }) }),
        /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
          ButtonItem,
          {
            layout: "below",
            disabled: pendingAction !== null,
            onClick: () => void handleOverlayCheck(),
            children: pendingAction === "overlay_check" ? "Checking..." : "Run overlay check"
          }
        ) }),
        overlayCheck && /* @__PURE__ */ jsxs(Fragment2, { children: [
          /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx("div", { style: { fontSize: "13px", fontWeight: 600, color: overlayCheck.ok ? "#5cc35c" : "#ff8a5c" }, children: overlayCheck.verdict }) }),
          overlayCheck.checks.map((check, index) => /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsxs("div", { style: { fontSize: "12px", display: "flex", gap: 6 }, children: [
            /* @__PURE__ */ jsx("span", { style: { color: check.ok ? "#5cc35c" : check.fatal === false ? "#d8c25c" : "#ff8a5c", flexShrink: 0 }, children: check.ok ? "✓" : check.fatal === false ? "!" : "✗" }),
            /* @__PURE__ */ jsxs("span", { style: { opacity: 0.9 }, children: [
              /* @__PURE__ */ jsx("b", { children: check.name }),
              check.detail ? ` — ${check.detail}` : ""
            ] })
          ] }) }, `${check.name}-${index}`)),
          (overlayCheck.last_status || overlayCheck.last_error) && /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsxs("div", { style: { fontSize: "12px", opacity: 0.8 }, children: [
            "Last popup: ",
            overlayCheck.last_status || "none yet",
            overlayCheck.last_error ? ` — ${overlayCheck.last_error}` : ""
          ] }) })
        ] })
      ] }),
      /* @__PURE__ */ jsxs(PanelSection, { title: "Status", children: [
        /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsx(
          ButtonItem,
          {
            disabled: pendingAction !== null,
            onClick: () => void refreshStatus(),
            description: "Manually refresh backend status.",
            children: "Refresh Status"
          }
        ) }),
        /* @__PURE__ */ jsx(PanelSectionRow, { children: /* @__PURE__ */ jsxs("div", { style: { fontSize: 13 }, children: [
          /* @__PURE__ */ jsxs("div", { children: [
            "Popup helper: ",
            status?.gamescope_overlay_status ?? "-"
          ] }),
          status?.gamescope_overlay_last_error ? /* @__PURE__ */ jsxs("div", { style: { color: "#ff8a80" }, children: [
            "Popup error: ",
            status.gamescope_overlay_last_error
          ] }) : null,
          /* @__PURE__ */ jsxs("div", { children: [
            "Last toast: ",
            formatTimestamp(status?.last_match_timestamp ?? null)
          ] }),
          /* @__PURE__ */ jsxs("div", { children: [
            "Last source: ",
            status?.last_match_source ?? "-"
          ] }),
          /* @__PURE__ */ jsxs("div", { children: [
            "Last: ",
            status?.last_match_sample ?? "-"
          ] }),
          /* @__PURE__ */ jsxs("div", { children: [
            "Last event:",
            " ",
            lastEvent ? `${lastEvent.title} @ ${formatTimestamp(lastEvent.timestamp)}` : "none"
          ] }),
          statusError ? /* @__PURE__ */ jsxs("div", { style: { color: "#ff8a80" }, children: [
            "Status error: ",
            statusError
          ] }) : null
        ] }) })
      ] })
    ] })
  ] });
}
var index_default = definePlugin(() => {
  return {
    name: "RetroAchievements Toasts",
    icon: /* @__PURE__ */ jsx(FaTrophy, {}),
    alwaysRender: true,
    titleView: /* @__PURE__ */ jsx("div", { className: staticClasses.Title, children: "RetroAchievements Toasts" }),
    content: /* @__PURE__ */ jsx(StatusPanel, {})
  };
});
export {
  index_default as default
};
