#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding='utf-8')


def write(path, text):
    (ROOT / path).write_text(text, encoding='utf-8')


def replace_required(text, old, new, label):
    if old not in text:
        raise RuntimeError(f'Patch anchor missing: {label}')
    return text.replace(old, new)


# ---------------------------------------------------------------------------
# 1) Detach Google Sign-In from the upstream developer's hard-coded Web OAuth
#    client. Android Google Sign-In will use package + signing certificate.
# ---------------------------------------------------------------------------
auth_path = 'lib/core/services/auth_service.dart'
auth = read(auth_path)
auth = replace_required(
    auth,
    "  final _googleSignIn = GoogleSignIn(\n    serverClientId:\n        '296863031657-69hn38bhprhqvrda6vd795sp65e8764d.apps.googleusercontent.com',\n    scopes: [",
    "  // Do not bind the fork to the upstream developer's OAuth Web client.\n"
    "  // Android Google Sign-In identifies this app by applicationId + signing\n"
    "  // certificate. Register ai.navixmind with the RastaCoder certificate in\n"
    "  // the Google Cloud project that will own Gmail/Calendar authorization.\n"
    "  final _googleSignIn = GoogleSignIn(\n    scopes: [",
    'remove upstream Google serverClientId',
)
auth = auth.replace('User declined additional scopes', '用户未授予额外的 Google 权限')
auth = auth.replace('Google disconnect error (ignored):', 'Google 账号解除连接时出现可忽略错误：')
auth = auth.replace('Token refresh failed:', 'Google 访问令牌刷新失败：')
write(auth_path, auth)


