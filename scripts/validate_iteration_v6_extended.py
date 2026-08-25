#!/usr/bin/env python3
"""Extended v6 release gate: full canonical-argument, TXT and history checks."""
from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
errors = []


def expect(value, message):
    if not value:
        errors.append(message)


def literal_assignment(path: Path, name: str):
    tree = ast.parse(path.read_text(encoding='utf-8'))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError(f'{name} not found in {path}')


# Import only the pure compatibility module after v6 patches have been applied.
compat_path = ROOT / 'python/navixmind/tools/compat.py'
spec = importlib.util.spec_from_file_location('v6_compat_extended', compat_path)
compat = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(compat)
normalize = compat.normalize_tool_call

# Exact systemic TXT-family reproduction: UI Skill name + generic param +
# hallucination-prone output form must become a complete write_file call.
name, args, notes = normalize(
    'text_files',
    {'param': 'write hello from RastaCoder to reliability_test.txt'},
    context={'output_dir': '/output'},
)
expect(name == 'write_file', f'TXT Skill did not route to write_file: {name}, {args}, {notes}')
expect(args.get('output_path') == 'reliability_test.txt', f'TXT output filename not recovered: {args}, {notes}')
expect(args.get('content') == 'hello from RastaCoder', f'TXT content not recovered: {args}, {notes}')
expect('param' not in args, f'TXT generic param leaked through normalization: {args}')

# Same generic failure class must be repaired for DOCX/PDF creation too.
for raw_name, raw, canonical, suffix in [
    ('word', {'param': 'write hello word to sample.docx'}, 'create_docx', '.docx'),
    ('pdf_create', {'param': 'write hello pdf to sample.pdf'}, 'create_pdf', '.pdf'),
]:
    n, a, repair = normalize(raw_name, raw, context={'output_dir':'/output'})
    expect(n == canonical, f'{raw_name} did not route to {canonical}: {n}, {a}, {repair}')
    expect(str(a.get('output_path','')).endswith(suffix), f'{raw_name} output missing: {a}')
    expect(bool(a.get('content')), f'{raw_name} content missing after freeform recovery: {a}')
    expect('param' not in a, f'{raw_name} generic param survived: {a}')

# Parse the canonical schemas and prove one representative normalized call for
# every one of the 23 functions satisfies all top-level required parameters.
tools_path = ROOT / 'python/navixmind/tools/__init__.py'
tools_text = tools_path.read_text(encoding='utf-8')
tools_schema = literal_assignment(tools_path, 'TOOLS_SCHEMA')
schemas = {item['name']: item['input_schema'] for item in tools_schema}
expected = {
    'python_execute','ffmpeg_process','smart_crop','ocr_image','read_pdf','create_pdf',
    'read_file','write_file','file_info','create_zip','convert_document','create_docx',
    'read_docx','read_pptx','read_xlsx','web_fetch','headless_browser','download_media',
    'modify_docx','modify_pptx','modify_xlsx','google_calendar','gmail',
}
expect(set(schemas) == expected, f'Canonical schema set changed: missing={sorted(expected-set(schemas))}, extra={sorted(set(schemas)-expected)}')

cases = {
    'python_execute': ({'code':'print(1)'}, {}),
    'ffmpeg_process': ({'param':'convert song.mp3 to wav'}, {'_current_files':['/files/song.mp3'], '_file_map':{'song.mp3':'/files/song.mp3'}}),
    'smart_crop': ({}, {'_current_files':['/files/photo.jpg']}),
    'ocr_image': ({}, {'_current_files':['/files/scan.png']}),
    'read_pdf': ({}, {'_current_files':['/files/paper.pdf']}),
    'create_pdf': ({'content':'hello'}, {}),
    'read_file': ({}, {'_current_files':['/files/notes.txt']}),
    'write_file': ({'content':'hello'}, {}),
    'file_info': ({}, {'_current_files':['/files/data.bin']}),
    'create_zip': ({'file_paths':['/files/a.txt']}, {}),
    'convert_document': ({'param':'convert notes.txt to docx'}, {'_current_files':['/files/notes.txt']}),
    'create_docx': ({'content':'hello'}, {}),
    'read_docx': ({}, {'_current_files':['/files/a.docx']}),
    'read_pptx': ({}, {'_current_files':['/files/a.pptx']}),
    'read_xlsx': ({}, {'_current_files':['/files/a.xlsx']}),
    'web_fetch': ({'url':'https://example.com'}, {}),
    'headless_browser': ({'url':'https://example.com'}, {}),
    'download_media': ({'url':'https://example.com/media'}, {}),
    'modify_docx': ({'operations':[{'action':'add_paragraph','params':{'text':'x'}}]}, {'_current_files':['/files/a.docx']}),
    'modify_pptx': ({'operations':[{'action':'add_slide','params':{}}]}, {'_current_files':['/files/a.pptx']}),
    'modify_xlsx': ({'operations':[{'action':'set_cell','params':{'cell':'A1','value':'x'}}]}, {'_current_files':['/files/a.xlsx']}),
    'google_calendar': ({'action':'list'}, {}),
    'gmail': ({'action':'list'}, {}),
}
expect(set(cases) == expected, f'Representative 23-tool matrix incomplete: {sorted(expected-set(cases))}')
for tool in sorted(expected):
    raw_args, ctx = cases[tool]
    n, repaired, notes = normalize(tool, raw_args, context=ctx)
    expect(n == tool, f'Canonical representative renamed {tool}->{n}: {repaired}, {notes}')
    missing = [key for key in schemas[tool].get('required', []) if repaired.get(key) in (None, '')]
    expect(not missing, f'{tool} representative still misses required {missing}: {repaired}; repairs={notes}')

