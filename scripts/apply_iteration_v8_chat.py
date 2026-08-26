from pathlib import Path


def patch(path: str, old: str, new: str, count: int = 1) -> None:
    p = Path(path)
    text = p.read_text(encoding='utf-8')
    actual = text.count(old)
    if actual != count:
        raise SystemExit(f'{path}: expected {count}, found {actual}: {old[:120]!r}')
    p.write_text(text.replace(old, new, count), encoding='utf-8')


chat = 'lib/features/chat/presentation/chat_screen.dart'

# One live tool-progress region per turn.
patch(
    chat,
    "  final Set<String> _announcedNativeToolIds = <String>{};\n  int? _conversationId;\n",
    "  final Set<String> _announcedNativeToolIds = <String>{};\n"
    "  // RASTACODER_V8_TURN_LAYOUT\n"
    "  final List<String> _currentToolEvents = <String>[];\n"
    "  int? _toolProgressIndex;\n"
    "  bool _toolProgressPersisted = false;\n"
    "  int? _conversationId;\n",
)

# Do not evaluate API-key/offline readiness during the temporary initializing UI.
patch(
    chat,
    "    _checkApiKey();\n    _loadSelfImproveSetting();\n",
    "    if (!widget.initializing) {\n      _syncModelRouteState();\n    }\n    _loadSelfImproveSetting();\n",
)
patch(
    chat,
    "    if (oldWidget.initializing && !widget.initializing && !_conversationLoaded) {\n      WidgetsBinding.instance.addPostFrameCallback((_) {\n        if (mounted) _initializeConversationHistory();\n      });\n    }\n",
    "    if (oldWidget.initializing && !widget.initializing) {\n      WidgetsBinding.instance.addPostFrameCallback((_) async {\n        if (!mounted) return;\n        await _syncModelRouteState();\n        if (mounted && !_conversationLoaded) {\n          await _initializeConversationHistory();\n        }\n      });\n    }\n",
)

# Restore persisted tool-process messages as a dedicated region.
patch(
    chat,
    "        'toolResult' => MessageRole.system,\n",
    "        'toolResult' => MessageRole.toolProgress,\n",
)
patch(
    chat,
    "      MessageRole.error => 'system',\n      MessageRole.system => 'system',\n",
    "      MessageRole.error => 'system',\n      MessageRole.system => 'system',\n      MessageRole.toolProgress => 'toolResult',\n",
)

# Replace the old API-key input mode with one routing source of truth.
p = Path(chat)
text = p.read_text(encoding='utf-8')
start = text.find('  Future<void> _checkApiKey() async {\n')
end = text.find('\n  void _listenToConnectivity() {', start)
if start < 0 or end < 0:
    raise SystemExit('chat_screen.dart: API key block not found')
