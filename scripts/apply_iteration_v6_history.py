#!/usr/bin/env python3
"""Wire the already-existing Isar conversation data layer into the v6 chat UI."""
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Initialize the existing ConversationManager with the already-open Isar DB.
# ---------------------------------------------------------------------------
main_path = Path('lib/main.dart')
main = main_path.read_text(encoding='utf-8')
main = replace_once(
    main,
    "import 'core/services/connectivity_service.dart';\n",
    "import 'core/services/connectivity_service.dart';\nimport 'core/services/conversation_manager.dart';\n",
    'conversation manager import',
)
main = replace_once(
    main,
    "  // Initialize cost manager for API usage tracking\n  CostManager.instance.initialize(isar);\n",
    "  // Initialize cost manager for API usage tracking\n  CostManager.instance.initialize(isar);\n\n  // Wire the existing Isar Conversation/Message store into the chat UI.\n  ConversationManager.instance.initialize(isar);\n",
    'conversation manager initialize',
)
main_path.write_text(main, encoding='utf-8')


# ---------------------------------------------------------------------------
# Extend ConversationManager with UI-safe history APIs and make session sync
# resilient while Python is still starting/restarting.
# ---------------------------------------------------------------------------
manager_path = Path('lib/core/services/conversation_manager.dart')
manager = manager_path.read_text(encoding='utf-8')

anchor = "  /// Check if a conversation needs summarization and trigger if so.\n"
helpers = r'''  /// Return active conversations newest-first for the history UI.
  Future<List<Map<String, dynamic>>> listConversationSummaries() async {
    if (_isar == null) return const [];
    final rows = await _isar!.conversations
        .filter()
        .isArchivedEqualTo(false)
        .sortByUpdatedAtDesc()
        .findAll();
    return rows
        .map((c) => <String, dynamic>{
              'id': c.id,
              'title': c.title,
              'createdAt': c.createdAt,
              'updatedAt': c.updatedAt,
            })
        .toList(growable: false);
  }

  /// Return persisted visible messages without exposing DB model types to UI.
  Future<List<Map<String, dynamic>>> getVisibleMessages(int conversationId) async {
    if (_isar == null) return const [];
    final rows = await _isar!.messages
        .filter()
        .conversationIdEqualTo(conversationId)
        .sortByCreatedAt()
        .findAll();
    return rows
        .map((m) => <String, dynamic>{
              'role': m.role.name,
              'content': m.content,
              'createdAt': m.createdAt,
              'attachments': m.attachments.map((a) => a.localPath).where((p) => p.isNotEmpty).toList(),
            })
        .toList(growable: false);
  }

  /// Persist a message which has already been processed by Python. This avoids
  /// double-inserting the same user/assistant message into Python SessionState.
  Future<void> storeVisibleMessage({
    required int conversationId,
    required String role,
    required String content,
    List<String>? attachmentPaths,
  }) async {
    if (_isar == null) return;
    final attachments = attachmentPaths
        ?.map((path) => <String, dynamic>{
              'local_path': path,
              'original_name': p.basename(path),
            })
        .toList();
    final message = Message()
      ..conversationId = conversationId
      ..role = _parseRole(role)
      ..content = content
      ..createdAt = DateTime.now()
      ..tokenCount = _estimateTokens(content)
      ..attachments = _buildAttachments(attachments);

    await _isar!.writeTxn(() async {
      await _isar!.messages.put(message);
      final conversation = await _isar!.conversations.get(conversationId);
      if (conversation != null) {
        conversation.updatedAt = DateTime.now();
        await _isar!.conversations.put(conversation);
      }
    });
  }

  Future<void> renameConversation(int conversationId, String title) async {
    if (_isar == null) return;
    final cleaned = title.trim();
    if (cleaned.isEmpty) return;
    await _isar!.writeTxn(() async {
      final conversation = await _isar!.conversations.get(conversationId);
      if (conversation == null) return;
      conversation.title = cleaned.length > 80 ? cleaned.substring(0, 80) : cleaned;
      conversation.updatedAt = DateTime.now();
      await _isar!.conversations.put(conversation);
    });
  }

  Future<void> deleteConversation(int conversationId) async {
    if (_isar == null) return;
    await _isar!.writeTxn(() async {
      await _isar!.messages.filter().conversationIdEqualTo(conversationId).deleteAll();
      await _isar!.conversations.delete(conversationId);
    });
  }

'''
if helpers.strip() not in manager:
    manager = manager.replace(anchor, helpers + anchor, 1)

