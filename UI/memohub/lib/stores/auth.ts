import { create } from 'zustand'
import { authApi } from '../api'

export interface User {
  id: string
  username: string
  email: string
  full_name?: string
  is_active: boolean
}

interface AuthState {
  user: User | null
  token: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  login: (username: string, password: string) => Promise<void>
  register: (username: string, email: string, password: string, full_name?: string) => Promise<void>
  logout: () => Promise<void>
  fetchUser: () => Promise<void>
  clearError: () => void
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: null,
  refreshToken: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
  
  login: async (username: string, password: string) => {
    set({ isLoading: true, error: null })
    try {
      const response = await authApi.login(username, password)
      
      set({
        token: response.access_token,
        refreshToken: response.refresh_token,
        isAuthenticated: true,
        isLoading: false
      })
      
      // Fetch user information
      await get().fetchUser()
    } catch (error: any) {
      set({
        error: error.message || 'Login failed, please check username and password',
        isLoading: false,
        isAuthenticated: false
      })
      throw error
    }
  },
  
  register: async (username: string, email: string, password: string, full_name?: string) => {
    set({ isLoading: true, error: null })
    try {
      const user = await authApi.register(username, email, password, full_name)
      
      // Auto login after registration
      await get().login(username, password)
    } catch (error: any) {
      set({
        error: error.message || 'Registration failed, username or email may already exist',
        isLoading: false
      })
      throw error
    }
  },
  
  fetchUser: async () => {
    try {
      const user = await authApi.getMe()
      set({ user })
    } catch (error: any) {
      console.error('Failed to fetch user:', error)
      // If fetching user info fails, token may have expired
      if (error.message.includes('401') || error.message.includes('Unauthorized')) {
        set({
          user: null,
          token: null,
          refreshToken: null,
          isAuthenticated: false
        })
      }
    }
  },
  
  logout: async () => {
    try {
      await authApi.logout()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      set({
        user: null,
        token: null,
        refreshToken: null,
        isAuthenticated: false,
        error: null
      })
    }
  },
  
  clearError: () => {
    set({ error: null })
  }
}))