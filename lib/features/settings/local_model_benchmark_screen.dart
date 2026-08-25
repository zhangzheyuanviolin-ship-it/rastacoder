import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../app/theme.dart';
import '../../core/models/model_registry.dart';
import '../../core/services/local_llm_service.dart';
import '../../core/services/storage_service.dart';

// RASTACODER_V5_SKILLS_PARAMS_BENCH_STREAM
class LocalModelBenchmarkScreen extends StatefulWidget {
  const LocalModelBenchmarkScreen({super.key});

  @override
  State<LocalModelBenchmarkScreen> createState() => _LocalModelBenchmarkScreenState();
}

class _LocalModelBenchmarkScreenState extends State<LocalModelBenchmarkScreen> {
  bool _running = false;
  Map<String, dynamic>? _current;
  List<Map<String, dynamic>> _history = [];
  String? _status;

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  Future<void> _loadHistory() async {
    final history = await StorageService.instance.getLocalBenchmarkHistory();
    if (mounted) setState(() => _history = history);
  }

  Future<void> _run() async {
    if (_running) return;
    final storage = StorageService.instance;
    final modelId = await storage.getPreferredModel();
    final model = ModelRegistry.getById(modelId);
    if (model == null || !model.isOffline) {
      _show('请先在设置中选择一个已下载的本地模型。');
      return;
    }
    final state = LocalLLMService.instance.modelStates[modelId];
    if (state?.downloadState != ModelDownloadState.downloaded) {
      _show('当前本地模型尚未下载完成。');
      return;
    }

    setState(() {
      _running = true;
      _status = '正在准备模型…';
    });

    try {
      final service = LocalLLMService.instance;
      final alreadyLoaded = service.loadedModelId == modelId &&
          service.loadState == ModelLoadState.loaded;
      final loadWatch = Stopwatch()..start();
      if (!alreadyLoaded) await service.loadModel(modelId);
      loadWatch.stop();

      if (!mounted) return;
      setState(() => _status = '正在运行固定基准测试…');
      final temperature = await storage.getLocalTemperature();
      final topP = await storage.getLocalTopP();
      final result = await service.runBenchmark(
        maxTokens: 128,
        temperature: temperature,
        topP: topP,
      );
      result['model_id'] = modelId;
      result['model_name'] = model.displayName;
      result['timestamp'] = DateTime.now().toIso8601String();
      result['model_load_ms'] = alreadyLoaded ? 0 : loadWatch.elapsedMilliseconds;
      result['load_mode'] = alreadyLoaded ? 'warm' : 'cold';
      if (mounted) {
        setState(() {
          _current = result;
          _status = '基准测试完成';
        });
      }
    } catch (e) {
      _show('基准测试失败：$e');
      if (mounted) setState(() => _status = null);
    } finally {
      if (mounted) setState(() => _running = false);
    }
  }

  Future<void> _save() async {
    final result = _current;
    if (result == null) return;
    await StorageService.instance.appendLocalBenchmarkResult(result);
    await _loadHistory();
    _show('测试结果已保存');
  }

  Future<void> _copy() async {
    final result = _current;
    if (result == null) return;
    await Clipboard.setData(ClipboardData(text: _formatResult(result)));
    _show('当前测试结果已复制到剪贴板');
  }

  void _show(String text) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(text)));
  }

  String _formatBytes(dynamic raw) {
    final value = raw is num ? raw.toDouble() : double.tryParse('$raw') ?? 0;
    if (value <= 0) return '不可用';
    return '${(value / 1024 / 1024).toStringAsFixed(1)} MB';
  }

  String _formatNum(dynamic raw, {int digits = 2}) {
    final value = raw is num ? raw.toDouble() : double.tryParse('$raw');
    return value == null ? '不可用' : value.toStringAsFixed(digits);
  }

  String _formatResult(Map<String, dynamic> r) {
    return [
      'RastaCoder 本地模型性能基准',
      '时间：${r['timestamp'] ?? ''}',
      '模型：${r['model_name'] ?? r['model_id'] ?? ''}',
      '加载模式：${r['load_mode'] ?? ''}',
      '模型加载：${r['model_load_ms'] ?? 0} ms',
      'Prompt Token：${r['prompt_tokens'] ?? 0}',
      'Completion Token：${r['completion_tokens'] ?? 0}',
      'Prefill：${_formatNum(r['prefill_tokens_per_s'])} tok/s',
      'Decode：${_formatNum(r['decode_tokens_per_s'])} tok/s',
      'TTFT：${_formatNum(r['ttft_ms'])} ms',
      '端到端延迟：${_formatNum(r['end_to_end_ms'])} ms',
      '进程 PSS：${_formatBytes((r['process_pss_kb'] as num? ?? 0) * 1024)}',
      'Java Heap：${_formatBytes(r['java_heap_bytes'])}',
      'Native Heap：${_formatBytes(r['native_heap_bytes'])}',
      'GPU 总内存（设备属性）：${r['gpu_total_mb'] ?? -1} MB',
      '采样：temperature=${r['temperature'] ?? ''}, top_p=${r['top_p'] ?? ''}',
    ].join('\n');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: NavixTheme.background,
      appBar: AppBar(title: const Text('本地模型性能基准')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text('固定基准会直接调用当前本地 MLC 模型，不加载任何工具。测试记录 Prefill、Decode、首 Token 延迟、端到端延迟与进程内存。'),
          const SizedBox(height: 12),
          ElevatedButton.icon(
            onPressed: _running ? null : _run,
            icon: _running
                ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                : const Icon(Icons.speed),
            label: Text(_running ? '正在跑分…' : '运行当前模型基准'),
          ),
          if (_status != null) ...[
            const SizedBox(height: 12),
            Semantics(liveRegion: true, child: Text(_status!)),
          ],
          if (_current != null) ...[
            const SizedBox(height: 20),
            Text('当前结果', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            SelectableText(_formatResult(_current!)),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                ElevatedButton.icon(
                  onPressed: _save,
                  icon: const Icon(Icons.save_outlined),
                  label: const Text('保存结果'),
                ),
                OutlinedButton.icon(
                  onPressed: _copy,
                  icon: const Icon(Icons.copy),
                  label: const Text('复制到剪贴板'),
                ),
              ],
            ),
          ],
          if (_history.isNotEmpty) ...[
            const SizedBox(height: 24),
            Text('已保存结果', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            for (final item in _history.take(10))
              ExpansionTile(
                title: Text('${item['model_name'] ?? item['model_id'] ?? '本地模型'} · ${item['timestamp'] ?? ''}'),
                children: [
                  Padding(
                    padding: const EdgeInsets.all(12),
                    child: SelectableText(_formatResult(item)),
                  ),
                ],
              ),
          ],
        ],
      ),
    );
  }
}
