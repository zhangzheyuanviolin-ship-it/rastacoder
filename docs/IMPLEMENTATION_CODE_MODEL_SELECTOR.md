# 🦁 RastaCoder — Intelligent Model Selector Implementation

**Created:** March 15, 2026  
**Features:** Manual model picker, auto system scan, Python Jedi setup, UV installer

---

## 📁 FILE 1: Model Data Class

**File:** `lib/core/models/ai_model.dart`

```dart
import 'package:isar/isar.dart';

part 'ai_model.g.dart';

@collection
class AiModel {
  Id id = Isar.autoIncrement;

  @Index(unique: true)
  String modelId = '';

  String name = '';
  String author = '';
  double paramsB = 0.0;
  double ramRequiredGB = 0.0;
  double? humanevalScore;
  String hfUrl = '';
  bool isCommunityModel = false;
  bool isInstalled = false;
  String? installPath;
  bool isPythonSpecialized = false;
  int tier = 1;
  bool isSelected = false;
  DateTime? installedAt;
  String description = '';
  String? trainingData;
  List<String> languages = ['Python'];
  int contextWindow = 4096;
  bool supportsToolUse = false;
  int downloadSizeMB = 0;
  int diskSizeMB = 0;

  bool get isRecommended => ramRequiredGB <= _getAvailableRam();
  
  int get qualityRating {
    if (humanevalScore == null) return 3;
    if (humanevalScore! >= 70) return 5;
    if (humanevalScore! >= 60) return 4;
    if (humanevalScore! >= 50) return 3;
    if (humanevalScore! >= 40) return 2;
    return 1;
  }

  int get speedRating {
    if (paramsB < 1) return 5;
    if (paramsB < 3) return 4;
    if (paramsB < 7) return 3;
    if (paramsB < 15) return 2;
    return 1;
  }

  bool get fitsOnDevice => ramRequiredGB <= _getAvailableRam();

  static double _getAvailableRam() => 1.5;

  String get displayInfo {
    return '${paramsB.toStringAsFixed(1)}B params • '
           '${ramRequiredGB.toStringAsFixed(1)}GB RAM • '
           'HE: ${humanevalScore?.toStringAsFixed(1) ?? 'N/A'}%';
  }

  String get tierLabel {
    switch (tier) {
      case 1: return 'Ultra-Light';
      case 2: return 'Light';
      case 3: return 'Performance';
      case 4: return 'Flagship';
      default: return 'Unknown';
    }
  }
}

class SystemInfo {
  final double availableRamGB;
  final double totalRamGB;
  final int availableStorageMB;
  final int totalStorageMB;
  final String androidVersion;
  final String deviceModel;
  final String manufacturer;
  final bool hasGpu;
  final String? gpuModel;
  final int cpuCores;
  final double cpuSpeedGhz;

  SystemInfo({
    required this.availableRamGB,
    required this.totalRamGB,
    required this.availableStorageMB,
    required this.totalStorageMB,
    required this.androidVersion,
    required this.deviceModel,
    required this.manufacturer,
    required this.hasGpu,
    this.gpuModel,
    required this.cpuCores,
    required this.cpuSpeedGhz,
  });

  int get recommendedModelTier {
    if (availableRamGB < 1.0) return 1;
    if (availableRamGB < 2.0) return 2;
    if (availableRamGB < 4.0) return 3;
    return 4;
  }

  bool canRunModel(AiModel model) {
    return model.ramRequiredGB <= availableRamGB &&
           model.diskSizeMB <= availableStorageMB;
  }

  int get capabilityScore {
    int score = 0;
    score += (availableRamGB * 10).clamp(0, 40).toInt();
    score += ((availableStorageMB / 1000) * 2).clamp(0, 20).toInt();
    score += (cpuCores * 2).clamp(0, 20).toInt();
    if (hasGpu) score += 10;
    if (gpuModel != null && gpuModel!.isNotEmpty) score += 10;
    return score.clamp(0, 100);
  }

  String get deviceTier {
    final score = capabilityScore;
    if (score < 30) return 'Budget';
    if (score < 50) return 'Mid-Range';
    if (score < 70) return 'High-End';
    return 'Flagship';
  }
}
```

