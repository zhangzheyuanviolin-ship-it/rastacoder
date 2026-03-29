# RastaCoder 🦁🌿

> **The AI assistant that runs 100% offline on Android — no internet required.**
> Built with Flutter · Powered by MLC LLM · Part of [Bakertreet Labs](https://github.com/Bakery-street-project)

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue?style=for-the-badge)](LICENSE)
[![Flutter](https://img.shields.io/badge/Flutter-3.x-02569B?style=for-the-badge&logo=flutter&logoColor=white)](https://flutter.dev)
[![Android](https://img.shields.io/badge/Android-API_24+-3DDC84?style=for-the-badge&logo=android&logoColor=white)](https://developer.android.com)
[![CI](https://github.com/BoozeLee/rastacoder/actions/workflows/ci.yml/badge.svg)](https://github.com/BoozeLee/rastacoder/actions/workflows/ci.yml)
[![Bakertreet Labs](https://img.shields.io/badge/Bakertreet_Labs-🧪-6366f1?style=for-the-badge)](https://github.com/Bakery-street-project)

---

## 🌟 What Makes RastaCoder Different?

Current mobile AI apps run on a **"remote runtime"** model. Great for chat — but they fail when tasks require:
- **Iterative loops** — checking results and retrying with adjusted parameters
- **Local file manipulation** — without uploading to cloud sandboxes
- **Multi-step workflows** — combining multiple tools in sequence
- **Privacy** — keeping your data on-device, forever

**RastaCoder fixes this** by embedding a full Python 3.10 runtime directly inside the APK via [Chaquopy](https://chaquo.com/chaquopy/), with on-device LLM inference via [MLC LLM](https://mlc.ai/). No API key, no internet, no cloud dependency.

> 💰 **Monetization:** Free tier available. Pro ($9.99/mo) unlocks cloud AI and advanced tools. Enterprise ($497/mo) for teams.

---

## 🎯 Example Use Cases

| Task | Cloud AI Apps | RastaCoder |
|------|---------------|------------|
| "Compress this video to under 25MB with best quality" | One-shot attempt, no feedback loop | Runs FFmpeg iteratively, adjusting bitrate until target is met |
| "Split this recording into 10-min MP3 segments and zip them" | Requires uploading huge files | Processes in-place, on-device |
| "Generate a PDF summary for each meeting tomorrow" | Cannot create/save files locally | Creates files directly on your phone |
| "Analyze this dataset and plot trends" | Sandboxed, no file access | pandas + matplotlib, runs locally |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Flutter UI                               │
│                  (Cyber-Clean dark theme)                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                    Kotlin Bridge
              (MethodChannel / EventChannel)
                           │
         ┌─────────────────┴──────────────────────┐
         │                                        │
┌────────▼────────┐                    ┌──────────▼──────────────┐
│  MLC LLM Engine │                    │  Python 3.10 (Chaquopy) │
│  (On-Device)    │                    │                         │
│                 │                    │  ┌────────────────────┐ │
│  Qwen2.5-Coder  │◄──── Claude API ──►│  │   ReAct Agent      │ │
│  Ministral-3B   │      (or local)    │  │   (tool-use loop)  │ │
│  Qwen3-4B       │                    │  └────────┬───────────┘ │
│                 │                    │           │             │
└─────────────────┘                    │  Tools: python_execute  │
                                       │  ffmpeg, OCR, requests  │
                                       │  pandas, pypdf, PIL     │
                                       └─────────────────────────┘
                           │
              Native Tools (Flutter)
         FFmpeg · OCR (ML Kit) · File Sharing
```

**Key design decisions:**
- **Python runs inside the APK** — no server, no cloud dependency
- **Dual inference paths** — Claude API (cloud) or MLC LLM (on-device), user's choice
- **Native tools for performance** — FFmpeg runs on Flutter side
- **JSON-RPC bridge** — clean separation between Python logic and native execution
- **ReAct agent loop** — model reasons, acts, observes, repeats

---

## ✨ Features

- 🔌 **Fully Offline AI** — Run Qwen2.5-Coder, Ministral-3B, or Qwen3-4B on-device via MLC LLM, no internet required
- ☁️ **Cloud AI** — Or use Claude API for maximum capability
- 🎮 **Interactive HTML & Games** — Create fullscreen mobile-optimized games, apps, and animations with touch controls
- 🖼️ **Image Manipulation** — concat, overlay, resize, adjust, crop, grayscale, blur via image_compose
- 🎬 **Video/Audio Processing** — crop, resize, extract audio, convert formats, adjust volume (FFmpeg)
- 📄 **Document Handling** — read/create PDFs, convert DOCX, Excel, PowerPoint
- 🌐 **Web Integration** — fetch pages, headless browser for JS-heavy sites
- 📅 **Google Services** — Calendar and Gmail integration (optional)
- 📊 **Data Analysis** — pandas and matplotlib for data processing and visualization
- 🧠 **Self-Improvement** — the agent can analyze successful workflows and update its own system prompt (opt-in)
- 🔑 **Your Choice** — bring your own Claude API key, or use offline models with zero cloud dependency

---

## 📱 On-Device LLM (Offline Mode)

RastaCoder can run entirely offline using on-device language models powered by [MLC LLM](https://llm.mlc.ai/). No API key, no internet connection — the model runs directly on your phone's GPU.

### Available Models

| Model | Size | RAM Required | Best For |
|-------|------|-------------|---------|
| Qwen2.5-Coder-0.5B | ~400MB | 2GB+ | Quick tasks, low-end devices |
| Qwen2.5-Coder-1.5B | ~1GB | 4GB+ | Balanced speed and quality |
| Qwen2.5-Coder-3B | ~2GB | 6GB+ | Best coding quality |
| Ministral-3B | ~2GB | 6GB+ | Best general quality, tool-use capable |
| Qwen3-4B | ~2.5GB | 6GB+ | Extended thinking, strongest offline model |

Models are quantized to `q4f16_0` (4-bit weights, 16-bit activations) for efficient mobile inference.

---

## 🚀 Getting Started

### Prerequisites

- Android device (API 24+)
- **Cloud mode:** [Claude API key](https://console.anthropic.com/) from Anthropic
- **Offline mode:** No API key or internet needed — download an on-device model from Settings

### Installation

**Option A: Download APK**
- Get the latest APK from [GitHub Releases](https://github.com/BoozeLee/rastacoder/releases)

**Option B: Google Play** (coming soon)

**Option C: Build from source**

```bash
# Clone the repository
git clone https://github.com/BoozeLee/rastacoder.git
cd rastacoder

# Install Flutter dependencies
flutter pub get

# Build debug APK
export JAVA_HOME="/path/to/jdk17"
flutter build apk --debug

# Install on connected device
adb install build/app/outputs/flutter-apk/app-debug.apk
```

---

## 📁 Project Structure

```
rastacoder/
├── lib/                          # Flutter/Dart code
│   ├── app/                      # App setup, theme, routes
│   └── core/
│       ├── bridge/               # Python↔Flutter JSON-RPC bridge
│       ├── models/               # Model registry (on-device LLM catalog)
│       ├── services/             # LocalLLMService, NativeToolExecutor
│       └── features/             # UI screens (chat, settings, legal)
├── python/
│   └── rastacoder/               # ReAct agent, tools, local LLM client
├── android/
│   ├── app/src/main/kotlin/      # Kotlin bridge, MLC inference, model downloads
│   └── mlc4j/                    # MLC LLM native library
├── test/                         # Dart tests
├── python/tests/                 # Python tests
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                # Flutter analyze · test · build
│   │   └── security.yml          # dart pub audit · semgrep
│   └── dependabot.yml
└── SECURITY.md
```

---

## 🔧 Tech Stack

| Layer | Technology |
|-------|------------|
| UI | Flutter 3.x |
| Python Runtime | Chaquopy (embedded in APK) |
| Cloud AI | Claude API (Anthropic) |
| On-Device AI | MLC LLM + Qwen2.5-Coder (q4f16_0) |
| Video/Audio | FFmpeg Kit |
| Database | Isar |
| Secure Storage | Flutter Secure Storage |
| Model Downloads | OkHttp (chunked, resumable) |

---

## 🔒 Security

See [SECURITY.md](SECURITY.md) for our full security policy.

- ✅ No data collection or telemetry (offline mode)
- ✅ API keys stored in Flutter Secure Storage (encrypted)
- ✅ Automated dependency auditing via Dependabot
- ✅ dart pub audit on every push

---

## 💰 Pricing

| Tier | Price | Features |
|------|-------|---------|
| **Free** | $0 | Offline models, basic tools, community support |
| **Pro** | $9.99/mo | Claude API integration, all advanced tools, priority support |
| **Enterprise** | $497/mo | Team deployment, custom models, SLA, dedicated support |

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Commit with [Conventional Commits](https://www.conventionalcommits.org/)
4. Submit a pull request

---

## 📄 License

Apache 2.0 — see [LICENSE](LICENSE) for details.

---

<div align="center">

**[Bakertreet Labs](https://github.com/Bakery-street-project)** · Building the future, one agent at a time 🧪

*AI that works for you — even without Wi-Fi 🌿*

</div>
