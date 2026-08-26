import 'dart:convert';
import 'dart:io';

import '../models/tool_skill.dart';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:path_provider/path_provider.dart';

/// Secure storage service for sensitive data
class StorageService {
  static final StorageService instance = StorageService._();

  StorageService._();

  final _storage = const FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
  );

  // Keys
  static const _keyApiKey = 'claude_api_key';
  static const _keyGoogleRefreshToken = 'google_refresh_token';
  static const _keyDailyLimit = 'daily_cost_limit';
  static const _keyMonthlyLimit = 'monthly_cost_limit';
  static const _keyLimitEnabled = 'cost_limit_enabled';
  static const _keyPreferredModel = 'preferred_model';
  static const _keyDailyTokenLimit = 'daily_token_limit';
  static const _keyMonthlyTokenLimit = 'monthly_token_limit';
  static const _keyToolTimeout = 'tool_timeout_seconds';
  static const _keyMaxIterations = 'max_agent_iterations';
  static const _keyMaxToolCalls = 'max_tool_calls';
  static const _keyMaxTokens = 'max_response_tokens';
  static const _keyLegalAccepted = 'legal_accepted';
  static const _keySelfImproveEnabled = 'self_improve_enabled';
  static const _keyOfflineModelStates = 'offline_model_states';
  // RASTACODER_V5_SKILLS_PARAMS_BENCH_STREAM
  static const _keyLocalEnabledSkills = 'local_enabled_skills';
  static const _keyLocalTemperature = 'local_temperature';
  static const _keyLocalTopP = 'local_top_p';
  static const _keyLocalContextTokens = 'local_context_tokens';
  static const _keyLocalMaxOutputTokens = 'local_max_output_tokens';
  static const _keyLocalThinkingMode = 'local_thinking_mode';
  static const _keyLocalBenchmarkHistory = 'local_benchmark_history';
  // RASTACODER_V8_SEARCH_KEYS
  static const _searchApiProviders = <String>{'anysearch', 'exa', 'langsearch', 'tavily'};

  /// Store Claude API key securely
  Future<void> setApiKey(String key) async {
    await _storage.write(key: _keyApiKey, value: key);
  }

  /// Get stored API key
  Future<String?> getApiKey() async {
    return await _storage.read(key: _keyApiKey);
  }

  /// Check if API key is stored
  Future<bool> hasApiKey() async {
    return await _storage.containsKey(key: _keyApiKey);
  }

  /// Delete API key
  Future<void> deleteApiKey() async {
    await _storage.delete(key: _keyApiKey);
  }

  // RASTACODER_V8_SEARCH_KEYS
  String _searchApiStorageKey(String provider) {
    final normalized = provider.trim().toLowerCase();
    if (!_searchApiProviders.contains(normalized)) {
      throw ArgumentError('Unsupported search provider: $provider');
    }
    return 'search_api_key_$normalized';
  }

  Future<void> setSearchApiKey(String provider, String key) async {
    final value = key.trim();
    if (value.isEmpty) {
      await deleteSearchApiKey(provider);
      return;
    }
    await _storage.write(key: _searchApiStorageKey(provider), value: value);
  }

  Future<String?> getSearchApiKey(String provider) async {
    final value = await _storage.read(key: _searchApiStorageKey(provider));
    return value == null || value.trim().isEmpty ? null : value.trim();
  }

  Future<bool> hasSearchApiKey(String provider) async =>
      (await getSearchApiKey(provider)) != null;

  Future<void> deleteSearchApiKey(String provider) async {
    await _storage.delete(key: _searchApiStorageKey(provider));
  }

  Future<Map<String, String>> getConfiguredSearchApiKeys() async {
    final result = <String, String>{};
    for (final provider in _searchApiProviders) {
      final value = await getSearchApiKey(provider);
      if (value != null) result[provider] = value;
    }
    return result;
  }

  /// Store Google refresh token (if needed for manual refresh)
  Future<void> setGoogleRefreshToken(String token) async {
    await _storage.write(key: _keyGoogleRefreshToken, value: token);
  }

  /// Get Google refresh token
  Future<String?> getGoogleRefreshToken() async {
    return await _storage.read(key: _keyGoogleRefreshToken);
  }

  /// Delete Google refresh token
  Future<void> deleteGoogleRefreshToken() async {
    await _storage.delete(key: _keyGoogleRefreshToken);
  }

  /// Clear all secure storage
  Future<void> clearAll() async {
    await _storage.deleteAll();
  }

  // Cost limit methods

  /// Set daily cost limit
  Future<void> setDailyLimit(double limit) async {
    await _storage.write(key: _keyDailyLimit, value: limit.toString());
  }

  /// Get daily cost limit (default: 0.50)
  Future<double> getDailyLimit() async {
    final value = await _storage.read(key: _keyDailyLimit);
    return value != null ? double.tryParse(value) ?? 0.50 : 0.50;
  }

  /// Set monthly cost limit
  Future<void> setMonthlyLimit(double limit) async {
    await _storage.write(key: _keyMonthlyLimit, value: limit.toString());
  }

  /// Get monthly cost limit (default: 10.00)
  Future<double> getMonthlyLimit() async {
    final value = await _storage.read(key: _keyMonthlyLimit);
    return value != null ? double.tryParse(value) ?? 10.00 : 10.00;
  }

  /// Enable/disable cost limits
  Future<void> setCostLimitEnabled(bool enabled) async {
    await _storage.write(key: _keyLimitEnabled, value: enabled.toString());
  }

  /// Check if cost limits are enabled (default: true)
  Future<bool> isCostLimitEnabled() async {
    final value = await _storage.read(key: _keyLimitEnabled);
    return value != 'false';
  }

  // Model preference methods

  /// Set preferred model ('auto', 'sonnet', 'haiku')
  Future<void> setPreferredModel(String model) async {
    await _storage.write(key: _keyPreferredModel, value: model);
  }

  /// Get preferred model. Fresh installs default to the on-device Qwen3 4B;
  /// an explicit cloud selection such as 'auto' is still persisted verbatim.
  Future<String> getPreferredModel() async {
    final value = await _storage.read(key: _keyPreferredModel);
    return value ?? 'qwen3-4b';
  }

  // Token limit methods

  /// Set daily token limit (input + output combined)
  Future<void> setDailyTokenLimit(int tokens) async {
    await _storage.write(key: _keyDailyTokenLimit, value: tokens.toString());
  }

  /// Get daily token limit (default: 100,000 tokens)
  Future<int> getDailyTokenLimit() async {
    final value = await _storage.read(key: _keyDailyTokenLimit);
    return value != null ? int.tryParse(value) ?? 100000 : 100000;
  }

  /// Set monthly token limit
  Future<void> setMonthlyTokenLimit(int tokens) async {
    await _storage.write(key: _keyMonthlyTokenLimit, value: tokens.toString());
  }

  /// Get monthly token limit (default: 1,000,000 tokens)
  Future<int> getMonthlyTokenLimit() async {
    final value = await _storage.read(key: _keyMonthlyTokenLimit);
    return value != null ? int.tryParse(value) ?? 1000000 : 1000000;
  }

  // Tool timeout methods

  /// Set tool timeout in seconds
  Future<void> setToolTimeout(int seconds) async {
    await _storage.write(key: _keyToolTimeout, value: seconds.toString());
  }

  /// Get tool timeout in seconds (default: 30)
  Future<int> getToolTimeout() async {
    final value = await _storage.read(key: _keyToolTimeout);
    return value != null ? int.tryParse(value) ?? 30 : 30;
  }

  // Agent loop limits

  /// Set max agent iterations per query
  Future<void> setMaxIterations(int iterations) async {
    await _storage.write(key: _keyMaxIterations, value: iterations.toString());
  }

  /// Get max agent iterations (default: 50)
  Future<int> getMaxIterations() async {
    final value = await _storage.read(key: _keyMaxIterations);
    return value != null ? int.tryParse(value) ?? 50 : 50;
  }

  /// Set max tool calls per query
  Future<void> setMaxToolCalls(int calls) async {
    await _storage.write(key: _keyMaxToolCalls, value: calls.toString());
  }

  /// Get max tool calls per query (default: 50)
  Future<int> getMaxToolCalls() async {
    final value = await _storage.read(key: _keyMaxToolCalls);
    return value != null ? int.tryParse(value) ?? 50 : 50;
  }

  /// Set max response tokens per API call
  Future<void> setMaxTokens(int tokens) async {
    await _storage.write(key: _keyMaxTokens, value: tokens.toString());
  }

  /// Get max response tokens per API call (default: 16384)
  Future<int> getMaxTokens() async {
    final value = await _storage.read(key: _keyMaxTokens);
    return value != null ? int.tryParse(value) ?? 16384 : 16384;
  }

  // Legal acceptance methods

  /// Set legal terms accepted
  Future<void> setLegalAccepted(bool accepted) async {
    await _storage.write(key: _keyLegalAccepted, value: accepted.toString());
  }

  /// Check if legal terms have been accepted
  Future<bool> isLegalAccepted() async {
    final value = await _storage.read(key: _keyLegalAccepted);
    return value == 'true';
  }

  // Self-improve methods

  /// Enable/disable self-improve button below assistant messages
  Future<void> setSelfImproveEnabled(bool enabled) async {
    await _storage.write(key: _keySelfImproveEnabled, value: enabled.toString());
  }

  /// Check if self-improve is enabled (default: false)
  Future<bool> isSelfImproveEnabled() async {
    final value = await _storage.read(key: _keySelfImproveEnabled);
    return value == 'true';
  }

  // Offline model state persistence

  /// Store offline model states as JSON string.
  Future<void> setOfflineModelStates(String jsonString) async {
    await _storage.write(key: _keyOfflineModelStates, value: jsonString);
  }

  /// Get stored offline model states JSON, or null if not set.
  Future<String?> getOfflineModelStates() async {
    return await _storage.read(key: _keyOfflineModelStates);
  }


  // RASTACODER_V5_SKILLS_PARAMS_BENCH_STREAM
  // On-device agent skills and model parameters.

  Future<void> setLocalEnabledSkills(Set<String> skillIds) async {
    final known = LocalToolSkillCatalog.allIds;
    final clean = skillIds.where(known.contains).toList()..sort();
    await _storage.write(key: _keyLocalEnabledSkills, value: jsonEncode(clean));
  }

  Future<Set<String>> getLocalEnabledSkills() async {
    final raw = await _storage.read(key: _keyLocalEnabledSkills);
    if (raw == null || raw.isEmpty) return Set<String>.from(LocalToolSkillCatalog.allIds);
    try {
      final decoded = jsonDecode(raw);
      if (decoded is List) {
        final known = LocalToolSkillCatalog.allIds;
        return decoded.map((e) => e.toString()).where(known.contains).toSet();
      }
    } catch (_) {}
    return Set<String>.from(LocalToolSkillCatalog.allIds);
  }

  Future<void> setLocalTemperature(double value) async =>
      _storage.write(key: _keyLocalTemperature, value: value.toString());

  Future<double> getLocalTemperature() async {
    final raw = await _storage.read(key: _keyLocalTemperature);
    final value = double.tryParse(raw ?? '');
    return value != null && value >= 0 && value <= 2 ? value : 0.7;
  }

  Future<void> setLocalTopP(double value) async =>
      _storage.write(key: _keyLocalTopP, value: value.toString());

  Future<double> getLocalTopP() async {
    final raw = await _storage.read(key: _keyLocalTopP);
    final value = double.tryParse(raw ?? '');
    return value != null && value > 0 && value <= 1 ? value : 0.95;
  }

  Future<void> setLocalContextTokens(int value) async =>
      _storage.write(key: _keyLocalContextTokens, value: value.toString());

  Future<int> getLocalContextTokens() async {
    final raw = await _storage.read(key: _keyLocalContextTokens);
    final value = int.tryParse(raw ?? '');
    return value != null && value >= 512 && value <= 32768 ? value : 32768;
  }

  Future<void> setLocalMaxOutputTokens(int value) async =>
      _storage.write(key: _keyLocalMaxOutputTokens, value: value.toString());

  Future<int> getLocalMaxOutputTokens() async {
    final raw = await _storage.read(key: _keyLocalMaxOutputTokens);
    final value = int.tryParse(raw ?? '');
    return value != null && value >= 1 && value <= 8192 ? value : 2048;
  }

  Future<void> setLocalThinkingMode(String value) async {
    const allowed = {'model_default', 'enabled', 'disabled'};
    await _storage.write(
      key: _keyLocalThinkingMode,
      value: allowed.contains(value) ? value : 'model_default',
    );
  }

  Future<String> getLocalThinkingMode() async {
    final raw = await _storage.read(key: _keyLocalThinkingMode);
    const allowed = {'model_default', 'enabled', 'disabled'};
    return raw != null && allowed.contains(raw) ? raw : 'model_default';
  }

  Future<List<Map<String, dynamic>>> getLocalBenchmarkHistory() async {
    final raw = await _storage.read(key: _keyLocalBenchmarkHistory);
    if (raw == null || raw.isEmpty) return <Map<String, dynamic>>[];
    try {
      final decoded = jsonDecode(raw);
      if (decoded is List) {
        return decoded
            .whereType<Map>()
            .map((item) => Map<String, dynamic>.from(item))
            .toList();
      }
    } catch (_) {}
    return <Map<String, dynamic>>[];
  }

  Future<void> appendLocalBenchmarkResult(Map<String, dynamic> result) async {
    final history = await getLocalBenchmarkHistory();
    history.insert(0, Map<String, dynamic>.from(result));
    if (history.length > 20) history.removeRange(20, history.length);
    await _storage.write(key: _keyLocalBenchmarkHistory, value: jsonEncode(history));
  }

  // System prompt methods (file-based — prompts can be large)

  /// Get the system prompt file path.
  Future<File> getSystemPromptFile() async {
    final dir = await getApplicationDocumentsDirectory();
    return File('${dir.path}/system_prompt.txt');
  }

  /// Read the custom system prompt, or null if not customized.
  Future<String?> getSystemPrompt() async {
    final file = await getSystemPromptFile();
    if (await file.exists()) {
      final content = await file.readAsString();
      return content.isNotEmpty ? content : null;
    }
    return null;
  }

  /// Save a custom system prompt.
  Future<void> setSystemPrompt(String prompt) async {
    final file = await getSystemPromptFile();
    await file.writeAsString(prompt);
  }

  /// Delete the custom system prompt (reverts to default).
  Future<void> resetSystemPrompt() async {
    final file = await getSystemPromptFile();
    if (await file.exists()) {
      await file.delete();
    }
  }
}
