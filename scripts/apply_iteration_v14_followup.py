from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
agent_path = ROOT / 'python/navixmind/agent.py'
native_path = ROOT / 'lib/core/services/native_tool_executor.dart'
service_path = ROOT / 'lib/core/services/local_llm_service.dart'
kotlin_path = ROOT / 'android/app/src/main/kotlin/ai/navixmind/services/MLCInferenceChannel.kt'
chat_path = ROOT / 'lib/features/chat/presentation/chat_screen.dart'


def once(text, old, new, label):
    if new in text:
        print(label + ': already applied')
        return text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected one anchor, found {count}')
    print(label + ': applied')
    return text.replace(old, new, 1)

agent = agent_path.read_text(encoding='utf-8')
native = native_path.read_text(encoding='utf-8')
service = service_path.read_text(encoding='utf-8')
kotlin = kotlin_path.read_text(encoding='utf-8')
chat = chat_path.read_text(encoding='utf-8')

# Preserve lexical order for Qwen's common {"a","b"} array mistake.
if 'RASTACODER_V14_ORDERED_JSONISH_PARSER' not in agent:
    pattern = re.compile(r'def _parse_mapping\(text: str\) -> Optional\[dict\]:[\s\S]*?\n\ndef _coerce_tool_args\(value: Any\) -> dict:')
    match = pattern.search(agent)
    if not match:
        raise SystemExit('ordered parser: function range not found')
    replacement = r'''# RASTACODER_V14_ORDERED_JSONISH_PARSER
def _ordered_literal_eval(text: str) -> Any:
    """Literal-eval JSON-ish output while preserving source order of brace-arrays."""
    import ast

    def walk(node):
        if isinstance(node, ast.Dict):
            return {walk(k): walk(v) for k, v in zip(node.keys, node.values)}
        if isinstance(node, ast.List):
            return [walk(v) for v in node.elts]
        if isinstance(node, ast.Tuple):
            return [walk(v) for v in node.elts]
        if isinstance(node, ast.Set):
            return [walk(v) for v in node.elts]
        return ast.literal_eval(node)

    return walk(ast.parse(text, mode='eval').body)


def _parse_mapping(text: str) -> Optional[dict]:
    """Parse JSON-like tool call objects without executing model text."""
    import re

    value = text.strip()
    candidates = [value, re.sub(r',\s*([}\]])', r'\1', value)]
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
    try:
        parsed = _ordered_literal_eval(value)
        if isinstance(parsed, dict):
            return parsed
    except (ValueError, SyntaxError, TypeError):
        pass
    return None


def _missing_json_value_keys(text: str) -> List[str]:
    """Detect object keys emitted without ': value'; never execute them silently."""
    keys: List[str] = []
    pattern = re.compile(r'(?P<prefix>[,{]\s*)"(?P<key>(?:\\.|[^"\\])*)"\s*(?=,|})')
    for match in pattern.finditer(str(text or '')):
        key = match.group('key').strip()
        if key and key not in keys:
            keys.append(key)
    return keys


def _coerce_tool_args(value: Any) -> dict:'''
    agent = agent[:match.start()] + replacement + agent[match.end():]

    old_try = '''def _try_parse_tool_json(json_str: str, index: int) -> Optional[dict]:
    """Parse common JSON/dict function-call variants into a tool_use block."""
    call_data = _parse_mapping(json_str)
    if not call_data:
        return None
'''
    new_try = '''def _try_parse_tool_json(json_str: str, index: int) -> Optional[dict]:
    """Parse common JSON/dict function-call variants into a tool_use block."""
    if _missing_json_value_keys(json_str):
        return None
    call_data = _parse_mapping(json_str)
    if not call_data:
        return None
'''
    agent = once(agent, old_try, new_try, 'reject missing-value JSON')

    old_retry = '''                        '[Tool call format error] The previous tool call was not executable. '
                        'Retry now using ONLY one enabled canonical function name and the exact argument keys '
                        'shown in the system prompt. Do not use Skill/category names or generic keys such as param. '
                        'Do not answer with prose.'
'''
    new_retry = '''                        '[Tool call format error] The previous tool call was not executable. '
                        + (
                            'The previous JSON contained argument key(s) with no value: '
                            + ', '.join(_missing_json_value_keys(raw_bad))
                            + '. Every included key must have a colon and a real JSON value. '
                            'Omit optional keys you do not need. For content/text/body, provide the complete requested text. '
                            if _missing_json_value_keys(raw_bad) else ''
                        )
                        + 'Retry now using ONLY one enabled canonical function name and the exact argument keys '
                        'shown in the system prompt. Do not use Skill/category names or generic keys such as param. '
                        'Do not answer with prose.'
'''
    agent = once(agent, old_retry, new_retry, 'precise parse retry')

