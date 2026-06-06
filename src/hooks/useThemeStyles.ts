import { useTheme } from '../contexts/ThemeContext';

export function useThemeStyles() {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  return {
    isDark,
    // Backgrounds
    sectionBg: isDark ? 'bg-graphite-950' : 'bg-lightBg',
    sectionBgSecondary: isDark ? 'bg-graphite-900/50' : 'bg-lightBgSecondary',

    // Text
    textPrimary: isDark ? 'text-ivory-100' : 'text-lightText',
    textSecondary: isDark ? 'text-ivory-300/70' : 'text-lightTextSecondary',
    textMuted: isDark ? 'text-ivory-400/60' : 'text-lightTextSecondary/60',

    // Borders
    border: isDark ? 'border-ivory-100/10' : 'border-lightBorder',
    borderLight: isDark ? 'border-ivory-100/20' : 'border-lightBorder/50',

    // Accents
    accentGold: isDark ? 'text-gold-400' : 'text-gold-600',
    accentGoldBg: isDark ? 'bg-gold-500/10' : 'bg-gold-100/20',
  };
}
