#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--contracts", required=True)
    ap.add_argument("--ledger", required=True)
    args = ap.parse_args()
    contracts_raw = json.loads(Path(args.contracts).read_text(encoding="utf-8"))
    contracts = contracts_raw.get("contracts", contracts_raw if isinstance(contracts_raw, list) else [])
    contract_by_id = {c.get("work_unit_id"): c for c in contracts}
    ledger = json.loads(Path(args.ledger).read_text(encoding="utf-8"))
    errors = []
    for s in ledger.get("shards", []):
        wid = s.get("work_unit_id")
        c = contract_by_id.get(wid)
        if not c:
            errors.append(f"ledger shard has no contract: {wid}")
            continue
        closed = set(s.get("coverage_closed", []))
        required = set(c.get("coverage_categories", []))
        missing = required - closed
        if s.get("status") == "complete" and missing:
            errors.append(f"{wid}: complete but missing coverage categories: {sorted(missing)}")
        if s.get("scope_reduced") is True:
            errors.append(f"{wid}: scope_reduced=true")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: no shard scope reduction")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