# Keep model-prefill serialization on the same safe boundary as tool logging.
agent = agent.replace('json.dumps(result, ensure_ascii=False, default=str)', '_json_boundary_dumps(result, ensure_ascii=False)')
agent = agent.replace('json.dumps(meta, ensure_ascii=False, default=str)', '_json_boundary_dumps(meta, ensure_ascii=False)')
agent = agent.replace('json.dumps(value, ensure_ascii=False, default=str)', '_json_boundary_dumps(value, ensure_ascii=False)')
agent = agent.replace('json.dumps(metadata, ensure_ascii=False, default=str)', '_json_boundary_dumps(metadata, ensure_ascii=False)')

# Explicit stream eligibility: top-level ReAct opts in; internal ingestion stays off.
if 'RASTACODER_V14_STREAM_TO_UI_FLAG' not in agent:
    start = agent.index('class LocalLLMClient:')
    end = agent.find('\nclass OpenAICompatibleClient', start)
    if end < 0:
        end = agent.find('\nclass APIError', start)
    local = agent[start:end]
    old_sig = '''        max_tokens: int = 2048,
        retry_count: int = 1
    ) -> dict:
'''
    new_sig = '''        max_tokens: int = 2048,
        retry_count: int = 1,
        stream_to_ui: bool = False
    ) -> dict:
'''
    local = once(local, old_sig, new_sig, 'LocalLLM stream flag signature')
    old_args = '''            'top_p': self.top_p,
        }
'''
    new_args = '''            'top_p': self.top_p,
            # RASTACODER_V14_STREAM_TO_UI_FLAG
            'stream_to_ui': bool(stream_to_ui),
        }
'''
    local = once(local, old_args, new_args, 'LocalLLM stream flag native args')
    agent = agent[:start] + local + agent[end:]

    old_main = '''            response = client.create_message(
                messages=messages,
                system=system_prompt,
                tools=None if (is_offline and force_no_tools_once) else tools_schema,
                max_tokens=max_tokens,
            )
'''
    new_main = '''            if is_offline:
                response = client.create_message(
                    messages=messages,
                    system=system_prompt,
                    tools=None if force_no_tools_once else tools_schema,
                    max_tokens=max_tokens,
                    stream_to_ui=True,
                )
            else:
                response = client.create_message(
                    messages=messages,
                    system=system_prompt,
                    tools=tools_schema,
                    max_tokens=max_tokens,
                )
'''
    agent = once(agent, old_main, new_main, 'top-level stream eligibility')

if 'RASTACODER_V14_STREAM_FORWARD_NATIVE' not in native:
    old_fields = '''    final topP = (args['top_p'] as num?)?.toDouble() ?? 0.95;
    final modelId = args['model_id'] as String?;
'''
    new_fields = '''    final topP = (args['top_p'] as num?)?.toDouble() ?? 0.95;
    // RASTACODER_V14_STREAM_FORWARD_NATIVE
    final streamToUi = args['stream_to_ui'] == true;
    final modelId = args['model_id'] as String?;
'''
    native = once(native, old_fields, new_fields, 'native stream flag read')
    native = native.replace('''        topP: topP,
      );''', '''        topP: topP,
        streamToUi: streamToUi,
      );''')
    if native.count('streamToUi: streamToUi') != 2:
        raise SystemExit(f'native stream forwarding: expected 2 calls, found {native.count("streamToUi: streamToUi")}')

if 'RASTACODER_V14_STREAM_SERVICE_FLAG' not in service:
    old_sig = '''    double temperature = 0.7,
    double topP = 0.95,
  }) async {
'''
    new_sig = '''    double temperature = 0.7,
    double topP = 0.95,
    // RASTACODER_V14_STREAM_SERVICE_FLAG
    bool streamToUi = false,
  }) async {
'''
    service = once(service, old_sig, new_sig, 'service stream signature')
    old_map = '''            'temperature': temperature,
            'topP': topP,
          },
'''
    new_map = '''            'temperature': temperature,
            'topP': topP,
            'streamToUi': streamToUi,
          },
'''
    service = once(service, old_map, new_map, 'service MethodChannel stream flag')

