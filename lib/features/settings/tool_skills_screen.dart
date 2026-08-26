import 'package:flutter/material.dart';

import '../../app/theme.dart';
import '../../core/models/tool_skill.dart';
import '../../core/services/storage_service.dart';
import 'search_provider_settings_screen.dart';

// RASTACODER_V5_SKILLS_PARAMS_BENCH_STREAM
class ToolSkillsScreen extends StatefulWidget {
  final Set<String>? initialEnabled;
  final bool persistAsDefaults;

  const ToolSkillsScreen({
    super.key,
    this.initialEnabled,
    this.persistAsDefaults = false,
  });

  @override
  State<ToolSkillsScreen> createState() => _ToolSkillsScreenState();
}

class _ToolSkillsScreenState extends State<ToolSkillsScreen> {
  static const _searchProviderBySkill = <String, String>{
    'anysearch_search': 'anysearch',
    'exa_search': 'exa',
    'langsearch_search': 'langsearch',
    'tavily_search': 'tavily',
  };
  static const _searchProviderLabels = <String, String>{
    'anysearch': 'AnySearch',
    'exa': 'Exa',
    'langsearch': 'LangSearch',
    'tavily': 'Tavily',
  };

  Set<String> _enabled = <String>{};
  Set<String> _configuredSearchProviders = <String>{};
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final initial = widget.initialEnabled ??
        await StorageService.instance.getLocalEnabledSkills();
    final known = LocalToolSkillCatalog.allIds;
    final configured = <String>{};
    for (final provider in _searchProviderLabels.keys) {
      if (await StorageService.instance.hasSearchApiKey(provider)) {
        configured.add(provider);
      }
    }
    if (!mounted) return;
    setState(() {
      _enabled = initial.where(known.contains).toSet();
      _configuredSearchProviders = configured;
      _loading = false;
    });
  }

  Future<void> _configureSearchApiKey(String provider) async {
    final label = _searchProviderLabels[provider] ?? provider;
    final controller = TextEditingController();
    final configured = _configuredSearchProviders.contains(provider);
    final action = await showDialog<String>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text('$label API Key'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(configured
                ? '已配置。输入新密钥可以替换；现有密钥不会显示在屏幕上。'
                : '请输入 $label API Key。密钥将保存在 Android 安全存储中。'),
            const SizedBox(height: 12),
            Semantics(
              textField: true,
              label: '$label API Key 输入框',
              child: TextField(
                controller: controller,
                autofocus: true,
                obscureText: true,
                enableSuggestions: false,
                autocorrect: false,
                decoration: InputDecoration(
                  labelText: '$label API Key',
                  hintText: configured ? '输入新密钥以替换' : '输入 API Key',
                ),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, 'cancel'),
            child: const Text('取消'),
          ),
          if (configured)
            TextButton(
              onPressed: () => Navigator.pop(dialogContext, 'clear'),
              child: const Text('清除密钥'),
            ),
          FilledButton(
            onPressed: () => Navigator.pop(dialogContext, 'save'),
            child: const Text('保存'),
          ),
        ],
      ),
    );
    if (!mounted || action == null || action == 'cancel') {
      controller.dispose();
      return;
    }
    if (action == 'clear') {
      await StorageService.instance.deleteSearchApiKey(provider);
      if (mounted) {
        setState(() => _configuredSearchProviders.remove(provider));
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('$label API Key 已清除')),
        );
      }
      controller.dispose();
      return;
    }
    final value = controller.text.trim();
    controller.dispose();
    if (value.isEmpty) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('API Key 不能为空')),
        );
      }
      return;
    }
    await StorageService.instance.setSearchApiKey(provider, value);
    if (mounted) {
      setState(() => _configuredSearchProviders.add(provider));
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('$label API Key 已安全保存')),
      );
    }
  }

  Widget _buildSkillTile(BuildContext context, LocalToolSkill skill) {
    final provider = _searchProviderBySkill[skill.id];
    final providerLabel = provider == null ? null : _searchProviderLabels[provider];
    final configured = provider != null && _configuredSearchProviders.contains(provider);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Semantics(
          container: true,
          label: '${skill.title}，${_enabled.contains(skill.id) ? '已开启' : '已关闭'}。${skill.description}。支持：${skill.capabilities.join('、')}',
          child: SwitchListTile(
            value: _enabled.contains(skill.id),
            title: Text(skill.title),
            subtitle: Text('${skill.description}\n支持动作：${skill.capabilities.join('、')}\n底层工具：${skill.toolNames.join(', ')}'),
            onChanged: (value) {
              setState(() {
                if (value) {
                  _enabled.add(skill.id);
                } else {
                  _enabled.remove(skill.id);
                }
              });
            },
            activeColor: NavixTheme.primary,
          ),
        ),
        if (provider != null)
          Padding(
            padding: const EdgeInsets.only(left: 16, right: 16, bottom: 12),
            child: Semantics(
              button: true,
              label: '$providerLabel API Key，${configured ? '已配置，双击更新或清除' : '未配置，双击配置'}',
              child: OutlinedButton.icon(
                onPressed: () => _configureSearchApiKey(provider),
                icon: const Icon(Icons.key, size: 18),
                label: Text(configured ? '$providerLabel API Key：已配置' : '配置 $providerLabel API Key'),
              ),
            ),
          ),
        if (provider != null)
          Padding(
            padding: const EdgeInsets.only(left: 16, right: 16, bottom: 12),
            child: Semantics(
              button: true,
              label: '$providerLabel 搜索设置，双击配置返回数量、搜索类型和过滤条件',
              child: OutlinedButton.icon(
                onPressed: () async {
                  final saved = await Navigator.push<bool>(
                    context,
                    MaterialPageRoute(
                      builder: (_) => SearchProviderSettingsScreen(
                        provider: provider,
                        providerLabel: providerLabel ?? provider,
                      ),
                    ),
                  );
                  if (saved == true && context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('$providerLabel 搜索设置已保存')),
                    );
                  }
                },
                icon: const Icon(Icons.tune, size: 18),
                label: Text('配置 $providerLabel 搜索设置'),
              ),
            ),
          ),
      ],
    );
  }

  Future<void> _restoreSavedDefaults() async {
    final defaults = await StorageService.instance.getLocalEnabledSkills();
    if (!mounted) return;
    setState(() {
      _enabled = defaults.where(LocalToolSkillCatalog.allIds.contains).toSet();
    });
  }

  Future<void> _save() async {
    if (widget.persistAsDefaults) {
      await StorageService.instance.setLocalEnabledSkills(_enabled);
    }
    if (!mounted) return;
    Navigator.pop(context, Set<String>.from(_enabled));
  }

  @override
  Widget build(BuildContext context) {
    final covered = LocalToolSkillCatalog.coveredToolNames.length;
    return Scaffold(
      backgroundColor: NavixTheme.background,
      appBar: AppBar(
        title: Text(widget.persistAsDefaults ? '默认工具与技能' : '本次会话工具'),
        actions: [
          TextButton(onPressed: _loading ? null : _save, child: const Text('保存')),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Semantics(
                  label: '当前启用 ${_enabled.length} 个技能，共 ${LocalToolSkillCatalog.all.length} 个。规范工具覆盖 $covered 个，共 ${LocalToolSkillCatalog.allCanonicalToolNames.length} 个。',
                  child: Text(
                    '当前启用 ${_enabled.length}/${LocalToolSkillCatalog.all.length} 个技能；规范工具覆盖 $covered/${LocalToolSkillCatalog.allCanonicalToolNames.length}。'
                    '${LocalToolSkillCatalog.hasCompleteCoverage ? ' 当前完整工具面均已归类。' : ' 工具覆盖异常。'}',
                  ),
                ),
                const SizedBox(height: 12),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    OutlinedButton(
                      onPressed: () => setState(() => _enabled = <String>{}),
                      child: const Text('全部关闭'),
                    ),
                    OutlinedButton(
                      onPressed: () => setState(
                        () => _enabled = Set<String>.from(LocalToolSkillCatalog.allIds),
                      ),
                      child: const Text('全部开启'),
                    ),
                    if (!widget.persistAsDefaults)
                      OutlinedButton(
                        onPressed: _restoreSavedDefaults,
                        child: const Text('恢复默认'),
                      ),
                  ],
                ),
                const SizedBox(height: 12),
                const Text('技能只由您手动开启。应用不会根据消息内容自动选择、开启或关闭技能。'),
                const SizedBox(height: 16),
                for (final category in LocalToolSkillCatalog.categories) ...[
                  Padding(
                    padding: const EdgeInsets.only(top: 12, bottom: 4),
                    child: Text(
                      category,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            color: NavixTheme.textPrimary,
                            fontWeight: FontWeight.w600,
                          ),
                    ),
                  ),
                  for (final skill in LocalToolSkillCatalog.inCategory(category))
                    _buildSkillTile(context, skill),
                ],
                const SizedBox(height: 24),
              ],
            ),
    );
  }
}
