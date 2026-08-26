from pathlib import Path

AGENT = Path('python/navixmind/agent.py')
HISTORY = Path('lib/features/chat/presentation/conversation_history_screen.dart')

text = AGENT.read_text()
marker = '# RASTACODER_V10_CONTEXT_SAFE_TOOL_RESULTS'
if marker not in text:
    anchor = '\n\nclass LocalLLMClient:'
    helpers = r'''

# RASTACODER_V10_CONTEXT_SAFE_TOOL_RESULTS
_SEARCH_RESULT_TOOLS = {
    'anysearch_search', 'anysearch_extract', 'anysearch_get_sub_domains',
    'exa_search', 'langsearch_search', 'tavily_search',
}


def _tool_result_char_budget(context: Dict[str, Any], max_output_tokens: int = 2048) -> int:
    """Bound tool payloads before they are re-prefilled into a local model."""
    if not isinstance(context, dict) or 'offline_model_info' not in context:
        return 10000
    try:
        ctx = max(2048, min(int(context.get('local_context_tokens', 32768)), 32768))
    except (TypeError, ValueError):
        ctx = 32768
    try:
        out = max(256, min(int(max_output_tokens), 8192))
    except (TypeError, ValueError):
        out = 2048
    available_tokens = max(900, ctx - out - 2400)
    return max(1200, min(int(available_tokens * 1.25), 12000))


def _trim_model_text(value: Any, limit: int) -> Tuple[str, bool]:
    value = str(value or '').strip()
    if len(value) <= limit:
        return value, False
    if limit < 300:
        return value[:limit], True
    head = max(180, int(limit * 0.78))
    tail = max(80, limit - head - 55)
    return value[:head] + '\n...[context-safe truncation]...\n' + value[-tail:], True


def _search_result_payload_for_model(tool_name: str, result: Any, max_chars: int) -> str:
    if not isinstance(result, dict):
        return _trim_model_text(result, max_chars)[0]
    provider = str(result.get('provider') or tool_name.replace('_search', ''))
    query = str(result.get('query') or '').strip()
    answer = str(result.get('answer') or '').strip()
    rows = result.get('results')
    out = [f'provider: {provider}']
    if query:
        out.append(f'query: {query}')
    if answer:
        answer_text, _ = _trim_model_text(answer, min(1400, max(350, max_chars // 4)))
        out += ['provider_answer:', answer_text]
    if isinstance(rows, list) and rows:
        out.append(f'result_count: {len(rows)}')
        remaining = max(600, max_chars - sum(len(x) for x in out) - 120)
        per = max(320, remaining // max(1, len(rows)))
        for index, item in enumerate(rows, 1):
            if not isinstance(item, dict):
                snippet, _ = _trim_model_text(item, per)
                out += [f'[{index}]', snippet]
                continue
            title = item.get('title') or item.get('name') or item.get('id') or f'Result {index}'
            url = item.get('url') or item.get('link') or item.get('id') or ''
            published = item.get('publishedDate') or item.get('published_date') or item.get('datePublished') or item.get('date') or ''
            summary = item.get('summary') or item.get('snippet') or item.get('description')
            if not summary:
                highlights = item.get('highlights')
                if isinstance(highlights, list):
                    summary = '\n'.join(str(x) for x in highlights if str(x).strip())
            if not summary:
                summary = item.get('text') or item.get('content') or item.get('raw_content') or ''
            summary_text, _ = _trim_model_text(summary, max(180, per - 180))
            out.append(f'[{index}] {title}')
            if url:
                out.append(f'URL: {url}')
            if published:
                out.append(f'published: {published}')
            if summary_text:
                out += ['summary:', summary_text]
    elif result.get('content'):
        payload, _ = _trim_model_text(result.get('content'), max(300, max_chars - 220))
        out += ['content:', payload]
    else:
        raw, _ = _trim_model_text(json.dumps(result, ensure_ascii=False, default=str), max_chars)
        out.append(raw)
    final, truncated = _trim_model_text('\n'.join(out), max_chars)
    if truncated:
        final += '\ncontext_safety_note: Search output was truncated before local-model prefill.'
    return final


def _prepare_tool_result_for_model(tool_name: str, result: Any, context: Dict[str, Any], max_output_tokens: int) -> str:
    max_chars = _tool_result_char_budget(context, max_output_tokens)
    if tool_name in _SEARCH_RESULT_TOOLS:
        payload = _search_result_payload_for_model(tool_name, result, max_chars)
    elif isinstance(result, dict):
        large_key = next((k for k in ('content', 'text', 'result', 'output', 'summary') if str(result.get(k) or '').strip()), None)
        if large_key:
            meta = {k: v for k, v in result.items() if k != large_key and isinstance(v, (str, int, float, bool, type(None)))}
            meta_text = json.dumps(meta, ensure_ascii=False, default=str)
            body_limit = max(300, max_chars - len(meta_text) - 120)
            body, truncated = _trim_model_text(result.get(large_key), body_limit)
            payload = f'metadata: {meta_text}\n{large_key}:\n{body}'
            if truncated:
                payload += '\ncontext_safety_note: Tool output was truncated before local-model prefill.'
        else:
            payload, truncated = _trim_model_text(json.dumps(result, ensure_ascii=False, default=str), max_chars)
            if truncated:
                payload += '\ncontext_safety_note: Tool output was truncated before local-model prefill.'
    else:
        payload, truncated = _trim_model_text(result, max_chars)
        if truncated:
            payload += '\ncontext_safety_note: Tool output was truncated before local-model prefill.'
    return (
        f'TOOL_RESULT\ntool: {tool_name}\nstatus: succeeded\npayload:\n{payload}\n\n'
        'NEXT_ACTION: Use this result to continue the original user request. If it is sufficient, answer the user directly in the user\'s language and stop. '
        'Do not repeat raw JSON or the tool result. Call another enabled tool only when genuinely necessary.'
    )


def _tool_error_for_model(tool_name: str, error: Any) -> str:
    msg = str(error or '').strip()
    low = msg.lower()
    if 'api key' in low and ('未配置' in msg or 'not configured' in low):
        recovery = 'NON_RETRYABLE: Do not call this provider again. Tell the user to configure its API Key in Tool Management.'
    elif 'http 401' in low or 'http 403' in low or 'unauthorized' in low or 'forbidden' in low:
        recovery = 'NON_RETRYABLE: Credentials or permission are invalid. Do not loop; report the configuration problem.'
    elif 'http 429' in low or 'rate limit' in low:
        recovery = 'Do not retry the same provider repeatedly. If another enabled search provider is available, use it once; otherwise report the rate limit.'
    elif '[model_tool_argument_error]' in low or '[model_tool_name_error]' in low:
        recovery = 'RECOVERABLE: Retry once with one enabled canonical tool name and the exact documented argument keys.'
    elif 'timeout' in low or 'request failed' in low or 'network' in low:
        recovery = 'RECOVERABLE_ONCE: Retry once or use one different enabled provider. Do not loop on the same failure.'
    else:
        recovery = 'Do not repeat the identical failed call. Correct the cause if clear; otherwise explain the failure to the user.'
    return f'TOOL_FAILURE\ntool: {tool_name}\nerror: {msg[:1800]}\nrecovery: {recovery}'


def _merge_continuation_text(parts: List[str], current: str) -> str:
    pieces = [str(x).strip() for x in parts if str(x).strip()]
    current = str(current or '').strip()
    if current:
        if not pieces or current != pieces[-1]:
            pieces.append(current)
    return '\n'.join(pieces).strip()
'''
    if anchor not in text:
        raise SystemExit('LocalLLMClient anchor missing')
    text = text.replace(anchor, helpers + anchor, 1)

