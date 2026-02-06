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
  },
  theme: {
    colors: {
      primary: '#18a058',
      primaryHover: '#36ad6a',
      secondary: '#2080f0',
      success: '#18a058',
      warning: '#f0a020',
      error: '#d03050',
      info: '#2080f0',
    },
  },
})