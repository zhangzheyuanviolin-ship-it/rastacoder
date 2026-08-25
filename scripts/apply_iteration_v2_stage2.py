#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_required(path: str, old: str, new: str) -> None:
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    if old not in text:
        raise SystemExit(f'Missing anchor in {path}: {old[:100]!r}')
    p.write_text(text.replace(old, new), encoding='utf-8')


# Rework Google auth so the OAuth web client can be replaced without rebuilding.
# The original upstream client remains only as a compatibility fallback.
auth = r'''import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:google_sign_in/google_sign_in.dart';

import 'analytics_service.dart';

/// Service for Google OAuth authentication.
///
/// RastaCoder keeps the OAuth client configurable because the upstream
/// NavixMind client is owned by the original developer and may restrict
/// sign-in to that project's test users. A user/developer can enter an
/// independent Web OAuth client ID in Settings without rebuilding the APK.
class AuthService {
  static final AuthService instance = AuthService._();

  AuthService._();

  static const _storage = FlutterSecureStorage();
  static const _clientIdKey = 'google_oauth_server_client_id';
  static const _upstreamClientId =
      '296863031657-69hn38bhprhqvrda6vd795sp65e8764d.apps.googleusercontent.com';

  static const _scopes = <String>[
    'email',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar.events',
  ];

  GoogleSignIn? _googleSignIn;
  GoogleSignInAccount? _currentUser;
  String? _customClientId;
  final _userController = StreamController<GoogleSignInAccount?>.broadcast();

  Stream<GoogleSignInAccount?> get userStream => _userController.stream;
  GoogleSignInAccount? get currentUser => _currentUser;
  bool get isSignedIn => _currentUser != null;
  bool get hasCustomOAuthClient =>
      _customClientId != null && _customClientId!.trim().isNotEmpty;
  String get activeOAuthClientId =>
      hasCustomOAuthClient ? _customClientId!.trim() : _upstreamClientId;

  GoogleSignIn _newGoogleSignIn() => GoogleSignIn(
        serverClientId: activeOAuthClientId,
        scopes: _scopes,
      );

  Future<void> initialize() async {
    _customClientId = await _storage.read(key: _clientIdKey);
    _googleSignIn = _newGoogleSignIn();
    _googleSignIn!.onCurrentUserChanged.listen((account) {
      _currentUser = account;
      _userController.add(account);
    });

    try {
      _currentUser = await _googleSignIn!.signInSilently();
      debugPrint(
          'Google silent sign-in: ${_currentUser != null ? "restored" : "no session"}');
    } catch (e) {
      debugPrint('Google silent sign-in failed: $e');
    }
  }

  Future<void> setOAuthClientId(String? clientId) async {
    final normalized = clientId?.trim();
    if (normalized == null || normalized.isEmpty) {
      await _storage.delete(key: _clientIdKey);
      _customClientId = null;
    } else {
      await _storage.write(key: _clientIdKey, value: normalized);
      _customClientId = normalized;
    }

    // A client switch requires a new GoogleSignIn instance and a fresh grant.
    try {
      await _googleSignIn?.signOut();
    } catch (_) {}
    _currentUser = null;
    _userController.add(null);
    _googleSignIn = _newGoogleSignIn();
    _googleSignIn!.onCurrentUserChanged.listen((account) {
      _currentUser = account;
      _userController.add(account);
    });
  }

  Future<GoogleSignInAccount?> signIn() async {
    await AnalyticsService.instance.googleSignInStarted();
    _googleSignIn ??= _newGoogleSignIn();
    try {
      _currentUser = await _googleSignIn!.signIn();
      if (_currentUser != null) {
        final granted = await _googleSignIn!.requestScopes([
          'https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/calendar.events',
        ]);
        if (!granted) {
          debugPrint('User declined additional Google scopes');
        }
      }
      await AnalyticsService.instance
          .googleSignInCompleted(success: _currentUser != null);
      return _currentUser;
    } catch (e) {
      await AnalyticsService.instance.googleSignInCompleted(success: false);
      rethrow;
    }
  }

  Future<void> signOut() async {
    await _googleSignIn?.signOut();
    _currentUser = null;
    _userController.add(null);
    await AnalyticsService.instance.googleSignOut();
  }

  Future<void> disconnect() async {
    try {
      await _googleSignIn?.disconnect();
    } catch (e) {
      debugPrint('Google disconnect error (ignored): $e');
    }
    _currentUser = null;
    _userController.add(null);
  }

  Future<String?> getValidAccessToken() async {
    if (_currentUser == null) return null;
    try {
      final auth = await _currentUser!.authentication;
      return auth.accessToken;
    } catch (e) {
      try {
        _currentUser = await _googleSignIn?.signInSilently();
        if (_currentUser == null) return null;
        final auth = await _currentUser!.authentication;
        return auth.accessToken;
      } catch (refreshError) {
        debugPrint('Token refresh failed: $refreshError');
        return null;
      }
    }
  }

  DateTime get tokenExpiry => DateTime.now().add(const Duration(minutes: 55));

  void dispose() {
    _userController.close();
  }
}
'''
(ROOT / 'lib/core/services/auth_service.dart').write_text(auth, encoding='utf-8')

