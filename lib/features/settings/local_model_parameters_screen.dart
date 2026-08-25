import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../app/theme.dart';
import '../../core/services/storage_service.dart';

// RASTACODER_V5_SKILLS_PARAMS_BENCH_STREAM
class LocalModelParametersScreen extends StatefulWidget {
  const LocalModelParametersScreen({super.key});

  @override
  State<LocalModelParametersScreen> createState() => _LocalModelParametersScreenState();
}

class _LocalModelParametersScreenState extends State<LocalModelParametersScreen> {
  final _temperature = TextEditingController();
  final _topP = TextEditingController();
  final _contextTokens = TextEditingController();
  final _outputTokens = TextEditingController();
  String _thinkingMode = 'model_default';
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final storage = StorageService.instance;
    final temperature = await storage.getLocalTemperature();
    final topP = await storage.getLocalTopP();
    final contextTokens = await storage.getLocalContextTokens();
    final outputTokens = await storage.getLocalMaxOutputTokens();
    final thinking = await storage.getLocalThinkingMode();
    if (!mounted) return;
    setState(() {
      _temperature.text = temperature.toString();
      _topP.text = topP.toString();
      _contextTokens.text = contextTokens.toString();
      _outputTokens.text = outputTokens.toString();
      _thinkingMode = thinking;
      _loading = false;
    });
  }

  void _error(String text) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(text)));
  }

  Future<void> _save() async {
    final temperature = double.tryParse(_temperature.text.trim());
    final topP = double.tryParse(_topP.text.trim());
    final contextTokens = int.tryParse(_contextTokens.text.trim());
    final outputTokens = int.tryParse(_outputTokens.text.trim());

    if (temperature == null || temperature < 0 || temperature > 2) {
      _error('Temperature 必须是 0 到 2 之间的数字。');
      return;
    }
    if (topP == null || topP <= 0 || topP > 1) {
      _error('Top P 必须大于 0 且不超过 1。');
      return;
    }
    if (contextTokens == null || contextTokens < 512 || contextTokens > 32768) {
      _error('上下文预算必须是 512 到 32768 之间的整数 Token。');
      return;
    }
    if (outputTokens == null || outputTokens < 1 || outputTokens > 8192) {
      _error('最大输出必须是 1 到 8192 之间的整数 Token。');
      return;
    }
    if (outputTokens >= contextTokens) {
      _error('最大输出 Token 必须小于上下文预算。');
      return;
    }
    if (contextTokens + outputTokens > 38912) {
      _error('为当前 MLC 运行时预留系统提示空间后，上下文预算与最大输出之和不能超过 38912 Token。');
      return;
    }

    final storage = StorageService.instance;
    await storage.setLocalTemperature(temperature);
    await storage.setLocalTopP(topP);
    await storage.setLocalContextTokens(contextTokens);
    await storage.setLocalMaxOutputTokens(outputTokens);
    await storage.setLocalThinkingMode(_thinkingMode);
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('本地模型参数已保存')));
  }

  Widget _numberField({
    required TextEditingController controller,
    required String label,
    required String helper,
    bool integerOnly = false,
    String? suffix,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: TextField(
        controller: controller,
        keyboardType: TextInputType.numberWithOptions(decimal: !integerOnly),
        inputFormatters: integerOnly ? [FilteringTextInputFormatter.digitsOnly] : null,
        decoration: InputDecoration(
          labelText: label,
          helperText: helper,
          suffixText: suffix,
          border: const OutlineInputBorder(),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: NavixTheme.background,
      appBar: AppBar(
        title: const Text('本地模型参数'),
        actions: [TextButton(onPressed: _loading ? null : _save, child: const Text('保存'))],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                const Text('这些参数只作用于设备端本地模型。工具技能和思考模式均不会被应用自动推断。'),
                const SizedBox(height: 16),
                _numberField(
                  controller: _temperature,
                  label: 'Temperature',
                  helper: '采样温度，允许 0–2。',
                ),
                _numberField(
                  controller: _topP,
                  label: 'Top P',
                  helper: '核采样概率，允许大于 0 且不超过 1。',
                ),
                _numberField(
                  controller: _contextTokens,
                  label: '上下文预算',
                  helper: '手动输入送入模型的会话历史预算；当前稳定上限 32768。',
                  integerOnly: true,
                  suffix: 'Token',
                ),
                _numberField(
                  controller: _outputTokens,
                  label: '单次最大输出',
                  helper: '手动输入每一轮本地模型允许生成的最大长度。',
                  integerOnly: true,
                  suffix: 'Token',
                ),
                const Divider(),
                Text('思考模式', style: Theme.of(context).textTheme.titleMedium),
                const Text('只按这里的手动设置执行；不会根据启用的技能自动切换。'),
                RadioListTile<String>(
                  value: 'model_default', groupValue: _thinkingMode,
                  title: const Text('保持模型默认'),
                  subtitle: const Text('不额外写入 /think 或 /no_think。'),
                  onChanged: (value) => setState(() => _thinkingMode = value!),
                ),
                RadioListTile<String>(
                  value: 'enabled', groupValue: _thinkingMode,
                  title: const Text('强制开启思考'),
                  subtitle: const Text('对支持 Qwen3 thinking 的模型写入 /think。'),
                  onChanged: (value) => setState(() => _thinkingMode = value!),
                ),
                RadioListTile<String>(
                  value: 'disabled', groupValue: _thinkingMode,
                  title: const Text('强制关闭思考'),
                  subtitle: const Text('对支持 Qwen3 thinking 的模型写入 /no_think。'),
                  onChanged: (value) => setState(() => _thinkingMode = value!),
                ),
              ],
            ),
    );
  }

  @override
  void dispose() {
    _temperature.dispose();
    _topP.dispose();
    _contextTokens.dispose();
    _outputTokens.dispose();
    super.dispose();
  }
}
