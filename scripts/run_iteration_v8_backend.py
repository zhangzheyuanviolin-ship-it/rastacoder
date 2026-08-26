#!/usr/bin/env python3
"""Run the v8 backend patch with the search-schema anchor narrowed uniquely."""
from pathlib import Path

path = Path('scripts/apply_iteration_v8_backend.py')
source = path.read_text(encoding='utf-8')
old = '''patch(
    'python/navixmind/tools/__init__.py',
    "\\n\\n# RASTACODER_V7_COMPLETE_SKILLS\\n",
    search_schema_block + "\\n\\n# RASTACODER_V7_COMPLETE_SKILLS\\n",
)
'''
new = '''patch(
    'python/navixmind/tools/__init__.py',
    "\\n\\n# RASTACODER_V7_COMPLETE_SKILLS\\n# Every structured v7 utility is available to the local model when its Skill is\\n",
    search_schema_block + "\\n\\n# RASTACODER_V7_COMPLETE_SKILLS\\n# Every structured v7 utility is available to the local model when its Skill is\\n",
)
'''
if source.count(old) != 1:
    raise SystemExit(f'backend wrapper: expected one broad schema insertion block, found {source.count(old)}')
source = source.replace(old, new, 1)
exec(compile(source, str(path), 'exec'), {'__name__': '__main__', '__file__': str(path)})