if 'RASTACODER_V14_EXPLICIT_UI_STREAM' not in kotlin:
    old_handler = '''                    val topP = (call.argument<Number>("topP")?.toFloat() ?: 0.95f).coerceIn(0.01f, 1.0f)
                    if (messagesJson == null) {
'''
    new_handler = '''                    val topP = (call.argument<Number>("topP")?.toFloat() ?: 0.95f).coerceIn(0.01f, 1.0f)
                    // RASTACODER_V14_EXPLICIT_UI_STREAM
                    val streamToUi = call.argument<Boolean>("streamToUi") ?: false
                    if (messagesJson == null) {
'''
    kotlin = once(kotlin, old_handler, new_handler, 'kotlin handler stream flag')
    kotlin = once(kotlin, 'generate(messagesJson, toolsJson, maxTokens, temperature, topP, result)', 'generate(messagesJson, toolsJson, maxTokens, temperature, topP, streamToUi, result)', 'kotlin handler forward stream flag')
    old_sig = '''        maxTokens: Int,
        temperature: Float,
        topP: Float,
        result: MethodChannel.Result
'''
    new_sig = '''        maxTokens: Int,
        temperature: Float,
        topP: Float,
        streamToUi: Boolean,
        result: MethodChannel.Result
'''
    kotlin = once(kotlin, old_sig, new_sig, 'kotlin generate stream signature')
    kotlin = kotlin.replace('emitEvent(mapOf("phase" to "generation_started", "elapsed_ms" to 0L))', 'if (streamToUi) emitEvent(mapOf("phase" to "generation_started", "elapsed_ms" to 0L))')
    kotlin = kotlin.replace('emitEvent(mapOf("phase" to "first_token", "elapsed_ms" to (System.currentTimeMillis() - startTime)))', 'if (streamToUi) emitEvent(mapOf("phase" to "first_token", "elapsed_ms" to (System.currentTimeMillis() - startTime)))')
    kotlin = kotlin.replace('emitEvent(mapOf("phase" to "thinking_started"))', 'if (streamToUi) emitEvent(mapOf("phase" to "thinking_started"))')
    kotlin = kotlin.replace('emitEvent(mapOf("phase" to "tool_call_started", "generation_id" to generationId))', 'if (streamToUi) emitEvent(mapOf("phase" to "tool_call_started", "generation_id" to generationId))')
    kotlin = kotlin.replace('if (tools != null && !toolCallEmitted) {', 'if (streamToUi && !toolCallEmitted) {')
    kotlin = kotlin.replace('emitEvent(mapOf("phase" to "generation_completed", "elapsed_ms" to elapsed))', 'if (streamToUi) emitEvent(mapOf("phase" to "generation_completed", "elapsed_ms" to elapsed))')

if 'RASTACODER_V14_STREAM_GENERATION_RESET' not in chat:
    old_start = '''        case 'generation_started':
          message = '本地模型开始生成…';
          break;
'''
    new_start = '''        case 'generation_started':
          // RASTACODER_V14_STREAM_GENERATION_RESET
          _beginStreamGeneration();
          message = '本地模型开始生成…';
          break;
'''
    chat = once(chat, old_start, new_start, 'chat generation stream reset')
    anchor = '''  String _streamVisibleText(String raw) {
'''
    method = '''  void _beginStreamGeneration() {
    final index = _streamDraftIndex;
    if (mounted && index != null && index >= 0 && index < _messages.length &&
        _messages[index].role == MessageRole.assistant) {
      setState(() => _messages.removeAt(index));
    }
    _resetStreamDraftState();
  }

''' + anchor
    chat = once(chat, anchor, method, 'chat begin stream generation')

agent_path.write_text(agent, encoding='utf-8')
native_path.write_text(native, encoding='utf-8')
service_path.write_text(service, encoding='utf-8')
kotlin_path.write_text(kotlin, encoding='utf-8')
chat_path.write_text(chat, encoding='utf-8')
print('V14 follow-up parser/stream hardening applied.')
