import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Obsidian Black Base
        'oled': '#030305',
        'surface': {
          DEFAULT: '#08080C',
          elevated: '#0E0E14',
          overlay: '#14141C',
        },
        // Electric Amber/Orange Accent System
        'accent': {
          amber: '#F59E0B',
          orange: '#EA580C',
          'amber-glow': '#FBBF24',
          'burnt-orange': '#C2410C',
          crimson: '#FF003C',
        },
        // Legacy support
        'cyan': '#00F0FF',
        'emerald': '#00FF66',
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.7)',
        'glass-elevated': '0 12px 40px 0 rgba(0, 0, 0, 0.85)',
        'neon-amber': '0 0 20px rgba(245, 158, 11, 0.4)',
        'neon-orange': '0 0 20px rgba(234, 88, 12, 0.4)',
        'neon-crimson': '0 0 20px rgba(255, 0, 60, 0.35)',
        'amber-glow': '0 0 30px rgba(251, 191, 36, 0.25)',
      },
      fontFamily: {
        sans: ['var(--font-inter)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-jetbrains)', 'monospace'],
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        'amber-ambient': 'radial-gradient(circle at 50% -20%, rgba(245, 158, 11, 0.1), rgba(234, 88, 12, 0.05) 40%, transparent 80%)',
        'obsidian-gradient': 'linear-gradient(180deg, #030305 0%, #08080C 50%, #0E0E14 100%)',
      },
      animation: {
        'amber-pulse': 'amber-pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow-pulse': 'glow-pulse 3s ease-in-out infinite',
      },
      keyframes: {
        'amber-pulse': {
          '0%, 100%': {
            opacity: '1',
            boxShadow: '0 0 8px rgba(245, 158, 11, 0.6)',
          },
          '50%': {
            opacity: '0.7',
            boxShadow: '0 0 2px rgba(245, 158, 11, 0.3)',
          },
        },
        'glow-pulse': {
          '0%, 100%': {
            boxShadow: '0 0 20px rgba(245, 158, 11, 0.3)',
          },
          '50%': {
            boxShadow: '0 0 40px rgba(245, 158, 11, 0.5)',
          },
        },
      },
    },
  },
  plugins: [],
};

export default config;
