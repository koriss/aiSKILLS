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
        "[2/3] Факты и проверки\n\nФактические утверждения выводятся карточками, без таблиц.\nЧувствительные контакты, адреса и raw-узлы в Telegram не выводятся.\n",
        "[3/3] Файлы\n\nfull-report.html — delivery manifest required\nresearch-package.zip — delivery manifest required\n"
    ]
    (root / "telegram").mkdir(exist_ok=True)
    for i, msg in enumerate(msgs, 1):
        (root / "telegram" / f"telegram-message-{i:03d}.txt").write_text(msg, encoding="utf-8")
    jwrite(root / "telegram" / "telegram-message-plan.json", {
        "plain_text_only": True,
        "no_tables": True,
        "no_local_paths": True,
        "messages": [f"telegram/telegram-message-{i:03d}.txt" for i in range(1, 4)]
    })
    print(root / "telegram")

if __name__ == "__main__":
    main()
