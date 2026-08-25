#!/usr/bin/env python3
from pathlib import Path
import ast
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
MARKER = "RASTACODER_V5_SKILLS_PARAMS_BENCH_STREAM"
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
FILES = [
    'python/navixmind/agent.py',
    'python/navixmind/tools/__init__.py',
    'lib/core/models/tool_skill.dart',
    'lib/core/services/storage_service.dart',
    'lib/core/bridge/bridge.dart',
    'lib/core/services/local_llm_service.dart',
    'lib/core/services/native_tool_executor.dart',
    'lib/features/chat/presentation/chat_screen.dart',
    'lib/features/chat/presentation/widgets/input_bar.dart',
    'lib/features/chat/presentation/widgets/status_banner.dart',
    'lib/features/settings/settings_screen.dart',
    'lib/features/settings/tool_skills_screen.dart',
    'lib/features/settings/local_model_parameters_screen.dart',
    'lib/features/settings/local_model_benchmark_screen.dart',
    'android/app/src/main/kotlin/ai/navixmind/services/MLCInferenceChannel.kt',
]

errors=[]
for rel in FILES:
    p=ROOT/rel
    if not p.exists(): errors.append(f'missing file: {rel}'); continue
    text=p.read_text(encoding='utf-8')
    if MARKER not in text: errors.append(f'missing v5 marker: {rel}')

# Parse Python canonical LOCAL_SKILLS as a literal and verify exactly 21 ids / 23 functions.
tools_text=(ROOT/'python/navixmind/tools/__init__.py').read_text(encoding='utf-8')
tree=ast.parse(tools_text)
local_skills=None
for node in tree.body:
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id=='LOCAL_SKILLS' for t in node.targets):
        local_skills=ast.literal_eval(node.value); break
if local_skills is None:
    errors.append('LOCAL_SKILLS assignment missing')
else:
    ids=set(local_skills)
    covered={name for skill in local_skills.values() for name in skill['tools']}
    if ids != EXPECTED_SKILLS:
        errors.append(f'skill id mismatch missing={sorted(EXPECTED_SKILLS-ids)} extra={sorted(ids-EXPECTED_SKILLS)}')
    if len(local_skills) != 21:
        errors.append(f'expected 21 skills, got {len(local_skills)}')
    if covered != EXPECTED_TOOLS:
        errors.append(f'tool coverage mismatch missing={sorted(EXPECTED_TOOLS-covered)} extra={sorted(covered-EXPECTED_TOOLS)}')

agent=(ROOT/'python/navixmind/agent.py').read_text(encoding='utf-8')
checks={
    'dynamic skill prompt':'build_offline_skill_prompt(enabled_skills)',
    'dynamic local schema':'get_offline_tools_for_skills(enabled_skills)',
    'manual skills context':"context.get('enabled_skills')",
    'manual thinking setting':"context.get('local_thinking_mode'",
    'exact local context':"context.get('local_context_tokens'",
    'exact local output':"context.get('local_max_output_tokens'",
    'temperature':"context.get('local_temperature'",
    'top-p':"context.get('local_top_p'",
}
for label, needle in checks.items():
    if needle not in agent: errors.append(f'agent missing {label}')
if 'FFMPEG PATTERNS:' in agent:
    errors.append('legacy all-tool FFmpeg pattern block still present in agent prompt')
if 'tools_schema = OFFLINE_TOOLS_SCHEMA if is_offline else TOOLS_SCHEMA' in agent:
    errors.append('legacy full offline schema injection still present')
dependency_patterns = [
    r'(?:thinking_mode|directive)\s*=.*enabled_skills',
    r'if\s+[^\n]*enabled_skills[^\n]*(?:thinking|/think|/no_think)',
    r'if\s+[^\n]*(?:thinking|/think|/no_think)[^\n]*enabled_skills',
]
if any(re.search(pattern, agent, flags=re.I) for pattern in dependency_patterns):
    errors.append('thinking mode appears to be inferred from enabled skills')

exec_text=tools_text
if '[MODEL_TOOL_DISABLED]' not in exec_text or "context.get('_allowed_tools')" not in exec_text:
    errors.append('execution-layer disabled-tool boundary missing')

input_bar=(ROOT/'lib/features/chat/presentation/widgets/input_bar.dart').read_text(encoding='utf-8')
if input_bar.find("icon: 'tools'") > input_bar.find('// Send button / processing indicator'):
    errors.append('tool manager is not immediately before send control')

params=(ROOT/'lib/features/settings/local_model_parameters_screen.dart').read_text(encoding='utf-8')
for needle in ['FilteringTextInputFormatter.digitsOnly', "suffix: 'Token'", "'model_default'", "'enabled'", "'disabled'"]:
    if needle not in params: errors.append(f'parameter page missing {needle}')
if 'Slider(' in params:
    errors.append('parameter page contains forbidden slider')

bench=(ROOT/'lib/features/settings/local_model_benchmark_screen.dart').read_text(encoding='utf-8')
for needle in ['prefill_tokens_per_s','decode_tokens_per_s','ttft_ms','end_to_end_ms','保存结果','复制到剪贴板','Clipboard.setData']:
    if needle not in bench: errors.append(f'benchmark missing {needle}')

kotlin=(ROOT/'android/app/src/main/kotlin/ai/navixmind/services/MLCInferenceChannel.kt').read_text(encoding='utf-8')
for needle in ['mlc_inference_events','generation_started','first_token','thinking_started','tool_call_started','generation_completed','runBenchmark','prefill_tokens_per_s','decode_tokens_per_s','Debug.getPss()','top_p = topP','temperature = temperature']:
    if needle not in kotlin: errors.append(f'Kotlin MLC missing {needle}')

chat=(ROOT/'lib/features/chat/presentation/chat_screen.dart').read_text(encoding='utf-8')
if "'enabled_skills': _enabledSkills.toList()" not in chat:
    errors.append('chat does not pass session-local skill selection')
if 'inferenceEventStream' not in chat:
    errors.append('chat does not listen to MLC telemetry')

storage=(ROOT/'lib/core/services/storage_service.dart').read_text(encoding='utf-8')
for needle in ['getLocalEnabledSkills','getLocalTemperature','getLocalTopP','getLocalContextTokens','getLocalMaxOutputTokens','getLocalThinkingMode','getLocalBenchmarkHistory','appendLocalBenchmarkResult']:
    if needle not in storage: errors.append(f'storage missing {needle}')

if errors:
    print('V5 VALIDATION FAILED:')
    for err in errors: print(' -',err)
    sys.exit(1)
print('V5 validation passed: 21 skills exactly cover all 23 original local tools; manual controls, benchmark and stream telemetry are present.')
