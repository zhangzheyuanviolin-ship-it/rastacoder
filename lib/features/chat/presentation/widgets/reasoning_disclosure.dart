import 'package:flutter/material.dart';

import '../../../../app/theme.dart';

/// Splits model output into hidden reasoning and the user-facing final answer.
///
/// Qwen3 and some other local reasoning models emit `<think>...</think>` in
/// their text stream. The reasoning is retained for inspection, but the normal
/// chat surface and accessibility label should expose only the final answer.
class AssistantReasoningParts {
  final String reasoning;
  final String answer;

  const AssistantReasoningParts({
    required this.reasoning,
    required this.answer,
  });

  bool get hasReasoning => reasoning.trim().isNotEmpty;

  static AssistantReasoningParts parse(String source) {
    final reasoningParts = <String>[];
    var visible = source;
    final completeThink = RegExp(
      r'<think>([\s\S]*?)</think>',
      caseSensitive: false,
    );

    for (final match in completeThink.allMatches(source)) {
      final text = match.group(1)?.trim();
      if (text != null && text.isNotEmpty) reasoningParts.add(text);
    }
    visible = visible.replaceAll(completeThink, '');

    // Defensive handling for an unfinished think block. This can happen while
    // streaming or if generation is interrupted. Never leak it into the normal
    // reply surface.
    final openThink = RegExp(r'<think>', caseSensitive: false).firstMatch(visible);
    if (openThink != null) {
      final tail = visible.substring(openThink.end).trim();
      if (tail.isNotEmpty) reasoningParts.add(tail);
      visible = visible.substring(0, openThink.start);
    }

    visible = visible
        .replaceAll(RegExp(r'</?think>', caseSensitive: false), '')
        .trim();

    return AssistantReasoningParts(
      reasoning: reasoningParts.join('\n\n'),
      answer: visible,
    );
  }
}

/// Accessible, collapsed-by-default reasoning section.
class ReasoningDisclosure extends StatefulWidget {
  final String reasoning;

  const ReasoningDisclosure({
    super.key,
    required this.reasoning,
  });

  @override
  State<ReasoningDisclosure> createState() => _ReasoningDisclosureState();
}

class _ReasoningDisclosureState extends State<ReasoningDisclosure> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Semantics(
          button: true,
          expanded: _expanded,
          label: _expanded ? '收起思考过程' : '展开思考过程',
          hint: _expanded ? '双击收起模型思考内容' : '双击查看模型思考内容',
          child: InkWell(
            onTap: () => setState(() => _expanded = !_expanded),
            borderRadius: BorderRadius.circular(8),
            child: Padding(
              padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 4),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    _expanded ? Icons.expand_less : Icons.expand_more,
                    size: 20,
                    color: NavixTheme.textTertiary,
                  ),
                  const SizedBox(width: 4),
                  Text(
                    _expanded ? '思考过程（已展开）' : '思考过程（默认收起）',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: NavixTheme.textTertiary,
                        ),
                  ),
                ],
              ),
            ),
          ),
        ),
        if (_expanded)
          Container(
            width: double.infinity,
            margin: const EdgeInsets.only(top: 6, bottom: 10),
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: NavixTheme.background.withOpacity(0.7),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: NavixTheme.surfaceVariant),
            ),
            child: SelectableText(
              widget.reasoning,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: NavixTheme.textTertiary,
                  ),
            ),
          ),
      ],
    );
  }
}
