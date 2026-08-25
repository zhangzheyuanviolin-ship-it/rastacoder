#!/usr/bin/env python3
"""Make v6 conversation history preserve real persistent file references.

PythonBridge already copies incoming attachments out of transient picker/cache
storage before inference. Expose that helper to ChatScreen so the database and
Python receive the same durable paths. Also attach created output files to the
persisted assistant message so SessionState.sync_full can rebuild its file map
when a historical conversation is reopened.
"""
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)


bridge_path = Path('lib/core/bridge/bridge.dart')
bridge = bridge_path.read_text(encoding='utf-8')
anchor = '''  /// Copy attached files from cache to persistent internal storage.
  /// Returns the list of persistent paths.
  Future<List<String>> _persistAttachedFiles(List<String> cachePaths) async {
'''
public = '''  /// Persist attachment paths for conversation history before a query is sent.
  /// Calling sendQuery with the returned paths is idempotent because the private
  /// persistence helper detects files which are already in the durable folder.
  Future<List<String>> persistAttachedFilesForConversation(List<String> paths) {
    return _persistAttachedFiles(paths);
  }

'''
if public.strip() not in bridge:
    bridge = replace_once(bridge, anchor, public + anchor, 'public attachment persistence')
bridge_path.write_text(bridge, encoding='utf-8')


chat_path = Path('lib/features/chat/presentation/chat_screen.dart')
chat = chat_path.read_text(encoding='utf-8')
old = '''    final conversationId = await _ensureConversation();
    final userAttachments = _attachedFiles.isNotEmpty ? List<String>.from(_attachedFiles) : null;

    // Add and persist the user message. Persistence is DB-only here because
'''
new = '''    final conversationId = await _ensureConversation();
    final originalAttachments = _attachedFiles.isNotEmpty ? List<String>.from(_attachedFiles) : null;
    final userAttachments = originalAttachments == null
        ? null
        : await PythonBridge.instance.persistAttachedFilesForConversation(originalAttachments);

    // Add and persist the user message with durable attachment paths. Persistence
    // is DB-only here because
'''
chat = replace_once(chat, old, new, 'durable user attachment paths')

old = '''        filePaths: _attachedFiles.isNotEmpty ? _attachedFiles : null,
        context: {
'''
new = '''        filePaths: userAttachments,
        context: {
'''
chat = replace_once(chat, old, new, 'send durable attachments')

old = '''        await ConversationManager.instance.storeVisibleMessage(
          conversationId: conversationId,
          role: hasError ? 'system' : 'assistant',
          content: content,
        );
'''
new = '''        await ConversationManager.instance.storeVisibleMessage(
          conversationId: conversationId,
          role: hasError ? 'system' : 'assistant',
          content: content,
          attachmentPaths: !hasError && createdFiles != null
              ? createdFiles.map((e) => e.toString()).toList()
              : null,
        );
'''
chat = replace_once(chat, old, new, 'persist created outputs on assistant message')

chat_path.write_text(chat, encoding='utf-8')
print('Applied v6 durable conversation attachment/file-map history hardening')
