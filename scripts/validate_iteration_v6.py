#!/usr/bin/env python3
"""RastaCoder v6 release-gate validator.

Runs after apply_iteration_v6*.py. It deliberately tests the failure classes
reported by the user across all 21 Skills / 23 canonical tools.
"""
from __future__ import annotations

import ast
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
errors: List[str] = []

EXPECTED_TOOLS = {
    'python_execute','ffmpeg_process','smart_crop','ocr_image','read_pdf','create_pdf',
    'read_file','write_file','file_info','create_zip','convert_document','create_docx',
    'read_docx','read_pptx','read_xlsx','web_fetch','headless_browser','download_media',
    'modify_docx','modify_pptx','modify_xlsx','google_calendar','gmail',
}
EXPECTED_SKILLS = {
    'text_files','zip_archive','pdf_read','pdf_create','document_convert','word','powerpoint','excel',
    'ocr','image_processing','video_processing','audio_processing','media_download','web_fetch','dynamic_web',
    'basic_calculation','scientific_calculation','data_analysis','charts','gmail','google_calendar',
}


def fail(msg: str) -> None:
    errors.append(msg)


def expect(condition: bool, msg: str) -> None:
    if not condition:
        fail(msg)


def load_literal_assignment(path: Path, name: str) -> Any:
    tree = ast.parse(path.read_text(encoding='utf-8'))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError(f'{name} assignment missing in {path}')


# ---------------------------------------------------------------------------
# Structural coverage: all 21 Skills, exact original 23 canonical functions.
# ---------------------------------------------------------------------------
tools_path = ROOT / 'python/navixmind/tools/__init__.py'
tools_text = tools_path.read_text(encoding='utf-8')
try:
    local_skills = load_literal_assignment(tools_path, 'LOCAL_SKILLS')
except Exception as exc:
    local_skills = {}
    fail(str(exc))

if local_skills:
    ids = set(local_skills)
    covered = {tool for skill in local_skills.values() for tool in skill['tools']}
    expect(ids == EXPECTED_SKILLS, f'21 Skill IDs mismatch missing={sorted(EXPECTED_SKILLS-ids)} extra={sorted(ids-EXPECTED_SKILLS)}')
    expect(len(local_skills) == 21, f'expected 21 Skills, got {len(local_skills)}')
    expect(covered == EXPECTED_TOOLS, f'23-tool coverage mismatch missing={sorted(EXPECTED_TOOLS-covered)} extra={sorted(covered-EXPECTED_TOOLS)}')

# The model prompt must not expose UI Skill IDs or teach generic "param" keys.
expect('RASTACODER_V6_TOOL_RELIABILITY' in tools_text, 'v6 tool-reliability marker missing')
expect('CALLABLE FUNCTIONS (these exact names only)' in tools_text, 'canonical callable-function prompt missing')
expect('Never call a Skill/category label' in tools_text, 'Skill/UI-name prohibition missing')
expect('Never invent generic argument keys such as param' in tools_text, 'generic-argument prohibition missing')
expect('ENABLED SKILLS:' not in tools_text, 'legacy model-facing Skill-ID heading still present')
expect('{"name":"tool_name","arguments":{"param":"value"}}' not in tools_text, 'unsafe generic param example still present')
# No loop should print selected Skill IDs into the local system prompt.
expect('lines.append(f"- {skill_id}' not in tools_text, 'Skill IDs are still interpolated into model prompt')

# ---------------------------------------------------------------------------
# Import the pure compatibility module and run the cross-Skill matrix.
# ---------------------------------------------------------------------------
compat_path = ROOT / 'python/navixmind/tools/compat.py'
spec = importlib.util.spec_from_file_location('v6_compat', compat_path)
compat = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(compat)
normalize = compat.normalize_tool_call

