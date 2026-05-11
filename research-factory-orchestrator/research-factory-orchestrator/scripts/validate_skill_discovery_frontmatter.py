#!/usr/bin/env python3
from pathlib import Path
import json
import re
import sys

root = Path(__file__).resolve().parents[1]
skill = root / "SKILL.md"
text = skill.read_text(encoding="utf-8") if skill.exists() else ""
errors: list[str] = []
ver_m = None

if not text.startswith("---"):
    errors.append("missing_yaml_frontmatter")
else:
    parts = text.split("---", 2)
    fm = parts[1] if len(parts) >= 3 else ""
    if not re.search(r"(?m)^name:\s*research_factory_orchestrator\s*$", fm):
        errors.append("missing_name_research_factory_orchestrator")
    if not re.search(r"(?m)^metadata:\s*$", fm):
        errors.append("missing_metadata")
    ver_m = re.search(r'(?m)^\s+version:\s*"([^"]+)"\s*$', fm)
    rel_m = re.search(r'(?m)^\s+release:\s*"([^"]+)"\s*$', fm)
    if not ver_m:
        errors.append("wrong_or_missing_metadata_version")
    else:
        vers = ver_m.group(1)
        if not re.match(r"^19\.(?:3|4)(?:\.\d+)*$", vers):
            errors.append(f"bad_skill_version_syntax_{vers}")
    if rel_m and ver_m and rel_m.group(1) != ver_m.group(1):
        errors.append("metadata_release_mismatch_metadata_version")

out_ver = ver_m.group(1) if ver_m else "unknown"
out = {
    "status": "fail" if errors else "pass",
    "validator": "validate_skill_discovery_frontmatter",
    "version": out_ver,
    "errors": errors,
}
print(json.dumps(out, ensure_ascii=False, indent=2))
sys.exit(1 if errors else 0)
