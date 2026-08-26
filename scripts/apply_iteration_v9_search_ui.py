#!/usr/bin/env python3
from pathlib import Path


def patch(path: str, old: str, new: str, count: int = 1) -> None:
    p = Path(path)
    text = p.read_text(encoding='utf-8')
    actual = text.count(old)
    if actual != count:
        raise SystemExit(f'{path}: expected {count} occurrence(s), found {actual}: {old[:120]!r}')
    p.write_text(text.replace(old, new, count), encoding='utf-8')


# ---------------------------------------------------------------------------
# Secure/private provider settings storage. These are configuration, not
# secrets, but using the existing encrypted storage keeps them scoped to app.
# ---------------------------------------------------------------------------
patch(
    'lib/core/services/storage_service.dart',
    "  Future<Map<String, String>> getConfiguredSearchApiKeys() async {\n"
    "    final result = <String, String>{};\n"
    "    for (final provider in _searchApiProviders) {\n"
    "      final value = await getSearchApiKey(provider);\n"
    "      if (value != null) result[provider] = value;\n"
    "    }\n"
    "    return result;\n"
    "  }\n",
    "  Future<Map<String, String>> getConfiguredSearchApiKeys() async {\n"
    "    final result = <String, String>{};\n"
    "    for (final provider in _searchApiProviders) {\n"
    "      final value = await getSearchApiKey(provider);\n"
    "      if (value != null) result[provider] = value;\n"
    "    }\n"
    "    return result;\n"
    "  }\n\n"
    "  // RASTACODER_V9_SEARCH_SETTINGS\n"
    "  String _searchSettingsStorageKey(String provider) {\n"
    "    final normalized = provider.trim().toLowerCase();\n"
    "    if (!_searchApiProviders.contains(normalized)) {\n"
    "      throw ArgumentError('Unsupported search provider: $provider');\n"
    "    }\n"
    "    return 'search_settings_$normalized';\n"
    "  }\n\n"
    "  Future<void> setSearchProviderSettings(\n"
    "    String provider, Map<String, dynamic> settings,\n"
    "  ) async {\n"
    "    await _storage.write(\n"
    "      key: _searchSettingsStorageKey(provider),\n"
    "      value: jsonEncode(settings),\n"
    "    );\n"
    "  }\n\n"
    "  Future<Map<String, dynamic>> getSearchProviderSettings(String provider) async {\n"
    "    final raw = await _storage.read(key: _searchSettingsStorageKey(provider));\n"
    "    if (raw == null || raw.trim().isEmpty) return <String, dynamic>{};\n"
    "    try {\n"
    "      final decoded = jsonDecode(raw);\n"
    "      if (decoded is Map) return Map<String, dynamic>.from(decoded);\n"
    "    } catch (_) {}\n"
    "    return <String, dynamic>{};\n"
    "  }\n\n"
    "  Future<Map<String, Map<String, dynamic>>> getConfiguredSearchProviderSettings() async {\n"
    "    final result = <String, Map<String, dynamic>>{};\n"
    "    for (final provider in _searchApiProviders) {\n"
    "      final value = await getSearchProviderSettings(provider);\n"
    "      if (value.isNotEmpty) result[provider] = value;\n"
    "    }\n"
    "    return result;\n"
    "  }\n",
)

# Bridge injects private provider settings alongside keys; neither is exposed in
# the local model's tool schema.
patch(
    'lib/core/bridge/bridge.dart',
    "    final searchApiKeys = await StorageService.instance.getConfiguredSearchApiKeys();\n",
    "    final searchApiKeys = await StorageService.instance.getConfiguredSearchApiKeys();\n"
    "    final searchSettings = await StorageService.instance.getConfiguredSearchProviderSettings();\n",
)
patch(
    'lib/core/bridge/bridge.dart',
    "      if (searchApiKeys.isNotEmpty) 'search_api_keys': searchApiKeys,\n",
    "      if (searchApiKeys.isNotEmpty) 'search_api_keys': searchApiKeys,\n"
    "      if (searchSettings.isNotEmpty) 'search_settings': searchSettings,\n",
)

# ---------------------------------------------------------------------------
# Search settings UI. Keep one clear settings control per provider, with fields
# appropriate to that provider. API-key control remains separate.
# ---------------------------------------------------------------------------
p = Path('lib/features/settings/tool_skills_screen.dart')
text = p.read_text(encoding='utf-8')
anchor = "  Future<void> _configureSearchApiKey(String provider) async {\n"
if anchor not in text:
    raise SystemExit('tool_skills_screen.dart: API key config anchor missing')
