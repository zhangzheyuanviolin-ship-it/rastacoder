import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Coderasta - Rastafarian Theme 🦁🇯🇲
///
/// Design Philosophy:
/// - Deep earth tones representing the African soil
/// - Red, Gold, Green colors of the Ethiopian flag
/// - Lion of Judah symbolism
/// - Natural, organic, spiritual aesthetic
/// - Terminal meets Caribbean vibes
class RastaTheme {
  // ═══════════════════════════════════════════════════════════════
  // RASTAFARIAN COLORS
  // ═══════════════════════════════════════════════════════════════
  
  /// **Red** - The blood of martyrs, sacrifice, struggle
  static const Color red = Color(0xFFCE1126);
  static const Color redLight = Color(0xFFFF4D4D);
  static const Color redDark = Color(0xFF8B0000);
  
  /// **Gold/Yellow** - The wealth of the homeland, sunshine, prosperity
  static const Color gold = Color(0xFFFFD700);
  static const Color goldLight = Color(0xFFFFE84D);
  static const Color goldDark = Color(0xFFB8860B);
  
  /// **Green** - The vegetation, hope, agricultural wealth of Ethiopia
  static const Color green = Color(0xFF009B3A);
  static const Color greenLight = Color(0xFF32CD32);
  static const Color greenDark = Color(0xFF006400);
  
  /// **Black** - The African people, strength, identity
  static const Color black = Color(0xFF1A1A1A);
  static const Color blackLight = Color(0xFF2D2D2D);
  static const Color charcoal = Color(0xFF0F0F12);
  
  /// **Earth tones** - Natural, organic colors
  static const Color earth = Color(0xFF8B4513);
  static const Color sand = Color(0xFFD2B48C);
  static const Color soil = Color(0xFF654321);

  // ═══════════════════════════════════════════════════════════════
  // UI COLORS
  // ═══════════════════════════════════════════════════════════════
  
  static const Color background = charcoal;
  static const Color surface = Color(0xFF1E1E24);
  static const Color surfaceVariant = Color(0xFF2A2A35);
  static const Color surfaceElevated = Color(0xFF353540);

  static const Color textPrimary = Color(0xFFFFF8E7);
  static const Color textSecondary = Color(0xFFD4C5A3);
  static const Color textTertiary = Color(0xFF8B8370);
  static const Color textGold = Color(0xFFFFD700);

  static const Color error = red;
  static const Color warning = gold;
  static const Color success = green;
  static const Color info = Color(0xFF4FC3F7);

  // Accent colors
  static const Color accentRed = red;
  static const Color accentGold = gold;
  static const Color accentGreen = green;
  static const Color accentPurple = Color(0xFF9C27B0);
  static const Color accentOrange = Color(0xFFFF9800);

  // ═══════════════════════════════════════════════════════════════
  // RASTAFARIAN SYMBOLS (Unicode)
  // ═══════════════════════════════════════════════════════════════
  
  /// Lion of Judah 🦁
  static const String iconLion = '🦁';
  static const String iconLionUnicode = '♌';
  
  /// Ethiopian Star of David ✡
  static const String iconStar = '⭐';
  static const String iconStarDavid = '✡';
  
  /// Crown of Judah 👑
  static const String iconCrown = '👑';
  
  /// Drum 🥁
  static const String iconDrum = '🥁';
  
  /// Fire 🔥
  static const String iconFire = '🔥';
  
  /// Leaf 🌿
  static const String iconLeaf = '🌿';
  
  /// Earth 🌍
  static const String iconEarth = '🌍';
  
  /// Sun ☀️
  static const String iconSun = '☀️';
  
  /// Moon 🌙
  static const String iconMoon = '🌙';
  
  /// Lightning ⚡
  static const String iconLightning = '⚡';
  
  /// Peace sign ✌️
  static const String iconPeace = '✌️';
  
  /// Raised fist ✊
  static const String iconFist = '✊';
  
  /// Hands folded 🙏
  static const String iconPrayer = '🙏';
  
  /// Musical note 🎵
  static const String iconMusic = '🎵';
  
  /// Reggae guitar 🎸
  static const String iconGuitar = '🎸';

  // Braille spinner animation frames (Rasta colors)
  static const List<String> spinnerFrames = [
    '⣷', '⣯', '⣟', '⡿', '⢿', '⣻', '⣽', '⣾',
  ];

  // Voice waveform characters
  static const List<String> waveformChars = ['▂', '▃', '▅', '▇', '█'];

