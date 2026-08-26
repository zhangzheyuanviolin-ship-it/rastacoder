from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
agent_path = ROOT / 'python/navixmind/agent.py'
compat_path = ROOT / 'python/navixmind/tools/compat.py'
kotlin_path = ROOT / 'android/app/src/main/kotlin/ai/navixmind/services/MLCInferenceChannel.kt'
chat_path = ROOT / 'lib/features/chat/presentation/chat_screen.dart'

agent = agent_path.read_text(encoding='utf-8')
compat = compat_path.read_text(encoding='utf-8')
kotlin = kotlin_path.read_text(encoding='utf-8')
chat = chat_path.read_text(encoding='utf-8')


def once(text, old, new, label):
    if new in text:
        print(label + ': already applied')
        return text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected one anchor, found {count}')
    print(label + ': applied')
    return text.replace(old, new, 1)

# ---------- Python: one JSON-safe boundary for every tool / diagnostic / model turn ----------
anchor = '''def _diag_safe(value: Any) -> Any:\n'''
block = '''# RASTACODER_V14_JSON_BOUNDARY\ndef _json_boundary_safe(value: Any) -> Any:\n    """Recursively convert arbitrary executor/model values to deterministic JSON-safe data."""\n    if isinstance(value, dict):\n        return {str(k): _json_boundary_safe(v) for k, v in value.items()}\n    if isinstance(value, (set, frozenset)):\n        return [_json_boundary_safe(v) for v in sorted(value, key=lambda x: repr(x))]\n    if isinstance(value, (list, tuple)):\n        return [_json_boundary_safe(v) for v in value]\n    if isinstance(value, bytes):\n        return value.decode('utf-8', errors='replace')\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    try:\n        if hasattr(value, 'item'):\n            return _json_boundary_safe(value.item())\n    except Exception:\n        pass\n    return str(value)\n\n\ndef _json_boundary_dumps(value: Any, **kwargs: Any) -> str:\n    return json.dumps(_json_boundary_safe(value), **kwargs)\n\n\n''' + anchor
agent = once(agent, anchor, block, 'json boundary helper')

agent = agent.replace("'messages_json': json.dumps(openai_messages),", "'messages_json': _json_boundary_dumps(openai_messages),")
agent = agent.replace("args['tools_json'] = json.dumps(openai_tools)", "args['tools_json'] = _json_boundary_dumps(openai_tools)")
agent = agent.replace("json.dumps({'name': raw_name, 'arguments': raw_input}, ensure_ascii=False)[:1500]", "_json_boundary_dumps({'name': raw_name, 'arguments': raw_input}, ensure_ascii=False)[:1500]")
agent = agent.replace("result_str = json.dumps(result) if isinstance(result, dict) else str(result)", "result_str = _json_boundary_dumps(result, ensure_ascii=False) if isinstance(result, (dict, list, tuple, set, frozenset)) else str(result)")
agent = agent.replace("return json.dumps({\n                \"jsonrpc\": \"2.0\",\n                \"id\": request_id,\n                \"result\": result\n            })", "return _json_boundary_dumps({\n                \"jsonrpc\": \"2.0\",\n                \"id\": request_id,\n                \"result\": result\n            }, ensure_ascii=False)")

old_diag = '''    if isinstance(value, list):\n        return [_diag_safe(v) for v in value[:50]]\n    if isinstance(value, str) and len(value) > 2000:\n'''
new_diag = '''    if isinstance(value, (list, tuple)):\n        return [_diag_safe(v) for v in list(value)[:50]]\n    if isinstance(value, (set, frozenset)):\n        return [_diag_safe(v) for v in sorted(value, key=lambda x: repr(x))[:50]]\n    if isinstance(value, bytes):\n        return value.decode('utf-8', errors='replace')\n    if isinstance(value, str) and len(value) > 2000:\n'''
agent = once(agent, old_diag, new_diag, 'diagnostic container safety')
agent = agent.replace("return json.dumps(safe, ensure_ascii=False, indent=2)", "return _json_boundary_dumps(safe, ensure_ascii=False, indent=2)")

