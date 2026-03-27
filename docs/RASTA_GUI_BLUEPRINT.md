# 🦁 RastaCoder GUI Blueprint
## Enhanced Rastafarian Design System for Mobile-First AI

**Version:** 2.0.0  
**Created:** March 15, 2026  
**Status:** Design Specification

---

## 🎨 DESIGN PHILOSOPHY

### Core Principles

> "Terminal meets Caribbean vibes — Deep earth tones, spiritual symbolism, mobile-native interactions"

1. **Rastafarian Identity** — Red, Gold, Green colors with deep earth tones
2. **Mobile-First** — Touch-optimized, thumb-friendly, gesture-based
3. **Terminal Aesthetic** — Monospace code, Braille spinners, ASCII art
4. **Spiritual Symbolism** — Lion of Judah, Ethiopian star, natural elements
5. **High Contrast** — Accessible, readable in sunlight, dark mode default

---

## 🌈 COLOR SYSTEM

### Primary Rasta Colors

| Color | Hex | Usage | Meaning |
|-------|-----|-------|---------|
| **Red** | `#CE1126` | Primary actions, alerts | Blood of martyrs |
| **Gold** | `#FFD700` | Primary brand, accents | Wealth of homeland |
| **Green** | `#009B3A` | Success, confirmations | Vegetation of Zion |
| **Black** | `#1A1A1A` | Background, surfaces | African people |

### Extended Palette

```dart
// RastaTheme class (lib/app/rasta_theme.dart)
static const Color red = Color(0xFFCE1126);
static const Color redLight = Color(0xFFFF4D4D);
static const Color redDark = Color(0xFF8B0000);

static const Color gold = Color(0xFFFFD700);
static const Color goldLight = Color(0xFFFFE84D);
static const Color goldDark = Color(0xFFB8860B);

static const Color green = Color(0xFF009B3A);
static const Color greenLight = Color(0xFF32CD32);
static const Color greenDark = Color(0xFF006400);

// Earth tones
static const Color earth = Color(0xFF8B4513);
static const Color sand = Color(0xFFD2B48C);
static const Color soil = Color(0xFF654321);

// UI Surfaces
static const Color background = Color(0xFF0F0F12);  // Charcoal
static const Color surface = Color(0xFF1E1E24);
static const Color surfaceVariant = Color(0xFF2A2A35);
static const Color surfaceElevated = Color(0xFF353540);
```

### Gradients

```dart
// Rastafarian gradient (Red → Gold → Green)
static const LinearGradient rastaGradient = LinearGradient(
  colors: [red, gold, green],
  begin: Alignment.topLeft,
  end: Alignment.bottomRight,
);

// Lion gradient (Gold → Orange)
static const LinearGradient lionGradient = LinearGradient(
  colors: [gold, accentOrange],
  begin: Alignment.topCenter,
  end: Alignment.bottomCenter,
);

// Earth gradient (Brown tones)
static const LinearGradient earthGradient = LinearGradient(
  colors: [soil, earth, sand],
  begin: Alignment.topCenter,
  end: Alignment.bottomCenter,
);
```

### Semantic Colors

| State | Color | Icon |
|-------|-------|------|
| **Success** | Green `#009B3A` | ✓ |
| **Error** | Red `#CE1126` | ✗ |
| **Warning** | Gold `#FFD700` | ⚠ |
| **Info** | Cyan `#4FC3F7` | ℹ |

---

## 🦁 SYMBOLISM & ICONS

### Unicode Symbol Library

```dart
// Spiritual symbols
static const String iconLion = '🦁';        // Lion of Judah
static const String iconStar = '✡';        // Ethiopian Star of David
static const String iconCrown = '👑';      // Crown of Judah
static const String iconDrum = '🥁';       // Nyabinghi drum
static const String iconFire = '🔥';       // Sacred fire
static const String iconLeaf = '🌿';       // Natural herb
static const String iconEarth = '🌍';      // Mother Earth
static const String iconSun = '☀️';        // Jah light
static const String iconMoon = '🌙';       // Night meditation

// Action symbols
static const String iconPeace = '✌️';      // Peace sign
static const String iconFist = '✊';        // Raised fist
static const String iconPrayer = '🙏';     // Hands folded
static const String iconMusic = '🎵';      // Musical note
static const String iconGuitar = '🎸';     // Reggae guitar

// UI symbols
static const String iconCheck = '✓';
static const String iconError = '✗';
static const String iconWarning = '⚠';
static const String iconSend = '➤';
static const String iconClose = '✕';
static const String iconMenu = '☰';
static const String iconAdd = '⊕';
static const String iconSearch = '🔍';
static const String iconSettings = '⚙';
static const String iconHome = '🏠';
static const String iconRefresh = '🔄';
static const String iconDownload = '⬇';
static const String iconUpload = '⬆';
static const String iconShare = '↗';
static const String iconCopy = '📋';
static const String iconDelete = '🗑';
static const String iconLock = '🔒';
static const String iconUnlock = '🔓';
static const String iconUser = '👤';
static const String iconAI = '🤖';
static const String iconBrain = '🧠';
static const String iconSparkle = '✨';
```