helper = r'''  Future<void> _configureSearchSettings(String provider) async {
    final label = _searchProviderLabels[provider] ?? provider;
    final current = await StorageService.instance.getSearchProviderSettings(provider);
    if (!mounted) return;

    final resultCount = TextEditingController(
      text: (current[provider == 'exa' ? 'num_results' : provider == 'langsearch' ? 'count' : 'max_results'] ?? 5).toString(),
    );
    final topic = TextEditingController(text: (current['topic'] ?? 'general').toString());
    final type = TextEditingController(text: (current['search_type'] ?? 'auto').toString());
    final date = TextEditingController(text: (current['start_published_date'] ?? '').toString());
    final freshness = TextEditingController(text: (current['freshness'] ?? 'noLimit').toString());
    final depth = TextEditingController(text: (current['search_depth'] ?? 'basic').toString());
    final timeRange = TextEditingController(text: (current['time_range'] ?? '').toString());
    final includeDomains = TextEditingController(
      text: (current['include_domains'] is List)
          ? (current['include_domains'] as List).join(',')
          : (current['include_domains'] ?? '').toString(),
    );
    final excludeDomains = TextEditingController(
      text: (current['exclude_domains'] is List)
          ? (current['exclude_domains'] as List).join(',')
          : (current['exclude_domains'] ?? '').toString(),
    );
    final domain = TextEditingController(text: (current['domain'] ?? '').toString());
    final subDomain = TextEditingController(text: (current['sub_domain'] ?? '').toString());
    bool includeText = current['include_text'] is bool ? current['include_text'] as bool : true;
    bool includeSummary = current['include_summary'] is bool ? current['include_summary'] as bool : true;
    bool includeHighlights = current['include_highlights'] is bool ? current['include_highlights'] as bool : false;
    bool summary = current['summary'] is bool ? current['summary'] as bool : true;
    bool includeAnswer = current['include_answer'] is bool ? current['include_answer'] as bool : true;
    bool includeRawContent = current['include_raw_content'] is bool ? current['include_raw_content'] as bool : false;

    List<String> splitDomains(String value) => value
        .split(',')
        .map((e) => e.trim())
        .where((e) => e.isNotEmpty)
        .toList();

    Widget field(TextEditingController controller, String labelText, {TextInputType? keyboardType}) {
      return Padding(
        padding: const EdgeInsets.only(bottom: 10),
        child: TextField(
          controller: controller,
          keyboardType: keyboardType,
          decoration: InputDecoration(labelText: labelText),
        ),
      );
    }

    Map<String, dynamic>? saved;
    await showDialog<void>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setLocalState) => AlertDialog(
          title: Text('$label 搜索参数'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Text('这些参数由您预设。模型调用搜索时只需要提供搜索关键词。'),
                const SizedBox(height: 12),
                field(resultCount, '返回结果数量（1-10）', keyboardType: TextInputType.number),
                if (provider == 'anysearch') ...[
                  field(domain, '固定 Domain（可留空）'),
                  field(subDomain, '固定 Sub-domain（可留空）'),
                ],
                if (provider == 'exa') ...[
                  field(topic, 'Topic，例如 general / news'),
                  field(type, 'Search type，例如 auto / neural'),
                  field(date, '起始发布日期（可留空）'),
                  field(includeDomains, '包含域名，逗号分隔（可留空）'),
                  field(excludeDomains, '排除域名，逗号分隔（可留空）'),
                  SwitchListTile(
                    value: includeText,
                    title: const Text('返回正文'),
                    onChanged: (v) => setLocalState(() => includeText = v),
                  ),
                  SwitchListTile(
                    value: includeSummary,
                    title: const Text('返回摘要'),
                    onChanged: (v) => setLocalState(() => includeSummary = v),
                  ),
                  SwitchListTile(
                    value: includeHighlights,
                    title: const Text('返回高亮'),
                    onChanged: (v) => setLocalState(() => includeHighlights = v),
                  ),
                ],
                if (provider == 'langsearch') ...[
                  field(freshness, 'Freshness，例如 noLimit / oneDay / oneWeek'),
                  SwitchListTile(
                    value: summary,
                    title: const Text('返回摘要'),
                    onChanged: (v) => setLocalState(() => summary = v),
                  ),
                ],
                if (provider == 'tavily') ...[
                  field(topic, 'Topic，例如 general / news'),
                  field(depth, 'Search depth，例如 basic / advanced'),
                  field(timeRange, '时间范围（可留空）'),
                  field(includeDomains, '包含域名，逗号分隔（可留空）'),
                  field(excludeDomains, '排除域名，逗号分隔（可留空）'),
                  SwitchListTile(
                    value: includeAnswer,
                    title: const Text('返回答案摘要'),
                    onChanged: (v) => setLocalState(() => includeAnswer = v),
                  ),
                  SwitchListTile(
                    value: includeRawContent,
                    title: const Text('返回原始正文'),
                    onChanged: (v) => setLocalState(() => includeRawContent = v),
                  ),
                ],
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext),
              child: const Text('取消'),
            ),
            TextButton(
              onPressed: () {
                saved = <String, dynamic>{};
                Navigator.pop(dialogContext);
              },
              child: const Text('恢复默认'),
            ),
            FilledButton(
              onPressed: () {
                final parsed = int.tryParse(resultCount.text.trim()) ?? 5;
                final count = parsed.clamp(1, 10).toInt();
                if (provider == 'anysearch') {
                  saved = {
                    'max_results': count,
                    if (domain.text.trim().isNotEmpty) 'domain': domain.text.trim(),
                    if (subDomain.text.trim().isNotEmpty) 'sub_domain': subDomain.text.trim(),
                  };
                } else if (provider == 'exa') {
                  saved = {
                    'num_results': count,
                    'topic': topic.text.trim().isEmpty ? 'general' : topic.text.trim(),
                    'search_type': type.text.trim().isEmpty ? 'auto' : type.text.trim(),
                    if (date.text.trim().isNotEmpty) 'start_published_date': date.text.trim(),
                    if (splitDomains(includeDomains.text).isNotEmpty) 'include_domains': splitDomains(includeDomains.text),
                    if (splitDomains(excludeDomains.text).isNotEmpty) 'exclude_domains': splitDomains(excludeDomains.text),
                    'include_text': includeText,
                    'include_summary': includeSummary,
                    'include_highlights': includeHighlights,
                  };
                } else if (provider == 'langsearch') {
                  saved = {
                    'count': count,
                    'freshness': freshness.text.trim().isEmpty ? 'noLimit' : freshness.text.trim(),
                    'summary': summary,
                  };
                } else if (provider == 'tavily') {
                  saved = {
                    'max_results': count,
                    'topic': topic.text.trim().isEmpty ? 'general' : topic.text.trim(),
                    'search_depth': depth.text.trim().isEmpty ? 'basic' : depth.text.trim(),
                    'include_answer': includeAnswer,
                    if (timeRange.text.trim().isNotEmpty) 'time_range': timeRange.text.trim(),
                    if (splitDomains(includeDomains.text).isNotEmpty) 'include_domains': splitDomains(includeDomains.text),
                    if (splitDomains(excludeDomains.text).isNotEmpty) 'exclude_domains': splitDomains(excludeDomains.text),
                    'include_raw_content': includeRawContent,
                  };
                }
                Navigator.pop(dialogContext);
              },
              child: const Text('保存'),
            ),
          ],
        ),
      ),
    );

    for (final controller in [
      resultCount, topic, type, date, freshness, depth, timeRange,
      includeDomains, excludeDomains, domain, subDomain,
    ]) {
      controller.dispose();
    }
    if (saved == null) return;
    await StorageService.instance.setSearchProviderSettings(provider, saved!);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(saved!.isEmpty ? '$label 搜索参数已恢复默认' : '$label 搜索参数已保存')),
      );
    }
  }

'''
text = text.replace(anchor, helper + anchor, 1)
p.write_text(text, encoding='utf-8')

