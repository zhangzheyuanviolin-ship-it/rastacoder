#!/usr/bin/env python3
"""Execute apply_iteration_v6_reliability3.py after one bounded delimiter repair.

The patcher embeds generated compat.py inside a raw triple-single-quoted string.
One regex inside that generated block accidentally reused triple-single quotes.
This runner changes only that exact regex literal to a normal double-quoted
Python regex, compiles the repaired patcher, and executes it deterministically.
"""
from pathlib import Path

p = Path(__file__).with_name('apply_iteration_v6_reliability3.py')
source = p.read_text(encoding='utf-8')
bad = "r'''\\s*[\"']?'''"
good = '"\\\\s*[\\\\\"\']?"'
count = source.count(bad)
if count != 1:
    raise SystemExit(f'Expected exactly one embedded reliability3 regex delimiter conflict, found {count}')
repaired = source.replace(bad, good, 1)
compile(repaired, str(p), 'exec')
namespace = {'__name__': '__main__', '__file__': str(p)}
exec(compile(repaired, str(p), 'exec'), namespace, namespace)