# ---------------------------------------------------------------------------
# 2) Assistant message rendering: split <think>...</think>, collapse thinking
#    by default, expose only the final answer to accessibility semantics.
# ---------------------------------------------------------------------------
mb_path = 'lib/features/chat/presentation/widgets/message_bubble.dart'
mb = read(mb_path)
mb = mb.replace("hint: 'Long press to copy',", "hint: '长按可复制',")
mb = mb.replace("MessageRole.user => 'You said',", "MessageRole.user => '您说',")
mb = mb.replace("MessageRole.assistant => 'NavixMind replied',", "MessageRole.assistant => 'NavixMind 回复',")
mb = mb.replace("MessageRole.system => 'System message',", "MessageRole.system => '系统消息',")
mb = mb.replace("MessageRole.error => 'Error',", "MessageRole.error => '错误',")
mb = replace_required(
    mb,
    "    return '$roleLabel: ${message.content}';",
    "    final semanticContent = message.role == MessageRole.assistant\n"
    "        ? _splitThinking(message.content)[1]\n"
    "        : message.content;\n"
    "    return '$roleLabel: $semanticContent';",
    'assistant accessibility final answer',
)
mb = replace_required(
    mb,
    "    // Check if content contains code blocks\n    if (message.content.contains('```')) {\n      return _buildMarkdownContent(context);\n    }",
    "    // Assistant responses from reasoning models may contain <think> tags.\n"
    "    // Render the final answer normally and keep reasoning collapsed.\n"
    "    if (message.role == MessageRole.assistant) {\n"
    "      return _buildAssistantContent(context);\n"
    "    }\n\n"
    "    // Check if content contains code blocks\n"
    "    if (message.content.contains('```')) {\n"
    "      return _buildMarkdownContent(context);\n"
    "    }",
    'assistant think rendering hook',
)
helper = r'''
  List<String> _splitThinking(String content) {
    final thinkRegex = RegExp(
      r'<think>([\s\S]*?)</think>',
      caseSensitive: false,
    );
    final thoughts = thinkRegex
        .allMatches(content)
        .map((m) => (m.group(1) ?? '').trim())
        .where((s) => s.isNotEmpty)
        .toList();
    final answer = content.replaceAll(thinkRegex, '').trim();

    // Defensive handling for a model that emitted an opening tag but was cut
    // off before </think>. Keep it out of the visible final answer.
    if (thoughts.isEmpty) {
      final lower = content.toLowerCase();
      final open = lower.indexOf('<think>');
      if (open >= 0) {
        final after = content.substring(open + 7).trim();
        return [after, content.substring(0, open).trim()];
      }
    }
    return [thoughts.join('\n\n'), answer];
  }

  Widget _buildAssistantContent(BuildContext context) {
    final parts = _splitThinking(message.content);
    final thinking = parts[0];
    final answer = parts[1];
    final needsGoogleConnect = !AuthService.instance.isSignedIn &&
        _mentionsGoogleConnect(answer);

    final children = <Widget>[];
    if (thinking.isNotEmpty) {
      children.add(
        Theme(
          data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
          child: ExpansionTile(
            initiallyExpanded: false,
            tilePadding: EdgeInsets.zero,
            childrenPadding: const EdgeInsets.only(bottom: 10),
            title: const Text('思考过程（点击展开）'),
            leading: const Icon(Icons.psychology_outlined, size: 20),
            children: [
              Align(
                alignment: Alignment.centerLeft,
                child: SelectableText(
                  thinking,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: RastaTheme.textTertiary,
                  ),
                ),
              ),
            ],
          ),
        ),
      );
    }

    if (answer.isNotEmpty) {
      children.add(_buildContentText(context, answer));
    }

    if (needsGoogleConnect) {
      children.add(const SizedBox(height: 12));
      children.add(
        ElevatedButton.icon(
          onPressed: () async {
            try {
              final account = await AuthService.instance.signIn();
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text(account != null
                        ? 'Google 账号已连接'
                        : '已取消登录'),
                  ),
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
          style: ElevatedButton.styleFrom(
            backgroundColor: RastaTheme.gold,
            foregroundColor: RastaTheme.black,
          ),
        ),
      );
    }

    if (children.isEmpty) {
      return const SizedBox.shrink();
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: children,
    );
  }

  Widget _buildContentText(BuildContext context, String content) {
    if (!content.contains('```')) {
      return SelectableText(
        content,
        style: Theme.of(context).textTheme.bodyLarge?.copyWith(
          color: RastaTheme.textPrimary,
        ),
      );
    }

    final parts = <Widget>[];
    final regex = RegExp(r'```(\w*)\n?([\s\S]*?)```');
    var lastEnd = 0;
    for (final match in regex.allMatches(content)) {
      if (match.start > lastEnd) {
        final text = content.substring(lastEnd, match.start).trim();
        if (text.isNotEmpty) {
          parts.add(SelectableText(
            text,
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
              color: RastaTheme.textPrimary,
            ),
          ));
        }
      }
      parts.add(_CodeBlock(
        code: (match.group(2) ?? '').trim(),
        language: match.group(1) ?? '',
      ));
      lastEnd = match.end;
    }
    if (lastEnd < content.length) {
      final text = content.substring(lastEnd).trim();
      if (text.isNotEmpty) {
        parts.add(SelectableText(
          text,
          style: Theme.of(context).textTheme.bodyLarge?.copyWith(
            color: RastaTheme.textPrimary,
          ),
        ));
      }
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: parts
          .map((w) => Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: w,
              ))
          .toList(),
    );
  }

'''
mb = replace_required(mb, "  bool _mentionsGoogleConnect(String content) {", helper + "  bool _mentionsGoogleConnect(String content) {", 'insert think helpers')
mb = mb.replace("? 'Google account connected!'\n                          : 'Sign-in cancelled'", "? 'Google 账号已连接'\n                          : '已取消登录'")
mb = mb.replace("SnackBar(content: Text('Sign-in failed: $e'))", "SnackBar(content: Text('Google 登录失败：$e'))")
mb = mb.replace("label: const Text('Connect Google Account'),", "label: const Text('连接 Google 账号'),")
mb = mb.replace("SnackBar(content: Text('File not found: $fileName'))", "SnackBar(content: Text('找不到文件：$fileName'))")
mb = mb.replace("title: const Text('Copy'),", "title: const Text('复制'),")
mb = mb.replace("Clipboard.setData(ClipboardData(text: message.content));", "Clipboard.setData(ClipboardData(text: message.role == MessageRole.assistant ? _splitThinking(message.content)[1] : message.content));")
mb = mb.replace("const SnackBar(content: Text('Copied to clipboard'))", "const SnackBar(content: Text('已复制到剪贴板'))")
write(mb_path, mb)


