#!/usr/bin/env python3
"""Validate a source-packet JSON file against ``contracts/source-packet-v1.schema.json`` (stdlib subset)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    here = Path(__file__).resolve().parent
    root = here.parent
    sys.path.insert(0, str(root))

    parser = argparse.ArgumentParser(description="Validate RFO source-packet JSON.")
    parser.add_argument("--source-packet", required=True, help="Path to source-packet.json")
    parser.add_argument(
        "--template-mode",
        action="store_true",
        help="Accept placeholder strings in topic/profile (for template fixtures only).",
    )
    args = parser.parse_args()

    path = Path(args.source_packet).expanduser().resolve(strict=False)
    if not path.is_file():
        print(json.dumps({"ok": False, "errors": [f"missing_file:{path}"]}, indent=2))
        return 2

    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(json.dumps({"ok": False, "errors": [f"json:{e}"]}, indent=2))
        return 2

    schema_path = root / "contracts" / "source-packet-v1.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    from validators.core.v19_stdlib_schema_walk import validate_instance

    errs = validate_instance(doc, schema, root=schema, strict_additional=False)
    soft: list[str] = []
    if args.template_mode:
        topic = str(doc.get("topic") or "")
        prof = str(doc.get("profile") or "")
        if topic.startswith("{{") or prof.startswith("{{"):
            soft.append("template_placeholder_ok")

    if errs:
        print(
            json.dumps(
                {"ok": False, "errors": [f"{c}:{m}" for c, m in errs], "notes": soft},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    print(json.dumps({"ok": True, "path": str(path), "notes": soft}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