  // Status indicators
  static const String iconCheck = '✓';
  static const String iconError = '✗';
  static const String iconWarning = '⚠';
  static const String iconInfo = 'ℹ';
  static const String iconSend = '➤';
  static const String iconClose = '✕';
  static const String iconMenu = '☰';
  static const String iconAdd = '⊕';
  static const String iconSearch = '🔍';
  static const String iconSettings = '⚙';
  static const String iconHome = '🏠';
  static const String iconBack = '◀';
  static const String iconForward = '▶';
  static const String iconRefresh = '🔄';
  static const String iconDownload = '⬇';
  static const String iconUpload = '⬆';
  static const String iconShare = '↗';
  static const String iconCopy = '📋';
  static const String iconDelete = '🗑';
  static const String iconEdit = '✏';
  static const String iconSave = '💾';
  static const String iconLock = '🔒';
  static const String iconUnlock = '🔓';
  static const String iconUser = '👤';
  static const String iconAI = '🤖';
  static const String iconBrain = '🧠';
  static const String iconSparkle = '✨';
  static const String iconZion = '🏔';
  static const String iconBabylon = '🏙';

  // Voice icons
  static const String iconVoiceIdle = '●';
  static const String iconVoiceRecording = '■';

  // File type icons
  static const String iconFile = '◰';
  static const String iconImage = '◫';
  static const String iconVideo = '▶';
  static const String iconAudio = '♪';
  static const String iconLocation = '◉';
  static const String iconCalendar = '◫';
  static const String iconEmail = '✉';

  // Status indicators
  static const String iconCheck = '✓';
  static const String iconError = '✗';
  static const String iconWarning = '⚠';
  static const String iconInfo = 'ℹ';
  static const String iconSend = '➤';
  static const String iconClose = '✕';
  static const String iconMenu = '☰';
  static const String iconAdd = '⊕';
  static const String iconSearch = '🔍';
  static const String iconSettings = '⚙';
  static const String iconHome = '🏠';
  static const String iconBack = '◀';
  static const String iconForward = '▶';
  static const String iconRefresh = '🔄';
  static const String iconDownload = '⬇';
  static const String iconUpload = '⬆';
  static const String iconShare = '↗';
  static const String iconCopy = '📋';
  static const String iconDelete = '🗑';
  static const String iconEdit = '✏';
  static const String iconSave = '💾';
  static const String iconLock = '🔒';
  static const String iconUnlock = '🔓';
  static const String iconUser = '👤';
  static const String iconAI = '🤖';
  static const String iconBrain = '🧠';
  static const String iconSparkle = '✨';
  static const String iconZion = '🏔';
  static const String iconBabylon = '🏙';

  // ═══════════════════════════════════════════════════════════════
  // RASTAFARIAN PHILOSOPHY DATASET
  // ═══════════════════════════════════════════════════════════════
  
  /// Core Rastafarian principles for AI responses
  static const Map<String, String> rastaPhilosophy = {
    'jah': 'Jah is the Almighty, the Creator, the God of Ethiopia. Rastafari livity is centered on the divinity of Haile Selassie I.',
    'zion': 'Zion represents the promised land, Ethiopia, Africa - the homeland. It symbolizes peace, freedom, and righteousness.',
    'babylon': 'Babylon represents the oppressive systems of the West, corruption, materialism, and mental slavery.',
    'livity': 'Livity is the Rastafarian way of life - natural, righteous living in harmony with nature and Jah.',
    'ital': 'Ital means natural, pure, unprocessed food and lifestyle. No artificial additives, often vegetarian/vegan.',
    'reasoning': 'Reasoning is the practice of communal discussion, meditation, and spiritual dialogue among Rastafari.',
    'nyabinghi': 'Nyabinghi is the oldest Rastafari mansion, featuring drumming ceremonies and spiritual gatherings.',
    'twelve_tribes': 'The Twelve Tribes of Israel is a Rastafari organization founded by Prophet Gad, with Haile Selassie as the 22nd descendant.',
    'haile_selassie': 'Emperor Haile Selassie I of Ethiopia (1892-1975), crowned King of Kings, Lord of Lords, Conquering Lion of the Tribe of Judah.',
    'ethiopia': 'Ethiopia is the spiritual homeland, the only African nation to resist colonization, symbol of African pride.',
    'repatriation': 'The belief in returning to Africa, the ancestral homeland, freedom from Babylon.',
    'ganja': 'Ganja (cannabis) is used sacramentally in reasoning sessions for meditation and spiritual enlightenment.',
    'dreadlocks': 'Dreadlocks represent the Lion of Judah, the Nazarite vow, and rejection of Babylon vanity.',
    'red_gold_green': 'The Rastafarian flag colors: Red (blood of martyrs), Gold (wealth of homeland), Green (vegetation of Zion).',
  };