# Keep only one controlled offline final-answer continuation; cloud behavior stays unchanged.
old = """    iteration = 0\n    tool_call_count = 0\n    final_response = None\n    created_files = []  # Track output files for session context\n"""
new = """    iteration = 0\n    tool_call_count = 0\n    final_response = None\n    created_files = []  # Track output files for session context\n    offline_max_token_continuations = 0\n    partial_final_chunks: List[str] = []\n    force_no_tools_once = False\n"""
if old in text:
    text = text.replace(old, new, 1)

old = """                tools=tools_schema,\n                max_tokens=max_tokens,\n"""
new = """                tools=None if (is_offline and force_no_tools_once) else tools_schema,\n                max_tokens=max_tokens,\n"""
if old in text:
    text = text.replace(old, new, 1)

old = """            final_response = _extract_text_content(visible_blocks)\n"""
new = """            final_response = _merge_continuation_text(partial_final_chunks, _extract_text_content(visible_blocks))\n"""
if old in text:
    text = text.replace(old, new, 1)

old = """                        if len(result_str) > 10000:\n                            result_str = result_str[:5000] + \"\\n\\n[Output truncated...]\\n\\n\" + result_str[-2000:]\n\n                        tool_results.append({\n                            \"type\": \"tool_result\",\n                            \"tool_use_id\": tool_id,\n                            \"content\": result_str\n                        })\n"""
new = """                        model_result = (\n                            _prepare_tool_result_for_model(tool_name, result, context, max_tokens)\n                            if is_offline else result_str\n                        )\n                        tool_results.append({\n                            \"type\": \"tool_result\",\n                            \"tool_use_id\": tool_id,\n                            \"content\": model_result\n                        })\n"""
if old not in text:
    raise SystemExit('success tool-result anchor missing')
