from pathlib import Path


def patch(path: str, old: str, new: str, count: int = 1) -> None:
    p = Path(path)
    text = p.read_text(encoding='utf-8')
    actual = text.count(old)
    if actual != count:
        raise SystemExit(f'{path}: expected {count}, found {actual}: {old[:120]!r}')
    p.write_text(text.replace(old, new, count), encoding='utf-8')


path = 'lib/features/settings/tool_skills_screen.dart'

patch(
    path,
    "class _ToolSkillsScreenState extends State<ToolSkillsScreen> {\n  Set<String> _enabled = <String>{};\n  bool _loading = true;\n",
    "class _ToolSkillsScreenState extends State<ToolSkillsScreen> {\n"
    "  static const _searchProviderBySkill = <String, String>{\n"
    "    'anysearch_search': 'anysearch',\n"
    "    'exa_search': 'exa',\n"
    "    'langsearch_search': 'langsearch',\n"
    "    'tavily_search': 'tavily',\n"
    "  };\n"
    "  static const _searchProviderLabels = <String, String>{\n"
    "    'anysearch': 'AnySearch',\n"
    "    'exa': 'Exa',\n"
    "    'langsearch': 'LangSearch',\n"
    "    'tavily': 'Tavily',\n"
    "  };\n\n"
    "  Set<String> _enabled = <String>{};\n"
    "  Set<String> _configuredSearchProviders = <String>{};\n"
    "  bool _loading = true;\n",
)

