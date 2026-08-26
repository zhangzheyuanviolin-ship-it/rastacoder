#!/usr/bin/env python3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))


def require(condition, message):
    if not condition:
        raise AssertionError(message)


# Source invariants for the exact real-device regressions reported after v7.
chat = (ROOT / 'lib/features/chat/presentation/chat_screen.dart').read_text(encoding='utf-8')
require('_ensureSelectedRouteReadyForSend' in chat, 'send-time model route synchronization missing')
require('LocalLLMService.instance.loadModel(preferredModel)' in chat, 'send-time local runtime load missing')
require("if (!widget.initializing)" in chat and '_syncModelRouteState();' in chat, 'cold-start initializing race still present')
require('_handleApiKeyInput' not in chat, 'normal chat can still be consumed as an API key')
require("enabled: isPythonReady && !_isProcessing" in chat, 'input bar still depends on API-key entry mode')
require('MessageRole.toolProgress' in chat, 'tool activity does not have a dedicated region')
require('_currentToolEvents' in chat and '_toolProgressIndex' in chat, 'tool events are not aggregated per turn')
require("role: 'toolResult'" in chat, 'tool-process history is not persisted as one region')
require("attachments: !hasError && createdFiles != null" in chat, 'created files are not attached to final response region')
require("content: '\\u{1F4CE} File: $filePath'" not in chat, 'created files still create extra system-message rows')

bubble = (ROOT / 'lib/features/chat/presentation/widgets/message_bubble.dart').read_text(encoding='utf-8')
require('ExpansionTile(' not in bubble, 'diagnostics/thinking still use nested ExpansionTile semantics')
require('onTap: _toggle' in bubble and 'if (_expanded)' in bubble, 'expand/collapse is not owned by one real state variable')
require('思考模式：' not in bubble, 'thinking-mode debug prose still leaks into normal chat UI')
require('本轮AI未输出思考内容。' in bubble, 'empty/disabled thinking state has no explicit message')
require("semanticTitle: '思考过程'" in bubble, 'thinking toggle missing')
require("semanticTitle: '工具调用诊断'" in bubble, 'diagnostics toggle missing')
require("label: '${widget.semanticTitle}，当前$stateLabel，$actionLabel'" in bubble, 'toggle semantic state is not dynamic')
require("hint: '长按可打开消息操作'" not in bubble, 'repeated long-press accessibility hint still pollutes each row')
require('return ExcludeSemantics(' in bubble, 'decorative role symbols can still be announced')

skills_ui = (ROOT / 'lib/features/settings/tool_skills_screen.dart').read_text(encoding='utf-8')
for label in ('AnySearch', 'Exa', 'LangSearch', 'Tavily'):
    require(label in skills_ui, f'{label} API key UI missing')
require('obscureText: true' in skills_ui, 'search API keys are not masked')
require('现有密钥不会显示在屏幕上' in skills_ui, 'configured key UI may expose secret values')

storage = (ROOT / 'lib/core/services/storage_service.dart').read_text(encoding='utf-8')
require('_searchApiProviders' in storage and 'getConfiguredSearchApiKeys' in storage, 'secure search key storage missing')
bridge = (ROOT / 'lib/core/bridge/bridge.dart').read_text(encoding='utf-8')
require("'search_api_keys': searchApiKeys" in bridge, 'search keys are not injected into private execution context')

skill_model = (ROOT / 'lib/core/models/tool_skill.dart').read_text(encoding='utf-8')
require('v8SearchToolNames' in skill_model, 'v8 search tool catalog missing')
for skill_id in ('anysearch_search', 'exa_search', 'langsearch_search', 'tavily_search'):
    require(f"id: '{skill_id}'" in skill_model, f'independent search Skill missing: {skill_id}')

# Python registry completeness: 25 manual Skills, 37 canonical local functions.
from navixmind.tools import (  # noqa: E402
    OFFLINE_TOOLS_SCHEMA, LOCAL_SKILLS, get_enabled_tool_names,
    get_offline_tools_for_skills,
)
from navixmind.bridge import ToolError  # noqa: E402
from navixmind.tools.extended_tools import file_manage  # noqa: E402

