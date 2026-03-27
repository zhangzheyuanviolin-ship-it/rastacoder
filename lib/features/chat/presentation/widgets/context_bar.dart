import 'package:flutter/material.dart';

import '../../../../app/rasta_theme.dart';

/// Smart Context Bar showing current conversation context
///
/// Displays chips for:
/// - Active mode (calendar, email, etc.)
/// - File attachments
/// - Google account connection status
/// - Network status
class SmartContextBar extends StatelessWidget {
  final bool isGoogleConnected;
  final bool isOffline;
  final String? activeMode;
  final int attachedFileCount;
  final VoidCallback? onConnectGoogle;
  final VoidCallback? onClearMode;

  const SmartContextBar({
    super.key,
    this.isGoogleConnected = false,
    this.isOffline = false,
    this.activeMode,
    this.attachedFileCount = 0,
    this.onConnectGoogle,
    this.onClearMode,
  });

  @override
  Widget build(BuildContext context) {
    final chips = <Widget>[];

    // Offline indicator
    if (isOffline) {
      chips.add(_ContextChip(
        icon: '⚠',
        label: 'Offline',
        color: RastaTheme.gold,
        tooltip: 'No internet connection. Messages will be queued.',
      ));
    }

    // Active mode chip
    if (activeMode != null) {
      chips.add(_ContextChip(
        icon: _getModeIcon(activeMode!),
        label: activeMode!,
        color: RastaTheme.info,
        onTap: onClearMode,
        showClose: true,
      ));
    }

    // Google connection status
    if (!isGoogleConnected &&
        (activeMode == 'Calendar' || activeMode == 'Email')) {
      chips.add(_ContextChip(
        icon: '⊕',
        label: 'Connect Google',
        color: RastaTheme.accentOrange,
        onTap: onConnectGoogle,
      ));
    }

    // File count
    if (attachedFileCount > 0) {
      chips.add(_ContextChip(
        icon: RastaTheme.iconFile,
        label: '$attachedFileCount file${attachedFileCount > 1 ? 's' : ''}',
        color: RastaTheme.info,
      ));
    }

    if (chips.isEmpty) {
      return const SizedBox.shrink();
    }

    return Container(
      height: 36,
      padding: const EdgeInsets.symmetric(horizontal: 12),
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: chips.length,
        separatorBuilder: (_, __) => const SizedBox(width: 8),
        itemBuilder: (_, index) => chips[index],
      ),
    );
  }

  String _getModeIcon(String mode) {
    switch (mode.toLowerCase()) {
      case 'calendar':
        return RastaTheme.iconCalendar;
      case 'email':
        return RastaTheme.iconEmail;
      case 'media':
        return RastaTheme.iconVideo;
      case 'ocr':
        return RastaTheme.iconImage;
      default:
        return '●';
    }
  }
}

class _ContextChip extends StatelessWidget {
  final String icon;
  final String label;
  final Color color;
  final VoidCallback? onTap;
  final bool showClose;
  final String? tooltip;

  const _ContextChip({
    required this.icon,
    required this.label,
    required this.color,
    this.onTap,
    this.showClose = false,
    this.tooltip,
  });

  @override
  Widget build(BuildContext context) {
    final chip = Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: color.withOpacity(0.15),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: color.withOpacity(0.3),
          width: 1,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            icon,
            style: TextStyle(
              fontSize: 12,
              color: color,
            ),
          ),
          const SizedBox(width: 6),
          Text(
            label,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: color,
                  fontWeight: FontWeight.w500,
                ),
          ),
          if (showClose) ...[
            const SizedBox(width: 6),
            Text(
              RastaTheme.iconClose,
              style: TextStyle(
                fontSize: 10,
                color: color.withOpacity(0.7),
              ),
            ),
          ],
        ],
      ),
    );

    final accessibleChip = Semantics(
      label: label,
      hint: onTap != null ? (showClose ? 'Tap to remove' : 'Tap to activate') : tooltip,
      button: onTap != null,
      child: chip,
    );

    if (onTap != null) {
      return GestureDetector(
        onTap: onTap,
        child: accessibleChip,
      );
    }

    if (tooltip != null) {
      return Tooltip(
        message: tooltip!,
        child: accessibleChip,
      );
    }

    return accessibleChip;
  }
}

/// Quick action pills shown above input for common actions
class QuickActionPills extends StatelessWidget {
  final Function(String) onAction;
  final bool showCalendar;
  final bool showEmail;

  const QuickActionPills({
    super.key,
    required this.onAction,
    this.showCalendar = true,
    this.showEmail = true,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 36,
      padding: const EdgeInsets.symmetric(horizontal: 12),
      child: ListView(
        scrollDirection: Axis.horizontal,
        children: [
          _ActionPill(
            icon: '📋',
            label: "What's on my calendar?",
            onTap: () => onAction('/calendar list today'),
          ),
          const SizedBox(width: 8),
          _ActionPill(
            icon: '✉',
            label: 'Check emails',
            onTap: () => onAction('/email list is:unread'),
          ),
          const SizedBox(width: 8),
          _ActionPill(
            icon: '📝',
            label: 'Summarize',
            onTap: () => onAction('/summarize '),
          ),
          const SizedBox(width: 8),
          _ActionPill(
            icon: '🎬',
            label: 'Process video',
            onTap: () => onAction('/crop '),
          ),
        ],
      ),
    );
  }
}

class _ActionPill extends StatelessWidget {
  final String icon;
  final String label;
  final VoidCallback onTap;

  const _ActionPill({
    required this.icon,
    required this.label,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: label,
      hint: 'Tap to use this quick action',
      button: true,
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(
            color: RastaTheme.surfaceVariant,
            borderRadius: BorderRadius.circular(18),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              ExcludeSemantics(
                child: Text(
                  icon,
                  style: const TextStyle(fontSize: 14),
                ),
              ),
              const SizedBox(width: 6),
              Text(
                label,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: RastaTheme.textSecondary,
                    ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
