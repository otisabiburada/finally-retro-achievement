"""Crude undefined-name / missing-method check (pyflakes isn't always available)."""
import ast, builtins, sys
path = sys.argv[1]
tree = ast.parse(open(path, encoding="utf-8").read())
defined = set(dir(builtins))
for n in ast.walk(tree):
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)): defined.add(n.name)
    if isinstance(n, ast.arg): defined.add(n.arg)
    if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)): defined.add(n.id)
    if isinstance(n, (ast.Import, ast.ImportFrom)):
        for a in n.names: defined.add((a.asname or a.name).split(".")[0])
    if isinstance(n, ast.ExceptHandler) and n.name: defined.add(n.name)
bad = sorted({(n.id, n.lineno) for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id not in defined})
cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Plugin")
members = {n.name for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
for n in cls.body:
    if isinstance(n, ast.Assign):
        for t in n.targets:
            if isinstance(t, ast.Name): members.add(t.id)
assigned = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute) and isinstance(n.ctx, ast.Store) and isinstance(n.value, ast.Name) and n.value.id == "self"}
missing = sorted({(n.attr, n.lineno) for n in ast.walk(cls) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "self"
                  and isinstance(n.ctx, ast.Load) and n.attr not in members and n.attr not in assigned})
print("undefined names:", bad); print("missing self attributes:", missing)
sys.exit(1 if bad or missing else 0)