# Normalize tool inputs again at the executor boundary so no Skill can receive set/tuple artifacts.
old_exec_norm = '''                    tool_name, tool_input, compat_notes = normalize_tool_call(tool_name, tool_input, context=context)\n                    if is_offline:\n'''
new_exec_norm = '''                    tool_name, tool_input, compat_notes = normalize_tool_call(tool_name, tool_input, context=context)\n                    tool_input = _json_boundary_safe(tool_input)\n                    if is_offline:\n'''
agent = once(agent, old_exec_norm, new_exec_norm, 'executor argument JSON normalization')

# Systemic postcondition: a successful tool turn must never silently end with empty final prose.
old_state = '''    partial_final_chunks: List[str] = []\n    force_no_tools_once = False\n'''
new_state = '''    partial_final_chunks: List[str] = []\n    force_no_tools_once = False\n    successful_tool_turns = 0\n    empty_final_recovery_used = False\n'''
agent = once(agent, old_state, new_state, 'final response recovery state')

old_end = '''        if stop_reason == 'end_turn':\n            visible_blocks = _strip_reasoning_from_blocks(content_blocks) if is_offline else content_blocks\n            final_response = _merge_continuation_text(partial_final_chunks, _extract_text_content(visible_blocks))\n            bridge.log("Preparing response...", progress=0.95)\n'''
new_end = '''        if stop_reason == 'end_turn':\n            visible_blocks = _strip_reasoning_from_blocks(content_blocks) if is_offline else content_blocks\n            final_response = _merge_continuation_text(partial_final_chunks, _extract_text_content(visible_blocks))\n            if is_offline and not final_response.strip() and successful_tool_turns > 0 and not empty_final_recovery_used:\n                empty_final_recovery_used = True\n                force_no_tools_once = True\n                context['_diagnostics'].append({\n                    'stage': 'empty_final_recovery',\n                    'successful_tool_turns': successful_tool_turns,\n                    'created_files': [os.path.basename(p) for p in created_files],\n                })\n                messages.append({\n                    'role': 'user',\n                    'content': (\n                        'The requested tool operation already succeeded. Produce the final user-facing answer now. '\n                        'Do not call tools. Mention created file paths when applicable. Do not return an empty answer.'\n                    ),\n                })\n                continue\n            bridge.log("Preparing response...", progress=0.95)\n'''
agent = once(agent, old_end, new_end, 'empty final response recovery')

old_success = '''                        tool_results.append({\n                            "type": "tool_result",\n                            "tool_use_id": tool_id,\n                            "content": model_result\n                        })\n'''
new_success = '''                        tool_results.append({\n                            "type": "tool_result",\n                            "tool_use_id": tool_id,\n                            "content": model_result\n                        })\n                        successful_tool_turns += 1\n'''
agent = once(agent, old_success, new_success, 'successful tool turn counter')

# Repair malformed JSON objects that contain a bare key ("content",) by treating it as null.
old_candidates = '''    value = text.strip()\n    candidates = [value, re.sub(r',\\s*([}\\]])', r'\\1', value)]\n'''
new_candidates = '''    value = text.strip()\n    trailing = re.sub(r',\\s*([}\\]])', r'\\1', value)\n    # Small models sometimes emit {"key","next":...}. Make the object parseable\n    # so strict validation/tool recovery can report the missing value precisely.\n    bare_key = re.sub(r'([,{]\\s*)(["\\'][^"\\']+["\\'])\\s*(?=,|})', r'\\1\\2:null', trailing)\n    candidates = [value, trailing, bare_key]\n'''
agent = once(agent, old_candidates, new_candidates, 'bare-key JSON parser recovery')

