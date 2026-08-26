import 'package:flutter/material.dart';

import '../../app/theme.dart';
import '../../core/services/storage_service.dart';

// RASTACODER_V11_OPENAI_COMPAT_SETTINGS_SCREEN
class OpenAICompatibleSettingsScreen extends StatefulWidget {
  const OpenAICompatibleSettingsScreen({super.key});

  @override
  State<OpenAICompatibleSettingsScreen> createState() =>
      _OpenAICompatibleSettingsScreenState();
}

class _OpenAICompatibleSettingsScreenState
    extends State<OpenAICompatibleSettingsScreen> {
  final _baseUrlController = TextEditingController();
  final _apiKeyController = TextEditingController();
  final _modelController = TextEditingController();
  bool _loading = true;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final config = await StorageService.instance.getOpenAICompatibleConfig();
    _baseUrlController.text = config['base_url'] ?? '';
    _apiKeyController.text = config['api_key'] ?? '';
    _modelController.text = config['model'] ?? '';
    if (mounted) setState(() => _loading = false);
  }

  @override
  void dispose() {
    _baseUrlController.dispose();
    _apiKeyController.dispose();
    _modelController.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    final baseUrl = _baseUrlController.text.trim();
    final model = _modelController.text.trim();
    if (baseUrl.isEmpty || model.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Base URL 和 Model ID 不能为空')),
      );
      return;
    }
    final uri = Uri.tryParse(baseUrl);
    if (uri == null || !uri.hasScheme ||
        (uri.scheme != 'http' && uri.scheme != 'https')) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Base URL 必须是 http 或 https 地址')),
      );
      return;
    }
    setState(() => _saving = true);
    await StorageService.instance.setOpenAICompatibleBaseUrl(baseUrl);
    await StorageService.instance.setOpenAICompatibleApiKey(_apiKeyController.text);
    await StorageService.instance.setOpenAICompatibleModel(model);
    if (!mounted) return;
    setState(() => _saving = false);
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('OpenAI 兼容接口配置已保存')),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: NavixTheme.background,
      appBar: AppBar(
        backgroundColor: NavixTheme.background,
        title: const Text('OpenAI 兼容接口'),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                const Text(
                  '兼容 OpenAI Chat Completions 工具调用协议。Base URL 可以填写服务根地址、以 /v1 结尾的地址，或完整 /chat/completions 地址。模型和本地 Qwen 共用同一套工具、兼容层与执行后验证。',
                ),
                const SizedBox(height: 16),
                Semantics(
                  textField: true,
                  label: 'OpenAI 兼容接口 Base URL',
                  child: TextField(
                    controller: _baseUrlController,
                    keyboardType: TextInputType.url,
                    autocorrect: false,
                    decoration: const InputDecoration(
                      labelText: 'Base URL',
                      hintText: 'https://api.example.com/v1',
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                Semantics(
                  textField: true,
                  label: 'OpenAI 兼容接口 API Key',
                  child: TextField(
                    controller: _apiKeyController,
                    obscureText: true,
                    autocorrect: false,
                    decoration: const InputDecoration(
                      labelText: 'API Key',
                      hintText: '可留空：部分兼容服务不要求密钥',
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                Semantics(
                  textField: true,
                  label: 'OpenAI 兼容接口 Model ID',
                  child: TextField(
                    controller: _modelController,
                    autocorrect: false,
                    decoration: const InputDecoration(
                      labelText: 'Model ID',
                      hintText: '例如 provider-model-name',
                    ),
                  ),
                ),
                const SizedBox(height: 20),
                Semantics(
                  button: true,
                  label: _saving ? '正在保存 OpenAI 兼容接口配置' : '保存 OpenAI 兼容接口配置',
                  child: ElevatedButton(
                    onPressed: _saving ? null : _save,
                    child: Text(_saving ? '正在保存…' : '保存'),
                  ),
                ),
                const SizedBox(height: 12),
                const Text(
                  '保存后回到“API 与模型”，在模型列表中选择 OpenAI Compatible。API Key 使用系统安全存储，并且不会写入模型提示词或工具参数。',
                ),
              ],
            ),
    );
  }
}
