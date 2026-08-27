import 'package:flutter/material.dart';

import '../../../core/services/conversation_manager.dart';

/// Accessible conversation-history manager backed by the existing Isar store.
class ConversationHistoryScreen extends StatefulWidget {
  final int? currentConversationId;

  const ConversationHistoryScreen({
    super.key,
    this.currentConversationId,
  });

  @override
  State<ConversationHistoryScreen> createState() => _ConversationHistoryScreenState();
}

class _ConversationHistoryScreenState extends State<ConversationHistoryScreen> {
  List<Map<String, dynamic>> _items = const [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _reload();
  }

  Future<void> _reload() async {
    final rows = await ConversationManager.instance.listConversationSummaries();
    if (!mounted) return;
    setState(() {
      _items = rows;
      _loading = false;
    });
  }

  Future<void> _rename(Map<String, dynamic> item) async {
    final controller = TextEditingController(text: item['title']?.toString() ?? '');
    final value = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('重命名对话'),
        content: TextField(
          controller: controller,
          autofocus: true,
          decoration: const InputDecoration(labelText: '对话名称'),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('取消')),
          TextButton(onPressed: () => Navigator.pop(context, controller.text.trim()), child: const Text('保存')),
        ],
      ),
    );
    controller.dispose();
    if (value == null || value.isEmpty) return;
    await ConversationManager.instance.renameConversation(item['id'] as int, value);
    await _reload();
  }

  // RASTACODER_V14_CLEAR_ALL_HISTORY_UI
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
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('删除对话'),
        content: Text('确认删除“${item['title']}”及其中的聊天记录吗？'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('取消')),
          TextButton(onPressed: () => Navigator.pop(context, true), child: const Text('删除')),
        ],
      ),
    );
    if (confirmed != true) return;
    final id = item['id'] as int;
    await ConversationManager.instance.deleteConversation(id);
    if (!mounted) return;
    if (id == widget.currentConversationId) {
      Navigator.pop(context, -1);
      return;
    }
    await _reload();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
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
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _items.isEmpty
              ? const Center(child: Text('暂无聊天记录'))
              : ListView.separated(
                  itemCount: _items.length,
                  separatorBuilder: (_, __) => const Divider(height: 1),
                  itemBuilder: (context, index) {
                    final item = _items[index];
                    final id = item['id'] as int;
                    final title = item['title']?.toString() ?? '未命名对话';
                    final updated = item['updatedAt'];
                    final selected = id == widget.currentConversationId;
                    // RASTACODER_V10_ACCESSIBLE_HISTORY_OPEN
                    return Row(
                      children: [
                        Expanded(
                          child: Semantics(
                            button: true,
                            selected: selected,
                            label: '打开对话：$title${selected ? '，当前对话' : ''}',
                            hint: '双击打开这条聊天记录',
                            onTap: () => Navigator.pop(context, id),
                            child: ExcludeSemantics(
                              child: ListTile(
                                title: Text(title),
                                subtitle: Text(updated is DateTime ? updated.toLocal().toString() : ''),
                                leading: Icon(selected ? Icons.chat_bubble : Icons.chat_bubble_outline),
                                onTap: () => Navigator.pop(context, id),
                              ),
                            ),
                          ),
                        ),
                        PopupMenuButton<String>(
                          tooltip: '管理对话：$title',
                          onSelected: (value) {
                            if (value == 'rename') _rename(item);
                            if (value == 'delete') _delete(item);
                          },
                          itemBuilder: (_) => const [
                            PopupMenuItem(value: 'rename', child: Text('重命名')),
                            PopupMenuItem(value: 'delete', child: Text('删除')),
                          ],
                        ),
                      ],
                    );
                  },
                ),
    );
  }
}