# Every UI Skill is exercised at least once. Multi-function Skills get several
# cases so their deterministic router cannot silently collapse capabilities.
skill_cases = [
    ('text_files', {'file_path':'notes.txt'}, 'read_file'),
    ('text_files', {'content':'hello'}, 'write_file'),
    ('text_files', {'param':'show file size notes.txt'}, 'file_info'),
    ('zip_archive', {'files':['a.txt']}, 'create_zip'),
    ('pdf_read', {'file':'paper.pdf'}, 'read_pdf'),
    ('pdf_create', {'content':'hello'}, 'create_pdf'),
    ('document_convert', {'param':'convert notes.txt to docx'}, 'convert_document'),
    ('word', {'content':'hello'}, 'create_docx'),
    ('word', {'docx_path':'a.docx'}, 'read_docx'),
    ('word', {'input_path':'a.docx','operations':[{'action':'add_paragraph','params':{'text':'x'}}]}, 'modify_docx'),
    ('powerpoint', {'pptx_path':'a.pptx'}, 'read_pptx'),
    ('powerpoint', {'input_path':'a.pptx','operations':[{'action':'add_slide','params':{}}]}, 'modify_pptx'),
    ('excel', {'xlsx_path':'a.xlsx'}, 'read_xlsx'),
    ('excel', {'input_path':'a.xlsx','operations':[{'action':'set_cell','params':{'cell':'A1','value':'x'}}]}, 'modify_xlsx'),
    ('ocr', {'file':'scan.png'}, 'ocr_image'),
    ('image_processing', {'input':'photo.jpg'}, 'smart_crop'),
    ('video_processing', {'input':'movie.mp4','operation':'trim','output':'clip.mp4','duration':'3'}, 'ffmpeg_process'),
    ('audio_processing', {'param':'convert analysis_article.mp3 to wav'}, 'ffmpeg_process'),
    ('media_download', {'url':'https://example.com/media'}, 'download_media'),
    ('web_fetch', {'url':'https://example.com'}, 'web_fetch'),
    ('dynamic_web', {'url':'https://example.com/app'}, 'headless_browser'),
    ('basic_calculation', {'code':'print(2+2)'}, 'python_execute'),
    ('scientific_calculation', {'code':'print(2+2)'}, 'python_execute'),
    ('data_analysis', {'code':'print(2+2)'}, 'python_execute'),
    ('charts', {'code':'print(2+2)'}, 'python_execute'),
    ('gmail', {'action':'list'}, 'gmail'),
    ('google_calendar', {'action':'list'}, 'google_calendar'),
]
seen_skills = set()
for skill, args, expected in skill_cases:
    seen_skills.add(skill)
    name, normalized_args, notes = normalize(skill, args)
    expect(name == expected, f'Skill route {skill} expected {expected}, got {name}; args={normalized_args}; notes={notes}')
expect(seen_skills == EXPECTED_SKILLS, f'Skill regression matrix incomplete: missing={sorted(EXPECTED_SKILLS-seen_skills)}')

# User's exact v5 audio failure must now become a canonical complete call.
ctx_audio = {
    '_current_files':['/files/analysis_article.mp3'],
    '_file_map':{'analysis_article.mp3':'/files/analysis_article.mp3'},
    'output_dir':'/output',
}
name, args, notes = normalize('audio_processing', {'param':'convert analysis_article.mp3 to wav'}, context=ctx_audio)
expect(name == 'ffmpeg_process', f'user audio sample name not repaired: {name}')
expect(args.get('input_path') == 'analysis_article.mp3' or str(args.get('input_path','')).endswith('/analysis_article.mp3'), f'user audio sample input missing: {args}')
expect(args.get('operation') == 'extract_audio', f'user audio sample should use extract_audio, got {args}')
expect(isinstance(args.get('params'), dict) and args['params'].get('format') == 'wav', f'user audio sample WAV target missing: {args}')
expect(str(args.get('output_path','')).endswith('.wav'), f'user audio sample output WAV not synthesized: {args}')
expect('param' not in args, f'generic param survived normalization: {args}')

# User's exact DOCX failure: content-only create_docx receives a safe filename.
name, args, notes = normalize('create_docx', {'content':'self introduction'}, context={'output_dir':'/output'})
expect(name == 'create_docx', 'create_docx canonical name changed unexpectedly')
expect(args.get('output_path') == 'document.docx', f'create_docx missing default output_path: {args}')

