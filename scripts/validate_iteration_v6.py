#!/usr/bin/env python3
"""Run the established v6 validator with its parser-source assertion updated.

The full original validator is retained in commit
d7e09da6f5e288ef71bb3c8ffde34d755796f5e3. Reliability3 intentionally changed
`canonical, args, _` to `canonical, args, parser_repairs` so the raw-vs-repaired
diagnostic log can explain exactly what the parser changed. This wrapper updates
only that stale source-string assertion; all behavioral tests remain intact.
"""
import subprocess

SOURCE_COMMIT = 'd7e09da6f5e288ef71bb3c8ffde34d755796f5e3'
SOURCE_PATH = 'scripts/validate_iteration_v6.py'
source = subprocess.check_output(
    ['git', 'show', f'{SOURCE_COMMIT}:{SOURCE_PATH}'],
    text=True,
)
old = '''expect("canonical, args, _ = normalize_tool_call(name, args)" in agent_text, 'agent parser does not normalize arguments before canonical-name validation')'''
new = '''expect(
    "canonical, args, _ = normalize_tool_call(name, args)" in agent_text
    or "canonical, args, parser_repairs = normalize_tool_call(name, raw_args)" in agent_text,
    'agent parser does not normalize arguments before canonical-name validation',
)'''
if source.count(old) != 1:
    raise SystemExit('Unexpected v6 validator parser assertion source')
source = source.replace(old, new, 1)
compile(source, SOURCE_PATH, 'exec')
namespace = {'__name__': '__main__', '__file__': SOURCE_PATH}
exec(compile(source, SOURCE_PATH, 'exec'), namespace, namespace)
