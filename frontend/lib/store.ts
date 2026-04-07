import { create } from 'zustand'
import type { User } from './types'

interface AuthState {
  user: User | null
  roles: string[]
  hydrated: boolean
  setUser: (user: User | null) => void
  setHydrated: () => void
  hasRole: (role: string) => boolean
  isAdmin: () => boolean
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  roles: [],
  hydrated: false,
  setUser: (user) => set({ user, roles: user?.roles ?? [] }),
  setHydrated: () => set({ hydrated: true }),
  hasRole: (role) => get().roles.includes(role),
  isAdmin: () => get().roles.includes('ADMIN'),
}))

// ── Theme ───────────────────────────────────────────────────────────────────

type Theme = 'light' | 'dark'

interface ThemeState {
  theme: Theme
  setTheme: (theme: Theme) => void
  toggleTheme: () => void
}

function getInitialTheme(): Theme {
  if (typeof window === 'undefined') return 'light'
  const stored = localStorage.getItem('theme')
  if (stored === 'dark' || stored === 'light') return stored
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export const useThemeStore = create<ThemeState>((set, get) => ({
  theme: getInitialTheme(),
  setTheme: (theme) => {
    set({ theme })
    localStorage.setItem('theme', theme)
    document.documentElement.classList.toggle('dark', theme === 'dark')
  },
  toggleTheme: () => {
    const next = get().theme === 'dark' ? 'light' : 'dark'
    get().setTheme(next)
  },
}))

// ── Sidebar ─────────────────────────────────────────────────────────────────

interface SidebarState {
  open: boolean
  collapsed: boolean
  setOpen: (open: boolean) => void
  toggleOpen: () => void
  toggleCollapsed: () => void
}

function getInitialOpen(): boolean {
  if (typeof window === 'undefined') return true
  const stored = localStorage.getItem('sidebar_open')
  if (stored !== null) return stored === 'true'
  return window.innerWidth >= 768
}

function getInitialCollapsed(): boolean {
  if (typeof window === 'undefined') return false
  return localStorage.getItem('sidebar_collapsed') === 'true'
}

export const useSidebarStore = create<SidebarState>((set, get) => ({
  open: getInitialOpen(),
  collapsed: getInitialCollapsed(),
  setOpen: (open) => {
    set({ open })
    localStorage.setItem('sidebar_open', String(open))
  },
  toggleOpen: () => {
    const next = !get().open
    set({ open: next })
    localStorage.setItem('sidebar_open', String(next))
  },
  toggleCollapsed: () => {
    const next = !get().collapsed
    set({ collapsed: next })
    localStorage.setItem('sidebar_collapsed', String(next))
  },
}))