# ---------------------------------------------------------------------------
# 3) Real-time execution trace + Chinese chat/status copy.
# ---------------------------------------------------------------------------
chat_path = 'lib/features/chat/presentation/chat_screen.dart'
chat = read(chat_path)
chat = chat.replace("msg.startsWith('File:') ||", "msg.startsWith('File:') ||\n          msg.startsWith('Completed tool:') ||")
chat = chat.replace("content: '$icon $msg',", "content: '$icon ${_localizeActivityMessage(msg)}',")
chat = replace_required(
    chat,
    "  Future<void> _sendMessage() async {",
    r'''  String _localizeActivityMessage(String msg) {
    if (msg.startsWith('Thinking:')) {
      return '思考：${msg.substring('Thinking:'.length).trim()}';
    }
    if (msg.startsWith('Tool:')) {
      return '准备调用工具：${msg.substring('Tool:'.length).trim()}';
    }
    if (msg.startsWith('Executing')) {
      return '正在执行：${msg.substring('Executing'.length).trim()}';
    }
    if (msg.startsWith('Completed tool:')) {
      return '工具执行完成：${msg.substring('Completed tool:'.length).trim()}';
    }
    if (msg.startsWith('Result:')) {
      return '工具结果：${msg.substring('Result:'.length).trim()}';
    }
    if (msg.startsWith('Code:')) {
      return '即将执行代码：${msg.substring('Code:'.length).trim()}';
    }
    if (msg.startsWith('File:')) {
      return '文件：${msg.substring('File:'.length).trim()}';
    }
    return msg;
  }

  Future<void> _sendMessage() async {''',
    'insert activity localization helper',
)
chat = replace_required(
    chat,
    "    setState(() {\n      _isProcessing = true;\n      _statusMessage = isUsingOfflineModel ? 'Running on device...' : 'Thinking...';\n    });",
    "    setState(() {\n      _isProcessing = true;\n      _statusMessage = isUsingOfflineModel ? '正在设备上运行…' : '正在思考…';\n"
    "      _messages.add(ChatMessage(\n"
    "        role: MessageRole.system,\n"
    "        content: '⚙️ 已开始处理，后续工具调用和执行结果会实时显示。',\n"
    "        timestamp: DateTime.now(),\n"
    "      ));\n"
    "    });\n"
    "    _scrollToBottom();",
    'immediate processing activity',
)
chat_replacements = {
    'Welcome to NavixMind! Please enter your Claude API key to get started.\\n\\nYou can get one at console.anthropic.com\\n\\nAlternatively, select an offline model in Settings to run fully on-device.': '欢迎使用 NavixMind！请输入 Claude API Key，或在设置中选择已经下载的本地模型，以完全离线方式运行。',
    "That doesn't look like a valid Claude API key. It should start with \"sk-\". Please try again.": '这个 Claude API Key 格式看起来不正确，应以“sk-”开头，请重新输入。',
    'API key saved! You can now start chatting with NavixMind.': 'API Key 已保存，现在可以开始对话。',
    'Initializing...': '正在初始化…',
    'Loading modules...': '正在加载模块…',
    'Connection error': '连接错误',
    'Reconnecting...': '正在重新连接…',
    '⏳ Message queued. Will send when online.': '⏳ 消息已进入队列，联网后会自动发送。',
    'Unknown error': '未知错误',
    'Unexpected response from agent': '智能体返回了无法识别的响应',
    'Analyzing conversation...': '正在分析对话…',
    'No conversation to analyze.': '当前没有可分析的对话。',
    'System prompt improved and saved. It will be used for future queries.': '系统提示词已优化并保存，之后的请求会使用新版本。',
    'Self-improve returned no changes.': '自我优化未返回需要修改的内容。',
    'Self-improve failed:': '自我优化失败：',
    'Self-improve error:': '自我优化错误：',
    'Offline model selected! You can now start chatting with NavixMind.': '本地模型已选择，现在可以开始对话。',
    "tooltip: 'Menu'": "tooltip: '菜单'",
    "message: _statusMessage ?? 'Connecting...'": "message: _statusMessage ?? '正在连接…'",
}
for old, new in chat_replacements.items():
    chat = chat.replace(old, new)
write(chat_path, chat)

agent_path = 'python/navixmind/agent.py'
agent = read(agent_path)
agent = replace_required(
    agent,
    "                        result_summary = _summarize_tool_result(tool_name, result_str)\n                        bridge.log(f\"Result: {result_summary}\", level=\"info\")",
    "                        result_summary = _summarize_tool_result(tool_name, result_str)\n"
    "                        bridge.log(f\"Result: {result_summary}\", level=\"info\")\n"
    "                        bridge.log(f\"Completed tool: {tool_name}\", level=\"info\")",
    'tool completion event',
)
write(agent_path, agent)


