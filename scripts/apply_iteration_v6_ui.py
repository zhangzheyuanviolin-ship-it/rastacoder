#!/usr/bin/env python3
"""Apply v6 Thinking visibility and copy/export diagnostics UI changes."""
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Chat screen: preserve per-response reasoning/diagnostic metadata.
# ---------------------------------------------------------------------------
chat_path = Path('lib/features/chat/presentation/chat_screen.dart')
chat = chat_path.read_text(encoding='utf-8')

old = r'''        final content = response.result!['content'] as String? ?? '';
        final hasError = response.result!['error'] == true;
        final createdFiles = response.result!['created_files'] as List<dynamic>?;
        setState(() {
          _messages.add(ChatMessage(
            role: hasError ? MessageRole.error : MessageRole.assistant,
            content: content,
            timestamp: DateTime.now(),
          ));
'''
new = r'''        final content = response.result!['content'] as String? ?? '';
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
'''
chat = replace_once(chat, old, new, 'response metadata')

old = r'''class ChatMessage {
  final MessageRole role;
  final String content;
  final DateTime timestamp;
  final List<String>? attachments;

  ChatMessage({
    required this.role,
    required this.content,
    required this.timestamp,
    this.attachments,
  });
}
'''
new = r'''class ChatMessage {
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
'''
chat = replace_once(chat, old, new, 'ChatMessage metadata')
chat_path.write_text(chat, encoding='utf-8')


# ---------------------------------------------------------------------------
# Message bubble: accessible collapsed Thinking panel + diagnostics copy/share.
# ---------------------------------------------------------------------------
bubble_path = Path('lib/features/chat/presentation/widgets/message_bubble.dart')
bubble = bubble_path.read_text(encoding='utf-8')

old = r'''    final visibleContent = message.role == MessageRole.assistant
        ? _splitThinking(message.content)[1]
        : message.content;
    return '$roleLabel：$visibleContent';
'''
new = r'''    final visibleContent = message.role == MessageRole.assistant
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
'''
bubble = replace_once(bubble, old, new, 'accessibility metadata')

# Error bubbles also need diagnostics, because parser/schema/native failures are
# exactly the cases where the user needs a copyable log.
old = r'''    if (message.role == MessageRole.error) {
      return Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            NavixTheme.iconWarning,
            style: TextStyle(
              fontSize: 16,
              color: NavixTheme.error,
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: SelectableText(
              message.content,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: NavixTheme.error,
              ),
            ),
          ),
        ],
      );
    }
'''
new = r'''    if (message.role == MessageRole.error) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                NavixTheme.iconWarning,
                style: TextStyle(fontSize: 16, color: NavixTheme.error),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: SelectableText(
                  message.content,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: NavixTheme.error,
                  ),
                ),
              ),
            ],
          ),
          if (message.diagnostics?.trim().isNotEmpty ?? false) ...[
            const SizedBox(height: 8),
            _buildDiagnosticsPanel(context, message.diagnostics!.trim()),
          ],
        ],
      );
    }
'''
bubble = replace_once(bubble, old, new, 'error diagnostics')

# Use explicit metadata reasoning first; retain legacy <think> parsing as a
# fallback for cloud/old messages.
old = r'''    final parts = _splitThinking(message.content);
    final thinking = parts[0];
    final answer = parts[1];
    final widgets = <Widget>[];

    if (thinking.isNotEmpty) {
'''
new = r'''    final parts = _splitThinking(message.content);
    final explicitThinking = message.thinking?.trim() ?? '';
    final thinking = explicitThinking.isNotEmpty ? explicitThinking : parts[0];
    final answer = parts[1];
    final widgets = <Widget>[];

    if (thinking.isNotEmpty) {
'''
bubble = replace_once(bubble, old, new, 'explicit thinking')

# Improve accessibility wording on the Thinking tile.
old = r'''            title: Text(
              '思考过程（点击展开）',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: NavixTheme.textSecondary,
                  ),
            ),
'''
new = r'''            title: Semantics(
              button: true,
              label: '思考过程，当前已折叠，双击展开',
              child: Text(
                '思考过程（点击展开）',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: NavixTheme.textSecondary,
                    ),
              ),
            ),
'''
bubble = replace_once(bubble, old, new, 'thinking semantics')

