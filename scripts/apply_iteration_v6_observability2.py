#!/usr/bin/env python3
"""Make the manual Qwen3 Thinking setting empirically inspectable in v6 UI."""
from pathlib import Path

p = Path('lib/features/chat/presentation/widgets/message_bubble.dart')
text = p.read_text(encoding='utf-8')
old = '''    if (thinking.isEmpty && message.thinkingMode != null) {
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
'''
new = '''    if (message.thinkingMode != null) {
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
'''
count = text.count(old)
if count != 1:
    raise SystemExit(f'Expected one Thinking mode status block, found {count}')
text = text.replace(old, new, 1)
p.write_text(text, encoding='utf-8')
print('Applied v6 explicit Qwen3 Thinking directive/status observability')
