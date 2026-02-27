import { defineConfig, presetUno, presetAttributify, presetIcons, presetWind } from 'unocss'

export default defineConfig({
  presets: [
    presetUno(),
    presetAttributify(),
    presetIcons({
      scale: 1.2,
      warn: true,
    }),
    presetWind(),
  ],
  shortcuts: {
    'flex-center': 'flex items-center justify-center',
    'flex-between': 'flex items-center justify-between',
    'flex-col-center': 'flex flex-col items-center justify-center',
    'absolute-center': 'absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2',
    'text-ellipsis': 'truncate overflow-hidden whitespace-nowrap',
    'sci-panel': 'tech-panel bg-bg-surface border border-line-primary rounded-none relative overflow-hidden',
    'sci-divider': 'border-0 border-t border-line-muted',
    'sci-accent-text': 'text-accent-violet',
  },
  theme: {
    colors: {
      bg: {
        base: '#000000',
        surface: '#050507',
      },
      text: {
        primary: '#ffffff',
        muted: '#a1a1aa',
      },
      line: {
        primary: 'rgba(255,255,255,0.72)',
        muted: 'rgba(255,255,255,0.28)',
      },
      accent: {
        violet: '#7c3aed',
        blue: '#3b82f6',
        green: '#22c55e',
      },
      primary: '#7c3aed',
      primaryHover: '#8b5cf6',
      secondary: '#3b82f6',
      success: '#22c55e',
      warning: '#f59e0b',
      error: '#ef4444',
      info: '#3b82f6',
    },
  },
})