# ---------- Compatibility: recursive container normalization for all 37 tools ----------
anchor = '''def normalize_tool_call(\n'''
helper = '''# RASTACODER_V14_CONTAINER_NORMALIZATION\ndef _normalize_container_types(value: Any) -> Any:\n    if isinstance(value, dict):\n        return {str(k): _normalize_container_types(v) for k, v in value.items()}\n    if isinstance(value, (set, frozenset)):\n        return [_normalize_container_types(v) for v in sorted(value, key=lambda x: repr(x))]\n    if isinstance(value, (list, tuple)):\n        return [_normalize_container_types(v) for v in value]\n    return value\n\n\n''' + anchor
compat = once(compat, anchor, helper, 'compat container helper')
old_args = '''    if isinstance(raw_args, dict):\n        args = dict(raw_args)\n'''
new_args = '''    if isinstance(raw_args, dict):\n        args = _normalize_container_types(raw_args)\n'''
compat = once(compat, old_args, new_args, 'normalize nested tool containers')

# ---------- Kotlin: expose real token deltas over the existing EventChannel ----------
kotlin = once(kotlin,
'''                    var firstTokenEmitted = false\n                    var thinkingEmitted = false\n''',
'''                    var firstTokenEmitted = false\n                    var thinkingEmitted = false\n                    val generationId = System.nanoTime()\n''',
'kotlin generation id')

kotlin = kotlin.replace('emitEvent(mapOf("phase" to "generation_started", "elapsed_ms" to 0L))', 'emitEvent(mapOf("phase" to "generation_started", "elapsed_ms" to 0L))')
old_delta = '''                                    if (!toolCallEmitted && probe.toString().contains("<tool_call", ignoreCase = true)) {\n                                        toolCallEmitted = true\n                                        emitEvent(mapOf("phase" to "tool_call_started"))\n                                    }\n'''
new_delta = '''                                    if (!toolCallEmitted && probe.toString().contains("<tool_call", ignoreCase = true)) {\n                                        toolCallEmitted = true\n                                        emitEvent(mapOf("phase" to "tool_call_started", "generation_id" to generationId))\n                                    }\n                                    // Only top-level ReAct generations have tools. Internal document-ingestion\n                                    // helper calls pass tools=null, so their private evidence notes never leak to UI.\n                                    if (tools != null && !toolCallEmitted) {\n                                        emitEvent(mapOf(\n                                            "phase" to "content_delta",\n                                            "generation_id" to generationId,\n                                            "delta" to delta\n                                        ))\n                                    }\n'''
kotlin = once(kotlin, old_delta, new_delta, 'kotlin content delta events')
kotlin = kotlin.replace('emitEvent(mapOf("phase" to "tool_call_started"))', 'emitEvent(mapOf("phase" to "tool_call_started", "generation_id" to generationId))')

# ---------- Flutter: transient streamed assistant message; canonical final response replaces it ----------
chat = once(chat,
'''  int? _conversationId;\n  String _conversationTitle = '新对话';\n''',
'''  int? _conversationId;\n  // RASTACODER_V14_FINAL_STREAMING\n  int? _streamDraftIndex;\n  String? _streamGenerationId;\n  final StringBuffer _streamRawBuffer = StringBuffer();\n  bool _streamSawToolCall = false;\n  String _conversationTitle = '新对话';\n''',
'chat streaming state')

old_listener = '''        case 'tool_call_started':\n          message = '正在形成工具调用…';\n          break;\n        case 'generation_completed':\n          message = '模型生成完成，正在处理响应…';\n          break;\n      }\n      if (message != null) setState(() => _statusMessage = message);\n'''
new_listener = '''        case 'content_delta':\n          _appendFinalStreamDelta(event);\n          return;\n        case 'tool_call_started':\n          _discardStreamDraft();\n          message = '正在形成工具调用…';\n          break;\n        case 'generation_completed':\n          message = '模型生成完成，正在处理响应…';\n          break;\n      }\n      if (message != null) setState(() => _statusMessage = message);\n'''
chat = once(chat, old_listener, new_listener, 'chat stream event handling')