### Braille Spinner Animation

```dart
// 8-frame Braille spinner (Rasta colors)
static const List<String> spinnerFrames = [
  '🔴', '🟡', '🟢', '🟡',  // Red, Gold, Green, Gold
];

// Alternative: Braille animation
static const List<String> brailleSpinner = [
  '⣷', '⣯', '⣟', '⡿', '⢿', '⣻', '⣽', '⣾',
];
```

### Voice Waveform

```dart
// Rasta-colored waveform visualization
static const List<String> waveformChars = ['▂', '▃', '▅', '▇', '█'];
// Colors: Red → Gold → Green gradient based on amplitude
```

---

## 📱 MOBILE-FIRST COMPONENTS

### 1. Chat Screen (Enhanced)

```
┌─────────────────────────────────────┐
│  🦁 RastaCoder          ⚙️ 👤      │  ← AppBar (Gold title)
├─────────────────────────────────────┤
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 🤖 AI Message               │   │
│  │ Bless up! Here's your code: │   │
│  │ ```python                   │   │
│  │ print("Irie vibes")         │   │
│  │ ```                         │   │
│  │ 🔥 🦁 ✨                    │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 👤 User Message             │   │
│  │ Compress this video         │   │
│  └─────────────────────────────┘   │
│                                     │
│  [🔴] [🟡] [🟢] ← Loading spinner   │
│                                     │
├─────────────────────────────────────┤
│  [📎] [🎤] ───────────── [➤]       │  ← Input bar
│   Attach  Voice       Send (Gold)  │
└─────────────────────────────────────┘
```

**Key Features:**
- Message bubbles with Rasta border accents (gold border)
- Gold-focused send button (thumb-optimized, 56x56dp)
- Braille spinner for AI thinking states
- Voice waveform visualization (Red→Gold→Green)
- Haptic feedback on message send

### 2. Navigation Bar (Bottom)

```
┌─────────────────────────────────────┐
│  🏠      💬      ⚡      👤        │
│ Home   Chat   Tools   Profile      │
│  ✓                                │
└─────────────────────────────────────┘
```

**Design:**
- Height: 80dp (thumb-friendly)
- Selected: Gold icon + text with glow
- Unselected: Gray text
- Background: Surface color (`#1E1E24`)
- Active indicator: Subtle gold gradient

### 3. Settings Screen

