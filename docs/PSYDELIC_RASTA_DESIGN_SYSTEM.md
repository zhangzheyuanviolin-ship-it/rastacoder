# 🦁🌀 Psychedelic Rasta Design System

**Project:** RastaCoder — Psytrance-Inspired GUI Graphics  
**Version:** 1.0.0 — Azlaar x Psytrance x Rasta Fusion  
**Created:** March 16, 2026  
**Status:** Design Specification — Ready for Implementation

---

## 🎨 DESIGN VISION

> **"Terminal meets Caribbean psychedelia — where Azlaar's sci-fi minimalism collides with psytrance fractals and Rastafarian symbolism"**

### Core Philosophy

```
┌─────────────────────────────────────────────────────────────────┐
│                    DESIGN FUSION TRIAD                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│         🎨 AZLAAR               🌀 PSYTRANCE           🦁 RASTA  │
│         Sci-Fi Minimal        Fractal Chaos          Spiritual  │
│         Dark Atmospheric      UV Neon Glow           Red-Gold-  │
│         Geometric Abstract    Sacred Geometry        Green      │
│                                                                  │
│                     ↓ FUSION ↓                                   │
│                                                                  │
│              🦁🌀 PSYDELIC RASTA 🌀🦁                             │
│         "Lion's Fractal Journey Through Zion"                    │
│                                                                  │
│  - Dark charcoal backgrounds (#0F0F12)                           │
│  - Gold fractal patterns (UV-reactive aesthetic)                 │
│  - Rasta color gradients (Red→Gold→Green)                        │
│  - Lion of Judah as central mandala                              │
│  - Sacred geometry + Ethiopian symbols                           │
│  - Sci-fi terminal meets psychedelic festival                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🌈 COLOR SYSTEM — PSYDELIC RASTA PALETTE

### Primary Colors (Rasta Foundation)

| Color | Hex | Usage | Psytrance Enhancement |
|-------|-----|-------|----------------------|
| **Red** | `#CE1126` | Primary actions, alerts | Add neon glow (`#FF2D4E`) |
| **Gold** | `#FFD700` | Brand, accents, fractals | UV-reactive (`#FFEA00`) |
| **Green** | `#009B3A` | Success, confirmations | Electric green (`#00FF66`) |
| **Black** | `#1A1A1A` | Background, surfaces | Deep space black (`#0A0A0F`) |

### Psytrance Neon Accents

| Color | Hex | Usage |
|-------|-----|-------|
| **Electric Blue** | `#00F0FF` | Links, highlights, energy flows |
| **Hot Pink** | `#FF00FF` | Special effects, rare accents |
| **UV Purple** | `#8B00FF` | Mystical elements, premium features |
| **Lime Green** | `#32FF00` | Success states, active elements |

### Extended Palette (Azlaar-Inspired Dark Tones)

| Color | Hex | Usage |
|-------|-----|-------|
| **Charcoal** | `#0F0F12` | Main background |
| **Deep Space** | `#1A1A2E` | Secondary background |
| **Metallic Gray** | `#2D2D3A` | Surface elevation |
| **Cyber Cyan** | `#00FFFF` | Terminal text, code highlights |

### Gradient System

```dart
// ═══════════════════════════════════════════════════════════════
// RASTA FRACTAL GRADIENTS
// ═══════════════════════════════════════════════════════════════

/// Classic Rasta gradient (Red → Gold → Green)
static const LinearGradient rastaGradient = LinearGradient(
  colors: [Color(0xFFCE1126), Color(0xFFFFD700), Color(0xFF009B3A)],
  begin: Alignment.topLeft,
  end: Alignment.bottomRight,
);

/// Psytrance UV gradient (Gold → Electric Blue → Hot Pink)
static const LinearGradient uvGradient = LinearGradient(
  colors: [Color(0xFFFFD700), Color(0xFF00F0FF), Color(0xFFFF00FF)],
  begin: Alignment.centerLeft,
  end: Alignment.centerRight,
);

/// Lion's Mane gradient (Gold → Orange → Red)
static const LinearGradient lionManeGradient = LinearGradient(
  colors: [Color(0xFFFFD700), Color(0xFFFF9800), Color(0xFFCE1126)],
  begin: Alignment.topCenter,
  end: Alignment.bottomCenter,
);

/// Fractal depth gradient (Black → Deep Purple → Electric Blue)
static const LinearGradient fractalDepthGradient = LinearGradient(
  colors: [Color(0xFF0A0A0F), Color(0xFF2D004E), Color(0xFF00F0FF)],
  begin: Alignment.topCenter,
  end: Alignment.bottomCenter,
);

/// Zion sunrise (Green → Gold → Red)
static const LinearGradient zionSunriseGradient = LinearGradient(
  colors: [Color(0xFF009B3A), Color(0xFFFFD700), Color(0xFFCE1126)],
  begin: Alignment.bottomCenter,
  end: Alignment.topCenter,
);

/// Babylon night (Deep Black → Purple → Red)
static const LinearGradient babylonNightGradient = LinearGradient(
  colors: [Color(0xFF0A0A0F), Color(0xFF4B0082), Color(0xFF8B0000)],
  begin: Alignment.topLeft,
  end: Alignment.bottomRight,
);
```

