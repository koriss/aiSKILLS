#!/usr/bin/env python3
"""AST-based import graph for the RFO skill.

Analyzes layered imports across `runtime/`, `scripts/`, `providers/`, `tools/`.
Outputs:
  - JSON: full edge list + leaks + cycles
  - Markdown summary with layer-leak detection and a Mermaid diagram

Layer rules (agent-native):
  - runtime/ MUST NOT import providers/* or scripts/* (top of the stack)
  - providers/* MAY import runtime/* (adapters use runtime API)
  - scripts/* MAY import runtime/* (validators/smoke tests)
  - tools/* MAY import runtime/* (operator-side tooling)
"""
from __future__ import annotations
import ast
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOTS = ("runtime", "scripts", "providers", "tools")
SKIP = {".venv", "__pycache__", ".tmp-exec-runs", "release-artifacts", "kb", "legacy"}


def file_to_module(path: Path, base: Path) -> str:
    rel = path.relative_to(base).with_suffix("")
    parts = rel.parts
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def collect_files(base: Path) -> list[Path]:
    out: list[Path] = []
    for r in ROOTS:
        d = base / r
        if not d.is_dir():
            continue
        for p in d.rglob("*.py"):
            if any(part in SKIP for part in p.relative_to(base).parts):
                continue
            out.append(p)
    return sorted(out)


def parse_imports(path: Path) -> list[tuple[str, int]]:
    """Return list of (imported_name, lineno)."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    imports: list[tuple[str, int]] = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for alias in n.names:
                imports.append((alias.name, n.lineno))
        elif isinstance(n, ast.ImportFrom):
            mod = n.module or ""
            level = n.level or 0
            imports.append(("." * level + mod, n.lineno))
    return imports


def normalize_relative(imp: str, src_module: str) -> str:
    if not imp.startswith("."):
        return imp
    dots = len(imp) - len(imp.lstrip("."))
    rest = imp[dots:]
    pkg = src_module.split(".")
    # drop trailing components for relative resolution
    if dots > len(pkg):
        return imp
    base = pkg[: len(pkg) - dots + 1] if dots > 0 else pkg
    base = pkg[: len(pkg) - dots]
    if rest:
        return ".".join([*base, rest]) if base else rest
    return ".".join(base)


def top_layer(module: str) -> str | None:
    head = module.split(".", 1)[0]
    if head in ROOTS:
        return head
    return None


def main() -> int:
    base = Path(os.environ["SKILL_DIR"]).resolve()
    out_dir = Path(os.environ["REPORTS_DIR"]) / "06-import-graph"
    out_dir.mkdir(parents=True, exist_ok=True)

    files = collect_files(base)
    file_to_mod: dict[Path, str] = {p: file_to_module(p, base) for p in files}
    edges: list[dict] = []
    leaks: list[dict] = []
    layer_edges: dict[tuple[str, str], int] = defaultdict(int)

    # build module -> path map for cycle / internal edges
    mod_to_path: dict[str, Path] = {m: p for p, m in file_to_mod.items()}

    for p in files:
        src_mod = file_to_mod[p]
        src_layer = top_layer(src_mod)
        if not src_layer:
            continue
        for imp, lineno in parse_imports(p):
            target = normalize_relative(imp, src_mod) if imp.startswith(".") else imp
            tgt_layer = top_layer(target)
            if not tgt_layer:
                continue
            edges.append(
                {
                    "src": src_mod,
                    "src_file": str(p.relative_to(base)),
                    "src_layer": src_layer,
                    "target": target,
                    "target_layer": tgt_layer,
                    "lineno": lineno,
                }
            )
            layer_edges[(src_layer, tgt_layer)] += 1
            # leak rule: runtime cannot import providers/scripts/tools
            if src_layer == "runtime" and tgt_layer in ("providers", "scripts", "tools"):
                leaks.append(
                    {
                        "src_file": str(p.relative_to(base)),
                        "src_module": src_mod,
                        "target": target,
                        "lineno": lineno,
                    }
                )

    # Cycle detection within runtime/ only (DFS)
    runtime_mods = sorted(m for m in mod_to_path if top_layer(m) == "runtime")
    g: dict[str, set[str]] = defaultdict(set)
    for e in edges:
        if e["src_layer"] == "runtime" and e["target_layer"] == "runtime":
            # store target as a known module if exists
            t = e["target"]
            # collapse subimport like runtime.x.y -> runtime.x.y if in mod_to_path
            if t in mod_to_path:
                g[e["src"]].add(t)
            else:
                # try short prefix
                parts = t.split(".")
                while parts:
                    cand = ".".join(parts)
                    if cand in mod_to_path:
                        g[e["src"]].add(cand)
                        break
                    parts.pop()

    cycles: list[list[str]] = []
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {m: WHITE for m in runtime_mods}
    stack: list[str] = []

    def dfs(u: str) -> None:
        color[u] = GRAY
        stack.append(u)
        for v in g.get(u, ()):
            if color.get(v, WHITE) == GRAY:
                # cycle
                idx = stack.index(v)
                cyc = stack[idx:] + [v]
                cycles.append(cyc)
            elif color.get(v, WHITE) == WHITE:
                dfs(v)
        stack.pop()
        color[u] = BLACK

    for m in runtime_mods:
        if color.get(m, WHITE) == WHITE:
            dfs(m)

    # Layer summary
    layer_summary = {f"{a}->{b}": n for (a, b), n in sorted(layer_edges.items())}

    # Save JSON
    out_json = {
        "files_scanned": len(files),
        "edge_count": len(edges),
        "layer_edges": layer_summary,
        "leaks_runtime_to_below": leaks,
        "cycles_in_runtime": [list(c) for c in cycles],
        "edges": edges,
    }
    (out_dir / "import-graph.json").write_text(json.dumps(out_json, indent=2))

    # Mermaid layer diagram
    mer = ["flowchart TD"]
    nodes = sorted({a for (a, _) in layer_edges} | {b for (_, b) in layer_edges})
    for n in nodes:
        mer.append(f"    {n}[{n}/]")
    for (a, b), n in sorted(layer_edges.items()):
        if a == b:
            continue
        arrow = "-->|" + str(n) + "|"
        mer.append(f"    {a} {arrow} {b}")
    (out_dir / "layer-graph.mmd").write_text("\n".join(mer) + "\n")

    # Print summary for shell
    print(f"files_scanned={len(files)} edges={len(edges)}")
    print("layer edges:")
    for k, v in layer_summary.items():
        print(f"  {k:40s} {v}")
    print(f"leaks runtime->[providers/scripts/tools]: {len(leaks)}")
    for l in leaks[:25]:
        print(f"  {l['src_file']}:{l['lineno']}  -> {l['target']}")
    print(f"cycles within runtime/: {len(cycles)}")
    for c in cycles[:10]:
        print("  " + " -> ".join(c))
    return 0


if __name__ == "__main__":
    sys.exit(main())
