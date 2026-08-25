#!/usr/bin/env python3
"""Close the cold-start lifecycle race in v6 conversation history.

main.dart intentionally runs the app once in an initializing skeleton state and
again after services/database are ready. A ChatScreen created during the first
run may keep its State across the second runApp, so initState alone cannot own
history loading. didUpdateWidget must catch initializing:true -> false.
"""
from pathlib import Path

p = Path('lib/features/chat/presentation/chat_screen.dart')
text = p.read_text(encoding='utf-8')
anchor = '''  @override
  void didChangeMetrics() {
'''
insert = '''  @override
  void didUpdateWidget(covariant ChatScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.initializing && !widget.initializing && !_conversationLoaded) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) _initializeConversationHistory();
      });
    }
  }

'''
if insert.strip() not in text:
    count = text.count(anchor)
    if count != 1:
        raise SystemExit(f'Expected one didChangeMetrics anchor, found {count}')
    text = text.replace(anchor, insert + anchor, 1)
p.write_text(text, encoding='utf-8')
print('Applied v6 cold-start conversation lifecycle hardening')
