# 🦁 RastaCoder — Week 2 Detailed Plan

**Phase:** Polish & UX  
**Duration:** March 17-23, 2026 (7 days)  
**Goal:** Transform RastaCoder from functional to beautiful and launch-ready

---

## 📊 WEEK 2 OVERVIEW

```
┌─────────────────────────────────────────────────────────────────┐
│                    WEEK 2: POLISH PHASE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Day 1          Day 2          Day 3          Day 4             │
│  ████████       ████████       ████████       ████████          │
│  Theme Merge    Components     Demo Video     Screenshots       │
│                                                                  │
│  Day 5          Day 6          Day 7                            │
│  ████████       ████████       ████████                          │
│  Setup Guide    Landing Page   Review & Test                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Deliverables

| # | Deliverable | Format | Status |
|---|-------------|--------|--------|
| 1 | Rasta Theme Implementation | Code (Dart) | ⏳ Pending |
| 2 | Demo Video (60s) | MP4 + Script | ⏳ Pending |
| 3 | Screenshots (5) | PNG (1080x2400) | ⏳ Pending |
| 4 | Setup Guide | PDF (10-15 pages) | ⏳ Pending |
| 5 | Landing Page | HTML/Carrd | ⏳ Pending |

---

## 📋 TASK 1: Rasta Theme Implementation

**Duration:** 2 days (8 hours)  
**Priority:** 🔴 HIGH  
**Files to Modify:** ~10 Dart files

### Research Findings

**Current State:**
- ✅ `lib/app/rasta_theme.dart` — Complete color palette, symbols, gradients
- ⚠️ `lib/app/theme.dart` — Old "NavixTheme" (needs merge/removal)
- ⚠️ Chat screen — Uses basic theme
- ⚠️ Settings screen — Needs Rasta integration

**Design System (from RASTA_GUI_BLUEPRINT.md):**
- Primary colors: Red (#CE1126), Gold (#FFD700), Green (#009B3A)
- Background: Charcoal (#0F0F12)
- Surfaces: Dark grays (#1E1E24, #2A2A35)
- Spiritual symbols: 🦁 Lion, ✡ Star, 👑 Crown, 🔥 Fire
- Braille spinner: ⣷ ⣯ ⣟ ⡿ ⢿ ⣻ ⣽ ⣾

### Implementation Plan

#### Step 1.1: Theme Unification (2 hours)

**Action:** Merge `theme.dart` into `rasta_theme.dart`

```dart
// lib/app/rasta_theme.dart — Single source of truth

class RastaTheme {
  // Keep existing colors
  // Add NavixTheme utilities:
  // - spinnerFrames (Braille animation)
  // - waveformChars (voice visualization)
  // - SlashCommand class
  // - fontFamilyUI, fontFamilyMono getters
}
```

**Files to Modify:**
- `lib/app/rasta_theme.dart` — Add missing utilities
- `lib/app/theme.dart` — Deprecate, add migration note
- `lib/main.dart` — Use `RastaTheme.darkTheme`

#### Step 1.2: Core UI Updates (3 hours)

**AppBar with Rasta Gradient:**
```dart
AppBar(
  title: Text('🦁 RastaCoder'),
  backgroundColor: RastaTheme.background,
  foregroundColor: RastaTheme.gold,
  flexibleSpace: Container(
    decoration: BoxDecoration(
      gradient: RastaTheme.rastaGradient, // Red → Gold → Green
    ),
  ),
)
```

**Message Bubbles with Gold Border:**
```dart
// AI messages: Left-aligned, gold left border
Container(
  decoration: BoxDecoration(
    color: RastaTheme.surface,
    borderRadius: BorderRadius.circular(16),
    border: Border(
      left: BorderSide(color: RastaTheme.gold, width: 3),
    ),
  ),
)