---

## 🌀 FRACTAL PATTERNS & SACRED GEOMETRY

### Core Fractal Motifs

| Pattern | Description | Usage |
|---------|-------------|-------|
| **Mandelbrot Spiral** | Infinite recursive pattern | Loading screens, backgrounds |
| **Flower of Life** | Sacred geometry (7 circles) | App icon center, splash screen |
| **Metatron's Cube** | 13 circles + connecting lines | Settings screen, premium features |
| **Sri Yantra** | 9 interlocking triangles (Hindu influence) | Meditation mode, chill section |
| **Golden Ratio Spiral** | Fibonacci sequence (1:1.618) | Content layout, image crops |

### Fractal Implementation

```dart
// ═══════════════════════════════════════════════════════════════
// FRACTAL DECORATIVE PATTERNS
// ═══════════════════════════════════════════════════════════════

/// Mandelbrot-inspired spiral pattern (simplified for performance)
class FractalSpiralPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = RastaTheme.gold.withOpacity(0.1)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2;
    
    final center = Offset(size.width / 2, size.height / 2);
    final maxRadius = size.width / 2;
    
    // Draw 8 spiral arms (Rasta colors)
    for (int i = 0; i < 8; i++) {
      final path = Path();
      final angleOffset = (i / 8) * 2 * pi;
      
      path.moveTo(center.dx, center.dy);
      
      for (double t = 0; t < 4 * pi; t += 0.1) {
        final radius = (t / (4 * pi)) * maxRadius;
        final angle = t + angleOffset;
        final x = center.dx + radius * cos(angle);
        final y = center.dy + radius * sin(angle);
        path.lineTo(x, y);
      }
      
      canvas.drawPath(path, paint);
    }
  }
  
  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

/// Sacred geometry overlay (Flower of Life simplified)
class SacredGeometryPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = RastaTheme.gold.withOpacity(0.05)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;
    
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 6;
    
    // Draw 7 circles (Flower of Life center)
    canvas.drawCircle(center, radius, paint);
    
    for (int i = 0; i < 6; i++) {
      final angle = (i / 6) * 2 * pi;
      final x = center.dx + radius * cos(angle);
      final y = center.dy + radius * sin(angle);
      canvas.drawCircle(Offset(x, y), radius, paint);
    }
  }
  
  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
```

### UV Blacklight Effect

```dart
// ═══════════════════════════════════════════════════════════════
// UV GLOW EFFECTS (Simulated blacklight reactivity)
// ═══════════════════════════════════════════════════════════════

/// Box decoration with UV glow (for cards, buttons)
BoxDecoration uvGlowDecoration({
  Color glowColor = const Color(0xFFFFD700),
  double blurRadius = 20,
  double spreadRadius = 5,
}) {
  return BoxDecoration(
    boxShadow: [
      BoxShadow(
        color: glowColor.withOpacity(0.3),
        blurRadius: blurRadius,
        spreadRadius: spreadRadius,
      ),
      BoxShadow(
        color: glowColor.withOpacity(0.1),
        blurRadius: blurRadius * 2,
        spreadRadius: spreadRadius * 2,
      ),
    ],
  );
}

/// Text style with neon glow effect
TextStyle neonTextStyle({
  Color textColor = const Color(0xFFFFD700),
  Color glowColor = const Color(0xFFFFD700),
}) {
  return TextStyle(
    color: textColor,
    shadows: [
      Shadow(
        color: glowColor.withOpacity(0.5),
        blurRadius: 10,
      ),
      Shadow(
        color: glowColor.withOpacity(0.3),
        blurRadius: 20,
      ),
    ],
  );
}
```

