from pathlib import Path
import re


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'Expected one anchor in {path}, found {count}: {old[:120]!r}')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')


def replace_regex_once(path: str, pattern: str, replacement: str) -> None:
    p = Path(path)
    text = p.read_text(encoding='utf-8')
    new_text, count = re.subn(pattern, replacement, text, count=1, flags=re.DOTALL)
    if count != 1:
        raise SystemExit(f'Expected one regex anchor in {path}, found {count}: {pattern[:120]!r}')
    p.write_text(new_text, encoding='utf-8')


# ---------------------------------------------------------------------------
# 1. Central path contract shared by executor and extended file tools.
# ---------------------------------------------------------------------------
path_contract = Path('python/navixmind/tools/path_contract.py')
if not path_contract.exists():
    path_contract.write_text(r'''"""Canonical model-facing path contract for RastaCoder.

The model works in a logical namespace. Physical Android/app paths are execution
implementation details. Small models may still emit common virtual absolute
aliases such as /workspace; those aliases are repaired deterministically.
"""
from __future__ import annotations

import os
from typing import Optional

from ..bridge import ToolError


ANDROID_LOGICAL_ROOTS = {
    'downloads': '/storage/emulated/0/Download',
    'documents': '/storage/emulated/0/Documents',
    'pictures': '/storage/emulated/0/Pictures',
    'screenshots': '/storage/emulated/0/Pictures/Screenshots',
    'camera': '/storage/emulated/0/DCIM/Camera',
}

WORKSPACE_ALIASES = {
    '', '.', './', 'workspace', 'workspace/', 'output', 'output/',
    '/workspace', '/workspace/', '/output', '/output/',
}


def _safe_join(base: str, remainder: str, label: str) -> str:
    base = os.path.normpath(base)
    remainder = str(remainder or '').replace('\\', '/').strip()
    while remainder.startswith('./'):
        remainder = remainder[2:]
    if not remainder:
        return base
    if remainder == '..' or remainder.startswith('../'):
        raise ToolError(f'Path escapes {label}: {remainder}')
    target = os.path.normpath(os.path.join(base, remainder))
    try:
        if os.path.commonpath([base, target]) != base:
            raise ToolError(f'Path escapes {label}: {remainder}')
    except ValueError as exc:
        raise ToolError(f'Invalid path for {label}: {remainder}') from exc
    return target


def _strip_virtual_workspace_prefix(raw: str) -> Optional[str]:
    value = raw.replace('\\', '/').strip()
    lower = value.lower()
    if lower in WORKSPACE_ALIASES:
        return ''
    for prefix in ('workspace/', 'output/', '/workspace/', '/output/'):
        if lower.startswith(prefix):
            return value[len(prefix):]
    return None


def resolve_model_path(value: str, workspace_root: str, allow_android_roots: bool = True) -> str:
    """Resolve one model-facing path while preserving trusted real absolute paths.

    Virtual workspace aliases are interpreted before the generic absolute-path
    branch. This is the key invariant missing in V11.
    """
    root = os.path.normpath(str(workspace_root))
    raw = str(value or '').strip().replace('\\', '/')

    virtual_remainder = _strip_virtual_workspace_prefix(raw)
    if virtual_remainder is not None:
        return _safe_join(root, virtual_remainder, 'workspace root')

    probe = raw.lstrip('/')
    first, sep, remainder = probe.partition('/')
    first_key = first.lower()
    if allow_android_roots and first_key in ANDROID_LOGICAL_ROOTS:
        # Only treat a leading-slash absolute path as a logical alias when the
        # first segment is one of our documented model-facing Android roots.
        if not raw.startswith('/') or raw.lower() == '/' + probe.lower():
            return _safe_join(ANDROID_LOGICAL_ROOTS[first_key], remainder if sep else '', f'{first_key} root')

    # Attached files and already-resolved real Android/app paths reach here as
    # genuine absolute paths and must remain usable.
    if os.path.isabs(raw):
        return os.path.normpath(raw)

    while raw.startswith('./'):
        raw = raw[2:]
    return _safe_join(root, raw, 'workspace root')


def resolve_output_path(value: str, workspace_root: str) -> str:
    """Resolve generated output paths. Virtual /workspace and /output are safe aliases."""
    return resolve_model_path(value, workspace_root, allow_android_roots=False)


def resolve_list_path(value: Optional[str], workspace_root: str, legacy_directory: str = 'output') -> str:
    """Resolve list_files target, retaining legacy directory compatibility."""
    raw = str(value or '').strip().replace('\\', '/')
    directory_key = str(legacy_directory or 'output').strip().lower()
    if not raw:
        if directory_key in {'output', 'workspace', ''}:
            return os.path.normpath(workspace_root)
        if directory_key in ANDROID_LOGICAL_ROOTS:
            return os.path.normpath(ANDROID_LOGICAL_ROOTS[directory_key])
        raw = directory_key

    # Legacy directory=<android-root> plus relative path keeps that root.
    if directory_key in ANDROID_LOGICAL_ROOTS and not os.path.isabs(raw):
        probe = raw.lstrip('./')
        first = probe.partition('/')[0].lower()
        if first not in ANDROID_LOGICAL_ROOTS and _strip_virtual_workspace_prefix(raw) is None:
            return _safe_join(ANDROID_LOGICAL_ROOTS[directory_key], probe, f'{directory_key} root')

    return resolve_model_path(raw, workspace_root, allow_android_roots=True)


def logicalize_path(value: str, workspace_root: str) -> str:
    """Convert a physical execution path back to the model-facing logical namespace."""
    raw = os.path.normpath(str(value or ''))
    root = os.path.normpath(str(workspace_root))
    try:
        if os.path.commonpath([root, raw]) == root:
            rel = os.path.relpath(raw, root).replace('\\', '/')
            return '.' if rel == '.' else rel
    except ValueError:
        pass
    for logical, physical in ANDROID_LOGICAL_ROOTS.items():
        base = os.path.normpath(physical)
        try:
            if os.path.commonpath([base, raw]) == base:
                rel = os.path.relpath(raw, base).replace('\\', '/')
                return logical if rel == '.' else f'{logical}/{rel}'
        except ValueError:
            continue
    # Do not teach the model arbitrary physical filesystem roots from list
    # results. A basename remains actionable only when an attachment/file map
    # supplied it; arbitrary external traversal is intentionally not promoted.
    return os.path.basename(raw) or '.'
''', encoding='utf-8')


