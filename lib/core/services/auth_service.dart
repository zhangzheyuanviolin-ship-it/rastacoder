import 'dart:async';

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
