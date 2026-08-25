#!/usr/bin/env python3
"""Deep v6 release gate for prompt isolation, parser leakage and edge aliases."""
from __future__ import annotations

import ast
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
errors: List[str] = []


def expect(value: Any, message: str) -> None:
    if not value:
        errors.append(message)


def literal_assignment(path: Path, name: str) -> Any:
    tree = ast.parse(path.read_text(encoding='utf-8'))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError(f'{name} not found in {path}')


# ---------------------------------------------------------------------------
# Canonical schemas, Skill coverage, and model-facing prompt isolation.
# ---------------------------------------------------------------------------
tools_path = ROOT / 'python/navixmind/tools/__init__.py'
tools_text = tools_path.read_text(encoding='utf-8')
tools_schema = literal_assignment(tools_path, 'TOOLS_SCHEMA')
local_skills = literal_assignment(tools_path, 'LOCAL_SKILLS')
prompt_hints = literal_assignment(tools_path, 'LOCAL_TOOL_PROMPT_HINTS')
schemas = {item['name']: item['input_schema'] for item in tools_schema}
expected_tools = {
    'python_execute','ffmpeg_process','smart_crop','ocr_image','read_pdf','create_pdf',
    'read_file','write_file','file_info','create_zip','convert_document','create_docx',
    'read_docx','read_pptx','read_xlsx','web_fetch','headless_browser','download_media',
    'modify_docx','modify_pptx','modify_xlsx','google_calendar','gmail',
}
expect(set(schemas) == expected_tools, 'deep gate: canonical schema set changed')
expect(set(prompt_hints) == expected_tools, 'deep gate: prompt hint set is not exactly 23 canonical tools')

for tool, schema in schemas.items():
    hint = prompt_hints.get(tool, '')
    expect(tool in hint, f'prompt hint does not name canonical function {tool}: {hint}')
    for required in schema.get('required', []):
        expect(required in hint, f'prompt hint for {tool} omits required parameter {required}: {hint}')

# Execute only the pure prompt-selection helpers in isolation.
tree = ast.parse(tools_text)
prompt_fn_names = {'_offline_tool_names','get_enabled_tool_names','get_offline_tools_for_skills','build_offline_skill_prompt'}
prompt_nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in prompt_fn_names]
prompt_ns: Dict[str, Any] = {
    'OFFLINE_TOOLS_SCHEMA': tools_schema,
    'LOCAL_SKILLS': local_skills,
    'ALL_LOCAL_SKILL_IDS': tuple(local_skills.keys()),
    'LOCAL_TOOL_PROMPT_HINTS': prompt_hints,
}
exec(compile(ast.Module(body=prompt_nodes, type_ignores=[]), str(tools_path), 'exec'), prompt_ns)
for skill_id, spec in local_skills.items():
    prompt = prompt_ns['build_offline_skill_prompt']([skill_id])
    enabled = set(spec['tools'])
    expect('ENABLED SKILLS:' not in prompt, f'{skill_id}: legacy Skill heading leaked into prompt')
    expect('{"name":"tool_name","arguments":{"param":"value"}}' not in prompt, f'{skill_id}: generic param example leaked')
    for ui_id in local_skills:
        expect(f'- {ui_id}:' not in prompt, f'{skill_id}: UI Skill label {ui_id} leaked into model prompt')
    for tool in expected_tools:
        signature_marker = f'- {tool}('
        if tool in enabled:
            expect(signature_marker in prompt, f'{skill_id}: enabled canonical tool signature missing: {tool}')
        else:
            expect(signature_marker not in prompt, f'{skill_id}: disabled canonical tool leaked into single-Skill prompt: {tool}')

# ---------------------------------------------------------------------------
# Pure compatibility layer edge cases.
# ---------------------------------------------------------------------------
compat_path = ROOT / 'python/navixmind/tools/compat.py'
spec = importlib.util.spec_from_file_location('v6_deep_compat', compat_path)
compat = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(compat)
normalize = compat.normalize_tool_call