# ---------------------------------------------------------------------------
# 2. Compatibility normalization: repair virtual absolute aliases early.
# ---------------------------------------------------------------------------
compat_path = 'python/navixmind/tools/compat.py'
compat = Path(compat_path).read_text(encoding='utf-8')
if '# RASTACODER_V12_VIRTUAL_WORKSPACE_ALIASES' not in compat:
    replace_once(
        compat_path,
        '        workspace_aliases = {"", ".", "./", "output", "output/", "workspace", "workspace/"}\n',
        '        # RASTACODER_V12_VIRTUAL_WORKSPACE_ALIASES\n'
        '        workspace_aliases = {"", ".", "./", "output", "output/", "workspace", "workspace/", "/output", "/output/", "/workspace", "/workspace/"}\n'
    )
    replace_once(
        compat_path,
        '''        path_text = str(args.get("path") or ".").strip().replace("\\\\", "/")\n        if path_text.lower() in workspace_aliases:\n            args["path"] = "."\n        elif path_text.lower().startswith("output/"):\n            args["path"] = path_text[7:] or "."\n        elif path_text.lower().startswith("workspace/"):\n            args["path"] = path_text[10:] or "."\n''',
        '''        path_text = str(args.get("path") or ".").strip().replace("\\\\", "/")\n        path_lower = path_text.lower()\n        if path_lower in workspace_aliases:\n            if path_text != ".":\n                notes.append(f"list_files:virtual_workspace_alias:{path_text}->.")\n            args["path"] = "."\n        elif path_lower.startswith("/output/"):\n            args["path"] = path_text[len("/output/"):] or "."\n            notes.append(f"list_files:virtual_workspace_prefix:{path_text}->{args['path']}")\n        elif path_lower.startswith("/workspace/"):\n            args["path"] = path_text[len("/workspace/"):] or "."\n            notes.append(f"list_files:virtual_workspace_prefix:{path_text}->{args['path']}")\n        elif path_lower.startswith("output/"):\n            args["path"] = path_text[7:] or "."\n        elif path_lower.startswith("workspace/"):\n            args["path"] = path_text[10:] or "."\n        else:\n            # Small models also invent leading slashes for documented logical\n            # Android roots. Canonicalize those without accepting arbitrary OS roots.\n            for _root in ("downloads", "documents", "pictures", "screenshots", "camera"):\n                if path_lower == f"/{_root}":\n                    args["path"] = _root\n                    notes.append(f"list_files:logical_root:{path_text}->{_root}")\n                    break\n                if path_lower.startswith(f"/{_root}/"):\n                    args["path"] = _root + "/" + path_text[len(_root) + 2:]\n                    notes.append(f"list_files:logical_root:{path_text}->{args['path']}")\n                    break\n'''
    )


