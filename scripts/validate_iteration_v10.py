from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))

from navixmind.agent import (
    _tool_result_char_budget,
    _prepare_tool_result_for_model,
    _tool_error_for_model,
    _merge_continuation_text,
)

ctx_8k = {
    'offline_model_info': {'id': 'qwen3-4b'},
    'local_context_tokens': 8192,
    'local_max_output_tokens': 2048,
}
budget = _tool_result_char_budget(ctx_8k, 2048)
assert 1200 <= budget <= 6000, budget

# Reproduce the reported shape: five Exa results with enough summary/body text to exceed ~8K chars raw.
results = []
for i in range(5):
    results.append({
        'title': f'2026 World Cup final result {i+1}',
        'url': f'https://example.com/world-cup/{i+1}',
        'publishedDate': f'2026-07-{20+i:02d}T12:00:00Z',
        'summary': ('Summary fact %d. ' % (i+1)) + ('important verified context ' * 70),
        'text': 'full webpage body ' * 350,
    })
exa = {
    'success': True,
    'provider': 'exa',
    'query': '2026年世界杯决赛相关新闻',
    'results': results,
}
raw_len = len(json.dumps(exa, ensure_ascii=False))
assert raw_len > 7900, raw_len
safe = _prepare_tool_result_for_model('exa_search', exa, ctx_8k, 2048)
assert len(safe) <= budget + 900, (len(safe), budget)
assert 'TOOL_RESULT' in safe and 'NEXT_ACTION' in safe
for i in range(5):
    assert f'2026 World Cup final result {i+1}' in safe
    assert f'https://example.com/world-cup/{i+1}' in safe
assert 'full webpage body full webpage body' not in safe, 'summary should take precedence over full body'

# Long text readers/web tools must use the same context-safety layer.
long_read = {'success': True, 'path': '/tmp/large.txt', 'content': '长文本事实。' * 8000}
read_safe = _prepare_tool_result_for_model('read_file', long_read, ctx_8k, 2048)
assert len(read_safe) <= budget + 1000, (len(read_safe), budget)
assert 'context_safety_note' in read_safe
assert 'path' in read_safe

# Failure text must tell the small model when retrying is useless vs recoverable.
missing_key = _tool_error_for_model('exa_search', 'Exa API Key 未配置。请在工具管理页面配置。')
assert 'NON_RETRYABLE' in missing_key and 'configure' in missing_key.lower()
arg_error = _tool_error_for_model('exa_search', '[MODEL_TOOL_ARGUMENT_ERROR] query is required')
assert 'RECOVERABLE' in arg_error and 'exact documented argument keys' in arg_error
rate = _tool_error_for_model('exa_search', 'Exa HTTP 429: rate limit')
assert 'another enabled search provider' in rate

# Controlled continuation assembly must preserve partial text without duplicating the same chunk.
assert _merge_continuation_text(['第一段'], '第二段') == '第一段\n第二段'
assert _merge_continuation_text(['第一段'], '第一段') == '第一段'

agent_src = (ROOT / 'python/navixmind/agent.py').read_text()
assert '# RASTACODER_V10_CONTEXT_SAFE_TOOL_RESULTS' in agent_src
assert 'offline_max_token_continuations >= 1' in agent_src
assert '[FINAL_ANSWER_CONTINUATION]' in agent_src
assert 'tools=None if (is_offline and force_no_tools_once) else tools_schema' in agent_src
assert '_prepare_tool_result_for_model(tool_name, result, context, max_tokens)' in agent_src

history_src = (ROOT / 'lib/features/chat/presentation/conversation_history_screen.dart').read_text()
assert '// RASTACODER_V10_ACCESSIBLE_HISTORY_OPEN' in history_src
assert "label: '打开对话：$title" in history_src
assert "hint: '双击打开这条聊天记录'" in history_src
assert 'child: ExcludeSemantics(' in history_src
# The management menu must remain a sibling, not the ListTile trailing action.
segment = history_src.split('// RASTACODER_V10_ACCESSIBLE_HISTORY_OPEN', 1)[1]
assert 'trailing: PopupMenuButton' not in segment
assert 'PopupMenuButton<String>' in segment

print('RastaCoder v10 validation passed: 8K-context Exa payload compaction, generic long-tool safety, explicit recovery guidance, bounded local max-token continuation, and accessible history opening.')