text = text.replace(old, new, 1)

old = """                        error_content = str(e)\n                        if is_offline and ('[MODEL_TOOL_ARGUMENT_ERROR]' in error_content or '[MODEL_TOOL_NAME_ERROR]' in error_content):\n                            error_content += (\n                                '\\n[RECOVERABLE] Retry the same task immediately with one enabled canonical tool and corrected exact arguments. '\n                                'Choose a safe output filename yourself when possible; only ask the user if a required INPUT file or genuinely ambiguous destructive choice is missing.'\n                            )\n"""
new = """                        error_content = _tool_error_for_model(tool_name, e) if is_offline else str(e)\n"""
if old not in text:
    raise SystemExit('tool-error anchor missing')
text = text.replace(old, new, 1)

old = """        # Case 3: Max tokens reached — continue the loop so Claude can finish\n        if stop_reason == 'max_tokens':\n            bridge.log(\"Response hit token limit, continuing...\", level=\"info\")\n            # Add partial assistant content to conversation and ask to continue\n            messages.append({\"role\": \"assistant\", \"content\": content_blocks})\n            messages.append({\"role\": \"user\", \"content\": \"Continue from where you left off.\"})\n            continue\n"""
new = """        # Case 3: Max tokens reached. Cloud keeps legacy continuation behavior.\n        # Local models get at most one tool-free continuation, preventing the 50-step max_tokens loop.\n        if stop_reason == 'max_tokens':\n            visible_blocks = _strip_reasoning_from_blocks(content_blocks) if is_offline else content_blocks\n            partial = _extract_text_content(visible_blocks).strip()\n            if not is_offline:\n                bridge.log(\"Response hit token limit, continuing...\", level=\"info\")\n                messages.append({\"role\": \"assistant\", \"content\": content_blocks})\n                messages.append({\"role\": \"user\", \"content\": \"Continue from where you left off.\"})\n                continue\n            if partial:\n                partial_final_chunks.append(partial)\n            context['_diagnostics'].append({\n                'stage': 'offline_max_tokens',\n                'continuation': offline_max_token_continuations,\n                'partial_chars': len(partial),\n                'tool_calls': tool_call_count,\n            })\n            if offline_max_token_continuations >= 1:\n                final_response = _merge_continuation_text(partial_final_chunks[:-1], partial_final_chunks[-1] if partial_final_chunks else '')\n                if not final_response:\n                    final_response = '本地模型连续达到单次输出上限，且没有产生可用正文。请调高“最大输出 Token”后重试。'\n                session.add_message(\"assistant\", final_response)\n                result = {\"content\": final_response}\n                if created_files:\n                    result[\"created_files\"] = created_files\n                result[\"thinking\"] = _thinking_for_ui(reasoning_parts, local_thinking_mode)\n                result[\"thinking_mode\"] = local_thinking_mode\n                result[\"diagnostics\"] = _format_diagnostics(context)\n                return result\n            offline_max_token_continuations += 1\n            force_no_tools_once = True\n            messages.append({\"role\": \"assistant\", \"content\": content_blocks})\n            messages.append({\n                \"role\": \"user\",\n                \"content\": (\n                    '[FINAL_ANSWER_CONTINUATION] Continue only the unfinished final answer. '\n                    'Do not call any tool, do not repeat earlier text, do not output raw JSON or hidden reasoning, and finish within this response.'\n                ),\n            })\n            continue\n"""
if old not in text:
    raise SystemExit('max_tokens anchor missing')
