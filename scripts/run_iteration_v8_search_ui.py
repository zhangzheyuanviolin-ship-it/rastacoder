#!/usr/bin/env python3
"""Apply v8 search UI patches with a structural final-list replacement."""
from pathlib import Path

script_path = Path('scripts/apply_iteration_v8_search_ui.py')
source = script_path.read_text(encoding='utf-8')
cut_marker = '# Replace inline switch construction with reusable tile that includes key control.\n'
cut = source.find(cut_marker)
if cut < 0:
    raise SystemExit('search UI wrapper: cut marker missing')
exec(compile(source[:cut], str(script_path), 'exec'), {'__name__': '__main__', '__file__': str(script_path)})

path = Path('lib/features/settings/tool_skills_screen.dart')
text = path.read_text(encoding='utf-8')
start_marker = '                  for (final skill in LocalToolSkillCatalog.inCategory(category))\n'
end_marker = '                const SizedBox(height: 24),\n'
start = text.find(start_marker)
end = text.find(end_marker, start)
if start < 0 or end < 0:
    raise SystemExit(f'search UI wrapper: structural skill-list anchors missing start={start} end={end}')
replacement = (
    "                  for (final skill in LocalToolSkillCatalog.inCategory(category))\n"
    "                    _buildSkillTile(context, skill),\n"
    "                ],\n"
)
# The old block ends with the category collection close `],` immediately before
# the final bottom spacer. Replace the whole per-skill body and preserve spacer.
path.write_text(text[:start] + replacement + text[end:], encoding='utf-8')
print('V8 search UI structural patch applied successfully')
