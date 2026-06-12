import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { User } from '../types'

interface AuthState {
  user: User | null
  token: string | null
  setAuth: (user: User, token: string) => void
  updateXP: (xp: number) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,

      setAuth: (user, token) => {
        localStorage.setItem('token', token)
        set({ user, token })
      },

      updateXP: (xp) =>
        set((state) => ({
          user: state.user ? { ...state.user, xp } : null,
        })),

      logout: () => {
        localStorage.removeItem('token')
        set({ user: null, token: null })
      },
    }),
    { name: 'lingualeap-auth' }
  )
)