// User messages: Right-aligned, no border
Container(
  decoration: BoxDecoration(
    color: RastaTheme.surfaceVariant,
    borderRadius: BorderRadius.circular(16),
  ),
)
```

**Files to Modify:**
- `lib/features/chat/presentation/chat_screen.dart`
- `lib/features/chat/presentation/widgets/message_bubble.dart`

#### Step 1.3: Component Polish (3 hours)

**Bottom Navigation (80dp height, gold accents):**
```dart
BottomNavigationBar(
  type: BottomNavigationBarType.fixed,
  backgroundColor: RastaTheme.surface,
  selectedItemColor: RastaTheme.gold,
  unselectedItemColor: RastaTheme.textTertiary,
  selectedLabelStyle: TextStyle(fontWeight: FontWeight.w600),
  elevation: 8,
)
```

**Floating Action Button (Lion icon):**
```dart
FloatingActionButton(
  onPressed: _handleAction,
  backgroundColor: RastaTheme.gold,
  child: Text('🦁', style: TextStyle(fontSize: 28)),
  elevation: 8,
)
```

**Braille Spinner Animation:**
```dart
class BrailleSpinner extends StatefulWidget {
  @override
  _BrailleSpinnerState createState() => _BrailleSpinnerState();
}

class _BrailleSpinnerState extends State<BrailleSpinner>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  
  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: Duration(milliseconds: 800),
      vsync: this,
    )..repeat();
  }
  
  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        final frameIndex = (_controller.value * 7).floor();
        final colors = [RastaTheme.red, RastaTheme.gold, RastaTheme.green, RastaTheme.gold];
        return Text(
          RastaTheme.spinnerFrames[frameIndex],
          style: TextStyle(
            fontSize: 24,
            color: colors[frameIndex % 4],
          ),
        );
      },
    );
  }
}
```

**Files to Create:**
- `lib/shared/widgets/braille_spinner.dart`
- `lib/shared/widgets/lion_fab.dart`
- `lib/shared/widgets/rasta_bottom_nav.dart`

### Success Criteria

- [ ] All screens use `RastaTheme` exclusively
- [ ] Gold accent on all primary actions
- [ ] Spiritual icons (🦁) visible in UI
- [ ] Braille spinner animates smoothly (60 FPS)
- [ ] Message bubbles have Rasta styling
- [ ] Bottom nav is 80dp, thumb-friendly

---

## 📋 TASK 2: Demo Video (60 seconds)

**Duration:** 1 day (4 hours)  
**Priority:** 🔴 HIGH  
**Format:** 1080p MP4, 60fps

### Research Findings

**Best Practices for Mobile App Demos:**
1. **Hook (0-5s):** Show problem/solution immediately
2. **Demo (5-45s):** 3-4 key features with screen recordings
3. **CTA (45-60s):** Where to get it + unique value

**Technical Specs:**
- Resolution: 1080x2400 (portrait) or 1920x1080 (landscape)
- Frame rate: 60fps (smooth animations)
- Length: 60 seconds max (attention span)
- Subtitles: Auto-generated (85% watch without sound)

### Video Script (60 seconds)

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEMO VIDEO SCRIPT                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ [0:00-0:05] HOOK                                                 │
│ Screen: Split screen — Cloud AI (loading...) vs RastaCoder (✓)  │
│ Voice: "Cloud AI can't do iterative workflows. This can."       │
│ Text: "100% OFFLINE AI"                                         │
│                                                                  │
│ [0:05-0:20] FEATURE 1: Iterative Video Processing               │
│ Screen: Type "Compress this video to under 25MB"                │
│       → Show FFmpeg running 3 times (bitrate adjustment)        │
│       → Final result: 24.8MB ✓                                  │
│ Voice: "Watch it compress video iteratively. Adjusts bitrate    │
│       until it hits the target. All on your phone."             │
│                                                                  │
│ [0:20-0:35] FEATURE 2: On-Device AI                              │
│ Screen: Settings → Download Model (Qwen2.5-Coder-1.5B)          │
│       → Turn off WiFi → Send message → Works offline            │
│ Voice: "Download AI models once. Use forever without internet.  │
│       No API keys. No subscriptions."                           │
│                                                                  │
│ [0:35-0:50] FEATURE 3: Python Execution                          │
│ Screen: Type "Analyze this CSV and plot sales trends"           │
│       → Show pandas code executing → Graph appears              │
│ Voice: "Run Python scripts. Process files. Create charts.       │
│       Full Python 3.11 embedded in the APK."                    │
│                                                                  │
│ [0:50-1:00] CALL TO ACTION                                       │
│ Screen: RastaCoder logo (🦁) with download buttons              │
│ Voice: "RastaCoder. AI that's actually yours."                  │
│ Text: "rastacoder.ai | GitHub: @alexandertaboriskiy"            │
│       "Free tier available • Pro $9.99/mo"                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Production Plan

#### Step 2.1: Screen Recording (1 hour)

**Tools:**
- Built-in Android screen recorder (Settings → Display → Screen recorder)
- Or: AZ Screen Recorder (Play Store)

**Shot List:**
1. Home screen with Rasta theme
2. Chat: "Compress this video to under 25MB"
3. FFmpeg running (speed up 2x for demo)
4. Settings → Model download
5. Offline mode demo (turn off WiFi)
6. Python code execution with graph output

#### Step 2.2: Editing (2 hours)

**Tools:**
- CapCut (free, Android)
- InShot (free, Android)

**Edits:**
- Trim clips to fit 60s
- Add transitions (fade, slide)
- Speed up slow parts (2x)
- Add background music (YouTube Audio Library — free)
- Auto-generate subtitles

#### Step 2.3: Export & Upload (1 hour)

**Export Settings:**
- Resolution: 1080x2400 (portrait)
- Frame rate: 60fps
- Bitrate: 12 Mbps
- Format: MP4 (H.264)

**Upload To:**
- YouTube (unlisted until launch)
- Gumroad product page
- Landing page

### Success Criteria

- [ ] Video is exactly 60 seconds (±5s)
- [ ] Shows 3+ key features
- [ ] Subtitles auto-generated
- [ ] Background music (no copyright)
- [ ] CTA with URL at end

---

## 📋 TASK 3: Screenshots (5 screens)

**Duration:** 0.5 days (2 hours)  
**Priority:** 🟡 MEDIUM  
**Format:** PNG, 1080x2400px

### Research Findings

**Google Play Screenshot Requirements:**
- Minimum: 320px (width), 480px (height)
- Maximum: 3840px (width/height)
- Aspect ratio: 16:9 to 9:16
- Format: PNG or JPEG

**Best Practices:**
1. Show key screens (onboarding, main feature, settings)
2. Add captions (what each screen does)
3. Use device frames (looks professional)
4. Consistent styling (Rasta colors)

### Screenshot List

| # | Screen | Caption | Purpose |
|---|--------|---------|---------|
| 1 | Home/Chat | "Chat with AI — offline or cloud" | Main feature |
| 2 | Video Processing | "Compress videos iteratively" | Unique capability |
| 3 | Model Download | "Download AI models once, use forever" | Offline mode |
| 4 | Python Execution | "Run Python scripts on your phone" | Developer feature |
| 5 | Settings | "Customize AI to your needs" | Configuration |

### Capture Plan

#### Step 3.1: Prepare Device (15 min)

1. Clean home screen (remove personal apps from view)
2. Enable "Show taps" (Developer options)
3. Set brightness to 80%
4. Turn on airplane mode (for clean shots)

#### Step 3.2: Capture Screens (30 min)

**Method A: Physical Device**
```bash
# Navigate to each screen in app
# Press: Power + Volume Down (screenshot)
# Transfer to computer for editing
```

**Method B: Android Studio (if available)**
```bash
# Tools → Device Manager → Screen Record
# Or: adb shell screencap -p /sdcard/screen.png
# adb pull /sdcard/screen.png
```

#### Step 3.3: Add Captions (1 hour)

**Tool:** Canva (free) or Figma (free)

**Template:**
```
┌─────────────────────────────┐
│                             │
│     [Screenshot here]       │
│                             │
├─────────────────────────────┤
│  Chat with AI — offline     │
│  or cloud. No internet      │
│  required for local models. │
└─────────────────────────────┘
  ↑ Caption bar (Rasta gradient)
