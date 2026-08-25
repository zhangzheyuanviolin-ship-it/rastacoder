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
      appBar: AppBar(title: const Text('聊天记录')),
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
                    return Semantics(
                      selected: selected,
                      label: '$title${selected ? '，当前对话' : ''}',
                      child: ListTile(
                        title: Text(title),
                        subtitle: Text(updated is DateTime ? updated.toLocal().toString() : ''),
                        leading: Icon(selected ? Icons.chat_bubble : Icons.chat_bubble_outline),
                        onTap: () => Navigator.pop(context, id),
                        trailing: PopupMenuButton<String>(
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
                      ),
                    );
                  },
                ),
    );
  }
}
