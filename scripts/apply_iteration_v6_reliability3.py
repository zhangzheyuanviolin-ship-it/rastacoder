#!/usr/bin/env python3
"""Apply the v6 third-pass reliability patch from its immutable source commit.

The original large patch source is retained in Git commit
b51c293bf33084e779618e3706122d5ae0489b64. This deterministic runner repairs
two patch-source-only issues before execution: one nested regex delimiter and
one deliberately non-unique free-form-loop anchor which must modify only its
first occurrence. All other replace_once anchors remain strict.
"""
from pathlib import Path
import subprocess

SOURCE_COMMIT = 'b51c293bf33084e779618e3706122d5ae0489b64'
SOURCE_PATH = 'scripts/apply_iteration_v6_reliability3.py'

source = subprocess.check_output(
    ['git', 'show', f'{SOURCE_COMMIT}:{SOURCE_PATH}'],
    text=True,
)

# Repair only the embedded generated-regex delimiter conflict.
bad = "r'''\\s*[\"']?'''"
good = 'r"\\s*[\\"' + chr(39) + ']?"'
count = source.count(bad)
if count != 1:
    raise SystemExit(
        f'Expected exactly one embedded reliability3 regex delimiter conflict, found {count}'
    )
source = source.replace(bad, good, 1)

# The free-form key loop exists both in _freeform() and in final generic-key
# cleanup. The first reliability3 edit intentionally targets only _freeform().
strict_helper = '''def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)
'''
scoped_helper = '''def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if label == "freeform query carrier":
        if count < 1:
            raise SystemExit(f"{label}: expected at least one anchor, found {count}")
        return text.replace(old, new, 1)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)
'''
if source.count(strict_helper) != 1:
    raise SystemExit('Unexpected reliability3 replace_once helper source')
source = source.replace(strict_helper, scoped_helper, 1)

compile(source, SOURCE_PATH, 'exec')
namespace = {'__name__': '__main__', '__file__': str(Path(SOURCE_PATH))}
exec(compile(source, SOURCE_PATH, 'exec'), namespace, namespace)
