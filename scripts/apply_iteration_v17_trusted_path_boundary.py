#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / 'python/navixmind/tools/__init__.py'
EXTENDED = ROOT / 'python/navixmind/tools/extended_tools.py'


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly one source block, found {count}')
    return text.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Shared executor: distinguish application-trusted attachment paths from path
# strings invented by a 3B-4B model. This closes the whole /etc, /data, /system,
# /foo family rather than special-casing only list_files('/').
# ---------------------------------------------------------------------------
tools = TOOLS.read_text(encoding='utf-8')

old = '''    # Resolve file paths: if a tool arg is a basename that matches an attached file,
    # replace it with the full path so native tools can find the file
    file_map = context.get('_file_map', {})
    if file_map:
        _resolve_file_paths(args, file_map)

    # Resolve every model-facing relative file path against the same workspace root.
    output_dir = context.get('output_dir')'''
new = '''    # RASTACODER_V17_EXPLICIT_TRUSTED_ATTACHMENT_PATHS
    # Resolve attachment basenames first, then carry the exact application-owned
    # absolute paths as a whitelist into the strict model-facing path resolver.
    # A model merely spelling an existing Android/Linux path never makes it trusted.
    file_map = context.get('_file_map', {})
    trusted_paths = {
        os.path.normpath(str(value))
        for value in (file_map.values() if isinstance(file_map, dict) else [])
        if isinstance(value, str) and value.strip() and os.path.isabs(value)
    }
    if file_map:
        _resolve_file_paths(args, file_map)

    # Resolve every model-facing relative file path against the same workspace root.
    output_dir = context.get('output_dir')'''
tools = replace_once(tools, old, new, 'trusted attachment collection')

old = '''        if tool_name != 'list_files':
            _resolve_workspace_input_paths(args, output_dir)
        _resolve_output_paths(args, output_dir)'''
new = '''        if tool_name != 'list_files':
            _resolve_workspace_input_paths(args, output_dir, trusted_paths=trusted_paths)
        _resolve_output_paths(args, output_dir)'''
tools = replace_once(tools, old, new, 'strict central input resolver call')

old = '''    if tool_name in {"list_files", "file_manage", "extract_zip", "pdf_manage", "download_media"} and output_dir:
        args["_output_dir"] = output_dir'''
new = '''    if tool_name in {"list_files", "file_manage", "extract_zip", "pdf_manage", "download_media"} and output_dir:
        args["_output_dir"] = output_dir
    if tool_name == "file_manage":
        # file_manage has its own lower-level resolver, so propagate the same
        # exact attachment whitelist through that second boundary.
        args["_trusted_paths"] = sorted(trusted_paths)'''
tools = replace_once(tools, old, new, 'file_manage trust propagation')

old = '''def _workspace_relative_path(value: str, output_dir: str) -> str:
    return resolve_model_path(value, output_dir, allow_android_roots=True)


def _resolve_workspace_input_paths(args: Dict[str, Any], output_dir: str) -> None:
    # RASTACODER_V17_ALL_LOCAL_PATH_BOUNDARY
    path_keys = [
        'image_path', 'input_path', 'pdf_path', 'file_path', 'path', 'source_path',
        'destination_path', 'zip_path', 'docx_path', 'pptx_path', 'xlsx_path',
    ]
    for key in path_keys:
        value = args.get(key)
        if isinstance(value, str):
            args[key] = _workspace_relative_path(value, output_dir)
    for key in ('image_paths', 'file_paths', 'input_paths'):
        values = args.get(key)
        if isinstance(values, list):
            args[key] = [
                _workspace_relative_path(v, output_dir) if isinstance(v, str) else v
                for v in values
            ]
    operations = args.get('operations')
    if isinstance(operations, list):
        for op in operations:
            if not isinstance(op, dict) or not isinstance(op.get('params'), dict):
                continue
            params = op['params']
            for key in ('image_path', 'file_path', 'source_path', 'input_path'):
                if isinstance(params.get(key), str):
                    params[key] = _workspace_relative_path(params[key], output_dir)'''
new = '''# RASTACODER_V17_STRICT_MODEL_PATH_RESOLUTION
def _workspace_relative_path(value: str, output_dir: str, trusted_paths=None) -> str:
    return resolve_model_path(
        value,
        output_dir,
        allow_android_roots=True,
        trusted_absolute_paths=trusted_paths or (),
        trust_existing_files=False,
    )


def _resolve_workspace_input_paths(args: Dict[str, Any], output_dir: str, trusted_paths=None) -> None:
    # RASTACODER_V17_ALL_LOCAL_PATH_BOUNDARY
    # destination_path is deliberately excluded here: it is an output path and
    # must never inherit trust merely because it equals an attached input file.
    path_keys = [
        'image_path', 'input_path', 'pdf_path', 'file_path', 'path', 'source_path',
        'zip_path', 'docx_path', 'pptx_path', 'xlsx_path',
    ]
    for key in path_keys:
        value = args.get(key)
        if isinstance(value, str):
            args[key] = _workspace_relative_path(value, output_dir, trusted_paths)
    for key in ('image_paths', 'file_paths', 'input_paths'):
        values = args.get(key)
        if isinstance(values, list):
            args[key] = [
                _workspace_relative_path(v, output_dir, trusted_paths) if isinstance(v, str) else v
                for v in values
            ]
    operations = args.get('operations')
    if isinstance(operations, list):
        for op in operations:
            if not isinstance(op, dict) or not isinstance(op.get('params'), dict):
                continue
            params = op['params']
            for key in ('image_path', 'file_path', 'source_path', 'input_path'):
                if isinstance(params.get(key), str):
                    params[key] = _workspace_relative_path(params[key], output_dir, trusted_paths)'''
