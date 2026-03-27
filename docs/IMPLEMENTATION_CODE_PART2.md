# Python Jedi Setup - Continuation of Implementation

## FILE 4: Python Jedi Service

**File:** `lib/core/services/python_jedi_service.dart`

```dart
import 'dart:convert';
import 'package:flutter/services.dart';
import '../bridge/bridge.dart';

class PythonJediService {
  static final _instance = PythonJediService._internal();
  factory PythonJediService() => _instance;
  PythonJediService._internal();

  static const _channel = MethodChannel('ai.rastacoder/python_jedi');
  
  bool _isInstalled = false;
  bool _isInstalling = false;
  String? _jediVersion;

  bool get isInstalled => _isInstalled;
  bool get isInstalling => _isInstalling;
  String? get jediVersion => _jediVersion;

  Future<void> initialize() async => await _checkJediStatus();

  Future<void> _checkJediStatus() async {
    try {
      final result = await PythonBridge.instance.sendQueryToPython(
        'import jedi; print(jedi.__version__)', {},
      );
      if (result != null && result.toString().isNotEmpty) {
        _isInstalled = true;
        _jediVersion = result.toString().trim();
        debugPrint('Jedi installed: v$_jediVersion');
      }
    } catch (e) {
      _isInstalled = false;
      debugPrint('Jedi not installed: $e');
    }
  }

  Future<bool> installUv({Function(String)? onLog}) async {
    if (_isInstalling) return false;
    _isInstalling = true;
    onLog?.call('🚀 Installing UV package manager...');
    
    try {
      final installCode = '''
import subprocess, sys
try:
    result = subprocess.run([sys.executable, "-m", "pip", "install", "uv", "-q"],
        capture_output=True, text=True, timeout=60)
    if result.returncode == 0:
        print("✓ UV installed successfully")
    else:
        print("✗ Failed: " + result.stderr)
except Exception as e:
    print(f"✗ Error: {e}")
''';
      final result = await PythonBridge.instance.sendQueryToPython(installCode, {});
      if (result != null && result.toString().contains('✓')) {
        onLog?.call('✅ UV installed!');
        _isInstalling = false;
        return true;
      }
      onLog?.call('❌ UV installation failed');
      _isInstalling = false;
      return false;
    } catch (e) {
      onLog?.call('❌ Error: $e');
      _isInstalling = false;
      return false;
    }
  }

  Future<bool> installJedi({Function(String)? onLog}) async {
    if (_isInstalling) return false;
    _isInstalling = true;
    onLog?.call('🧙 Installing Python Jedi...');
    
    try {
      final installCode = '''
import subprocess, sys
try:
    result = subprocess.run([sys.executable, "-m", "pip", "install", "jedi", "-q"],
        capture_output=True, text=True, timeout=60)
    if result.returncode == 0:
        import jedi
        print(f"✓ Jedi installed: v{jedi.__version__}")
    else:
        print("✗ Failed: " + result.stderr)
except Exception as e:
    print(f"✗ Error: {e}")
''';
      final result = await PythonBridge.instance.sendQueryToPython(installCode, {});
      if (result != null && result.toString().contains('✓')) {
        onLog?.call('✅ Jedi installed!');
        await _checkJediStatus();
        _isInstalling = false;
        return true;
      }
      onLog?.call('❌ Jedi installation failed');
      _isInstalling = false;
      return false;
    } catch (e) {
      onLog?.call('❌ Error: $e');
      _isInstalling = false;
      return false;
    }
  }

  Future<bool> installCompleteSetup({Function(String)? onLog}) async {
    onLog?.call('🚀 Starting Python Jedi setup...\n');
    final uvSuccess = await installUv(onLog: onLog);
    if (!uvSuccess) return false;
    await Future.delayed(const Duration(seconds: 1));
    return await installJedi(onLog: onLog);
  }

  Future<List<Map<String, dynamic>>> getCompletions(String code, int line, int column) async {
    if (!_isInstalled) return [];
    try {
      final jediCode = '''
import jedi, json
code = ${json.dumps(code)}
script = jedi.Script(code, path='example.py')
completions = script.complete(line=$line, column=$column)
results = [{'name': c.name, 'type': c.type, 'docstring': (c.docstring() or '')[:200]} for c in completions[:20]]
print(json.dumps(results))
''';
      final result = await PythonBridge.instance.sendQueryToPython(jediCode, {});
      if (result != null) {
        return (json.decode(result.toString()) as List).cast<Map<String, dynamic>>();
      }
    } catch (e) {
      debugPrint('Jedi completion error: $e');
    }
    return [];
  }

  Future<bool> uninstallJedi({Function(String)? onLog}) async {
    try {
      final uninstallCode = '''
import subprocess, sys
result = subprocess.run([sys.executable, "-m", "pip", "uninstall", "jedi", "-y", "-q"],
    capture_output=True, text=True)
print("✓ Jedi uninstalled" if result.returncode == 0 else "✗ Failed")
''';
      await PythonBridge.instance.sendQueryToPython(uninstallCode, {});
      _isInstalled = false;
      _jediVersion = null;
      onLog?.call('✅ Jedi uninstalled');
      return true;
    } catch (e) {
      onLog?.call('❌ Error: $e');
      return false;
    }
  }
}
```

