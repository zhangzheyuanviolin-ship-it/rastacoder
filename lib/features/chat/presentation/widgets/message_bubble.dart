import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:share_plus/share_plus.dart';

import '../../../../app/theme.dart';
import '../../../../core/services/auth_service.dart';
import '../chat_screen.dart';

/// Platform channel for native file operations
const _fileChannel = MethodChannel('ai.navixmind/file_opener');

/// Individual message bubble with role-based styling
class MessageBubble extends StatelessWidget {
  final ChatMessage message;

  const MessageBubble({
    super.key,
    required this.message,
  });

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: _accessibilityLabel,
      hint: '长按可打开消息操作',
      container: true,
      explicitChildNodes: true,
      child: GestureDetector(
        onLongPress: () => _showContextMenu(context),
        child: Row(
          mainAxisAlignment: _alignment,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (message.role == MessageRole.assistant)
              _RoleIndicator(role: message.role),
            Flexible(
              child: Container(
                constraints: BoxConstraints(
                  maxWidth: MediaQuery.of(context).size.width * 0.8,
                ),
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                decoration: BoxDecoration(
                  color: _backgroundColor,
                  borderRadius: BorderRadius.circular(16).copyWith(
                    bottomLeft: message.role == MessageRole.assistant
                        ? const Radius.circular(4)
                        : null,
                    bottomRight: message.role == MessageRole.user
                        ? const Radius.circular(4)
                        : null,
                  ),
                  border: _border,
                ),
                child: _buildContent(context),
              ),
            ),
            if (message.role == MessageRole.user)
              _RoleIndicator(role: message.role),
          ],
        ),
      ),
    );
  }

  String get _accessibilityLabel {
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

  MainAxisAlignment get _alignment {
    switch (message.role) {
      case MessageRole.user:
        return MainAxisAlignment.end;
      case MessageRole.assistant:
      case MessageRole.system:
      case MessageRole.error:
        return MainAxisAlignment.start;
    }
  }

  Color get _backgroundColor {
    switch (message.role) {
      case MessageRole.user:
        return NavixTheme.primary.withOpacity(0.15);
      case MessageRole.assistant:
        return NavixTheme.surface;
      case MessageRole.system:
        return NavixTheme.surfaceVariant;
      case MessageRole.error:
        return NavixTheme.error.withOpacity(0.15);
    }
  }

  Border? get _border {
    if (message.role == MessageRole.error) {
      return Border.all(color: NavixTheme.error.withOpacity(0.5));
    }
    return null;
  }

  Widget _buildContent(BuildContext context) {
    if (message.role == MessageRole.assistant) {
      return _buildAssistantContent(context);
    }

    if (message.role == MessageRole.error) {
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

    // Check if this is a file link (from tool output)
    if (message.content.startsWith('📎 File:')) {
      return _buildFileLink(context);
    }

    // Check if content contains code blocks
    if (message.content.contains('```')) {
      return _buildMarkdownContent(context);
    }

    // Check if message suggests connecting Google account
    final needsGoogleConnect = !AuthService.instance.isSignedIn &&
        message.role == MessageRole.assistant &&
        _mentionsGoogleConnect(message.content);

    if (needsGoogleConnect) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SelectableText(
            message.content,
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
              color: NavixTheme.textPrimary,
            ),
          ),
          const SizedBox(height: 12),
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
                    SnackBar(content: Text('登录失败：$e')),
                  );
                }
              }
            },
            icon: const Icon(Icons.account_circle, size: 18),
            label: const Text('连接 Google 账号'),
            style: ElevatedButton.styleFrom(
              backgroundColor: NavixTheme.primary,
              foregroundColor: Colors.white,
            ),
          ),
        ],
      );
    }

    return SelectableText(
      message.content,
      style: Theme.of(context).textTheme.bodyLarge?.copyWith(
        color: NavixTheme.textPrimary,
      ),
    );
  }

  List<String> _splitThinking(String content) {
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
    final explicitThinking = message.thinking?.trim() ?? '';
    final thinking = explicitThinking.isNotEmpty ? explicitThinking : parts[0];
    final answer = parts[1];
    final widgets = <Widget>[];

    if (thinking.isNotEmpty) {
      widgets.add(
        _AccessibleExpansionSection(
          semanticTitle: '思考过程',
          child: Align(
            alignment: Alignment.centerLeft,
            child: SelectableText(
              thinking,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: NavixTheme.textTertiary,
                  ),
            ),
          ),
        ),
      );
    }

    if (message.thinkingMode != null) {
      final modeLabel = switch (message.thinkingMode) {
        'enabled' => '手动开启',
        'disabled' => '手动关闭',
        _ => '模型默认',
      };
      final detail = switch (message.thinkingMode) {
        'enabled' => thinking.isNotEmpty
            ? '本轮已向 Qwen3 发送 /think，并收到可展开的思考内容。'
            : '本轮已向 Qwen3 发送 /think，但模型没有返回可显示的 <think> 内容。',
        'disabled' => thinking.isNotEmpty
            ? '本轮已向 Qwen3 发送 /no_think，但模型仍返回了可显示的思考内容。'
            : '本轮已向 Qwen3 发送 /no_think，且没有返回可显示的思考内容。',
        _ => thinking.isNotEmpty
            ? '本轮未强制附加 /think 或 /no_think，模型返回了可展开的思考内容。'
            : '本轮未强制附加 /think 或 /no_think，模型没有返回可显示的思考内容。',
      };
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

    if (message.diagnostics?.trim().isNotEmpty ?? false) {
      widgets.add(const SizedBox(height: 8));
      widgets.add(_buildDiagnosticsPanel(context, message.diagnostics!.trim()));
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: widgets,
    );
  }

  Widget _buildDiagnosticsPanel(BuildContext context, String diagnostics) {
    return _AccessibleExpansionSection(
      semanticTitle: '工具调用诊断',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
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

  bool _mentionsGoogleConnect(String content) {
    final lower = content.toLowerCase();
    return (lower.contains('google') || lower.contains('gmail') || lower.contains('calendar')) &&
        (lower.contains('connect') || lower.contains('sign in') || lower.contains('settings') || lower.contains('authorize'));
  }

  Widget _buildFileLink(BuildContext context) {
    final filePath = message.content.replaceFirst('📎 File: ', '').trim();
    final fileName = filePath.split('/').last;

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        // Tappable file link - opens with Android default viewer
        Flexible(
          child: InkWell(
            onTap: () async {
              final file = File(filePath);
              if (await file.exists()) {
                try {
                  // Try to open with native file viewer
                  final opened = await _fileChannel.invokeMethod<bool>(
                    'openFile',
                    {'path': filePath},
                  );
                  if (opened != true && context.mounted) {
                    // Fallback to share if no app can open the file
                    await Share.shareXFiles([XFile(filePath)]);
                  }
                } catch (e) {
                  // Fallback to share on any error
                  if (context.mounted) {
                    await Share.shareXFiles([XFile(filePath)]);
                  }
                }
              } else {
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('找不到文件：$fileName')),
                  );
                }
              }
            },
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.insert_drive_file, size: 20, color: NavixTheme.primary),
                const SizedBox(width: 8),
                Flexible(
                  child: Text(
                    fileName,
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      color: NavixTheme.primary,
                      decoration: TextDecoration.underline,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(width: 12),
        // Share button
        InkWell(
          onTap: () async {
            final file = File(filePath);
            if (await file.exists()) {
              await Share.shareXFiles([XFile(filePath)]);
            }
          },
          borderRadius: BorderRadius.circular(16),
          child: Padding(
            padding: const EdgeInsets.all(4),
            child: Icon(Icons.share, size: 18, color: NavixTheme.textTertiary),
          ),
        ),
      ],
    );
  }

  Widget _buildMarkdownContent(BuildContext context) {
    // Simple code block parsing
    final parts = <Widget>[];
    final regex = RegExp(r'```(\w*)\n?([\s\S]*?)```');
    var lastEnd = 0;

    for (final match in regex.allMatches(message.content)) {
      // Text before code block
      if (match.start > lastEnd) {
        final text = message.content.substring(lastEnd, match.start);
        if (text.trim().isNotEmpty) {
          parts.add(SelectableText(
            text.trim(),
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
              color: NavixTheme.textPrimary,
            ),
          ));
        }
      }

      // Code block
      final language = match.group(1) ?? '';
      final code = match.group(2) ?? '';
      parts.add(_CodeBlock(code: code.trim(), language: language));

      lastEnd = match.end;
    }

    // Text after last code block
    if (lastEnd < message.content.length) {
      final text = message.content.substring(lastEnd);
      if (text.trim().isNotEmpty) {
        parts.add(SelectableText(
          text.trim(),
          style: Theme.of(context).textTheme.bodyLarge?.copyWith(
            color: NavixTheme.textPrimary,
          ),
        ));
      }
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: parts.map((w) => Padding(
        padding: const EdgeInsets.only(bottom: 8),
        child: w,
      )).toList(),
    );
  }

  void _showContextMenu(BuildContext context) {
    // Store reference to outer scaffold messenger before showing modal
    final scaffoldMessenger = ScaffoldMessenger.of(context);

    showModalBottomSheet(
      context: context,
      builder: (modalContext) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
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
          ],
        ),
      ),
    );
  }
}