```

**Export:**
- Format: PNG
- Size: 1080x2400px
- Quality: 100%

### Success Criteria

- [ ] 5 screenshots captured
- [ ] All show Rasta theme
- [ ] Captions added (clear, benefit-focused)
- [ ] Consistent styling
- [ ] Exported at 1080x2400px

---

## 📋 TASK 4: Setup Guide (PDF)

**Duration:** 1 day (3 hours)  
**Priority:** 🟡 MEDIUM  
**Format:** PDF, 10-15 pages

### Research Findings

**Effective Setup Guide Structure:**
1. **Welcome** — What is this app?
2. **Quick Start** — Get running in 5 minutes
3. **Features** — What can it do?
4. **FAQ** — Common questions
5. **Support** — How to get help

**Design Tips:**
- Use screenshots (visual learners)
- Step-by-step numbered lists
- Benefit-focused headings
- Include troubleshooting section

### Setup Guide Outline

```
┌─────────────────────────────────────────────────────────────────┐
│              RASTACODER SETUP GUIDE                              │
│                    Table of Contents                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Welcome to RastaCoder ........................ Page 3       │
│     What is RastaCoder?                                          │
│     Why offline AI matters                                       │
│                                                                  │
│  2. Quick Start ................................... Page 4       │
│     Installation (2 min)                                         │
│     First launch (1 min)                                         │
│     Choose your AI mode (1 min)                                  │
│                                                                  │
│  3. Core Features ................................. Page 6       │
│     Chat with AI                                                 │
│     Video/audio processing                                       │
│     Document handling                                            │
│     Python execution                                             │
│     Offline mode                                                 │
│                                                                  │
│  4. Settings & Configuration ...................... Page 10      │
│     AI model selection                                           │
│     API key setup (cloud mode)                                   │
│     Cost limits                                                  │
│     Appearance                                                   │
│                                                                  │
│  5. Example Workflows ............................. Page 12      │
│     "Compress this video to 25MB"                                │
│     "Summarize this PDF"                                         │
│     "Analyze this CSV and plot trends"                           │
│     "Extract audio from video"                                   │
│                                                                  │
│  6. Troubleshooting ............................... Page 14      │
│     Common issues & solutions                                    │
│     FAQ                                                          │
│                                                                  │
│  7. Support & Updates ............................. Page 15      │
│     Contact information                                          │
│     GitHub repository                                            │
│     Discord community                                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Writing Plan