route_block = r'''  Future<void> _syncModelRouteState() async {
    final preferredModel = await StorageService.instance.getPreferredModel();
    final modelInfo = ModelRegistry.getById(preferredModel);
    final hasKey = await StorageService.instance.hasApiKey();
    final isOffline = modelInfo?.isOffline ?? false;

    if (isOffline) {
      // Offline routing never enters Claude-key input mode. The displayed model
      // and the actual MLC runtime are synchronized to the same stored id.
      final downloaded = LocalLLMService.instance.modelStates[preferredModel]?.downloadState ==
          ModelDownloadState.downloaded;
      if (downloaded &&
          (LocalLLMService.instance.loadedModelId != preferredModel ||
              LocalLLMService.instance.loadState != LocalModelLoadState.loaded)) {
        try {
          await LocalLLMService.instance.loadModel(preferredModel);
        } catch (e) {
          debugPrint('[V8 route restore] $e');
        }
      }
      if (!mounted) return;
      setState(() {
        _hasApiKey = hasKey;
        _awaitingApiKey = false;
      });
      return;
    }

    if (!mounted) return;
    setState(() {
      _hasApiKey = hasKey;
      _awaitingApiKey = !hasKey;
    });
    if (hasKey) _sendStoredApiKeyToPython();
  }

  Future<bool> _ensureSelectedRouteReadyForSend() async {
    final preferredModel = await StorageService.instance.getPreferredModel();
    final modelInfo = ModelRegistry.getById(preferredModel);
    final isOffline = modelInfo?.isOffline ?? false;

    if (isOffline) {
      if (mounted && _awaitingApiKey) {
        setState(() => _awaitingApiKey = false);
      }
      final state = LocalLLMService.instance.modelStates[preferredModel];
      if (state?.downloadState != ModelDownloadState.downloaded) {
        _addRoutingError('已选择本地模型 ${modelInfo?.displayName ?? preferredModel}，但模型文件尚未下载完成。请在模型页面完成下载后再发送。');
        return false;
      }
      try {
        if (LocalLLMService.instance.loadedModelId != preferredModel ||
            LocalLLMService.instance.loadState != LocalModelLoadState.loaded) {
          if (mounted) setState(() => _statusMessage = '正在加载已选择的本地模型…');
          await LocalLLMService.instance.loadModel(preferredModel);
        }
      } catch (e) {
        _addRoutingError('本地模型加载失败：$e');
        return false;
      }
      if (LocalLLMService.instance.loadedModelId != preferredModel ||
          LocalLLMService.instance.loadState != LocalModelLoadState.loaded) {
        _addRoutingError('本地模型尚未进入可推理状态，请重新加载模型后再试。');
        return false;
      }
      return true;
    }

    final hasKey = await StorageService.instance.hasApiKey();
    if (mounted) {
      setState(() {
        _hasApiKey = hasKey;
        _awaitingApiKey = !hasKey;
      });
    }
    if (!hasKey) {
      _addRoutingError('当前选择的是云端模型，但尚未配置 Claude API Key。请到设置中配置 API Key，您的聊天文本不会再被当作 API Key 输入。');
      return false;
    }
    await _doSendApiKey();
    return true;
  }

  void _addRoutingError(String message) {
    if (!mounted) return;
    setState(() {
      _messages.add(ChatMessage(
        role: MessageRole.error,
        content: message,
        timestamp: DateTime.now(),
      ));
      _statusMessage = null;
    });
    _scrollToBottom();
  }

  void _sendStoredApiKeyToPython() {
    if (PythonBridge.instance.status == PythonStatus.ready) {
      _doSendApiKey();
      return;
    }
    StreamSubscription<PythonStatus>? subscription;
    subscription = PythonBridge.instance.statusStream.listen((status) {
      if (status == PythonStatus.ready) {
        _doSendApiKey();
        subscription?.cancel();
      }
    });
    Future.delayed(const Duration(seconds: 30), () => subscription?.cancel());
  }

  Future<void> _doSendApiKey() async {
    final apiKey = await StorageService.instance.getApiKey();
    if (apiKey != null) {
      try {
        await PythonBridge.instance.setApiKey(apiKey);
      } catch (e) {
        debugPrint('Failed to send API key to Python: $e');
      }
    }
  }
'''
p.write_text(text[:start] + route_block + text[end:], encoding='utf-8')

# Tool logs become one region instead of many system messages.
p = Path(chat)
text = p.read_text(encoding='utf-8')
start = text.find('  void _listenToLogs() {\n')
end = text.find('\n  String _localizeAgentLog(String msg) {', start)
if start < 0 or end < 0:
    raise SystemExit('chat_screen.dart: log listener block not found')
