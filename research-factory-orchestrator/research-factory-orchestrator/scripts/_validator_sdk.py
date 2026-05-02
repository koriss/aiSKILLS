"""Compatibility shim: canonical validator helpers live in runtime.validator_sdk."""
from __future__ import annotations

from runtime.validator_sdk import Result, fail, load_json, ok, read_json

__all__ = ["Result", "fail", "load_json", "ok", "read_json"]
