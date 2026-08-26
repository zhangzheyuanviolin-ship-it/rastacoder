#!/usr/bin/env python3
"""Run the V9 core patch with an EOF-aware XLSX replacement.

The persisted V8 documents.py ends at modify_xlsx, so there is no following
section header that can serve as an end anchor. Keep every other reviewed V9
patch unchanged and replace only that one patch-script statement at runtime.
"""
from pathlib import Path

path = Path('scripts/apply_iteration_v9_core.py')
source = path.read_text(encoding='utf-8')
old = "replace_between('python/navixmind/tools/documents.py', 'def modify_xlsx(', '# ---------------------------------------------------------------------------\\n#', XLSX)"
new = '''_xlsx_path = Path('python/navixmind/tools/documents.py')
_xlsx_text = _xlsx_path.read_text(encoding='utf-8')
_xlsx_start = _xlsx_text.find('def modify_xlsx(')
if _xlsx_start < 0:
    raise SystemExit('documents.py: terminal modify_xlsx anchor missing')
_xlsx_path.write_text(_xlsx_text[:_xlsx_start] + XLSX.rstrip() + '\\n', encoding='utf-8')'''
if source.count(old) != 1:
    raise SystemExit(f'V9 core wrapper expected one terminal XLSX call, found {source.count(old)}')
source = source.replace(old, new, 1)
exec(compile(source, str(path), 'exec'), {'__name__': '__main__', '__file__': str(path)})
