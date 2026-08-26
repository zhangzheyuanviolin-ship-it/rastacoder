#!/usr/bin/env python3
"""Apply V14 malformed-call recovery and guaranteed final-answer state machine."""
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)


path = Path("python/navixmind/agent.py")
text = path.read_text()
if "RASTACODER_V14_FINALIZATION_STATE_MACHINE" not in text:
    helper_anchor = '''def _coerce_tool_args(value: Any) -> dict:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str):
        parsed = _parse_mapping(value)
        if isinstance(parsed, dict):
            return parsed
        value = value.strip()
        return {"param": value} if value else {}
    return {}


'''
    helper_block = helper_anchor + '''# RASTACODER_V14_FINALIZATION_STATE_MACHINE

def _bare_json_value_keys(text: str) -> List[str]:
    """Find quoted object keys emitted without a colon/value by small models."""
    import re
    value = str(text or "")
    return list(dict.fromkeys(
        m.group(1) for m in re.finditer(r'(?<=[{,])\\s*"([A-Za-z_][A-Za-z0-9_]*)"\\s*(?=,|})', value)
    ))


def _guess_broken_tool_name(text: str) -> str:
    import re
    value = str(text or "")
    match = re.search(r'"(?:name|tool|tool_name)"\\s*:\\s*"([A-Za-z_][A-Za-z0-9_-]*)"', value)
    return normalize_tool_name(match.group(1)) if match else ""


def _raw_arguments_from_source(source: Any) -> Optional[Tuple[str, dict]]:
    """Reparse the immutable raw JSON call so nested array order wins over mutations."""
    if not isinstance(source, str) or not source.strip():
        return None
    parsed = _parse_mapping(source)
    if not isinstance(parsed, dict):
        return None
    nested = parsed.get("function") or parsed.get("function_call")
    if isinstance(nested, dict):
        name = nested.get("name") or nested.get("tool") or nested.get("tool_name")
        args = nested.get("arguments", nested.get("args", nested.get("parameters", nested.get("input", {}))))
    else:
        name = parsed.get("name") or parsed.get("tool") or parsed.get("tool_name")
        arg_key = next((key for key in ("arguments", "args", "parameters", "input") if key in parsed), None)
        args = parsed.get(arg_key) if arg_key else {
            key: value for key, value in parsed.items()
            if key not in {"name", "tool", "tool_name", "type", "id"}
        }
    if not name or not isinstance(args, dict):
        return None
    return str(name), to_json_safe(args)


def _fallback_after_empty_final(created_files: List[str], last_tool_payloads: List[str]) -> str:
    if created_files:
        paths = "\\n".join(f"- {path}" for path in dict.fromkeys(created_files))
        return "工具已经执行并通过文件后置校验，但本地模型没有生成最终说明。已生成文件：\\n" + paths
    if last_tool_payloads:
        payload = str(last_tool_payloads[-1] or "").strip()
        marker = "payload:\\n"
        if marker in payload:
            payload = payload.split(marker, 1)[1]
            payload = payload.split("\\n\\nNEXT_ACTION:", 1)[0].strip()
        payload, _ = _trim_model_text(payload, 6000)
        return "工具已经执行成功，但本地模型在最终总结阶段仍返回空正文。以下保留本轮工具读取结果：\\n\\n" + payload
    return "本地模型本轮没有生成可用的最终正文。请重试本轮请求。"


'''
    text = replace_once(text, helper_anchor, helper_block, "finalization helpers")

    text = replace_once(
        text,
        "    force_no_tools_once = False\n",
        "    force_no_tools_once = False\n    empty_final_retries = 0\n    last_successful_tool_payloads: List[str] = []\n",
        "finalization state vars",
    )

    # Target malformed JSON with the exact missing-value keys instead of sending
    # the same generic instruction that caused repeated identical PDF failures.
    old_retry = '''            if parse_retry_count <= 2:
                messages.append({
                    'role': 'user',
                    'content': (
                        '[Tool call format error] The previous tool call was not executable. '
                        'Retry now using ONLY one enabled canonical function name and the exact argument keys '
                        'shown in the system prompt. Do not use Skill/category names or generic keys such as param. '
                        'Do not answer with prose.'
                    )
                })
                continue
'''
    new_retry = '''            if parse_retry_count <= 2:
                bare_keys = _bare_json_value_keys(raw_bad)
                broken_tool = _guess_broken_tool_name(raw_bad)
                specific = ""
                if bare_keys:
                    specific = (
                        " Your JSON contained key(s) with no colon/value: " + ", ".join(bare_keys) + ". "
                        "Every included key must have a real JSON value. Omit unused optional keys completely."
                    )
                if broken_tool == "create_pdf":
                    specific += (
                        " For a text PDF use exactly create_pdf with output_path and actual content text; "
                        "do not emit bare content/title/image_paths keys."
                    )
                messages.append({
                    'role': 'user',
                    'content': (
                        '[Tool call format error] The previous tool call was not executable.' + specific + ' '
                        'Retry now using ONLY one enabled canonical function name and exact argument keys. '
                        'Generate any task content that is required by the user request instead of leaving a key blank. '
                        'Do not use Skill/category names or generic keys such as param. Do not answer with prose.'
                    )
                })
                continue
'''
    text = replace_once(text, old_retry, new_retry, "targeted parse retry")

    # Empty end_turn after a successful PDF/XLSX/read/etc tool is a state-machine
    # failure, not a valid final answer. Run exactly one tool-free continuation.
    old_end = '''        if stop_reason == 'end_turn':
            visible_blocks = _strip_reasoning_from_blocks(content_blocks) if is_offline else content_blocks
            final_response = _merge_continuation_text(partial_final_chunks, _extract_text_content(visible_blocks))
            bridge.log("Preparing response...", progress=0.95)
'''
    new_end = '''        if stop_reason == 'end_turn':
            visible_blocks = _strip_reasoning_from_blocks(content_blocks) if is_offline else content_blocks
            final_response = _merge_continuation_text(partial_final_chunks, _extract_text_content(visible_blocks))
            if is_offline and not str(final_response or "").strip():
                context['_diagnostics'].append({
                    'stage': 'empty_final_answer',
                    'retry': empty_final_retries,
                    'tool_calls': tool_call_count,
                    'created_files': [os.path.basename(p) for p in created_files],
                })
                if empty_final_retries < 1:
                    empty_final_retries += 1
                    force_no_tools_once = True
                    messages.append({
                        'role': 'user',
                        'content': (
                            '[FINAL_ANSWER_REQUIRED] Tool execution for the original request has finished. '
                            'Return a non-empty user-facing final answer now. Do not call tools, do not output JSON/XML, '
                            'do not expose hidden reasoning. For a created file, confirm completion and give its path. '
                            'For a read/analyze task, answer the original question from the tool result already in context.'
                        ),
                    })
                    continue
                final_response = _fallback_after_empty_final(created_files, last_successful_tool_payloads)
                context['_diagnostics'].append({
                    'stage': 'empty_final_fallback',
                    'chars': len(final_response),
                })
            bridge.log("Preparing response...", progress=0.95)
'''
    text = replace_once(text, old_end, new_end, "empty final continuation")

    # Reparse immutable raw source before the second normalizer pass. This is a
    # systemic guard against nested list/set mutation and recovers exact arrays.
    old_tool = '''                    raw_source = block.get('_raw_source')
                    tool_name, tool_input, compat_notes = normalize_tool_call(tool_name, tool_input, context=context)
                    tool_input = to_json_safe(tool_input)
'''
    new_tool = '''                    raw_source = block.get('_raw_source')
                    recovered_source = _raw_arguments_from_source(raw_source) if is_offline else None
                    if recovered_source is not None:
                        recovered_name, recovered_args = recovered_source
                        tool_name, tool_input, compat_notes = normalize_tool_call(recovered_name, recovered_args, context=context)
                        compat_notes = ["raw_source:reparsed"] + list(compat_notes)
                    else:
                        tool_name, tool_input, compat_notes = normalize_tool_call(tool_name, tool_input, context=context)
                    tool_input = to_json_safe(tool_input)
'''
    text = replace_once(text, old_tool, new_tool, "raw source replay")

    text = replace_once(
        text,
        '''                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": model_result
                        })
''',
        '''                        last_successful_tool_payloads.append(str(model_result))
                        if len(last_successful_tool_payloads) > 8:
                            last_successful_tool_payloads[:] = last_successful_tool_payloads[-8:]
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": model_result
                        })
''',
        "remember successful tool payload",
    )

    path.write_text(text)

print("Applied V14 targeted parse recovery and guaranteed finalization")
