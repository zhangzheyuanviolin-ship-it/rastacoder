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
# A. Product invariant: the whole local tool surface is present.
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

# ---------------------------------------------------------------------------
# B. Exact V16 phone failure + every shared path-bearing key.
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

    # Arbitrary model-invented leading slashes are virtual workspace paths.
    require(resolve_model_path('/ghost.txt', root) == os.path.join(root, 'ghost.txt'), 'Invented /file leaked to Android root')
    require(resolve_model_path('/folder/new.txt', root) == os.path.join(root, 'folder', 'new.txt'), 'Invented /folder/file leaked')
    require(resolve_output_path('/result.txt', root) == os.path.join(root, 'result.txt'), 'Generated /result leaked to Android root')
    # Existing attached file remains real, preserving the V12 attachment contract.
    require(resolve_model_path(str(external_file), root) == str(external_file), 'Trusted attached absolute file was damaged')

    # Exact copied phone call.
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

    # Direct lower-layer list and file-manager paths use the same contract.
    direct = list_files(path='/', recursive=False, include_directories=True, _output_dir=root)
    require(os.path.normpath(direct['directory']) == root, direct)
    managed = file_manage(action='list', path='/', recursive=False, _output_dir=root)
    require(os.path.normpath(managed['directory']) == root, managed)
    made = file_manage(action='mkdir', path='/created_by_local_model', _output_dir=root)
    require(Path(root, 'created_by_local_model').is_dir(), made)

    # Every shared scalar input/destination key must virtualize both '/' and
    # '/child', covering file, Office, archive, image and media families.
    scalar_keys = (
        'image_path', 'input_path', 'pdf_path', 'file_path', 'path', 'source_path',
        'destination_path', 'zip_path', 'docx_path', 'pptx_path', 'xlsx_path',
    )
    for key in scalar_keys:
        probe = {key: '/'}
        _resolve_workspace_input_paths(probe, root)
        require(probe[key] == root, f'Bare slash leaked for {key}: {probe[key]}')
        child = {key: '/v17-child.dat'}
        _resolve_workspace_input_paths(child, root)
        require(child[key] == os.path.join(root, 'v17-child.dat'), f'Leading slash leaked for {key}: {child[key]}')

    # extract_zip uses output_dir instead of output_path; lock both output forms.
    out_probe = {'output_path': '/generated.bin', 'output_dir': '/unzipped'}
    _resolve_output_paths(out_probe, root)
    require(out_probe['output_path'] == os.path.join(root, 'generated.bin'), out_probe)
    require(out_probe['output_dir'] == os.path.join(root, 'unzipped'), out_probe)

    for logical, physical in ANDROID_LOGICAL_ROOTS.items():
        require(resolve_model_path(logical, root) == os.path.normpath(physical), f'Android logical root failed: {logical}')
        require(resolve_model_path('/' + logical, root) == os.path.normpath(physical), f'Android /alias root failed: {logical}')

# ---------------------------------------------------------------------------
# C. Small-model structured ABI audit for tools which previously had thinner
# compatibility coverage than Word/PDF/text tools.
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

# Root-only output is not a filename. Deterministic defaults must replace it.
for tool, raw, expected in [
    ('write_file', {'output_path': '/', 'content': 'x'}, 'output.txt'),
    ('create_docx', {'output_path': '/', 'content': 'x'}, 'document.docx'),
    ('create_pdf', {'output_path': '/', 'content': 'x'}, 'document.pdf'),
    ('create_pptx', {'output_path': '/', 'title': 'x'}, 'presentation.pptx'),
    ('create_xlsx', {'output_path': '/', 'sheets': []}, 'spreadsheet.xlsx'),
]:
    _, repaired, notes = normalize_tool_call(tool, raw, context=ctx)
    require(repaired.get('output_path') == expected, (tool, repaired, notes))

# ---------------------------------------------------------------------------
# D. Required-output ABI: every local schema which requires output_path must be
# able to reach strict executor validation without asking a 4B model for a
# meaningless Android filesystem root.
# ---------------------------------------------------------------------------
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
# E. Prompt/runtime markers: prevent future cloud/runtime changes from silently
# deleting the local-first contract again.
# ---------------------------------------------------------------------------
tools_source = (ROOT / 'python/navixmind/tools/__init__.py').read_text(encoding='utf-8')
compat_source = (ROOT / 'python/navixmind/tools/compat.py').read_text(encoding='utf-8')
path_source = (ROOT / 'python/navixmind/tools/path_contract.py').read_text(encoding='utf-8')
for marker in (
    'RASTACODER_V17_ALL_LOCAL_PATH_BOUNDARY',
    'RASTACODER_V17_OUTPUT_DIRECTORY_BOUNDARY',
    'OUTPUT PATH RULE:',
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

print('V17 validation passed: exact Qwen3 / regression, arbitrary leading-slash virtualization, all shared input/output path keys, structured v7 tool ABI defaults, and complete 25-Skill/37-function local surface are locked.')
