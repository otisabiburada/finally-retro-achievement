#!/bin/sh
# Runs every check. From the plugin folder:  sh tests/run_all.sh
# UI test is skipped unless playwright (python) and NODE_TOOLS (esbuild, react, react-dom) are available.
set -e
cd "$(dirname "$0")/.."
python3 tests/lint_names.py main.py
python3 tests/test_backend.py .
python3 tests/test_backend.py . html.parser,http.server,xml,sqlite3      # Decky's Python can lack modules
python3 tests/test_v11.py .
python3 tests/test_v11.py . html.parser,http.server,xml,sqlite3
python3 tests/test_v12.py .
python3 tests/test_v12.py . html.parser,http.server,xml,sqlite3
python3 tests/test_v13.py .
python3 tests/test_v13.py . html.parser,http.server,xml,sqlite3
if python3 -c "import playwright" 2>/dev/null && [ -n "$NODE_TOOLS" ]; then
  node tests/ui/build_harness.mjs
  python3 tests/ui/run_ui.py .
else
  echo "UI test skipped (needs python playwright and NODE_TOOLS)"
fi
echo "ALL CHECKS PASSED"
