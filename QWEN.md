# 🚀 RastaCoder — AI Development Context

**Project:** RastaCoder — Offline-First AI Assistant for Android  
**Version:** 1.0.0+1  
**Package:** `ai.rastacoder`  
**Location:** `~/navixmind/`  
**Status:** Production Ready (v0.5.2+16)

---

## 📋 PROJECT OVERVIEW

RastaCoder is a **revolutionary Android AI assistant** that runs 100% offline using embedded Python 3.10 and local LLMs. Unlike cloud-based AI apps, RastaCoder performs iterative, multi-step tasks with local file manipulation — no internet required.

### Unique Value Proposition
> "The only AI assistant that runs **entirely on your phone** — process files, execute Python, create content. All offline."

### Core Capabilities
- **Offline AI** — Qwen2.5-Coder models (0.5B/1.5B/3B/4B) via MLC LLM, no internet needed
- **Cloud AI** — Claude API integration (Opus 4.6/Sonnet 4.5/Haiku 4.5)
- **Python Runtime** — Full Python 3.10 embedded via Chaquopy
- **Media Processing** — FFmpeg for video/audio manipulation
- **Document Handling** — PDF, DOCX, Excel, PowerPoint
- **Web Integration** — Browser automation, scraping
- **Google Services** — Calendar, Gmail (optional)
- **Self-Improvement** — Agent learns from successful workflows

---

## 🏗️ ARCHITECTURE

```
┌──────────────────────────────────────────────────────────────┐
│                       Flutter UI                              │
│                 (Cyber-Clean dark theme)                       │
├──────────────────────────────────────────────────────────────┤
│                     Kotlin Bridge                              │
│            (MethodChannel / EventChannel)                      │
├──────────────┬───────────────────────────────────────────────┤
│  MLC LLM     │           Python 3.10 (Chaquopy)               │
│  Engine      │  ┌─────────────┐ ┌──────────┐ ┌───────────┐  │
│  (On-Device) │  │ ReAct Agent │ │  Tools   │ │ Libraries │  │
│  ┌─────────┐ │  │ Claude API  │ │ (Web,    │ │ (requests,│  │
│  │ Qwen2.5 │◄├──┤   — or —   │ │  PDF,    │ │  pypdf,   │  │
│  │ Coder   │ │  │ Local LLM  │ │  FFmpeg) │ │  pandas)  │  │
│  └─────────┘ │  └─────────────┘ └──────────┘ └───────────┘  │
├──────────────┴───────────────────────────────────────────────┤
│                   Native Tools (Flutter)                       │
│          FFmpeg  │  OCR (ML Kit)  │  File Sharing              │
└──────────────────────────────────────────────────────────────┘
```

### Key Design Decisions
- **Python runs inside the APK** — no server, no cloud dependency
- **Dual inference paths** — Claude API (cloud) or MLC LLM (on-device)
- **Native tools for performance** — FFmpeg runs on Flutter side
- **JSON-RPC bridge** — clean separation between Python logic and native execution
- **ReAct agent loop** — model reasons, acts, observes, repeats

---

## 📁 PROJECT STRUCTURE

