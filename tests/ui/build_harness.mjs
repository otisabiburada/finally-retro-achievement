// Bundles the stand-in Decky environment used by run_ui.py. Needs esbuild + react + react-dom (NODE_TOOLS).
import { pathToFileURL } from "node:url";
import path from "node:path";
const tools = process.env.NODE_TOOLS || path.resolve("node_modules");
const { build } = await import(pathToFileURL(path.join(tools, "esbuild/lib/main.js")).href);
const here = path.dirname(new URL(import.meta.url).pathname);
await build({ entryPoints: [path.join(here, "harness_entry.jsx")], bundle: true, format: "esm", outfile: path.join(here, "harness.js"),
  jsx: "automatic", nodePaths: [tools, ...(process.env.REACT_PATH ? [process.env.REACT_PATH] : [])], external: ["/dist/index.js"], logLevel: "warning", target: "es2022" });
console.log("built tests/ui/harness.js");