# Missing unique input attachment inference across every file-reading/editing family.
unique_cases = [
    ('read_pdf', {}, '/files/a.pdf', 'pdf_path'),
    ('read_docx', {}, '/files/a.docx', 'docx_path'),
    ('read_pptx', {}, '/files/a.pptx', 'pptx_path'),
    ('read_xlsx', {}, '/files/a.xlsx', 'xlsx_path'),
    ('ocr_image', {}, '/files/a.png', 'image_path'),
    ('read_file', {}, '/files/a.txt', 'file_path'),
    ('file_info', {}, '/files/a.bin', 'file_path'),
    ('ffmpeg_process', {'operation':'trim','params':{'duration':'1'}}, '/files/a.mp3', 'input_path'),
    ('smart_crop', {}, '/files/a.jpg', 'input_path'),
    ('convert_document', {'output_format':'docx'}, '/files/a.txt', 'input_path'),
    ('modify_docx', {'operations':[]}, '/files/a.docx', 'input_path'),
    ('modify_pptx', {'operations':[]}, '/files/a.pptx', 'input_path'),
    ('modify_xlsx', {'operations':[]}, '/files/a.xlsx', 'input_path'),
]
for tool, raw_args, path, key in unique_cases:
    ctx = {'_current_files':[path], '_file_map':{Path(path).name:path}}
    name, args, notes = normalize(tool, raw_args, context=ctx)
    expect(args.get(key) == path, f'{tool} failed unique attachment inference for {key}: {args}, {notes}')

# Safe output synthesis across creation/modification/media families.
def check_output(tool: str, raw_args: Dict[str, Any], suffix: str, ctx: Optional[Dict[str, Any]]=None) -> None:
    name, args, notes = normalize(tool, raw_args, context=ctx or {})
    expect(str(args.get('output_path','')).endswith(suffix), f'{tool} output default expected *{suffix}: {args}; {notes}')

check_output('create_pdf', {'content':'x'}, '.pdf', {})
check_output('write_file', {'content':'x'}, '.txt', {})
check_output('create_zip', {'file_paths':['a.txt']}, '.zip', {})
check_output('modify_docx', {'input_path':'a.docx','operations':[]}, '.docx', {})
check_output('modify_pptx', {'input_path':'a.pptx','operations':[]}, '.pptx', {})
check_output('modify_xlsx', {'input_path':'a.xlsx','operations':[]}, '.xlsx', {})
check_output('smart_crop', {'input_path':'a.jpg'}, '.jpg', {})

# Existing v4/v5 aliases remain supported.
alias_cases = [
    ('python', {'code':'print(1)'}, 'python_execute'),
    ('audio_edit', {'input_path':'a.mp3','output_path':'b.wav','operation':'extract_audio','format':'wav'}, 'ffmpeg_process'),
    ('video_edit', {'input_path':'a.mp4','output_path':'b.mp4','operation':'trim','duration':'1'}, 'ffmpeg_process'),
    ('create_word_document', {'content':'x'}, 'create_docx'),
    ('document_convert', {'input_path':'a.txt','format':'word'}, 'convert_document'),
    ('calendar', {'operation':'show'}, 'google_calendar'),
    ('email', {'operation':'search'}, 'gmail'),
]
for raw_name, raw_args, expected in alias_cases:
    name, args, notes = normalize(raw_name, raw_args)
    expect(name == expected, f'legacy alias regression {raw_name}->{name}, expected {expected}')

# Canonical names must remain canonical for all 23 tools.
for canonical in EXPECTED_TOOLS:
    name, _, _ = normalize(canonical, {})
    expect(name == canonical, f'canonical tool renamed unexpectedly: {canonical}->{name}')