---

## 🦁 SYMBOLISM — RASTA x PSYTRANCE FUSION

### Central Icon: Lion's Fractal Mandala

```
┌─────────────────────────────────────────────────────────────────┐
│                    LION'S FRACTAL MANDALA                        │
│                                                                  │
│              Outer Ring: Rasta Colors (Red-Gold-Green)          │
│                     ╭─────────────────────╮                     │
│                  ╭──┤  Sacred Geometry   ├──╮                  │
│                ╭──┤  │  (Flower of Life) │  ├──╮                │
│              ╭──┤  │  │    ╭─────╮      │  ├──╮                │
│            ╭──┤  │  │  │  │  🦁  │  │  │  ├──╮                │
│            │  │  │  │  │  │ LION │  │  │  │  │                │
│            │  │  │  │  │  │  Core │  │  │  │  │                │
│            │  │  │  │  │  ╰─────╯      │  │  │                │
│              ╰──┤  │  │  Fractal Arms  │  ├──╯                │
│                ╰──┤  │  (8 directions) │  ├──╯                │
│                  ╰──┤                 ├──╯                  │
│                     ╰─────────────────────╯                     │
│              Outer Ring: Rasta Colors (Red-Gold-Green)          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Symbolism:**
- **Center:** Lion of Judah (🦁) — Rastafarian identity
- **Middle Ring:** Flower of Life — Sacred geometry, unity
- **Outer Ring:** 8 fractal arms — Infinite consciousness expansion
- **Colors:** Red-Gold-Green gradient — Rastafarian flag

### Icon Library (Unicode + Custom)

```dart
// ═══════════════════════════════════════════════════════════════
// PSYDELIC RASTA SYMBOLS
// ═══════════════════════════════════════════════════════════════

class PsydelicRastaIcons {
  // Spiritual core
  static const String lion = '🦁';           // Lion of Judah (centerpiece)
  static const String lionUnicode = '♌';     // Astrological Leo
  static const String crown = '👑';          // Crown of Judah
  static const String star = '✡';            // Star of David (Ethiopian)
  static const String starSix = '⭐';        // Six-pointed star
  
  // Psytrance elements
  static const String fractal = '🌀';        // Spiral/fractal
  static const String mushroom = '🍄';       // Psychedelic mushroom
  static const String thirdEye = '👁️';      // Third eye, awareness
  static const String infinity = '∞';        // Infinite consciousness
  static const String om = 'ॐ';              // Sacred sound (Goa influence)
  
  // Nature & Zion
  static const String leaf = '🌿';           // Natural herb (Ital lifestyle)
  static const String earth = '🌍';          // Mother Earth
  static const String sun = '☀️';            // Jah light
  static const String moon = '🌙';           // Night meditation
  static const String mountain = '🏔️';      // Zion (Ethiopian highlands)
  static const String palm = '🌴';           // Tropical Zion
  
  // Energy & power
  static const String fire = '🔥';           // Sacred fire (Nyabinghi)
  static const String lightning = '⚡';      // Divine power
  static const String drum = '🥁';           // Nyabinghi drum
  static const String music = '🎵';          // Reggae/Psytrance
  static const String guitar = '🎸';         // Reggae guitar
  
  // Actions (psydelic style)
  static const String send = '➤';            // Send message
  static const String expand = '◈';          // Expand consciousness
  static const String contract = '◇';        // Return to center
  static const String balance = '⚖';         // Balance (Rasta justice)
  static const String peace = '✌️';          // Peace sign
  static const String fist = '✊';            // Raised fist (resistance)
  
