import 'package:flutter/material.dart';

import '../../core/services/storage_service.dart';

/// User-controlled provider tuning. Local models only see the search query.
class SearchProviderSettingsScreen extends StatefulWidget {
  final String provider;
  final String providerLabel;

  const SearchProviderSettingsScreen({
    super.key,
    required this.provider,
    required this.providerLabel,
  });

  @override
  State<SearchProviderSettingsScreen> createState() =>
      _SearchProviderSettingsScreenState();
}

class _SearchProviderSettingsScreenState
    extends State<SearchProviderSettingsScreen> {
  Map<String, dynamic> _settings = <String, dynamic>{};
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final settings = await StorageService.instance
        .getSearchProviderSettings(widget.provider);
    if (!mounted) return;
    setState(() {
      _settings = Map<String, dynamic>.from(settings);
      _loading = false;
    });
  }

  int _intValue(String key, int fallback) {
    final value = _settings[key];
    if (value is int) return value;
    return int.tryParse(value?.toString() ?? '') ?? fallback;
  }

  List<String> _stringList(String key) {
    final value = _settings[key];
    if (value is List) {
      return value.map((e) => e.toString()).where((e) => e.isNotEmpty).toList();
    }
    if (value is String && value.trim().isNotEmpty) {
      return value.split(',').map((e) => e.trim()).where((e) => e.isNotEmpty).toList();
    }
    return <String>[];
  }

  Widget _numberField(String key, String label, int fallback) {
    return Semantics(
      textField: true,
      label: label,
      child: TextFormField(
        initialValue: _intValue(key, fallback).toString(),
        keyboardType: TextInputType.number,
        decoration: InputDecoration(labelText: label, helperText: '允许 1 到 10'),
        onChanged: (value) {
          final parsed = int.tryParse(value);
          if (parsed != null) _settings[key] = parsed.clamp(1, 10);
        },
      ),
    );
  }

  Widget _textField(String key, String label, {String? helper}) {
    return Semantics(
      textField: true,
      label: label,
      child: TextFormField(
        initialValue: _settings[key]?.toString() ?? '',
        decoration: InputDecoration(labelText: label, helperText: helper),
        onChanged: (value) => _settings[key] = value.trim(),
      ),
    );
  }

  Widget _domainsField(String key, String label) {
    return Semantics(
      textField: true,
      label: label,
      child: TextFormField(
        initialValue: _stringList(key).join(', '),
        decoration: InputDecoration(
          labelText: label,
          helperText: '多个域名用英文逗号分隔；留空表示不限制',
        ),
        onChanged: (value) {
          _settings[key] = value
              .split(',')
              .map((e) => e.trim())
              .where((e) => e.isNotEmpty)
              .take(10)
              .toList();
        },
      ),
    );
  }

  Widget _choiceField(
    String key,
    String label,
    List<String> values,
    String fallback,
  ) {
    final current = values.contains(_settings[key]) ? _settings[key] as String : fallback;
    return Semantics(
      label: '$label，当前 $current',
      child: DropdownButtonFormField<String>(
        value: current,
        decoration: InputDecoration(labelText: label),
        items: values
            .map((value) => DropdownMenuItem(value: value, child: Text(value.isEmpty ? '不限制' : value)))
            .toList(),
        onChanged: (value) {
          if (value != null) setState(() => _settings[key] = value);
        },
      ),
    );
  }

  Widget _toggle(String key, String label, bool fallback) {
    final value = _settings[key] is bool ? _settings[key] as bool : fallback;
    return Semantics(
      toggled: value,
      label: label,
      child: SwitchListTile(
        contentPadding: EdgeInsets.zero,
        title: Text(label),
        value: value,
        onChanged: (next) => setState(() => _settings[key] = next),
      ),
    );
  }

  List<Widget> _providerControls() {
    switch (widget.provider) {
      case 'anysearch':
        return [
          _numberField('max_results', '返回结果数量', 5),
          const SizedBox(height: 12),
          _textField('domain', '限定主域名', helper: '可选，例如 example.com'),
          const SizedBox(height: 12),
          _textField('sub_domain', '限定子域', helper: '可选；仅在主域名存在时使用'),
        ];
      case 'exa':
        return [
          _numberField('num_results', '返回结果数量', 5),
          const SizedBox(height: 12),
          _choiceField('topic', '搜索主题', const ['general', 'news'], 'general'),
          const SizedBox(height: 12),
          _choiceField(
            'search_type',
            '搜索类型',
            const ['auto', 'neural', 'fast', 'deep'],
            'auto',
          ),
          const SizedBox(height: 12),
          _textField(
            'start_published_date',
            '最早发布日期',
            helper: '可选，例如 2026-01-01；留空表示不限制',
          ),
          const SizedBox(height: 12),
          _domainsField('include_domains', '只包含这些域名'),
          const SizedBox(height: 12),
          _domainsField('exclude_domains', '排除这些域名'),
          _toggle('include_text', '返回网页正文', true),
          _toggle('include_summary', '返回摘要', true),
          _toggle('include_highlights', '返回高亮片段', false),
        ];
      case 'langsearch':
        return [
          _numberField('count', '返回结果数量', 5),
          const SizedBox(height: 12),
          _choiceField(
            'freshness',
            '时间新鲜度',
            const ['noLimit', 'oneDay', 'oneWeek', 'oneMonth', 'oneYear'],
            'noLimit',
          ),
          _toggle('summary', '返回摘要', true),
        ];
      case 'tavily':
        return [
          _numberField('max_results', '返回结果数量', 5),
          const SizedBox(height: 12),
          _choiceField('topic', '搜索主题', const ['general', 'news'], 'general'),
          const SizedBox(height: 12),
          _choiceField(
            'search_depth',
            '搜索深度',
            const ['basic', 'advanced'],
            'basic',
          ),
          const SizedBox(height: 12),
          _choiceField(
            'time_range',
            '时间范围',
            const ['', 'day', 'week', 'month', 'year'],
            '',
          ),
          const SizedBox(height: 12),
          _domainsField('include_domains', '只包含这些域名'),
          const SizedBox(height: 12),
          _domainsField('exclude_domains', '排除这些域名'),
          _toggle('include_answer', '返回搜索答案摘要', true),
          _toggle('include_raw_content', '返回网页原始正文', false),
        ];
      default:
        return [const Text('当前搜索提供商没有可配置参数。')];
    }
  }

  Future<void> _save() async {
    await StorageService.instance
        .setSearchProviderSettings(widget.provider, _settings);
    if (!mounted) return;
    Navigator.pop(context, true);
  }

  Future<void> _reset() async {
    final defaults = StorageService.instance
        .defaultSearchProviderSettings(widget.provider);
    setState(() => _settings = defaults);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('${widget.providerLabel} 搜索设置'),
        actions: [
          TextButton(onPressed: _loading ? null : _save, child: const Text('保存')),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                const Text(
                  '这些参数由您预先配置。调用搜索时，本地模型只需要提供搜索关键词，应用会在执行层自动合并这里的设置。',
                ),
                const SizedBox(height: 20),
                ..._providerControls(),
                const SizedBox(height: 24),
                OutlinedButton(
                  onPressed: _reset,
                  child: const Text('恢复该提供商默认搜索设置'),
                ),
                const SizedBox(height: 24),
              ],
            ),
    );
  }
}