  /// Rastafarian greetings and phrases
  static const Map<String, String> rastaPhrases = {
    'bless_up': 'Bless up - Expression of positivity and gratitude',
    'give_thanks': 'Give thanks - Expression of gratitude to Jah',
    'irie': 'Irie - Everything is good, positive vibes',
    'yaad': 'Yaad - Home, familiar place',
    'irie_vibes': 'Irie vibes - Good energy, positive atmosphere',
    'no_babylon': 'No Babylon - Rejecting negative systems',
    'zion_high': 'Zion high - Spiritual elevation',
    'jah_guide': 'Jah guide - May God guide you',
    'selassie_i': 'Selassie I - Reference to Haile Selassie',
    'conquering_lion': 'Conquering Lion of the Tribe of Judah',
  };

  // ═══════════════════════════════════════════════════════════════
  // FONTS
  // ═══════════════════════════════════════════════════════════════
  
  /// Get the UI font family using Google Fonts
  static String get fontFamilyUI => GoogleFonts.nunitoSans().fontFamily!;
  
  /// Get the monospace font family
  static String get fontFamilyMono => GoogleFonts.jetBrainsMono().fontFamily!;
  
  /// Get a Rastafarian-inspired display font
  static String get fontFamilyDisplay => GoogleFonts.shrikhand().fontFamily!;

  // ═══════════════════════════════════════════════════════════════
  // THEME DATA
  // ═══════════════════════════════════════════════════════════════
  
