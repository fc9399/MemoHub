import { create } from 'zustand'
import { apiKeysApi } from '../api'
import { useAuthStore } from './auth'

export interface ApiKey {
  id: string
  keyMasked: string
  createdAt: string
  lastUsed?: string
  expiresAt?: string  // Expiration time
  isActive: boolean
  fullKey?: string  // Full key, only available at creation
}

interface ApiKeyState {
  keys: ApiKey[]
  loading: boolean
  error: string | null
  createKey: (name?: string, expiresAt?: string) => Promise<ApiKey>
  revokeKey: (id: string) => Promise<void>
  copyKey: (id: string) => Promise<void>
  loadKeys: () => Promise<void>
}

export const useApiKeyStore = create<ApiKeyState>((set, get) => ({
  keys: [],
  loading: false,
  error: null,
  
  loadKeys: async () => {
    // Check if authenticated
    const { isAuthenticated, token } = useAuthStore.getState()
    
    if (!isAuthenticated || !token) {
      console.warn('User not authenticated, skipping API keys load')
      set({ loading: false, error: null, keys: [] })
      return
    }
    
    try {
      set({ loading: true, error: null })
      const response = await apiKeysApi.list()
      
      const keys: ApiKey[] = response.keys.map((k) => ({
        id: k.id,
        keyMasked: k.key_prefix,
        createdAt: k.created_at,
        lastUsed: k.last_used,
        expiresAt: k.expires_at,
        isActive: k.is_active
      }))
      
      set({ keys, loading: false })
    } catch (error: any) {
      console.error('Failed to load API keys:', error)
      
      // If authentication error, clear state but don't show error (will be handled by AuthGuard)
      if (error.message?.includes('authentication') || error.message?.includes('401') || error.message?.includes('Unauthorized')) {
        set({ 
          keys: [],
          loading: false,
          error: null  // Don't show error, let AuthGuard handle redirect
        })
        return
      }
      
      set({ 
        error: error.message || 'Failed to load API keys',
        loading: false 
      })
    }
  },
  
  createKey: async (name?: string, expiresAt?: string) => {
    try {
      set({ loading: true, error: null })
      const response = await apiKeysApi.create(name, expiresAt)
      
      const newKey: ApiKey = {
        id: response.id,
        keyMasked: response.key_prefix,
        createdAt: response.created_at,
        lastUsed: response.last_used,
        expiresAt: response.expires_at,
        isActive: response.is_active,
        fullKey: response.key  // Save full key, only available at creation
      }
      
      // Add to beginning of list
      set((state) => ({
        keys: [newKey, ...state.keys],
        loading: false
      }))
      
      return newKey
    } catch (error: any) {
      console.error('Failed to create API key:', error)
      set({ 
        error: error.message || 'Failed to create API key',
        loading: false 
      })
      throw error
    }
  },
  
  revokeKey: async (id: string) => {
    try {
      set({ loading: true, error: null })
      await apiKeysApi.revoke(id)
      
      // Remove from list or mark as invalid
      set((state) => ({
        keys: state.keys.filter(key => key.id !== id),
        loading: false
      }))
    } catch (error: any) {
      console.error('Failed to revoke API key:', error)
      set({ 
        error: error.message || 'Failed to revoke API key',
        loading: false 
      })
      throw error
    }
  },
  
  copyKey: async (id: string) => {
    const key = get().keys.find(k => k.id === id)
    if (key) {
      // If full key exists, copy full key; otherwise copy prefix
      const textToCopy = key.fullKey || key.keyMasked
      await navigator.clipboard.writeText(textToCopy)
    }
  }
}))