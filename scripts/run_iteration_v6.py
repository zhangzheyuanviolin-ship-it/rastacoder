#!/usr/bin/env python3
"""Execute apply_iteration_v6.py after repairing embedded regex delimiters.

The initial v6 patcher embeds the generated compat.py in a raw triple-single-
quoted string. A handful of regex literals inside that generated module also
used triple-single quotes, prematurely terminating the outer literal. This
runner rewrites only that bounded regex-helper section to triple-double quoted
regex literals, compiles the repaired patcher, then executes it.

Release/validation workflows call this runner so the transformation is
reproducible from the committed v6 branch.
"""
from pathlib import Path

p = Path(__file__).with_name('apply_iteration_v6.py')
source = p.read_text(encoding='utf-8')
start = source.index('def _extract_file_tokens(text: str)')
end = source.index('def _extension(path: Any)', start)
segment = source[start:end]
count_open = segment.count("r'''")
count_close = segment.count("'''")
if count_open != 5 or count_close != 5:
    raise SystemExit(
        f'Unexpected embedded regex delimiter count: raw-open={count_open}, close={count_close}'
    )
segment = segment.replace("r'''", 'r"""').replace("'''", '"""')
repaired = source[:start] + segment + source[end:]
compile(repaired, str(p), 'exec')
namespace = {'__name__': '__main__', '__file__': str(p)}
exec(compile(repaired, str(p), 'exec'), namespace, namespace)
