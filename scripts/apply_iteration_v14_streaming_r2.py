from pathlib import Path

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

# Python: internal local-model helper calls default to no UI streaming. Only the
# top-level ReAct loop explicitly opts in, including tool-free final recovery.
if 'RASTACODER_V14_STREAM_TO_UI_FLAG' not in agent:
    class_start = agent.index('class LocalLLMClient:')
    class_end = agent.find('\nclass OpenAICompatibleClient', class_start)
    if class_end < 0:
        class_end = agent.find('\nclass APIError', class_start)
    if class_end < 0:
        raise SystemExit('LocalLLMClient class end not found')
    local = agent[class_start:class_end]
    local = once(
        local,
        '''        max_tokens: int = 2048,
        retry_count: int = 1
    ) -> dict:
''',
        '''        max_tokens: int = 2048,
        retry_count: int = 1,
        stream_to_ui: bool = False
    ) -> dict:
''',
        'LocalLLM stream flag signature',
    )
    local = once(
        local,
        '''            'top_p': self.top_p,
        }
''',
        '''            'top_p': self.top_p,
            # RASTACODER_V14_STREAM_TO_UI_FLAG
            'stream_to_ui': bool(stream_to_ui),
        }
''',
        'LocalLLM stream native arg',
    )
    agent = agent[:class_start] + local + agent[class_end:]

    agent = once(
        agent,
        '''            response = client.create_message(
                messages=messages,
                system=system_prompt,
                tools=None if (is_offline and force_no_tools_once) else tools_schema,
                max_tokens=max_tokens,
            )
''',
        '''            if is_offline:
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
''',
        'top-level ReAct stream opt-in',
    )

# Dart native executor: carry the explicit bit across Python native-tool bridge,
# including the retry path when Android has evicted the model.
if 'RASTACODER_V14_STREAM_FORWARD_NATIVE' not in native:
    fn_start = native.index('  Future<Map<String, dynamic>> _executeLLMGenerate(')
    fn_end = native.index('\n  void dispose()', fn_start)
    block = native[fn_start:fn_end]
    block = once(
        block,
        '''    final topP = (args['top_p'] as num?)?.toDouble() ?? 0.95;
    final modelId = args['model_id'] as String?;
''',
        '''    final topP = (args['top_p'] as num?)?.toDouble() ?? 0.95;
    // RASTACODER_V14_STREAM_FORWARD_NATIVE
    final streamToUi = args['stream_to_ui'] == true;
    final modelId = args['model_id'] as String?;
''',
        'native stream flag read',
    )
    block = block.replace(
        '''        topP: topP,
      );''',
        '''        topP: topP,
        streamToUi: streamToUi,
      );''',
    )
    block = block.replace(
        '''          topP: topP,
        );''',
        '''          topP: topP,
          streamToUi: streamToUi,
        );''',
    )
    if block.count('streamToUi: streamToUi') != 2:
        raise SystemExit(f'native stream forwarding expected 2 calls, got {block.count("streamToUi: streamToUi")}')
    native = native[:fn_start] + block + native[fn_end:]

# LocalLLMService: scope the change only to generate(), never runBenchmark().
if 'RASTACODER_V14_STREAM_SERVICE_FLAG' not in service:
    service_start = service.index('  Future<String> generate(')
    service_end = service.index('  // RASTACODER_V5_SKILLS_PARAMS_BENCH_STREAM', service_start)
    block = service[service_start:service_end]
    block = once(
        block,
        '''    double temperature = 0.7,
    double topP = 0.95,
  }) async {
''',
        '''    double temperature = 0.7,
    double topP = 0.95,
    // RASTACODER_V14_STREAM_SERVICE_FLAG
    bool streamToUi = false,
  }) async {
''',
        'service generate stream signature',
    )
    block = once(
        block,
        '''            'temperature': temperature,
            'topP': topP,
          },
''',
        '''            'temperature': temperature,
            'topP': topP,
            'streamToUi': streamToUi,
          },
''',
        'service MethodChannel stream bit',
    )
    service = service[:service_start] + block + service[service_end:]

