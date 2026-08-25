#!/usr/bin/env python3
"""Apply the v6 third-pass reliability patch from its immutable source commit.

The original large patch source is retained in Git commit
b51c293bf33084e779618e3706122d5ae0489b64. One generated regex literal reused
the outer triple-single-quote delimiter. This small deterministic runner reads
that exact historical source, changes only the conflicting literal, compiles the
repaired patcher, and executes it. Keeping the historical source immutable makes
CI replay auditable without duplicating a very large payload.
"""
from pathlib import Path
import subprocess

SOURCE_COMMIT = 'b51c293bf33084e779618e3706122d5ae0489b64'
SOURCE_PATH = 'scripts/apply_iteration_v6_reliability3.py'

source = subprocess.check_output(
    ['git', 'show', f'{SOURCE_COMMIT}:{SOURCE_PATH}'],
    text=True,
)
bad = "r'''\\s*[\"']?'''"
good = 'r"\\s*[\\"' + chr(39) + ']?"'
count = source.count(bad)
if count != 1:
    raise SystemExit(
        f'Expected exactly one embedded reliability3 regex delimiter conflict, found {count}'
    )
repaired = source.replace(bad, good, 1)
compile(repaired, SOURCE_PATH, 'exec')
namespace = {'__name__': '__main__', '__file__': str(Path(SOURCE_PATH))}
exec(compile(repaired, SOURCE_PATH, 'exec'), namespace, namespace)
