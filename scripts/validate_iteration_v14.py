from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))

from navixmind import agent
from navixmind.tools import (
    ALL_LOCAL_SKILL_IDS,
    TOOLS_SCHEMA,
    get_enabled_tool_names,
    get_offline_tools_for_skills,
)
from navixmind.tools.compat import normalize_tool_call


def check(condition, message):
    if not condition:
        raise AssertionError(message)


# Catalogue invariants: V14 is a systemic hardening pass, not a tool removal pass.
check(len(ALL_LOCAL_SKILL_IDS) == 25, f'expected 25 Skills, got {len(ALL_LOCAL_SKILL_IDS)}')
canonical = get_enabled_tool_names(ALL_LOCAL_SKILL_IDS)
check(len(canonical) == 37, f'expected 37 canonical functions, got {len(canonical)}')

# Every projected local schema must remain ordinary strict JSON.
local_tools = get_offline_tools_for_skills(ALL_LOCAL_SKILL_IDS)
check(len({t['name'] for t in local_tools}) == 37, 'local projected schema lost canonical functions')
json.dumps(local_tools, ensure_ascii=False, allow_nan=False)

# Reproduce the field XLSX failure: Qwen used object braces for each row.
raw_excel = '''{"name":"create_xlsx","arguments":{"output_path":"models_comparison.xlsx","sheets":[{"sheet_name":"Models_Comparison","data":[{"Model","Country","Key_Features"},{"Qwen","China","Multi-lingual"}]}]}}'''
parsed = agent._parse_mapping(raw_excel)
check(isinstance(parsed, dict), 'Excel JSON-ish call did not parse')
rows = parsed['arguments']['sheets'][0]['data']
check(rows[0] == ['Model', 'Country', 'Key_Features'], f'brace-array order lost: {rows[0]!r}')
check(rows[1] == ['Qwen', 'China', 'Multi-lingual'], f'brace-array row order lost: {rows[1]!r}')
name, args, _ = normalize_tool_call(parsed['name'], parsed['arguments'])
check(name == 'create_xlsx', name)
check(isinstance(args['sheets'][0]['data'][0], list), 'create_xlsx row is not JSON array after normalization')
json.dumps(args, ensure_ascii=False, allow_nan=False)

# Reproduce the field PDF malformed-call failure. Bare keys must be rejected,
# never silently turned into null/empty PDF arguments.
raw_pdf = '''{"name":"create_pdf","arguments":{"output_path":"output.pdf","content","title","image_paths"}}'''
missing = agent._missing_json_value_keys(raw_pdf)
check(missing == ['content', 'title', 'image_paths'], f'unexpected bare keys: {missing}')
check(agent._try_parse_tool_json(raw_pdf, 0) is None, 'incomplete PDF call must enter bounded parser retry')

# Shared JSON boundary: nested Python-only containers from any executor may not
# kill the successful-tool -> model-finalization transition.
weird_result = {
    'success': True,
    'rows': ({'b', 'a'}, ('x', 'y')),
    'nested': {'set': {3, 1, 2}},
    'blob': b'hello',
}
safe = agent._json_boundary_safe(weird_result)
serialized = agent._json_boundary_dumps(weird_result, ensure_ascii=False)
check(isinstance(safe['rows'], list), safe)
check('"success": true' in serialized.lower(), serialized)
json.loads(serialized)

# Exercise the common post-tool prefill boundary for create/read classes,
# including PDF/XLSX. These must remain serializable even with set-like extras.
ctx = {'offline_model_info': {'display_name': 'Qwen3 4B'}, 'local_context_tokens': 32768}
for tool_name in ('create_pdf', 'read_pdf', 'create_xlsx', 'read_xlsx', 'create_docx', 'read_docx'):
    payload = agent._prepare_tool_result_for_model(
        tool_name,
        {'success': True, 'content': 'ok', 'metadata': {'flags': {'x', 'y'}}},
        ctx,
        2048,
    )
    check('TOOL_RESULT' in payload and 'status: succeeded' in payload, tool_name)