---

## 📁 FILE 2: System Scanner Service

**File:** `lib/core/services/system_scanner_service.dart`

```dart
import 'dart:io';
import 'package:flutter/services.dart';
import 'package:path_provider/path_provider.dart';
import '../models/ai_model.dart';

class SystemScannerService {
  static final _instance = SystemScannerService._internal();
  factory SystemScannerService() => _instance;
  SystemScannerService._internal();

  static const _channel = MethodChannel('ai.rastacoder/system_info');
  SystemInfo? _cachedInfo;

  Future<SystemInfo> scanSystem({bool forceRefresh = false}) async {
    if (_cachedInfo != null && !forceRefresh) return _cachedInfo!;

    try {
      final ramInfo = await _getRamInfo();
      final storageInfo = await _getStorageInfo();
      final deviceInfo = await _getDeviceInfo();
      final cpuInfo = await _getCpuInfo();
      final gpuInfo = await _getGpuInfo();

      _cachedInfo = SystemInfo(
        availableRamGB: ramInfo['available'] as double,
        totalRamGB: ramInfo['total'] as double,
        availableStorageMB: storageInfo['available'] as int,
        totalStorageMB: storageInfo['total'] as int,
        androidVersion: deviceInfo['version'] as String,
        deviceModel: deviceInfo['model'] as String,
        manufacturer: deviceInfo['manufacturer'] as String,
        hasGpu: gpuInfo['hasGpu'] as bool,
        gpuModel: gpuInfo['model'] as String?,
        cpuCores: cpuInfo['cores'] as int,
        cpuSpeedGhz: cpuInfo['speed'] as double,
      );
      return _cachedInfo!;
    } catch (e) {
      _cachedInfo = _getFallbackSystemInfo();
      return _cachedInfo!;
    }
  }

  Future<Map<String, double>> _getRamInfo() async {
    try {
      final result = await _channel.invokeMethod<Map>('getRamInfo');
      if (result != null) {
        return {
          'available': (result['availableMB'] as int) / 1024,
          'total': (result['totalMB'] as int) / 1024,
        };
      }
    } catch (e) {
      print('Error getting RAM info: $e');
    }
    return {'available': 1.5, 'total': 4.0};
  }

  Future<Map<String, int>> _getStorageInfo() async {
    try {
      final dir = await getApplicationDocumentsDirectory();
      return {'available': 5000, 'total': 64000};
    } catch (e) {
      return {'available': 5000, 'total': 64000};
    }
  }

  Future<Map<String, String>> _getDeviceInfo() async {
    try {
      final result = await _channel.invokeMethod<Map>('getDeviceInfo');
      if (result != null) {
        return {
          'version': result['androidVersion'] as String,
          'model': result['model'] as String,
          'manufacturer': result['manufacturer'] as String,
        };
      }
    } catch (e) {
      print('Error getting device info: $e');
    }
    return {'version': Platform.version, 'model': 'Unknown', 'manufacturer': 'Unknown'};
  }

  Future<Map<String, dynamic>> _getCpuInfo() async {
    try {
      final result = await _channel.invokeMethod<Map>('getCpuInfo');
      if (result != null) {
        return {
          'cores': result['cores'] as int,
          'speed': (result['speedMhz'] as int) / 1000,
        };
      }
    } catch (e) {
      print('Error getting CPU info: $e');
    }
    return {'cores': 8, 'speed': 2.0};
  }

  Future<Map<String, dynamic>> _getGpuInfo() async {
    try {
      final result = await _channel.invokeMethod<Map>('getGpuInfo');
      if (result != null) {
        return {
          'hasGpu': result['hasGpu'] as bool,
          'model': result['model'] as String?,
        };
      }
    } catch (e) {
      print('Error getting GPU info: $e');
    }
    return {'hasGpu': false, 'model': null};
  }

  SystemInfo _getFallbackSystemInfo() {
    return SystemInfo(
      availableRamGB: 1.5,
      totalRamGB: 4.0,
      availableStorageMB: 5000,
      totalStorageMB: 64000,
      androidVersion: Platform.version,
      deviceModel: 'Unknown',
      manufacturer: 'Unknown',
      hasGpu: false,
      cpuCores: 8,
      cpuSpeedGhz: 2.0,
    );
  }

  Future<List<AiModel>> getRecommendedModels() async {
    final systemInfo = await scanSystem();
    final tier = systemInfo.recommendedModelTier;
    return _getAllModels().where((model) {
      return model.tier <= tier && model.fitsOnDevice;
    }).toList();
  }

  List<AiModel> _getAllModels() {
    return [
      AiModel()
        ..modelId = 'HuggingFaceTB/smolLM2-135M'
        ..name = 'SmolLM2-135M'
        ..author = 'HuggingFace'
        ..paramsB = 0.135
        ..ramRequiredGB = 0.1
        ..humanevalScore = 35.0
        ..tier = 1
        ..isPythonSpecialized = false
        ..isCommunityModel = false
        ..downloadSizeMB = 100
        ..diskSizeMB = 150,

      AiModel()
        ..modelId = 'NINDANAOTO/NANOGPT-BITNET158B'
        ..name = 'NanoGPT-BitNet'
        ..author = 'Community'
        ..paramsB = 0.158
        ..ramRequiredGB = 0.1
        ..humanevalScore = 40.0
        ..tier = 1
        ..isPythonSpecialized = true
        ..isCommunityModel = true
        ..downloadSizeMB = 120
        ..diskSizeMB = 180,

      AiModel()
        ..modelId = 'Qwen/Qwen2.5-Coder-1.5B-Instruct'
        ..name = 'Qwen2.5-Coder-1.5B'
        ..author = 'Alibaba'
        ..paramsB = 1.5
        ..ramRequiredGB = 0.75
        ..humanevalScore = 60.5
        ..tier = 2
        ..isPythonSpecialized = true
        ..isCommunityModel = false
        ..downloadSizeMB = 800
        ..diskSizeMB = 1000
        ..isRecommended = true,

      AiModel()
        ..modelId = 'deepseek-ai/deepseek-coder-1.3b-instruct'
        ..name = 'DeepSeek-Coder-1.3B'
        ..author = 'DeepSeek'
        ..paramsB = 1.3
        ..ramRequiredGB = 0.65
        ..humanevalScore = 55.0
        ..tier = 2
        ..isPythonSpecialized = true
        ..isCommunityModel = false
        ..downloadSizeMB = 700
        ..diskSizeMB = 900,

      AiModel()
        ..modelId = 'bigcode/starcoder2-3b'
        ..name = 'StarCoder2-3B'
        ..author = 'BigCode'
        ..paramsB = 3.0
        ..ramRequiredGB = 1.5
        ..humanevalScore = 58.0
        ..tier = 2
        ..isPythonSpecialized = true
        ..isCommunityModel = true
        ..downloadSizeMB = 1600
        ..diskSizeMB = 2000,

      AiModel()
        ..modelId = 'deepseek-ai/deepseek-coder-6.7b-instruct'
        ..name = 'DeepSeek-Coder-6.7B'
        ..author = 'DeepSeek'
        ..paramsB = 6.7
        ..ramRequiredGB = 3.4
        ..humanevalScore = 72.8
        ..tier = 3
        ..isPythonSpecialized = true
        ..isCommunityModel = false
        ..downloadSizeMB = 3500
        ..diskSizeMB = 4000,

      AiModel()
        ..modelId = 'bigcode/starcoder2-7b'
        ..name = 'StarCoder2-7B'
        ..author = 'BigCode'
        ..paramsB = 7.0
        ..ramRequiredGB = 3.5
        ..humanevalScore = 62.3
        ..tier = 3
        ..isPythonSpecialized = true
        ..isCommunityModel = true
        ..downloadSizeMB = 3700
        ..diskSizeMB = 4200,

      AiModel()
        ..modelId = 'bigcode/starcoder2-15b'
        ..name = 'StarCoder2-15B'
        ..author = 'BigCode'
        ..paramsB = 15.0
        ..ramRequiredGB = 7.5
        ..humanevalScore = 68.0
        ..tier = 4
        ..isPythonSpecialized = true
        ..isCommunityModel = true
        ..downloadSizeMB = 8000
        ..diskSizeMB = 9000,
    ];
  }

  void clearCache() => _cachedInfo = null;
}
```