---

## FILE 5: Native Android SystemInfo Channel

**File:** `android/app/src/main/kotlin/ai/rastacoder/services/SystemInfoChannel.kt`

```kotlin
package ai.rastacoder.services

import android.app.ActivityManager
import android.content.Context
import android.os.Build
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import java.io.File

class SystemInfoChannel(flutterEngine: FlutterEngine, private val context: Context) {
    private val channel = MethodChannel(
        flutterEngine.dartExecutor.binaryMessenger,
        "ai.rastacoder/system_info"
    )

    init {
        channel.setMethodCallHandler { call, result ->
            when (call.method) {
                "getRamInfo" -> getRamInfo(result)
                "getDeviceInfo" -> getDeviceInfo(result)
                "getCpuInfo" -> getCpuInfo(result)
                "getGpuInfo" -> getGpuInfo(result)
                else -> result.notImplemented()
            }
        }
    }

    private fun getRamInfo(result: MethodChannel.Result) {
        try {
            val activityManager = context.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
            val memInfo = ActivityManager.MemoryInfo()
            activityManager.getMemoryInfo(memInfo)
            val totalMB = memInfo.totalMem / (1024 * 1024)
            val availableMB = memInfo.availMem / (1024 * 1024)
            result.success(mapOf(
                "totalMB" to totalMB,
                "availableMB" to availableMB,
                "percentAvailable" to (availableMB.toDouble() / totalMB * 100)
            ))
        } catch (e: Exception) {
            result.error("RAM_ERROR", e.message, null)
        }
    }

    private fun getDeviceInfo(result: MethodChannel.Result) {
        try {
            result.success(mapOf(
                "androidVersion" to Build.VERSION.RELEASE,
                "model" to Build.MODEL,
                "manufacturer" to Build.MANUFACTURER,
                "brand" to Build.BRAND,
                "sdkVersion" to Build.VERSION.SDK_INT
            ))
        } catch (e: Exception) {
            result.error("DEVICE_ERROR", e.message, null)
        }
    }

    private fun getCpuInfo(result: MethodChannel.Result) {
        try {
            val cores = Runtime.getRuntime().availableProcessors()
            var speedMhz = 2000
            try {
                val cpuFile = File("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq")
                if (cpuFile.exists()) {
                    speedMhz = cpuFile.readText().trim().toInt() / 1000
                }
            } catch (e: Exception) { }
            result.success(mapOf(
                "cores" to cores,
                "speedMhz" to speedMhz,
                "speedGhz" to speedMhz / 1000.0
            ))
        } catch (e: Exception) {
            result.error("CPU_ERROR", e.message, null)
        }
    }

    private fun getGpuInfo(result: MethodChannel.Result) {
        try {
            result.success(mapOf(
                "hasGpu" to true,
                "model" to "Unknown",
                "renderer" to android.opengl.GLES20.glGetString(android.opengl.GLES20.GL_RENDERER)
            ))
        } catch (e: Exception) {
            result.success(mapOf("hasGpu" to false, "model" to null, "renderer" to null))
        }
    }
}
```