#### Step 4.1: Draft Content (1.5 hours)

**Template for Each Section:**

```markdown
## [Feature Name]

**What it does:** [One sentence benefit]

**How to use:**
1. Step one
2. Step two
3. Step three

**Example:**
> User: "Compress this video to under 25MB"
> RastaCoder: [Shows iterative process]
> Result: 24.8MB video ✓

**Pro tip:** [Advanced usage tip]
```

#### Step 4.2: Add Screenshots (1 hour)

- Insert screenshots from Task 3
- Add arrows/callouts (red circles)
- Number each step visually

#### Step 4.3: Export as PDF (30 min)

**Tools:**
- Google Docs (free) → File → Download → PDF
- Canva (free templates) → Download → PDF Print

**Export Settings:**
- Quality: High (300 DPI)
- Size: A4 or Letter
- Include bleed (for professional printing if needed)

### Success Criteria

- [ ] 10-15 pages
- [ ] All sections complete
- [ ] Screenshots included
- [ ] Step-by-step instructions
- [ ] FAQ section (5+ questions)
- [ ] Exported as PDF

---

## 📋 TASK 5: Landing Page

**Duration:** 1 day (6 hours)  
**Priority:** 🔴 HIGH  
**Platform:** Carrd.co (recommended) or Framer

### Research Findings

**High-Converting Landing Page Structure:**
1. **Hero** — Headline + subheadline + CTA (above fold)
2. **Problem** — What pain point does this solve?
3. **Solution** — How RastaCoder fixes it
4. **Features** — 3-5 key capabilities
5. **Social Proof** — Testimonials, GitHub stars
6. **Pricing** — Clear tiers
7. **FAQ** — Address objections
8. **CTA** — Final push to action