insert_anchor = '''  Future<void> _initializeConversationHistory() async {\n'''
stream_methods = r'''  String _streamVisibleText(String raw) {
    var value = raw.replaceAll(RegExp(r'<think>[\s\S]*?</think>', caseSensitive: false), '');
    value = value.replaceAll(RegExp(r'<think>[\s\S]*$', caseSensitive: false), '');
    value = value.replaceAll(RegExp(r'</?think>', caseSensitive: false), '');
    return value;
  }

  void _appendFinalStreamDelta(Map<String, dynamic> event) {
    if (!mounted || !_isProcessing || _streamSawToolCall) return;
    final generationId = event['generation_id']?.toString() ?? '';
    final delta = event['delta']?.toString() ?? '';
    if (delta.isEmpty) return;
    if (_streamGenerationId != null && _streamGenerationId != generationId) {
      _discardStreamDraft();
    }
    _streamGenerationId = generationId;
    _streamRawBuffer.write(delta);
    final visible = _streamVisibleText(_streamRawBuffer.toString());
    if (visible.isEmpty || visible.contains('<tool_call')) return;
    setState(() {
      final index = _streamDraftIndex;
      final draft = ChatMessage(
        role: MessageRole.assistant,
        content: visible,
        timestamp: DateTime.now(),
      );
      if (index != null && index >= 0 && index < _messages.length &&
          _messages[index].role == MessageRole.assistant) {
        _messages[index] = draft;
      } else {
        _messages.add(draft);
        _streamDraftIndex = _messages.length - 1;
      }
    });
    _scrollToBottom();
  }

  void _discardStreamDraft() {
    _streamSawToolCall = true;
    final index = _streamDraftIndex;
    if (mounted && index != null && index >= 0 && index < _messages.length &&
        _messages[index].role == MessageRole.assistant) {
      setState(() => _messages.removeAt(index));
    }
    _streamDraftIndex = null;
    _streamGenerationId = null;
    _streamRawBuffer.clear();
  }

  void _resetStreamDraftState() {
    _streamDraftIndex = null;
    _streamGenerationId = null;
    _streamRawBuffer.clear();
    _streamSawToolCall = false;
  }

''' + insert_anchor
chat = once(chat, insert_anchor, stream_methods, 'chat streaming methods')

chat = once(chat,
'''    _announcedNativeToolIds.clear();\n\n    final conversationId = await _ensureConversation();\n''',
'''    _announcedNativeToolIds.clear();\n    _resetStreamDraftState();\n\n    final conversationId = await _ensureConversation();\n''',
'reset stream per turn')

old_final_add = '''        setState(() {\n          _messages.add(ChatMessage(\n            role: hasError ? MessageRole.error : MessageRole.assistant,\n            content: content,\n            timestamp: DateTime.now(),\n            thinking: thinking,\n            thinkingMode: thinkingMode,\n            diagnostics: diagnostics,\n            attachments: !hasError && createdFiles != null\n                ? createdFiles.map((e) => e.toString()).toList()\n                : null,\n          ));\n        });\n'''
new_final_add = '''        setState(() {\n          final canonical = ChatMessage(\n            role: hasError ? MessageRole.error : MessageRole.assistant,\n            content: content,\n            timestamp: DateTime.now(),\n            thinking: thinking,\n            thinkingMode: thinkingMode,\n            diagnostics: diagnostics,\n            attachments: !hasError && createdFiles != null\n                ? createdFiles.map((e) => e.toString()).toList()\n                : null,\n          );\n          final index = _streamDraftIndex;\n          if (!hasError && index != null && index >= 0 && index < _messages.length &&\n              _messages[index].role == MessageRole.assistant) {\n            _messages[index] = canonical;\n          } else {\n            _messages.add(canonical);\n          }\n          _resetStreamDraftState();\n        });\n'''
chat = once(chat, old_final_add, new_final_add, 'replace stream draft with canonical final')

agent_path.write_text(agent, encoding='utf-8')
compat_path.write_text(compat, encoding='utf-8')
kotlin_path.write_text(kotlin, encoding='utf-8')
chat_path.write_text(chat, encoding='utf-8')
print('V14 systemic result/streaming patch applied.')
