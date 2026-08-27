#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / 'python/navixmind/tools/__init__.py'
text = TOOLS.read_text(encoding='utf-8')

if '\nimport os\n' not in text[:500]:
    anchor = 'import copy\n'
    if text.count(anchor) != 1:
        raise SystemExit(f'Expected one import-copy anchor, found {text.count(anchor)}')
    text = text.replace(anchor, anchor + 'import os\n', 1)

if '\nimport os\n' not in text[:500]:
    raise SystemExit('Global os import required by V17 trusted path executor is missing')

TOOLS.write_text(text, encoding='utf-8')
print('Added V17 trusted-path os import guard')