# ---------------------------------------------------------------------------
# 3. Executor: use the central contract for every model-facing path.
# ---------------------------------------------------------------------------
tools_path = 'python/navixmind/tools/__init__.py'
tools = Path(tools_path).read_text(encoding='utf-8')
if '# RASTACODER_V12_PATH_CONTRACT_IMPORT' not in tools:
    replace_once(
        tools_path,
        'from .compat import normalize_tool_call\n',
        'from .compat import normalize_tool_call\n'
        '# RASTACODER_V12_PATH_CONTRACT_IMPORT\n'
        'from .path_contract import resolve_model_path, resolve_output_path\n'
    )

    replace_once(
        tools_path,
        '"list_files": "list_files(path=\'.\', recursive=false, pattern=null, include_directories=true) ; path is workspace-relative",\n',
        '"list_files": "list_files(path=\'.\', recursive=false, pattern=null, include_directories=true) ; use path=\'.\' for workspace root",\n'
    )

    replace_once(
        tools_path,
        '                    "path": {"type": "string", "default": ".", "description": "Workspace-relative folder path; \'.\' means workspace root"},\n',
        '                    "path": {"type": "string", "default": ".", "description": "Logical folder path. Use exactly \'.\' for workspace root; nested workspace paths are relative such as folder/sub"},\n'
    )

    replace_once(
        tools_path,
        '        "- Use attached file basenames exactly as shown in the user message; the app resolves them to real paths.",\n',
        '        "- Use attached file basenames exactly as shown in the user message; the app resolves them to real paths.",\n'
        '        "- WORKSPACE PATH RULE: use path=\'.\' for the workspace root and relative paths like folder/file.txt below it. Do not invent Linux roots such as /workspace or /output.",\n'
    )

    replace_regex_once(
        tools_path,
        r"# RASTACODER_V11_GLOBAL_WORKSPACE_PATHS\ndef _workspace_relative_path\(value: str, output_dir: str\) -> str:\n.*?\n\ndef _resolve_workspace_input_paths",
        '''# RASTACODER_V11_GLOBAL_WORKSPACE_PATHS\n# RASTACODER_V12_CENTRAL_PATH_CONTRACT\ndef _workspace_relative_path(value: str, output_dir: str) -> str:\n    return resolve_model_path(value, output_dir, allow_android_roots=True)\n\n\ndef _resolve_workspace_input_paths'''
    )

    replace_regex_once(
        tools_path,
        r"def _resolve_output_paths\(args: Dict\[str, Any\], output_dir: str\) -> None:\n.*?\n\ndef _file_info",
        '''def _resolve_output_paths(args: Dict[str, Any], output_dir: str) -> None:\n    \"\"\"Resolve generated outputs through the same virtual-workspace contract.\"\"\"\n    import os\n    os.makedirs(output_dir, exist_ok=True)\n    value = args.get('output_path')\n    if isinstance(value, str):\n        args['output_path'] = resolve_output_path(value, output_dir)\n\n\ndef _file_info'''
    )


# ---------------------------------------------------------------------------
# 4. Extended file tools: same contract even when called below executor level.
# ---------------------------------------------------------------------------
ext_path = 'python/navixmind/tools/extended_tools.py'
ext = Path(ext_path).read_text(encoding='utf-8')
if '# RASTACODER_V12_EXTENDED_PATH_CONTRACT' not in ext:
    replace_once(
        ext_path,
        'from ..bridge import ToolError\n',
        'from ..bridge import ToolError\n'
        '# RASTACODER_V12_EXTENDED_PATH_CONTRACT\n'
        'from .path_contract import resolve_model_path, resolve_list_path\n'
    )
    replace_regex_once(
        ext_path,
        r"# RASTACODER_V11_WORKSPACE_ROOT\ndef _resolve_workspace_path\(value: str, _output_dir: Optional\[str\]\) -> str:\n.*?\n\ndef _resolve_named_directory",
        '''# RASTACODER_V11_WORKSPACE_ROOT\n# RASTACODER_V12_EXTENDED_PATH_CONTRACT\ndef _resolve_workspace_path(value: str, _output_dir: Optional[str]) -> str:\n    \"\"\"Resolve through the same central model-facing path contract as execute_tool.\"\"\"\n    root = os.path.normpath(_default_output_dir(_output_dir))\n    return resolve_model_path(value, root, allow_android_roots=True)\n\n\ndef _resolve_named_directory'''
    )
    replace_regex_once(
        ext_path,
        r"def _resolve_list_target\(directory: str, path: Optional\[str\], _output_dir: Optional\[str\]\) -> str:\n.*?\n\ndef list_files",
        '''def _resolve_list_target(directory: str, path: Optional[str], _output_dir: Optional[str]) -> str:\n    \"\"\"Resolve list target through the central logical namespace.\"\"\"\n    root = os.path.normpath(_default_output_dir(_output_dir))\n    return resolve_list_path(path, root, legacy_directory=directory)\n\n\ndef list_files'''
    )


