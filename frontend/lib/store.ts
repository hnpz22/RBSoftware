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
