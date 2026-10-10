// Offline fallback for building dist/index.js with esbuild (when pnpm/rollup can't be used).
// The official build is `pnpm install && pnpm run build`. This produces an equivalent bundle that talks to
// Decky through the same window globals. Usage: node tools/build-offline.mjs
// Needs esbuild and react-icons; set NODE_TOOLS to a node_modules folder that has them.
import { pathToFileURL } from "node:url";
import path from "node:path";
const tools = process.env.NODE_TOOLS || path.resolve("node_modules");
const { build } = await import(pathToFileURL(path.join(tools, "esbuild/lib/main.js")).href);
const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const shim = (f) => path.join(root, "tools/shims", f);
const map = { "react": shim("react.js"), "react/jsx-runtime": shim("jsx.js"), "@decky/ui": shim("ui.js"), "@decky/api": shim("api.js") };
await build({
  entryPoints: [path.join(root, "src/index.tsx")], bundle: true, format: "esm", target: "es2020",
  outfile: path.join(root, "dist/index.js"), jsx: "automatic", charset: "utf8", logLevel: "warning",
  nodePaths: [tools],
  plugins: [{ name: "decky-globals", setup(b) { b.onResolve({ filter: /^(react|react\/jsx-runtime|@decky\/ui|@decky\/api)$/ }, (a) => ({ path: map[a.path] })); } }],
});
console.log("built dist/index.js");
