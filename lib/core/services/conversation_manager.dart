import 'dart:async';
import 'dart:io';

import 'package:isar/isar.dart';
import 'package:path/path.dart' as p;

import '../bridge/bridge.dart';
import '../database/collections/conversation.dart';
import '../database/collections/message.dart';

/// Manages conversation state and auto-summarization.
///
/// When a conversation exceeds the message threshold, automatically
/// generates a summary using the LLM and updates the session state.
class ConversationManager {
  static final ConversationManager instance = ConversationManager._();

  ConversationManager._();

  Isar? _isar;
  final _bridge = PythonBridge.instance;

  /// Message count threshold for auto-summarization
  static const int summarizationThreshold = 50;

  /// Minimum messages to keep after summarization (most recent)
  static const int keepRecentCount = 20;

  /// Initialize with Isar database reference
  void initialize(Isar isar) {
    _isar = isar;
  }

  /// Return active conversations newest-first for the history UI.
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

  /// Check if a conversation needs summarization and trigger if so.
  ///
  /// Should be called after adding a new message to a conversation.
  Future<void> checkAndSummarize(int conversationId) async {
    if (_isar == null) return;

    final messageCount = await _isar!.messages
        .filter()
        .conversationIdEqualTo(conversationId)
        .count();

    if (messageCount >= summarizationThreshold) {
      await _triggerSummarization(conversationId);
    }
  }

  /// Generate a summary of older messages.
  Future<void> _triggerSummarization(int conversationId) async {
    if (_isar == null) return;
    if (_bridge.status != PythonStatus.ready) return;

    // Get the conversation
    final conversation =
        await _isar!.conversations.get(conversationId);
    if (conversation == null) return;

    // Already summarized recently? Skip if less than threshold + 10 new messages
    final currentCount = await _isar!.messages
        .filter()
        .conversationIdEqualTo(conversationId)
        .count();

    if (conversation.summarizedUpToId != null) {
      final newMessageCount = await _isar!.messages
          .filter()
          .conversationIdEqualTo(conversationId)
          .idGreaterThan(conversation.summarizedUpToId!)
          .count();

      // Only re-summarize if we have many new messages
      if (newMessageCount < 30) return;
    }

    // Get messages to summarize (all except recent ones)
    final allMessages = await _isar!.messages
        .filter()
        .conversationIdEqualTo(conversationId)
        .sortByCreatedAt()
        .findAll();

    if (allMessages.length <= keepRecentCount) return;

    // Messages to summarize (older ones)
    final messagesToSummarize =
        allMessages.take(allMessages.length - keepRecentCount).toList();

    if (messagesToSummarize.isEmpty) return;

    // Build the text to summarize
    final textToSummarize = _buildSummaryText(
      messagesToSummarize,
      conversation.summary,
    );

    // Request summary from LLM (using a special summarization query)
    try {
      final response = await _bridge.sendQuery(
        query: _buildSummarizationPrompt(textToSummarize),
        checkCostLimits: false, // Summarization is internal, don't block
      );

      final summaryText = response.result?['content'] as String?;
      if (summaryText == null || summaryText.isEmpty) return;

      // Get the ID of the last summarized message
      final lastSummarizedId = messagesToSummarize.last.id;

      // Update conversation with summary
      await _isar!.writeTxn(() async {
        conversation.summary = summaryText;
        conversation.summarizedUpToId = lastSummarizedId;
        conversation.updatedAt = DateTime.now();
        await _isar!.conversations.put(conversation);
      });

      // Send delta to Python to update session state
      await _bridge.applyDelta({
        'action': 'set_summary',
        'summary': summaryText,
        'summarized_up_to_id': lastSummarizedId,
      });
    } catch (e) {
      // Summarization failed - log but don't block
      // This is a background optimization, not critical
    }
  }

  String _buildSummaryText(
    List<Message> messages,
    String? existingSummary,
  ) {
    final buffer = StringBuffer();

    if (existingSummary != null) {
      buffer.writeln('Previous summary:');
      buffer.writeln(existingSummary);
      buffer.writeln();
      buffer.writeln('New messages to include:');
    }

    for (final msg in messages) {
      final role = msg.role == MessageRole.user ? 'User' : 'Assistant';
      // Truncate very long messages
      var content = msg.content;
      if (content.length > 500) {
        content = '${content.substring(0, 500)}...';
      }
      buffer.writeln('$role: $content');
    }

    return buffer.toString();
  }

  String _buildSummarizationPrompt(String text) {
    return '''[SYSTEM: This is an internal summarization request. Provide a concise summary of the conversation below for context management. Focus on key topics, decisions, and relevant information. Keep it under 500 words.]

$text

Please summarize the conversation above, preserving important context for future reference.''';
  }

