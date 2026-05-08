"""AST-based scan of runtime/ for agent-native violations.

Findings collected:
- str_with_url: any string literal of length >=10 containing http://, https://, .com, .org, .io, .net, .ai
- env_lookup: every os.environ.get(name) / os.environ[name] / os.getenv(name)
- network_imports: top-level imports of requests, httpx, urllib.request, aiohttp
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

URL_TOKENS = ("http://", "https://", ".com", ".org", ".io", ".net", ".ai")
NETWORK_MODULES = {"requests", "httpx", "aiohttp"}
NETWORK_FROM = {("urllib", "request"), ("urllib", "urlopen")}

def scan_file(path: Path) -> dict:
    findings = {
        "url_strings": [],
        "env_lookups": [],
        "network_imports": [],
    }
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return {"error": str(exc)}
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        return {"error": f"syntax: {exc}"}

    for node in ast.walk(tree):
        # url strings
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            v = node.value
            if len(v) >= 10 and any(t in v for t in URL_TOKENS):
                findings["url_strings"].append({
                    "line": node.lineno,
                    "value": v if len(v) <= 200 else (v[:200] + "...[truncated]"),
                })
        # env lookups
        elif isinstance(node, ast.Call):
            target_name = None
            target_attr = None
            if isinstance(node.func, ast.Attribute):
                attr = node.func.attr
                if attr in {"get", "getenv"} and isinstance(node.func.value, ast.Attribute):
                    if node.func.value.attr == "environ" and isinstance(node.func.value.value, ast.Name):
                        if node.func.value.value.id == "os":
                            target_attr = attr
                if attr == "getenv" and isinstance(node.func.value, ast.Name) and node.func.value.id == "os":
                    target_attr = "getenv"
            if target_attr:
                arg = node.args[0] if node.args else None
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    findings["env_lookups"].append({
                        "line": node.lineno,
                        "name": arg.value,
                        "kind": target_attr,
                    })
        elif isinstance(node, ast.Subscript):
            # os.environ['NAME']
            if isinstance(node.value, ast.Attribute) and node.value.attr == "environ":
                if isinstance(node.value.value, ast.Name) and node.value.value.id == "os":
                    sl = node.slice
                    if isinstance(sl, ast.Constant) and isinstance(sl.value, str):
                        findings["env_lookups"].append({
                            "line": node.lineno,
                            "name": sl.value,
                            "kind": "subscript",
                        })
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in NETWORK_MODULES:
                    findings["network_imports"].append({"line": node.lineno, "import": alias.name})
                if alias.name == "urllib.request":
                    findings["network_imports"].append({"line": node.lineno, "import": alias.name})
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module in NETWORK_MODULES:
                for alias in node.names:
                    findings["network_imports"].append({
                        "line": node.lineno,
                        "import": f"{node.module}.{alias.name}",
                    })
            if node.module == "urllib.request" or node.module == "urllib":
                for alias in node.names:
                    findings["network_imports"].append({
                        "line": node.lineno,
                        "import": f"{node.module}.{alias.name}",
                    })
    return findings


def main(argv: list[str]) -> int:
    runtime = Path(argv[1])
    out_path = Path(argv[2])
    aggregate = {}
    py_files = sorted(runtime.rglob("*.py"))
    for pf in py_files:
        rel = str(pf.relative_to(runtime.parent))
        result = scan_file(pf)
        if "error" in result:
            aggregate[rel] = result
            continue
        # only keep non-empty
        if result["url_strings"] or result["env_lookups"] or result["network_imports"]:
            aggregate[rel] = result
    out_path.write_text(json.dumps(aggregate, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    # quick stats
    stats = {
        "files_scanned": len(py_files),
        "files_with_findings": len(aggregate),
        "url_string_total": sum(len(v.get("url_strings", [])) for v in aggregate.values() if isinstance(v, dict)),
        "env_lookup_total": sum(len(v.get("env_lookups", [])) for v in aggregate.values() if isinstance(v, dict)),
        "network_import_total": sum(len(v.get("network_imports", [])) for v in aggregate.values() if isinstance(v, dict)),
    }
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
