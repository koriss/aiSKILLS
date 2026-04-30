#!/usr/bin/env python3
from pathlib import Path
import argparse, json, re, sys
from html.parser import HTMLParser

BAD_TAGS = {"tdtd", "thth", "trtr", "bodybody", "htmlhtml"}

class Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.errors = []
        self.tags = []
        self.script_ids = []
        self.json_scripts = []
        self.in_json_script = None
        self.buf = []
    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        self.tags.append(tag)
        if tag in BAD_TAGS:
            self.errors.append(f"invalid-looking tag <{tag}>")
        attrs = dict(attrs)
        if tag == "script" and attrs.get("type") == "application/json":
            sid = attrs.get("id")
            if not sid:
                self.errors.append("json script without id")
            self.script_ids.append(sid)
            self.in_json_script = sid
            self.buf = []
    def handle_data(self, data):
        if self.in_json_script:
            self.buf.append(data)
    def handle_endtag(self, tag):
        if tag.lower() == "script" and self.in_json_script:
            self.json_scripts.append((self.in_json_script, "".join(self.buf).strip()))
            self.in_json_script = None
            self.buf = []

def resolve_html_path(path):
    p = Path(path)
    if p.is_dir():
        p = p / "report" / "full-report.html"
    return p

def validate(path):
    p = resolve_html_path(path)
    if not p.exists():
        return [f"html missing: {p}"]
    text = p.read_text(encoding="utf-8", errors="replace")
    errors = []
    if "<html" not in text.lower() or "</html>" not in text.lower():
        errors.append("missing html root tags")
    if "<body" not in text.lower() or "</body>" not in text.lower():
        errors.append("missing body tags")
    if re.search(r"<\s*tdtd\b", text, re.I):
        errors.append("malformed <tdtd> tag")
    if re.search(r"<\s*td\s*td\b", text, re.I):
        errors.append("malformed <td td> tag")
    parser = Parser()
    try:
        parser.feed(text)
        parser.close()
    except Exception as e:
        errors.append(f"html parser error: {type(e).__name__}: {e}")
    errors.extend(parser.errors)
    ids = [x for x in parser.script_ids if x]
    dupes = sorted({x for x in ids if ids.count(x) > 1})
    if dupes:
        errors.append("duplicate json script ids: " + ", ".join(dupes))
    for sid, raw in parser.json_scripts:
        if not raw:
            errors.append(f"empty json script block: {sid}")
            continue
        try:
            json.loads(raw)
        except Exception as e:
            errors.append(f"invalid json script block {sid}: {e}")
    return errors

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    args = ap.parse_args()
    errors = validate(args.path)
    if errors:
        print(json.dumps({"status":"fail","errors":errors}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps({"status":"pass"}, ensure_ascii=False, indent=2))
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
