import { create } from 'zustand'
import type { User } from './types'

interface AuthState {
  user: User | null
  hydrated: boolean
  setUser: (user: User | null) => void
  setHydrated: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  hydrated: false,
  setUser: (user) => set({ user }),
  setHydrated: () => set({ hydrated: true }),
}))