# History loading should still update UI even if Python has not finished booting.
old = r'''    // Send full sync to Python
    await _bridge.applyDelta({
      'action': 'sync_full',
      'conversation_id': conversationId,
      'messages': messages.map((m) => m.toSyncJson()).toList(),
      'summary': conversation.summary,
    });
'''
new = r'''    // Send full sync when Python is ready. ChatScreen retries this on the
    // Python ready event after cold start/restart, so DB access never depends
    // on runtime initialization timing.
    if (_bridge.status == PythonStatus.ready) {
      await _bridge.applyDelta({
        'action': 'sync_full',
        'conversation_id': conversationId,
        'messages': messages.map((m) => m.toSyncJson()).toList(),
        'summary': conversation.summary,
      });
    }
'''
manager = replace_once(manager, old, new, 'load conversation guarded sync')

old = r'''    // Notify Python of new conversation
    await _bridge.applyDelta({
      'action': 'new_conversation',
      'conversation_id': conversation.id,
    });
'''
new = r'''    // Notify Python when ready. ChatScreen also re-syncs the selected
    // conversation on Python ready after cold start/restart.
    if (_bridge.status == PythonStatus.ready) {
      await _bridge.applyDelta({
        'action': 'new_conversation',
        'conversation_id': conversation.id,
      });
    }
'''
manager = replace_once(manager, old, new, 'new conversation guarded sync')

# Fix enum/string comparison in summary formatting while this service is active.
manager = manager.replace(
    "      final role = msg.role == 'user' ? 'User' : 'Assistant';",
    "      final role = msg.role == MessageRole.user ? 'User' : 'Assistant';",
)
manager_path.write_text(manager, encoding='utf-8')


# ---------------------------------------------------------------------------
# Accessible history screen: load/switch, rename, delete.
# ---------------------------------------------------------------------------
history = r'''import 'package:flutter/material.dart';

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
'''
Path('lib/features/chat/presentation/conversation_history_screen.dart').write_text(history, encoding='utf-8')


# ---------------------------------------------------------------------------
# ChatScreen: current conversation lifecycle, persistence, history/new buttons.
# This patch runs AFTER apply_iteration_v6_ui.py so ChatMessage already carries
# thinking/diagnostics metadata.
# ---------------------------------------------------------------------------
chat_path = Path('lib/features/chat/presentation/chat_screen.dart')
chat = chat_path.read_text(encoding='utf-8')
chat = replace_once(
    chat,
    "import '../../../core/services/connectivity_service.dart';\n",
    "import '../../../core/services/connectivity_service.dart';\nimport '../../../core/services/conversation_manager.dart';\n",
    'chat conversation manager import',
)
chat = replace_once(
    chat,
    "import 'widgets/context_bar.dart';\n",
    "import 'widgets/context_bar.dart';\nimport 'conversation_history_screen.dart';\n",
    'chat history screen import',
)

old = r'''  Set<String> _enabledSkills = Set<String>.from(LocalToolSkillCatalog.allIds);
  final Set<String> _announcedNativeToolIds = <String>{};
'''
new = r'''  Set<String> _enabledSkills = Set<String>.from(LocalToolSkillCatalog.allIds);
  final Set<String> _announcedNativeToolIds = <String>{};
  int? _conversationId;
  String _conversationTitle = '新对话';
  bool _conversationLoaded = false;
'''
chat = replace_once(chat, old, new, 'chat conversation fields')

old = r'''    _listenToSharedFiles();
  }
'''
new = r'''    _listenToSharedFiles();
    if (!widget.initializing) {
      WidgetsBinding.instance.addPostFrameCallback((_) => _initializeConversationHistory());
    }
  }
'''
chat = replace_once(chat, old, new, 'chat history init')