patch(
    path,
    "  Future<void> _load() async {\n    final initial = widget.initialEnabled ??\n        await StorageService.instance.getLocalEnabledSkills();\n    final known = LocalToolSkillCatalog.allIds;\n    if (!mounted) return;\n    setState(() {\n      _enabled = initial.where(known.contains).toSet();\n      _loading = false;\n    });\n  }\n",
    "  Future<void> _load() async {\n"
    "    final initial = widget.initialEnabled ??\n"
    "        await StorageService.instance.getLocalEnabledSkills();\n"
    "    final known = LocalToolSkillCatalog.allIds;\n"
    "    final configured = <String>{};\n"
    "    for (final provider in _searchProviderLabels.keys) {\n"
    "      if (await StorageService.instance.hasSearchApiKey(provider)) {\n"
    "        configured.add(provider);\n"
    "      }\n"
    "    }\n"
    "    if (!mounted) return;\n"
    "    setState(() {\n"
    "      _enabled = initial.where(known.contains).toSet();\n"
    "      _configuredSearchProviders = configured;\n"
    "      _loading = false;\n"
    "    });\n"
    "  }\n\n"
    "  Future<void> _configureSearchApiKey(String provider) async {\n"
    "    final label = _searchProviderLabels[provider] ?? provider;\n"
    "    final controller = TextEditingController();\n"
    "    final configured = _configuredSearchProviders.contains(provider);\n"
    "    final action = await showDialog<String>(\n"
    "      context: context,\n"
    "      builder: (dialogContext) => AlertDialog(\n"
    "        title: Text('$label API Key'),\n"
    "        content: Column(\n"
    "          mainAxisSize: MainAxisSize.min,\n"
    "          crossAxisAlignment: CrossAxisAlignment.start,\n"
    "          children: [\n"
    "            Text(configured\n"
    "                ? '已配置。输入新密钥可以替换；现有密钥不会显示在屏幕上。'\n"
    "                : '请输入 $label API Key。密钥将保存在 Android 安全存储中。'),\n"
    "            const SizedBox(height: 12),\n"
    "            Semantics(\n"
    "              textField: true,\n"
    "              label: '$label API Key 输入框',\n"
    "              child: TextField(\n"
    "                controller: controller,\n"
    "                autofocus: true,\n"
    "                obscureText: true,\n"
    "                enableSuggestions: false,\n"
    "                autocorrect: false,\n"
    "                decoration: InputDecoration(\n"
    "                  labelText: '$label API Key',\n"
    "                  hintText: configured ? '输入新密钥以替换' : '输入 API Key',\n"
    "                ),\n"
    "              ),\n"
    "            ),\n"
    "          ],\n"
    "        ),\n"
    "        actions: [\n"
    "          TextButton(\n"
    "            onPressed: () => Navigator.pop(dialogContext, 'cancel'),\n"
    "            child: const Text('取消'),\n"
    "          ),\n"
    "          if (configured)\n"
    "            TextButton(\n"
    "              onPressed: () => Navigator.pop(dialogContext, 'clear'),\n"
    "              child: const Text('清除密钥'),\n"
    "            ),\n"
    "          FilledButton(\n"
    "            onPressed: () => Navigator.pop(dialogContext, 'save'),\n"
    "            child: const Text('保存'),\n"
    "          ),\n"
    "        ],\n"
    "      ),\n"
    "    );\n"
    "    if (!mounted || action == null || action == 'cancel') {\n"
    "      controller.dispose();\n"
    "      return;\n"
    "    }\n"
    "    if (action == 'clear') {\n"
    "      await StorageService.instance.deleteSearchApiKey(provider);\n"
    "      if (mounted) {\n"
    "        setState(() => _configuredSearchProviders.remove(provider));\n"
    "        ScaffoldMessenger.of(context).showSnackBar(\n"
    "          SnackBar(content: Text('$label API Key 已清除')),\n"
    "        );\n"
    "      }\n"
    "      controller.dispose();\n"
    "      return;\n"
    "    }\n"
    "    final value = controller.text.trim();\n"
    "    controller.dispose();\n"
    "    if (value.isEmpty) {\n"
    "      if (mounted) {\n"
    "        ScaffoldMessenger.of(context).showSnackBar(\n"
    "          const SnackBar(content: Text('API Key 不能为空')),\n"
    "        );\n"
    "      }\n"
    "      return;\n"
    "    }\n"
    "    await StorageService.instance.setSearchApiKey(provider, value);\n"
    "    if (mounted) {\n"
    "      setState(() => _configuredSearchProviders.add(provider));\n"
    "      ScaffoldMessenger.of(context).showSnackBar(\n"
    "        SnackBar(content: Text('$label API Key 已安全保存')),\n"
    "      );\n"
    "    }\n"
    "  }\n\n"
    "  Widget _buildSkillTile(BuildContext context, LocalToolSkill skill) {\n"
    "    final provider = _searchProviderBySkill[skill.id];\n"
    "    final providerLabel = provider == null ? null : _searchProviderLabels[provider];\n"
    "    final configured = provider != null && _configuredSearchProviders.contains(provider);\n"
    "    return Column(\n"
    "      crossAxisAlignment: CrossAxisAlignment.stretch,\n"
    "      children: [\n"
    "        Semantics(\n"
    "          container: true,\n"
    "          label: '${skill.title}，${_enabled.contains(skill.id) ? '已开启' : '已关闭'}。${skill.description}。支持：${skill.capabilities.join('、')}',\n"
    "          child: SwitchListTile(\n"
    "            value: _enabled.contains(skill.id),\n"
    "            title: Text(skill.title),\n"
    "            subtitle: Text('${skill.description}\\n支持动作：${skill.capabilities.join('、')}\\n底层工具：${skill.toolNames.join(', ')}'),\n"
    "            onChanged: (value) {\n"
    "              setState(() {\n"
    "                if (value) {\n"
    "                  _enabled.add(skill.id);\n"
    "                } else {\n"
    "                  _enabled.remove(skill.id);\n"
    "                }\n"
    "              });\n"
    "            },\n"
    "            activeColor: NavixTheme.primary,\n"
    "          ),\n"
    "        ),\n"
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
    "          ),\n"
    "      ],\n"
    "    );\n"
    "  }\n",
)

# Replace inline switch construction with reusable tile that includes key control.
p = Path(path)
text = p.read_text(encoding='utf-8')
old = '''                  for (final skill in LocalToolSkillCatalog.inCategory(category))
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
'''
new = '''                  for (final skill in LocalToolSkillCatalog.inCategory(category))
                    _buildSkillTile(context, skill),
'''
if text.count(old) != 1:
    raise SystemExit('tool_skills_screen.dart: inline skill tile block missing')
p.write_text(text.replace(old, new, 1), encoding='utf-8')

print('V8 search UI patch applied successfully')