class _AccessibleExpansionSection extends StatefulWidget {
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

  @override
  Widget build(BuildContext context) {
    final stateLabel = _expanded ? '已展开' : '已折叠';
    final actionLabel = _expanded ? '双击收起' : '双击展开';
    return Theme(
      data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
      child: ExpansionTile(
        tilePadding: EdgeInsets.zero,
        childrenPadding: const EdgeInsets.only(bottom: 10),
        initiallyExpanded: false,
        maintainState: true,
        onExpansionChanged: (value) {
          if (mounted) setState(() => _expanded = value);
        },
        title: Semantics(
          container: true,
          button: true,
          label: '${widget.semanticTitle}，当前$stateLabel，$actionLabel',
          child: ExcludeSemantics(
            child: Text(
              _expanded
                  ? '${widget.semanticTitle}（点击收起）'
                  : '${widget.semanticTitle}（点击展开）',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: NavixTheme.textSecondary,
                  ),
            ),
          ),
        ),
        children: [widget.child],
      ),
    );
  }
}

class _RoleIndicator extends StatelessWidget {
  final MessageRole role;

  const _RoleIndicator({required this.role});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 8),
      child: Container(
        width: 24,
        height: 24,
        decoration: BoxDecoration(
          color: _color.withOpacity(0.2),
          shape: BoxShape.circle,
        ),
        child: Center(
          child: Text(
            _icon,
            style: TextStyle(
              fontSize: 12,
              color: _color,
            ),
          ),
        ),
      ),
    );
  }

  String get _icon {
    switch (role) {
      case MessageRole.user:
        return '●';
      case MessageRole.assistant:
        return '◆';
      case MessageRole.system:
        return '◉';
      case MessageRole.error:
        return '!';
    }
  }

  Color get _color {
    switch (role) {
      case MessageRole.user:
        return NavixTheme.primary;
      case MessageRole.assistant:
        return NavixTheme.accentCyan;
      case MessageRole.system:
        return NavixTheme.textTertiary;
      case MessageRole.error:
        return NavixTheme.error;
    }
  }
}

class _CodeBlock extends StatelessWidget {
  final String code;
  final String language;

  const _CodeBlock({
    required this.code,
    required this.language,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: NavixTheme.background,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: NavixTheme.surfaceVariant),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (language.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Text(
                language,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: NavixTheme.textTertiary,
                ),
              ),
            ),
          SelectableText(
            code,
            style: NavixTheme.monoStyle,
          ),
        ],
      ),
    );
  }
}