```
navixmind/
├── lib/                          # Flutter/Dart code
│   ├── app/                      # App setup, theme, routes
│   │   ├── app.dart              # Main MaterialApp widget
│   │   └── theme.dart            # Cyber-Clean theme (dark)
│   ├── core/
│   │   ├── bridge/               # Python↔Flutter JSON-RPC bridge
│   │   │   └── bridge.dart       # PythonBridge class
│   │   ├── constants/            # App constants
│   │   ├── database/             # Isar database setup
│   │   ├── models/               # Data models (Isar entities)
│   │   └── services/             # Core services
│   │       ├── analytics_service.dart
│   │       ├── auth_service.dart
│   │       ├── connectivity_service.dart
│   │       ├── cost_manager.dart
│   │       ├── crash_detector.dart
│   │       ├── local_llm_service.dart    # MLC LLM integration
│   │       ├── native_tool_executor.dart # FFmpeg, OCR, etc.
│   │       ├── offline_queue_manager.dart
│   │       └── share_receiver_service.dart
│   ├── features/                 # UI screens by feature
│   │   ├── chat/                 # Main chat interface
│   │   ├── legal/                # ToS, Privacy Policy
│   │   ├── onboarding/           # First-run experience
│   │   └── settings/             # App settings
│   ├── shared/                   # Shared widgets
│   └── main.dart                 # App entry point
├── python/                       # Python agent code
│   └── rastacoder/               # ReAct agent implementation
│       ├── __init__.py
│       ├── agent.py              # Main ReAct loop, Claude client
│       ├── bridge.py             # Flutter↔Python communication
│       ├── session.py            # Session management
│       ├── crash_logger.py       # Error logging
│       ├── tracing.py            # Mentiora tracing
│       ├── rasta_philosophy.py   # Rasta philosophy
│       └── tools/                # Tool implementations
│           ├── __init__.py       # Tool registry
│           ├── python_execute.py
│           ├── ffmpeg_process.py
│           ├── image_compose.py
│           ├── web_fetch.py
│           ├── read_pdf.py
│           ├── create_pdf.py
│           ├── read_docx.py
│           ├── modify_pptx.py
│           ├── google_calendar.py
│           └── ...
├── android/
│   ├── app/
│   │   ├── src/main/
│   │   │   ├── kotlin/           # Kotlin bridge code
│   │   │   ├── AndroidManifest.xml
│   │   │   └── res/
│   │   ├── build.gradle          # Android build config
│   │   └── google-services.json  # Firebase config
│   ├── mlc4j/                    # MLC LLM native library
│   ├── build.gradle              # Root build config
│   ├── gradle.properties
│   └── key.properties.example    # Signing config template
├── test/                         # Dart tests
├── python/tests/                 # Python tests
├── www/                          # Website (rastacoder.ai)
├── docs/                         # Documentation
│   ├── RASTACODER_BLUEPRINT.md
│   ├── RASTACODER_LAUNCH_CHECKLIST.md
│   ├── RASTACODER_QUICK_LAUNCH.md
│   └── rastacoder_monetization_analysis.ipynb
├── mlc-package-config.json       # MLC model registry
├── pubspec.yaml                  # Flutter dependencies
├── requirements.txt              # Python dependencies
├── analysis_options.yaml         # Dart linter rules
└── upload_queries.py             # Dataset upload script
```

---

## 🛠️ TECH STACK

| Layer | Technology |
|-------|------------|
| **UI Framework** | Flutter 3.x (Dart) |
| **Python Runtime** | Chaquopy 16.0.0 |
| **Cloud AI** | Claude API (Anthropic) |
| **On-Device AI** | MLC LLM + Qwen2.5-Coder (q4f16_0) |
| **Video/Audio** | FFmpeg Kit |
| **Database** | Isar |
| **Secure Storage** | Flutter Secure Storage |
| **Model Downloads** | OkHttp (chunked, resumable) |
| **Analytics** | Firebase Analytics + Crashlytics |
| **Auth** | Google Sign-In + Firebase Auth |

### Available On-Device Models

| Model | Size | RAM Required | Best For |
|-------|------|-------------|----------|
| Qwen2.5-Coder-0.5B | ~400MB | 2GB+ | Quick tasks, low-end devices |
| Qwen2.5-Coder-1.5B | ~1GB | 4GB+ | Balanced speed and quality |
| Qwen2.5-Coder-3B | ~2GB | 6GB+ | Best coding quality |
| Ministral-3B | ~2GB | 6GB+ | Best general quality, tool-use capable |
| Qwen3-4B | ~2.5GB | 6GB+ | Extended thinking, strongest offline model |

All models are quantized to `q4f16_0` (4-bit weights, 16-bit activations).

---

## 🚀 BUILDING & RUNNING

### Prerequisites
- Flutter SDK 3.x
- Java 17 (`JAVA_HOME` set)
- Android SDK (API 24+)
- Android NDK 25.1.8937393
- CMake, Rust (for MLC LLM)
- Python 3.10+ (for building MLC)

