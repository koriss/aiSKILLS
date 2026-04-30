#!/usr/bin/env python3
from pathlib import Path
import argparse, json

def block_to_text(block, seq, total):
    title = block.get("title", block.get("type", "Message"))
    body = block.get("text", "")
    return f"[{seq}/{total}] {title}\n\n{body}".strip() + "\n"

def split_long_text(title, text, limit):
    lines = text.splitlines()
    chunks, cur = [], []
    for line in lines:
        candidate = "\n".join(cur + [line])
        if len(candidate) > limit and cur:
            chunks.append("\n".join(cur))
            cur = [line]
        else:
            cur.append(line)
    if cur:
        chunks.append("\n".join(cur))
    return [{"title": title, "text": c} for c in chunks]

def item_text(x):
    return x.get("text", str(x)) if isinstance(x, dict) else str(x)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary-json", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--limit", type=int, default=3200)
    args = ap.parse_args()

    data = json.loads(Path(args.summary_json).read_text(encoding="utf-8"))
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    blocks = []
    blocks.append({"type": "verdict", "title": "🦊 Исследование: " + data.get("title", ""), "text": data.get("verdict", "")})
    if data.get("key_findings"):
        blocks.append({"type": "key_findings", "title": "Ключевые выводы", "text": "\n".join(f"{i+1}. {item_text(x)}" for i, x in enumerate(data["key_findings"]))})
    if data.get("fact_cards"):
        blocks.append({"type": "facts", "title": "Факты и цифры", "text": "\n\n".join(item_text(x) for x in data["fact_cards"])})
    if data.get("gaps") or data.get("warnings"):
        items = []
        for x in data.get("warnings", []): items.append("⚠️ " + item_text(x))
        for x in data.get("gaps", []): items.append("— " + item_text(x))
        blocks.append({"type": "gaps", "title": "Ограничения и пробелы", "text": "\n".join(items)})
    if data.get("top_sources"):
        def label(x):
            return x.get("label", str(x)) if isinstance(x, dict) else str(x)
        blocks.append({"type": "sources", "title": "Главные источники", "text": "\n".join(f"[{i+1}] {label(x)}" for i, x in enumerate(data["top_sources"][:8]))})
    blocks.append({"type": "files", "title": "Файлы", "text": "📎 full-report.html — полный standalone HTML-отчёт.\n📎 research-package.zip — proof package."})

    expanded = []
    for b in blocks:
        if len(b["text"]) > args.limit:
            expanded.extend(split_long_text(b["title"], b["text"], args.limit))
        else:
            expanded.append(b)

    total = len(expanded)
    messages = []
    for i, b in enumerate(expanded, 1):
        text = block_to_text(b, i, total)
        path = out / f"telegram-message-{i:03d}.txt"
        path.write_text(text, encoding="utf-8")
        messages.append({"message_id": path.stem, "sequence": i, "total": total, "block_type": b.get("type", "block"), "path": str(path), "char_count": len(text)})

    plan = {"plain_text_only": True, "no_large_tables": True, "messages": messages}
    (out / "telegram-message-plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(plan, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
