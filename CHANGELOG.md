# Changelog

All notable changes to RastaCoder (formerly NavixMind) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-03-27

### 🎉 Production Release

**The AI assistant that runs entirely on your phone — no internet required.**

### ✨ Added

#### Core Features
- **On-Device LLM Support** - Run Qwen2.5-Coder models (0.5B, 1.5B, 3B) offline via MLC LLM
- **Cloud AI Integration** - Claude API support (Opus 4.6, Sonnet 4.5, Haiku 4.5)
- **Python 3.10 Runtime** - Embedded via Chaquopy for on-device code execution
- **ReAct Agent Loop** - Reasoning + Action pattern for complex multi-step tasks
- **Dual AI Modes** - Switch between cloud and offline modes seamlessly

#### Tools & Capabilities
- **FFmpeg Integration** - Video/audio processing (compress, convert, extract, split)
- **Image Processing** - Concat, overlay, resize, crop, adjust, grayscale, blur
- **Document Handling** - PDF, DOCX, Excel, PowerPoint read/create/convert
- **Web Integration** - HTTP requests, headless browser for JS-heavy sites
- **Google Services** - Calendar and Gmail integration (optional)
- **Data Analysis** - pandas and matplotlib for data processing and visualization
- **OCR** - ML Kit integration for text extraction from images
- **Interactive HTML** - Create mobile-optimized games, apps, animations with touch controls

#### Self-Improvement
- **Prompt Learning** - Agent can analyze successful workflows and update its own system prompt
- **Context Management** - Automatic summarization for long conversations

#### UI/UX
- **Rasta Theme** - Cyber-Clean dark theme with Rastafarian vibes (red, gold, green accents)
- **Chat Interface** - Real-time message streaming with typing indicators
- **Settings Screen** - Configure AI mode, models, timeouts, limits
- **Onboarding Flow** - Terms of Service and Privacy Policy acceptance
- **Status Banner** - Live connection status and model info display

#### Security & Privacy
- **Secure Storage** - API keys encrypted via Flutter Secure Storage
- **Local-First** - All processing on-device by default
- **No Data Collection** - Zero telemetry, no analytics
- **Open Source** - Full transparency, Apache 2.0 license

### 🔧 Technical

#### Architecture
- **Flutter 3.x** - Cross-platform UI framework
- **Kotlin Bridge** - MethodChannel/EventChannel for native communication
- **JSON-RPC Protocol** - Clean separation between Python logic and Flutter UI
- **MLC LLM Engine** - GPU-accelerated on-device inference
- **Chaquopy** - Python runtime embedded in APK

#### Model Downloads
- **Resumable Downloads** - OkHttp with chunked download support
- **HuggingFace Integration** - Direct model fetching with progress tracking
- **Model Management** - Download, delete, switch models from Settings

#### Performance
- **Memory Monitoring** - Automatic cleanup for low-RAM devices
- **Lazy Loading** - Models load on-demand, not at app startup
- **GPU Acceleration** - MLC LLM uses Vulkan/Metal for inference

### 📦 Changed

- **Rebrand** - NavixMind → RastaCoder (Rastafarian theme)
- **Default Model** - Claude Sonnet 4.5 (balanced cost/performance)
- **Tool Timeout** - Increased default to 30s for complex operations
- **Max Steps** - Increased to 50 for extended reasoning

### 🐛 Fixed

- **JSON Repair** - Auto-repair malformed JSON from small on-device models
- **Memory Leaks** - Fixed in MLC inference channel
- **Connection State** - Proper event streaming for bridge status
- **Error Messages** - User-friendly error formatting

### 📚 Documentation

- **README.md** - Comprehensive setup and usage guide
- **BUILD_GUIDE.md** - Detailed build instructions
- **APK_OPTIMIZATION_GUIDE.md** - Size optimization techniques
- **ANDROID_ROMS_ANALYSIS.md** - Custom ROM compatibility research
- **KAGGLE_SHIZUKU_RESEARCH.md** - Android automation research

---

## [0.5.2-beta] - 2026-03-20

### Added
- MLC LLM integration for on-device inference
- Model download manager with progress tracking
- Settings screen for AI configuration
- Qwen2.5-Coder model support (0.5B, 1.5B, 3B)

### Changed
- Improved error handling in Python bridge
- Better progress reporting for long operations

### Fixed
- Connection state synchronization
- Memory management in MLC inference

---

## [0.5.1-beta] - 2026-03-15

### Added
- Python code executor with ReAct agent
- FFmpeg tool integration
- Basic chat interface

### Fixed
- Initial bug fixes in JSON-RPC bridge

---

## [0.5.0-beta] - 2026-03-10

### Added
- Initial beta release
- Core Python runtime integration
- Claude API support
- Basic tool framework

---

## [0.4.0] - 2026-03-01

### Added
- Project foundation
- Flutter app structure
- Python bridge prototype

---

## [Unreleased]

### Planned for v1.1.0
- iOS support (alternative Python embedding)
- Additional on-device models (Ministral-3B, Qwen3-4B)
- Plugin system for custom tools
- Workflow templates library
- Backup/restore functionality

### Under Consideration
- WebAssembly Python runtime for iOS
- Federated learning for prompt improvements
- P2P model sharing between devices

---

## Version History

| Version | Release Date | Type | Key Feature |
|---------|--------------|------|-------------|
| 0.4.0 | 2026-03-01 | Stable | Foundation |
| 0.5.0-beta | 2026-03-10 | Beta | Python runtime |
| 0.5.1-beta | 2026-03-15 | Beta | ReAct agent |
| 0.5.2-beta | 2026-03-20 | Beta | MLC LLM |
| **1.0.0** | **2026-03-27** | **Production** | **Full release** |

---

## Migration Guide

### From v0.5.x to v1.0.0

No breaking changes. Upgrade is seamless:

1. Install v1.0.0 APK over existing installation
2. Your settings and API keys are preserved
3. Download on-device models again if using offline mode (model format unchanged)

### For Developers

- Package name unchanged: `com.navixmind.rastacoder`
- API structure unchanged
- Python tool interface unchanged

---

## Support

- **Issues:** https://github.com/alexandertaboriskiy/rastacoder/issues
- **Discord:** https://discord.gg/navixmind
- **Email:** support@rastacoder.ai
- **Website:** https://rastacoder.ai

---

*Jah Rastafari! 🦁🇯🇲*