edge_cases = [
    ('write_file', {'filename':'note.txt','text':'hello'}, {}, 'write_file', {'output_path':'note.txt','content':'hello'}),
    ('create_docx', {'filename':'note.docx','body':'hello'}, {}, 'create_docx', {'output_path':'note.docx','content':'hello'}),
    ('web_fetch', {'link':'https://example.com'}, {}, 'web_fetch', {'url':'https://example.com'}),
    ('dynamic_web', {'website':'https://example.com/app'}, {}, 'headless_browser', {'url':'https://example.com/app'}),
    ('smart_crop', {'input_path':'photo.jpg','ratio':'16/9'}, {}, 'smart_crop', {'aspect_ratio':'16:9'}),
    ('media_download', {'url':'https://example.com/a','format':'mp3'}, {}, 'download_media', {'format':'audio'}),
    ('word', {'param':'open notes.docx'}, {}, 'read_docx', {'docx_path':'notes.docx'}),
    ('zip_archive', {'param':'zip a.txt b.txt to bundle.zip'}, {}, 'create_zip', {'output_path':'bundle.zip'}),
    ('document_convert', {'param':'convert notes.txt to converted.docx'}, {}, 'convert_document', {'input_path':'notes.txt','output_path':'converted.docx','output_format':'docx'}),
    ('ffmpeg_process', {'input_path':'song.mp3','output_path':'song.wav','target_format':'wav'}, {}, 'ffmpeg_process', {'operation':'extract_audio'}),
    ('modify_docx', {'input_path':'a.docx','action':'append','text':'hello'}, {}, 'modify_docx', {}),
    ('google_calendar', {'action':'create','title':'Lesson','start':'2026-08-26T09:00','end':'2026-08-26T10:00'}, {}, 'google_calendar', {}),
    ('python_execute', {'query':'print(2+2)'}, {}, 'python_execute', {'code':'print(2+2)'}),
]
for raw_name, raw_args, ctx, expected_name, expected_args in edge_cases:
    name, repaired, notes = normalize(raw_name, raw_args, context=ctx)
    expect(name == expected_name, f'edge route {raw_name}->{name}, expected {expected_name}; {repaired}; {notes}')
    for key, value in expected_args.items():
        expect(repaired.get(key) == value, f'{raw_name}: expected {key}={value!r}, got {repaired}; repairs={notes}')

# Specific nested checks.
_, zip_args, _ = normalize('zip_archive', {'param':'zip a.txt b.txt to bundle.zip'}, context={})
expect(zip_args.get('file_paths') == ['a.txt','b.txt'], f'ZIP output was not excluded from source list: {zip_args}')
_, ff_args, _ = normalize('ffmpeg_process', {'input_path':'song.mp3','output_path':'song.wav','target_format':'wav'}, context={})
expect(ff_args.get('params',{}).get('format') == 'wav', f'FFmpeg target format not nested into params: {ff_args}')
_, mod_args, _ = normalize('modify_docx', {'input_path':'a.docx','action':'append','text':'hello'}, context={})
expect(isinstance(mod_args.get('operations'), list) and mod_args['operations'][0].get('action') == 'add_paragraph', f'DOCX simple action not wrapped: {mod_args}')
expect(mod_args['operations'][0].get('params',{}).get('text') == 'hello', f'DOCX simple action params lost: {mod_args}')
_, cal_args, _ = normalize('google_calendar', {'action':'create','title':'Lesson','start':'2026-08-26T09:00','end':'2026-08-26T10:00'}, context={})
expect(cal_args.get('event',{}).get('title') == 'Lesson' and 'start' in cal_args.get('event',{}), f'Calendar top-level event not wrapped: {cal_args}')

# ---------------------------------------------------------------------------
# Full text-parser behavior: no recognizable tool wrapper may escape as final
# prose, and raw model calls must be preserved before canonical repair.
# ---------------------------------------------------------------------------
agent_path = ROOT / 'python/navixmind/agent.py'
agent_text = agent_path.read_text(encoding='utf-8')
agent_tree = ast.parse(agent_text)
helper_names = {'_parse_mapping','_coerce_tool_args','_extract_json_objects','_build_tool_use','_try_parse_tool_json','_try_parse_function_syntax'}
agent_nodes = [n for n in agent_tree.body if isinstance(n, ast.FunctionDef) and n.name in helper_names]
client_node = next(n for n in agent_tree.body if isinstance(n, ast.ClassDef) and n.name == 'LocalLLMClient')
parser_ns: Dict[str, Any] = {
    'json': json,
    'Any': Any, 'Dict': Dict, 'List': List, 'Optional': Optional,
    'TOOLS_SCHEMA': tools_schema,
    'OFFLINE_SYSTEM_PROMPT': '',
    'normalize_tool_call': normalize,
    'normalize_tool_name': compat.normalize_tool_name,
    'get_bridge': lambda: None,
    'CrashLogger': type('CrashLogger', (), {'log_error': staticmethod(lambda *a, **k: None)}),
    'APIError': Exception,
    'ToolError': Exception,
}
exec(compile(ast.Module(body=agent_nodes + [client_node], type_ignores=[]), str(agent_path), 'exec'), parser_ns)
parse_text = parser_ns['LocalLLMClient']._parse_tool_calls_from_text