text = text.replace(old, new, 1)
AGENT.write_text(text)

h = HISTORY.read_text()
h_marker = '// RASTACODER_V10_ACCESSIBLE_HISTORY_OPEN'
if h_marker not in h:
    old = """                    return Semantics(\n                      selected: selected,\n                      label: '$title${selected ? '，当前对话' : ''}',\n                      child: ListTile(\n                        title: Text(title),\n                        subtitle: Text(updated is DateTime ? updated.toLocal().toString() : ''),\n                        leading: Icon(selected ? Icons.chat_bubble : Icons.chat_bubble_outline),\n                        onTap: () => Navigator.pop(context, id),\n                        trailing: PopupMenuButton<String>(\n                          tooltip: '管理对话：$title',\n                          onSelected: (value) {\n                            if (value == 'rename') _rename(item);\n                            if (value == 'delete') _delete(item);\n                          },\n                          itemBuilder: (_) => const [\n                            PopupMenuItem(value: 'rename', child: Text('重命名')),\n                            PopupMenuItem(value: 'delete', child: Text('删除')),\n                          ],\n                        ),\n                      ),\n                    );\n"""
    new = """                    // RASTACODER_V10_ACCESSIBLE_HISTORY_OPEN\n                    return Row(\n                      children: [\n                        Expanded(\n                          child: Semantics(\n                            button: true,\n                            selected: selected,\n                            label: '打开对话：$title${selected ? '，当前对话' : ''}',\n                            hint: '双击打开这条聊天记录',\n                            onTap: () => Navigator.pop(context, id),\n                            child: ExcludeSemantics(\n                              child: ListTile(\n                                title: Text(title),\n                                subtitle: Text(updated is DateTime ? updated.toLocal().toString() : ''),\n                                leading: Icon(selected ? Icons.chat_bubble : Icons.chat_bubble_outline),\n                                onTap: () => Navigator.pop(context, id),\n                              ),\n                            ),\n                          ),\n                        ),\n                        PopupMenuButton<String>(\n                          tooltip: '管理对话：$title',\n                          onSelected: (value) {\n                            if (value == 'rename') _rename(item);\n                            if (value == 'delete') _delete(item);\n                          },\n                          itemBuilder: (_) => const [\n                            PopupMenuItem(value: 'rename', child: Text('重命名')),\n                            PopupMenuItem(value: 'delete', child: Text('删除')),\n                          ],\n                        ),\n                      ],\n                    );\n"""
    if old not in h:
        raise SystemExit('history row anchor missing')
    h = h.replace(old, new, 1)
    HISTORY.write_text(h)

print('Applied RastaCoder v10 context-safe search/long-tool and accessible-history patch.')
