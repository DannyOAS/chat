import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type Theme = 'light' | 'dark' | 'system'

interface ThemeState {
  theme: Theme
  setTheme: (theme: Theme) => void
  toggleTheme: () => void
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      theme: 'system',
      setTheme: (theme) => {
        set({ theme })

        // Apply theme to document
        const root = window.document.documentElement
        root.classList.remove('light', 'dark')

        if (theme === 'system') {
          const systemTheme = window.matchMedia('(prefers-color-scheme: dark)')
            .matches
            ? 'dark'
            : 'light'
          root.classList.add(systemTheme)
        } else {
          root.classList.add(theme)
        }
      },
      toggleTheme: () => {
        const currentTheme = get().theme
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark'
        get().setTheme(newTheme)
      },
    }),
    {
      name: 'theme-storage',
    }
  )
)

// Initialize theme on load
if (typeof window !== 'undefined') {
  const storedTheme = localStorage.getItem('theme-storage')
  if (storedTheme) {
    const { state } = JSON.parse(storedTheme)
    useThemeStore.getState().setTheme(state.theme)
  }
}
