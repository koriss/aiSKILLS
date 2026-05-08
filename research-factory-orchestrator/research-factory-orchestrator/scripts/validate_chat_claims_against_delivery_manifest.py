#!/usr/bin/env python3
from pathlib import Path
import argparse, json, re, sys

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from runtime.legacy_compat import read_fag_gates

DELIVERED_RE = re.compile(r"(отправлен|отправлено|доставлен|доставлено|прид[её]т в Telegram|sent to Telegram|HTML-отч[её]т.*отправлен|пакет.*отправлен|package.*sent)", re.I)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("path"); args=ap.parse_args()
    p=Path(args.path); errors=[]
    if p.is_dir():
        texts=[]
        for f in (p/"chat").glob("*.txt"):
            texts.append(f.read_text(encoding="utf-8", errors="replace"))
        text="\n".join(texts)
        delivery_path=p/"delivery-manifest.json"
        gate_path=p/"final-answer-gate.json"
        delivery=json.loads(delivery_path.read_text(encoding="utf-8")) if delivery_path.exists() else {}
        gate=json.loads(gate_path.read_text(encoding="utf-8")) if gate_path.exists() else {}
        _gm, _ = read_fag_gates(gate if isinstance(gate, dict) else {})
        user_gate = (_gm.get("final_user_claim_gate") or {}) if isinstance(_gm, dict) else {}
        external_gate = (_gm.get("external_delivery_gate") or {}) if isinstance(_gm, dict) else {}
        if DELIVERED_RE.search(text):
            if user_gate.get("status")!="pass" or external_gate.get("status")!="pass":
                errors.append("chat claims delivery, but final_user_claim_gate/external_delivery_gate is not pass")
        # Even without delivered text, manifest must not allow delivery claim unless final_user pass.
        if delivery.get("delivery_claim_allowed") and user_gate.get("status")!="pass":
            errors.append("delivery-manifest allows delivery claim while final_user_claim_gate is not pass")
    else:
        text=p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""
        if DELIVERED_RE.search(text):
            errors.append("standalone chat/log claims delivery but no delivery-manifest/final-answer-gate provided")
    print(json.dumps({"status":"pass" if not errors else "fail","errors":errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1
if __name__=="__main__":
    raise SystemExit(main())
