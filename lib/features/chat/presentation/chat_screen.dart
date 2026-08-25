import 'dart:async';

import 'package:flutter/material.dart';

import '../../../app/theme.dart';
import '../../../core/bridge/bridge.dart';
import '../../../core/constants/defaults.dart';
import '../../../core/services/analytics_service.dart';
import '../../../core/services/auth_service.dart';
import '../../../core/services/connectivity_service.dart';
import '../../../core/services/conversation_manager.dart';
import '../../../core/models/model_registry.dart';
import '../../../core/models/tool_skill.dart';
import '../../../core/services/local_llm_service.dart';
import '../../../core/services/offline_queue_manager.dart';
import '../../../core/services/share_receiver_service.dart';
import '../../../core/services/storage_service.dart';
import '../../../shared/widgets/spinner.dart';
import 'widgets/message_list.dart';
import 'widgets/input_bar.dart';
import 'widgets/status_banner.dart';
import 'widgets/context_bar.dart';
import 'conversation_history_screen.dart';
import '../../settings/tool_skills_screen.dart';

/// Main chat screen - the "Living Log" interface
class ChatScreen extends StatefulWidget {
  final bool initializing;

  const ChatScreen({
    super.key,
    this.initializing = false,
  });

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> with WidgetsBindingObserver {
  final _inputController = TextEditingController();
  final _scrollController = ScrollController();
  final _messages = <ChatMessage>[];
  bool _isProcessing = false;
  String? _statusMessage;
  String? _activeMode;
  List<String> _attachedFiles = [];
  bool _isGoogleConnected = false;
  bool _showQuickActions = true;
  bool _awaitingApiKey = false;
  bool _hasApiKey = false;
  bool _selfImproveEnabled = false;
  double _lastKeyboardHeight = 0;
  bool _pendingMetricsCheck = false;
  List<String> _externalFiles = [];
  StreamSubscription<SharedFilesEvent>? _shareSubscription;
  StreamSubscription? _nativeToolSubscription;
  StreamSubscription<Map<String, dynamic>>? _mlcEventSubscription;
  Set<String> _enabledSkills = Set<String>.from(LocalToolSkillCatalog.allIds);
  final Set<String> _announcedNativeToolIds = <String>{};
  int? _conversationId;
  String _conversationTitle = '新对话';
  bool _conversationLoaded = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _checkApiKey();
    _loadSelfImproveSetting();
    _loadSkillDefaults();
    _listenToPythonStatus();
    _listenToLogs();
    _listenToNativeTools();
    _listenToMlcEvents();
    _listenToConnectivity();
    _listenToAuth();
    _listenToSharedFiles();
    if (!widget.initializing) {
      WidgetsBinding.instance.addPostFrameCallback((_) => _initializeConversationHistory());
    }
  }

