'use client'

import { useState, useEffect } from 'react'
import { useIntegrationStore } from '@/lib/stores/integrations'
import { OAuthAuthWindow } from './oauth-auth-window'
import { 
  HardDrive, 
  FileText, 
  CheckCircle, 
  XCircle, 
  RefreshCw,
  ExternalLink
} from 'lucide-react'

const integrationConfig = {
  'google-drive': {
    name: 'Google Drive',
    icon: HardDrive,
    description: 'Connect your Google Drive account to automatically sync files',
    color: 'bg-blue-500'
  },
  'notion': {
    name: 'Notion',
    icon: FileText,
    description: 'Connect your Notion workspace to sync pages and databases',
    color: 'bg-gray-900'
  }
}

export function IntegrationCard() {
  const { integrations, loadIntegrations, connect, disconnect, sync, isLoading, error } = useIntegrationStore()
  const [oauthWindow, setOAuthWindow] = useState<{
    isOpen: boolean
    provider: 'google-drive' | 'notion'
  }>({ isOpen: false, provider: 'google-drive' })

  // Load integration data when component mounts
  useEffect(() => {
    loadIntegrations()
  }, [loadIntegrations])

  const handleConnect = (provider: 'google-drive' | 'notion') => {
    setOAuthWindow({ isOpen: true, provider })
  }

  const handleOAuthSuccess = async (code: string, state: string, redirectUri?: string) => {
    try {
      console.log(`📞 Starting to connect integration: ${oauthWindow.provider}`)
      await connect(oauthWindow.provider, code, state, redirectUri)
      console.log(`✅ Connection successful, reloading integration list`)
      await loadIntegrations() // Reload data
    } catch (error) {
      console.error('❌ Connection failed:', error)
      // Show error message to user
      alert(`Connection failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  const handleDisconnect = async (provider: 'google-drive' | 'notion') => {
    if (confirm('Are you sure you want to disconnect?')) {
      try {
        await disconnect(provider)
        await loadIntegrations() // Reload data
      } catch (error) {
        console.error('Disconnect failed:', error)
      }
    }
  }

  const handleSync = async (provider: 'google-drive' | 'notion') => {
    try {
      const response = await sync(provider)
      console.log(`✅ Sync successful: ${response.synced_items} files`)
      // After sync success, will trigger Dashboard auto-refresh
    } catch (error) {
      console.error('❌ Sync failed:', error)
      // Error already handled by store and set to error state
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900">Integrations</h2>
        <p className="text-sm text-gray-500 mt-1">
          Connect external services to automatically sync your files and data
        </p>
      </div>

      {/* Integrations Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {integrations.map((integration) => {
          const config = integrationConfig[integration.provider]
          const IconComponent = config.icon
          
          const handleConnectForProvider = () => handleConnect(integration.provider)
          
          return (
            <div key={integration.provider} className="bg-white rounded-2xl shadow-brand p-6">
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-3">
                  <div className={`w-12 h-12 ${config.color} rounded-lg flex items-center justify-center`}>
                    <IconComponent className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      {config.name}
                    </h3>
                    <p className="text-sm text-gray-500 mt-1">
                      {config.description}
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  {integration.connected ? (
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  ) : (
                    <XCircle className="w-5 h-5 text-gray-400" />
                  )}
                </div>
              </div>
              
              {integration.connected && (
                <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">
                      Account: {integration.account}
                    </span>
                    {integration.lastSync && (
                      <span className="text-gray-500">
                        Last sync: {new Date(integration.lastSync).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </div>
              )}
              
              <div className="mt-4 flex items-center space-x-2">
                {integration.connected ? (
                  <>
                    <button
                      onClick={() => handleSync(integration.provider)}
                      className="flex items-center space-x-2 px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                    >
                      <RefreshCw className="w-4 h-4" />
                      <span>Sync</span>
                    </button>
                    <button
                      onClick={() => handleDisconnect(integration.provider)}
                      className="px-3 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors"
                    >
                      Disconnect
                    </button>
                  </>
                ) : (
                  <button
                    onClick={handleConnectForProvider}
                    className="flex items-center space-x-2 px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors"
                  >
                    <ExternalLink className="w-4 h-4" />
                    <span>Connect</span>
                  </button>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* OAuth Authorization Window */}
      <OAuthAuthWindow
        isOpen={oauthWindow.isOpen}
        onClose={() => setOAuthWindow({ isOpen: false, provider: 'google-drive' })}
        provider={oauthWindow.provider}
        providerName={integrationConfig[oauthWindow.provider]?.name || ''}
        onSuccess={(code: string, state: string, redirectUri?: string) => handleOAuthSuccess(code, state, redirectUri)}
      />
    </div>
  )
}