from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
model_path = ROOT / "lib/core/models/model_registry.dart"
chat_path = ROOT / "lib/features/chat/presentation/chat_screen.dart"

model_text = model_path.read_text(encoding="utf-8")
chat_text = chat_path.read_text(encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        print(f"{label}: already applied")
        return text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one anchor, found {count}")
    print(f"{label}: applied")
    return text.replace(old, new, 1)


model_text = replace_once(
    model_text,
    "enum ModelProvider { cloud, offline }\n",
    "enum ModelProvider { cloud, offline }\n\n"
    "// RASTACODER_V13_PROVIDER_IDENTITY\n"
    "enum ModelRouteProvider { local, anthropic, openAICompatible }\n",
    "provider identity enum",
)

model_text = replace_once(
    model_text,
    "  bool get isOffline => provider == ModelProvider.offline;\n"
    "  bool get isCloud => provider == ModelProvider.cloud;\n",
    "  bool get isOffline => provider == ModelProvider.offline;\n"
    "  bool get isCloud => provider == ModelProvider.cloud;\n\n"
    "  ModelRouteProvider get routeProvider {\n"
    "    if (isOffline) return ModelRouteProvider.local;\n"
    "    if (id == 'openai-compatible') return ModelRouteProvider.openAICompatible;\n"
    "    return ModelRouteProvider.anthropic;\n"
    "  }\n",
    "provider identity getter",
)

sync_pattern = re.compile(
    r"  Future<void> _syncModelRouteState\(\) async \{[\s\S]*?\n  \}\n\n  Future<bool> _ensureSelectedRouteReadyForSend\(\) async \{",
    re.MULTILINE,
)
sync_match = sync_pattern.search(chat_text)
if not sync_match:
    if "RASTACODER_V13_PROVIDER_ROUTE_SYNC" not in chat_text:
        raise SystemExit("provider sync/readiness block anchor not found")
else:
    replacement = '''  Future<void> _syncModelRouteState() async {
    // RASTACODER_V13_PROVIDER_ROUTE_SYNC
    final preferredModel = await StorageService.instance.getPreferredModel();
    final modelInfo = ModelRegistry.getById(preferredModel);
    final routeProvider = modelInfo?.routeProvider ?? ModelRouteProvider.anthropic;

    if (routeProvider == ModelRouteProvider.local) {
      final hasKey = await StorageService.instance.hasApiKey();
      final downloaded = LocalLLMService.instance.modelStates[preferredModel]?.downloadState ==
          ModelDownloadState.downloaded;
      if (downloaded &&
          (LocalLLMService.instance.loadedModelId != preferredModel ||
              LocalLLMService.instance.loadState != ModelLoadState.loaded)) {
        try {
          await LocalLLMService.instance.loadModel(preferredModel);
        } catch (e) {
          debugPrint('[V13 route restore] $e');
        }
      }
      if (!mounted) return;
      setState(() {
        _hasApiKey = hasKey;
        _awaitingApiKey = false;
      });
      return;
    }

    if (routeProvider == ModelRouteProvider.openAICompatible) {
      // Base URL + Model ID define readiness. Provider API keys are optional
      // because some OpenAI-compatible endpoints are local or unauthenticated.
      final config = await StorageService.instance.getOpenAICompatibleConfig();
      final configured = (config['base_url'] ?? '').trim().isNotEmpty &&
          (config['model'] ?? '').trim().isNotEmpty;
      if (!mounted) return;
      setState(() {
        _hasApiKey = configured;
        _awaitingApiKey = false;
      });
      return;
    }

    final hasKey = await StorageService.instance.hasApiKey();
    if (!mounted) return;
    setState(() {
      _hasApiKey = hasKey;
      _awaitingApiKey = !hasKey;
    });
    if (hasKey) _sendStoredApiKeyToPython();
  }

  Future<bool> _ensureSelectedRouteReadyForSend() async {'''
    chat_text = chat_text[:sync_match.start()] + replacement + chat_text[sync_match.end():]
    print("provider sync routing: applied")

ready_pattern = re.compile(
    r"  Future<bool> _ensureSelectedRouteReadyForSend\(\) async \{[\s\S]*?\n  \}\n\n  void _addRoutingError",
    re.MULTILINE,
)
ready_match = ready_pattern.search(chat_text)
if not ready_match:
    if "RASTACODER_V13_PROVIDER_ROUTE_READY" not in chat_text:
        raise SystemExit("provider readiness method anchor not found")
else:
    replacement = '''  Future<bool> _ensureSelectedRouteReadyForSend() async {
    // RASTACODER_V13_PROVIDER_ROUTE_READY
    final preferredModel = await StorageService.instance.getPreferredModel();
    final modelInfo = ModelRegistry.getById(preferredModel);
    final routeProvider = modelInfo?.routeProvider ?? ModelRouteProvider.anthropic;

    if (routeProvider == ModelRouteProvider.local) {
      if (mounted && _awaitingApiKey) {
        setState(() => _awaitingApiKey = false);
      }
      final state = LocalLLMService.instance.modelStates[preferredModel];
      if (state?.downloadState != ModelDownloadState.downloaded) {
        _addRoutingError('已选择本地模型 ${modelInfo?.displayName ?? preferredModel}，但模型文件尚未下载完成。请在模型页面完成下载后再发送。');
        return false;
      }
      try {
        if (LocalLLMService.instance.loadedModelId != preferredModel ||
            LocalLLMService.instance.loadState != ModelLoadState.loaded) {
          if (mounted) setState(() => _statusMessage = '正在加载已选择的本地模型…');
          await LocalLLMService.instance.loadModel(preferredModel);
        }
      } catch (e) {
        _addRoutingError('本地模型加载失败：$e');
        return false;
      }
      if (LocalLLMService.instance.loadedModelId != preferredModel ||
          LocalLLMService.instance.loadState != ModelLoadState.loaded) {
        _addRoutingError('本地模型尚未进入可推理状态，请重新加载模型后再试。');
        return false;
      }
      return true;
    }

    if (routeProvider == ModelRouteProvider.openAICompatible) {
      final config = await StorageService.instance.getOpenAICompatibleConfig();
      final baseUrl = (config['base_url'] ?? '').trim();
      final model = (config['model'] ?? '').trim();
      if (baseUrl.isEmpty || model.isEmpty) {
        _addRoutingError('OpenAI 兼容接口尚未配置完整。请在设置中填写 Base URL 和 Model ID。API Key 可按服务商要求选填。');
        return false;
      }
      if (mounted) {
        setState(() {
          _hasApiKey = true;
          _awaitingApiKey = false;
        });
      }
      return true;
    }

    final hasKey = await StorageService.instance.hasApiKey();
    if (mounted) {
      setState(() {
        _hasApiKey = hasKey;
        _awaitingApiKey = !hasKey;
      });
    }
    if (!hasKey) {
      _addRoutingError('当前选择的是 Claude 云端模型，但尚未配置 Claude API Key。请到设置中配置 API Key。');
      return false;
    }
    await _doSendApiKey();
    return true;
  }

  void _addRoutingError'''
    chat_text = chat_text[:ready_match.start()] + replacement + chat_text[ready_match.end():]
    print("provider readiness routing: applied")

model_path.write_text(model_text, encoding="utf-8")
chat_path.write_text(chat_text, encoding="utf-8")
print("V13 provider routing patch applied.")