# Kotlin: scope the signature/emission changes only to interactive generate(),
# leaving benchmark telemetry semantics unchanged.
if 'RASTACODER_V14_EXPLICIT_UI_STREAM' not in kotlin:
    kotlin = once(
        kotlin,
        '''                    val topP = (call.argument<Number>("topP")?.toFloat() ?: 0.95f).coerceIn(0.01f, 1.0f)
                    if (messagesJson == null) {
''',
        '''                    val topP = (call.argument<Number>("topP")?.toFloat() ?: 0.95f).coerceIn(0.01f, 1.0f)
                    // RASTACODER_V14_EXPLICIT_UI_STREAM
                    val streamToUi = call.argument<Boolean>("streamToUi") ?: false
                    if (messagesJson == null) {
''',
        'kotlin handler stream flag',
    )
    kotlin = once(
        kotlin,
        'generate(messagesJson, toolsJson, maxTokens, temperature, topP, result)',
        'generate(messagesJson, toolsJson, maxTokens, temperature, topP, streamToUi, result)',
        'kotlin handler stream forwarding',
    )

    fn_start = kotlin.index('    private fun generate(')
    fn_end = kotlin.index('    /**\n     * Parse OpenAI-format messages', fn_start)
    block = kotlin[fn_start:fn_end]
    block = once(
        block,
        '''        maxTokens: Int,
        temperature: Float,
        topP: Float,
        result: MethodChannel.Result
''',
        '''        maxTokens: Int,
        temperature: Float,
        topP: Float,
        streamToUi: Boolean,
        result: MethodChannel.Result
''',
        'kotlin generate stream signature',
    )
    block = block.replace(
        'emitEvent(mapOf("phase" to "generation_started", "elapsed_ms" to 0L))',
        'if (streamToUi) emitEvent(mapOf("phase" to "generation_started", "elapsed_ms" to 0L))',
    )
    block = block.replace(
        'emitEvent(mapOf("phase" to "first_token", "elapsed_ms" to (System.currentTimeMillis() - startTime)))',
        'if (streamToUi) emitEvent(mapOf("phase" to "first_token", "elapsed_ms" to (System.currentTimeMillis() - startTime)))',
    )
    block = block.replace(
        'emitEvent(mapOf("phase" to "thinking_started"))',
        'if (streamToUi) emitEvent(mapOf("phase" to "thinking_started"))',
    )
    block = block.replace(
        'emitEvent(mapOf("phase" to "tool_call_started", "generation_id" to generationId))',
        'if (streamToUi) emitEvent(mapOf("phase" to "tool_call_started", "generation_id" to generationId))',
    )
    block = block.replace(
        'if (tools != null && !toolCallEmitted) {',
        'if (streamToUi && !toolCallEmitted) {',
    )
    block = block.replace(
        'emitEvent(mapOf("phase" to "generation_completed", "elapsed_ms" to elapsed))',
        'if (streamToUi) emitEvent(mapOf("phase" to "generation_completed", "elapsed_ms" to elapsed))',
    )
    kotlin = kotlin[:fn_start] + block + kotlin[fn_end:]

# Flutter: every top-level local generation starts a fresh draft. A tool-call
# generation may discard its provisional prose; the subsequent final generation
# then streams normally instead of inheriting the tool-call suppression state.
if 'RASTACODER_V14_STREAM_GENERATION_RESET' not in chat:
    chat = once(
        chat,
        '''        case 'generation_started':
          message = '本地模型开始生成…';
          break;
''',
        '''        case 'generation_started':
          // RASTACODER_V14_STREAM_GENERATION_RESET
          _beginStreamGeneration();
          message = '本地模型开始生成…';
          break;
''',
        'chat generation reset event',
    )
    chat = once(
        chat,
        '''  String _streamVisibleText(String raw) {
''',
        '''  void _beginStreamGeneration() {
    final index = _streamDraftIndex;
    if (mounted && index != null && index >= 0 && index < _messages.length &&
        _messages[index].role == MessageRole.assistant) {
      setState(() => _messages.removeAt(index));
    }
    _resetStreamDraftState();
  }

  String _streamVisibleText(String raw) {
''',
        'chat fresh stream draft per generation',
    )

agent_path.write_text(agent, encoding='utf-8')
native_path.write_text(native, encoding='utf-8')
service_path.write_text(service, encoding='utf-8')
kotlin_path.write_text(kotlin, encoding='utf-8')
chat_path.write_text(chat, encoding='utf-8')
print('V14 streaming R2 applied: explicit UI stream bit, internal helper isolation, post-tool final streaming.')