log_block = r'''  void _appendToolProgress(String event) {
    final clean = event.trim();
    if (!mounted || clean.isEmpty) return;
    if (_currentToolEvents.isNotEmpty && _currentToolEvents.last == clean) return;
    _currentToolEvents.add(clean);
    if (_currentToolEvents.length > 60) {
      _currentToolEvents.removeAt(0);
    }
    final content = _currentToolEvents.join('\n');
    setState(() {
      final index = _toolProgressIndex;
      if (index != null && index >= 0 && index < _messages.length &&
          _messages[index].role == MessageRole.toolProgress) {
        final previous = _messages[index];
        _messages[index] = ChatMessage(
          role: MessageRole.toolProgress,
          content: content,
          timestamp: previous.timestamp,
        );
      } else {
        _messages.add(ChatMessage(
          role: MessageRole.toolProgress,
          content: content,
          timestamp: DateTime.now(),
        ));
        _toolProgressIndex = _messages.length - 1;
      }
      _statusMessage = clean;
    });
    _scrollToBottom();
  }

  Future<void> _persistCurrentToolProgress(int conversationId) async {
    if (_toolProgressPersisted || _currentToolEvents.isEmpty) return;
    _toolProgressPersisted = true;
    await ConversationManager.instance.storeVisibleMessage(
      conversationId: conversationId,
      role: 'toolResult',
      content: _currentToolEvents.join('\n'),
    );
  }

  void _listenToLogs() {
    PythonBridge.instance.logStream.listen((log) {
      if (!mounted || !_isProcessing) return;
      final msg = log.message;

      if (msg.startsWith('Tool:')) {
        _appendToolProgress('准备调用工具：${msg.substring('Tool:'.length).trim()}');
      } else if (msg.startsWith('Executing')) {
        _appendToolProgress('正在执行${msg.substring('Executing'.length)}');
      } else if (msg.startsWith('Result:')) {
        _appendToolProgress('工具调用成功：${msg.substring('Result:'.length).trim()}');
      } else if (msg.startsWith('File:')) {
        _appendToolProgress('已生成文件：${msg.substring('File:'.length).trim()}');
      } else if (msg.startsWith('Tool error:')) {
        _appendToolProgress('工具调用失败：${msg.substring('Tool error:'.length).trim()}');
      } else if (msg.startsWith('Tool exception:')) {
        _appendToolProgress('工具调用失败：${msg.substring('Tool exception:'.length).trim()}');
      }

      if (log.hasProgress) {
        if (log.progress! < 1.0) {
          setState(() => _statusMessage = '${log.message} (${(log.progress! * 100).toInt()}%)');
        }
      } else if (!msg.startsWith('Thinking:') &&
          !msg.startsWith('Code:') &&
          !msg.startsWith('Tool compatibility:')) {
        setState(() => _statusMessage = _localizeAgentLog(msg));
      }
    });
  }

  void _listenToNativeTools() {
    _nativeToolSubscription = PythonBridge.instance.nativeToolStream.listen((request) {
      if (!mounted || !_isProcessing) return;
      if (!_announcedNativeToolIds.add(request.id)) return;
      _appendToolProgress('正在调用工具：${request.tool}');
    });
  }
'''
p.write_text(text[:start] + log_block + text[end:], encoding='utf-8')

# Routing is verified BEFORE accepting the user's message into a turn.
patch(
    chat,
    "    // Handle API key input\n    if (_awaitingApiKey) {\n      await _handleApiKeyInput(text);\n      return;\n    }\n\n    final conversationId = await _ensureConversation();\n",
    "    // V8: synchronize displayed selection with the actual inference route.\n"
    "    if (!await _ensureSelectedRouteReadyForSend()) return;\n\n"
    "    _currentToolEvents.clear();\n"
    "    _toolProgressIndex = null;\n"
    "    _toolProgressPersisted = false;\n"
    "    _announcedNativeToolIds.clear();\n\n"
    "    final conversationId = await _ensureConversation();\n",
)

