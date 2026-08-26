#!/usr/bin/env python3
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"v7 UI patch anchor missing: {label}")
    return text.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Model persistence: local-first default + actual cold-start runtime restore.
# ---------------------------------------------------------------------------
p = Path('lib/core/services/storage_service.dart')
text = p.read_text()
text = replace_once(
    text,
    "  /// Get preferred model (default: 'auto')\n  Future<String> getPreferredModel() async {\n    final value = await _storage.read(key: _keyPreferredModel);\n    return value ?? 'auto';\n  }\n",
    "  /// Get preferred model. Fresh installs default to the on-device Qwen3 4B;\n"
    "  /// an explicit cloud selection such as 'auto' is still persisted verbatim.\n"
    "  Future<String> getPreferredModel() async {\n"
    "    final value = await _storage.read(key: _keyPreferredModel);\n"
    "    return value ?? 'qwen3-4b';\n"
    "  }\n",
    'local-first model default',
)
p.write_text(text)

p = Path('lib/main.dart')
text = p.read_text()
text = replace_once(
    text,
    "import 'core/services/local_llm_service.dart';\n",
    "import 'core/services/local_llm_service.dart';\n"
    "import 'core/services/storage_service.dart';\n"
    "import 'core/models/model_registry.dart';\n",
    'main model restore imports',
)
text = replace_once(
    text,
    "  // Initialize local LLM service (scans disk for downloaded models)\n"
    "  await LocalLLMService.instance.initialize();\n\n"
    "  // Phase 3: Python init (runs async, doesn't block UI)\n",
    "  // Initialize local LLM service (scans disk for downloaded models).\n"
    "  await LocalLLMService.instance.initialize();\n\n"
    "  // RASTACODER_V7_LOCAL_MODEL_RESTORE\n"
    "  // Persisting a model ID is not enough: after process death the native MLC\n"
    "  // engine is empty. Restore the last explicitly selected local model so the\n"
    "  // app does not appear to jump back to cloud/Auto after every restart.\n"
    "  final preferredModel = await StorageService.instance.getPreferredModel();\n"
    "  final preferredInfo = ModelRegistry.getById(preferredModel);\n"
    "  if (preferredInfo != null && preferredInfo.isOffline) {\n"
    "    try {\n"
    "      if (await LocalLLMService.instance.isModelDownloaded(preferredModel)) {\n"
    "        await LocalLLMService.instance.loadModel(preferredModel);\n"
    "      }\n"
    "    } catch (e) {\n"
    "      // Keep the user's selection even if the OS/driver cannot load it now;\n"
    "      // the normal on-demand load path can retry and surface the real error.\n"
    "      debugPrint('Preferred local model restore failed: $e');\n"
    "    }\n"
    "  }\n\n"
    "  // Phase 3: Python init (runs async, doesn't block UI)\n",
    'cold start model restore',
)
p.write_text(text)

# Selecting a model in Settings should change both persistent preference and
# live MLC state, rather than leaving a stale runtime until the next query.
p = Path('lib/features/settings/settings_screen.dart')
text = p.read_text()
old = '''            onChanged: (model) async {
              await StorageService.instance.setPreferredModel(model);
              setState(() => _preferredModel = model);
            },
'''
new = '''            onChanged: (model) async {
              await StorageService.instance.setPreferredModel(model);
              final info = ModelRegistry.getById(model);
              if (info != null && info.isOffline) {
                final downloaded = await LocalLLMService.instance.isModelDownloaded(model);
                if (downloaded) {
                  await LocalLLMService.instance.loadModel(model);
                }
              } else if (LocalLLMService.instance.loadedModelId != null) {
                await LocalLLMService.instance.unloadModel();
              }
              if (mounted) setState(() => _preferredModel = model);
            },
'''
text = replace_once(text, old, new, 'settings live model selection')
p.write_text(text)


# ---------------------------------------------------------------------------
# App-bar accessibility: explicit semantic buttons, independent of tooltip.
# ---------------------------------------------------------------------------
p = Path('lib/features/chat/presentation/chat_screen.dart')
text = p.read_text()
old = '''          IconButton(
            onPressed: _isProcessing ? null : _openConversationHistory,
            icon: const Icon(Icons.history),
            tooltip: '聊天记录',
          ),
          IconButton(
            onPressed: _isProcessing ? null : _startNewConversation,
            icon: const Icon(Icons.add_comment_outlined),
            tooltip: '新建对话',
          ),
'''
new = '''          Semantics(
            button: true,
            label: '聊天记录',
            hint: '打开对话历史记录',
            enabled: !_isProcessing,
            child: IconButton(
              onPressed: _isProcessing ? null : _openConversationHistory,
              icon: const Icon(Icons.history),
              tooltip: '聊天记录',
            ),
          ),
          Semantics(
            button: true,
            label: '新建对话',
            hint: '创建一个新的聊天会话',
            enabled: !_isProcessing,
            child: IconButton(
              onPressed: _isProcessing ? null : _startNewConversation,
              icon: const Icon(Icons.add_comment_outlined),
              tooltip: '新建对话',
            ),
          ),
'''
text = replace_once(text, old, new, 'chat history/new chat semantics')
p.write_text(text)


