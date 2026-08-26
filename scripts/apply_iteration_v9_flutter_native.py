#!/usr/bin/env python3
"""Apply v9 Flutter search-settings wiring and native FFmpeg speed support."""
from pathlib import Path


def patch(path: str, old: str, new: str, count: int = 1) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    actual = text.count(old)
    if actual != count:
        raise SystemExit(f"{path}: expected {count}, found {actual}: {old[:120]!r}")
    p.write_text(text.replace(old, new, count), encoding="utf-8")


# --- persistent per-provider search settings -------------------------------
patch(
    "lib/core/services/storage_service.dart",
    "  static const _searchApiProviders = <String>{'anysearch', 'exa', 'langsearch', 'tavily'};\n",
    '''  static const _searchApiProviders = <String>{'anysearch', 'exa', 'langsearch', 'tavily'};\n  // RASTACODER_V9_SEARCH_SETTINGS\n  static const Map<String, Map<String, dynamic>> _searchSettingsDefaults = {\n    'anysearch': {'max_results': 5, 'domain': '', 'sub_domain': ''},\n    'exa': {\n      'num_results': 5, 'topic': 'general', 'search_type': 'auto',\n      'start_published_date': '', 'include_domains': <String>[],\n      'exclude_domains': <String>[], 'include_text': true,\n      'include_summary': true, 'include_highlights': false,\n    },\n    'langsearch': {'count': 5, 'freshness': 'noLimit', 'summary': true},\n    'tavily': {\n      'max_results': 5, 'topic': 'general', 'search_depth': 'basic',\n      'include_answer': true, 'time_range': '',\n      'include_domains': <String>[], 'exclude_domains': <String>[],\n      'include_raw_content': false,\n    },\n  };\n''',
)
patch(
    "lib/core/services/storage_service.dart",
    '''  Future<Map<String, String>> getConfiguredSearchApiKeys() async {\n    final result = <String, String>{};\n    for (final provider in _searchApiProviders) {\n      final value = await getSearchApiKey(provider);\n      if (value != null) result[provider] = value;\n    }\n    return result;\n  }\n''',
    '''  Future<Map<String, String>> getConfiguredSearchApiKeys() async {\n    final result = <String, String>{};\n    for (final provider in _searchApiProviders) {\n      final value = await getSearchApiKey(provider);\n      if (value != null) result[provider] = value;\n    }\n    return result;\n  }\n\n  String _searchSettingsStorageKey(String provider) {\n    final normalized = provider.trim().toLowerCase();\n    if (!_searchApiProviders.contains(normalized)) {\n      throw ArgumentError('Unsupported search provider: $provider');\n    }\n    return 'search_provider_settings_$normalized';\n  }\n\n  Map<String, dynamic> defaultSearchProviderSettings(String provider) {\n    final normalized = provider.trim().toLowerCase();\n    final defaults = _searchSettingsDefaults[normalized];\n    if (defaults == null) {\n      throw ArgumentError('Unsupported search provider: $provider');\n    }\n    return Map<String, dynamic>.from(defaults.map((key, value) =>\n        MapEntry(key, value is List ? List<dynamic>.from(value) : value)));\n  }\n\n  Future<Map<String, dynamic>> getSearchProviderSettings(String provider) async {\n    final defaults = defaultSearchProviderSettings(provider);\n    final raw = await _storage.read(key: _searchSettingsStorageKey(provider));\n    if (raw == null || raw.isEmpty) return defaults;\n    try {\n      final decoded = jsonDecode(raw);\n      if (decoded is Map) {\n        for (final entry in decoded.entries) {\n          defaults[entry.key.toString()] = entry.value;\n        }\n      }\n    } catch (_) {}\n    return defaults;\n  }\n\n  Future<void> setSearchProviderSettings(\n    String provider,\n    Map<String, dynamic> settings,\n  ) async {\n    final merged = defaultSearchProviderSettings(provider)..addAll(settings);\n    await _storage.write(\n      key: _searchSettingsStorageKey(provider),\n      value: jsonEncode(merged),\n    );\n  }\n\n  Future<Map<String, Map<String, dynamic>>> getAllSearchProviderSettings() async {\n    final result = <String, Map<String, dynamic>>{};\n    for (final provider in _searchApiProviders) {\n      result[provider] = await getSearchProviderSettings(provider);\n    }\n    return result;\n  }\n''',
)