  static ThemeData get darkTheme {
    final baseTextTheme = GoogleFonts.nunitoSansTextTheme(
      ThemeData.dark().textTheme,
    );

    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: background,
      colorScheme: ColorScheme.dark(
        primary: gold,
        onPrimary: black,
        secondary: green,
        onSecondary: textPrimary,
        tertiary: red,
        onTertiary: textPrimary,
        surface: surface,
        onSurface: textPrimary,
        error: error,
        onError: textPrimary,
        outline: gold.withOpacity(0.3),
      ),
      textTheme: baseTextTheme.copyWith(
        displayLarge: baseTextTheme.displayLarge?.copyWith(
          fontSize: 36,
          fontWeight: FontWeight.w800,
          color: gold,
          fontFamily: fontFamilyDisplay,
        ),
        displayMedium: baseTextTheme.displayMedium?.copyWith(
          fontSize: 30,
          fontWeight: FontWeight.w700,
          color: textGold,
        ),
        displaySmall: baseTextTheme.displaySmall?.copyWith(
          fontSize: 26,
          fontWeight: FontWeight.w700,
          color: textPrimary,
        ),
        headlineMedium: baseTextTheme.headlineMedium?.copyWith(
          fontSize: 22,
          fontWeight: FontWeight.w600,
          color: textPrimary,
        ),
        titleLarge: baseTextTheme.titleLarge?.copyWith(
          fontSize: 20,
          fontWeight: FontWeight.w600,
          color: textPrimary,
        ),
        titleMedium: baseTextTheme.titleMedium?.copyWith(
          fontSize: 17,
          fontWeight: FontWeight.w600,
          color: textPrimary,
        ),
        bodyLarge: baseTextTheme.bodyLarge?.copyWith(
          fontSize: 16,
          fontWeight: FontWeight.w400,
          color: textPrimary,
        ),
        bodyMedium: baseTextTheme.bodyMedium?.copyWith(
          fontSize: 14,
          fontWeight: FontWeight.w400,
          color: textSecondary,
        ),
        bodySmall: baseTextTheme.bodySmall?.copyWith(
          fontSize: 12,
          fontWeight: FontWeight.w400,
          color: textTertiary,
        ),
        labelLarge: baseTextTheme.labelLarge?.copyWith(
          fontSize: 14,
          fontWeight: FontWeight.w600,
          color: textPrimary,
        ),
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: background,
        elevation: 0,
        centerTitle: true,
        titleTextStyle: GoogleFonts.nunitoSans(
          fontSize: 22,
          fontWeight: FontWeight.w700,
          color: gold,
        ),
        iconTheme: const IconThemeData(color: gold),
      ),
      cardTheme: CardTheme(
        color: surface,
        elevation: 2,
        shadowColor: gold.withOpacity(0.1),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: BorderSide(
            color: gold.withOpacity(0.2),
            width: 1,
          ),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: surfaceVariant,
        hintStyle: const TextStyle(color: textTertiary),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide.none,
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide.none,
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide(color: gold, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: red, width: 2),
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: gold,
          foregroundColor: black,
          elevation: 4,
          shadowColor: gold.withOpacity(0.4),
          padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
          textStyle: GoogleFonts.nunitoSans(
            fontSize: 16,
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: gold,
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
          textStyle: GoogleFonts.nunitoSans(
            fontSize: 14,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: gold,
          side: const BorderSide(color: gold, width: 2),
          padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
          textStyle: GoogleFonts.nunitoSans(
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: surfaceVariant,
        selectedColor: green.withOpacity(0.3),
        labelStyle: GoogleFonts.nunitoSans(
          fontSize: 13,
          fontWeight: FontWeight.w600,
          color: textPrimary,
        ),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(24),
          side: BorderSide(color: gold.withOpacity(0.3)),
        ),
      ),
      dividerTheme: const DividerThemeData(
        color: surfaceElevated,
        thickness: 1,
      ),
      bottomSheetTheme: const BottomSheetThemeData(
        backgroundColor: surface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
        ),
      ),
      snackBarTheme: SnackBarThemeData(
        backgroundColor: surfaceElevated,
        contentTextStyle: GoogleFonts.nunitoSans(
          fontSize: 14,
          color: textPrimary,
        ),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
        behavior: SnackBarBehavior.floating,
      ),
      floatingActionButtonTheme: const FloatingActionButtonThemeData(
        backgroundColor: gold,
        foregroundColor: black,
        elevation: 6,
      ),
      iconTheme: const IconThemeData(
        color: gold,
        size: 24,
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: surface,
        indicatorColor: gold.withOpacity(0.2),
        labelTextStyle: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return GoogleFonts.nunitoSans(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: gold,
            );
          }
          return GoogleFonts.nunitoSans(
            fontSize: 12,
            fontWeight: FontWeight.w500,
            color: textSecondary,
          );
        }),
      ),
    );
  }

  /// Monospace text style for code/logs
  static TextStyle get monoStyle => GoogleFonts.jetBrainsMono(
    fontSize: 13,
    fontWeight: FontWeight.w400,
    color: textPrimary,
    height: 1.5,
  );

  /// Monospace text style for inline code (gold accent)
  static TextStyle get monoInlineStyle => GoogleFonts.jetBrainsMono(
    fontSize: 13,
    fontWeight: FontWeight.w400,
    color: accentGold,
    backgroundColor: surfaceVariant,
  );

  /// Rastafarian gradient (Red, Gold, Green)
  static const LinearGradient rastaGradient = LinearGradient(
    colors: [red, gold, green],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  /// Lion gradient (Gold to Orange)
  static const LinearGradient lionGradient = LinearGradient(
    colors: [gold, accentOrange],
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
  );

  /// Earth gradient (Brown tones)
  static const LinearGradient earthGradient = LinearGradient(
    colors: [soil, earth, sand],
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
  );

  /// Zion sunrise (Green → Gold → Red)
  static const LinearGradient zionSunriseGradient = LinearGradient(
    colors: [green, gold, red],
    begin: Alignment.bottomCenter,
    end: Alignment.topCenter,
  );

  /// Babylon night (Deep Black → Purple → Red)
  static const LinearGradient babylonNightGradient = LinearGradient(
    colors: [charcoal, accentPurple, redDark],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  /// Fractal depth gradient (Black → Purple → Electric Blue)
  static const LinearGradient fractalDepthGradient = LinearGradient(
    colors: [charcoal, Color(0xFF2D004E), Color(0xFF00F0FF)],
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
  );

  // ═══════════════════════════════════════════════════════════════
  // SLASH COMMANDS
  // ═══════════════════════════════════════════════════════════════

  /// Common slash commands for quick actions
  static const Map<String, SlashCommand> slashCommands = {
    '/crop': SlashCommand(
      name: '/crop',
      description: 'Crop a video to focus on faces',
      icon: '✂',
      category: 'media',
    ),
    '/extract': SlashCommand(
      name: '/extract',
      description: 'Extract audio from video',
      icon: '♪',
      category: 'media',
    ),
    '/summarize': SlashCommand(
      name: '/summarize',
      description: 'Summarize a document or webpage',
      icon: '◰',
      category: 'text',
    ),
    '/ocr': SlashCommand(
      name: '/ocr',
      description: 'Extract text from an image',
      icon: '◫',
      category: 'text',
    ),
    '/calendar': SlashCommand(
      name: '/calendar',
      description: 'View or create calendar events',
      icon: '◫',
      category: 'google',
    ),
    '/email': SlashCommand(
      name: '/email',
      description: 'Read or send emails',
      icon: '✉',
      category: 'google',
    ),
    '/download': SlashCommand(
      name: '/download',
      description: 'Download media from URL',
      icon: '↓',
      category: 'media',
    ),
    '/pdf': SlashCommand(
      name: '/pdf',
      description: 'Create or read PDF documents',
      icon: '◰',
      category: 'text',
    ),
  };
}

/// Slash command definition
class SlashCommand {
  final String name;
  final String description;
  final String icon;
  final String category;

  const SlashCommand({
    required this.name,
    required this.description,
    required this.icon,
    required this.category,
  });
}