tools = replace_once(tools, old, new, 'strict shared path functions')

old = '''    # RASTACODER_V17_OUTPUT_DIRECTORY_BOUNDARY
    # extract_zip uses output_dir while all other producers use output_path.
    for key in ('output_path', 'output_dir'):
        value = args.get(key)
        if isinstance(value, str):
            args[key] = resolve_output_path(value, output_dir)'''
new = '''    # RASTACODER_V17_OUTPUT_DIRECTORY_BOUNDARY
    # Outputs are always workspace-owned. extract_zip uses output_dir and
    # file_manage uses destination_path, so both belong to this strict branch.
    for key in ('output_path', 'output_dir', 'destination_path'):
        value = args.get(key)
        if isinstance(value, str):
            args[key] = resolve_output_path(value, output_dir)'''
tools = replace_once(tools, old, new, 'strict output/destination resolver')

for marker in (
    'RASTACODER_V17_EXPLICIT_TRUSTED_ATTACHMENT_PATHS',
    'RASTACODER_V17_STRICT_MODEL_PATH_RESOLUTION',
    "for key in ('output_path', 'output_dir', 'destination_path'):",
    'args["_trusted_paths"] = sorted(trusted_paths)',
):
    if marker not in tools:
        raise SystemExit(f'Missing trusted-path executor invariant: {marker}')
TOOLS.write_text(tools, encoding='utf-8')


# ---------------------------------------------------------------------------
# file_manage has a second path resolver inside extended_tools. Make it consume
# the exact same attachment whitelist so the central fix cannot be undone one
# function deeper in the call stack.
# ---------------------------------------------------------------------------
extended = EXTENDED.read_text(encoding='utf-8')

old = '''def _resolve_workspace_path(value: str, _output_dir: Optional[str]) -> str:
    """Resolve through the same central model-facing path contract as execute_tool."""
    root = os.path.normpath(_default_output_dir(_output_dir))
    return resolve_model_path(value, root, allow_android_roots=True)'''
new = '''def _resolve_workspace_path(value: str, _output_dir: Optional[str], _trusted_paths=None) -> str:
    """Resolve through the strict central model-facing path contract."""
    root = os.path.normpath(_default_output_dir(_output_dir))
    return resolve_model_path(
        value,
        root,
        allow_android_roots=True,
        trusted_absolute_paths=_trusted_paths or (),
        trust_existing_files=False,
    )'''
extended = replace_once(extended, old, new, 'extended strict resolver')

old = '''    overwrite: bool = False,
    _output_dir: Optional[str] = None,
) -> dict:
    """Manage files relative to the real app output root and verify mutations."""'''
new = '''    overwrite: bool = False,
    _output_dir: Optional[str] = None,
    _trusted_paths: Optional[List[str]] = None,
) -> dict:
    """Manage files relative to the app workspace with explicit attachment trust."""'''
extended = replace_once(extended, old, new, 'file_manage trusted parameter')

# Every file_manage source/target call must pass the whitelist through the
# lower resolver. These strings are intentionally exact and count-checked.
for old_call, new_call, label in (
    ('_resolve_workspace_path(path, _output_dir)', '_resolve_workspace_path(path, _output_dir, _trusted_paths)', 'file_manage list'),
    ('_resolve_workspace_path(target_raw, _output_dir)', '_resolve_workspace_path(target_raw, _output_dir, _trusted_paths)', 'file_manage targets'),
    ('_resolve_workspace_path(source_raw, _output_dir)', '_resolve_workspace_path(source_raw, _output_dir, _trusted_paths)', 'file_manage sources'),
    ('_resolve_workspace_path(destination_path, _output_dir)', '_resolve_workspace_path(destination_path, _output_dir, _trusted_paths)', 'file_manage destination'),
):
    if new_call in extended:
        continue
    count = extended.count(old_call)
    if count < 1:
        raise SystemExit(f'{label}: source call not found')
    extended = extended.replace(old_call, new_call)

for marker in (
    'trusted_absolute_paths=_trusted_paths or ()',
    'trust_existing_files=False',
    '_trusted_paths: Optional[List[str]] = None',
):
    if marker not in extended:
        raise SystemExit(f'Missing extended trusted-path invariant: {marker}')
EXTENDED.write_text(extended, encoding='utf-8')

print('Applied V17 explicit attachment whitelist and strict model absolute-path boundary')