# Bridge injects settings privately alongside credentials.
patch(
    "lib/core/bridge/bridge.dart",
    '''    final searchApiKeys = await StorageService.instance.getConfiguredSearchApiKeys();\n''',
    '''    final searchApiKeys = await StorageService.instance.getConfiguredSearchApiKeys();\n    final searchProviderSettings =\n        await StorageService.instance.getAllSearchProviderSettings();\n''',
)
patch(
    "lib/core/bridge/bridge.dart",
    '''      if (searchApiKeys.isNotEmpty) 'search_api_keys': searchApiKeys,\n''',
    '''      if (searchApiKeys.isNotEmpty) 'search_api_keys': searchApiKeys,\n      'search_provider_settings': searchProviderSettings,\n''',
)

# Tool manager exposes a dedicated settings button per search Skill.
patch(
    "lib/features/settings/tool_skills_screen.dart",
    "import '../../core/services/storage_service.dart';\n",
    "import '../../core/services/storage_service.dart';\nimport 'search_provider_settings_screen.dart';\n",
)
patch(
    "lib/features/settings/tool_skills_screen.dart",
    '''                label: Text(configured ? '$providerLabel API Key：已配置' : '配置 $providerLabel API Key'),\n              ),\n            ),\n          ),\n      ],\n''',
    '''                label: Text(configured ? '$providerLabel API Key：已配置' : '配置 $providerLabel API Key'),\n              ),\n            ),\n          ),\n        if (provider != null)\n          Padding(\n            padding: const EdgeInsets.only(left: 16, right: 16, bottom: 12),\n            child: Semantics(\n              button: true,\n              label: '$providerLabel 搜索设置，双击配置返回数量、搜索类型和过滤条件',\n              child: OutlinedButton.icon(\n                onPressed: () async {\n                  final saved = await Navigator.push<bool>(\n                    context,\n                    MaterialPageRoute(\n                      builder: (_) => SearchProviderSettingsScreen(\n                        provider: provider,\n                        providerLabel: providerLabel ?? provider,\n                      ),\n                    ),\n                  );\n                  if (saved == true && context.mounted) {\n                    ScaffoldMessenger.of(context).showSnackBar(\n                      SnackBar(content: Text('$providerLabel 搜索设置已保存')),\n                    );\n                  }\n                },\n                icon: const Icon(Icons.tune, size: 18),\n                label: Text('配置 $providerLabel 搜索设置'),\n              ),\n            ),\n          ),\n      ],\n''',
)

# Search Skill descriptions make the responsibility split explicit.
for old, new in {
    "description: '独立使用 AnySearch 搜索、网页抽取和子域能力；API Key 由用户手动配置。',": "description: '模型只提交搜索关键词；API Key、返回数量和域名参数由用户预先配置。',",
    "description: '独立使用 Exa 神经/自动搜索；API Key 由用户手动配置。',": "description: '模型只提交搜索关键词；API Key、结果数量、搜索类型和过滤条件由用户预先配置。',",
    "description: '独立使用 LangSearch 网络搜索；API Key 由用户手动配置。',": "description: '模型只提交搜索关键词；API Key、结果数量、新鲜度和摘要选项由用户预先配置。',",
    "description: '独立使用 Tavily 搜索；API Key 由用户手动配置。',": "description: '模型只提交搜索关键词；API Key、结果数量、主题、深度和过滤条件由用户预先配置。',",
}.items():
    patch("lib/core/models/tool_skill.dart", old, new)