  @override
  void didUpdateWidget(covariant ChatScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.initializing && !widget.initializing && !_conversationLoaded) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) _initializeConversationHistory();
      });
    }
  }

  @override
  void didChangeMetrics() {
    super.didChangeMetrics();
    // Scroll to bottom when keyboard appears.
    // Debounce: only check once per frame to avoid lag from repeated metric changes.
    if (_pendingMetricsCheck) return;
    _pendingMetricsCheck = true;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _pendingMetricsCheck = false;
      if (!mounted) return;
      final keyboardHeight = MediaQuery.of(context).viewInsets.bottom;
      if (keyboardHeight > _lastKeyboardHeight && _messages.isNotEmpty) {
        _scrollToBottom();
      }
      _lastKeyboardHeight = keyboardHeight;
    });
  }


  // RASTACODER_V5_SKILLS_PARAMS_BENCH_STREAM
  Future<void> _loadSkillDefaults() async {
    final enabled = await StorageService.instance.getLocalEnabledSkills();
    if (!mounted) return;
    setState(() => _enabledSkills = enabled);
  }

  Future<void> _manageTools() async {
    final result = await Navigator.push<Set<String>>(
      context,
      MaterialPageRoute(
        builder: (_) => ToolSkillsScreen(
          initialEnabled: Set<String>.from(_enabledSkills),
          persistAsDefaults: false,
        ),
      ),
    );
    if (result != null && mounted) {
      setState(() => _enabledSkills = result);
    }
  }

  void _listenToMlcEvents() {
    _mlcEventSubscription = LocalLLMService.instance.inferenceEventStream.listen((event) {
      if (!mounted || !_isProcessing) return;
      final phase = event['phase']?.toString();
      String? message;
      switch (phase) {
        case 'generation_started':
          message = '本地模型开始生成…';
          break;
        case 'first_token':
          final ms = event['elapsed_ms'];
          message = ms == null ? '已生成首个 Token' : '已生成首个 Token（${ms} ms）';
          break;
        case 'thinking_started':
          message = '正在思考…';
          break;
        case 'tool_call_started':
          message = '正在形成工具调用…';
          break;
        case 'generation_completed':
          message = '模型生成完成，正在处理响应…';
          break;
      }
      if (message != null) setState(() => _statusMessage = message);
    }, onError: (Object error) {
      debugPrint('[MLC telemetry] $error');
    });
  }

  Future<void> _initializeConversationHistory() async {
    if (_conversationLoaded || widget.initializing) return;
    final summaries = await ConversationManager.instance.listConversationSummaries();
    if (!mounted) return;
    if (summaries.isEmpty) {
      await _startNewConversation();
      return;
    }
    final newest = summaries.first;
    await _loadConversation(newest['id'] as int, newest['title']?.toString() ?? '未命名对话');
  }

  Future<int> _ensureConversation() async {
    if (_conversationId != null) return _conversationId!;
    final conversation = await ConversationManager.instance.createConversation(title: '新对话');
    if (mounted) {
      setState(() {
        _conversationId = conversation.id;
        _conversationTitle = conversation.title;
        _conversationLoaded = true;
      });
    }
    return conversation.id;
  }

  Future<void> _loadConversation(int id, String title) async {
    final rows = await ConversationManager.instance.getVisibleMessages(id);
    if (!mounted) return;
    final restored = rows.map((row) {
      final role = switch (row['role']?.toString()) {
        'user' => MessageRole.user,
        'assistant' => MessageRole.assistant,
        'toolResult' => MessageRole.system,
        _ => MessageRole.system,
      };
      final attachments = (row['attachments'] as List?)?.map((e) => e.toString()).toList();
      return ChatMessage(
        role: role,
        content: row['content']?.toString() ?? '',
        timestamp: row['createdAt'] is DateTime ? row['createdAt'] as DateTime : DateTime.now(),
        attachments: attachments?.isNotEmpty == true ? attachments : null,
      );
    }).toList();
    setState(() {
      _conversationId = id;
      _conversationTitle = title;
      _conversationLoaded = true;
      _messages
        ..clear()
        ..addAll(restored);
      _attachedFiles = [];
      _externalFiles = [];
    });
    if (PythonBridge.instance.status == PythonStatus.ready) {
      await ConversationManager.instance.loadConversation(id);
    }
    _scrollToBottom();
  }

  Future<void> _startNewConversation() async {
    if (_isProcessing) return;
    final conversation = await ConversationManager.instance.createConversation(title: '新对话');
    if (!mounted) return;
    setState(() {
      _conversationId = conversation.id;
      _conversationTitle = conversation.title;
      _conversationLoaded = true;
      _messages.clear();
      _attachedFiles = [];
      _externalFiles = [];
      _activeMode = null;
      _statusMessage = null;
    });
  }

  Future<void> _openConversationHistory() async {
    if (_isProcessing) return;
    final selected = await Navigator.push<int>(
      context,
      MaterialPageRoute(
        builder: (_) => ConversationHistoryScreen(currentConversationId: _conversationId),
      ),
    );
    if (!mounted || selected == null) return;
    if (selected == -1) {
      await _startNewConversation();
      return;
    }
    final summaries = await ConversationManager.instance.listConversationSummaries();
    final match = summaries.where((row) => row['id'] == selected).toList();
    if (match.isEmpty) {
      await _startNewConversation();
      return;
    }
    await _loadConversation(selected, match.first['title']?.toString() ?? '未命名对话');
  }

  Future<void> _persistVisibleMessage(
    MessageRole role,
    String content, {
    List<String>? attachments,
  }) async {
    final id = await _ensureConversation();
    final dbRole = switch (role) {
      MessageRole.user => 'user',
      MessageRole.assistant => 'assistant',
      MessageRole.error => 'system',
      MessageRole.system => 'system',
    };
    await ConversationManager.instance.storeVisibleMessage(
      conversationId: id,
      role: dbRole,
      content: content,
      attachmentPaths: attachments,
    );
  }

  Future<void> _autoTitleConversation(String userText) async {
    final id = _conversationId;
    if (id == null || _conversationTitle != '新对话') return;
    var title = userText.trim().replaceAll(RegExp(r'\s+'), ' ');
    if (title.isEmpty && _attachedFiles.isNotEmpty) {
      title = _attachedFiles.first.split('/').last;
    }
    if (title.isEmpty) return;
    if (title.length > 28) title = '${title.substring(0, 28)}…';
    await ConversationManager.instance.renameConversation(id, title);
    if (mounted) setState(() => _conversationTitle = title);
  }

  Future<void> _loadSelfImproveSetting() async {
    final enabled = await StorageService.instance.isSelfImproveEnabled();
    if (mounted) {
      setState(() => _selfImproveEnabled = enabled);
    }
  }

  Future<void> _checkApiKey() async {
    final hasKey = await StorageService.instance.hasApiKey();

    // Check if an offline model is selected and downloaded
    final preferredModel = await StorageService.instance.getPreferredModel();
    final modelInfo = ModelRegistry.getById(preferredModel);
    final isOfflineSelected = modelInfo != null && modelInfo.isOffline;
    final offlineReady = isOfflineSelected &&
        LocalLLMService.instance.modelStates[preferredModel]?.downloadState ==
            ModelDownloadState.downloaded;

    setState(() {
      _hasApiKey = hasKey;
      if (!hasKey && !offlineReady) {
        _awaitingApiKey = true;
        _messages.add(ChatMessage(
          role: MessageRole.system,
          content: '欢迎使用 RastaCoder！您可以在设置中配置 Claude API Key，或者直接选择并下载本地模型，在设备端离线运行。',
          timestamp: DateTime.now(),
        ));
      }
    });

    // If we have an API key, send it to Python when bridge is ready
    if (hasKey) {
      _sendStoredApiKeyToPython();
    }
  }

  void _sendStoredApiKeyToPython() {
    // Try immediately if ready
    if (PythonBridge.instance.status == PythonStatus.ready) {
      _doSendApiKey();
      return;
    }

    // Otherwise, listen for ready status
    StreamSubscription<PythonStatus>? subscription;
    subscription = PythonBridge.instance.statusStream.listen((status) {
      if (status == PythonStatus.ready) {
        _doSendApiKey();
        subscription?.cancel();
      }
    });

    // Clean up after a reasonable timeout
    Future.delayed(const Duration(seconds: 30), () {
      subscription?.cancel();
    });
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

  Future<void> _handleApiKeyInput(String input) async {
    final key = input.trim();
    _inputController.clear();

    // Basic validation - Claude API keys start with "sk-"
    if (!key.startsWith('sk-')) {
      setState(() {
        _messages.add(ChatMessage(
          role: MessageRole.system,
          content: '这个 Claude API Key 格式看起来不正确，应当以 "sk-" 开头，请重新输入。',
          timestamp: DateTime.now(),
        ));
      });
      _scrollToBottom();
      return;
    }

    // Save the API key
    await StorageService.instance.setApiKey(key);

    setState(() {
      _awaitingApiKey = false;
      _hasApiKey = true;
      _messages.add(ChatMessage(
        role: MessageRole.system,
        content: 'API Key 已保存，现在可以开始对话。',
        timestamp: DateTime.now(),
      ));
    });
    _scrollToBottom();

    // Send the API key to Python bridge
    await PythonBridge.instance.setApiKey(key);
  }

  void _listenToConnectivity() {
    ConnectivityService.instance.statusStream.listen((isConnected) {
      setState(() {});
    });
  }

  void _listenToAuth() {
    // Set initial state
    _isGoogleConnected = AuthService.instance.isSignedIn;

    // Listen for changes (sign-in / sign-out from Settings)
    AuthService.instance.userStream.listen((user) {
      if (mounted) {
        setState(() {
          _isGoogleConnected = user != null;
        });
      }
    });
  }

  void _listenToSharedFiles() {
    _shareSubscription = ShareReceiverService.instance.stream.listen((event) {
      _applySharedFiles(event);
    });

    // Check for buffered cold-start event — must defer to after build
    // to avoid setState() during build.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      final pending = ShareReceiverService.instance.consumePending();
      if (pending != null) {
        _applySharedFiles(pending);
      }
    });
  }

  void _applySharedFiles(SharedFilesEvent event) {
    final validFiles = <String>[];
    final errors = <String>[];

    for (final file in event.files) {
      if (file.error != null) {
        errors.add(file.error!);
      } else if (file.path.isNotEmpty) {
        validFiles.add(file.path);
      }
    }

    setState(() {
      // Show error messages for failed files
      for (final error in errors) {
        _messages.add(ChatMessage(
          role: MessageRole.error,
          content: error,
          timestamp: DateTime.now(),
        ));
      }

      if (validFiles.isNotEmpty) {
        // Append to existing attached files
        _attachedFiles = [..._attachedFiles, ...validFiles];
        _externalFiles = [..._externalFiles, ...validFiles];

        _messages.add(ChatMessage(
          role: MessageRole.system,
          content: '已接收 ${validFiles.length} 个分享文件，请输入要求后发送。',
          timestamp: DateTime.now(),
        ));
      }

      // If extra text was shared, put it in the input field
      if (event.text != null && event.text!.isNotEmpty) {
        _inputController.text = event.text!;
        _inputController.selection = TextSelection.fromPosition(
          TextPosition(offset: event.text!.length),
        );
      }
    });

    _scrollToBottom();
  }

  void _listenToPythonStatus() {
    PythonBridge.instance.statusStream.listen((status) {
      setState(() {
        switch (status) {
          case PythonStatus.initializing:
            _statusMessage = '正在初始化…';
            break;
          case PythonStatus.importing:
            _statusMessage = '正在加载模块…';
            break;
          case PythonStatus.ready:
            _statusMessage = null;
            final id = _conversationId;
            if (id != null) {
              Future.microtask(() => ConversationManager.instance.loadConversation(id));
            }
            break;
          case PythonStatus.error:
            _statusMessage = '连接错误';
            break;
          case PythonStatus.restarting:
            _statusMessage = '正在重新连接…';
            break;
          default:
            break;
        }
      });
    });
  }

  void _listenToLogs() {
    PythonBridge.instance.logStream.listen((log) {
      if (!mounted) return;

      // Only process logs while we're actively processing a query
      if (!_isProcessing) {
        return;
      }

      // Show important messages as chat messages (thinking, tool use, results)
      final msg = log.message;
      // Keep model reasoning content private/collapsed by default.
      // Live chat messages focus on observable tool activity and results.
      final shouldShowInChat = msg.startsWith('Tool:') ||
          msg.startsWith('Result:') ||
          msg.startsWith('Executing') ||
          msg.startsWith('Code:') ||
          msg.startsWith('File:') ||
          log.isError ||
          log.isWarning;

      if (shouldShowInChat) {
        // Choose icon based on message type
        String icon;
        if (log.isError) {
          icon = '⚠️';
        } else if (log.isWarning) {
          icon = '⚡';
        } else if (msg.startsWith('Thinking:')) {
          icon = '💭';
        } else if (msg.startsWith('Tool:')) {
          icon = '🔧';
        } else if (msg.startsWith('Executing')) {
          icon = '⚙️';
        } else if (msg.startsWith('Result:')) {
          icon = '📋';
        } else if (msg.startsWith('Code:')) {
          icon = '💻';
        } else if (msg.startsWith('File:')) {
          icon = '📎';
        } else {
          icon = '💭';
        }
        setState(() {
          _messages.add(ChatMessage(
            role: MessageRole.system,
            content: '$icon ${_localizeAgentLog(msg)}',
            timestamp: DateTime.now(),
          ));
        });
        _scrollToBottom();
      }

      // Also update status bar for progress and simple status
      if (log.hasProgress) {
        // If progress is 100%, we're done - don't show status
        if (log.progress! >= 1.0) {
          return;
        }
        setState(() {
          _statusMessage = '${log.message} (${(log.progress! * 100).toInt()}%)';
        });
      } else {
        setState(() {
          // A Thinking: log may contain a preview of the model's hidden
          // reasoning. Expose only a generic progress state here; the full
          // <think> block remains available through the collapsed control
          // attached to the final assistant message.
          _statusMessage = msg.startsWith('Thinking:')
              ? '正在思考…'
              : _localizeAgentLog(msg);
        });
      }
    });
  }

  void _listenToNativeTools() {
    _nativeToolSubscription = PythonBridge.instance.nativeToolStream.listen((request) {
      if (!mounted || !_isProcessing) return;
      if (!_announcedNativeToolIds.add(request.id)) return;

      setState(() {
        _messages.add(ChatMessage(
          role: MessageRole.system,
          content: '⚙️ 正在调用工具：${request.tool}',
          timestamp: DateTime.now(),
        ));
        _statusMessage = '正在调用工具：${request.tool}';
      });
      _scrollToBottom();
    });
  }

  String _localizeAgentLog(String msg) {
    if (msg.startsWith('Thinking:')) {
      return '思考：${msg.substring('Thinking:'.length).trim()}';
    }
    if (msg.startsWith('Tool:')) {
      return '准备调用工具：${msg.substring('Tool:'.length).trim()}';
    }
    if (msg.startsWith('Executing')) {
      return '正在执行${msg.substring('Executing'.length)}';
    }
    if (msg.startsWith('Result:')) {
      return '工具结果：${msg.substring('Result:'.length).trim()}';
    }
    if (msg.startsWith('Code:')) {
      return '执行代码：${msg.substring('Code:'.length).trim()}';
    }
    if (msg.startsWith('File:')) {
      return '文件：${msg.substring('File:'.length).trim()}';
    }
    if (msg == 'Preparing response...') return '正在整理最终回复…';
    return msg;
  }

  Future<void> _sendMessage() async {
    final text = _inputController.text.trim();
    if (text.isEmpty && _attachedFiles.isEmpty) return;

    // Handle API key input
    if (_awaitingApiKey) {
      await _handleApiKeyInput(text);
      return;
    }

    final conversationId = await _ensureConversation();
    final originalAttachments = _attachedFiles.isNotEmpty ? List<String>.from(_attachedFiles) : null;
    final userAttachments = originalAttachments == null
        ? null
        : await PythonBridge.instance.persistAttachedFilesForConversation(originalAttachments);

    // Add and persist the user message with durable attachment paths. Persistence
    // is DB-only here because
    // process_query itself owns Python SessionState insertion for this turn.
    setState(() {
      _messages.add(ChatMessage(
        role: MessageRole.user,
        content: text,
        timestamp: DateTime.now(),
        attachments: userAttachments,
      ));
      _inputController.clear();
    });
    await ConversationManager.instance.storeVisibleMessage(
      conversationId: conversationId,
      role: 'user',
      content: text,
      attachmentPaths: userAttachments,
    );
    await _autoTitleConversation(text);

    _scrollToBottom();

    // Check if using an offline model (skip connectivity gate)
    final preferredModel = await StorageService.instance.getPreferredModel();
    final selectedModelInfo = ModelRegistry.getById(preferredModel);
    final isUsingOfflineModel = selectedModelInfo?.isOffline ?? false;

    // If offline and not using an on-device model, queue the message
    if (!isUsingOfflineModel) {
      final isOnline = await ConnectivityService.instance.checkConnectivity();
      if (!isOnline) {
        await OfflineQueueManager.instance.queueMessage(
          query: text,
          attachmentPaths: _attachedFiles.isNotEmpty ? _attachedFiles : null,
        );

        setState(() {
          _messages.add(ChatMessage(
            role: MessageRole.system,
            content: '⏳ 消息已排队，恢复网络后发送。',
            timestamp: DateTime.now(),
          ));
          _attachedFiles = [];
        });
        _scrollToBottom();
        return;
      }
    }

    // Track message sent
    await AnalyticsService.instance.messageSent(
      hasAttachments: _attachedFiles.isNotEmpty,
      attachmentCount: _attachedFiles.length,
    );

    setState(() {
      _isProcessing = true;
      _statusMessage = isUsingOfflineModel ? '正在设备端运行…' : '正在思考…';
    });

    final stopwatch = Stopwatch()..start();
    try {
      debugPrint('Sending query to Python...');
      final response = await PythonBridge.instance.sendQuery(
        query: text,
        filePaths: userAttachments,
        context: {
          'enabled_skills': _enabledSkills.toList(),
        },
      );

      if (!mounted) return;

      if (response.isSuccess && response.result != null) {
        final content = response.result!['content'] as String? ?? '';
        final hasError = response.result!['error'] == true;
        final createdFiles = response.result!['created_files'] as List<dynamic>?;
        final thinking = response.result!['thinking'] as String?;
        final thinkingMode = response.result!['thinking_mode'] as String?;
        final diagnostics = response.result!['diagnostics'] as String?;
        setState(() {
          _messages.add(ChatMessage(
            role: hasError ? MessageRole.error : MessageRole.assistant,
            content: content,
            timestamp: DateTime.now(),
            thinking: thinking,
            thinkingMode: thinkingMode,
            diagnostics: diagnostics,
          ));
          // Add tappable file links for every created file
          if (createdFiles != null && !hasError) {
            for (final filePath in createdFiles) {
              _messages.add(ChatMessage(
                role: MessageRole.system,
                content: '\u{1F4CE} File: $filePath',
                timestamp: DateTime.now(),
              ));
            }
          }
        });
        await ConversationManager.instance.storeVisibleMessage(
          conversationId: conversationId,
          role: hasError ? 'system' : 'assistant',
          content: content,
          attachmentPaths: !hasError && createdFiles != null
              ? createdFiles.map((e) => e.toString()).toList()
              : null,
        );
        if (createdFiles != null && !hasError) {
          for (final filePath in createdFiles) {
            await ConversationManager.instance.storeVisibleMessage(
              conversationId: conversationId,
              role: 'system',
              content: '\u{1F4CE} File: $filePath',
            );
          }
        }
      } else if (response.isError) {
        final errorText = response.error?.message ?? '未知错误';
        setState(() {
          _messages.add(ChatMessage(
            role: MessageRole.error,
            content: errorText,
            timestamp: DateTime.now(),
          ));
        });
        await ConversationManager.instance.storeVisibleMessage(
          conversationId: conversationId,
          role: 'system',
          content: errorText,
        );
      } else {
        // Unexpected response format
        debugPrint('Unexpected response: $response');
        setState(() {
          _messages.add(ChatMessage(
            role: MessageRole.error,
            content: '智能体返回了无法识别的响应',
            timestamp: DateTime.now(),
          ));
        });
      }
    } catch (e, stackTrace) {
      stopwatch.stop();
      debugPrint('Error in _sendMessage: $e');
      debugPrint('Stack trace: $stackTrace');
      await AnalyticsService.instance.queryFailed(error: e.toString());
      if (!mounted) return;
      setState(() {
        _messages.add(ChatMessage(
          role: MessageRole.error,
          content: e.toString(),
          timestamp: DateTime.now(),
        ));
      });
    } finally {
      if (mounted) {
        setState(() {
          _isProcessing = false;
          _statusMessage = null;
          _attachedFiles = [];
          _externalFiles = [];
          _announcedNativeToolIds.clear();
        });
        _scrollToBottom();
      }
    }
  }

  Future<void> _handleSelfImprove(int messageIndex) async {
    if (_isProcessing) return;

    setState(() {
      _isProcessing = true;
      _statusMessage = '正在分析对话…';
    });

    try {
      // Build conversation up to the selected message
      final conversationMessages = <Map<String, String>>[];
      for (var i = 0; i <= messageIndex && i < _messages.length; i++) {
        final msg = _messages[i];
        if (msg.role == MessageRole.user || msg.role == MessageRole.assistant) {
          conversationMessages.add({
            'role': msg.role == MessageRole.user ? 'user' : 'assistant',
            'content': msg.content,
          });
        }
      }

      if (conversationMessages.isEmpty) {
        setState(() {
          _messages.add(ChatMessage(
            role: MessageRole.system,
            content: '没有可分析的对话。',
            timestamp: DateTime.now(),
          ));
        });
        return;
      }

      // Get current system prompt
      final currentPrompt = await StorageService.instance.getSystemPrompt();
      final promptToImprove = currentPrompt ?? defaultSystemPrompt;

      final response = await PythonBridge.instance.selfImprove(
        conversationMessages: conversationMessages,
        currentSystemPrompt: promptToImprove,
      );

      if (!mounted) return;

      if (response.isSuccess && response.result != null) {
        final improvedPrompt = response.result!['improved_prompt'] as String?;
        if (improvedPrompt != null && improvedPrompt.isNotEmpty) {
          await StorageService.instance.setSystemPrompt(improvedPrompt);
          setState(() {
            _messages.add(ChatMessage(
              role: MessageRole.system,
              content: '系统提示词已优化并保存，后续对话将使用新版本。',
              timestamp: DateTime.now(),
            ));
          });
        } else {
          setState(() {
            _messages.add(ChatMessage(
              role: MessageRole.system,
              content: '自我优化没有产生修改。',
              timestamp: DateTime.now(),
            ));
          });
        }
      } else {
        final errorMsg = response.error?.message ?? '未知错误';
        setState(() {
          _messages.add(ChatMessage(
            role: MessageRole.error,
            content: '自我优化失败：$errorMsg',
            timestamp: DateTime.now(),
          ));
        });
      }
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _messages.add(ChatMessage(
          role: MessageRole.error,
          content: '自我优化错误：$e',
          timestamp: DateTime.now(),
        ));
      });
    } finally {
      if (mounted) {
        setState(() {
          _isProcessing = false;
          _statusMessage = null;
        });
        _scrollToBottom();
      }
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _openMenu() async {
    final wasAwaitingApiKey = _awaitingApiKey;
    await Navigator.pushNamed(context, '/settings');

    // Reload self-improve setting (may have changed in Settings)
    _loadSelfImproveSetting();

    // Check if API key was saved or offline model selected while in Settings
    if (wasAwaitingApiKey && mounted) {
      final hasKey = await StorageService.instance.hasApiKey();
      if (hasKey) {
        final apiKey = await StorageService.instance.getApiKey();
        if (apiKey != null) {
          setState(() {
            _awaitingApiKey = false;
            _hasApiKey = true;
            _messages.add(ChatMessage(
              role: MessageRole.system,
              content: 'API Key 已保存，现在可以开始对话。',
              timestamp: DateTime.now(),
            ));
          });
          _scrollToBottom();

          // Send the API key to Python bridge
          await PythonBridge.instance.setApiKey(apiKey);
        }
      } else {
        // Check if an offline model was selected and downloaded
        final preferredModel = await StorageService.instance.getPreferredModel();
        final modelInfo = ModelRegistry.getById(preferredModel);
        final isOfflineSelected = modelInfo != null && modelInfo.isOffline;
        final offlineReady = isOfflineSelected &&
            LocalLLMService.instance.modelStates[preferredModel]?.downloadState ==
                ModelDownloadState.downloaded;
        if (offlineReady) {
          setState(() {
            _awaitingApiKey = false;
            _messages.add(ChatMessage(
              role: MessageRole.system,
              content: '本地模型已选择，现在可以开始对话。',
              timestamp: DateTime.now(),
            ));
          });
          _scrollToBottom();
        }
      }
    }
  }

  void _connectGoogle() {
    // Navigate to settings to connect Google account
    Navigator.pushNamed(context, '/settings', arguments: {'section': 'google'});
  }

  void _handleQuickAction(String action) {
    _inputController.text = action;
    _inputController.selection = TextSelection.fromPosition(
      TextPosition(offset: action.length),
    );

    // Detect active mode from action
    if (action.startsWith('/calendar')) {
      setState(() => _activeMode = 'Calendar');
    } else if (action.startsWith('/email')) {
      setState(() => _activeMode = 'Email');
    } else if (action.startsWith('/crop') || action.startsWith('/extract')) {
      setState(() => _activeMode = 'Media');
    } else if (action.startsWith('/ocr')) {
      setState(() => _activeMode = 'OCR');
    }

    // Hide quick actions after selection
    setState(() => _showQuickActions = false);
  }

  @override
  Widget build(BuildContext context) {
    final isPythonReady = PythonBridge.instance.status == PythonStatus.ready;

    return Scaffold(
      backgroundColor: NavixTheme.background,
      appBar: AppBar(
        backgroundColor: NavixTheme.background,
        title: Text(_conversationTitle == '新对话' ? 'RastaCoder' : 'RastaCoder · $_conversationTitle'),
        leading: IconButton(
          icon: Text(
            NavixTheme.iconMenu,
            style: TextStyle(
              fontSize: 24,
              color: NavixTheme.textPrimary,
            ),
          ),
          onPressed: _openMenu,
          tooltip: '菜单',
        ),
        actions: [
          IconButton(
            onPressed: _isProcessing ? null : _openConversationHistory,
            icon: const Icon(Icons.history),
            tooltip: '聊天记录',
          ),
          IconButton(
            onPressed: _isProcessing ? null : _startNewConversation,
            icon: const Icon(Icons.add_comment_outlined),
            tooltip: '新建对话',
          ),
          if (_isProcessing)
            const Padding(
              padding: EdgeInsets.only(right: 16),
              child: BrailleSpinner(size: 20),
            ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Status banner
            if (_statusMessage != null || !isPythonReady)
              StatusBanner(
                message: _statusMessage ?? '正在连接…',
                isError: PythonBridge.instance.status == PythonStatus.error,
              ),

            // Smart context bar
            SmartContextBar(
              isGoogleConnected: _isGoogleConnected,
              isOffline: !ConnectivityService.instance.isConnected,
              activeMode: _activeMode,
              attachedFileCount: _attachedFiles.length,
              onConnectGoogle: _connectGoogle,
              onClearMode: () => setState(() => _activeMode = null),
            ),

            // Message list
            Expanded(
              child: MessageList(
                messages: _messages,
                scrollController: _scrollController,
                selfImproveEnabled: _selfImproveEnabled,
                isProcessing: _isProcessing,
                onSelfImprove: _handleSelfImprove,
              ),
            ),

            // Quick action pills (show when no messages and idle)
            if (_messages.isEmpty && _showQuickActions && !_isProcessing)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: QuickActionPills(
                  onAction: _handleQuickAction,
                ),
              ),

            // Input bar
            InputBar(
              controller: _inputController,
              onSend: _sendMessage,
              enabled: (isPythonReady || _awaitingApiKey) && !_isProcessing,
              isProcessing: _isProcessing,
              onManageTools: _manageTools,
              enabledSkillCount: _enabledSkills.length,
              totalSkillCount: LocalToolSkillCatalog.all.length,
              externalFiles: _externalFiles,
              onFilesSelected: (files) {
                setState(() {
                  _attachedFiles = files;
                });
              },
            ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _shareSubscription?.cancel();
    _nativeToolSubscription?.cancel();
    _mlcEventSubscription?.cancel();
    WidgetsBinding.instance.removeObserver(this);
    _inputController.dispose();
    _scrollController.dispose();
    super.dispose();
  }
}

/// Chat message model
class ChatMessage {
  final MessageRole role;
  final String content;
  final DateTime timestamp;
  final List<String>? attachments;
  /// Local-model reasoning returned separately from the final answer.
  final String? thinking;
  /// model_default / enabled / disabled; null for cloud/system messages.
  final String? thinkingMode;
  /// Redacted, copyable per-query tool-call diagnostics.
  final String? diagnostics;

  ChatMessage({
    required this.role,
    required this.content,
    required this.timestamp,
    this.attachments,
    this.thinking,
    this.thinkingMode,
    this.diagnostics,
  });
}

enum MessageRole {
  user,
  assistant,
  system,
  error,
}