# ---------------------------------------------------------------------------
# 5. Agent: logicalize list results before model prefill + specific recovery.
# ---------------------------------------------------------------------------
agent_path = 'python/navixmind/agent.py'
agent = Path(agent_path).read_text(encoding='utf-8')
if '# RASTACODER_V12_LOGICAL_LIST_RESULTS' not in agent:
    replace_once(
        agent_path,
        'from .tools.compat import normalize_tool_call, normalize_tool_name\n',
        'from .tools.compat import normalize_tool_call, normalize_tool_name\n'
        'from .tools.path_contract import logicalize_path\n'
    )
    replace_once(
        agent_path,
        '\ndef _prepare_tool_result_for_model(tool_name: str, result: Any, context: Dict[str, Any], max_output_tokens: int) -> str:\n',
        r'''
# RASTACODER_V12_LOGICAL_LIST_RESULTS
def _list_files_payload_for_model(result: Any, max_chars: int) -> str:
    """Expose logical workspace paths to the model, never the physical app root."""
    if not isinstance(result, dict):
        return _trim_model_text(result, max_chars)[0]
    root = str(result.get('workspace_root') or '')
    requested = str(result.get('requested_path') or '.').strip() or '.'
    lines = [
        f'workspace_path: {requested}',
        f'count: {int(result.get("count") or 0)}',
        f'recursive: {bool(result.get("recursive"))}',
    ]
    pattern = result.get('pattern')
    if pattern:
        lines.append(f'pattern: {pattern}')
    entries = result.get('entries') if isinstance(result.get('entries'), list) else []
    lines.append('entries:')
    for item in entries:
        if not isinstance(item, dict):
            continue
        logical = logicalize_path(str(item.get('path') or item.get('name') or ''), root) if root else str(item.get('name') or '')
        kind = str(item.get('type') or 'file')
        if kind == 'directory':
            lines.append(f'- directory: {logical}')
        else:
            lines.append(f'- file: {logical} ({int(item.get("size_bytes") or 0)} bytes)')
    if result.get('truncated'):
        lines.append('truncated: true')
    payload, truncated = _trim_model_text('\n'.join(lines), max_chars)
    if truncated:
        payload += '\ncontext_safety_note: File listing was truncated before local-model prefill.'
    return payload


def _prepare_tool_result_for_model(tool_name: str, result: Any, context: Dict[str, Any], max_output_tokens: int) -> str:
'''
    )
    replace_once(
        agent_path,
        '''    if tool_name in _SEARCH_RESULT_TOOLS:\n        payload = _search_result_payload_for_model(tool_name, result, max_chars)\n    elif isinstance(result, dict):\n''',
        '''    if tool_name in _SEARCH_RESULT_TOOLS:\n        payload = _search_result_payload_for_model(tool_name, result, max_chars)\n    elif tool_name == 'list_files':\n        payload = _list_files_payload_for_model(result, max_chars)\n    elif isinstance(result, dict):\n'''
    )
    replace_once(
        agent_path,
        '''    elif '[model_tool_argument_error]' in low or '[model_tool_name_error]' in low:\n        recovery = 'RECOVERABLE: Retry once with one enabled canonical tool name and the exact documented argument keys.'\n''',
        '''    elif tool_name == 'list_files' and ('directory not found' in low or 'workspace' in low or 'path' in low):\n        recovery = (\n            "RECOVERABLE: If the user asked for the workspace root, retry once with list_files(path='.', recursive as needed). "\n            "For an unknown nested path, first list path='.' and choose an existing logical path. Do not ask the user to re-attach a workspace directory."\n        )\n    elif '[model_tool_argument_error]' in low or '[model_tool_name_error]' in low:\n        recovery = 'RECOVERABLE: Retry once with one enabled canonical tool name and the exact documented argument keys.'\n'''
    )

print('Applied RastaCoder v12 workspace alias hardening patch.')