# --- native FFmpeg: structured speed + physical/duration postconditions -----
patch(
    "lib/core/services/native_tool_executor.dart",
    "  /// Execute FFmpeg operation\n",
    '''  String _buildATempoChain(double factor) {\n    if (!factor.isFinite || factor <= 0 || factor > 16.0) {\n      throw ArgumentError('Speed factor must be greater than 0 and at most 16');\n    }\n    var remaining = factor;\n    final filters = <String>[];\n    while (remaining > 2.0) {\n      filters.add('atempo=2.0');\n      remaining /= 2.0;\n    }\n    while (remaining < 0.5) {\n      filters.add('atempo=0.5');\n      remaining /= 0.5;\n    }\n    final value = remaining\n        .toStringAsFixed(6)\n        .replaceFirst(RegExp(r'0+$'), '')\n        .replaceFirst(RegExp(r'\\.$'), '');\n    filters.add('atempo=$value');\n    return filters.join(',');\n  }\n\n  /// Execute FFmpeg operation\n''',
)
patch(
    "lib/core/services/native_tool_executor.dart",
    "      case 'crop':\n",
    '''      case 'speed':\n        final rawFactor = params['factor'] ?? params['speed'] ?? params['rate'];\n        final factor = rawFactor is num\n            ? rawFactor.toDouble()\n            : double.tryParse(rawFactor?.toString() ?? '');\n        if (factor == null || !factor.isFinite || factor <= 0 || factor > 16.0) {\n          throw ArgumentError('Speed requires params.factor > 0 and <= 16, for example 1.5');\n        }\n        final audioFilter = _buildATempoChain(factor);\n        const audioExts = <String>{'.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg', '.opus', '.wma', '.amr'};\n        final dot = inputPath.lastIndexOf('.');\n        final inputExt = dot >= 0 ? inputPath.substring(dot).toLowerCase() : '';\n        if (audioExts.contains(inputExt)) {\n          command = '-y -i "$inputPath" -filter:a "$audioFilter" "$outputPath"';\n        } else {\n          command = '-y -i "$inputPath" -filter:v "setpts=PTS/$factor" -filter:a "$audioFilter" -c:v libx264 -pix_fmt yuv420p -c:a aac "$outputPath"';\n        }\n        break;\n\n      case 'crop':\n''',
)
patch(
    "lib/core/services/native_tool_executor.dart",
    '''    // Execute FFmpeg command\n    debugPrint('[FFmpeg] Command: $command');\n''',
    '''    // Capture source duration for operations whose postcondition depends on it.\n    double? inputMediaDuration;\n    if (operation == 'speed') {\n      try {\n        final probeSession = await FFprobeKit.getMediaInformation(inputPath);\n        final durationStr = probeSession.getMediaInformation()?.getDuration();\n        if (durationStr != null) inputMediaDuration = double.tryParse(durationStr);\n      } catch (_) {}\n    }\n\n    // Execute FFmpeg command\n    debugPrint('[FFmpeg] Command: $command');\n''',
)
patch(
    "lib/core/services/native_tool_executor.dart",
    '''        files.sort();\n        return {\n''',
    '''        files.sort();\n        if (files.isEmpty || totalSize <= 0) {\n          throw Exception('FFmpeg reported success but generated no non-empty output files');\n        }\n        return {\n''',
)
patch(
    "lib/core/services/native_tool_executor.dart",
    '''      final outputFile = File(outputPath);\n      final outputSize = await outputFile.length();\n''',
    '''      final outputFile = File(outputPath);\n      if (!await outputFile.exists()) {\n        throw Exception('FFmpeg reported success but output file is missing');\n      }\n      final outputSize = await outputFile.length();\n      if (outputSize <= 0) {\n        throw Exception('FFmpeg reported success but output file is empty');\n      }\n''',
)
patch(
    "lib/core/services/native_tool_executor.dart",
    '''      final result = {\n        'success': true,\n''',
    '''      bool durationVerified = false;\n      double? verifiedSpeedFactor;\n      if (operation == 'speed' && inputMediaDuration != null && mediaDuration != null) {\n        final rawFactor = params['factor'] ?? params['speed'] ?? params['rate'];\n        final factor = rawFactor is num\n            ? rawFactor.toDouble()\n            : double.tryParse(rawFactor?.toString() ?? '');\n        if (factor != null && factor > 0) {\n          final expected = inputMediaDuration! / factor;\n          var tolerance = expected * 0.25;\n          if (tolerance < 1.5) tolerance = 1.5;\n          if ((mediaDuration - expected).abs() > tolerance) {\n            try { await outputFile.delete(); } catch (_) {}\n            throw Exception(\n                'Speed verification failed: expected about ${expected.toStringAsFixed(2)}s, got ${mediaDuration.toStringAsFixed(2)}s');\n          }\n          verifiedSpeedFactor = factor;\n          durationVerified = true;\n        }\n      }\n\n      final result = {\n        'success': true,\n''',
)
patch(
    "lib/core/services/native_tool_executor.dart",
    '''      if (mediaDuration != null) {\n        result['media_duration_seconds'] = mediaDuration;\n      }\n      return result;\n''',
    '''      if (mediaDuration != null) {\n        result['media_duration_seconds'] = mediaDuration;\n      }\n      if (verifiedSpeedFactor != null) {\n        result['speed_factor'] = verifiedSpeedFactor;\n        result['duration_verified'] = durationVerified;\n      }\n      return result;\n''',
)

print("Applied RastaCoder v9 Flutter/native hardening")
