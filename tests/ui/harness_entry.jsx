import * as React from "react";
import { createRoot } from "react-dom/client";
import * as JSX from "react/jsx-runtime";
const h = React.createElement;
window.SP_REACT = React; window.SP_JSX = JSX;
const listeners = {};
window.DFL = {
  PanelSection: ({ title, children }) => h("section", { className: "sec" }, h("h3", null, title), children),
  PanelSectionRow: ({ children }) => h("div", { className: "row" }, children),
  DialogButton: ({ onClick, children, style }) => h("button", { onClick, style: { ...style, width: "auto" } }, children),
  ButtonItem: ({ onClick, disabled, children, description }) => h("div", null, h("button", { onClick, disabled }, children), description ? h("small", null, description) : null),
  ToggleField: ({ label, checked, onChange, disabled, description }) => h("label", { className: "tog" }, h("input", { type: "checkbox", checked: !!checked, disabled, onChange: (e) => onChange(e.target.checked) }), " ", label, description ? h("small", null, " " + description) : null),
  TextField: ({ label, value, onChange, description, bIsPassword, disabled }) => h("label", null, label, h("input", { "aria-label": label, type: bIsPassword ? "password" : "text", value, disabled, onChange }), description ? h("small", null, description) : null),
  SliderField: ({ label, value, min, max, step, onChange, disabled }) => h("label", null, label + " " + value, h("input", { "aria-label": label, type: "range", min, max, step, value, disabled, onChange: (e) => onChange(Number(e.target.value)) })),
  DropdownItem: ({ label, rgOptions, selectedOption, onChange }) => h("label", null, label, h("select", { "aria-label": label, value: selectedOption, onChange: (e) => onChange(rgOptions.find((o) => o.data === e.target.value)) }, rgOptions.map((o) => h("option", { key: o.data, value: o.data }, o.label)))),
  Focusable: ({ children }) => h("div", null, children),
  ColorPickerModal: () => null, showModal: () => null, staticClasses: { Title: "t" },
};
window.__DECKY_SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED_deckyLoaderAPIInit = {
  connect: () => ({
    callable: (name) => async (...args) => {
      const r = await fetch("/call", { method: "POST", body: JSON.stringify({ name, args }) });
      const j = await r.json(); if (j.error) throw new Error(j.error); return j.result;
    },
    addEventListener: (n, cb) => { (listeners[n] ||= []).push(cb); return cb; },
    removeEventListener: () => {}, routerHook: {}, toaster: {},
  }),
};
const mod = await import("/dist/index.js");
const plugin = mod.default();
createRoot(document.getElementById("root")).render(h("div", { id: "qam" }, plugin.titleView, plugin.content));
window.__ready = true;