### Installation

```bash
# Clone repository
git clone https://github.com/alexandertaboriskiy/rastacoder.git
cd rastacoder

# Install Flutter dependencies
flutter pub get

# Build MLC LLM native libraries (required for on-device inference)
pip install --pre -U -f https://mlc.ai/wheels mlc-llm-nightly mlc-ai-nightly
mlc_llm package --config mlc-package-config.json
cp -r dist/lib/mlc4j/ android/mlc4j/

# Build debug APK
export JAVA_HOME="/path/to/jdk17"
flutter build apk --debug

# Install on connected device
adb install build/app/outputs/flutter-apk/app-debug.apk
```

### Build Commands

```bash
# Debug build
flutter build apk --debug

# Release build
flutter build apk --release

# App bundle (Play Store)
flutter build appbundle --release

# Clean build
flutter clean && flutter pub get

# Run on device
flutter run
```

### Running Tests

```bash
# Flutter tests
flutter test

# Python tests
cd python && pytest

# With coverage
cd python && pytest --cov=coderasta
```

### Debug Logging

```bash
# View Flutter/Python logs
adb logcat -s flutter,PythonBridge,NativeToolResponse

# Clear logs
adb logcat -c
```

---

## 🧪 TESTING PRACTICES

### Flutter Tests
- Location: `test/`
- Framework: `flutter_test` + `mocktail`
- Run: `flutter test`

### Python Tests
- Location: `python/tests/`
- Framework: `pytest` + `pytest-cov`
- Run: `cd python && pytest`

### Test Conventions
- Unit tests for core logic
- Integration tests for bridge communication
- Mock external services (Claude API, Google)
- Test both cloud and offline modes

---

## 📝 DEVELOPMENT CONVENTIONS

### Coding Style

**Dart/Flutter:**
- Follow Effective Dart guidelines
- Use `const` constructors where possible
- Prefer `final` over `var`
- Trailing commas in multi-line collections
- Avoid `print()` — use `debugPrint()` or analytics

**Python:**
- PEP 8 compliant
- Type hints for public APIs
- Docstrings for functions/classes
- ReAct pattern for agent logic

**Kotlin:**
- Kotlin style guide
- Null safety with `?.` and `?:`
- Coroutines for async operations

### Git Workflow

```bash
# Feature branches
git checkout -b feature/offline-model-download
git commit -m "feat: add resumable model downloads"
git push origin feature/offline-model-download
```

### Commit Messages
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `refactor:` Code refactoring
- `test:` Tests
- `chore:` Maintenance

### Linting

```bash
# Dart analysis
flutter analyze

# Python linting (if configured)
cd python && flake8 rastacoder
```

---

## 🔑 CONFIGURATION

### Firebase Setup
1. Download `google-services.json` from Firebase Console
2. Place in `android/app/`
3. Enable: Analytics, Crashlytics, Auth

### Signing Configuration

```bash
# Create key.properties from template
cp android/key.properties.example android/key.properties

# Edit with your keystore details
# storePassword=xxx
# keyPassword=xxx
# keyAlias=upload
# storeFile=/path/to/keystore.jks
```

### API Keys
- **Claude API:** User-provided in Settings (cloud mode)
- **Google Services:** OAuth via Firebase Auth
- **Mentiora Tracing:** Optional, set in settings

---

## 🎯 AVAILABLE TOOLS (Python Agent)