agent_src = (ROOT / 'python/navixmind/agent.py').read_text()
compat_src = (ROOT / 'python/navixmind/tools/compat.py').read_text()
native_src = (ROOT / 'lib/core/services/native_tool_executor.dart').read_text()
service_src = (ROOT / 'lib/core/services/local_llm_service.dart').read_text()
kotlin_src = (ROOT / 'android/app/src/main/kotlin/ai/navixmind/services/MLCInferenceChannel.kt').read_text()
chat_src = (ROOT / 'lib/features/chat/presentation/chat_screen.dart').read_text()
manager_src = (ROOT / 'lib/core/services/conversation_manager.dart').read_text()
history_src = (ROOT / 'lib/features/chat/presentation/conversation_history_screen.dart').read_text()

check('RASTACODER_V14_JSON_BOUNDARY' in agent_src, 'missing shared JSON boundary')
check('RASTACODER_V14_ORDERED_JSONISH_PARSER' in agent_src, 'missing ordered JSON-ish parser')
check('successful_tool_turns' in agent_src and 'empty_final_recovery' in agent_src, 'missing post-tool final response recovery')
check("result_str = json.dumps(result)" not in agent_src, 'unsafe result serialization survived')
check('RASTACODER_V14_CONTAINER_NORMALIZATION' in compat_src, 'missing all-tool container normalization')

# Streaming must traverse Python -> Dart native executor -> LocalLLMService ->
# Kotlin EventChannel -> ChatScreen. Internal helper calls default to false.
check('stream_to_ui: bool = False' in agent_src, 'LocalLLM stream default is not internal-safe')
check(agent_src.count('stream_to_ui=True') == 1, 'top-level stream opt-in count changed unexpectedly')
check("'stream_to_ui': bool(stream_to_ui)" in agent_src, 'Python native stream flag missing')
check('RASTACODER_V14_STREAM_FORWARD_NATIVE' in native_src and 'streamToUi: streamToUi' in native_src, 'native executor does not forward stream flag')
check('RASTACODER_V14_STREAM_SERVICE_FLAG' in service_src and "'streamToUi': streamToUi" in service_src, 'LocalLLMService does not forward stream flag')
check('RASTACODER_V14_EXPLICIT_UI_STREAM' in kotlin_src, 'Kotlin explicit stream gate missing')
check('if (streamToUi && !toolCallEmitted)' in kotlin_src, 'Kotlin delta emission is not explicitly UI-gated')
check('"phase" to "content_delta"' in kotlin_src, 'Kotlin content delta event missing')
check('RASTACODER_V14_FINAL_STREAMING' in chat_src, 'chat streaming draft missing')
check('RASTACODER_V14_STREAM_GENERATION_RESET' in chat_src, 'post-tool generation stream reset missing')
check("case 'content_delta':" in chat_src, 'ChatScreen does not consume token deltas')

# Clear-all history is additive: batch delete exists, accessible UI action exists,
# and legacy per-conversation deletion remains.
check('RASTACODER_V14_CLEAR_ALL_HISTORY' in manager_src, 'manager clear-all method missing')
check('Future<void> deleteAllConversations()' in manager_src, 'manager clear-all signature missing')
check('messages.clear()' in manager_src and 'conversations.clear()' in manager_src, 'clear-all is not one database transaction')
check('Future<void> deleteConversation(int conversationId)' in manager_src, 'single-conversation delete was removed')
check('RASTACODER_V14_CLEAR_ALL_HISTORY_UI' in history_src, 'history clear-all UI missing')
check("tooltip: '清除所有聊天记录'" in history_src, 'clear-all accessible tooltip missing')
check("if (value == 'delete') _delete(item);" in history_src, 'per-item delete UI was removed')

print('V14 validation passed: 25 Skills / 37 functions, JSON-safe shared boundary, ordered brace-array repair, incomplete-call rejection, post-tool finalization recovery, explicit UI token streaming, and clear-all history with single-delete retained.')