# Attach generated files to the final assistant region and persist one tool process region.
patch(
    chat,
    "            diagnostics: diagnostics,\n          ));\n          // Add tappable file links for every created file\n          if (createdFiles != null && !hasError) {\n            for (final filePath in createdFiles) {\n              _messages.add(ChatMessage(\n                role: MessageRole.system,\n                content: '\\u{1F4CE} File: $filePath',\n                timestamp: DateTime.now(),\n              ));\n            }\n          }\n        });\n        await ConversationManager.instance.storeVisibleMessage(\n",
    "            diagnostics: diagnostics,\n"
    "            attachments: !hasError && createdFiles != null\n"
    "                ? createdFiles.map((e) => e.toString()).toList()\n"
    "                : null,\n"
    "          ));\n"
    "        });\n"
    "        await _persistCurrentToolProgress(conversationId);\n"
    "        await ConversationManager.instance.storeVisibleMessage(\n",
)
# Remove old per-file system-message persistence.
p = Path(chat)
text = p.read_text(encoding='utf-8')
old = "        if (createdFiles != null && !hasError) {\n          for (final filePath in createdFiles) {\n            await ConversationManager.instance.storeVisibleMessage(\n              conversationId: conversationId,\n              role: 'system',\n              content: '\\u{1F4CE} File: $filePath',\n            );\n          }\n        }\n"
if text.count(old) != 1:
    raise SystemExit('chat_screen.dart: old created-file persistence block missing')
text = text.replace(old, '', 1)
p.write_text(text, encoding='utf-8')

# Persist tool process before explicit response errors as well.
patch(
    chat,
    "      } else if (response.isError) {\n        final errorText = response.error?.message ?? '未知错误';\n",
    "      } else if (response.isError) {\n"
    "        await _persistCurrentToolProgress(conversationId);\n"
    "        final errorText = response.error?.message ?? '未知错误';\n",
)

# Returning from settings always resynchronizes the actual route; no chat-system notices.
p = Path(chat)
text = p.read_text(encoding='utf-8')
start = text.find('  void _openMenu() async {\n')
end = text.find('\n  void _connectGoogle() {', start)
if start < 0 or end < 0:
    raise SystemExit('chat_screen.dart: _openMenu block not found')
open_menu = r'''  void _openMenu() async {
    await Navigator.pushNamed(context, '/settings');
    await _loadSelfImproveSetting();
    await _loadSkillDefaults();
    await _syncModelRouteState();
  }
'''
p.write_text(text[:start] + open_menu + text[end:], encoding='utf-8')

# Input is normal chat input only; API keys live in Settings.
patch(
    chat,
    "              enabled: (isPythonReady || _awaitingApiKey) && !_isProcessing,\n",
    "              enabled: isPythonReady && !_isProcessing,\n",
)

# Dedicated message role.
patch(
    chat,
    "  assistant,\n  system,\n  error,\n",
    "  assistant,\n  toolProgress,\n  system,\n  error,\n",
)

# ---------------------------------------------------------------------------
# MessageBubble: one semantic tree, one actual toggle state, no debug prose.
# ---------------------------------------------------------------------------
bubble = 'lib/features/chat/presentation/widgets/message_bubble.dart'
patch(
    bubble,
    "    return Semantics(\n      label: _accessibilityLabel,\n      hint: '长按可打开消息操作',\n      container: true,\n      explicitChildNodes: true,\n",
    "    return Semantics(\n      container: true,\n      explicitChildNodes: true,\n",
)
# Remove the verbose parent accessibility label getter entirely.
p = Path(bubble)
text = p.read_text(encoding='utf-8')
start = text.find('  String get _accessibilityLabel {\n')
end = text.find('\n  MainAxisAlignment get _alignment {', start)
if start < 0 or end < 0:
    raise SystemExit('message_bubble.dart: accessibility getter not found')
text = text[:start] + text[end:]
p.write_text(text, encoding='utf-8')

# Add role cases.
patch(
    bubble,
    "      case MessageRole.assistant:\n      case MessageRole.system:\n      case MessageRole.error:\n",
    "      case MessageRole.assistant:\n      case MessageRole.toolProgress:\n      case MessageRole.system:\n      case MessageRole.error:\n",
)
patch(
    bubble,
    "      case MessageRole.assistant:\n        return NavixTheme.surface;\n      case MessageRole.system:\n",
    "      case MessageRole.assistant:\n        return NavixTheme.surface;\n"
    "      case MessageRole.toolProgress:\n        return NavixTheme.surfaceVariant;\n"
    "      case MessageRole.system:\n",
)

