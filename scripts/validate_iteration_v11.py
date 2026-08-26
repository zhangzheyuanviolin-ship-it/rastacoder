import json
import os
import re
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))

from navixmind.agent import OpenAICompatibleClient
from navixmind.tools import (
    LOCAL_TOOL_PROMPT_HINTS,
    TOOLS_SCHEMA,
    execute_tool,
)
from navixmind.tools.compat import normalize_tool_call


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def test_argument_sanitizer_and_workspace_chain():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nested = root / 'folder' / 'sub'
        nested.mkdir(parents=True)
        (nested / 'inside.txt').write_text('workspace nested payload', encoding='utf-8')
        (root / 'root.pptx').write_bytes(b'placeholder')
        context = {'output_dir': str(root), '_diagnostics': []}

        # Exact real-device failure family 1: literal question marks copied from hints.
        name, args, notes = normalize_tool_call(
            'list_files',
            {'directory?': True, 'path?': './', 'recursive?': True, 'pattern?': None},
            context=context,
        )
        require(name == 'list_files', name)
        require(args.get('path') == '.', args)
        require(args.get('recursive') is True, args)
        require('directory?' not in args and 'path?' not in args, args)
        require(any('arg_key:directory?->directory' in note for note in notes), notes)
        result = execute_tool(name, args, context)
        paths = {Path(item['path']).name for item in result['entries']}
        require('inside.txt' in paths, result)
        require(Path(result['directory']).resolve() == root.resolve(), result)

        # Exact real-device failure family 2: optional directory emitted as boolean.
        _, args2, notes2 = normalize_tool_call(
            'list_files', {'directory': True, 'path': '.', 'recursive': True}, context=context
        )
        require(args2.get('path') == '.', args2)
        require('directory' not in args2, args2)
        require(any('removed_boolean_directory' in note for note in notes2), notes2)
        result2 = execute_tool('list_files', args2, context)
        require(Path(result2['directory']).resolve() == root.resolve(), result2)

        # Exact real-device failure family 3: directory=output + path=output.
        _, args3, _ = normalize_tool_call(
            'list_files', {'directory': 'output', 'path': 'output', 'recursive': True}, context=context
        )
        require(args3.get('path') == '.', args3)
        result3 = execute_tool('list_files', args3, context)
        require(Path(result3['directory']).resolve() == root.resolve(), result3)

        # Nested traversal must use the same workspace root.
        nested_list = execute_tool('list_files', {'path': 'folder/sub', 'recursive': False}, context)
        require(nested_list['count'] == 1, nested_list)
        require(nested_list['entries'][0]['name'] == 'inside.txt', nested_list)

        # A relative path discovered/known in the workspace must be reusable by a read tool.
        read_back = execute_tool('read_file', {'file_path': 'folder/sub/inside.txt'}, context)
        if isinstance(read_back, dict):
            content = read_back.get('content') or read_back.get('text') or ''
        else:
            content = str(read_back)
        require('workspace nested payload' in content, read_back)

        # output/ prefix must not create output/output duplication.
        write_result = execute_tool(
            'write_file', {'output_path': 'output/folder/new.txt', 'content': 'written once'}, context
        )
        require((root / 'folder' / 'new.txt').read_text(encoding='utf-8') == 'written once', write_result)
        require(not (root / 'output').exists(), 'output/output duplication was reintroduced')

        # Traversal outside the workspace must fail before file access.
        failed = False
        try:
            execute_tool('read_file', {'file_path': '../escape.txt'}, context)
        except Exception as exc:
            failed = 'escapes workspace root' in str(exc)
        require(failed, 'workspace traversal was not rejected')


def test_model_contract_has_no_optional_question_mark_keys():
    list_schema = next(t for t in TOOLS_SCHEMA if t.get('name') == 'list_files')['input_schema']
    props = set(list_schema.get('properties', {}))
    require(props == {'path', 'recursive', 'pattern', 'include_directories'}, props)
    require('directory' not in props, props)
    for name, hint in LOCAL_TOOL_PROMPT_HINTS.items():
        bad = re.findall(r'\b[A-Za-z_][A-Za-z0-9_]*\?', hint)
        require(not bad, f'{name} still exposes optional ? suffixes: {bad} in {hint}')


class FakeResponse:
    status_code = 200
    headers = {}
    text = ''

    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


