#!/usr/bin/env python3
from pathlib import Path
import argparse, json
from common_runtime import jwrite

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    args = ap.parse_args()
    root = Path(args.run_dir)
    run = json.loads((root / "run.json").read_text(encoding="utf-8"))
    msgs = [
        f"[1/3] Сопроводительная аналитическая записка\n\nТема:\n{run.get('topic')}\n\nСтатус:\n{run.get('status')}\n\nДальше:\nфакты, источники, файлы.\n",
        "[2/3] Факты и проверки\n\nФактические утверждения выводятся карточками, без таблиц.\nЧувствительные контакты, адреса и raw-узлы в user-visible plain text не выводятся.\n",
        "[3/3] Файлы\n\nfull-report.html — delivery manifest required\nresearch-package.zip — delivery manifest required\n"
    ]
    out_dir = root / "plain-text"
    out_dir.mkdir(exist_ok=True)
    for i, msg in enumerate(msgs, 1):
        (out_dir / f"plain-text-message-{i:03d}.txt").write_text(msg, encoding="utf-8")
    jwrite(out_dir / "plain-text-message-plan.json", {
        "plain_text_only": True,
        "no_tables": True,
        "no_local_paths": True,
        "messages": [f"plain-text/plain-text-message-{i:03d}.txt" for i in range(1, 4)]
    })
    print(out_dir)

if __name__ == "__main__":
    main()