# When the selected mode produced no visible reasoning, display that fact. This
# makes the user's manual Thinking setting empirically inspectable instead of
# silently hiding all three modes behind an identical final answer.
anchor = r'''    if (answer.isNotEmpty) {
      widgets.add(_buildTextContent(context, answer));
'''
insert = r'''    if (thinking.isEmpty && message.thinkingMode != null) {
      final modeLabel = switch (message.thinkingMode) {
        'enabled' => '手动开启',
        'disabled' => '手动关闭',
        _ => '模型默认',
      };
      final detail = message.thinkingMode == 'disabled'
          ? '本轮未返回可显示的思考内容。'
          : '本轮模型没有返回可显示的思考文本。';
      widgets.add(
        Semantics(
          label: '思考模式：$modeLabel。$detail',
          child: Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Text(
              '思考模式：$modeLabel；$detail',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: NavixTheme.textTertiary,
                  ),
            ),
          ),
        ),
      );
    }

    if (answer.isNotEmpty) {
      widgets.add(_buildTextContent(context, answer));
'''
bubble = replace_once(bubble, anchor, insert, 'thinking mode status')

# Add diagnostics after answer / Google-connect content.
old = r'''    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: widgets,
    );
  }

  Widget _buildTextContent(BuildContext context, String content) {
'''
new = r'''    if (message.diagnostics?.trim().isNotEmpty ?? false) {
      widgets.add(const SizedBox(height: 8));
      widgets.add(_buildDiagnosticsPanel(context, message.diagnostics!.trim()));
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: widgets,
    );
  }

  Widget _buildDiagnosticsPanel(BuildContext context, String diagnostics) {
    return Theme(
      data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
      child: ExpansionTile(
        tilePadding: EdgeInsets.zero,
        childrenPadding: const EdgeInsets.only(bottom: 8),
        initiallyExpanded: false,
        maintainState: true,
        title: Semantics(
          button: true,
          label: '工具调用诊断，当前已折叠，双击展开',
          child: Text(
            '工具调用诊断（点击展开）',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: NavixTheme.textSecondary,
                ),
          ),
        ),
        children: [
          Align(
            alignment: Alignment.centerLeft,
            child: SelectableText(
              diagnostics,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: NavixTheme.textTertiary,
                    fontFamily: 'monospace',
                  ),
            ),
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              OutlinedButton.icon(
                onPressed: () async {
                  await Clipboard.setData(ClipboardData(text: diagnostics));
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('工具调用诊断已复制到剪贴板')),
                    );
                  }
                },
                icon: const Icon(Icons.copy, size: 18),
                label: const Text('复制诊断日志'),
              ),
              OutlinedButton.icon(
                onPressed: () => Share.share(
                  diagnostics,
                  subject: 'RastaCoder 工具调用诊断',
                ),
                icon: const Icon(Icons.share, size: 18),
                label: const Text('分享诊断日志'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildTextContent(BuildContext context, String content) {
'''
bubble = replace_once(bubble, old, new, 'diagnostics panel')

# Long-press menu also exposes diagnostics directly.
old = r'''            ListTile(
              leading: const Icon(Icons.copy),
              title: const Text('复制'),
              onTap: () {
                Clipboard.setData(ClipboardData(text: message.content));
                Navigator.pop(modalContext);
                scaffoldMessenger.showSnackBar(
                  const SnackBar(content: Text('已复制到剪贴板')),
                );
              },
            ),
'''
new = r'''            ListTile(
              leading: const Icon(Icons.copy),
              title: const Text('复制回复'),
              onTap: () {
                Clipboard.setData(ClipboardData(text: message.content));
                Navigator.pop(modalContext);
                scaffoldMessenger.showSnackBar(
                  const SnackBar(content: Text('回复已复制到剪贴板')),
                );
              },
            ),
            if (message.diagnostics?.trim().isNotEmpty ?? false)
              ListTile(
                leading: const Icon(Icons.bug_report),
                title: const Text('复制工具调用诊断'),
                onTap: () {
                  Clipboard.setData(ClipboardData(text: message.diagnostics!.trim()));
                  Navigator.pop(modalContext);
                  scaffoldMessenger.showSnackBar(
                    const SnackBar(content: Text('工具调用诊断已复制到剪贴板')),
                  );
                },
              ),
            if (message.diagnostics?.trim().isNotEmpty ?? false)
              ListTile(
                leading: const Icon(Icons.share),
                title: const Text('分享工具调用诊断'),
                onTap: () {
                  final diagnostics = message.diagnostics!.trim();
                  Navigator.pop(modalContext);
                  Share.share(diagnostics, subject: 'RastaCoder 工具调用诊断');
                },
              ),
'''
bubble = replace_once(bubble, old, new, 'context diagnostics')

bubble_path.write_text(bubble, encoding='utf-8')
print('Applied RastaCoder v6 Thinking/diagnostics UI patch')
