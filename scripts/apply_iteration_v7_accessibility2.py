#!/usr/bin/env python3
from pathlib import Path

p = Path('lib/features/chat/presentation/widgets/message_bubble.dart')
text = p.read_text()

# Replace the whole Thinking panel regardless of the intermediate v7 UI wrapper.
start = text.index('    if (thinking.isNotEmpty) {')
end = text.index('    if (message.thinkingMode != null) {', start)
thinking_block = '''    if (thinking.isNotEmpty) {
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

'''
text = text[:start] + thinking_block + text[end:]

# Replace diagnostics panel with the same stateful, dynamic semantic control.
start = text.index('  Widget _buildDiagnosticsPanel(BuildContext context, String diagnostics) {')
end = text.index('  Widget _buildTextContent(BuildContext context, String content) {', start)
diag_block = '''  Widget _buildDiagnosticsPanel(BuildContext context, String diagnostics) {
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

'''
text = text[:start] + diag_block + text[end:]

# A stateful helper gives accessibility services a real independent button and
# updates "已折叠/已展开" after activation. This fixes the v6 static label which
# always claimed the panel was collapsed even after expansion.
anchor = 'class _RoleIndicator extends StatelessWidget {'
helper = '''class _AccessibleExpansionSection extends StatefulWidget {
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

'''
if anchor not in text:
    raise SystemExit('v7 accessibility helper anchor missing')
text = text.replace(anchor, helper + anchor, 1)
p.write_text(text)
print('Applied v7 stateful accessible expansion controls')
