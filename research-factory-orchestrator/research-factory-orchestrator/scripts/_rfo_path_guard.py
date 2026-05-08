"""RFO v19.2.1 hard-guard module: canonical skill path + approved runs-root.

This module is imported by every public RFO entry point in ``scripts/`` before
any other RFO code is imported. It enforces the honesty contract introduced in
v19.2.1 so that an agent (or operator) physically cannot run RFO from a
``*.bak``/``*.old``/``*.disabled`` skill copy or with an unmanaged
``--runs-root`` such as ``/tmp/rfo-runs`` without explicit consent.

When an invariant is violated the process exits with a stable code and a
deterministic stderr stamp so that ``scripts/verify_openclaw_run.py`` can
classify the failure (see ``LIE-DETECTED-*`` codes added in v19.2.1).

Stable exit codes
-----------------
``11``  ``RFO-NON-CANONICAL-SKILL-PATH``
``12``  ``RFO-RUNS-ROOT-FORBIDDEN``

Override env vars (consent for smoke / dev only)
-------------------------------------------------
``RFO_RUNS_ROOT``               extra absolute path that is treated as an
                                allowed runs-root (in addition to the
                                default ``$HOME/.openclaw/workspace/rfo-runs``).
``RFO_ALLOW_TMP_RUNS_ROOT=1``   permit ``/tmp`` or ``/var/tmp`` as runs-root
                                (used by smoke tests; logged in
                                ``feature-truth-matrix.json`` as
                                ``runs_root_consent_tmp``).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

EXIT_NON_CANONICAL_SKILL_PATH = 11
EXIT_RUNS_ROOT_FORBIDDEN = 12

CANONICAL_SKILL_NAME = "research-factory-orchestrator"

ALLOWED_PARENT_DIR_NAMES = (
    "skills",
    "research-factory-orchestrator",
)

FORBIDDEN_PATH_TOKENS = (
    ".bak",
    ".old",
    ".backup",
    ".disabled",
    ".tmp",
    ".save",
    "copy of ",
)

RUNS_ROOT_ENV = "RFO_RUNS_ROOT"
ALLOW_TMP_ENV = "RFO_ALLOW_TMP_RUNS_ROOT"

_CANONICAL_HINT = (
    "Canonical invocation:\n"
    "  cd ~/.openclaw/workspace/skills/research-factory-orchestrator && \\\n"
    "    python3 -S scripts/interface_runtime_adapter.py \\\n"
    "      --runs-root ~/.openclaw/workspace/rfo-runs \\\n"
    "      --interface telegram --provider telegram \\\n"
    "      --chat-id \"$TELEGRAM_INCOMING_CHAT_ID\" \\\n"
    "      --reply-to-message-id \"$TELEGRAM_INCOMING_MESSAGE_ID\" \\\n"
    "      --api-base \"${TELEGRAM_API_BASE:-https://api.telegram.org}\" \\\n"
    "      --task \"...\"\n"
)


def _stamp(error_code: str, message: str) -> None:
    sys.stderr.write(f"{error_code} {message}\n")
    sys.stderr.flush()


def resolve_skill_root_for(entry_file: str | os.PathLike[str]) -> Path:
    """Resolve the skill root for an entry point at ``<skill_root>/scripts/*.py``."""
    p = Path(entry_file).resolve()
    return p.parent.parent


def enforce_canonical_skill_path(entry_file: str | os.PathLike[str]) -> Path:
    """Validate the canonical skill path.

    Exits with ``EXIT_NON_CANONICAL_SKILL_PATH`` on violation. Returns the
    resolved skill root on success.
    """
    skill_root = resolve_skill_root_for(entry_file)

    if skill_root.name != CANONICAL_SKILL_NAME:
        _stamp(
            "RFO-NON-CANONICAL-SKILL-PATH",
            f"basename(skill_root)={skill_root.name!r} != "
            f"{CANONICAL_SKILL_NAME!r} (skill_root={skill_root})\n"
            f"{_CANONICAL_HINT}",
        )
        sys.exit(EXIT_NON_CANONICAL_SKILL_PATH)

    parent_name = skill_root.parent.name
    if parent_name not in ALLOWED_PARENT_DIR_NAMES:
        _stamp(
            "RFO-NON-CANONICAL-SKILL-PATH",
            f"parent of skill_root is {parent_name!r}; expected one of "
            f"{ALLOWED_PARENT_DIR_NAMES} (skill_root={skill_root})\n"
            f"{_CANONICAL_HINT}",
        )
        sys.exit(EXIT_NON_CANONICAL_SKILL_PATH)

    parts_lower = [p.lower() for p in skill_root.parts]
    for tok in FORBIDDEN_PATH_TOKENS:
        for part in parts_lower:
            if tok in part:
                _stamp(
                    "RFO-NON-CANONICAL-SKILL-PATH",
                    f"path segment {part!r} contains forbidden token "
                    f"{tok!r} (skill_root={skill_root})\n{_CANONICAL_HINT}",
                )
                sys.exit(EXIT_NON_CANONICAL_SKILL_PATH)

    return skill_root


def _extract_runs_root(argv: list[str]) -> str | None:
    for i, tok in enumerate(argv):
        if tok == "--runs-root" and i + 1 < len(argv):
            return argv[i + 1]
        if tok.startswith("--runs-root="):
            return tok.split("=", 1)[1]
    return None


def _allowed_runs_roots() -> list[Path]:
    home = Path.home()
    roots: list[Path] = [home / ".openclaw" / "workspace" / "rfo-runs"]
    extra = os.environ.get(RUNS_ROOT_ENV, "").strip()
    if extra:
        roots.append(Path(extra).expanduser())
    resolved: list[Path] = []
    for r in roots:
        try:
            resolved.append(r.expanduser().resolve(strict=False))
        except OSError:
            resolved.append(r)
    return resolved


def enforce_runs_root_argv(argv: list[str]) -> None:
    """Validate ``--runs-root`` taken from ``argv`` if present."""
    raw = _extract_runs_root(argv)
    if raw is None:
        return  # subcommand may not need --runs-root (e.g. failure)
    candidate = Path(raw).expanduser().resolve(strict=False)
    s = str(candidate)

    is_tmp = (
        s == "/tmp"
        or s.startswith("/tmp/")
        or s == "/var/tmp"
        or s.startswith("/var/tmp/")
    )
    if is_tmp:
        if os.environ.get(ALLOW_TMP_ENV) == "1":
            return
        _stamp(
            "RFO-RUNS-ROOT-FORBIDDEN",
            f"--runs-root={candidate} is inside /tmp without "
            f"{ALLOW_TMP_ENV}=1.\n"
            "Use ~/.openclaw/workspace/rfo-runs (default) or set "
            "RFO_RUNS_ROOT explicitly.",
        )
        sys.exit(EXIT_RUNS_ROOT_FORBIDDEN)

    allowed = _allowed_runs_roots()
    cand_str = str(candidate)
    for ok in allowed:
        ok_str = str(ok)
        if candidate == ok or cand_str == ok_str or cand_str.startswith(ok_str + os.sep):
            return

    _stamp(
        "RFO-RUNS-ROOT-FORBIDDEN",
        f"--runs-root={candidate} is not under any allowed root.\n"
        f"Allowed roots: {[str(p) for p in allowed]}\n"
        "Override with RFO_RUNS_ROOT=<absolute_path> for production "
        "or RFO_ALLOW_TMP_RUNS_ROOT=1 for smoke (consent).",
    )
    sys.exit(EXIT_RUNS_ROOT_FORBIDDEN)


__all__ = [
    "ALLOWED_PARENT_DIR_NAMES",
    "ALLOW_TMP_ENV",
    "CANONICAL_SKILL_NAME",
    "EXIT_NON_CANONICAL_SKILL_PATH",
    "EXIT_RUNS_ROOT_FORBIDDEN",
    "FORBIDDEN_PATH_TOKENS",
    "RUNS_ROOT_ENV",
    "enforce_canonical_skill_path",
    "enforce_runs_root_argv",
    "resolve_skill_root_for",
]
