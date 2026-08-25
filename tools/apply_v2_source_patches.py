#!/usr/bin/env python3
"""Apply the RastaCoder v2 source changes to the exact e165 baseline.

This script is intentionally deterministic: important structural edits assert
that the expected upstream text exists exactly once. It lets the project keep
an immutable known-good source baseline while materializing the v2 UI/auth
changes during CI without touching the verified MLC model/runtime binary.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Version + Android build: keep the package ID so v2 upgrades the signed v1.
# Firebase is optional at runtime; remove Gradle plugins which require the
# original developer's private google-services.json. Google Sign-In itself is
# independent and is configured through Android OAuth package+certificate.
# ---------------------------------------------------------------------------
pubspec = read("pubspec.yaml")
pubspec = replace_once(pubspec, "version: 0.0.1+15", "version: 0.0.2+16", "version")
write("pubspec.yaml", pubspec)

build_gradle = read("android/app/build.gradle")
build_gradle = replace_once(
    build_gradle,
    '    id "com.google.gms.google-services"\n    id "com.google.firebase.crashlytics"\n',
    '',
    "remove original Firebase Gradle configuration",
)
build_gradle = replace_once(
    build_gradle,
    '            abiFilters "armeabi-v7a", "arm64-v8a", "x86_64"',
    '            abiFilters "arm64-v8a"',
    "arm64-only MLC baseline",
)
write("android/app/build.gradle", build_gradle)

# ---------------------------------------------------------------------------
# Google OAuth: detach from the original developer's hard-coded Web client.
# Access-token-only Gmail/Calendar usage doesn't need a server auth client ID.
# Google Play services identifies an Android OAuth client by package name and
# signing SHA-1. RastaCoder keeps the package ID ai.navixmind for update
# compatibility, and CI keeps the stable RastaCoder signing certificate.
# ---------------------------------------------------------------------------
auth = read("lib/core/services/auth_service.dart")
auth = replace_once(
    auth,
    "  final _googleSignIn = GoogleSignIn(\n    serverClientId:\n        '296863031657-69hn38bhprhqvrda6vd795sp65e8764d.apps.googleusercontent.com',\n    scopes: [",
    "  final _googleSignIn = GoogleSignIn(\n    scopes: [",
    "remove original Google server client id",
)
write("lib/core/services/auth_service.dart", auth)

# ---------------------------------------------------------------------------
# Assistant reply rendering: preserve model reasoning, but hide it by default
# and exclude it from the default screen-reader announcement.
# ---------------------------------------------------------------------------
message = read("lib/features/chat/presentation/widgets/message_bubble.dart")
message = replace_once(
    message,
    "import '../chat_screen.dart';\n",
    "import '../chat_screen.dart';\nimport 'reasoning_disclosure.dart';\n",
    "reasoning disclosure import",
)
message = replace_once(
    message,
    "      hint: 'Long press to copy',",
    "      hint: '长按可复制',",
    "accessible copy hint",
)
message = replace_once(
    message,
    "      MessageRole.user => 'You said',\n      MessageRole.assistant => 'NavixMind replied',\n      MessageRole.system => 'System message',\n      MessageRole.error => 'Error',\n    };\n    return '$roleLabel: ${message.content}';",
    "      MessageRole.user => '您说',\n      MessageRole.assistant => '助手回复',\n      MessageRole.system => '系统消息',\n      MessageRole.error => '错误',\n    };\n    final accessibleContent = message.role == MessageRole.assistant\n        ? AssistantReasoningParts.parse(message.content).answer\n        : message.content;\n    return '$roleLabel: $accessibleContent';",
    "assistant accessibility label",
)
message = replace_once(
    message,
    "  Widget _buildContent(BuildContext context) {\n    if (message.role == MessageRole.error) {",
    "  Widget _buildContent(BuildContext context) {\n    final reasoningParts = AssistantReasoningParts.parse(message.content);\n    final displayContent = message.role == MessageRole.assistant\n        ? reasoningParts.answer\n        : message.content;\n    final primary = _buildPrimaryContent(context, displayContent);\n\n    if (message.role == MessageRole.assistant && reasoningParts.hasReasoning) {\n      return Column(\n        crossAxisAlignment: CrossAxisAlignment.start,\n        children: [\n          ReasoningDisclosure(reasoning: reasoningParts.reasoning),\n          if (displayContent.isNotEmpty) const SizedBox(height: 6),\n          if (displayContent.isNotEmpty) primary,\n        ],\n      );\n    }\n    return primary;\n  }\n\n  Widget _buildPrimaryContent(BuildContext context, String content) {\n    if (message.role == MessageRole.error) {",
    "reasoning-aware content wrapper",
)

# Only rewrite message.content references in the primary-content function.
start = message.index("  Widget _buildPrimaryContent")
end = message.index("  bool _mentionsGoogleConnect", start)
segment = message[start:end]
segment = segment.replace("message.content.startsWith", "content.startsWith")
segment = segment.replace("message.content.contains", "content.contains")
segment = segment.replace("_mentionsGoogleConnect(message.content)", "_mentionsGoogleConnect(content)")
segment = segment.replace("_buildFileLink(context);", "_buildFileLink(context, content);")
segment = segment.replace("_buildMarkdownContent(context);", "_buildMarkdownContent(context, content);")
segment = segment.replace("message.content,", "content,")
message = message[:start] + segment + message[end:]

message = replace_once(
    message,
    "  Widget _buildFileLink(BuildContext context) {\n    final filePath = message.content.replaceFirst('📎 File: ', '').trim();",
    "  Widget _buildFileLink(BuildContext context, String content) {\n    final filePath = content.replaceFirst('📎 File: ', '').trim();",
    "file link visible content",
)
message = replace_once(
    message,
    "  Widget _buildMarkdownContent(BuildContext context) {\n    // Simple code block parsing\n    final parts = <Widget>[];\n    final regex = RegExp(r'```(\\w*)\\n?([\\s\\S]*?)```');\n    var lastEnd = 0;\n\n    for (final match in regex.allMatches(message.content)) {",
    "  Widget _buildMarkdownContent(BuildContext context, String content) {\n    // Simple code block parsing\n    final parts = <Widget>[];\n    final regex = RegExp(r'```(\\w*)\\n?([\\s\\S]*?)```');\n    var lastEnd = 0;\n\n    for (final match in regex.allMatches(content)) {",
    "markdown content parameter",
)
# Remaining markdown references are confined to this function.
start = message.index("  Widget _buildMarkdownContent")
end = message.index("  void _showContextMenu", start)
segment = message[start:end].replace("message.content", "content")
message = message[:start] + segment + message[end:]

message = replace_once(
    message,
    "  void _showContextMenu(BuildContext context) {\n    // Store reference to outer scaffold messenger before showing modal\n    final scaffoldMessenger = ScaffoldMessenger.of(context);",
    "  void _showContextMenu(BuildContext context) {\n    // Copying an assistant reply defaults to the user-facing answer.\n    final copyText = message.role == MessageRole.assistant\n        ? AssistantReasoningParts.parse(message.content).answer\n        : message.content;\n    // Store reference to outer scaffold messenger before showing modal\n    final scaffoldMessenger = ScaffoldMessenger.of(context);",
    "copy visible answer",
)
message = replace_once(
    message,
    "Clipboard.setData(ClipboardData(text: message.content));",
    "Clipboard.setData(ClipboardData(text: copyText));",
    "copy answer action",
)
write("lib/features/chat/presentation/widgets/message_bubble.dart", message)

# ---------------------------------------------------------------------------
# Native tool activity stream: Python already emits Tool/Result logs, but this
# stream is emitted exactly at the Dart/native execution boundary. It gives UI
# a deterministic, immediate start/success/failure signal for FFmpeg/OCR/
# browser/vision/native local-model operations.
# ---------------------------------------------------------------------------
native = read("lib/core/services/native_tool_executor.dart")
native = replace_once(
    native,
    "/// Executor for native tools called from Python.\n",
    "enum NativeToolActivityStage { started, succeeded, failed }\n\nclass NativeToolActivity {\n  final String tool;\n  final NativeToolActivityStage stage;\n  final int? durationMs;\n  final String? error;\n\n  const NativeToolActivity({\n    required this.tool,\n    required this.stage,\n    this.durationMs,\n    this.error,\n  });\n}\n\n/// Executor for native tools called from Python.\n",
    "native activity model",
)
native = replace_once(
    native,
    "  final _bridge = PythonBridge.instance;\n  StreamSubscription? _subscription;",
    "  final _bridge = PythonBridge.instance;\n  StreamSubscription? _subscription;\n  final _activityController = StreamController<NativeToolActivity>.broadcast();\n\n  Stream<NativeToolActivity> get activityStream => _activityController.stream;",
    "native activity controller",
)
native = replace_once(
    native,
    "    debugPrint('[NativeTool] Received request: ${request.tool} (id: ${request.id})');\n    final stopwatch = Stopwatch()..start();",
    "    debugPrint('[NativeTool] Received request: ${request.tool} (id: ${request.id})');\n    _activityController.add(NativeToolActivity(\n      tool: request.tool,\n      stage: NativeToolActivityStage.started,\n    ));\n    final stopwatch = Stopwatch()..start();",
    "native tool start event",
)
native = replace_once(
    native,
    "      debugPrint('[NativeTool] Result sent for: ${request.tool}');\n\n      // Track successful tool execution",
    "      debugPrint('[NativeTool] Result sent for: ${request.tool}');\n      _activityController.add(NativeToolActivity(\n        tool: request.tool,\n        stage: NativeToolActivityStage.succeeded,\n        durationMs: stopwatch.elapsedMilliseconds,\n      ));\n\n      // Track successful tool execution",
    "native tool success event",
)
native = replace_once(
    native,
    "      debugPrint('[NativeTool] Error sent for: ${request.tool}');\n\n      // Track failed tool execution",
    "      debugPrint('[NativeTool] Error sent for: ${request.tool}');\n      _activityController.add(NativeToolActivity(\n        tool: request.tool,\n        stage: NativeToolActivityStage.failed,\n        durationMs: stopwatch.elapsedMilliseconds,\n        error: e.toString(),\n      ));\n\n      // Track failed tool execution",
    "native tool failure event",
)
write("lib/core/services/native_tool_executor.dart", native)

# ---------------------------------------------------------------------------
# Chat screen listens to native tool activity immediately. Python-only tools
# keep using the existing async log stream, so both execution paths remain
# observable without altering the proven agent loop.
# ---------------------------------------------------------------------------
chat = read("lib/features/chat/presentation/chat_screen.dart")
chat = replace_once(
    chat,
    "import '../../../core/services/local_llm_service.dart';\n",
    "import '../../../core/services/local_llm_service.dart';\nimport '../../../core/services/native_tool_executor.dart';\n",
    "native activity chat import",
)
chat = replace_once(
    chat,
    "    _listenToLogs();\n    _listenToConnectivity();",
    "    _listenToLogs();\n    _listenToNativeToolActivity();\n    _listenToConnectivity();",
    "listen to native tool activity",
)
marker = "  void _listenToLogs() {\n"
if chat.count(marker) != 1:
    raise RuntimeError("chat log listener marker mismatch")
listener = r'''  void _listenToNativeToolActivity() {
    NativeToolExecutor.instance.activityStream.listen((activity) {
      if (!mounted || !_isProcessing) return;

      final toolLabel = _toolDisplayName(activity.tool);
      String status;
      String chatLine;
      switch (activity.stage) {
        case NativeToolActivityStage.started:
          status = '正在执行工具：$toolLabel';
          chatLine = '⚙️ 正在执行工具：$toolLabel';
          break;
        case NativeToolActivityStage.succeeded:
          final elapsed = activity.durationMs == null
              ? ''
              : '（${(activity.durationMs! / 1000).toStringAsFixed(2)} 秒）';
          status = '工具执行完成：$toolLabel';
          chatLine = '✅ 工具执行完成：$toolLabel$elapsed';
          break;
        case NativeToolActivityStage.failed:
          status = '工具执行失败：$toolLabel';
          chatLine = '⚠️ 工具执行失败：$toolLabel';
          break;
      }

      setState(() {
        _statusMessage = status;
        _messages.add(ChatMessage(
          role: activity.stage == NativeToolActivityStage.failed
              ? MessageRole.error
              : MessageRole.system,
          content: chatLine,
          timestamp: DateTime.now(),
        ));
      });
      _scrollToBottom();
    });
  }

  String _toolDisplayName(String tool) {
    const names = <String, String>{
      'ffmpeg': '音视频处理',
      'ocr': '文字识别',
      'headless_browser': '网页浏览器',
      'face_detect': '人脸检测',
      'smart_crop': '智能裁剪',
      'llm_generate': '本地模型推理',
      'python_execute': 'Python 执行器',
      'ffmpeg_process': '音视频处理',
    };
    return names[tool] ?? tool;
  }

'''
chat = chat.replace(marker, listener + marker, 1)
write("lib/features/chat/presentation/chat_screen.dart", chat)

# ---------------------------------------------------------------------------
# Chinese-first UI copy. This intentionally translates visible application
# strings while leaving protocol names, tool names, JSON keys and model IDs
# untouched. Chinese is the v2 default regardless of system language.
# ---------------------------------------------------------------------------
translations = {
    "'Settings'": "'设置'",
    "'API Configuration'": "'API 配置'",
    "'Claude API Key'": "'Claude API 密钥'",
    "'Loading...'": "'正在加载…'",
    "'Configured'": "'已配置'",
    "'Not configured'": "'未配置'",
    "'System Prompt'": "'系统提示词'",
    "'Custom'": "'自定义'",
    "'Default'": "'默认'",
    "'Self Improve'": "'自我改进'",
    "'Show button to auto-improve system prompt from conversation'": "'显示按钮，根据当前对话自动改进系统提示词'",
    "'Tool Timeout'": "'工具超时时间'",
    "'Max Steps per Query'": "'每次请求最大步骤数'",
    "'Max Tool Calls per Query'": "'每次请求最大工具调用次数'",
    "'Max Response Tokens'": "'最大回复 Token 数'",
    "'Connected Accounts'": "'已连接账户'",
    "'Google Account'": "'Google 账号'",
    "'Connected'": "'已连接'",
    "'Not connected'": "'未连接'",
    "'Connect'": "'连接'",
    "'Disconnect'": "'断开连接'",
    "'Usage & Limits'": "'用量与限制'",
    "'Enable Token Limits'": "'启用 Token 限制'",
    "'Pause agent when limits are reached'": "'达到限制时暂停智能体'",
    "'Today'": "'今天'",
    "'This Month'": "'本月'",
    "'Legal'": "'法律信息'",
    "'Terms of Service'": "'服务条款'",
    "'Privacy Policy'": "'隐私政策'",
    "'About'": "'关于'",
    "'Version'": "'版本'",
    "'Licenses'": "'开源许可'",
    "'Copy'": "'复制最终回复'",
    "'Copied to clipboard'": "'已复制到剪贴板'",
    "'Google account connected!'": "'Google 账号已连接'",
    "'Sign-in cancelled'": "'已取消登录'",
    "'Connect Google Account'": "'连接 Google 账号'",
    "'Initializing...'": "'正在初始化…'",
    "'Loading modules...'": "'正在加载模块…'",
    "'Connection error'": "'连接错误'",
    "'Reconnecting...'": "'正在重新连接…'",
    "'Running on device...'": "'正在设备本地运行…'",
    "'Thinking...'": "'正在思考…'",
    "'Analyzing conversation...'": "'正在分析对话…'",
    "'Unknown error'": "'未知错误'",
    "'Unexpected response from agent'": "'智能体返回了无法识别的响应'",
    "'Send'": "'发送'",
    "'Cancel'": "'取消'",
    "'Save'": "'保存'",
    "'Close'": "'关闭'",
    "'Delete'": "'删除'",
    "'Download'": "'下载'",
    "'Retry'": "'重试'",
    "'Done'": "'完成'",
    "'Back'": "'返回'",
    "'Continue'": "'继续'",
    "'Agree'": "'同意'",
    "'Decline'": "'拒绝'",
    "'Accept'": "'接受'",
    "'Model'": "'模型'",
    "'Models'": "'模型'",
    "'Offline Models'": "'离线模型'",
    "'Download Model'": "'下载模型'",
    "'Delete Model'": "'删除模型'",
    "'Model downloaded'": "'模型已下载'",
    "'Model loaded'": "'模型已加载'",
    "'Loading model...'": "'正在加载模型…'",
    "'Downloading...'": "'正在下载…'",
    "'Ready'": "'就绪'",
    "'Error'": "'错误'",
    "'Warning'": "'警告'",
    "'File not found'": "'未找到文件'",
    "'Select files'": "'选择文件'",
    "'New chat'": "'新对话'",
    "'Clear conversation'": "'清空对话'",
    "'Clear'": "'清空'",
    "'Daily Limit'": "'每日限制'",
    "'Monthly Limit'": "'每月限制'",
    "'Unlimited'": "'不限'",
    "'Enabled'": "'已启用'",
    "'Disabled'": "'已禁用'",
    "'Privacy'": "'隐私'",
    "'Terms'": "'条款'",
    "'Account'": "'账户'",
    "'Appearance'": "'外观'",
    "'General'": "'通用'",
    "'Advanced'": "'高级'",
    "'API Key'": "'API 密钥'",
    "'Edit'": "'编辑'",
    "'Remove'": "'移除'",
    "'Share'": "'分享'",
}

for path in (ROOT / "lib").rglob("*.dart"):
    text = path.read_text(encoding="utf-8")
    original = text
    for old, new in translations.items():
        text = text.replace(old, new)
    if text != original:
        path.write_text(text, encoding="utf-8")

print("RastaCoder v2 source patches applied successfully")
