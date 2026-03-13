# 🦁 RastaCoder - App Renaming Summary

**Date:** March 13, 2026  
**Renamed From:** NavixMind/Coderasta  
**Renamed To:** RastaCoder

---

## ✅ COMPLETED CHANGES

### 1. Python Package ✅
- **Old:** `python/coderasta/`
- **New:** `python/rastacoder/`
- **Status:** Directory renamed, all imports updated

### 2. Android Application ✅
- **Old Package:** `ai.coderasta`
- **New Package:** `ai.rastacoder`
- **Namespace:** Updated in `android/app/build.gradle`
- **Application ID:** Updated in `android/app/build.gradle`
- **Kotlin Files:** Package directory renamed, all references updated

### 3. Flutter/Dart Code ✅
- **Package Name:** `rastacoder` (in `pubspec.yaml`)
- **Method Channels:** Updated to `ai.rastacoder/*`
  - `ai.rastacoder/python_bridge`
  - `ai.rastacoder/python_events`
  - `ai.rastacoder/model_download`
  - `ai.rastacoder/model_download_events`
  - `ai.rastacoder/mlc_inference`
  - `ai.rastacoder/file_opener`
  - `ai.rastacoder/share_receiver`

### 4. Documentation ✅
- **README.md:** Updated app name and description
- **QWEN.md:** Updated project context
- **GitHub Links:** Updated to `alexandertaboriskiy/rastacoder`
- **Website:** Updated to `rastacoder.ai`

---

## 📁 FILES MODIFIED

### Configuration Files
- [x] `pubspec.yaml` - Package name and description
- [x] `android/app/build.gradle` - Namespace and applicationId
- [x] `python/rastacoder/__init__.py` - Package docstring

### Dart/Flutter Files
- [x] `lib/core/bridge/bridge.dart` - Method/Event channels
- [x] `lib/core/services/share_receiver_service.dart` - Channel name
- [x] `lib/core/services/local_llm_service.dart` - Channel names
- [x] `lib/features/chat/presentation/widgets/message_bubble.dart` - Channel name

### Kotlin Files (All in `android/app/src/main/kotlin/ai/rastacoder/`)
- [x] `MainActivity.kt` - Package and channel references
- [x] `PythonMethodChannel.kt` - Package and channel names
- [x] `services/ModelDownloadChannel.kt` - Package and constants
- [x] `services/MLCInferenceChannel.kt` - Package and constants
- [x] `services/ForegroundServiceChannel.kt` - Package and constants
- [x] `services/TaskForegroundService.kt` - Package and action names

### Python Files
- [x] All files in `python/rastacoder/` - Import statements updated
- [x] All files in `python/tests/` - Import statements updated

### Documentation
- [x] `README.md` - App name, description, links
- [x] `QWEN.md` - Project context, package references
- [x] `LINT_REPORT.md` - (Reference only, not critical)
- [x] `APK_OPTIMIZATION_GUIDE.md` - (Reference only, not critical)
- [x] `TASK_COMPLETION_REPORT.md` - (Reference only, not critical)

---

## 🔄 MIGRATION GUIDE

### For Developers

1. **Pull Latest Changes:**
   ```bash
   cd ~/navixmind
   git pull
   ```

2. **Clean Build:**
   ```bash
   flutter clean
   cd android && ./gradlew clean
   cd ..
   ```

3. **Rebuild:**
   ```bash
   flutter pub get
   flutter build apk --debug
   ```

### For Existing Installations

⚠️ **Important:** The application ID has changed from `ai.coderasta` to `ai.rastacoder`.

- **New Install:** Will work normally
- **Existing Users:** Must uninstall old version first (different package ID)
- **Data Migration:** User data will NOT be automatically migrated (different package)

---

## 🎯 BRANDING UPDATES

### User-Facing Changes
| Element | Old | New |
|---------|-----|-----|
| App Name | NavixMind | RastaCoder |
| Package | Coderasta | RastaCoder |
| App ID | ai.coderasta | ai.rastacoder |
| Website | navixmind.ai | rastacoder.ai |
| GitHub | navixmind | rastacoder |
| Discord | navixmind | rastacoder |
| Support | support@navixmind.ai | support@rastacoder.ai |

### Internal References
| Component | Old | New |
|-----------|-----|-----|
| Python Package | coderasta | rastacoder |
| Kotlin Package | ai.coderasta | ai.rastacoder |
| Method Channels | ai.coderasta/* | ai.rastacoder/* |

---

## 📝 REMAINING TASKS

### Content Updates (Optional)
- [ ] Update README.md links (Discord, Instagram, etc.)
- [ ] Update website references throughout docs
- [ ] Update social media handles in documentation
- [ ] Update GitHub repo references

### App Store Considerations
- [ ] **Play Store:** New listing required (different package ID)
- [ ] **GitHub:** Create new repository or rename existing
- [ ] **Domain:** Register rastacoder.ai
- [ ] **Social Media:** Update handles/profiles

---

## 🔧 TECHNICAL NOTES

### Package Structure
```
navixmind/
├── android/
│   └── app/
│       └── src/main/kotlin/ai/
│           └── rastacoder/          ← Renamed from coderasta
│               ├── MainActivity.kt
│               ├── PythonMethodChannel.kt
│               └── services/
├── python/
│   └── rastacoder/                  ← Renamed from coderasta
│       ├── __init__.py
│       ├── agent.py
│       ├── bridge.py
│       └── tools/
├── lib/
│   └── core/
│       └── bridge/
│           └── bridge.dart          ← Channel names updated
└── docs/
    └── (documentation to update)
```

### Channel Naming Convention
All Method/Event channels now follow: `ai.rastacoder/<service>`

| Channel | Type | Purpose |
|---------|------|---------|
| `ai.rastacoder/python_bridge` | MethodChannel | Flutter ↔ Python communication |
| `ai.rastacoder/python_events` | EventChannel | Python → Flutter events |
| `ai.rastacoder/model_download` | MethodChannel | LLM model download control |
| `ai.rastacoder/model_download_events` | EventChannel | Download progress updates |
| `ai.rastacoder/mlc_inference` | MethodChannel | MLC LLM inference |
| `ai.rastacoder/file_opener` | MethodChannel | Native file operations |
| `ai.rastacoder/share_receiver` | MethodChannel | Android share intent handling |

---

## ✅ VERIFICATION CHECKLIST

- [x] Python package renamed
- [x] Android package renamed
- [x] Flutter package renamed
- [x] All channel references updated
- [x] All import statements updated
- [x] Build configuration updated
- [x] Documentation updated (core files)
- [ ] Full build test required
- [ ] App run test required
- [ ] Python bridge test required

---

## 🚀 NEXT STEPS

1. **Test Build:**
   ```bash
   flutter build apk --debug
   ```

2. **Test App:**
   - Install on device
   - Verify Python bridge works
   - Test offline LLM functionality
   - Test all tools

3. **Update Remaining Docs:**
   - Rename documentation files
   - Update internal references

4. **Deploy:**
   - Push to GitHub
   - Update CI/CD pipelines
   - Deploy to testing track

---

**Renaming Completed By:** Qwen Code Agent  
**Status:** ✅ Core Renaming Complete  
**Build Status:** ⏳ Needs Testing

*Baker Street Laboratory © 2026* 🔱
