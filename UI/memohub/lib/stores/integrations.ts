import { create } from 'zustand'
import { integrationsApi } from '@/lib/api'

export interface IntegrationState {
  provider: 'google-drive' | 'notion'
  connected: boolean
  account?: string
  lastSync?: string
  id?: string
  userId?: string
}

interface IntegrationsState {
  integrations: IntegrationState[]
  isLoading: boolean
  error: string | null
  loadIntegrations: () => Promise<void>
  connect: (provider: 'google-drive' | 'notion', code: string, state: string, redirectUri?: string) => Promise<void>
  disconnect: (provider: 'google-drive' | 'notion') => Promise<void>
  sync: (provider: 'google-drive' | 'notion') => Promise<any>
  clearError: () => void
}

export const useIntegrationStore = create<IntegrationsState>((set, get) => ({
  integrations: [
    {
      provider: 'google-drive',
      connected: false
    },
    {
      provider: 'notion',
      connected: false
    }
  ],
  isLoading: false,
  error: null,
  
  loadIntegrations: async () => {
    set({ isLoading: true, error: null })
    try {
      const response = await integrationsApi.list()
      
      // Map backend data to frontend format
      const backendIntegrations = response.integrations || []
      const allProviders = ['google-drive', 'notion']
      
      const integrations: IntegrationState[] = allProviders.map(provider => {
        const backendIntegration = backendIntegrations.find(
          (bi: any) => bi.provider === provider
        )
        
        if (backendIntegration) {
          return {
            provider: provider as 'google-drive' | 'notion',
            connected: backendIntegration.connected,
            account: backendIntegration.account,
            lastSync: backendIntegration.last_sync,
            id: backendIntegration.id,
            userId: backendIntegration.user_id
          }
        }
        
        return {
          provider: provider as 'google-drive' | 'notion',
          connected: false
        }
      })
      
      set({ integrations, isLoading: false })
    } catch (error: any) {
      set({ 
        error: error.message || 'Failed to load integrations', 
        isLoading: false 
      })
    }
  },
  
  connect: async (provider: 'google-drive' | 'notion', code: string, state: string, redirectUri?: string) => {
    set({ isLoading: true, error: null })
    try {
      const response = await integrationsApi.connect(provider, code, state, redirectUri)
      
      // Update integration status
      set((state) => ({
        integrations: state.integrations.map(integration => 
          integration.provider === provider 
            ? { 
                ...integration, 
                connected: response.integration.connected, 
                account: response.integration.account,
                lastSync: response.integration.last_sync,
                id: response.integration.id,
                userId: response.integration.user_id
              }
            : integration
        ),
        isLoading: false
      }))
    } catch (error: any) {
      set({ 
        error: error.message || 'Connection failed', 
        isLoading: false 
      })
      throw error
    }
  },
  
  disconnect: async (provider: 'google-drive' | 'notion') => {
    set({ isLoading: true, error: null })
    try {
      await integrationsApi.disconnect(provider)
      
      set((state) => ({
        integrations: state.integrations.map(integration => 
          integration.provider === provider 
            ? { 
                ...integration, 
                connected: false, 
                account: undefined,
                lastSync: undefined,
                id: undefined,
                userId: undefined
              }
            : integration
        ),
        isLoading: false
      }))
    } catch (error: any) {
      set({ 
        error: error.message || 'Failed to disconnect', 
        isLoading: false 
      })
      throw error
    }
  },
  
  sync: async (provider: 'google-drive' | 'notion') => {
    set({ isLoading: true, error: null })
    try {
      const response = await integrationsApi.sync(provider)
      
      // Update lastSync time
      set((state) => ({
        integrations: state.integrations.map(integration => 
          integration.provider === provider 
            ? { 
                ...integration, 
                lastSync: response.last_sync
              }
            : integration
        ),
        isLoading: false
      }))
      
      // After successful sync, trigger Dashboard refresh (via custom event)
      if (response.success && response.synced_items > 0) {
        window.dispatchEvent(new CustomEvent('memories-updated'))
      }
      
      return response
    } catch (error: any) {
      set({ 
        error: error.message || 'Sync failed', 
        isLoading: false 
      })
      throw error
    }
  },
  
  clearError: () => set({ error: null })
}))