#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))


def require(condition, message):
    if not condition:
        raise AssertionError(message)


from navixmind.tools import (
    ALL_LOCAL_SKILL_IDS,
    TOOLS_SCHEMA,
    execute_tool,
    get_enabled_tool_names,
    _resolve_workspace_input_paths,
)
from navixmind.tools.compat import normalize_tool_call
from navixmind.tools.extended_tools import file_manage, list_files
from navixmind.tools.path_contract import (
    ANDROID_LOGICAL_ROOTS,
    WORKSPACE_ALIASES,
    resolve_list_path,
    resolve_model_path,
    resolve_output_path,
)

# Product invariant: local tool calling is the primary feature. Never silently
# lose a Skill or canonical function while repairing cloud/runtime behavior.
require(len(ALL_LOCAL_SKILL_IDS) == 25, f'Expected 25 local Skills, got {len(ALL_LOCAL_SKILL_IDS)}')
canonical_names = {tool.get('name') for tool in TOOLS_SCHEMA}
require(len(canonical_names) == 37, f'Expected 37 canonical functions, got {len(canonical_names)}')
require(len(get_enabled_tool_names(ALL_LOCAL_SKILL_IDS)) == 37, 'All local Skills no longer expose all 37 canonical functions')
require('list_files' in canonical_names and 'file_manage' in canonical_names, 'Core local workspace tools disappeared')

# Exact V16 real-device failure: Qwen3-4B emitted list_files(path="/"). A bare
# slash is a model-facing logical root and must resolve to the app workspace.
require('/' in WORKSPACE_ALIASES, 'Bare slash workspace alias missing')
with tempfile.TemporaryDirectory() as td:
    root = os.path.normpath(td)
    Path(root, 'alpha.txt').write_text('alpha', encoding='utf-8')
    Path(root, 'beta.txt').write_text('beta', encoding='utf-8')
    Path(root, 'folder').mkdir()

    for alias in ('', '.', './', '/', 'workspace', '/workspace', 'output', '/output'):
        require(resolve_model_path(alias, root) == root, f'Model workspace alias failed: {alias!r}')
        require(resolve_list_path(alias, root) == root, f'list_files workspace alias failed: {alias!r}')

    require(resolve_output_path('/', root) == root, 'Output resolver leaked bare slash to Android root')

    # Direct tool implementation replay.
    listed = list_files(path='/', recursive=False, include_directories=True, _output_dir=root)
    names = {entry['name'] for entry in listed['entries']}
    require({'alpha.txt', 'beta.txt', 'folder'} <= names, f'Bare-slash list_files did not list workspace: {listed}')
    require(os.path.normpath(listed['directory']) == root, f'list_files escaped workspace: {listed["directory"]}')

    # Exact agent/executor boundary replay using the raw arguments copied from
    # the V16 phone diagnostic.
    raw_args = {'path': '/', 'recursive': False, 'pattern': None, 'include_directories': True}
    canonical, args, repairs = normalize_tool_call('list_files', raw_args, context={})
    require(canonical == 'list_files', f'list_files canonicalization changed: {canonical}')
    context = {'output_dir': root, '_file_map': {}, '_diagnostics': []}
    executed = execute_tool(canonical, args, context)
    executed_names = {entry['name'] for entry in executed['entries']}
    require({'alpha.txt', 'beta.txt', 'folder'} <= executed_names, f'Executor replay failed: {executed}')
    require(os.path.normpath(executed['directory']) == root, f'Executor targeted Android root: {executed}')
    require(not any("Permission denied: '/'" in str(event) for event in context['_diagnostics']), 'V16 EACCES signature survived')

    # file_manage uses the same central path contract; prove the fix is shared
    # instead of being a one-off list_files patch.
    managed = file_manage(action='list', path='/', recursive=False, _output_dir=root)
    managed_names = {entry['name'] for entry in managed['entries']}
    require({'alpha.txt', 'beta.txt', 'folder'} <= managed_names, f'file_manage list("/") failed: {managed}')

    # Every scalar model-facing input-path key resolved by the common executor
    # must map bare slash to the workspace root. This protects document, image,
    # archive, media and file tools which share these keys.
    scalar_keys = (
        'image_path', 'input_path', 'pdf_path', 'file_path', 'path', 'source_path',
        'zip_path', 'docx_path', 'pptx_path', 'xlsx_path',
    )
    for key in scalar_keys:
        probe = {key: '/'}
        _resolve_workspace_input_paths(probe, root)
        require(probe[key] == root, f'Common path resolver leaked / for {key}: {probe[key]}')

    # Trusted already-resolved absolute paths must remain usable, otherwise
    # attachments and outputs from earlier tool turns would regress.
    trusted = os.path.join(root, 'alpha.txt')
    require(resolve_model_path(trusted, root) == trusted, 'Trusted workspace absolute path was damaged')

    # Documented Android logical roots remain stable.
    for logical, physical in ANDROID_LOGICAL_ROOTS.items():
        require(resolve_model_path(logical, root) == os.path.normpath(physical), f'Android logical root failed: {logical}')
        require(resolve_model_path('/' + logical, root) == os.path.normpath(physical), f'Android /alias root failed: {logical}')

# Prompt/schema invariant: local Qwen should be taught the logical namespace,
# while runtime remains tolerant when it chooses '/' anyway.
source = (ROOT / 'python/navixmind/tools/__init__.py').read_text(encoding='utf-8')
require("use path='.' for workspace root" in source, 'Local list_files workspace-root hint missing')
require('RASTACODER_V13_SMALL_MODEL_TOOL_ABI' in source, 'Small-model tool ABI projection disappeared')

print('V17 validation passed: exact Qwen3 list_files(path="/") phone failure is repaired at the shared path contract; 25 Skills / 37 functions and inherited path semantics remain intact.')