samples = [
    ('<tool_call>{"name":"text_files","arguments":{"param":"write hello to note.txt"}}</tool_call>', 'write_file'),
    ('<tool_call>{"name":"word","arguments":{"content":"hello"}}</tool_call>', 'create_docx'),
    ('<tool_call>{"name":"audio_processing","arguments":"convert song.mp3 to wav"}</tool_call>', 'ffmpeg_process'),
    ('<tool_call>{"name":"zip_archive","arguments":{"param":"zip a.txt b.txt to bundle.zip"}}</tool_call>', 'create_zip'),
    ('<tool_call>{"name":"web_fetch","arguments":{"link":"https://example.com"}}</tool_call>', 'web_fetch'),
]
for raw, expected_name in samples:
    parsed = parse_text({'stop_reason':'end_turn','content':[{'type':'text','text':raw}]})
    expect(parsed.get('stop_reason') == 'tool_use', f'full parser failed to enter tool_use for {raw}: {parsed}')
    tool_blocks = [b for b in parsed.get('content',[]) if isinstance(b,dict) and b.get('type') == 'tool_use']
    expect(len(tool_blocks) == 1, f'full parser expected one tool block for {raw}: {parsed}')
    if tool_blocks:
        block = tool_blocks[0]
        expect(block.get('name') == expected_name, f'full parser canonical name mismatch {expected_name}: {block}')
        expect(block.get('_raw_name'), f'full parser lost raw model tool name: {block}')
        expect('_raw_input' in block and '_raw_source' in block and '_parser_repairs' in block, f'full parser diagnostics metadata incomplete: {block}')
    text_blocks = [str(b.get('text','')) for b in parsed.get('content',[]) if isinstance(b,dict) and b.get('type') == 'text']
    expect(all('<tool_call' not in t.lower() and '</tool_call' not in t.lower() for t in text_blocks), f'tool wrapper leaked into parsed text: {parsed}')

# Unterminated wrapper with valid JSON must still execute and strip the orphan tag.
unterminated_valid = '<tool_call>\n{"name":"text_files","arguments":{"param":"write hello to note.txt"}}'
parsed = parse_text({'stop_reason':'end_turn','content':[{'type':'text','text':unterminated_valid}]})
expect(parsed.get('stop_reason') == 'tool_use', f'unterminated valid wrapper not recovered: {parsed}')
expect(all('<tool_call' not in str(b.get('text','')).lower() for b in parsed.get('content',[]) if isinstance(b,dict) and b.get('type') == 'text'), f'orphan tool tag leaked after recovery: {parsed}')

# Unterminated invalid wrapper is classified for bounded retry and never final prose.
unterminated_bad = '<tool_call>{"name":'
parsed = parse_text({'stop_reason':'end_turn','content':[{'type':'text','text':unterminated_bad}]})
expect(parsed.get('stop_reason') == 'tool_parse_error', f'unterminated malformed wrapper did not become parse error: {parsed}')
expect(bool(parsed.get('_tool_parse_error')), f'parse-error raw preview missing: {parsed}')

# Raw-string arguments must survive _coerce_tool_args.
coerced = parser_ns['_coerce_tool_args']('convert song.mp3 to wav')
expect(coerced.get('param') == 'convert song.mp3 to wav', f'raw string argument was dropped: {coerced}')

# Diagnostic plumbing must expose original + repaired calls and redact secrets.
for needle in ["'_raw_name'", "'_raw_input'", "'_raw_source'", "'_parser_repairs'", "'raw_name':", "'raw_args':", "'raw_source':", '[REDACTED]']:
    expect(needle in agent_text, f'deep diagnostic marker missing: {needle}')

# ---------------------------------------------------------------------------
# Thinking directive visibility and persistent-history attachment integrity.
# ---------------------------------------------------------------------------
bubble = (ROOT/'lib/features/chat/presentation/widgets/message_bubble.dart').read_text(encoding='utf-8')
for needle in ['本轮已向 Qwen3 发送 /think', '本轮已向 Qwen3 发送 /no_think', '思考过程（点击展开）']:
    expect(needle in bubble, f'Thinking directive observability missing: {needle}')

bridge = (ROOT/'lib/core/bridge/bridge.dart').read_text(encoding='utf-8')
chat = (ROOT/'lib/features/chat/presentation/chat_screen.dart').read_text(encoding='utf-8')
manager = (ROOT/'lib/core/services/conversation_manager.dart').read_text(encoding='utf-8')
expect('persistAttachedFilesForConversation' in bridge, 'history attachments are not persisted through public Bridge helper')
for needle in ['persistAttachedFilesForConversation(originalAttachments)', 'filePaths: userAttachments', 'attachmentPaths: !hasError && createdFiles != null']:
    expect(needle in chat, f'durable conversation file wiring missing: {needle}')
expect("'attachments': m.attachments.map((a) => a.localPath)" in manager, 'history reload does not surface persisted attachment paths')

if errors:
    print('V6 DEEP VALIDATION FAILED:')
    for error in errors:
        print(' -', error)
    sys.exit(1)
print('V6 deep validation passed: single-Skill prompt isolation, canonical required signatures, edge aliases, raw-string/parser leakage recovery, true raw diagnostics, Thinking directives and durable history attachments are all gated.')
