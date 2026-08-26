#!/usr/bin/env python3
"""Apply the reviewed v8 chat patch with two compile-safe corrections.

The original patch draft used the wrong MLC load-state enum name and wrapped
_RoleIndicator at the class-body level with an imbalanced parenthesis. This
wrapper keeps all reviewed chat/layout changes, skips only that bad wrapper,
then excludes the two decorative role-indicator usages from semantics.
"""
from pathlib import Path

script_path = Path('scripts/apply_iteration_v8_chat.py')
source = script_path.read_text(encoding='utf-8')

# Use the real enum declared by local_llm_service.dart.
source = source.replace('LocalModelLoadState', 'ModelLoadState')

# Skip only the two class-level ExcludeSemantics wrapping patches. Keep the
# following toolProgress switch cases so the new enum remains exhaustive.
bad_start_marker = '# Decorative role symbols such as ◆ must never be spoken.\n'
keep_from_marker = '# New role in role-indicator switches, though decorative indicator is normally\n'
bad_start = source.find(bad_start_marker)
keep_from = source.find(keep_from_marker, bad_start)
if bad_start < 0 or keep_from < 0:
    raise SystemExit(f'chat wrapper: decorative patch markers missing start={bad_start} keep={keep_from}')
source = source[:bad_start] + bad_start_marker + source[keep_from:]

exec(compile(source, str(script_path), 'exec'), {
    '__name__': '__main__',
    '__file__': str(script_path),
})

# Decorative ●/◆ role glyphs are visual-only. Exclude the two actual usages
# from the accessibility tree without changing _RoleIndicator's widget syntax.
bubble = Path('lib/features/chat/presentation/widgets/message_bubble.dart')
text = bubble.read_text(encoding='utf-8')
old = '_RoleIndicator(role: message.role),'
new = 'ExcludeSemantics(child: _RoleIndicator(role: message.role)),'
if text.count(old) != 2:
    raise SystemExit(f'chat wrapper: expected two role-indicator usages, found {text.count(old)}')
text = text.replace(old, new)
bubble.write_text(text, encoding='utf-8')

print('V8 chat wrapper applied with ModelLoadState and compile-safe decorative semantics')