  // UI elements (fractal-styled)
  static const String menu = '☰';            // Menu (3 lines = mind-body-spirit)
  static const String close = '✕';           // Close (X = crossroads)
  static const String settings = '⚙';        // Settings (gear = karma wheel)
  static const String search = '🔍';         // Search (seek truth)
  static const String home = '🏠';           // Home (Zion)
  static const String back = '◀';            // Back (return to source)
  static const String forward = '▶';         // Forward (progress)
  static const String refresh = '🔄';        // Refresh (reincarnation cycle)
}
```

---

## 🎭 COMPONENT DESIGN — PSYDELIC RASTA STYLE

### 1. App Icon (512x512px)

```
┌─────────────────────────────────────────────────────────────────┐
│                    APP ICON DESIGN                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │     ╭─────────────────────────────────────────────────╮   │  │
│  │   ╭─┤  Background: Deep Space Black (#0A0A0F)       ├─╮ │  │
│  │  ╭──┤                                               ├──╮│  │
│  │  │  │    ╭─────────────────────────────────────╮   │  ││  │
│  │  │  │   ╭┤  Center: Lion of Judah (Gold UV)   ├╮  │  ││  │
│  │  │  │   ││  Surrounded by Flower of Life      ││  │  ││  │
│  │  │  │   ││  (8 fractal arms, Rasta colors)    ││  │  ││  │
│  │  │  │   ╰┤                                   ├╯  │  ││  │
│  │  │  │    ╰─────────────────────────────────────╯   │  ││  │
│  │  │  │                                              │  ││  │
│  │  ╰──┤  Outer Glow: Gold UV (#FFD700, 20px blur)   ├──╯│  │
│  │   ╰─┤                                               ├─╯ │  │
│  │     ╰─────────────────────────────────────────────────╯   │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Technical Specs:                                               │
│  - Size: 512x512px (Play Store), 1024x1024px (App Store)       │
│  - Format: PNG with transparency                                │
│  - Style: UV-reactive gold lion on black background            │
│  - Fractal arms: 8 directions (Red→Gold→Green gradient)        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Splash Screen

```dart
// ═══════════════════════════════════════════════════════════════
// SPLASH SCREEN — LION'S FRACTAL JOURNEY
// ═══════════════════════════════════════════════════════════════

class PsydelicRastaSplashScreen extends StatefulWidget {
  @override
  _PsydelicRastaSplashScreenState createState() =>
      _PsydelicRastaSplashScreenState();
}

class _PsydelicRastaSplashScreenState
    extends State<PsydelicRastaSplashScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scaleAnimation;
  late Animation<double> _rotationAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: Duration(milliseconds: 2000),
      vsync: this,
    );

    _scaleAnimation = Tween<double>(begin: 0.5, end: 1.0).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeOutCubic),
    );

    _rotationAnimation = Tween<double>(begin: 0, end: 2 * pi).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOutSine),
    );

    _controller.forward();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        gradient: RastaTheme.fractalDepthGradient,
      ),
      child: Center(
        child: AnimatedBuilder(
          animation: _controller,
          builder: (context, child) {
            return Transform.rotate(
              angle: _rotationAnimation.value * 0.1, // Subtle rotation
              child: Transform.scale(
                scale: _scaleAnimation.value,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    // Lion of Judah (centerpiece)
                    Text(
                      '🦁',
                      style: TextStyle(
                        fontSize: 120,
                        shadows: [
                          Shadow(
                            color: RastaTheme.gold.withOpacity(0.5),
                            blurRadius: 40,
                          ),
                        ],
                      ),
                    ),
                    SizedBox(height: 24),
                    // App name with neon glow
                    Text(
                      'RASTACODER',
                      style: RastaTheme.neonTextStyle(
                        textColor: RastaTheme.gold,
                        glowColor: RastaTheme.gold,
                      ).copyWith(
                        fontSize: 32,
                        fontWeight: FontWeight.w900,
                        letterSpacing: 4,
                      ),
                    ),
                    SizedBox(height: 8),
                    // Tagline
                    Text(
                      'Offline AI • Psydelic Mind',
                      style: TextStyle(
                        color: RastaTheme.textSecondary,
                        fontSize: 14,
                        letterSpacing: 2,
                      ),
                    ),
                  ],
                ),
              ),
            );
          },
        ),
      ),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }
}
```

### 3. Message Bubbles (Fractal Borders)

```dart
// ═══════════════════════════════════════════════════════════════
// MESSAGE BUBBLES — FRACTAL-EDGED WITH RASTA GLOW
// ═══════════════════════════════════════════════════════════════

class PsydelicMessageBubble extends StatelessWidget {
  final String message;
  final bool isUser;
  final List<String>? attachments;

  const PsydelicMessageBubble({
    Key? key,
    required this.message,
    this.isUser = false,
    this.attachments,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        padding: EdgeInsets.all(16),
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
        decoration: BoxDecoration(
          color: isUser
              ? RastaTheme.surfaceVariant
              : RastaTheme.surface,
          borderRadius: BorderRadius.circular(20),
          // AI messages: Gold left border with UV glow
          border: isUser
              ? null
              : Border(
                  left: BorderSide(
                    color: RastaTheme.gold,
                    width: 4,
                  ),
                ),
          boxShadow: isUser
              ? []
              : [
                  BoxShadow(
                    color: RastaTheme.gold.withOpacity(0.2),
                    blurRadius: 15,
                    spreadRadius: 2,
                  ),
                ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Lion icon for AI messages
            if (!isUser)
              Padding(
                padding: EdgeInsets.only(bottom: 8),
                child: Text('🦁', style: TextStyle(fontSize: 20)),
              ),
            // Message content
            Text(
              message,
              style: RastaTheme.textTheme.bodyMedium?.copyWith(
                color: RastaTheme.textPrimary,
                height: 1.5,
              ),
            ),
            // Attachments (files, images, etc.)
            if (attachments != null && attachments!.isNotEmpty) ...[
              SizedBox(height: 12),
              ...attachments!.map((attachment) => _buildAttachment(attachment)),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildAttachment(String attachment) {
    return Container(
      padding: EdgeInsets.all(12),
      margin: EdgeInsets.only(top: 8),
      decoration: BoxDecoration(
        color: RastaTheme.surfaceElevated,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: RastaTheme.gold.withOpacity(0.3),
          width: 1,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.insert_drive_file, color: RastaTheme.gold, size: 24),
          SizedBox(width: 12),
          Expanded(
            child: Text(
              attachment,
              style: RastaTheme.textTheme.bodySmall?.copyWith(
                color: RastaTheme.textPrimary,
              ),
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}
```

### 4. Loading Spinner (Braille + Fractal)

```dart
// ═══════════════════════════════════════════════════════════════
// FRACTAL SPINNER — RASTA COLORS + BRAILLE ANIMATION
// ═══════════════════════════════════════════════════════════════

class FractalSpinner extends StatefulWidget {
  final double size;
  final bool useBraille;

  const FractalSpinner({
    Key? key,
    this.size = 48,
    this.useBraille = true,
  }) : super(key: key);

  @override
  _FractalSpinnerState createState() => _FractalSpinnerState();
}

class _FractalSpinnerState extends State<FractalSpinner>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _rotation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: Duration(milliseconds: 1200),
      vsync: this,
    )..repeat();

    _rotation = Tween<double>(begin: 0, end: 2 * pi).animate(_controller);
  }

  @override
  Widget build(BuildContext context) {
    if (widget.useBraille) {
      // Braille spinner with Rasta colors
      return _BrailleSpinner(controller: _controller);
    } else {
      // Fractal spiral spinner
      return AnimatedBuilder(
        animation: _rotation,
        builder: (context, child) {
          return Transform.rotate(
            angle: _rotation.value,
            child: CustomPaint(
              size: Size(widget.size, widget.size),
              painter: _FractalSpiralPainter(),
            ),
          );
        },
      );
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }
}

class _BrailleSpinner extends StatelessWidget {
  final AnimationController controller;

  const _BrailleSpinner({Key? key, required this.controller}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final colors = [
      RastaTheme.red,
      RastaTheme.gold,
      RastaTheme.green,
      RastaTheme.gold,
    ];

    final frames = ['🔴', '🟡', '🟢', '🟡'];

    return AnimatedBuilder(
      animation: controller,
      builder: (context, child) {
        final frameIndex = (controller.value * 3).floor() % 4;
        return Text(
          frames[frameIndex],
          style: TextStyle(
            fontSize: 32,
            color: colors[frameIndex],
            shadows: [
              Shadow(
                color: colors[frameIndex].withOpacity(0.5),
                blurRadius: 10,
              ),
            ],
          ),
        );
      },
    );
  }
}

class _FractalSpiralPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final maxRadius = size.width / 2;

    // Draw 8 spiral arms (Rasta colors)
    for (int i = 0; i < 8; i++) {
      final paint = Paint()
        ..color = _getSpiralColor(i).withOpacity(0.6)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 3;

      final path = Path();
      final angleOffset = (i / 8) * 2 * pi;

      path.moveTo(center.dx, center.dy);

      for (double t = 0; t < 2 * pi; t += 0.1) {
        final radius = (t / (2 * pi)) * maxRadius;
        final angle = t + angleOffset;
        final x = center.dx + radius * cos(angle);
        final y = center.dy + radius * sin(angle);
        path.lineTo(x, y);
      }

      canvas.drawPath(path, paint);
    }
  }

  Color _getSpiralColor(int index) {
    final colors = [
      RastaTheme.red,
      RastaTheme.gold,
      RastaTheme.green,
      RastaTheme.gold,
      RastaTheme.red,
      RastaTheme.gold,
      RastaTheme.green,
      RastaTheme.gold,
    ];
    return colors[index % colors.length];
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
```

### 5. Bottom Navigation (UV Glow on Selection)

```dart
// ═══════════════════════════════════════════════════════════════
// BOTTOM NAV — 80DP HEIGHT WITH UV GLOW INDICATORS
// ═══════════════════════════════════════════════════════════════

class PsydelicBottomNav extends StatelessWidget {
  final int currentIndex;
  final Function(int) onTap;

  const PsydelicBottomNav({
    Key? key,
    required this.currentIndex,
    required this.onTap,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 80, // Thumb-friendly height
      decoration: BoxDecoration(
        color: RastaTheme.surface,
        boxShadow: [
          BoxShadow(
            color: RastaTheme.gold.withOpacity(0.1),
            blurRadius: 20,
            spreadRadius: 5,
          ),
        ],
      ),
      child: BottomNavigationBar(
        currentIndex: currentIndex,
        onTap: onTap,
        type: BottomNavigationBarType.fixed,
        backgroundColor: RastaTheme.surface,
        selectedItemColor: RastaTheme.gold,
        unselectedItemColor: RastaTheme.textTertiary,
        selectedLabelStyle: TextStyle(
          fontWeight: FontWeight.w700,
          fontSize: 12,
          color: RastaTheme.gold,
        ),
        unselectedLabelStyle: TextStyle(
          fontWeight: FontWeight.w500,
          fontSize: 12,
        ),
        elevation: 0,
        iconSize: 28,
        selectedFontSize: 12,
        unselectedFontSize: 12,
        items: [
          BottomNavigationBarItem(
            icon: Icon(Icons.home),
            label: 'Zion',
            // Active icon has UV glow
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.chat),
            label: 'Chat',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.auto_awesome),
            label: 'Tools',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.settings),
            label: 'Settings',
          ),
        ],
      ),
    );
  }
}
```

---

## 🎪 SCREEN DESIGNS

### Chat Screen (Main Interface)

```
┌─────────────────────────────────────────────────────────────────┐
│  🦁 RastaCoder                      ⚙️  👑  👤                  │  ← AppBar (Gold text, fractal bg)
├─────────────────────────────────────────────────────────────────┤
│  [Fractal background pattern - subtle gold on charcoal]         │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 🦁 Bless up! I compressed your video:                   │   │
│  │                                                         │   │
│  │ 📹 video_compressed.mp4                                 │   │
│  │    24.8 MB (was 156 MB)                                 │   │
│  │    [▶ Open]  [↗ Share]                                  │   │
│  │                                                         │   │
│  │ ✨ Used 3 FFmpeg iterations to hit target size.         │   │
│  └─────────────────────────────────────────────────────────┘   │
│    ╰─ Gold left border + UV glow                               │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Compress this video to under 25MB          │   │
│  └─────────────────────────────────────────────────────────┘   │
│    ╰─ User message (surface variant, right-aligned)            │
│                                                                  │
│  [🔴🟡🟢🟡] ← Fractal spinner (AI thinking)                      │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  [📎] [🎤] ─────────────────────────────── [🦁➤]               │  ← Input bar
│   Attach  Voice                    Send (Gold Lion, UV glow)   │
└─────────────────────────────────────────────────────────────────┘
│  🏠      💬      🛠️      ⚙️                                   │  ← Bottom nav (80dp)
│  Zion    Chat    Tools   Settings                              │
└─────────────────────────────────────────────────────────────────┘
```

### Settings Screen

```
┌─────────────────────────────────────────────────────────────────┐
│  ⚙️ Settings                                    🦁             │
├─────────────────────────────────────────────────────────────────┤
│  [Sacred geometry overlay - subtle Flower of Life pattern]      │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 🤖 AI Configuration                                     │   │
│  │ ─────────────────────────────────────────────────────── │   │
│  │ Cloud Mode                                      [▶]     │   │
│  │ Model: Claude Sonnet 4.5                        [▶]     │   │
│  │ API Key: •••••••••••••                          [✏]     │   │
│  └─────────────────────────────────────────────────────────┘   │
│    ╰─ Gold border, UV glow on tap                              │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 📱 On-Device AI (Offline Mode)                          │   │
│  │ ─────────────────────────────────────────────────────── │   │
│  │ Download Model                                   [⬇]    │   │
│  │ Qwen2.5-Coder-1.5B                               [✓]    │   │
│  │ RAM: 1.2GB / 4GB                                        │   │
│  │ [Fractal progress indicator]                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 🎨 Appearance                                           │   │
│  │ ─────────────────────────────────────────────────────── │   │
│  │ Theme: Psydelic Rasta                           [▶]     │   │
│  │ Icons: Spiritual + Fractal                      [▶]     │   │
│  │ Animations: On                                  [◉]     │   │
│  │ UV Glow Intensity: ████████░░ 80%               [─┬─]   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 💰 Pro Features (Upgrade to Unlock)                     │   │
│  │ ─────────────────────────────────────────────────────── │   │
│  │ Daily Token Limit: 100,000                      [✏]     │   │
│  │ Usage This Month: 45,230                                │   │
│  │                                                         │   │
│  │ [👑 Upgrade to Pro - $9.99/mo]                          │   │
│  │   ╰─ Gold button with UV glow                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📐 IMPLEMENTATION CHECKLIST

### Phase 1: Core Theme (Week 2)
- [ ] Update `rasta_theme.dart` with psydelic colors
- [ ] Add fractal gradient definitions
- [ ] Implement UV glow effects (box shadows, text shadows)
- [ ] Create sacred geometry painters
- [ ] Update splash screen with Lion's Fractal Mandala

### Phase 2: Components (Week 2-3)
- [ ] Build `FractalSpinner` widget
- [ ] Create `PsydelicMessageBubble` with gold borders
- [ ] Implement `PsydelicBottomNav` (80dp, UV glow)
- [ ] Design app icon (512x512px, Lion + Flower of Life)
- [ ] Create fractal background patterns

### Phase 3: Screen Updates (Week 3)
- [ ] Update chat screen with psydelic styling
- [ ] Redesign settings screen with sacred geometry
- [ ] Add UV glow to all interactive elements
- [ ] Implement Rasta color gradients throughout

### Phase 4: Polish (Week 3-4)
- [ ] Add haptic feedback patterns
- [ ] Create micro-animations (button press, transitions)
- [ ] Optimize performance (fractal rendering)
- [ ] Test on physical devices (UV effect visibility)

---

## 🎨 ASSET CREATION LIST

| Asset | Size | Format | Priority |
|-------|------|--------|----------|
| App Icon | 512x512, 1024x1024 | PNG | 🔴 HIGH |
| Splash Screen | Device-specific | PNG/SVG | 🔴 HIGH |
| Feature Graphics (Play Store) | 1024x500 | PNG | 🟡 MEDIUM |
| Promotional Banner | 1920x1080 | PNG | 🟡 MEDIUM |
| Fractal Background Pattern | 512x512 (tileable) | PNG/SVG | 🟡 MEDIUM |
| Sacred Geometry Overlays | Various | SVG | 🟢 LOW |
| Social Media Kit | Various | PNG | 🟢 LOW |

---

## 🔗 REFERENCES

### Azlaar's Style
- **DeviantArt:** [deviantart.com/azlaar](https://www.deviantart.com/azlaar)
- **Key Elements:** Sci-fi minimalism, dark atmospheric tones, geometric abstraction

### Psytrance Visual Culture
- **Fractal Art:** Mandelbrot sets, sacred geometry, algorithmic patterns
- **Color Schemes:** UV neon, high-contrast, psychedelic rainbow
- **Festival Aesthetics:** Boom Festival, Ozora, VooV Experience

### Rastafarian Symbolism
- **Colors:** Red (martyrs), Gold (wealth), Green (vegetation)
- **Symbols:** Lion of Judah, Star of David, Crown of Judah
- **Philosophy:** Zion vs Babylon, Ital lifestyle, Haile Selassie I

---

**Created:** March 16, 2026  
**Status:** Design Specification — Ready for Implementation  
**Next Step:** Begin Phase 1 (Core Theme updates to `rasta_theme.dart`)

*Baker Street Laboratory © 2026* 🔱  
*Jah Rastafari! 🦁🇯🇲🌀*