# ---------------------------------------------------------------------------
# 4) Chinese-first UI. Translate the primary product surface and accessibility
#    labels. These are literal UI strings; model/tool protocol strings are left
#    unchanged so function calling remains compatible.
# ---------------------------------------------------------------------------
translations = {
    'lib/features/chat/presentation/widgets/input_bar.dart': {
        'Failed to pick files:': '选择文件失败：',
        ' is too large (': ' 文件过大（',
        '). Max: ': '）。最大允许：',
        "tooltip: 'Add file'": "tooltip: '添加文件'",
        "? 'Type a message...'": "? '输入消息…'",
        ": 'Connecting...'": ": '正在连接…'",
        "tooltip: 'Send'": "tooltip: '发送'",
    },
    'lib/features/chat/presentation/widgets/context_bar.dart': {
        "label: 'Offline'": "label: '离线'",
        "tooltip: 'No internet connection. Messages will be queued.'": "tooltip: '当前没有网络连接，消息会进入等待队列。'",
        "label: 'Connect Google'": "label: '连接 Google'",
        "label: '$attachedFileCount file${attachedFileCount > 1 ? 's' : ''}'": "label: '$attachedFileCount 个文件'",
        "showClose ? 'Tap to remove' : 'Tap to activate'": "showClose ? '点击移除' : '点击启用'",
        '"What\'s on my calendar?"': "'查看今天的日历'",
        "label: 'Check emails'": "label: '查看未读邮件'",
        "label: 'Summarize'": "label: '总结内容'",
        "label: 'Process video'": "label: '处理视频'",
        "hint: 'Tap to use this quick action'": "hint: '点击使用此快捷操作'",
    },
    'lib/features/onboarding/onboarding_screen.dart': {
        'Welcome to NavixMind': '欢迎使用 NavixMind',
        'Your AI-powered console agent for Android. Process documents, manage calendar, and automate tasks with natural language.': 'Android 手机上的 AI 智能体。可以用自然语言处理文档、管理日历并执行自动化任务。',
        'Process Any Media': '处理各种媒体与文档',
        'Extract text from PDFs, crop videos, and convert documents. All processing happens on your device.': '提取 PDF 文本、裁剪视频、转换文档；支持在设备本地完成多种处理。',
        'Connect Your Services': '连接您的服务',
        'Link your Google account to manage calendar events and emails directly through conversation.': '连接 Google 账号后，可以在对话中查询邮件并管理日历。',
        'Please enter your Claude API key': '请输入 Claude API Key',
        "child: const Text('Back')": "child: const Text('返回')",
        "child: const Text('Next')": "child: const Text('下一步')",
        "child: const Text('Get Started')": "child: const Text('开始使用')",
        'Enter Your API Key': '输入 API Key',
        'NavixMind uses Claude AI to understand your requests. Get your API key from console.anthropic.com': '使用云端 Claude 模型时需要 API Key；也可以在设置中下载并选择本地模型。',
        "labelText: 'Claude API Key'": "labelText: 'Claude API Key'",
        'Your API key is stored securely on your device and never sent to our servers.': 'API Key 安全保存在您的设备上，只用于连接您选择的模型服务。',
    },
    'lib/features/settings/settings_screen.dart': {
        "title: const Text('Settings')": "title: const Text('设置')",
        "title: 'AI Model'": "title: 'AI 模型'",
        "title: 'System Prompt'": "title: '系统提示词'",
        "subtitle: _hasCustomPrompt ? 'Custom' : 'Default'": "subtitle: _hasCustomPrompt ? '自定义' : '默认'",
        "title: 'Self Improve'": "title: '对话自我优化'",
        "subtitle: 'Show button to auto-improve system prompt from conversation'": "subtitle: '显示根据对话自动优化系统提示词的按钮'",
        "title: 'Tool Timeout'": "title: '工具超时时间'",
        '— max wait for native tools (OCR, etc.)': '— 本地工具（OCR 等）的最长等待时间',
        "title: 'Max Steps per Query'": "title: '每次请求最大步骤数'",
        '— reasoning steps before stopping': '— 达到后停止继续推理',
        "title: 'Max Tool Calls per Query'": "title: '每次请求最大工具调用次数'",
        '— tool executions before stopping': '— 达到后停止继续调用工具',
        "title: 'Max Response Tokens'": "title: '最大回复 Token 数'",
        '— per API call (higher = longer responses)': '— 每次模型调用上限，数值越高可生成越长回复',
        "_SectionHeader(title: 'Connected Accounts')": "_SectionHeader(title: '已连接账号')",
        "title: 'Google Account'": "title: 'Google 账号'",
        "?? 'Connected'": "?? '已连接'",
        ": 'Not connected'": ": '未连接'",
        "child: const Text('Disconnect')": "child: const Text('断开连接')",
        "child: const Text('Connect')": "child: const Text('连接')",
        "_SectionHeader(title: 'Usage & Limits')": "_SectionHeader(title: '用量与限制')",
        "title: 'Enable Token Limits'": "title: '启用 Token 限制'",
        "subtitle: 'Pause agent when limits are reached'": "subtitle: '达到限制时暂停智能体'",
        "title: 'Today'": "title: '今天'",
        "title: 'This Month'": "title: '本月'",
        "title: 'Export Usage Data'": "title: '导出用量数据'",
        "subtitle: 'Download usage history as CSV'": "subtitle: '将用量历史导出为 CSV'",
        "_SectionHeader(title: 'Legal')": "_SectionHeader(title: '法律与隐私')",
        "title: 'Terms of Service'": "title: '服务条款'",
        "title: 'Privacy Policy'": "title: '隐私政策'",
        "_SectionHeader(title: 'About')": "_SectionHeader(title: '关于')",
        "title: 'Version'": "title: '版本'",
        "title: 'Licenses'": "title: '开源许可'",
        "title: const Text('Delete Model')": "title: const Text('删除模型')",
        "child: const Text('Cancel')": "child: const Text('取消')",
        "'Delete'": "'删除'",
        "'Daily Token Limit'": "'每日 Token 限制'",
        "'Monthly Token Limit'": "'每月 Token 限制'",
        "labelText: 'Token limit'": "labelText: 'Token 上限'",
        "suffixText: 'tokens'": "suffixText: 'Token'",
        "child: const Text('Save')": "child: const Text('保存')",
        "label: 'OK'": "label: '确定'",
        'Exported to:': '已导出到：',
        'Export failed:': '导出失败：',
    },
}

