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
  // RASTACODER_V8_TURN_LAYOUT
  final List<String> _currentToolEvents = <String>[];
  int? _toolProgressIndex;
  bool _toolProgressPersisted = false;
  int? _conversationId;
  // RASTACODER_V14_FINAL_STREAMING
  int? _streamDraftIndex;
  String? _streamGenerationId;
  final StringBuffer _streamRawBuffer = StringBuffer();
  bool _streamSawToolCall = false;
  String _conversationTitle = '新对话';
  bool _conversationLoaded = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    if (!widget.initializing) {
      _syncModelRouteState();
    }
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
    if (oldWidget.initializing && !widget.initializing) {
      WidgetsBinding.instance.addPostFrameCallback((_) async {
        if (!mounted) return;
        await _syncModelRouteState();
        if (mounted && !_conversationLoaded) {
          await _initializeConversationHistory();
        }
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
          // RASTACODER_V14_STREAM_GENERATION_RESET
          _beginStreamGeneration();
          message = '本地模型开始生成…';
          break;
        case 'first_token':
          final ms = event['elapsed_ms'];
          message = ms == null ? '已生成首个 Token' : '已生成首个 Token（${ms} ms）';
          break;
        case 'thinking_started':
          message = '正在思考…';
          break;
        case 'content_delta':
          _appendFinalStreamDelta(event);
          return;
        case 'tool_call_started':
          _discardStreamDraft();
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

  void _beginStreamGeneration() {
    final index = _streamDraftIndex;
    if (mounted && index != null && index >= 0 && index < _messages.length &&
        _messages[index].role == MessageRole.assistant) {
      setState(() => _messages.removeAt(index));
    }
    _resetStreamDraftState();
  }

  String _streamVisibleText(String raw) {
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
        'toolResult' => MessageRole.toolProgress,
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
      MessageRole.toolProgress => 'toolResult',
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

  Future<void> _syncModelRouteState() async {
    // RASTACODER_V13_PROVIDER_ROUTE_SYNC
    final preferredModel = await StorageService.instance.getPreferredModel();
    final modelInfo = ModelRegistry.getById(preferredModel);
    final routeProvider = modelInfo?.routeProvider ?? ModelRouteProvider.anthropic;

    if (routeProvider == ModelRouteProvider.local) {
      final hasKey = await StorageService.instance.hasApiKey();
      final downloaded = LocalLLMService.instance.modelStates[preferredModel]?.downloadState ==
          ModelDownloadState.downloaded;
      if (downloaded &&
          (LocalLLMService.instance.loadedModelId != preferredModel ||
              LocalLLMService.instance.loadState != ModelLoadState.loaded)) {
        try {
          await LocalLLMService.instance.loadModel(preferredModel);
        } catch (e) {
          debugPrint('[V13 route restore] $e');
        }
      }
      if (!mounted) return;
      setState(() {
        _hasApiKey = hasKey;
        _awaitingApiKey = false;
      });
      return;
    }

    if (routeProvider == ModelRouteProvider.openAICompatible) {
      // Base URL + Model ID define readiness. Provider API keys are optional
      // because some OpenAI-compatible endpoints are local or unauthenticated.
      final config = await StorageService.instance.getOpenAICompatibleConfig();
      final configured = (config['base_url'] ?? '').trim().isNotEmpty &&
          (config['model'] ?? '').trim().isNotEmpty;
      if (!mounted) return;
      setState(() {
        _hasApiKey = configured;
        _awaitingApiKey = false;
      });
      return;
    }

    final hasKey = await StorageService.instance.hasApiKey();
    if (!mounted) return;
    setState(() {
      _hasApiKey = hasKey;
      _awaitingApiKey = !hasKey;
    });
    if (hasKey) _sendStoredApiKeyToPython();
  }

  Future<bool> _ensureSelectedRouteReadyForSend() async {
    // RASTACODER_V13_PROVIDER_ROUTE_READY
    final preferredModel = await StorageService.instance.getPreferredModel();
    final modelInfo = ModelRegistry.getById(preferredModel);
    final routeProvider = modelInfo?.routeProvider ?? ModelRouteProvider.anthropic;

    if (routeProvider == ModelRouteProvider.local) {
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
            LocalLLMService.instance.loadState != ModelLoadState.loaded) {
          if (mounted) setState(() => _statusMessage = '正在加载已选择的本地模型…');
          await LocalLLMService.instance.loadModel(preferredModel);
        }
      } catch (e) {
        _addRoutingError('本地模型加载失败：$e');
        return false;
      }
      if (LocalLLMService.instance.loadedModelId != preferredModel ||
          LocalLLMService.instance.loadState != ModelLoadState.loaded) {
        _addRoutingError('本地模型尚未进入可推理状态，请重新加载模型后再试。');
        return false;
      }
      return true;
    }

    if (routeProvider == ModelRouteProvider.openAICompatible) {
      final config = await StorageService.instance.getOpenAICompatibleConfig();
      final baseUrl = (config['base_url'] ?? '').trim();
      final model = (config['model'] ?? '').trim();
      if (baseUrl.isEmpty || model.isEmpty) {
        _addRoutingError('OpenAI 兼容接口尚未配置完整。请在设置中填写 Base URL 和 Model ID。API Key 可按服务商要求选填。');
        return false;
      }
      if (mounted) {
        setState(() {
          _hasApiKey = true;
          _awaitingApiKey = false;
        });
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
      _addRoutingError('当前选择的是 Claude 云端模型，但尚未配置 Claude API Key。请到设置中配置 API Key。');
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

  void _appendToolProgress(String event) {
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

    // V8: synchronize displayed selection with the actual inference route.
    if (!await _ensureSelectedRouteReadyForSend()) return;

    _currentToolEvents.clear();
    _toolProgressIndex = null;
    _toolProgressPersisted = false;
    _announcedNativeToolIds.clear();
    _resetStreamDraftState();

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
          final canonical = ChatMessage(
            role: hasError ? MessageRole.error : MessageRole.assistant,
            content: content,
            timestamp: DateTime.now(),
            thinking: thinking,
            thinkingMode: thinkingMode,
            diagnostics: diagnostics,
            attachments: !hasError && createdFiles != null
                ? createdFiles.map((e) => e.toString()).toList()
                : null,
          );
          final index = _streamDraftIndex;
          if (!hasError && index != null && index >= 0 && index < _messages.length &&
              _messages[index].role == MessageRole.assistant) {
            _messages[index] = canonical;
          } else {
            _messages.add(canonical);
          }
          _resetStreamDraftState();
        });
        await _persistCurrentToolProgress(conversationId);
        await ConversationManager.instance.storeVisibleMessage(
          conversationId: conversationId,
          role: hasError ? 'system' : 'assistant',
          content: content,
          attachmentPaths: !hasError && createdFiles != null
              ? createdFiles.map((e) => e.toString()).toList()
              : null,
        );
      } else if (response.isError) {
        await _persistCurrentToolProgress(conversationId);
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
    await Navigator.pushNamed(context, '/settings');
    await _loadSelfImproveSetting();
    await _loadSkillDefaults();
    await _syncModelRouteState();
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
          Semantics(
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
              enabled: isPythonReady && !_isProcessing,
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
  toolProgress,
  system,
  error,
}