```
┌─────────────────────────────────────┐
│  ⚙️ Settings              🦁        │
├─────────────────────────────────────┤
│  ┌─────────────────────────────┐   │
│  │ 🤖 AI Configuration         │   │
│  │ ─────────────────────────── │   │
│  │ Cloud Mode          [▶]     │   │
│  │ Model: Claude Sonnet  [▶]   │   │
│  │ API Key: •••••••••••  [✏]   │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 📱 On-Device AI             │   │
│  │ ─────────────────────────── │   │
│  │ Download Model       [⬇]    │   │
│  │ Qwen2.5-Coder-1.5B   [✓]    │   │
│  │ RAM: 1.2GB / 4GB            │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 🎨 Appearance               │   │
│  │ ─────────────────────────── │   │
│  │ Theme: Rasta Dark     [▶]   │   │
│  │ Icons: Spiritual      [▶]   │   │
│  │ Animations: On        [◉]   │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 💰 Pro Features             │   │
│  │ ─────────────────────────── │   │
│  │ Daily Token Limit: 100K [✏] │   │
│  │ Usage This Month: 45K       │   │
│  │ Upgrade to Pro      [👑]    │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

### 4. Tool Selection (Mobile Grid)

```
┌─────────────────────────────────────┐
│  🛠️ Tools                  ✕        │
├─────────────────────────────────────┤
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐  │
│  │ 📹  │ │ 📄  │ │ 🎵  │ │ 🌐  │  │
│  │Video│ │ Doc │ │Audio│ │ Web │  │
│  └─────┘ └─────┘ └─────┘ └─────┘  │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐  │
│  │ 🐍  │ │ 📊  │ │ 📷  │ │ 📝  │  │
│  │Python│ │Data│ │ OCR │ │ PDF │  │
│  └─────┘ └─────┘ └─────┘ └─────┘  │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐  │
│  │ 📅  │ │ 📧  │ │ 🗂️  │ │ ⚙  │  │
│  │Calendar│ │Gmail│ │Files│ │More│  │
│  └─────┘ └─────┘ └─────┘ └─────┘  │
└─────────────────────────────────────┘
```

**Grid Layout:**
- 4 columns × 3 rows
- Icon size: 48x48dp
- Card size: 80x80dp
- Rasta gradient borders on selected
- Tap to expand tool options

### 5. Quick Actions (Floating)

```
                    ┌─────┐
                    │  📎 │ ← Attach File
                    └─────┘
                    ┌─────┐
                    │  🎤 │ ← Voice Input
                    └─────┘
                    ┌─────┐
              ┌───────────┐
              │     🦁    │ ← Main FAB (Lion)
              │  (Gold)   │
              └───────────┘