| Tool | Description |
|------|-------------|
| `python_execute` | Run Python code (math, pandas, matplotlib, etc.) |
| `ffmpeg_process` | Video/audio processing (trim, crop, convert, filter) |
| `image_compose` | Image manipulation (concat, overlay, resize, adjust) |
| `smart_crop` | Smart crop video/image to focus on faces |
| `ocr_image` | Extract text from images (ML Kit) |
| `web_fetch` | Fetch webpage and extract text/HTML |
| `headless_browser` | JavaScript-heavy page automation |
| `read_pdf` / `create_pdf` | PDF handling |
| `read_docx` / `modify_docx` | Word document handling |
| `read_pptx` / `modify_pptx` | PowerPoint handling |
| `read_xlsx` / `modify_xlsx` | Excel handling |
| `convert_document` | Convert between DOCX/PDF/HTML/TXT |
| `create_zip` | Create ZIP archives |
| `download_media` | Download video/audio (not YouTube) |
| `google_calendar` | Query/create calendar events |
| `gmail` | Read Gmail messages |
| `list_files` | List files in device directories |
| `file_info` | Get file metadata |
| `read_file` / `write_file` | Generic file I/O |

---

## 🔒 SECURITY PRACTICES

### API Key Management
- Claude API key stored in `flutter_secure_storage`
- Never commit API keys to repository
- Use environment variables for development

### Android Security
- ProGuard/R8 obfuscation (release builds)
- EncryptedSharedPreferences for tokens
- Network Security Configuration
- SSL pinning for sensitive APIs

### Privacy
- All processing happens on-device by default
- Cloud mode requires explicit API key
- Google services are opt-in
- See [Privacy Policy](https://navixmind.ai/privacy.html)

---

## 📊 MONETIZATION

| Tier | Price | Features |
|------|-------|----------|
| **Free** | $0 | Basic offline models, limited tool calls |
| **Pro** | $9.99/mo | Cloud AI (Claude), advanced tools, unlimited |
| **Enterprise** | $497/mo | Team licensing, priority support, custom features |

### Revenue Channels
- Direct APK sales (Gumroad)
- Google Play Store subscription
- Enterprise licensing

---

## 🔗 ESSENTIAL LINKS

### Documentation
- [Complete Blueprint](docs/RASTACODER_BLUEPRINT.md)
- [Launch Checklist](docs/RASTACODER_LAUNCH_CHECKLIST.md)
- [Quick Launch Guide](docs/RASTACODER_QUICK_LAUNCH.md)
- [Monetization Analysis](docs/rastacoder_monetization_analysis.ipynb)

### External Resources
- [Website](https://rastacoder.ai)
- [GitHub](https://github.com/alexandertaboriskiy/rastacoder)
- [Discord](https://discord.gg/rastacoder)
- [MLC LLM](https://llm.mlc.ai/)
- [Chaquopy](https://chaquo.com/chaquopy/)
- [Claude API](https://console.anthropic.com/)

---

## 🆘 TROUBLESHOOTING

### Build Fails

```bash
# Clean and rebuild
flutter clean
flutter pub get
cd android && ./gradlew clean
cd ..

# Check Java version
java -version  # Must be 17

# Check NDK version
cat android/local.properties  # ndk.version=25.1.8937393
```

### MLC LLM Issues

```bash
# Rebuild native libraries
mlc_llm package --config mlc-package-config.json
cp -r dist/lib/mlc4j/ android/mlc4j/

# Check model downloads
adb shell ls /data/data/ai.rastacoder/files/mlc/
```

### Python Bridge Issues

```bash
# Check Chaquopy installation
adb logcat -s chaquopy

# Restart app
adb shell am force-stop ai.rastacoder
```

### Memory Issues (Mobile Context)

```bash
# Check available RAM
free -m

# Clear Flutter build cache
flutter clean
rm -rf build/
```

---

## 📈 CURRENT STATUS

**Version:** 1.0.0+1  
**Build Status:** Production Ready  
**Next Milestone:** Launch on Gumroad/Play Store

### Known Limitations
- Android only (Chaquopy is Android-specific)
- On-device models require 2-6GB RAM
- iOS would require alternative Python embedding

### Future Enhancements
- iOS support (alternative Python runtime)
- Additional on-device models (Llama 3, Phi-3)
- Enhanced tool ecosystem
- Multi-language support

---

**Last Updated:** March 13, 2026  
**Maintained By:** Kiliaan Vanvoorden (@BoozeLee)  
**Contact:** support@rastacoder.ai

*Baker Street Laboratory © 2026* 🔱
