import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))

from navixmind.agent import _prepare_tool_result_for_model, _tool_error_for_model
from navixmind.bridge import ToolError
from navixmind.tools import LOCAL_TOOL_PROMPT_HINTS, TOOLS_SCHEMA, build_offline_skill_prompt, execute_tool
from navixmind.tools.compat import normalize_tool_call
from navixmind.tools.extended_tools import _resolve_workspace_path
from navixmind.tools.path_contract import logicalize_path, resolve_model_path


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def text_from_read(result):
    if isinstance(result, dict):
        return str(result.get('content') or result.get('text') or result)
    return str(result)


def test_exact_user_workspace_failure_and_alias_family():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nested = root / 'folder' / 'sub'
        nested.mkdir(parents=True)
        (root / 'root.txt').write_text('root payload', encoding='utf-8')
        (nested / 'inside.txt').write_text('nested payload', encoding='utf-8')
        context = {'output_dir': str(root), '_diagnostics': []}

        # Exact V11 real-device failure from the user.
        name, args, notes = normalize_tool_call(
            'list_files',
            {'path': '/workspace', 'recursive': False, 'pattern': None, 'include_directories': True},
            context=context,
        )
        require(name == 'list_files', name)
        require(args.get('path') == '.', (args, notes))
        require(any('virtual_workspace_alias' in n for n in notes), notes)
        listed = execute_tool(name, args, context)
        require(Path(listed['directory']).resolve() == root.resolve(), listed)
        names = {entry['name'] for entry in listed['entries']}
        require({'root.txt', 'folder'} <= names, listed)

        # Equivalent virtual absolute root alias.
        _, output_args, output_notes = normalize_tool_call(
            'list_files', {'path': '/output', 'recursive': False}, context=context
        )
        require(output_args.get('path') == '.', (output_args, output_notes))
        listed_output = execute_tool('list_files', output_args, context)
        require(Path(listed_output['directory']).resolve() == root.resolve(), listed_output)

        # Nested virtual aliases must map inside the same real workspace.
        _, nested_args, nested_notes = normalize_tool_call(
            'list_files', {'path': '/workspace/folder/sub', 'recursive': False}, context=context
        )
        require(nested_args.get('path') == 'folder/sub', (nested_args, nested_notes))
        nested_list = execute_tool('list_files', nested_args, context)
        require(nested_list['count'] == 1 and nested_list['entries'][0]['name'] == 'inside.txt', nested_list)

        nested_read = execute_tool('read_file', {'file_path': '/workspace/folder/sub/inside.txt'}, context)
        require('nested payload' in text_from_read(nested_read), nested_read)

        # Generated outputs using model-invented virtual absolute roots must land in workspace.
        write_result = execute_tool(
            'write_file', {'output_path': '/workspace/generated.txt', 'content': 'generated payload'}, context
        )
        require((root / 'generated.txt').read_text(encoding='utf-8') == 'generated payload', write_result)
        require(not Path('/workspace/generated.txt').exists(), 'literal /workspace output path was used')

        # The lower extended-tools resolver must independently honor the same alias.
        require(Path(_resolve_workspace_path('/workspace', str(root))).resolve() == root.resolve(), 'extended resolver root')
        require(
            Path(_resolve_workspace_path('/output/folder/sub/inside.txt', str(root))).resolve() == (nested / 'inside.txt').resolve(),
            'extended resolver nested alias',
        )

        # Leading-slash logical Android roots are compatibility aliases, not literal /downloads paths.
        _, android_args, android_notes = normalize_tool_call(
            'list_files', {'path': '/downloads/example'}, context=context
        )
        require(android_args.get('path') == 'downloads/example', (android_args, android_notes))
        require(resolve_model_path('/downloads/example', str(root)).endswith('/storage/emulated/0/Download/example'), 'android logical alias')

        # Traversal remains rejected after virtual-prefix repair.
        failed = False
        try:
            execute_tool('read_file', {'file_path': '/workspace/../escape.txt'}, context)
        except Exception as exc:
            failed = 'escapes workspace root' in str(exc).lower() or 'escapes workspace' in str(exc).lower()
        require(failed, 'virtual alias traversal escaped or produced wrong error')


def test_model_facing_listing_is_logical_not_physical():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / 'alpha').mkdir()
        (root / 'alpha' / 'one.txt').write_text('1', encoding='utf-8')
        (root / 'two.txt').write_text('22', encoding='utf-8')
        context = {
            'output_dir': str(root),
            '_diagnostics': [],
            'offline_model_info': {'id': 'qwen3-4b'},
            'local_context_tokens': 8192,
        }
        result = execute_tool('list_files', {'path': '.', 'recursive': True}, context)
        payload = _prepare_tool_result_for_model('list_files', result, context, 2048)
        require(str(root) not in payload, payload)
        require('workspace_root' not in payload, payload)
        require('directory: ' + str(root) not in payload, payload)
        require('alpha/one.txt' in payload, payload)
        require('two.txt' in payload, payload)
        require('workspace_path: .' in payload, payload)
        require(logicalize_path(str(root / 'alpha' / 'one.txt'), str(root)) == 'alpha/one.txt', 'logicalize nested')


def test_prompt_and_error_recovery_contract():
    list_schema = next(t for t in TOOLS_SCHEMA if t.get('name') == 'list_files')
    desc = list_schema['input_schema']['properties']['path']['description']
    require("Use exactly '.' for workspace root" in desc, desc)
    require("use path='.' for workspace root" in LOCAL_TOOL_PROMPT_HINTS['list_files'], LOCAL_TOOL_PROMPT_HINTS['list_files'])

    prompt = build_offline_skill_prompt(['text_files'])
    require("WORKSPACE PATH RULE: use path='.' for the workspace root" in prompt, prompt)
    require('Do not invent Linux roots such as /workspace or /output.' in prompt, prompt)

    recovery = _tool_error_for_model('list_files', ToolError('Directory not found or inaccessible: /workspace'))
    require('RECOVERABLE' in recovery, recovery)
    require("path='.'" in recovery, recovery)
    require('Do not ask the user to re-attach a workspace directory' in recovery, recovery)


def test_trusted_real_absolute_paths_still_survive():
    with tempfile.TemporaryDirectory() as workspace, tempfile.TemporaryDirectory() as external:
        external_file = Path(external) / 'attached.txt'
        external_file.write_text('trusted attachment', encoding='utf-8')
        resolved = resolve_model_path(str(external_file), workspace)
        require(Path(resolved).resolve() == external_file.resolve(), (resolved, external_file))


if __name__ == '__main__':
    test_exact_user_workspace_failure_and_alias_family()
    test_model_facing_listing_is_logical_not_physical()
    test_prompt_and_error_recovery_contract()
    test_trusted_real_absolute_paths_still_survive()
    print('RastaCoder v12 validation passed: exact /workspace real-device failure repaired, virtual root aliases unified across layers, logical list results prevent physical-path drift, workspace recovery is explicit, traversal remains blocked, and trusted attachment absolute paths remain usable.')
