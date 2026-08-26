from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manager_path = ROOT / 'lib/core/services/conversation_manager.dart'
history_path = ROOT / 'lib/features/chat/presentation/conversation_history_screen.dart'


def once(text, old, new, label):
    if new in text:
        print(label + ': already applied')
        return text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected one anchor, found {count}')
    print(label + ': applied')
    return text.replace(old, new, 1)

manager = manager_path.read_text(encoding='utf-8')
history = history_path.read_text(encoding='utf-8')

if 'RASTACODER_V14_CLEAR_ALL_HISTORY' not in manager:
    old = '''  Future<void> deleteConversation(int conversationId) async {
    if (_isar == null) return;
    await _isar!.writeTxn(() async {
      await _isar!.messages.filter().conversationIdEqualTo(conversationId).deleteAll();
      await _isar!.conversations.delete(conversationId);
    });
  }

'''
    new = '''  Future<void> deleteConversation(int conversationId) async {
    if (_isar == null) return;
    await _isar!.writeTxn(() async {
      await _isar!.messages.filter().conversationIdEqualTo(conversationId).deleteAll();
      await _isar!.conversations.delete(conversationId);
    });
  }

  // RASTACODER_V14_CLEAR_ALL_HISTORY
  /// Delete every persisted chat conversation and message in one transaction.
  /// Generated/workspace files are intentionally left untouched.
  Future<void> deleteAllConversations() async {
    if (_isar == null) return;
    await _isar!.writeTxn(() async {
      await _isar!.messages.clear();
      await _isar!.conversations.clear();
    });
  }

'''
    manager = once(manager, old, new, 'manager clear-all transaction')

if 'RASTACODER_V14_CLEAR_ALL_HISTORY_UI' not in history:
    old = '''  Future<void> _delete(Map<String, dynamic> item) async {
'''
    method = '''  // RASTACODER_V14_CLEAR_ALL_HISTORY_UI
  Future<void> _deleteAll() async {
    if (_items.isEmpty) return;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('清除所有聊天记录'),
        content: const Text('确认清除全部聊天记录吗？此操作会删除所有对话和消息，无法撤销。已生成文件和工作区文件不会被删除。'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('取消')),
          TextButton(onPressed: () => Navigator.pop(context, true), child: const Text('清除全部')),
        ],
      ),
    );
    if (confirmed != true) return;
    await ConversationManager.instance.deleteAllConversations();
    if (!mounted) return;
    Navigator.pop(context, -1);
  }

  Future<void> _delete(Map<String, dynamic> item) async {
'''
    history = once(history, old, method, 'history clear-all method')

    old_appbar = "      appBar: AppBar(title: const Text('聊天记录')),\n"
    new_appbar = '''      appBar: AppBar(
        title: const Text('聊天记录'),
        actions: [
          Semantics(
            button: true,
            label: '清除所有聊天记录',
            hint: '双击后会先要求确认',
            child: IconButton(
              tooltip: '清除所有聊天记录',
              onPressed: _loading || _items.isEmpty ? null : _deleteAll,
              icon: const Icon(Icons.delete_sweep_outlined),
            ),
          ),
        ],
      ),
'''
    history = once(history, old_appbar, new_appbar, 'history clear-all appbar action')

manager_path.write_text(manager, encoding='utf-8')
history_path.write_text(history, encoding='utf-8')
print('V14 clear-all conversation history patch applied; per-item delete retained.')