# Dedicated tool-process content region.
patch(
    bubble,
    "    if (message.role == MessageRole.assistant) {\n      return _buildAssistantContent(context);\n    }\n\n    if (message.role == MessageRole.error) {\n",
    "    if (message.role == MessageRole.assistant) {\n      return _buildAssistantContent(context);\n    }\n\n"
    "    if (message.role == MessageRole.toolProgress) {\n"
    "      return Column(\n"
    "        crossAxisAlignment: CrossAxisAlignment.start,\n"
    "        children: [\n"
    "          Text('工具调用过程', style: Theme.of(context).textTheme.labelLarge?.copyWith(color: NavixTheme.textSecondary)),\n"
    "          const SizedBox(height: 6),\n"
    "          SelectableText(message.content, style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: NavixTheme.textPrimary)),\n"
    "        ],\n"
    "      );\n"
    "    }\n\n"
    "    if (message.role == MessageRole.error) {\n",
)

# Replace assistant layout wholesale so it is: thinking toggle -> final answer -> files -> diagnostics toggle.
p = Path(bubble)
text = p.read_text(encoding='utf-8')
start = text.find('  Widget _buildAssistantContent(BuildContext context) {\n')
end = text.find('\n  Widget _buildDiagnosticsPanel(BuildContext context, String diagnostics) {', start)
if start < 0 or end < 0:
    raise SystemExit('message_bubble.dart: assistant content block not found')
assistant_block = r'''  Widget _buildAssistantContent(BuildContext context) {
    final parts = _splitThinking(message.content);
    final explicitThinking = message.thinking?.trim() ?? '';
    final thinking = explicitThinking.isNotEmpty ? explicitThinking : parts[0];
    final answer = parts[1];
    final widgets = <Widget>[];

    // A local-model turn always has one predictable thinking control. When
    // thinking was disabled or the model emitted none, expanding says so.
    final showThinkingControl = message.thinkingMode != null || thinking.isNotEmpty;
    if (showThinkingControl) {
      widgets.add(
        _AccessibleExpansionSection(
          semanticTitle: '思考过程',
          child: Align(
            alignment: Alignment.centerLeft,
            child: SelectableText(
              thinking.isEmpty ? '本轮AI未输出思考内容。' : thinking,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: NavixTheme.textTertiary,
                  ),
            ),
          ),
        ),
      );
      widgets.add(const SizedBox(height: 8));
    }

    if (answer.isNotEmpty) {
      widgets.add(_buildTextContent(context, answer));
    } else {
      widgets.add(Text(
        'AI本轮未返回文本回复。',
        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: NavixTheme.textSecondary,
            ),
      ));
    }

    final needsGoogleConnect = !AuthService.instance.isSignedIn &&
        _mentionsGoogleConnect(answer);
    if (needsGoogleConnect) {
      widgets.add(const SizedBox(height: 12));
      widgets.add(ElevatedButton.icon(
        onPressed: () async {
          try {
            final account = await AuthService.instance.signIn();
            if (context.mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text(account != null ? 'Google 账号已连接' : '已取消登录')),
              );
            }
          } catch (e) {
            if (context.mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text('Google 登录失败：$e')),
              );
            }
          }
        },
        icon: const Icon(Icons.account_circle, size: 18),
        label: const Text('连接 Google 账号'),
      ));
    }

    if (message.attachments?.isNotEmpty ?? false) {
      widgets.add(const SizedBox(height: 10));
      for (final path in message.attachments!) {
        widgets.add(Padding(
          padding: const EdgeInsets.only(bottom: 6),
          child: _buildFileLinkForPath(context, path),
        ));
      }
    }

    if (message.diagnostics?.trim().isNotEmpty ?? false) {
      widgets.add(const SizedBox(height: 8));
      widgets.add(_buildDiagnosticsPanel(context, message.diagnostics!.trim()));
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: widgets,
    );
  }
'''
p.write_text(text[:start] + assistant_block + text[end:], encoding='utf-8')