# Add separate search-settings button beside API-key control.
patch(
    'lib/features/settings/tool_skills_screen.dart',
    "        if (provider != null)\n"
    "          Padding(\n"
    "            padding: const EdgeInsets.only(left: 16, right: 16, bottom: 12),\n"
    "            child: Semantics(\n"
    "              button: true,\n"
    "              label: '$providerLabel API Key，${configured ? '已配置，双击更新或清除' : '未配置，双击配置'}',\n"
    "              child: OutlinedButton.icon(\n"
    "                onPressed: () => _configureSearchApiKey(provider),\n"
    "                icon: const Icon(Icons.key, size: 18),\n"
    "                label: Text(configured ? '$providerLabel API Key：已配置' : '配置 $providerLabel API Key'),\n"
    "              ),\n"
    "            ),\n"
    "          ),\n",
    "        if (provider != null)\n"
    "          Padding(\n"
    "            padding: const EdgeInsets.only(left: 16, right: 16, bottom: 12),\n"
    "            child: Column(\n"
    "              crossAxisAlignment: CrossAxisAlignment.stretch,\n"
    "              children: [\n"
    "                Semantics(\n"
    "                  button: true,\n"
    "                  label: '$providerLabel API Key，${configured ? '已配置，双击更新或清除' : '未配置，双击配置'}',\n"
    "                  child: OutlinedButton.icon(\n"
    "                    onPressed: () => _configureSearchApiKey(provider),\n"
    "                    icon: const Icon(Icons.key, size: 18),\n"
    "                    label: Text(configured ? '$providerLabel API Key：已配置' : '配置 $providerLabel API Key'),\n"
    "                  ),\n"
    "                ),\n"
    "                const SizedBox(height: 8),\n"
    "                Semantics(\n"
    "                  button: true,\n"
    "                  label: '$providerLabel 搜索参数，双击配置返回数量、类型和过滤条件',\n"
    "                  child: OutlinedButton.icon(\n"
    "                    onPressed: () => _configureSearchSettings(provider),\n"
    "                    icon: const Icon(Icons.tune, size: 18),\n"
    "                    label: Text('配置 $providerLabel 搜索参数'),\n"
    "                  ),\n"
    "                ),\n"
    "              ],\n"
    "            ),\n"
    "          ),\n",
)

print('Applied RastaCoder v9 private search settings UI')
