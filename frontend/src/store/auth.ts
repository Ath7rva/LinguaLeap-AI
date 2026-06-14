import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { User } from '../types'

interface AuthState {
  user: User | null
  token: string | null
  refreshToken: string | null
  setAuth: (user: User, token: string, refreshToken?: string) => void
  updateXP: (xp: number) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      refreshToken: null,

      setAuth: (user, token, refreshToken) => {
        localStorage.setItem('token', token)
        if (refreshToken) localStorage.setItem('refresh_token', refreshToken)
        set((state) => ({ user, token, refreshToken: refreshToken || state.refreshToken }))
      },

      updateXP: (xp) =>
        set((state) => ({
          user: state.user ? { ...state.user, xp } : null,
        })),

      logout: () => {
        localStorage.removeItem('token')
        localStorage.removeItem('refresh_token')
        set({ user: null, token: null, refreshToken: null })
      },
    }),
    { name: 'lingualeap-auth' }
  )
)
