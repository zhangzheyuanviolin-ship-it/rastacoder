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


from navixmind.agent import _prepare_tool_result_for_model
from navixmind.bridge import ToolError
from navixmind.tools import (
    ALL_LOCAL_SKILL_IDS,
    LOCAL_TOOL_PROMPT_HINTS,
    TOOLS_SCHEMA,
    execute_tool,
    get_enabled_tool_names,
    get_offline_tools_for_skills,
    _resolve_workspace_input_paths,
    _resolve_output_paths,
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

# ---------------------------------------------------------------------------
# A. Product invariant: the whole local tool surface is present and reachable.
# ---------------------------------------------------------------------------
require(len(ALL_LOCAL_SKILL_IDS) == 25, f'Expected 25 local Skills, got {len(ALL_LOCAL_SKILL_IDS)}')
canonical_names = {tool.get('name') for tool in TOOLS_SCHEMA}
require(len(canonical_names) == 37, f'Expected 37 canonical functions, got {len(canonical_names)}')
all_enabled = get_enabled_tool_names(ALL_LOCAL_SKILL_IDS)
require(len(all_enabled) == 37, f'All Skills expose {len(all_enabled)} functions, expected 37')
require(all_enabled == canonical_names, f'Local/cloud canonical surface drift: local-only={all_enabled-canonical_names}, missing-local={canonical_names-all_enabled}')
projected = get_offline_tools_for_skills(ALL_LOCAL_SKILL_IDS)
require({tool['name'] for tool in projected} == canonical_names, 'Projected 4B tool schema lost canonical functions')
require(set(LOCAL_TOOL_PROMPT_HINTS) == canonical_names, 'A canonical local function is missing its compact 4B prompt hint')

# Every canonical function must survive the small-model compatibility boundary
# under its own exact function name, even before required-argument validation.
for tool_name in sorted(canonical_names):
    normalized_name, normalized_args, notes = normalize_tool_call(tool_name, {}, context={})
    require(normalized_name == tool_name, f'Canonical local function renamed unexpectedly: {tool_name}->{normalized_name}, {notes}')
    require(isinstance(normalized_args, dict), f'Normalizer returned non-object args for {tool_name}')

# Auto-inventory every path-bearing field exposed to the 4B model. A future
# function cannot add another *_path/paths/output_dir field without forcing a
# deliberate V17-style audit update.
schema_path_keys = {
    key
    for tool in projected
    for key in ((tool.get('input_schema') or {}).get('properties') or {})
    if key == 'path' or key.endswith('_path') or key.endswith('_paths') or key.endswith('_dir')
}
expected_schema_path_keys = {
    'path', 'image_path', 'input_path', 'pdf_path', 'file_path', 'source_path',
    'destination_path', 'zip_path', 'docx_path', 'pptx_path', 'xlsx_path',
    'image_paths', 'file_paths', 'input_paths', 'output_path', 'output_dir',
}
require(
    schema_path_keys == expected_schema_path_keys,
    f'Local schema path inventory changed; audit central resolver before accepting: found={sorted(schema_path_keys)}, expected={sorted(expected_schema_path_keys)}',
)

# ---------------------------------------------------------------------------
# B. Exact V16 phone failure + entire leading-slash family.
# ---------------------------------------------------------------------------
require('/' in WORKSPACE_ALIASES, 'Bare slash workspace alias missing')
with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as external:
    root = os.path.normpath(td)
    Path(root, 'alpha.txt').write_text('alpha', encoding='utf-8')
    Path(root, 'beta.txt').write_text('beta', encoding='utf-8')
    Path(root, 'folder').mkdir()
    external_file = Path(external, 'attached.txt')
    external_file.write_text('trusted attachment', encoding='utf-8')

    for alias in ('', '.', './', '/', 'workspace', '/workspace', 'output', '/output'):
        require(resolve_model_path(alias, root) == root, f'Model workspace alias failed: {alias!r}')
        require(resolve_list_path(alias, root) == root, f'list_files workspace alias failed: {alias!r}')

    require(resolve_model_path('/ghost.txt', root, trusted_absolute_paths=(), trust_existing_files=False) == os.path.join(root, 'ghost.txt'), 'Invented /file leaked to Android root')
    require(resolve_model_path('/folder/new.txt', root, trusted_absolute_paths=(), trust_existing_files=False) == os.path.join(root, 'folder', 'new.txt'), 'Invented /folder/file leaked')
    require(resolve_output_path('/result.txt', root) == os.path.join(root, 'result.txt'), 'Generated /result leaked to Android root')

    # Exact copied phone call from V16.
    raw_args = {'path': '/', 'recursive': False, 'pattern': None, 'include_directories': True}
    canonical, args, repairs = normalize_tool_call('list_files', raw_args, context={'output_dir': root})
    require(canonical == 'list_files', canonical)
    require(args.get('path') == '.', f'Local ABI did not repair / -> .: {args}')
    require(any('virtual_workspace_alias:/->.' in note for note in repairs), repairs)
    context = {'output_dir': root, '_file_map': {}, '_diagnostics': []}
    executed = execute_tool(canonical, args, context)
    names = {entry['name'] for entry in executed['entries']}
    require({'alpha.txt', 'beta.txt', 'folder'} <= names, executed)
    require(os.path.normpath(executed['directory']) == root, executed)
    require(not any("Permission denied: '/'" in str(event) for event in context['_diagnostics']), 'V16 EACCES signature survived')

    direct = list_files(path='/', recursive=False, include_directories=True, _output_dir=root)
    require(os.path.normpath(direct['directory']) == root, direct)
    managed = file_manage(action='list', path='/', recursive=False, _output_dir=root)
    require(os.path.normpath(managed['directory']) == root, managed)
    made = file_manage(action='mkdir', path='/created_by_local_model', _output_dir=root)
    require(Path(root, 'created_by_local_model').is_dir(), made)

    # Every shared input key virtualizes both '/' and '/child'. destination_path
    # is tested separately as an output below.
    scalar_input_keys = (
        'image_path', 'input_path', 'pdf_path', 'file_path', 'path', 'source_path',
        'zip_path', 'docx_path', 'pptx_path', 'xlsx_path',
    )
    for key in scalar_input_keys:
        probe = {key: '/'}
        _resolve_workspace_input_paths(probe, root, trusted_paths=set())
        require(probe[key] == root, f'Bare slash leaked for {key}: {probe[key]}')
        child = {key: '/v17-child.dat'}
        _resolve_workspace_input_paths(child, root, trusted_paths=set())
        require(child[key] == os.path.join(root, 'v17-child.dat'), f'Leading slash leaked for {key}: {child[key]}')

    for key in ('image_paths', 'file_paths', 'input_paths'):
        probe = {key: ['/', '/v17-array-child.dat']}
        _resolve_workspace_input_paths(probe, root, trusted_paths=set())
        require(
            probe[key] == [root, os.path.join(root, 'v17-array-child.dat')],
            f'Array path resolver leaked a model absolute path for {key}: {probe[key]}',
        )

    out_probe = {'output_path': '/generated.bin', 'output_dir': '/unzipped', 'destination_path': '/renamed.bin'}
    _resolve_output_paths(out_probe, root)
    require(out_probe['output_path'] == os.path.join(root, 'generated.bin'), out_probe)
    require(out_probe['output_dir'] == os.path.join(root, 'unzipped'), out_probe)
    require(out_probe['destination_path'] == os.path.join(root, 'renamed.bin'), out_probe)

    # -----------------------------------------------------------------------
    # C. Explicit trust boundary. /etc/passwd exists on the Linux CI runner;
    # therefore this proves trust comes from _file_map, not filesystem existence.
    # -----------------------------------------------------------------------
    system_probe = '/etc/passwd'
    if os.path.isfile(system_probe):
        untrusted = {'file_path': system_probe}
        _resolve_workspace_input_paths(untrusted, root, trusted_paths=set())
        require(untrusted['file_path'] == os.path.join(root, 'etc', 'passwd'), f'Existing system path bypassed model boundary: {untrusted}')

    trusted = {'file_path': str(external_file)}
    _resolve_workspace_input_paths(trusted, root, trusted_paths={str(external_file)})
    require(trusted['file_path'] == str(external_file), f'Explicit attachment whitelist was lost: {trusted}')

    attachment_context = {
        'output_dir': root,
        '_file_map': {'attached.txt': str(external_file)},
        '_diagnostics': [],
    }
    read_attachment = execute_tool('read_file', {'file_path': 'attached.txt'}, attachment_context)
    require(read_attachment.get('content') == 'trusted attachment', read_attachment)

    # file_manage has a second internal path resolver. Prove the whitelist
    # survives both layers while destination stays workspace-owned.
    copied = execute_tool(
        'file_manage',
        {'action': 'copy', 'source_path': 'attached.txt', 'destination_path': '/copied_from_attachment.txt'},
        attachment_context,
    )
    require(Path(root, 'copied_from_attachment.txt').read_text(encoding='utf-8') == 'trusted attachment', copied)
    require(os.path.normpath(copied['destination_path']) == os.path.join(root, 'copied_from_attachment.txt'), copied)

    # Nested Office operation paths share the same trust whitelist.
    nested = {'operations': [{'action': 'noop', 'params': {'image_path': str(external_file)}}]}
    _resolve_workspace_input_paths(nested, root, trusted_paths={str(external_file)})
    require(nested['operations'][0]['params']['image_path'] == str(external_file), nested)

    for logical, physical in ANDROID_LOGICAL_ROOTS.items():
        require(resolve_model_path(logical, root, trusted_absolute_paths=(), trust_existing_files=False) == os.path.normpath(physical), f'Android logical root failed: {logical}')
        require(resolve_model_path('/' + logical, root, trusted_absolute_paths=(), trust_existing_files=False) == os.path.normpath(physical), f'Android /alias root failed: {logical}')

    # Model-facing list result must never teach the 4B model private physical
    # paths which it could echo back on its next tool turn.
    offline_context = {'output_dir': root, 'offline_model_info': {'id': 'qwen3-4b'}}
    model_payload = _prepare_tool_result_for_model('list_files', executed, offline_context, 2048)
    require(root not in model_payload, f'Physical workspace path leaked back to local model: {model_payload}')
    require('alpha.txt' in model_payload, model_payload)

    # Manual Skill boundary remains authoritative after all compatibility repair.
    blocked_context = {'output_dir': root, '_allowed_tools': {'read_file'}, '_diagnostics': []}
    blocked = False
    try:
        execute_tool('write_file', {'output_path': 'blocked.txt', 'content': 'x'}, blocked_context)
    except ToolError as exc:
        blocked = '[MODEL_TOOL_DISABLED]' in str(exc)
    require(blocked, 'Compatibility layer bypassed manual local Skill boundary')

# ---------------------------------------------------------------------------
# D. Small-model structured ABI audit for historically thinner v7 tool schemas.
# ---------------------------------------------------------------------------
ctx = {'output_dir': '/tmp/v17-workspace', '_file_map': {}, '_current_files': []}

name, args, notes = normalize_tool_call('file_manage', {'operation': 'ls'}, context=ctx)
require(name == 'file_manage' and args.get('action') == 'list' and args.get('path') == '.', (args, notes))

for tool in ('list_zip', 'extract_zip'):
    name, args, notes = normalize_tool_call(tool, {'path': 'archive.zip'}, context=ctx)
    require(args.get('zip_path') == 'archive.zip', (tool, args, notes))

name, args, notes = normalize_tool_call('pdf_manage', {'operation': 'extract', 'path': 'a.pdf', 'pages': '1'}, context=ctx)
require(args.get('action') == 'extract_pages' and args.get('input_path') == 'a.pdf', (args, notes))

name, args, notes = normalize_tool_call('create_pptx', {'title': 'V17'}, context=ctx)
require(args.get('output_path') == 'presentation.pptx', (args, notes))

name, args, notes = normalize_tool_call('create_xlsx', {'sheets': {'name': 'S', 'rows': [['x']]}}, context=ctx)
require(args.get('output_path') == 'spreadsheet.xlsx' and isinstance(args.get('sheets'), list), (args, notes))

name, args, notes = normalize_tool_call('image_compose', {'image_path': 'a.png', 'action': 'convert', 'params': {'format': 'jpg'}}, context=ctx)
require(args.get('input_paths') == ['a.png'], (args, notes))
require(args.get('operation') == 'convert', (args, notes))
require(str(args.get('output_path', '')).endswith('.jpg'), (args, notes))

name, args, notes = normalize_tool_call('convert_document', {'input_path': 'a.txt', 'format': 'docx'}, context=ctx)
require(args.get('output_format') == 'docx', (args, notes))
require(args.get('output_path') == 'a_converted.docx', (args, notes))

name, args, notes = normalize_tool_call('anysearch_extract', {'link': 'https://example.com/'}, context=ctx)
require(args.get('url') == 'https://example.com/', (args, notes))

# Root-only output is a directory notation, never a filename. Deterministic
# defaults replace it before strict schema validation.
for tool, raw, expected in [
    ('write_file', {'output_path': '/', 'content': 'x'}, 'output.txt'),
    ('create_docx', {'output_path': '/', 'content': 'x'}, 'document.docx'),
    ('create_pdf', {'output_path': '/', 'content': 'x'}, 'document.pdf'),
    ('create_pptx', {'output_path': '/', 'title': 'x'}, 'presentation.pptx'),
    ('create_xlsx', {'output_path': '/', 'sheets': []}, 'spreadsheet.xlsx'),
]:
    _, repaired, notes = normalize_tool_call(tool, raw, context=ctx)
    require(repaired.get('output_path') == expected, (tool, repaired, notes))

# Every schema which requires output_path gets a deterministic local-model route.
minimal = {
    'write_file': {'content': 'x'},
    'create_docx': {'content': 'x'},
    'create_pdf': {'content': 'x'},
    'create_zip': {'file_paths': ['a.txt']},
    'create_pptx': {'title': 'x'},
    'create_xlsx': {'sheets': []},
    'image_compose': {'input_paths': ['a.png'], 'operation': 'convert'},
    'smart_crop': {'input_path': 'a.png'},
    'ffmpeg_process': {'input_path': 'a.mp3', 'operation': 'extract_audio', 'params': {'format': 'mp3'}},
    'modify_docx': {'input_path': 'a.docx', 'operations': []},
    'modify_pptx': {'input_path': 'a.pptx', 'operations': []},
    'modify_xlsx': {'input_path': 'a.xlsx', 'operations': []},
}
for schema in projected:
    required = set((schema.get('input_schema') or {}).get('required') or [])
    if 'output_path' not in required:
        continue
    tool = schema['name']
    require(tool in minimal, f'No V17 output-default audit case for required-output tool {tool}')
    _, repaired, notes = normalize_tool_call(tool, minimal[tool], context=ctx)
    require(repaired.get('output_path'), f'{tool} still depends on model supplying output_path: {repaired}, {notes}')
    require(repaired['output_path'] not in {'/', '.', './'}, f'{tool} produced root-only output: {repaired}')

# ---------------------------------------------------------------------------
# E. Source markers permanently guard the local-first contract.
# ---------------------------------------------------------------------------
tools_source = (ROOT / 'python/navixmind/tools/__init__.py').read_text(encoding='utf-8')
compat_source = (ROOT / 'python/navixmind/tools/compat.py').read_text(encoding='utf-8')
path_source = (ROOT / 'python/navixmind/tools/path_contract.py').read_text(encoding='utf-8')
extended_source = (ROOT / 'python/navixmind/tools/extended_tools.py').read_text(encoding='utf-8')
for marker in (
    'RASTACODER_V17_ALL_LOCAL_PATH_BOUNDARY',
    'RASTACODER_V17_OUTPUT_DIRECTORY_BOUNDARY',
    'RASTACODER_V17_EXPLICIT_TRUSTED_ATTACHMENT_PATHS',
    'RASTACODER_V17_STRICT_MODEL_PATH_RESOLUTION',
    'OUTPUT PATH RULE:',
    'Do not invent Linux roots such as /workspace or /output.',
):
    require(marker in tools_source, f'Missing executor/prompt marker: {marker}')
for marker in (
    'RASTACODER_V17_LOCAL_ROOT_ALIAS_RECOVERY',
    'RASTACODER_V17_ALL_LOCAL_OUTPUT_ALIASES',
    'RASTACODER_V17_STRUCTURED_TOOL_ABI_RECOVERY',
    'RASTACODER_V17_DETERMINISTIC_OUTPUT_DEFAULTS',
):
    require(marker in compat_source, f'Missing local ABI marker: {marker}')
require('every other leading-slash path is interpreted as workspace-relative' in path_source, 'Systemic leading-slash path policy missing')
require('trust_existing_files=False' in tools_source, 'Executor is not using strict explicit-trust mode')
require('trusted_absolute_paths=_trusted_paths or ()' in extended_source, 'file_manage lower resolver lost attachment whitelist')

print('V17 validation passed: exact Qwen3 / regression, all 25 Skills / 37 functions, automatic path inventory, explicit attachment whitelist, existing-system-path rejection, scalar/array/destination/output boundaries, structured 4B ABI defaults, logical result reinjection, and manual Skill enforcement are locked.')
