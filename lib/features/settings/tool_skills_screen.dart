import 'package:flutter/material.dart';

import '../../app/theme.dart';
import '../../core/models/tool_skill.dart';
import '../../core/services/storage_service.dart';

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
  Set<String> _enabled = <String>{};
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
    if (!mounted) return;
    setState(() {
      _enabled = initial.where(known.contains).toSet();
      _loading = false;
    });
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
                ],
                const SizedBox(height: 24),
              ],
            ),
    );
  }
}