---

## FILE 6: Register in MainActivity

**File:** `android/app/src/main/kotlin/ai/rastacoder/MainActivity.kt`

Add to `configureFlutterEngine`:

```kotlin
override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
    super.configureFlutterEngine(flutterEngine)
    // ... existing code ...
    
    // Register SystemInfo channel
    val systemInfoChannel = SystemInfoChannel(flutterEngine, applicationContext)
}
```

---

## FILE 7: Python Jedi Setup Script

**File:** `python/rastacoder/jedi_setup.py`

```python
"""Jedi Setup - Python code intelligence for RastaCoder"""

import subprocess
import sys
from typing import Optional, Callable

class JediSetup:
    def __init__(self):
        self.python_executable = sys.executable
        self.is_installed = False
        self.jedi_version: Optional[str] = None
    
    def check_jedi_installed(self) -> bool:
        try:
            import jedi
            self.jedi_version = jedi.__version__
            self.is_installed = True
            return True
        except ImportError:
            self.is_installed = False
            return False
    
    def install_uv(self, log_callback: Optional[Callable[[str], None]] = None) -> bool:
        if log_callback: log_callback("🚀 Installing UV...")
        try:
            result = subprocess.run(
                [self.python_executable, "-m", "pip", "install", "uv", "-q"],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                if log_callback: log_callback("✅ UV installed!")
                return True
            if log_callback: log_callback(f"❌ Failed: {result.stderr}")
            return False
        except Exception as e:
            if log_callback: log_callback(f"❌ Error: {e}")
            return False
    
    def install_jedi(self, log_callback: Optional[Callable[[str], None]] = None) -> bool:
        if log_callback: log_callback("🧙 Installing Jedi...")
        try:
            result = subprocess.run(
                [self.python_executable, "-m", "pip", "install", "jedi", "-q"],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                import jedi
                self.jedi_version = jedi.__version__
                self.is_installed = True
                if log_callback: log_callback(f"✅ Jedi v{self.jedi_version} installed!")
                return True
            if log_callback: log_callback(f"❌ Failed: {result.stderr}")
            return False
        except Exception as e:
            if log_callback: log_callback(f"❌ Error: {e}")
            return False
    
    def install_complete_setup(self, log_callback: Optional[Callable[[str], None]] = None) -> bool:
        if log_callback: log_callback("🚀 Starting Python Jedi setup...\n")
        if not self.install_uv(log_callback=log_callback): return False
        import time; time.sleep(1)
        return self.install_jedi(log_callback=log_callback)
    
    def get_completions(self, code: str, line: int, column: int) -> list:
        if not self.is_installed: return []
        try:
            import jedi
            script = jedi.Script(code, path='example.py')
            completions = script.complete(line=line, column=column)
            return [{'name': c.name, 'type': c.type, 'docstring': (c.docstring() or '')[:200]} 
                    for c in completions[:20]]
        except Exception as e:
            print(f"Jedi error: {e}")
            return []
```

---

## USAGE

### 1. Manual Model Selection:
```dart
await Navigator.push(context, MaterialPageRoute(builder: (_) => ModelSelectorScreen()));
```

### 2. Auto System Scan:
```dart
final info = await SystemScannerService().scanSystem();
print('Device: ${info.deviceTier}, RAM: ${info.availableRamGB}GB');
```

### 3. Python Jedi Setup:
```dart
await PythonJediService().installCompleteSetup(onLog: print);
```

**All code complete!** 🦁