# The model-facing prompt must contain every currently enabled canonical tool's
# exact signature source and never expose the UI Skill IDs.
expect('LOCAL_TOOL_PROMPT_HINTS' in tools_text, 'Canonical prompt-hint dictionary missing')
expect('ENABLED SKILLS:' not in tools_text, 'Model-facing Skill heading survived v6')
for skill_id in ('text_files','audio_processing','video_processing','word','powerpoint','excel'):
    prompt_section = tools_text[tools_text.find('def build_offline_skill_prompt'):]
    expect(f'lines.append(f"- {skill_id}' not in prompt_section, f'Skill ID {skill_id} is interpolated into model prompt')

# MLC structured tool calls must accumulate by streamed call index, not map size.
kotlin = (ROOT/'android/app/src/main/kotlin/ai/navixmind/services/MLCInferenceChannel.kt').read_text(encoding='utf-8')
expect('forEachIndexed { index, tc ->' in kotlin, 'MLC tool calls are not indexed by streamed call index')
expect('toolCallAccumulators.getOrPut(index)' in kotlin, 'MLC tool accumulator does not reuse call index')
expect('merged.putAll(args)' in kotlin, 'MLC streamed argument fragments are not merged')
expect('getOrPut(toolCallAccumulators.size)' not in kotlin, 'Legacy broken MLC per-fragment accumulator still present')

# Persistent chat lifecycle must use the pre-existing Isar data layer and sync
# the chosen conversation back to Python SessionState.
main = (ROOT/'lib/main.dart').read_text(encoding='utf-8')
manager = (ROOT/'lib/core/services/conversation_manager.dart').read_text(encoding='utf-8')
chat = (ROOT/'lib/features/chat/presentation/chat_screen.dart').read_text(encoding='utf-8')
history_path = ROOT/'lib/features/chat/presentation/conversation_history_screen.dart'
expect('ConversationManager.instance.initialize(isar)' in main, 'ConversationManager is still not initialized')
for needle in [
    'listConversationSummaries', 'getVisibleMessages', 'storeVisibleMessage',
    'renameConversation', 'deleteConversation', "'action': 'sync_full'", "'action': 'new_conversation'",
]:
    expect(needle in manager, f'ConversationManager history lifecycle missing {needle}')
for needle in [
    '_initializeConversationHistory', '_startNewConversation', '_openConversationHistory',
    'ConversationHistoryScreen', "tooltip: '聊天记录'", "tooltip: '新建对话'",
    'storeVisibleMessage', 'loadConversation(id)', '_conversationId',
]:
    expect(needle in chat, f'Chat history wiring missing {needle}')
expect(history_path.exists(), 'Conversation history screen file missing')
if history_path.exists():
    history = history_path.read_text(encoding='utf-8')
    for needle in ['聊天记录', '重命名', '删除', 'currentConversationId', 'Semantics(']:
        expect(needle in history, f'History UI/accessibility missing {needle}')

# Thinking and tool diagnostics remain mandatory together with chat history.
bubble = (ROOT/'lib/features/chat/presentation/widgets/message_bubble.dart').read_text(encoding='utf-8')
for needle in ['思考过程（点击展开）', '工具调用诊断（点击展开）', '复制诊断日志', '分享诊断日志']:
    expect(needle in bubble, f'Observability surface regressed while adding history: {needle}')

if errors:
    print('V6 EXTENDED VALIDATION FAILED:')
    for error in errors:
        print(' -', error)
    sys.exit(1)
print('V6 extended validation passed: TXT/DOCX/PDF free-form recovery, all 23 required-argument representatives, MLC accumulation, Thinking/diagnostics and persistent multi-conversation lifecycle are present.')