schema_names = {item['name'] for item in OFFLINE_TOOLS_SCHEMA}
covered = get_enabled_tool_names(tuple(LOCAL_SKILLS.keys()))
require(len(LOCAL_SKILLS) == 25, f'expected 25 manual Skills, got {len(LOCAL_SKILLS)}')
require(len(schema_names) == 37, f'expected 37 canonical local functions, got {len(schema_names)}')
require(schema_names == covered, f'schema/Skill mismatch: schema-only={schema_names-covered}, skill-only={covered-schema_names}')
require(
    {x['name'] for x in get_offline_tools_for_skills(['anysearch_search'])} ==
    {'anysearch_search', 'anysearch_extract', 'anysearch_get_sub_domains'},
    'AnySearch Skill is bundled incorrectly or incomplete',
)
for skill_id, tool_name in (
    ('exa_search', 'exa_search'),
    ('langsearch_search', 'langsearch_search'),
    ('tavily_search', 'tavily_search'),
):
    require({x['name'] for x in get_offline_tools_for_skills([skill_id])} == {tool_name}, f'{skill_id} is not independent')

# Functional reproduction of v7 false-success delete: output/subfolder/file.txt.
with tempfile.TemporaryDirectory() as td:
    output = Path(td) / 'output'
    output.mkdir()
    file_manage('mkdir', path='nested', _output_dir=str(output))
    touched = file_manage('touch', path='nested/test.txt', _output_dir=str(output))['path']
    Path(touched).write_text('delete me', encoding='utf-8')
    require((output / 'nested' / 'test.txt').exists(), 'nested test file setup failed')
    deleted = file_manage('delete', path='output/nested', recursive=True, _output_dir=str(output))
    require(deleted['success'] is True and deleted['exists_after'] is False, 'delete did not report verified absence')
    require(not (output / 'nested').exists(), 'recursive delete returned but real output directory still exists')

    file_manage('mkdir', path='nested2', _output_dir=str(output))
    file_manage('touch', path='nested2/test2.txt', _output_dir=str(output))
    file_manage('delete', path='nested2', recursive=True, _output_dir=str(output))
    require(not (output / 'nested2').exists(), 'relative nested delete did not target the output root')

    try:
        file_manage('delete', path='does-not-exist', recursive=True, _output_dir=str(output))
    except ToolError:
        pass
    else:
        raise AssertionError('missing delete target still returns fake success')

# Reasoning sanitization: tool call payload can never appear as Thinking content.
from navixmind.agent import _sanitize_reasoning, _thinking_for_ui  # noqa: E402
raw_reasoning = '''先确认目标文件，再执行删除。\n<tool_call>{"name":"file_manage","arguments":{"action":"delete","path":"output/nested"}}</tool_call>\n删除后需要检查结果。'''
clean = _sanitize_reasoning(raw_reasoning)
require('file_manage' not in clean and '<tool_call>' not in clean, 'tool call leaked into thinking content')
require('先确认目标文件' in clean and '删除后需要检查结果' in clean, 'real reasoning was over-filtered')
require(_thinking_for_ui([clean], 'disabled') == '', '/no_think mode can still expose reasoning')
require(_thinking_for_ui([clean], 'enabled') == clean, 'enabled thinking was unexpectedly removed')

# Search provider functions: credentials come only from _context and requests are
# test-mocked so preflight never contacts external services.
import navixmind.tools.search_tools as st  # noqa: E402

class FakeResponse:
    ok = True
    status_code = 200
    text = ''
    def __init__(self, payload): self._payload = payload
    def json(self): return self._payload

calls = []
def fake_post(url, **kwargs):
    calls.append((url, kwargs))
    if 'anysearch' in url:
        return FakeResponse({'result': {'content': [{'type': 'text', 'text': 'any result'}]}})
    if 'exa.ai' in url:
        return FakeResponse({'results': [{'title': 'exa'}]})
    if 'langsearch' in url:
        return FakeResponse({'code': 200, 'data': {'webPages': {'value': [{'name': 'lang'}]}}})
    return FakeResponse({'answer': 'tavily answer', 'results': [{'title': 'tavily'}]})

st.requests.post = fake_post
ctx = {'search_api_keys': {'anysearch': 'a-secret', 'exa': 'e-secret', 'langsearch': 'l-secret', 'tavily': 't-secret'}}
require(st.anysearch_search('test', _context=ctx)['provider'] == 'anysearch', 'AnySearch adapter failed')
require(st.exa_search('test', _context=ctx)['provider'] == 'exa', 'Exa adapter failed')
require(st.langsearch_search('test', _context=ctx)['provider'] == 'langsearch', 'LangSearch adapter failed')
require(st.tavily_search('test', _context=ctx)['provider'] == 'tavily', 'Tavily adapter failed')
require(len(calls) == 4, 'search adapter mock did not execute all four providers')
try:
    st.tavily_search('test', _context={})
except ToolError:
    pass
else:
    raise AssertionError('search without configured API key did not fail clearly')

print('RastaCoder v8 validation passed: cold-start route gates, clean 3-region turn UI, verified delete, 25 Skills / 37 functions, four independent search providers.')