anchor = r'''  Future<void> _loadSelfImproveSetting() async {
'''
methods = r'''  Future<void> _initializeConversationHistory() async {
    if (_conversationLoaded || widget.initializing) return;
    final summaries = await ConversationManager.instance.listConversationSummaries();
    if (!mounted) return;
    if (summaries.isEmpty) {
      await _startNewConversation();
      return;
    }
    final newest = summaries.first;
    await _loadConversation(newest['id'] as int, newest['title']?.toString() ?? '未命名对话');
  }

  Future<int> _ensureConversation() async {
    if (_conversationId != null) return _conversationId!;
    final conversation = await ConversationManager.instance.createConversation(title: '新对话');
    if (mounted) {
      setState(() {
        _conversationId = conversation.id;
        _conversationTitle = conversation.title;
        _conversationLoaded = true;
      });
    }
    return conversation.id;
  }

  Future<void> _loadConversation(int id, String title) async {
    final rows = await ConversationManager.instance.getVisibleMessages(id);
    if (!mounted) return;
    final restored = rows.map((row) {
      final role = switch (row['role']?.toString()) {
        'user' => MessageRole.user,
        'assistant' => MessageRole.assistant,
        'toolResult' => MessageRole.system,
        _ => MessageRole.system,
      };
      final attachments = (row['attachments'] as List?)?.map((e) => e.toString()).toList();
      return ChatMessage(
        role: role,
        content: row['content']?.toString() ?? '',
        timestamp: row['createdAt'] is DateTime ? row['createdAt'] as DateTime : DateTime.now(),
        attachments: attachments?.isNotEmpty == true ? attachments : null,
      );
    }).toList();
    setState(() {
      _conversationId = id;
      _conversationTitle = title;
      _conversationLoaded = true;
      _messages
        ..clear()
        ..addAll(restored);
      _attachedFiles = [];
      _externalFiles = [];
    });
    if (PythonBridge.instance.status == PythonStatus.ready) {
      await ConversationManager.instance.loadConversation(id);
    }
    _scrollToBottom();
  }

  Future<void> _startNewConversation() async {
    if (_isProcessing) return;
    final conversation = await ConversationManager.instance.createConversation(title: '新对话');
    if (!mounted) return;
    setState(() {
      _conversationId = conversation.id;
      _conversationTitle = conversation.title;
      _conversationLoaded = true;
      _messages.clear();
      _attachedFiles = [];
      _externalFiles = [];
      _activeMode = null;
      _statusMessage = null;
    });
  }

  Future<void> _openConversationHistory() async {
    if (_isProcessing) return;
    final selected = await Navigator.push<int>(
      context,
      MaterialPageRoute(
        builder: (_) => ConversationHistoryScreen(currentConversationId: _conversationId),
      ),
    );
    if (!mounted || selected == null) return;
    if (selected == -1) {
      await _startNewConversation();
      return;
    }
    final summaries = await ConversationManager.instance.listConversationSummaries();
    final match = summaries.where((row) => row['id'] == selected).toList();
    if (match.isEmpty) {
      await _startNewConversation();
      return;
    }
    await _loadConversation(selected, match.first['title']?.toString() ?? '未命名对话');
  }

  Future<void> _persistVisibleMessage(
    MessageRole role,
    String content, {
    List<String>? attachments,
  }) async {
    final id = await _ensureConversation();
    final dbRole = switch (role) {
      MessageRole.user => 'user',
      MessageRole.assistant => 'assistant',
      MessageRole.error => 'system',
      MessageRole.system => 'system',
    };
    await ConversationManager.instance.storeVisibleMessage(
      conversationId: id,
      role: dbRole,
      content: content,
      attachmentPaths: attachments,
    );
  }

  Future<void> _autoTitleConversation(String userText) async {
    final id = _conversationId;
    if (id == null || _conversationTitle != '新对话') return;
    var title = userText.trim().replaceAll(RegExp(r'\s+'), ' ');
    if (title.isEmpty && _attachedFiles.isNotEmpty) {
      title = _attachedFiles.first.split('/').last;
    }
    if (title.isEmpty) return;
    if (title.length > 28) title = '${title.substring(0, 28)}…';
    await ConversationManager.instance.renameConversation(id, title);
    if (mounted) setState(() => _conversationTitle = title);
  }

'''
chat = replace_once(chat, anchor, methods + anchor, 'chat history methods')

# When Python becomes ready after cold start/restart, restore selected DB session.
old = r'''      });
    });
  }

  void _sendStoredApiKeyToPython() {
'''
# This anchor occurs after _checkApiKey, not status listener, so avoid it.
# Patch the explicit ready switch case instead.
old_ready = r'''          case PythonStatus.ready:
            _statusMessage = null;
            break;
'''
new_ready = r'''          case PythonStatus.ready:
            _statusMessage = null;
            final id = _conversationId;
            if (id != null) {
              Future.microtask(() => ConversationManager.instance.loadConversation(id));
            }
            break;
'''
chat = replace_once(chat, old_ready, new_ready, 'python ready conversation resync')