# ---------------------------------------------------------------------------
# Parser extraction: execute only the relevant pure helper functions from
# agent.py so host CI does not need Chaquopy/runtime imports.
# ---------------------------------------------------------------------------
agent_path = ROOT / 'python/navixmind/agent.py'
agent_text = agent_path.read_text(encoding='utf-8')
expect("canonical, args, _ = normalize_tool_call(name, args)" in agent_text, 'agent parser does not normalize arguments before canonical-name validation')
expect("response['stop_reason'] = 'tool_parse_error'" in agent_text, 'unparseable tool-call wrapper retry state missing')
expect("response['_reasoning'] = _extract_reasoning_blocks" in agent_text, 'reasoning is not captured before parser cleanup')
expect("result[\"diagnostics\"] = _format_diagnostics(context)" in agent_text, 'final local diagnostics not returned')
expect("result[\"thinking\"] = \"\\n\\n\".join(reasoning_parts)" in agent_text, 'final local reasoning metadata not returned')

# Compile selected parser functions in isolation.
tree = ast.parse(agent_text)
selected_names = {
    '_parse_mapping','_coerce_tool_args','_extract_json_objects','_build_tool_use','_try_parse_tool_json',
}
selected_nodes = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in selected_names]
namespace: Dict[str, Any] = {
    'json': json,
    'Any': Any, 'Dict': Dict, 'List': List, 'Optional': Optional,
    'TOOLS_SCHEMA': [{'name': name} for name in EXPECTED_TOOLS],
    'normalize_tool_call': normalize,
    'normalize_tool_name': compat.normalize_tool_name,
}
try:
    exec(compile(ast.Module(body=selected_nodes, type_ignores=[]), str(agent_path), 'exec'), namespace)
    parsed = namespace['_try_parse_tool_json'](
        '{"name":"audio_processing","arguments":{"param":"convert analysis_article.mp3 to wav"}}', 0
    )
    expect(isinstance(parsed, dict), f'parser failed user audio JSON: {parsed}')
    if isinstance(parsed, dict):
        expect(parsed.get('name') == 'ffmpeg_process', f'parser did not canonicalize user audio Skill name: {parsed}')
        expect(parsed.get('input',{}).get('operation') == 'extract_audio', f'parser did not repair audio operation: {parsed}')
except Exception as exc:
    fail(f'isolated agent parser test failed: {exc}')

# ---------------------------------------------------------------------------
# UI / observability gates.
# ---------------------------------------------------------------------------
chat = (ROOT/'lib/features/chat/presentation/chat_screen.dart').read_text(encoding='utf-8')
bubble = (ROOT/'lib/features/chat/presentation/widgets/message_bubble.dart').read_text(encoding='utf-8')
for needle in [
    "response.result!['thinking']", "response.result!['thinking_mode']", "response.result!['diagnostics']",
    'final String? thinking;', 'final String? thinkingMode;', 'final String? diagnostics;',
]:
    expect(needle in chat, f'chat metadata plumbing missing: {needle}')
for needle in [
    '工具调用诊断（点击展开）', '复制诊断日志', '分享诊断日志',
    '思考过程（点击展开）', '思考模式：$modeLabel', 'message.thinking', 'message.diagnostics',
]:
    expect(needle in bubble, f'message bubble observability missing: {needle}')
expect('Share.share' in bubble and 'Clipboard.setData' in bubble, 'diagnostics copy/share implementation missing')

# Existing manual settings must remain independent.
expect("context.get('local_thinking_mode'" in agent_text, 'manual thinking setting missing')
for pattern in ('enabled_skills.*thinking_mode', 'thinking_mode.*enabled_skills'):
    import re
    if re.search(pattern, agent_text, flags=re.I):
        fail('thinking mode appears coupled to enabled skills')

# Diagnostics must include explicit secret redaction logic.
expect('[REDACTED]' in agent_text, 'agent diagnostics redaction marker missing')
expect('[REDACTED]' in tools_text, 'tool diagnostics redaction marker missing')

if errors:
    print('V6 VALIDATION FAILED:')
    for error in errors:
        print(' -', error)
    sys.exit(1)

print('V6 validation passed: all 21 Skills / 23 canonical tools covered; user regression samples repaired; parser leak guard, Thinking visibility and copy/share diagnostics present.')