for path, mapping in translations.items():
    text = read(path)
    for old, new in mapping.items():
        text = text.replace(old, new)
    write(path, text)

# Main chat mode labels are visible in the context bar.
chat = read(chat_path)
chat = chat.replace("_activeMode = 'Calendar'", "_activeMode = '日历'")
chat = chat.replace("_activeMode = 'Email'", "_activeMode = '邮件'")
chat = chat.replace("_activeMode = 'Media'", "_activeMode = '媒体'")
# Keep OCR unchanged; it is a standard acronym.
write(chat_path, chat)

# Context bar must recognize translated mode names for Google-connect visibility.
ctx_path = 'lib/features/chat/presentation/widgets/context_bar.dart'
ctx = read(ctx_path)
ctx = ctx.replace("(activeMode == 'Calendar' || activeMode == 'Email')", "(activeMode == 'Calendar' || activeMode == 'Email' || activeMode == '日历' || activeMode == '邮件')")
ctx = ctx.replace("case 'calendar':", "case 'calendar':\n      case '日历':")
ctx = ctx.replace("case 'email':", "case 'email':\n      case '邮件':")
ctx = ctx.replace("case 'media':", "case 'media':\n      case '媒体':")
write(ctx_path, ctx)


# ---------------------------------------------------------------------------
# 5) Make source builds self-contained for this fork.
#    Firebase remains optional at runtime (main.dart already catches init error),
#    while removing Gradle-only plugins avoids requiring upstream
#    google-services.json. Keep package ai.navixmind stable for OAuth identity.
# ---------------------------------------------------------------------------
gradle_path = 'android/app/build.gradle'
gradle = read(gradle_path)
gradle = gradle.replace('    id "com.google.gms.google-services"\n', '')
gradle = gradle.replace('    id "com.google.firebase.crashlytics"\n', '')
gradle = gradle.replace('abiFilters "armeabi-v7a", "arm64-v8a", "x86_64"', 'abiFilters "arm64-v8a"')
write(gradle_path, gradle)

print('Iteration v2 patch applied successfully.')
