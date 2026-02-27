import type { GlobalThemeOverrides } from 'naive-ui'

export const naiveThemeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#7c3aed',
    primaryColorHover: '#8b5cf6',
    primaryColorPressed: '#6d28d9',
    primaryColorSuppl: '#a78bfa',

    infoColor: '#3b82f6',
    infoColorHover: '#60a5fa',
    infoColorPressed: '#2563eb',

    successColor: '#22c55e',
    successColorHover: '#4ade80',
    successColorPressed: '#16a34a',

    bodyColor: '#000000',
    cardColor: '#050507',
    modalColor: '#050507',
    popoverColor: '#050507',

    textColorBase: '#ffffff',
    textColor1: '#ffffff',
    textColor2: '#d4d4d8',
    textColor3: '#a1a1aa',

    borderColor: 'rgba(255, 255, 255, 0.72)',
    dividerColor: 'rgba(255, 255, 255, 0.28)',

    borderRadius: '0px',
    borderRadiusSmall: '0px',
    fontWeightStrong: '600',
  },
  Input: {
    borderRadius: '0px',
    color: '#050507',
    colorFocus: '#050507',
    colorFocusError: '#050507',
  },
  Button: {
    borderRadiusSmall: '0px',
    borderRadiusMedium: '0px',
    borderRadiusLarge: '0px',
    textColorPrimary: '#ffffff',
    textColorHoverPrimary: '#ffffff',
    textColorPressedPrimary: '#ffffff',
  },
  Card: {
    borderRadius: '0px',
  },
  Drawer: {
    borderRadius: '0px',
  },
  Modal: {
    borderRadius: '0px',
  },
  Tabs: {
    tabBorderRadius: '0px',
  },
  Tag: {
    borderRadius: '0px',
  },
}
