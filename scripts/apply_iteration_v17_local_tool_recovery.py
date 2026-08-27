#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPAT = ROOT / 'python/navixmind/tools/compat.py'

text = COMPAT.read_text(encoding='utf-8')

old = '''        workspace_aliases = {"", ".", "./", "output", "output/", "workspace", "workspace/", "/output", "/output/", "/workspace", "/workspace/"}'''
new = '''        # RASTACODER_V17_LOCAL_ROOT_ALIAS_RECOVERY
        # Qwen3-4B may express the logical workspace root as '/'. Repair it at
        # the model ABI boundary so diagnostics and downstream tools see '.'.
        # The central path contract independently carries the same invariant.
        workspace_aliases = {"", ".", "./", "/", "output", "output/", "workspace", "workspace/", "/output", "/output/", "/workspace", "/workspace/"}'''

if new not in text:
    if text.count(old) != 1:
        raise SystemExit(f'Expected exactly one V12 workspace_aliases block, found {text.count(old)}')
    text = text.replace(old, new, 1)

# Guard against an accidental future edit which restores the V16 failure.
required = [
    'RASTACODER_V17_LOCAL_ROOT_ALIAS_RECOVERY',
    'workspace_aliases = {"", ".", "./", "/",',
    'list_files:virtual_workspace_alias:{path_text}->.',
]
for marker in required:
    if marker not in text:
        raise SystemExit(f'Missing V17 compatibility invariant: {marker}')

COMPAT.write_text(text, encoding='utf-8')
print('Applied V17 local-model root alias recovery to compat.py')