```

### 6. Message Bubble Design

```
User Message (Right aligned):
┌─────────────────────────────┐
│  Compress this video        │
│  under 25MB                 │
└─────────────────────────────┘
  ╰─ Surface variant (#2A2A35)

AI Message (Left aligned):
┌─────────────────────────────┐
│🦁 Bless up! I compressed    │
│  your video:                │
│                             │
│  📹 video_compressed.mp4    │
│     24.8 MB (was 156 MB)    │
│     [Open] [Share]          │
└─────────────────────────────┘
  ╰─ Gold border left (3px)
```

---

## 🔌 API INTEGRATION ARCHITECTURE

### Core Architecture (What We Use)

```
┌─────────────────────────────────────────────────────────────┐
│                    FLUTTER UI LAYER                          │
│  Chat │ Settings │ Tools │ On-Device Models                 │
├─────────────────────────────────────────────────────────────┤
│                   SERVICE LAYER (Dart)                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐│
│  │ Claude API  │ │ Local LLM   │ │  Native Tools           ││
│  │ Service     │ │ Service     │ │  (FFmpeg, OCR, ML Kit)  ││
│  └─────────────┘ └─────────────┘ └─────────────────────────┘│
├──────────────────┬──────────────────────────────────────────┤
│  KOTLIN BRIDGE   │           PYTHON AGENT                   │
│  (Android)       │  ┌─────────────────────────────────────┐ │
│  ┌─────────────┐ │  │  ReAct Loop + Tool Router           │ │
│  │MLC Channel  │◄├──┤  - Claude API (cloud)               │ │
│  │Model D/L    │ │  │  - Local LLM (offline)              │ │
│  │File Opener  │ │  │  - File/Document tools              │ │
│  │Share Recv   │ │  │  - Media tools (FFmpeg)             │ │
│  └─────────────┘ │  └─────────────────────────────────────┘ │
└──────────────────┴──────────────────────────────────────────┘
```

### What We DON'T Need

❌ **NOT implementing:**
- SMS/MMS — Not needed for file processing AI
- Contacts — Not needed for this use case
- Phone calls — Not relevant
- GPS Location — Not required
- Device Sensors — Not needed

**Focus:** File processing, document handling, media manipulation, AI inference

---

## 🎨 THEME IMPLEMENTATION

### Current State

**File:** `lib/app/rasta_theme.dart` ✅ EXISTS

**What's implemented:**
- ✅ Full Rasta color palette
- ✅ Spiritual symbols library
- ✅ Rasta philosophy dataset
- ✅ Dark theme with gold accents
- ✅ Monospace code styling
- ✅ Gradient definitions

**What needs updating:**
- ⚠️ `lib/app/theme.dart` — Still has old "NavixTheme" (merge or remove)
- ⚠️ Chat screen — Uses basic theme, needs Rasta styling
- ⚠️ Settings screen — Needs Rasta theme integration

---

## 🔧 GUI ENHANCEMENT PLAN

### Phase 1: Theme Unification (Week 1)

**Tasks:**
1. Merge `theme.dart` into `rasta_theme.dart` (single source of truth)
2. Update all screens to use `RastaTheme` exclusively
3. Add Rasta gradient to app bar
4. Implement Braille spinner animations

**Files to Modify:**
```
lib/app/theme.dart → Merge with rasta_theme.dart
lib/features/chat/presentation/chat_screen.dart
lib/features/settings/settings_screen.dart
lib/main.dart → Use RastaTheme.darkTheme
```

### Phase 2: Component Polish (Week 1-2)

**Tasks:**
1. Message bubble styling (gold borders, Rasta colors)
2. Bottom navigation bar (80dp, gold accents)
3. Tool grid with spiritual icons
4. Floating action button (Lion icon)
5. Voice waveform visualization

**Files to Create:**
```
lib/shared/widgets/
├── rasta_message_bubble.dart
├── rasta_bottom_nav.dart
├── tool_grid.dart
├── lion_fab.dart
└── voice_waveform.dart
```

### Phase 3: Animations & Feedback (Week 2)

**Tasks:**
1. Rasta-colored loading animations
2. Haptic feedback on interactions
3. Smooth page transitions
4. Tool execution progress indicators
5. Success/error states with Rasta colors

---

## 📊 COMPONENT SPECIFICATIONS

### App Bar

```dart
AppBar(
  title: Text('🦁 RastaCoder', style: RastaTheme.textTheme.headlineMedium),
  backgroundColor: RastaTheme.background,
  foregroundColor: RastaTheme.gold,
  elevation: 0,
  flexibleSpace: Container(
    decoration: BoxDecoration(
      gradient: RastaTheme.rastaGradient,
    ),
  ),
  actions: [
    IconButton(icon: Icon(Icons.settings), onPressed: () {}),
    IconButton(icon: Icon(Icons.person), onPressed: () {}),
  ],
)
```

### Message Bubble

```dart
Container(
  decoration: BoxDecoration(
    color: isUser ? RastaTheme.surfaceVariant : RastaTheme.surface,
    borderRadius: BorderRadius.circular(16),
    border: isUser ? null : Border(
      left: BorderSide(color: RastaTheme.gold, width: 3),
    ),
  ),
  child: Padding(
    padding: EdgeInsets.all(16),
    child: Column(
      children: [
        // Lion icon for AI messages
        if (!isUser) Text('🦁', style: TextStyle(fontSize: 20)),
        // Message content
        Text(message, style: RastaTheme.textTheme.bodyMedium),
        // Tool results (code, files, etc.)
        if (hasAttachment) _buildAttachment(),
      ],
    ),
  ),
)
```

### Loading Spinner

```dart
AnimationBuilder(
  builder: (context, frame) => Text(
    RastaTheme.spinnerFrames[frame],
    style: TextStyle(fontSize: 24),
  ),
)
// Cycles through: 🔴 🟡 🟢 🟡
```

---

## 📈 SUCCESS METRICS

### Visual Design Targets

| Metric | Target |
|--------|--------|
| Rasta Color Usage | 80% of UI elements |
| Gold Accent Consistency | 100% primary actions |
| Spiritual Icons | 50%+ icon replacement |
| Animation Smoothness | 60 FPS |

### User Experience

| Feature | Target Satisfaction |
|---------|---------------------|
| Theme Consistency | 90% positive feedback |
| Touch Targets | 100% > 48dp |
| Loading Feedback | < 100ms perceived delay |
| Accessibility | WCAG AA contrast |

---

## 🔗 RELATED DOCUMENTS

- [RASTACODER_BLUEPRINT.md](RASTACODER_BLUEPRINT.md) — Complete architecture
- [RASTACODER_LAUNCH_CHECKLIST.md](RASTACODER_LAUNCH_CHECKLIST.md) — Launch steps
- [MOBILE_INTEGRATION_STATUS.md](MOBILE_INTEGRATION_STATUS.md) — What we use vs don't need

---

**Created By:** Qwen Code Agent  
**Date:** March 15, 2026  
**Status:** Design Specification — Ready for Implementation

*Baker Street Laboratory © 2026* 🔱  
*Jah Rastafari! 🦁🇯🇲*
