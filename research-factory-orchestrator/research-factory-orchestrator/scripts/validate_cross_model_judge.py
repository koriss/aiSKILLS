#!/usr/bin/env python3
"""Cross-model judge ledger (FairJudge / IJCNLP-AACL-style debiasing fields)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", type=Path)
    args = ap.parse_args()
    rd = args.run_dir
    ledger = rd / "self-audit" / "cross-model-judge.json"
    if not ledger.exists():
        print(
            json.dumps(
                {
                    "status": "pass",
                    "validator": "validate_cross_model_judge",
                    "mode": "single-model-allowed",
                    "note": "judge ledger absent; no cross-model claim permitted",
                },
                ensure_ascii=False,
            )
        )
        return 0

    try:
        data = json.loads(ledger.read_text(encoding="utf-8"))
    except Exception as exc:
        print(json.dumps({"status": "fail", "validator": "validate_cross_model_judge", "reason": f"invalid_ledger:{exc}"}, ensure_ascii=False))
        return 1

    mode = str(data.get("mode") or "")
    if mode == "single-model-allowed":
        print(json.dumps({"status": "pass", "validator": "validate_cross_model_judge", "mode": mode}, ensure_ascii=False))
        return 0

    verdict = str(data.get("verdict") or "")
    if verdict not in {"agree", "disagree", "inconclusive"}:
        print(json.dumps({"status": "fail", "validator": "validate_cross_model_judge", "reason": "unexpected_verdict"}, ensure_ascii=False))
        return 1

    need = ("position_consistency", "repetition_stability", "preference_fairness", "judges", "swap_test_passed")
    miss = [k for k in need if k not in data]
    if miss:
        print(json.dumps({"status": "fail", "validator": "validate_cross_model_judge", "missing_fields": miss}, ensure_ascii=False))
        return 1
    if not isinstance(data.get("judges"), list) or len(data["judges"]) < 2:
        print(json.dumps({"status": "fail", "validator": "validate_cross_model_judge", "reason": "judges_must_be_multi"}, ensure_ascii=False))
        return 1
    for k in ("position_consistency", "repetition_stability", "preference_fairness"):
        v = data.get(k)
        if not isinstance(v, (int, float)) or not (0 <= float(v) <= 1):
            print(json.dumps({"status": "fail", "validator": "validate_cross_model_judge", "field": k, "reason": "expected_0_1"}, ensure_ascii=False))
            return 1
    if data.get("swap_test_passed") is not True:
        print(json.dumps({"status": "fail", "validator": "validate_cross_model_judge", "reason": "swap_test_required"}, ensure_ascii=False))
        return 1

    print(json.dumps({"status": "pass", "validator": "validate_cross_model_judge", "verdict": verdict, "mode": mode or "multi"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