# File links can live inside the final assistant region.
patch(
    bubble,
    "  Widget _buildFileLink(BuildContext context) {\n    final filePath = message.content.replaceFirst('📎 File: ', '').trim();\n    final fileName = filePath.split('/').last;\n\n    return Row(\n",
    "  Widget _buildFileLink(BuildContext context) {\n"
    "    final filePath = message.content.replaceFirst('📎 File: ', '').trim();\n"
    "    return _buildFileLinkForPath(context, filePath);\n"
    "  }\n\n"
    "  Widget _buildFileLinkForPath(BuildContext context, String filePath) {\n"
    "    final fileName = filePath.split('/').last;\n\n"
    "    return Row(\n",
)

# Replace ExpansionTile with one stateful semantic button and conditional body.
p = Path(bubble)
text = p.read_text(encoding='utf-8')
start = text.find('class _AccessibleExpansionSection extends StatefulWidget {\n')
end = text.find('\nclass _RoleIndicator extends StatelessWidget {', start)
if start < 0 or end < 0:
    raise SystemExit('message_bubble.dart: expansion section block not found')
expansion = r'''class _AccessibleExpansionSection extends StatefulWidget {
  final String semanticTitle;
  final Widget child;

  const _AccessibleExpansionSection({
    required this.semanticTitle,
    required this.child,
  });

  @override
  State<_AccessibleExpansionSection> createState() =>
      _AccessibleExpansionSectionState();
}

class _AccessibleExpansionSectionState
    extends State<_AccessibleExpansionSection> {
  bool _expanded = false;

  void _toggle() => setState(() => _expanded = !_expanded);

  @override
  Widget build(BuildContext context) {
    final stateLabel = _expanded ? '已展开' : '已折叠';
    final actionLabel = _expanded ? '双击收起' : '双击展开';
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Semantics(
          container: true,
          button: true,
          label: '${widget.semanticTitle}，当前$stateLabel，$actionLabel',
          onTap: _toggle,
          child: ExcludeSemantics(
            child: InkWell(
              onTap: _toggle,
              borderRadius: BorderRadius.circular(8),
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 8),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      _expanded ? '${widget.semanticTitle}（收起）' : '${widget.semanticTitle}（展开）',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: NavixTheme.textSecondary,
                          ),
                    ),
                    const SizedBox(width: 4),
                    Icon(
                      _expanded ? Icons.expand_less : Icons.expand_more,
                      size: 20,
                      color: NavixTheme.textSecondary,
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
        if (_expanded)
          Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: widget.child,
          ),
      ],
    );
  }
}
'''
p.write_text(text[:start] + expansion + text[end:], encoding='utf-8')

# Decorative role symbols such as ◆ must never be spoken.
patch(
    bubble,
    "  Widget build(BuildContext context) {\n    return Padding(\n      padding: const EdgeInsets.symmetric(horizontal: 8),\n      child: Container(\n",
    "  Widget build(BuildContext context) {\n"
    "    return ExcludeSemantics(\n"
    "      child: Padding(\n"
    "        padding: const EdgeInsets.symmetric(horizontal: 8),\n"
    "        child: Container(\n",
)
# Close the extra ExcludeSemantics around _RoleIndicator's Padding. Target the
# exact tail before String get _icon.
patch(
    bubble,
    "        ),\n      ),\n    );\n  }\n\n  String get _icon {\n",
    "        ),\n      ),\n    );\n      ),\n    );\n  }\n\n  String get _icon {\n",
)
# New role in role-indicator switches, though decorative indicator is normally
# only instantiated for user/assistant.
patch(
    bubble,
    "      case MessageRole.assistant:\n        return '◆';\n      case MessageRole.system:\n",
    "      case MessageRole.assistant:\n        return '◆';\n"
    "      case MessageRole.toolProgress:\n        return '↻';\n"
    "      case MessageRole.system:\n",
)
patch(
    bubble,
    "      case MessageRole.assistant:\n        return NavixTheme.accentCyan;\n      case MessageRole.system:\n",
    "      case MessageRole.assistant:\n        return NavixTheme.accentCyan;\n"
    "      case MessageRole.toolProgress:\n        return NavixTheme.textSecondary;\n"
    "      case MessageRole.system:\n",
)

print('V8 chat patch applied successfully')
