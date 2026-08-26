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
print('Applied v9 generated-source fixups')