# Ensure a conversation exists before the user message is appended, then persist it.
old = r'''    // Add user message
    setState(() {
      _messages.add(ChatMessage(
        role: MessageRole.user,
        content: text,
        timestamp: DateTime.now(),
        attachments: _attachedFiles.isNotEmpty ? List.from(_attachedFiles) : null,
      ));
      _inputController.clear();
    });

    _scrollToBottom();
'''
new = r'''    final conversationId = await _ensureConversation();
    final userAttachments = _attachedFiles.isNotEmpty ? List<String>.from(_attachedFiles) : null;

    // Add and persist the user message. Persistence is DB-only here because
    // process_query itself owns Python SessionState insertion for this turn.
    setState(() {
      _messages.add(ChatMessage(
        role: MessageRole.user,
        content: text,
        timestamp: DateTime.now(),
        attachments: userAttachments,
      ));
      _inputController.clear();
    });
    await ConversationManager.instance.storeVisibleMessage(
      conversationId: conversationId,
      role: 'user',
      content: text,
      attachmentPaths: userAttachments,
    );
    await _autoTitleConversation(text);

    _scrollToBottom();
'''
chat = replace_once(chat, old, new, 'persist user message')

# Persist final assistant/error output and created file-link messages.
old = r'''        setState(() {
          _messages.add(ChatMessage(
            role: hasError ? MessageRole.error : MessageRole.assistant,
            content: content,
            timestamp: DateTime.now(),
            thinking: thinking,
            thinkingMode: thinkingMode,
            diagnostics: diagnostics,
          ));
          // Add tappable file links for every created file
          if (createdFiles != null && !hasError) {
            for (final filePath in createdFiles) {
              _messages.add(ChatMessage(
                role: MessageRole.system,
                content: '\u{1F4CE} File: $filePath',
                timestamp: DateTime.now(),
              ));
            }
          }
        });
'''
new = r'''        setState(() {
          _messages.add(ChatMessage(
            role: hasError ? MessageRole.error : MessageRole.assistant,
            content: content,
            timestamp: DateTime.now(),
            thinking: thinking,
            thinkingMode: thinkingMode,
            diagnostics: diagnostics,
          ));
          // Add tappable file links for every created file
          if (createdFiles != null && !hasError) {
            for (final filePath in createdFiles) {
              _messages.add(ChatMessage(
                role: MessageRole.system,
                content: '\u{1F4CE} File: $filePath',
                timestamp: DateTime.now(),
              ));
            }
          }
        });
        await ConversationManager.instance.storeVisibleMessage(
          conversationId: conversationId,
          role: hasError ? 'system' : 'assistant',
          content: content,
        );
        if (createdFiles != null && !hasError) {
          for (final filePath in createdFiles) {
            await ConversationManager.instance.storeVisibleMessage(
              conversationId: conversationId,
              role: 'system',
              content: '\u{1F4CE} File: $filePath',
            );
          }
        }
'''
chat = replace_once(chat, old, new, 'persist final response')

# Persist RPC error response as a system/error history record.
old = r'''      } else if (response.isError) {
        setState(() {
          _messages.add(ChatMessage(
            role: MessageRole.error,
            content: response.error?.message ?? '未知错误',
            timestamp: DateTime.now(),
          ));
        });
'''
new = r'''      } else if (response.isError) {
        final errorText = response.error?.message ?? '未知错误';
        setState(() {
          _messages.add(ChatMessage(
            role: MessageRole.error,
            content: errorText,
            timestamp: DateTime.now(),
          ));
        });
        await ConversationManager.instance.storeVisibleMessage(
          conversationId: conversationId,
          role: 'system',
          content: errorText,
        );
'''
chat = replace_once(chat, old, new, 'persist rpc error')

# App bar gets explicit history and new-chat controls; both have screen-reader tooltips.
old = r'''        title: const Text('NavixMind'),
        leading: IconButton(
'''
new = r'''        title: Text(_conversationTitle == '新对话' ? 'RastaCoder' : 'RastaCoder · $_conversationTitle'),
        leading: IconButton(
'''
chat = replace_once(chat, old, new, 'conversation title')

old = r'''        actions: [
          if (_isProcessing)
            const Padding(
              padding: EdgeInsets.only(right: 16),
              child: BrailleSpinner(size: 20),
            ),
        ],
'''
new = r'''        actions: [
          IconButton(
            onPressed: _isProcessing ? null : _openConversationHistory,
            icon: const Icon(Icons.history),
            tooltip: '聊天记录',
          ),
          IconButton(
            onPressed: _isProcessing ? null : _startNewConversation,
            icon: const Icon(Icons.add_comment_outlined),
            tooltip: '新建对话',
          ),
          if (_isProcessing)
            const Padding(
              padding: EdgeInsets.only(right: 16),
              child: BrailleSpinner(size: 20),
            ),
        ],
'''
chat = replace_once(chat, old, new, 'history/new actions')

chat_path.write_text(chat, encoding='utf-8')
print('Applied RastaCoder v6 persistent conversation history patch')