# ---------------------------------------------------------------------------
# Message semantics: V6 excludeSemantics swallowed the nested ExpansionTile
# controls. Keep a concise parent summary but preserve explicit child nodes so
# screen readers can focus and activate Thinking/Diagnostics separately.
# ---------------------------------------------------------------------------
p = Path('lib/features/chat/presentation/widgets/message_bubble.dart')
text = p.read_text()
text = replace_once(
    text,
    "    return Semantics(\n      label: _accessibilityLabel,\n      hint: '长按可复制',\n      excludeSemantics: true,\n",
    "    return Semantics(\n"
    "      label: _accessibilityLabel,\n"
    "      hint: '长按可打开消息操作',\n"
    "      container: true,\n"
    "      explicitChildNodes: true,\n",
    'message semantics tree',
)
old_getter = '''  String get _accessibilityLabel {
    final roleLabel = switch (message.role) {
      MessageRole.user => '您说',
      MessageRole.assistant => 'RastaCoder 回复',
      MessageRole.system => '系统消息',
      MessageRole.error => '错误',
    };
    final visibleContent = message.role == MessageRole.assistant
        ? _splitThinking(message.content)[1]
        : message.content;
    final hasThinking = (message.thinking?.trim().isNotEmpty ?? false) ||
        (message.role == MessageRole.assistant && _splitThinking(message.content)[0].isNotEmpty);
    final hasDiagnostics = message.diagnostics?.trim().isNotEmpty ?? false;
    final extras = <String>[
      if (hasThinking) '包含可展开的思考过程',
      if (message.thinkingMode != null && !hasThinking) '包含思考模式状态',
      if (hasDiagnostics) '包含可展开并复制或分享的工具调用诊断',
    ];
    return '$roleLabel：$visibleContent${extras.isEmpty ? '' : '。${extras.join('；')}'}';
  }
'''
new_getter = '''  String get _accessibilityLabel {
    final roleLabel = switch (message.role) {
      MessageRole.user => '您的消息',
      MessageRole.assistant => 'RastaCoder 回复',
      MessageRole.system => '系统消息',
      MessageRole.error => '错误消息',
    };
    final hasThinking = (message.thinking?.trim().isNotEmpty ?? false) ||
        (message.role == MessageRole.assistant && _splitThinking(message.content)[0].isNotEmpty);
    final hasDiagnostics = message.diagnostics?.trim().isNotEmpty ?? false;
    final extras = <String>[
      if (hasThinking) '下方有独立的思考过程展开按钮',
      if (hasDiagnostics) '下方有独立的工具调用诊断展开按钮',
    ];
    return '$roleLabel${extras.isEmpty ? '' : '，${extras.join('，')}'}';
  }
'''
text = replace_once(text, old_getter, new_getter, 'message accessibility label')

# Mark each expansion tile itself as a separate semantic container. This is in
# addition to its button title and prevents the outer message node from merging
# it back into ordinary response text.
text = text.replace(
    "          child: ExpansionTile(\n            tilePadding: EdgeInsets.zero,\n            childrenPadding: const EdgeInsets.only(bottom: 10),",
    "          child: Semantics(\n            container: true,\n            explicitChildNodes: true,\n            child: ExpansionTile(\n            tilePadding: EdgeInsets.zero,\n            childrenPadding: const EdgeInsets.only(bottom: 10),",
    1,
)
text = text.replace(
    "            ],\n          ),\n        ),\n      );\n    }\n\n    if (message.thinkingMode != null)",
    "            ],\n            ),\n          ),\n        ),\n      );\n    }\n\n    if (message.thinkingMode != null)",
    1,
)

# Diagnostics uses the same independent semantic-container pattern.
diag_anchor = '''      child: ExpansionTile(
        tilePadding: EdgeInsets.zero,
        childrenPadding: const EdgeInsets.only(bottom: 8),
'''
diag_new = '''      child: Semantics(
        container: true,
        explicitChildNodes: true,
        child: ExpansionTile(
        tilePadding: EdgeInsets.zero,
        childrenPadding: const EdgeInsets.only(bottom: 8),
'''
text = replace_once(text, diag_anchor, diag_new, 'diagnostics semantic container')
diag_close = '''          ),
        ],
      ),
    );
  }

  Widget _buildTextContent'''
diag_close_new = '''          ),
        ],
        ),
      ),
    );
  }

  Widget _buildTextContent'''
text = replace_once(text, diag_close, diag_close_new, 'diagnostics semantic close')
p.write_text(text)

print('Applied RastaCoder v7 accessibility and local-model persistence patch')
