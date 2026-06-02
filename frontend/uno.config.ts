import { defineConfig, presetAttributify, presetTypography, presetUno, presetIcons, presetWebFonts } from 'unocss'

export default defineConfig({
  presets: [
    presetUno(),
    presetAttributify(),
    presetTypography(),
    presetIcons({
      scale: 1.2,
      warn: true,
    }),
    presetWebFonts({
      fonts: {
        sans: 'Inter:400,500,600,700',
        mono: 'Fira Code',
      },
    }),
  ],
  shortcuts: {
    // 布局
    'flex-center': 'flex justify-center items-center',
    'flex-between': 'flex justify-between items-center',
    'flex-start': 'flex justify-start items-center',
    'flex-col-center': 'flex flex-col justify-center items-center',
    
    // 容器
    'container-base': 'max-w-6xl mx-auto px-4',
    'card-base': 'bg-#1a1a1a border border-#2a2a2a rounded-lg p-4',
    
    // 文字
    'text-primary': 'text-#ffffff',
    'text-secondary': 'text-#a0a0a0',
    'text-muted': 'text-#666666',
    
    // 颜色
    'bg-primary': 'bg-#000000',
    'bg-secondary': 'bg-#0f0f0f',
    'bg-card': 'bg-#1a1a1a',
    
    // 边框
    'border-base': 'border border-#2a2a2a',
    
    // 过渡
    'transition-base': 'transition-all duration-200 ease-in-out',
  },
  theme: {
    colors: {
      primary: '#000000',
      secondary: '#0f0f0f',
      card: '#1a1a1a',
      border: '#2a2a2a',
      muted: '#666666',
    },
  },
})