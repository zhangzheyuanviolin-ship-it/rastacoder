#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_required(path: str, old: str, new: str) -> None:
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    if old not in text:
        raise SystemExit(f'Missing required anchor in {path}: {old[:80]!r}')
    p.write_text(text.replace(old, new), encoding='utf-8')


def replace_many(path: str, mapping: dict[str, str]) -> None:
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    for old, new in mapping.items():
        text = text.replace(old, new)
    p.write_text(text, encoding='utf-8')


# 1) Assistant replies: separate <think>...</think> from the final answer.
message_path = 'lib/features/chat/presentation/widgets/message_bubble.dart'
replace_required(
    message_path,
    "  String get _accessibilityLabel {\n    final roleLabel = switch (message.role) {\n      MessageRole.user => 'You said',\n      MessageRole.assistant => 'NavixMind replied',\n      MessageRole.system => 'System message',\n      MessageRole.error => 'Error',\n    };\n    return '$roleLabel: ${message.content}';\n  }",
    "  String get _accessibilityLabel {\n    final roleLabel = switch (message.role) {\n      MessageRole.user => '您说',\n      MessageRole.assistant => 'RastaCoder 回复',\n      MessageRole.system => '系统消息',\n      MessageRole.error => '错误',\n    };\n    final visibleContent = message.role == MessageRole.assistant\n        ? _splitThinking(message.content)[1]\n        : message.content;\n    return '$roleLabel：$visibleContent';\n  }"
)
replace_required(
    message_path,
    "  Widget _buildContent(BuildContext context) {\n    if (message.role == MessageRole.error) {",
    "  Widget _buildContent(BuildContext context) {\n    if (message.role == MessageRole.assistant) {\n      return _buildAssistantContent(context);\n    }\n\n    if (message.role == MessageRole.error) {"
)
anchor = "  bool _mentionsGoogleConnect(String content) {"
helper = r'''  List<String> _splitThinking(String content) {
    final thinkRegex = RegExp(r'<think>([\s\S]*?)</think>', caseSensitive: false);
    final thinkingParts = <String>[];
    var finalText = content;

    for (final match in thinkRegex.allMatches(content)) {
      final thinking = match.group(1)?.trim();
      if (thinking != null && thinking.isNotEmpty) thinkingParts.add(thinking);
    }
    finalText = finalText.replaceAll(thinkRegex, '').trim();

    // Defensive handling for a model response which ends while a think tag is open.
    final openThink = RegExp(r'<think>([\s\S]*)$', caseSensitive: false).firstMatch(finalText);
    if (openThink != null) {
      final thinking = openThink.group(1)?.trim();
      if (thinking != null && thinking.isNotEmpty) thinkingParts.add(thinking);
      finalText = finalText.substring(0, openThink.start).trim();
    }

    return [thinkingParts.join('\n\n'), finalText];
  }

  Widget _buildAssistantContent(BuildContext context) {
    final parts = _splitThinking(message.content);
    final thinking = parts[0];
    final answer = parts[1];
    final widgets = <Widget>[];

    if (thinking.isNotEmpty) {
      widgets.add(
        Theme(
          data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
          child: ExpansionTile(
            tilePadding: EdgeInsets.zero,
            childrenPadding: const EdgeInsets.only(bottom: 10),
            initiallyExpanded: false,
            maintainState: true,
            title: Text(
              '思考过程（点击展开）',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: NavixTheme.textSecondary,
                  ),
            ),
            children: [
              Align(
                alignment: Alignment.centerLeft,
                child: SelectableText(
                  thinking,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: NavixTheme.textTertiary,
                      ),
                ),
              ),
            ],
          ),
        ),
      );
    }

    if (answer.isNotEmpty) {
      widgets.add(_buildTextContent(context, answer));
    } else if (thinking.isNotEmpty) {
      widgets.add(Text(
        '正在整理最终回复…',
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

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: widgets,
    );
  }

  Widget _buildTextContent(BuildContext context, String content) {
    if (!content.contains('```')) {
      return SelectableText(
        content,
        style: Theme.of(context).textTheme.bodyLarge?.copyWith(
              color: NavixTheme.textPrimary,
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
          parts.add(SelectableText(text,
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                    color: NavixTheme.textPrimary,
                  )));
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
        parts.add(SelectableText(text,
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                  color: NavixTheme.textPrimary,
                )));
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
p = ROOT / message_path
text = p.read_text(encoding='utf-8')
if anchor not in text:
    raise SystemExit('message_bubble helper anchor missing')
p.write_text(text.replace(anchor, helper + anchor), encoding='utf-8')

# 2) Primary UI localization. Internal command identifiers remain English.
replace_many(message_path, {
    "hint: 'Long press to copy'": "hint: '长按可复制'",
    "'Google account connected!'": "'Google 账号已连接'",
    "'Sign-in cancelled'": "'已取消登录'",
    "'Sign-in failed: $e'": "'登录失败：$e'",
    "'Connect Google Account'": "'连接 Google 账号'",
    "'File not found: $fileName'": "'找不到文件：$fileName'",
    "title: const Text('Copy')": "title: const Text('复制')",
    "const SnackBar(content: Text('Copied to clipboard'))": "const SnackBar(content: Text('已复制到剪贴板'))",
})

replace_many('lib/features/chat/presentation/chat_screen.dart', {
    "'Welcome to NavixMind! Please enter your Claude API key to get started.\\n\\nYou can get one at console.anthropic.com\\n\\nAlternatively, select an offline model in Settings to run fully on-device.'": "'欢迎使用 RastaCoder！您可以在设置中配置 Claude API Key，或者直接选择并下载本地模型，在设备端离线运行。'",
    "'That doesn\\'t look like a valid Claude API key. It should start with \"sk-\". Please try again.'": "'这个 Claude API Key 格式看起来不正确，应当以 \"sk-\" 开头，请重新输入。'",
    "'API key saved! You can now start chatting with NavixMind.'": "'API Key 已保存，现在可以开始对话。'",
    "'Received ${validFiles.length} file(s) from share. Add a prompt and send.'": "'已接收 ${validFiles.length} 个分享文件，请输入要求后发送。'",
    "'Initializing...'": "'正在初始化…'",
    "'Loading modules...'": "'正在加载模块…'",
    "'Connection error'": "'连接错误'",
    "'Reconnecting...'": "'正在重新连接…'",
    "'⏳ Message queued. Will send when online.'": "'⏳ 消息已排队，恢复网络后发送。'",
    "'Running on device...'": "'正在设备端运行…'",
    "'Thinking...'": "'正在思考…'",
    "'Unknown error'": "'未知错误'",
    "'Unexpected response from agent'": "'智能体返回了无法识别的响应'",
    "'Analyzing conversation...'": "'正在分析对话…'",
    "'No conversation to analyze.'": "'没有可分析的对话。'",
    "'System prompt improved and saved. It will be used for future queries.'": "'系统提示词已优化并保存，后续对话将使用新版本。'",
    "'Self-improve returned no changes.'": "'自我优化没有产生修改。'",
    "'Self-improve failed: $errorMsg'": "'自我优化失败：$errorMsg'",
    "'Self-improve error: $e'": "'自我优化错误：$e'",
    "tooltip: 'Menu'": "tooltip: '菜单'",
    "message: _statusMessage ?? 'Connecting...'": "message: _statusMessage ?? '正在连接…'",
    "'Offline model selected! You can now start chatting with NavixMind.'": "'本地模型已选择，现在可以开始对话。'",
})

replace_many('lib/features/chat/presentation/widgets/input_bar.dart', {
    "'Failed to pick files: $e'": "'选择文件失败：$e'",
    "'$name is too large ($sizeStr). Max: $limitStr'": "'$name 文件过大（$sizeStr），最大允许 $limitStr'",
    "tooltip: 'Add file'": "tooltip: '添加文件'",
    "? 'Type a message...'": "? '输入消息…'",
    ": 'Connecting...'": ": '正在连接…'",
    "tooltip: 'Send'": "tooltip: '发送'",
})

replace_many('lib/features/chat/presentation/widgets/context_bar.dart', {
    "label: 'Offline'": "label: '离线'",
    "tooltip: 'No internet connection. Messages will be queued.'": "tooltip: '当前没有网络连接，联网后将继续处理。'",
    "label: 'Connect Google'": "label: '连接 Google'",
    "label: '$attachedFileCount file${attachedFileCount > 1 ? 's' : ''}'": "label: '$attachedFileCount 个文件'",
    "hint: onTap != null ? (showClose ? 'Tap to remove' : 'Tap to activate') : tooltip": "hint: onTap != null ? (showClose ? '点击移除' : '点击启用') : tooltip",
    "label: \"What's on my calendar?\"": "label: '查看我的日历'",
    "label: 'Check emails'": "label: '检查邮件'",
    "label: 'Summarize'": "label: '总结内容'",
    "label: 'Process video'": "label: '处理视频'",
    "hint: 'Tap to use this quick action'": "hint: '点击使用此快捷操作'",
})

replace_many('lib/features/chat/presentation/widgets/message_list.dart', {
    "'Self Improve'": "'自我优化'",
    "'Start a conversation'": "'开始对话'",
    "'Ask me anything or share a file to get started'": "'输入问题，或者分享一个文件开始处理'",
})

# Settings: translate visible controls while preserving internal model IDs.
replace_many('lib/features/settings/settings_screen.dart', {
    "title: const Text('Settings')": "title: const Text('设置')",
    "_SectionHeader(title: 'API Configuration')": "_SectionHeader(title: 'API 与模型')",
    "title: 'Claude API Key'": "title: 'Claude API Key'",
    "? 'Loading...'": "? '正在加载…'",
    "(_hasApiKey ? 'Configured' : 'Not configured')": "(_hasApiKey ? '已配置' : '未配置')",
    "hintText: 'sk-ant-... (leave empty to remove)'": "hintText: 'sk-ant-...（留空可删除）'",
    "child: const Text('Cancel')": "child: const Text('取消')",
    "child: const Text('Save')": "child: const Text('保存')",
    "const SnackBar(content: Text('API key removed'))": "const SnackBar(content: Text('API Key 已删除'))",
    "const SnackBar(content: Text('API key saved'))": "const SnackBar(content: Text('API Key 已保存'))",
    "title: 'System Prompt'": "title: '系统提示词'",
    "subtitle: _hasCustomPrompt ? 'Custom' : 'Default'": "subtitle: _hasCustomPrompt ? '自定义' : '默认'",
    "title: 'Self Improve'": "title: '自我优化'",
    "subtitle: 'Show button to auto-improve system prompt from conversation'": "subtitle: '显示按钮，可根据当前对话自动优化系统提示词'",
    "title: 'Tool Timeout'": "title: '工具超时时间'",
    "subtitle: '${_toolTimeout}s — max wait for native tools (OCR, etc.)'": "subtitle: '${_toolTimeout} 秒 — OCR 等本地工具的最长等待时间'",
    "title: 'Max Steps per Query'": "title: '每次任务最大步骤数'",
    "subtitle: '$_maxIterations — reasoning steps before stopping'": "subtitle: '$_maxIterations — 达到该推理步数后停止'",
    "title: 'Max Tool Calls per Query'": "title: '每次任务最大工具调用次数'",
    "subtitle: '$_maxToolCalls — tool executions before stopping'": "subtitle: '$_maxToolCalls — 达到该工具执行次数后停止'",
    "title: 'Max Response Tokens'": "title: '单次回复最大 Token'",
    "subtitle: '$_maxTokens — per API call (higher = longer responses)'": "subtitle: '$_maxTokens — 数值越高允许回复越长'",
    "_SectionHeader(title: 'Connected Accounts')": "_SectionHeader(title: '已连接账号')",
    "title: 'Google Account'": "title: 'Google 账号'",
    "?? 'Connected'": "?? '已连接'",
    ": 'Not connected'": ": '未连接'",
    "child: const Text('Disconnect')": "child: const Text('断开连接')",
    "child: const Text('Connect')": "child: const Text('连接')",
    "? 'Google account connected!'": "? 'Google 账号已连接'",
    ": 'Sign-in cancelled'": ": '已取消登录'",
    "'Sign-in failed: $e'": "'登录失败：$e'",
    "const SnackBar(content: Text('Google account disconnected'))": "const SnackBar(content: Text('Google 账号已断开'))",
    "_SectionHeader(title: 'Usage & Limits')": "_SectionHeader(title: '用量与限制')",
    "title: 'Enable Token Limits'": "title: '启用 Token 限制'",
    "subtitle: 'Pause agent when limits are reached'": "subtitle: '达到设定上限时暂停智能体'",
    "title: 'Today'": "title: '今天'",
    "title: 'This Month'": "title: '本月'",
    "title: 'Export Usage Data'": "title: '导出用量数据'",
    "subtitle: 'Download usage history as CSV'": "subtitle: '将历史用量导出为 CSV'",
    "_SectionHeader(title: 'Legal')": "_SectionHeader(title: '法律与隐私')",
    "title: 'Terms of Service'": "title: '服务条款'",
    "title: 'Privacy Policy'": "title: '隐私政策'",
    "_SectionHeader(title: 'About')": "_SectionHeader(title: '关于')",
    "title: 'Version'": "title: '版本'",
    "title: 'Licenses'": "title: '开源许可证'",
    "'Cloud Models (API Key Required)'": "'云端模型（需要 API Key）'",
    "'Offline Models (On-Device)'": "'本地模型（设备端运行）'",
    "'Research only'": "'仅供研究'",
    "'May exceed GPU memory (${estimatedVramMB} MB > ${gpuMemoryMB} MB)'": "'可能超过 GPU 内存（${estimatedVramMB} MB > ${gpuMemoryMB} MB）'",
    "const Text('Download')": "const Text('下载')",
    "const Text('Delete')": "const Text('删除')",
    "'Loading...'": "'正在加载…'",
    "'Loaded'": "'已加载'",
    "const Text('Unload')": "const Text('卸载')",
    "?? 'Download failed'": "?? '下载失败'",
    "const Text('Retry')": "const Text('重试')",
    "title: const Text('Delete Model')": "title: const Text('删除模型')",
    "'You can re-download it later.'": "'之后仍可重新下载。'",
    "title: const Text('Download Required')": "title: const Text('需要下载模型')",
    "'to use it offline?'": "'后即可离线使用，是否下载？'",
    "'Limit reached. Agent paused.'": "'已达到限制，智能体已暂停。'",
    "'Approaching limit (${(progress * 100).toInt()}%)'": "'即将达到限制（${(progress * 100).toInt()}%）'",
    "title: const Text('System Prompt')": "title: const Text('系统提示词')",
    "child: const Text('Reset')": "child: const Text('恢复默认')",
    "_isCustom ? 'Custom prompt' : 'Default prompt'": "_isCustom ? '自定义提示词' : '默认提示词'",
    "'${_controller.text.length} characters'": "'${_controller.text.length} 个字符'",
    "const SnackBar(content: Text('System prompt saved'))": "const SnackBar(content: Text('系统提示词已保存'))",
    "labelText: 'Token limit'": "labelText: 'Token 上限'",
    "suffixText: 'tokens'": "suffixText: 'Token'",
    "helperText: 'Current: ${_formatTokens(currentValue)}'": "helperText: '当前：${_formatTokens(currentValue)}'",
    "'Exported to: $filePath'": "'已导出到：$filePath'",
    "'Export failed: $e'": "'导出失败：$e'",
})

# Translate common onboarding / legal UI labels without touching legal semantics or URLs.
for path in [
    'lib/features/onboarding/onboarding_screen.dart',
    'lib/features/legal/legal_acceptance_dialog.dart',
    'lib/features/legal/privacy_policy.dart',
    'lib/features/legal/terms_of_service.dart',
]:
    replace_many(path, {
        "'Welcome to NavixMind'": "'欢迎使用 RastaCoder'",
        "'Get Started'": "'开始使用'",
        "'Continue'": "'继续'",
        "'Skip'": "'跳过'",
        "'Back'": "'返回'",
        "'Accept'": "'接受'",
        "'Decline'": "'拒绝'",
        "'Terms of Service'": "'服务条款'",
        "'Privacy Policy'": "'隐私政策'",
        "'I Agree'": "'同意'",
        "'Close'": "'关闭'",
    })

print('Iteration v2 patches applied successfully.')
