#!/usr/bin/env python3
from pathlib import Path

p = Path('python/navixmind/tools/__init__.py')
text = p.read_text(encoding='utf-8')
anchor = 'from typing import Any, Dict\n'
if 'from pathlib import Path\n' not in text:
    if text.count(anchor) != 1:
        raise SystemExit('tools/__init__.py typing import anchor missing')
    text = text.replace(anchor, anchor + 'from pathlib import Path\n', 1)
p.write_text(text, encoding='utf-8')

# The real agent performs the execution-stage normalization with a context map;
# that second pass is where safe output filenames are synthesized. Make the
# regression test reproduce that exact stage instead of the parser-only pass.
p = Path('scripts/run_validate_iteration_v9.py')
text = p.read_text(encoding='utf-8')
old = "name, args, notes = normalize_tool_call('ffmpeg_process', {\n    'input_path': 'analysis_article.mp3',\n    'operation': 'speed',\n    'params': '1.5',\n})\n"
new = "name, args, notes = normalize_tool_call('ffmpeg_process', {\n    'input_path': 'analysis_article.mp3',\n    'operation': 'speed',\n    'params': '1.5',\n}, context={})\n"
if text.count(old) != 1:
    raise SystemExit('v9 validator speed normalization anchor missing')
p.write_text(text.replace(old, new, 1), encoding='utf-8')

print('Applied v9 generated-source/test fixups')