def test_openai_compatible_tool_adapter():
    captured = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured['url'] = url
        captured['headers'] = headers or {}
        captured['body'] = json or {}
        captured['timeout'] = timeout
        return FakeResponse({
            'choices': [{
                'finish_reason': 'tool_calls',
                'message': {
                    'role': 'assistant',
                    'content': None,
                    'tool_calls': [{
                        'id': 'call_workspace',
                        'type': 'function',
                        'function': {
                            'name': 'list_files',
                            'arguments': json_module.dumps({'path': '.', 'recursive': True}),
                        },
                    }],
                },
            }],
            'usage': {'prompt_tokens': 123, 'completion_tokens': 17},
        })

    json_module = json
    client = OpenAICompatibleClient('https://provider.example/v1', 'secret-key', 'cloud-model-x')
    tools = [next(t for t in TOOLS_SCHEMA if t.get('name') == 'list_files')]
    with patch('navixmind.agent.requests.post', side_effect=fake_post):
        response = client.create_message(
            messages=[{'role': 'user', 'content': '列出工作区文件'}],
            system='system',
            tools=tools,
            max_tokens=2048,
            retry_count=1,
        )
    require(captured['url'] == 'https://provider.example/v1/chat/completions', captured)
    require(captured['headers'].get('authorization') == 'Bearer secret-key', captured)
    require(captured['body']['model'] == 'cloud-model-x', captured)
    require(captured['body']['tools'][0]['type'] == 'function', captured)
    require(captured['body']['tools'][0]['function']['name'] == 'list_files', captured)
    require(response['stop_reason'] == 'tool_use', response)
    call = next(b for b in response['content'] if b.get('type') == 'tool_use')
    require(call['id'] == 'call_workspace', call)
    require(call['name'] == 'list_files', call)
    require(call['input'] == {'path': '.', 'recursive': True}, call)
    require(response['usage'] == {'input_tokens': 123, 'output_tokens': 17}, response)

    # Verify assistant tool_use + user tool_result round-trip to native OpenAI roles.
    captured2 = {}

    def fake_post2(url, headers=None, json=None, timeout=None):
        captured2['body'] = json or {}
        return FakeResponse({
            'choices': [{'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': '完成'}}],
            'usage': {'prompt_tokens': 200, 'completion_tokens': 2},
        })

    history = [
        {'role': 'assistant', 'content': [{
            'type': 'tool_use', 'id': 'call_workspace', 'name': 'list_files',
            'input': {'path': '.', 'recursive': True},
        }]},
        {'role': 'user', 'content': [{
            'type': 'tool_result', 'tool_use_id': 'call_workspace',
            'content': 'TOOL_RESULT\ncount: 2',
        }]},
    ]
    with patch('navixmind.agent.requests.post', side_effect=fake_post2):
        response2 = client.create_message(history, system='system', tools=tools, retry_count=1)
    messages = captured2['body']['messages']
    require(any(m.get('role') == 'assistant' and m.get('tool_calls') for m in messages), messages)
    require(any(m.get('role') == 'tool' and m.get('tool_call_id') == 'call_workspace' for m in messages), messages)
    require(response2['stop_reason'] == 'end_turn', response2)

    # Base URL normalization accepts root, /v1 and full endpoint forms.
    require(OpenAICompatibleClient('https://x.example', '', 'm')._endpoint() == 'https://x.example/v1/chat/completions', 'root endpoint')
    require(OpenAICompatibleClient('https://x.example/v1', '', 'm')._endpoint() == 'https://x.example/v1/chat/completions', '/v1 endpoint')
    require(OpenAICompatibleClient('https://x.example/v1/chat/completions', '', 'm')._endpoint() == 'https://x.example/v1/chat/completions', 'full endpoint')


def test_flutter_wiring_static():
    storage = (ROOT / 'lib/core/services/storage_service.dart').read_text(encoding='utf-8')
    bridge = (ROOT / 'lib/core/bridge/bridge.dart').read_text(encoding='utf-8')
    models = (ROOT / 'lib/core/models/model_registry.dart').read_text(encoding='utf-8')
    settings = (ROOT / 'lib/features/settings/settings_screen.dart').read_text(encoding='utf-8')
    screen = (ROOT / 'lib/features/settings/openai_compatible_settings_screen.dart').read_text(encoding='utf-8')
    require('RASTACODER_V11_OPENAI_COMPAT_STORAGE' in storage, 'storage marker missing')
    require("'openai_compatible': openAICompatibleConfig" in bridge, 'bridge config injection missing')
    require("id: 'openai-compatible'" in models, 'model registry entry missing')
    require("title: 'OpenAI 兼容接口'" in settings, 'settings tile missing')
    require('Semantics(' in screen and 'textField: true' in screen and 'button: true' in screen, 'accessibility semantics missing')


if __name__ == '__main__':
    test_argument_sanitizer_and_workspace_chain()
    test_model_contract_has_no_optional_question_mark_keys()
    test_openai_compatible_tool_adapter()
    test_flutter_wiring_static()
    print('RastaCoder v11 validation passed: exact list_files failures repaired, one workspace path root across nested multi-step file operations, optional-key punctuation removed, and OpenAI-compatible native tool_calls round-trip verified.')
