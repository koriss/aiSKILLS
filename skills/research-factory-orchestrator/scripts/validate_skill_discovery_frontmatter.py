#!/usr/bin/env python3
from pathlib import Path
import json, re, sys
root=Path(__file__).resolve().parents[1]
skill=root/'SKILL.md'
text=skill.read_text(encoding='utf-8') if skill.exists() else ''
errors=[]
if not text.startswith('---'):
    errors.append('missing_yaml_frontmatter')
else:
    parts=text.split('---',2)
    fm=parts[1] if len(parts)>=3 else ''
    if not re.search(r'(?m)^name:\s*research_factory_orchestrator\s*$', fm): errors.append('missing_name_research_factory_orchestrator')
    if not re.search(r'(?m)^metadata:\s*$', fm): errors.append('missing_metadata')
    if '18.3.2-delivery-truth-smoke-runtime-contract-hotfix' not in fm: errors.append('wrong_or_missing_metadata_version_v18_3_2')
out={'status':'fail' if errors else 'pass','validator':'validate_skill_discovery_frontmatter','version':'18.3.2-delivery-truth-smoke-runtime-contract-hotfix','errors':errors}
print(json.dumps(out,ensure_ascii=False,indent=2)); sys.exit(1 if errors else 0)