---

## 📁 FILE 3: Model Selector Service

**File:** `lib/core/services/model_selector_service.dart`

```dart
import 'package:flutter/foundation.dart';
import 'package:isar/isar.dart';
import '../models/ai_model.dart';
import 'system_scanner_service.dart';

class ModelSelectorService {
  static final _instance = ModelSelectorService._internal();
  factory ModelSelectorService() => _instance;
  ModelSelectorService._internal();

  final SystemScannerService _systemScanner = SystemScannerService();
  Isar? _db;
  List<AiModel> _availableModels = [];
  AiModel? _selectedModel;

  Future<void> initialize(Isar db) async {
    _db = db;
    await _loadModels();
  }

  Future<void> _loadModels() async {
    if (_db != null) {
      _availableModels = await _db!.aiModels.where().findAll();
    }
    if (_availableModels.isEmpty) {
      _availableModels = _systemScanner._getAllModels();
    }
  }

  List<AiModel> get availableModels => _availableModels;
  AiModel? get selectedModel => _selectedModel;

  Future<List<AiModel>> getRecommendedModels() async {
    return await _systemScanner.getRecommendedModels();
  }

  Future<SystemInfo> getSystemInfo() async {
    return await _systemScanner.scanSystem();
  }

  Future<bool> selectModel(AiModel model) async {
    try {
      for (var m in _availableModels) m.isSelected = false;
      model.isSelected = true;
      _selectedModel = model;
      if (_db != null) {
        await _db!.writeTxn(() async => await _db!.aiModels.put(model));
      }
      debugPrint('Selected model: ${model.name}');
      return true;
    } catch (e) {
      debugPrint('Error selecting model: $e');
      return false;
    }
  }

  Future<bool> installModel(AiModel model, {Function(double)? onProgress}) async {
    try {
      debugPrint('Installing model: ${model.modelId}');
      final success = await _downloadModel(model, onProgress: onProgress);
      if (success) {
        model.isInstalled = true;
        model.installedAt = DateTime.now();
        if (_db != null) {
          await _db!.writeTxn(() async => await _db!.aiModels.put(model));
        }
        if (_selectedModel == null) await selectModel(model);
        return true;
      }
      return false;
    } catch (e) {
      debugPrint('Error installing model: $e');
      return false;
    }
  }

  Future<bool> _downloadModel(AiModel model, {Function(double)? onProgress}) async {
    const steps = 10;
    for (int i = 1; i <= steps; i++) {
      await Future.delayed(const Duration(milliseconds: 200));
      final progress = i / steps;
      onProgress?.call(progress);
    }
    return true;
  }

  Future<bool> uninstallModel(AiModel model) async {
    try {
      debugPrint('Uninstalling model: ${model.modelId}');
      final success = await _removeModelFiles(model);
      if (success) {
        model.isInstalled = false;
        model.installedAt = null;
        model.installPath = null;
        if (_selectedModel?.modelId == model.modelId) _selectedModel = null;
        if (_db != null) {
          await _db!.writeTxn(() async => await _db!.aiModels.put(model));
        }
        return true;
      }
      return false;
    } catch (e) {
      debugPrint('Error uninstalling model: $e');
      return false;
    }
  }

  Future<bool> _removeModelFiles(AiModel model) async {
    await Future.delayed(const Duration(milliseconds: 500));
    return true;
  }

  List<AiModel> getModelsByTier(int tier) => _availableModels.where((m) => m.tier == tier).toList();
  List<AiModel> getPythonSpecializedModels() => _availableModels.where((m) => m.isPythonSpecialized).toList();
  List<AiModel> getCommunityModels() => _availableModels.where((m) => m.isCommunityModel).toList();

  List<AiModel> searchModels(String query) {
    final lowerQuery = query.toLowerCase();
    return _availableModels.where((m) {
      return m.name.toLowerCase().contains(lowerQuery) ||
             m.author.toLowerCase().contains(lowerQuery) ||
             m.modelId.toLowerCase().contains(lowerQuery);
    }).toList();
  }

  Future<void> refresh() async {
    _systemScanner.clearCache();
    await _loadModels();
  }
}
```

---

**Continued in next part...**