**Best Practices:**
- One primary CTA (don't split attention)
- Benefit-focused copy (not features)
- Mobile-optimized (60%+ traffic)
- Fast loading (<3s)
- Clear value proposition

### Landing Page Wireframe

```
┌─────────────────────────────────────────────────────────────────┐
│                    HERO SECTION                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│           🦁 RASTACODER                                          │
│                                                                  │
│     The AI Assistant That Runs 100% Offline                      │
│                                                                  │
│     No internet. No API keys. No subscriptions.                  │
│     Full Python + AI embedded in your APK.                       │
│                                                                  │
│              [🚀 Get RastaCoder — Free]                          │
│              [📱 Watch Demo (60s)]                               │
│                                                                  │
│              GitHub: ⭐ 500+  │  Users: 2,000+                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    PROBLEM SECTION                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Why Cloud AI Apps Fail on Mobile                                │
│                                                                  │
│  ❌ Can't do iterative workflows                                 │
│     (They run once, can't retry)                                 │
│                                                                  │
│  ❌ Your data leaves your phone                                  │
│     (Privacy concerns, GDPR issues)                              │
│                                                                  │
│  ❌ Requires internet                                            │
│     (No offline mode, always dependent)                          │
│                                                                  │
│  ❌ Monthly subscriptions add up                                 │
│     ($20-50/month for basic features)                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    SOLUTION SECTION                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  RastaCoder Fixes This                                           │
│                                                                  │
│  ✅ Iterative workflows                                          │
│     (Runs FFmpeg multiple times until target met)                │
│                                                                  │
│  ✅ 100% on-device processing                                    │
│     (Your data never leaves your phone)                          │
│                                                                  │
│  ✅ Works offline                                                │
│     (Download models once, use forever)                          │
│                                                                  │
│  ✅ Free tier + one-time purchase                                │
│     (No mandatory subscription)                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    FEATURES SECTION                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  What Can RastaCoder Do?                                         │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ 📹       │  │ 📄       │  │ 🐍       │  │ 📱       │       │
│  │ Video    │  │ Document │  │ Python   │  │ Offline  │       │
│  │ Process  │  │ Handling │  │ Execute  │  │ AI       │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│                                                                  │
│  [View All Features →]                                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    PRICING SECTION                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Simple, Transparent Pricing                                     │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ FREE        │  │ PRO         │  │ ENTERPRISE  │             │
│  │ $0          │  │ $9.99/mo    │  │ $497/mo     │             │
│  │             │  │             │  │             │             │
│  │ ✓ Basic AI  │  │ ✓ Cloud AI  │  │ ✓ White-    │             │
│  │ ✓ Offline   │  │ ✓ Unlimited │  │   label     │             │
│  │ ✓ 50 calls  │  │ ✓ Advanced  │  │ ✓ Custom    │             │
│  │   /day      │  │   tools     │  │   models    │             │
│  │             │  │             │  │ ✓ SLA       │             │
│  │             │  │             │  │   support   │             │
│  │ [Download]  │  │ [Start Free │  │ [Contact]   │             │
│  │             │  │   Trial]    │  │             │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    CTA SECTION                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Ready to Try RastaCoder?                                        │
│                                                                  │
│  Join 2,000+ users running AI offline                            │
│                                                                  │
│              [🚀 Download Now — Free]                            │
│                                                                  │
│  Available for Android 7.0+ (API 24+)                            │
│  Also on: [GitHub] [Gumroad] [Play Store]                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Build Plan

#### Step 5.1: Choose Platform (30 min)

**Option A: Carrd.co (Recommended)**
- Cost: $19/year (Pro plan)
- Pros: Easy, mobile-optimized, templates
- Cons: Limited customization

**Option B: Framer**
- Cost: Free tier available
- Pros: More flexible, modern
- Cons: Steeper learning curve

**Option C: GitHub Pages (Free)**
- Cost: Free
- Pros: Free, custom domain
- Cons: Requires HTML/CSS knowledge

**Decision:** Use Carrd.co for speed (launch in 1 day)

#### Step 5.2: Write Copy (2 hours)

**Headline Formulas:**
- "The AI Assistant That Runs 100% Offline"
- "No Internet? No Problem."
- "AI That's Actually Yours"

**Subheadline:**
- "Full Python + AI embedded in your APK. Process files, execute code, automate workflows — all on your phone."

**CTA Buttons:**
- Primary: "🚀 Get RastaCoder — Free"
- Secondary: "📱 Watch Demo (60s)"

#### Step 5.3: Build Page (3 hours)

**Carrd.co Steps:**
1. Sign up → Create New Site
2. Choose template (Landing Page category)
3. Customize colors (Rasta: Red, Gold, Green)
4. Add sections (Hero, Problem, Solution, Features, Pricing, CTA)
5. Upload demo video (YouTube embed)
6. Add screenshots
7. Connect domain (rastacoder.ai)
8. Publish

#### Step 5.4: Test & Launch (30 min)

**Checklist:**
- [ ] Mobile responsive (test on phone)
- [ ] All links work
- [ ] Demo video plays
- [ ] CTA buttons work
- [ ] Page loads <3s
- [ ] Analytics connected (Google Analytics)

### Success Criteria

- [ ] Landing page live at rastacoder.ai
- [ ] All 6 sections complete
- [ ] Demo video embedded
- [ ] Pricing table clear
- [ ] CTA buttons functional
- [ ] Mobile-optimized

---

## 📅 WEEK 2 SCHEDULE

### Day 1-2: Rasta Theme
```
Monday (Day 1):
├─ 9:00-11:00  Step 1.1: Theme unification
├─ 11:00-12:00 Break
├─ 13:00-16:00 Step 1.2: Core UI updates
└─ 16:00-17:00 Review & test

Tuesday (Day 2):
├─ 9:00-12:00  Step 1.3: Component polish
├─ 12:00-13:00 Break
├─ 13:00-15:00 Testing & bug fixes
└─ 15:00-17:00 Final review
```

### Day 3: Demo Video
```
Wednesday (Day 3):
├─ 9:00-10:00  Step 2.1: Screen recording
├─ 10:00-12:00 Step 2.2: Editing (part 1)
├─ 12:00-13:00 Break
├─ 13:00-15:00 Step 2.2: Editing (part 2)
└─ 15:00-17:00 Step 2.3: Export & upload
```

### Day 4: Screenshots
```
Thursday (Day 4):
├─ 9:00-10:00  Step 3.1: Prepare device
├─ 10:00-10:30 Step 3.2: Capture screens
├─ 10:30-12:00 Break
├─ 13:00-15:00 Step 3.3: Add captions
└─ 15:00-17:00 Export & review
```

### Day 5: Setup Guide
```
Friday (Day 5):
├─ 9:00-10:30  Step 4.1: Draft content
├─ 10:30-12:00 Break
├─ 13:00-14:00 Step 4.2: Add screenshots
└─ 14:00-15:00 Step 4.3: Export PDF
```

### Day 6: Landing Page
```
Saturday (Day 6):
├─ 9:00-9:30   Step 5.1: Choose platform
├─ 9:30-11:30  Step 5.2: Write copy
├─ 11:30-12:00 Break
├─ 13:00-16:00 Step 5.3: Build page
└─ 16:00-17:00 Step 5.4: Test & launch
```

### Day 7: Review & Buffer
```
Sunday (Day 7):
├─ 9:00-12:00  Review all deliverables
├─ 12:00-13:00 Break
├─ 13:00-15:00 Fix any issues
└─ 15:00-17:00 Week 3 planning
```

---

## 📊 SUCCESS METRICS

### Week 2 Completion Criteria

| Deliverable | Quality Target | Status |
|-------------|----------------|--------|
| Rasta Theme | 100% screens use RastaTheme | ⏳ |
| Demo Video | 60s, 3+ features shown | ⏳ |
| Screenshots | 5 screens, captions added | ⏳ |
| Setup Guide | 10-15 pages, PDF | ⏳ |
| Landing Page | Live at rastacoder.ai | ⏳ |

### Quality Checklist

**Before marking Week 2 complete:**
- [ ] All 5 deliverables created
- [ ] Demo video uploaded to YouTube
- [ ] Landing page live and tested
- [ ] Setup guide PDF downloadable
- [ ] Screenshots ready for app stores
- [ ] Rasta theme consistent across app

---

## 🔗 RELATED DOCUMENTS

- [RASTA_GUI_BLUEPRINT.md](RASTA_GUI_BLUEPRINT.md) — Design system
- [RASTACODER_QUICK_LAUNCH.md](RASTACODER_QUICK_LAUNCH.md) — 24-hour launch
- [RASTACODER_LAUNCH_CHECKLIST.md](RASTACODER_LAUNCH_CHECKLIST.md) — 7-day plan
- [BUILDING_PHASE_PLAN.md](BUILDING_PHASE_PLAN.md) — Overall phase plan

---

**Created:** March 16, 2026  
**Owner:** Kiliaan Vanvoorden (@BoozeLee)  
**Status:** Ready for Execution

*Baker Street Laboratory © 2026* 🔱  
*Jah Rastafari! 🦁🇯🇲*