# Show native tool dispatch immediately in the chat stream. The existing log
# stream continues to show Python/web/document tool progress and results.
chat_path = 'lib/features/chat/presentation/chat_screen.dart'
replace_required(
    chat_path,
    "  StreamSubscription<SharedFilesEvent>? _shareSubscription;",
    "  StreamSubscription<SharedFilesEvent>? _shareSubscription;\n  StreamSubscription? _nativeToolSubscription;\n  final Set<String> _announcedNativeToolIds = <String>{};"
)
replace_required(
    chat_path,
    "    _listenToLogs();\n    _listenToConnectivity();",
    "    _listenToLogs();\n    _listenToNativeTools();\n    _listenToConnectivity();"
)
insert_anchor = "  Future<void> _sendMessage() async {"
native_listener = r'''  void _listenToNativeTools() {
    _nativeToolSubscription = PythonBridge.instance.nativeToolStream.listen((request) {
      if (!mounted || !_isProcessing) return;
      if (!_announcedNativeToolIds.add(request.id)) return;

      setState(() {
        _messages.add(ChatMessage(
          role: MessageRole.system,
          content: '⚙️ 正在调用工具：${request.tool}',
          timestamp: DateTime.now(),
        ));
        _statusMessage = '正在调用工具：${request.tool}';
      });
      _scrollToBottom();
    });
  }

  String _localizeAgentLog(String msg) {
    if (msg.startsWith('Thinking:')) {
      return '思考：${msg.substring('Thinking:'.length).trim()}';
    }
    if (msg.startsWith('Tool:')) {
      return '准备调用工具：${msg.substring('Tool:'.length).trim()}';
    }
    if (msg.startsWith('Executing')) {
      return '正在执行${msg.substring('Executing'.length)}';
    }
    if (msg.startsWith('Result:')) {
      return '工具结果：${msg.substring('Result:'.length).trim()}';
    }
    if (msg.startsWith('Code:')) {
      return '执行代码：${msg.substring('Code:'.length).trim()}';
    }
    if (msg.startsWith('File:')) {
      return '文件：${msg.substring('File:'.length).trim()}';
    }
    if (msg == 'Preparing response...') return '正在整理最终回复…';
    return msg;
  }

'''
p = ROOT / chat_path
text = p.read_text(encoding='utf-8')
if insert_anchor not in text:
    raise SystemExit('native listener insert anchor missing')
p.write_text(text.replace(insert_anchor, native_listener + insert_anchor), encoding='utf-8')
replace_required(
    chat_path,
    "            content: '$icon $msg',",
    "            content: '$icon ${_localizeAgentLog(msg)}',"
)
replace_required(
    chat_path,
    "          _attachedFiles = [];\n          _externalFiles = [];",
    "          _attachedFiles = [];\n          _externalFiles = [];\n          _announcedNativeToolIds.clear();"
)
replace_required(
    chat_path,
    "    _shareSubscription?.cancel();\n    WidgetsBinding.instance.removeObserver(this);",
    "    _shareSubscription?.cancel();\n    _nativeToolSubscription?.cancel();\n    WidgetsBinding.instance.removeObserver(this);"
)

# Add a settings editor for an independent Google OAuth Web client ID.
settings_path = 'lib/features/settings/settings_screen.dart'
method_anchor = "  Future<void> _disconnectGoogle() async {"
method = r'''  Future<void> _setGoogleOAuthClientId() async {
    final controller = TextEditingController(
      text: AuthService.instance.hasCustomOAuthClient
          ? AuthService.instance.activeOAuthClientId
          : '',
    );
    final result = await showDialog<String?>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Google OAuth Client ID'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              '原作者的 OAuth Client 可能只允许其测试账号登录。这里可以填写您自己的 Google OAuth Web Client ID；留空则恢复上游默认值。',
            ),
            const SizedBox(height: 12),
            TextField(
              controller: controller,
              decoration: const InputDecoration(
                labelText: 'OAuth Web Client ID',
                hintText: 'xxxxxxxx.apps.googleusercontent.com',
              ),
              autocorrect: false,
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('取消'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, controller.text.trim()),
            child: const Text('保存'),
          ),
        ],
      ),
    );
    if (result == null) return;
    await AuthService.instance.setOAuthClientId(result);
    if (!mounted) return;
    setState(() => _isGoogleConnected = false);
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(result.isEmpty
            ? '已恢复上游 OAuth Client；需要重新连接 Google 账号'
            : '独立 OAuth Client ID 已保存；请重新连接 Google 账号'),
      ),
    );
  }

'''
p = ROOT / settings_path
text = p.read_text(encoding='utf-8')
if method_anchor not in text:
    raise SystemExit('settings method anchor missing')
text = text.replace(method_anchor, method + method_anchor)
tile_anchor = "          const SizedBox(height: 24),\n\n          // Usage Section"
tile = r'''          _SettingsTile(
            title: 'Google OAuth Client ID',
            subtitle: AuthService.instance.hasCustomOAuthClient
                ? '已配置独立 OAuth Client'
                : '当前使用上游 OAuth Client（可能受测试用户限制）',
            trailing: const Icon(Icons.key, size: 20),
            onTap: _setGoogleOAuthClientId,
          ),

          const SizedBox(height: 24),

          // Usage Section'''
if tile_anchor not in text:
    raise SystemExit('settings Google tile anchor missing')
text = text.replace(tile_anchor, tile)
p.write_text(text, encoding='utf-8')

print('Iteration v2 stage2 patches applied successfully.')
