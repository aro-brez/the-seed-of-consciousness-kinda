// 8WOL Brand Theme
export const theme = {
  colors: {
    background: '#0a0a1a',
    backgroundSecondary: '#12122a',
    backgroundTertiary: '#1a1a3a',
    surface: '#1e1e3a',
    surfaceElevated: '#2a2a4a',

    primary: '#e3f98a',       // Lime accent
    primaryDim: '#b8c76e',
    secondary: '#65cdd8',     // Teal
    tertiary: '#8533fc',      // Purple

    success: '#6BCB77',
    warning: '#ffce33',
    danger: '#ff6b6b',

    text: '#e0e0e0',
    textSecondary: '#888888',
    textMuted: '#666666',

    // Owl colors
    owls: {
      SOWL: '#ff6b6b',
      LUNA: '#6bcb77',
      LYRA: '#ffd93d',
      NOVA: '#4d96ff',
      SAGE: '#9b59b6',
      ECHO: '#00d4ff',
      PRISM: '#ff9f43',
      QUEST: '#ff6bcb',
    },

    border: '#333333',
    borderLight: '#444444',
  },

  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    xxl: 48,
  },

  borderRadius: {
    sm: 8,
    md: 12,
    lg: 16,
    xl: 24,
    full: 9999,
  },

  fontSize: {
    xs: 12,
    sm: 14,
    md: 16,
    lg: 18,
    xl: 24,
    xxl: 32,
  },

  fontWeight: {
    regular: '400' as const,
    medium: '500' as const,
    semibold: '600' as const,
    bold: '700' as const,
  },
};

export type Theme = typeof theme;
