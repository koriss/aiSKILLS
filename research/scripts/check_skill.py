#!/usr/bin/env python3
"""Structural validation for SKILL.md (same contract as deep-investigation-agent)."""
import re
import sys
from pathlib import Path

ALLOWED_KEYS = {"name", "description", "license", "allowed-tools", "metadata"}


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    sys.exit(1)


def ok(message: str) -> None:
    print(f"OK: {message}")
    sys.exit(0)


def extract_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        fail("SKILL.md must start with YAML frontmatter")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        fail("Invalid YAML frontmatter block")
    return match.group(1)


def parse_top_level_keys(frontmatter: str):
    keys = []
    for line in frontmatter.splitlines():
        if not line.strip():
            continue
        if line.startswith(" ") or line.startswith("\t"):
            continue
        m = re.match(r"^([A-Za-z0-9_-]+):", line)
        if m:
            keys.append(m.group(1))
    return keys


def extract_scalar(frontmatter: str, key: str):
    pattern = rf"(?m)^{re.escape(key)}:\s*(.+)$"
    m = re.search(pattern, frontmatter)
    if not m:
        return None
    value = m.group(1).strip()
    if value.startswith('"') and value.endswith('"'):
        value = value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        value = value[1:-1]
    return value


def main():
    if len(sys.argv) != 2:
        fail("Usage: python3 check_skill.py <skill_directory>")
    skill_dir = Path(sys.argv[1])
    skill_md = skill_dir / "SKILL.md"
    if not skill_dir.exists() or not skill_dir.is_dir():
        fail(f"Skill directory not found: {skill_dir}")
    if not skill_md.exists():
        fail(f"SKILL.md not found: {skill_md}")
    text = skill_md.read_text(encoding="utf-8")
    frontmatter = extract_frontmatter(text)
    keys = parse_top_level_keys(frontmatter)
    unexpected = sorted(set(keys) - ALLOWED_KEYS)
    if unexpected:
        fail(f"Unexpected frontmatter keys: {', '.join(unexpected)}")
    name = extract_scalar(frontmatter, "name")
    description = extract_scalar(frontmatter, "description")
    if not name:
        fail("Missing 'name' in frontmatter")
    if not re.fullmatch(r"[a-z0-9-]+", name):
        fail("name must be hyphen-case: lowercase letters, digits, and hyphens only")
    if name.startswith("-") or name.endswith("-") or "--" in name:
        fail("name cannot start/end with hyphen or contain consecutive hyphens")
    if len(name) > 64:
        fail("name exceeds 64 characters")
    if not description:
        fail("Missing 'description' in frontmatter")
    if "<" in description or ">" in description:
        fail("description cannot contain angle brackets")
    if len(description) > 1024:
        fail("description exceeds 1024 characters")
    for section in (
        "## Runtime workflow",
        "## Tool policy",
        "## Memory policy",
        "## Output requirements",
        "## Quality gates",
    ):
        if section not in text:
            fail(f"SKILL.md must contain '{section}'")
    ok("skill structure and frontmatter validated")


if __name__ == "__main__":
    main()
