/** @type {import('tailwindcss').Config} */

// Token system for NIGRANI frontend redesign (see NIGRANI-FRONTEND-PLAN.md §4).
// All existing tokens are extended/preserved so existing pages keep working.
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    // Spacing scale: 4/8/16/24/32/48 and 72px section rhythm.
    spacing: {
      0: '0px',
      px: '1px',
      1: '4px',
      2: '8px',
      4: '16px',
      6: '24px',
      8: '32px',
      12: '48px',
      18: '72px',
      // Round-3 card and control spacing tokens (F1)
      'card-x': '26px',
      'card-y': '22px',
      'card-gap': '16px',
      'grid-gap': '20px',
      'stack-sm': '8px',
      'stack-md': '14px',
      'stack-lg': '20px',
      'btn-gap': '12px',
    },
    // One radius (4px) everywhere.
    borderRadius: {
      none: '0px',
      DEFAULT: '4px',
      sm: '4px',
      md: '4px',
      lg: '4px',
    },
    colors: {
      transparent: 'transparent',
      current: 'currentColor',
      white: '#FFFFFF',

      // Brand palette — semantic
      bg: '#FAF8F4',
      navy: '#132A47',
      green: '#2E7D5B',
      gold: '#C8952B',
      coral: '#D4573D',

      // Institutional portal tokens (§4.1)
      paper: '#FFFFFF',
      'paper-sunk': '#F4F6F8',
      portal: '#0B2E4F',
      'portal-deep': '#071F36',
      'portal-tint': '#E8EFF5',
      rule: '#D5DEE6',
      'rule-strong': '#A9BCCB',
      saffron: '#E07A2F',

      // Text tokens
      ink: '#14171A',
      'ink-secondary': '#5B6169',
      'ink-muted': '#94989E',

      // Border tokens
      border: '#DDD9D0',
      'border-strong': '#C7C2B6',

      // Surface tokens
      surface: '#FFFFFF',
      'surface-sunk': '#F3F0EA',
    },
    extend: {
      fontSize: {
        // Landing page and heroes (§4.2, Part B4)
        hero: ['64px', { lineHeight: '1.04', fontWeight: '600', letterSpacing: '-0.015em' }],
        'hero-sub': ['26px', { lineHeight: '1.35', fontWeight: '400' }],
        'band-title': ['40px', { lineHeight: '1.15', fontWeight: '600' }],
        'section-title': ['30px', { lineHeight: '1.2', fontWeight: '600' }],
        stat: ['42px', { lineHeight: '1.0', fontWeight: '600' }],
        'stat-label': ['13px', { lineHeight: '1.4', letterSpacing: '0.04em', fontWeight: '500' }],
        lede: ['21px', { lineHeight: '1.6', fontWeight: '400' }],

        // Interior scale floor per Part C2
        'score-display': ['48px', { lineHeight: '1', fontWeight: '600' }],
        'page-title': ['38px', { lineHeight: '1.2', fontWeight: '600' }],
        'section-heading': ['26px', { lineHeight: '1.3', fontWeight: '600' }],
        body: ['17px', { lineHeight: '1.5' }],
        'body-secondary': ['15px', { lineHeight: '1.5' }],
        'meta-label': ['13px', { lineHeight: '1.4', letterSpacing: '0.04em', fontWeight: '500' }],
        'table-header': ['13px', { lineHeight: '1.4', letterSpacing: '0.04em', fontWeight: '500' }],
        'table-cell': ['16px', { lineHeight: '1.5' }],
        btn: ['16px', { lineHeight: '1.4', fontWeight: '600' }],
      },
      fontFamily: {
        display: ['"Source Serif 4"', '"Noto Sans Devanagari"', '"Noto Sans Gujarati"', 'Fraunces', 'Georgia', 'serif'],
        sans: ['Inter', '"Noto Sans Devanagari"', '"Noto Sans Gujarati"', 'system-ui', 'sans-serif'],
        devanagari: ['"Noto Sans Devanagari"', 'sans-serif'],
        gujarati: ['"Noto Sans Gujarati"', 'sans-serif'],
      },
      width: {
        sidebar: '288px',
      },
      height: {
        topbar: '60px',
        masthead: '88px',
        utility: '36px',
      },
      minHeight: {
        region: '320px',
      },
      boxShadow: {
        card: '0 1px 2px rgba(19, 42, 71, 0.06)',
      },
    },
  },
  plugins: [],
}