  /// Load a conversation and sync to Python session.
  Future<void> loadConversation(int conversationId) async {
    if (_isar == null) return;

    final conversation =
        await _isar!.conversations.get(conversationId);
    if (conversation == null) return;

    // Get recent messages (after summary cutoff if exists)
    List<Message> messages;
    if (conversation.summarizedUpToId != null) {
      messages = await _isar!.messages
          .filter()
          .conversationIdEqualTo(conversationId)
          .idGreaterThan(conversation.summarizedUpToId!)
          .sortByCreatedAt()
          .findAll();
    } else {
      messages = await _isar!.messages
          .filter()
          .conversationIdEqualTo(conversationId)
          .sortByCreatedAt()
          .findAll();
    }

    // Send full sync when Python is ready. ChatScreen retries this on the
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
  }

  /// Start a new conversation and sync to Python.
  Future<Conversation> createConversation({String? title}) async {
    if (_isar == null) {
      throw StateError('ConversationManager not initialized');
    }

    final conversation = Conversation.create(
      uuid: DateTime.now().millisecondsSinceEpoch.toString(),
      title: title ?? 'New Conversation',
    );

    await _isar!.writeTxn(() async {
      await _isar!.conversations.put(conversation);
    });

    // Notify Python when ready. ChatScreen also re-syncs the selected
    // conversation on Python ready after cold start/restart.
    if (_bridge.status == PythonStatus.ready) {
      await _bridge.applyDelta({
        'action': 'new_conversation',
        'conversation_id': conversation.id,
      });
    }

    return conversation;
  }

  /// Add a message and check for summarization.
  Future<Message> addMessage({
    required int conversationId,
    required String role,
    required String content,
    List<Map<String, dynamic>>? attachments,
    List<Map<String, dynamic>>? toolCalls,
  }) async {
    if (_isar == null) {
      throw StateError('ConversationManager not initialized');
    }

    final messageRole = _parseRole(role);

    final message = Message()
      ..conversationId = conversationId
      ..role = messageRole
      ..content = content
      ..createdAt = DateTime.now()
      ..tokenCount = _estimateTokens(content)
      ..attachments = _buildAttachments(attachments);

    await _isar!.writeTxn(() async {
      await _isar!.messages.put(message);

      // Update conversation timestamp
      final conversation =
          await _isar!.conversations.get(conversationId);
      if (conversation != null) {
        conversation.updatedAt = DateTime.now();
        await _isar!.conversations.put(conversation);
      }
    });

    // Send delta to Python
    await _bridge.applyDelta({
      'action': 'add_message',
      'message': {
        'id': message.id,
        'role': role,
        'content': content,
        'token_count': message.tokenCount,
        if (attachments != null) 'attachments': attachments,
      },
    });

    // Check if summarization needed (async, don't wait)
    checkAndSummarize(conversationId);

    return message;
  }

  List<Attachment> _buildAttachments(List<Map<String, dynamic>>? attachmentMaps) {
    if (attachmentMaps == null || attachmentMaps.isEmpty) return [];
    return attachmentMaps.map((a) {
      final localPath = a['local_path'] as String? ?? '';
      final originalName = a['original_name'] as String? ?? p.basename(localPath);
      return Attachment()
        ..localPath = localPath
        ..originalName = originalName
        ..mimeType = a['mime_type'] as String? ?? ''
        ..sizeBytes = a['size_bytes'] as int? ?? 0
        ..type = _detectAttachmentType(originalName);
    }).toList();
  }

  AttachmentType _detectAttachmentType(String filename) {
    final ext = p.extension(filename).toLowerCase();
    if ({'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}.contains(ext)) {
      return AttachmentType.image;
    }
    if ({'.mp4', '.mov', '.avi', '.webm', '.mkv'}.contains(ext)) {
      return AttachmentType.video;
    }
    if ({'.mp3', '.wav', '.aac', '.ogg', '.m4a', '.flac'}.contains(ext)) {
      return AttachmentType.audio;
    }
    if (ext == '.pdf') return AttachmentType.pdf;
    return AttachmentType.file;
  }

  int _estimateTokens(String text) {
    // Rough estimate: ~4 characters per token
    return (text.length / 4).ceil();
  }

  MessageRole _parseRole(String role) {
    switch (role.toLowerCase()) {
      case 'user':
        return MessageRole.user;
      case 'assistant':
        return MessageRole.assistant;
      case 'system':
        return MessageRole.system;
      case 'tool_result':
        return MessageRole.toolResult;
      default:
        return MessageRole.user;
    }
  }
}
