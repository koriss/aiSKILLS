#!/usr/bin/env python3
"""Query the propaganda methods knowledge base."""
import json
import sys

KB_PATH = 'reports/propaganda-books-processed/PROPAGANDA_METHODS_v2.json'

def load():
    return json.load(open(KB_PATH))

def find(keyword, limit=20):
    """Find methods matching keyword in name, definition, context."""
    keyword = keyword.lower()
    results = []
    for m in load():
        text = ' '.join([
            m.get('name_ru', ''),
            m.get('name_en', ''),
            m.get('definition', ''),
            m.get('mechanism', ''),
            m.get('context', ''),
            ' '.join(m.get('examples', []))
        ]).lower()
        if keyword in text:
            results.append(m)
    return results[:limit]

def by_source(source_name, limit=50):
    """Find all methods from a specific source."""
    results = []
    for m in load():
        src = m.get('source', '').lower()
        if source_name.lower() in src:
            results.append(m)
    return results[:limit]

def by_id(method_id):
    """Get method by ID."""
    for m in load():
        if m['method_id'] == method_id:
            return m
    return None

def categories():
    """List all sources."""
    sources = {}
    for m in load():
        src = m['source'].split(',')[0].strip()
        sources[src] = sources.get(src, 0) + 1
    return sorted(sources.items(), key=lambda x: -x[1])

def all_methods(limit=20):
    """List all methods."""
    return load()[:limit]

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'help'
    args = sys.argv[2:]
    
    if cmd == 'find' and args:
        for m in find(args[0]):
            print(f"[{m['method_id']}] {m['name_ru']} / {m.get('name_en','')}")
            print(f"  source: {m['source']}")
            print(f"  def: {m['definition'][:150]}...")
            print()
    elif cmd == 'id' and args:
        m = by_id(args[0])
        if m:
            print(json.dumps(m, ensure_ascii=False, indent=2))
        else:
            print(f"Method {args[0]} not found")
    elif cmd == 'source' and args:
        for m in by_source(args[0]):
            print(f"[{m['method_id']}] {m['name_ru']}")
    elif cmd == 'categories':
        for src, cnt in categories():
            print(f"  {cnt:3d}  {src}")
    elif cmd == 'all':
        for m in all_methods():
            print(f"[{m['method_id']}] {m['name_ru']}")
    elif cmd == 'count':
        print(f"Total methods: {len(load())}")
    else:
        print("Usage:")
        print("  find <keyword>     — search methods by keyword")
        print("  id <method_id>     — get method by ID")
        print("  source <name>      — methods from source")
        print("  categories         — list all sources")
        print("  all                — list all methods")
        print("  count              — total count")
        print()
        print(f"Knowledge base: {KB_PATH}")
