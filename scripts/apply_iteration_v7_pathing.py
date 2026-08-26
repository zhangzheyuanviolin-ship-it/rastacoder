#!/usr/bin/env python3
from pathlib import Path

p = Path('python/navixmind/tools/__init__.py')
text = p.read_text()
old = "    path_keys = ['image_path', 'input_path', 'pdf_path', 'file_path', 'path', 'docx_path', 'pptx_path', 'xlsx_path']\n"
new = "    path_keys = ['image_path', 'input_path', 'pdf_path', 'file_path', 'path', 'source_path', 'zip_path', 'docx_path', 'pptx_path', 'xlsx_path']\n"
if old not in text:
    raise SystemExit('v7 pathing anchor missing: path_keys')
text = text.replace(old, new, 1)

anchor = '''            args[key] = resolved\n\n\ndef _resolve_output_paths'''
addition = '''            args[key] = resolved\n\n    # Office modification operations may carry attached image/file paths one\n    # level deeper under operations[*].params. Resolve those basenames too.\n    operations = args.get('operations')\n    if isinstance(operations, list):\n        for op in operations:\n            if not isinstance(op, dict):\n                continue\n            params = op.get('params')\n            if not isinstance(params, dict):\n                continue\n            for nested_key in ('image_path', 'file_path', 'source_path', 'input_path'):\n                value = params.get(nested_key)\n                if not isinstance(value, str):\n                    continue\n                if value in file_map:\n                    params[nested_key] = file_map[value]\n                elif os.path.basename(value) in file_map:\n                    params[nested_key] = file_map[os.path.basename(value)]\n\n\ndef _resolve_output_paths'''
if anchor not in text:
    raise SystemExit('v7 pathing anchor missing: nested operations')
text = text.replace(anchor, addition, 1)
p.write_text(text)
print('Applied v7 attachment/path resolution extensions')
