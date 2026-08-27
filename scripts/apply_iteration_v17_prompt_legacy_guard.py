#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / 'python/navixmind/tools/__init__.py'
text = TOOLS.read_text(encoding='utf-8')

legacy = 'Do not invent Linux roots such as /workspace or /output.'
if legacy not in text:
    anchor = '''        "- WORKSPACE PATH RULE: use path='.' for the workspace root and relative paths like folder/file.txt below it. Never use bare '/' or Linux-style absolute roots; the app owns the real Android paths.",'''
    replacement = anchor + '''\n        "- Do not invent Linux roots such as /workspace or /output. Bare '/' is also forbidden in model-facing calls and is repaired to the workspace by the runtime.",'''
    if text.count(anchor) != 1:
        raise SystemExit(f'V17 enhanced workspace prompt anchor count={text.count(anchor)}')
    text = text.replace(anchor, replacement, 1)

if legacy not in text:
    raise SystemExit('Inherited V12 workspace prompt contract was not preserved')
if 'OUTPUT PATH RULE:' not in text:
    raise SystemExit('V17 output path rule disappeared')

TOOLS.write_text(text, encoding='utf-8')
print('Preserved inherited V12 prompt wording alongside V17 stronger local path rules')
