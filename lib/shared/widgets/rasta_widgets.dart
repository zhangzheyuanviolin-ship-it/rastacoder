import 'dart:async';

import 'package:flutter/material.dart';

import '../../app/rasta_theme.dart';

/// Braille spinner animation with Rasta colors 🦁
///
/// Shows the classic Braille pattern spinner in Red, Gold, Green colors
/// representing the Rastafarian trinity.
class RastaBrailleSpinner extends StatefulWidget {
  final double size;
  final bool useRastaColors;

  const RastaBrailleSpinner({
    super.key,
    this.size = 24,
    this.useRastaColors = true,
  });

  @override
  State<RastaBrailleSpinner> createState() => _RastaBrailleSpinnerState();
}

class _RastaBrailleSpinnerState extends State<RastaBrailleSpinner> {
  int _frameIndex = 0;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _startAnimation();
  }

  void _startAnimation() {
    _timer = Timer.periodic(const Duration(milliseconds: 100), (timer) {
      setState(() {
        _frameIndex = (_frameIndex + 1) % RastaTheme.spinnerFrames.length;
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    // Respect reduce motion setting
    final reduceMotion = MediaQuery.of(context).disableAnimations;

    if (reduceMotion) {
      return SizedBox(
        width: widget.size,
        height: widget.size,
        child: Center(
          child: Text(
            '●',
            style: TextStyle(
              fontSize: widget.size * 0.9,
              color: RastaTheme.gold,
            ),
          ),
        ),
      );
    }

    return SizedBox(
      width: widget.size,
      height: widget.size,
      child: Center(
        child: Text(
          RastaTheme.spinnerFrames[_frameIndex],
          style: TextStyle(
            fontSize: widget.size * 0.9,
            height: 1.0,
            color: _getCurrentColor(),
          ),
          textAlign: TextAlign.center,
          textHeightBehavior: const TextHeightBehavior(
            applyHeightToFirstAscent: false,
            applyHeightToLastDescent: false,
          ),
        ),
      ),
    );
  }

  /// Cycle through Rasta colors based on frame index
  Color _getCurrentColor() {
    if (!widget.useRastaColors) {
      return RastaTheme.gold;
    }

    // Cycle: Red (0-1), Gold (2-3), Green (4-5), Gold (6-7)
    final index = _frameIndex % 8;
    if (index < 2) return RastaTheme.red;
    if (index < 4) return RastaTheme.gold;
    if (index < 6) return RastaTheme.green;
    return RastaTheme.gold;
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }
}

/// Lion of Judah FAB - Floating Action Button with Rasta theme 🦁
class LionFAB extends StatelessWidget {
  final VoidCallback onPressed;
  final String? tooltip;
  final bool disabled;

  const LionFAB({
    super.key,
    required this.onPressed,
    this.tooltip = 'New Action',
    this.disabled = false,
  });

  @override
  Widget build(BuildContext context) {
    return FloatingActionButton(
      onPressed: disabled ? null : onPressed,
      tooltip: tooltip,
      backgroundColor: disabled
          ? RastaTheme.textTertiary
          : RastaTheme.gold,
      foregroundColor: disabled
          ? RastaTheme.surface
          : RastaTheme.black,
      elevation: disabled ? 0 : 6,
      child: const Text(
        RastaTheme.iconLion,
        style: TextStyle(fontSize: 32),
      ),
    );
  }
}

/// Rasta-themed bottom navigation bar (80dp height, thumb-friendly)
class RastaBottomNav extends StatelessWidget {
  final int currentIndex;
  final ValueChanged<int> onTap;
  final List<NavDestination> destinations;

  const RastaBottomNav({
    super.key,
    required this.currentIndex,
    required this.onTap,
    required this.destinations,
  });

  @override
  Widget build(BuildContext context) {
    return NavigationBar(
      selectedIndex: currentIndex,
      onDestinationSelected: onTap,
      backgroundColor: RastaTheme.surface,
      indicatorColor: RastaTheme.gold.withOpacity(0.2),
      elevation: 8,
      height: 80, // Thumb-friendly height
      destinations: destinations.map((dest) {
        final isSelected = currentIndex == destinations.indexOf(dest);
        return NavigationDestination(
          icon: Text(
            dest.icon,
            style: TextStyle(
              fontSize: 24,
              color: isSelected ? RastaTheme.gold : RastaTheme.textSecondary,
            ),
          ),
          label: dest.label,
          selectedIcon: Text(
            dest.icon,
            style: const TextStyle(
              fontSize: 24,
              color: RastaTheme.gold,
            ),
          ),
        );
      }).toList(),
    );
  }
}

/// Navigation destination for RastaBottomNav
class NavDestination {
  final String icon;
  final String label;

  const NavDestination({
    required this.icon,
    required this.label,
  });
}

/// Gold-bordered card with Rasta styling
class RastaCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry? padding;
  final EdgeInsetsGeometry? margin;
  final Color? color;

  const RastaCard({
    super.key,
    required this.child,
    this.padding,
    this.margin,
    this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: margin ?? const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
      decoration: BoxDecoration(
        color: color ?? RastaTheme.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: RastaTheme.gold.withOpacity(0.3),
          width: 1,
        ),
        boxShadow: [
          BoxShadow(
            color: RastaTheme.gold.withOpacity(0.1),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Padding(
        padding: padding ?? const EdgeInsets.all(16),
        child: child,
      ),
    );
  }
}

/// Rasta-themed app bar with gradient
class RastaAppBar extends StatelessWidget implements PreferredSizeWidget {
  final String title;
  final List<Widget>? actions;
  final bool showGradient;
  final Widget? leading;

  const RastaAppBar({
    super.key,
    required this.title,
    this.actions,
    this.showGradient = true,
    this.leading,
  });

  @override
  Size get preferredSize => const Size.fromHeight(kToolbarHeight);

  @override
  Widget build(BuildContext context) {
    return AppBar(
      title: Text(
        title,
        style: const TextStyle(
          fontFamily: 'Shrikhand',
          fontSize: 22,
          fontWeight: FontWeight.w700,
        ),
      ),
      leading: leading,
      actions: actions,
      backgroundColor: RastaTheme.background,
      elevation: 0,
      centerTitle: true,
      flexibleSpace: showGradient
          ? Container(
              decoration: const BoxDecoration(
                gradient: RastaTheme.rastaGradient,
              ),
            )
          : null,
      titleTextStyle: const TextStyle(
        color: RastaTheme.black,
        fontSize: 22,
        fontWeight: FontWeight.w700,
        fontFamily: 'Shrikhand',
      ),
      iconTheme: const IconThemeData(
        color: RastaTheme.black,
        size: 24,
      ),
    );
  }
}
