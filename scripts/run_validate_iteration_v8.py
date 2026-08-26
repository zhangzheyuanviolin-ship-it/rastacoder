#!/usr/bin/env python3
"""Run the v8 validator with the compile-safe role-indicator semantic check."""
from pathlib import Path

validator = Path('scripts/validate_iteration_v8.py')
source = validator.read_text(encoding='utf-8')
old = "require('return ExcludeSemantics(' in bubble, 'decorative role symbols can still be announced')"
new = "require('ExcludeSemantics(child: _RoleIndicator' in bubble, 'decorative role symbols can still be announced')"
if source.count(old) != 1:
    raise SystemExit(f'validator wrapper: expected one decorative semantic assertion, found {source.count(old)}')
source = source.replace(old, new, 1)
exec(compile(source, str(validator), 'exec'), {
    '__name__': '__main__',
    '__file__': str(validator.resolve()),
})
