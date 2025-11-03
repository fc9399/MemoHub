'use client'

import { useState, useEffect } from 'react'
import { X, ExternalLink, Loader2, CheckCircle, AlertCircle, Shield, Lock } from 'lucide-react'
import { integrationsApi } from '@/lib/api'

interface OAuthAuthWindowProps {
  isOpen: boolean
  onClose: () => void
  provider: 'google-drive' | 'notion'
  providerName: string
  onSuccess: (code: string, state: string, redirectUri?: string) => void // Added redirectUri parameter
}

export function OAuthAuthWindow({ isOpen, onClose, provider, providerName, onSuccess }: OAuthAuthWindowProps) {
  const [step, setStep] = useState<'loading' | 'ready' | 'authorizing' | 'success' | 'error'>('loading')
  const [authUrl, setAuthUrl] = useState('')
  const [oauthState, setOauthState] = useState('')
  const [redirectUri, setRedirectUri] = useState<string>('') // Store redirect_uri used in auth
  const [error, setError] = useState<string | null>(null)
  const [authWindow, setAuthWindow] = useState<Window | null>(null)

  // Get authorization URL
  useEffect(() => {
    if (!isOpen) return

    const fetchAuthUrl = async () => {
      try {
        setStep('loading')
        setError(null)
        
        // Call backend API to get authorization URL
        const data = await integrationsApi.getAuthUrl(provider)
        
        if (!data.auth_url) {
          throw new Error('No authorization URL received')
        }
        
        // Extract redirect_uri from authorization URL for subsequent token exchange
        try {
          const url = new URL(data.auth_url)
          const extractedRedirectUri = url.searchParams.get('redirect_uri')
          if (extractedRedirectUri) {
            const decodedUri = decodeURIComponent(extractedRedirectUri)
            setRedirectUri(decodedUri)
            console.log(`🔍 Extracted redirect_uri from auth URL: ${decodedUri}`)
          } else {
            // If not in URL, use default value (based on current frontend URL)
            const defaultRedirectUri = `${window.location.origin}/api/integrations/${provider}/callback`
            setRedirectUri(defaultRedirectUri)
            console.log(`⚠️  No redirect_uri in auth URL, using default: ${defaultRedirectUri}`)
          }
        } catch (e) {
          // If parsing fails, use default value
          const defaultRedirectUri = `${window.location.origin}/api/integrations/${provider}/callback`
          setRedirectUri(defaultRedirectUri)
          console.error('❌ Failed to parse auth URL, using default redirect_uri:', e)
        }
        
        setAuthUrl(data.auth_url)
        setOauthState(data.state)
        setStep('ready')
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to initialize authorization')
        setStep('error')
        console.error('Auth URL fetch error:', err)
      }
    }

    fetchAuthUrl()
  }, [isOpen, provider])

  // Open authorization window
  const handleAuthorize = () => {
    if (!authUrl) return

    setStep('authorizing')
    
    // Open authorization page in new window
    const popup = window.open(
      authUrl,
      `${providerName} Authorization`,
      'width=600,height=700,scrollbars=yes,resizable=yes,left=' + 
      (window.screen.width / 2 - 300) + 
      ',top=' + 
      (window.screen.height / 2 - 350)
    )
    
    setAuthWindow(popup)

    // Monitor authorization window closure
    const checkClosed = setInterval(() => {
      if (popup?.closed) {
        clearInterval(checkClosed)
        // After window closes, check if authorization was successful
        // In practice, should check via callback URL or polling API
        checkAuthStatus()
      }
    }, 500)

    // Listen for messages from authorization window (callback page will send postMessage)
    const messageHandler = async (event: MessageEvent) => {
      // Security check: ensure message is from same origin
      if (event.origin !== window.location.origin) return
      
      if (event.data.type === 'oauth-success') {
        clearInterval(checkClosed)
        // Callback page sent code, state and redirect_uri, now parent window handles connection (using main app's auth token)
        try {
          // Use redirect_uri sent by callback page (if provided), otherwise use locally saved one
          const callbackRedirectUri = event.data.redirect_uri || redirectUri
          console.log(`📨 Received callback message, redirect_uri: ${callbackRedirectUri}`)
          
          await handleAuthSuccess(
            event.data.code, 
            event.data.state, 
            callbackRedirectUri  // Pass redirect_uri to handleAuthSuccess
          )
        } catch (err) {
          setStep('error')
          setError(err instanceof Error ? err.message : 'Connection failed')
        }
      } else if (event.data.type === 'oauth-error') {
        clearInterval(checkClosed)
        setStep('error')
        setError(event.data.error || 'Authorization failed')
      }
    }
    
    window.addEventListener('message', messageHandler)
    
    // Cleanup function
    return () => {
      clearInterval(checkClosed)
      window.removeEventListener('message', messageHandler)
    }
  }

  // Check authorization status - extract code from popup URL
  const checkAuthStatus = async () => {
    try {
      // Check if popup contains callback URL
      if (authWindow && !authWindow.closed) {
        try {
          // Try to read popup's URL (may fail due to same-origin policy)
          const popupUrl = authWindow.location.href
          const url = new URL(popupUrl)
          const code = url.searchParams.get('code')
          const error = url.searchParams.get('error')
          const returnedState = url.searchParams.get('state')
          
          if (error) {
            throw new Error(`OAuth error: ${error}`)
          }
          
          if (code && returnedState === oauthState) {
            // Authorization successful, use code
            await handleAuthSuccess(code)
            return
          }
        } catch (e) {
          // Cross-origin error, cannot read popup URL
          // Use fallback method: monitor URL changes or prompt user for manual input
          console.log('Cannot access popup URL (cross-origin). Waiting for manual callback...')
          // In production, should set up a callback page to handle this
        }
      }
      
      // If not successful, show error
      setStep('error')
      setError('Authorization failed. Please try again or check the popup window.')
    } catch (err) {
      setStep('error')
      setError(err instanceof Error ? err.message : 'Authorization failed. Please try again.')
    }
  }

  // Handle authorization success
  const handleAuthSuccess = async (code: string, state?: string, callbackRedirectUri?: string) => {
    try {
      // Use state received from callback page, if not available use locally saved oauthState
      const finalState = state || oauthState
      
      // Prioritize redirect_uri sent by callback page, then use locally extracted one, finally use default
      const finalRedirectUri = callbackRedirectUri || redirectUri || `${window.location.origin}/api/integrations/${provider}/callback`
      console.log(`🔗 Connecting integration, final redirect_uri used: ${finalRedirectUri}`)
      console.log(`   - Provided by callback page: ${callbackRedirectUri || 'none'}`)
      console.log(`   - Locally saved: ${redirectUri || 'none'}`)
      
      // Show success status, then let onSuccess callback handle actual connection
      // This avoids reusing authorization code
      setStep('success')
      
      setTimeout(() => {
        // Pass code, state and redirectUri to onSuccess, let caller handle connection
        onSuccess(code, finalState, finalRedirectUri)
        onClose()
        resetState()
      }, 1500)
    } catch (err) {
      setStep('error')
      setError(err instanceof Error ? err.message : 'Authorization failed')
      throw err // Re-throw error for caller to handle
    }
  }

  // Reset state
  const resetState = () => {
    setStep('loading')
    setError(null)
    setAuthUrl('')
    setOauthState('')
    setRedirectUri('')
    setAuthWindow(null)
  }

  // Reset on close
  useEffect(() => {
    if (!isOpen) {
      resetState()
      if (authWindow && !authWindow.closed) {
        authWindow.close()
      }
    }
  }, [isOpen])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative bg-white rounded-3xl shadow-2xl max-w-md w-full overflow-hidden animate-in fade-in zoom-in duration-200">
        {/* Header with gradient */}
        <div className="bg-gradient-to-r from-gray-900 to-gray-700 p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                <Shield className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white">
                  Connect {providerName}
                </h2>
                <p className="text-sm text-white/80 mt-0.5">
                  Secure authorization required
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/10 rounded-lg transition-colors text-white"
              disabled={step === 'authorizing'}
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Loading State */}
          {step === 'loading' && (
            <div className="text-center py-8">
              <Loader2 className="w-12 h-12 text-gray-400 animate-spin mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Preparing Authorization
              </h3>
              <p className="text-sm text-gray-600">
                Setting up secure connection to {providerName}...
              </p>
            </div>
          )}

          {/* Ready State */}
          {step === 'ready' && (
            <div className="space-y-6">
              <div className="text-center">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Lock className="w-8 h-8 text-blue-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Authorization Required
                </h3>
                <p className="text-sm text-gray-600 mb-1">
                  You'll be redirected to {providerName}'s secure login page.
                </p>
                <p className="text-xs text-gray-500">
                  After authorizing, you can close that window and return here.
                </p>
              </div>

              {/* Security Notice */}
              <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
                <div className="flex items-start space-x-3">
                  <Shield className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-blue-900 mb-1">
                      Secure Authorization
                    </p>
                    <p className="text-xs text-blue-700">
                      You'll authorize MemoHub to access your {providerName} data. 
                      Your credentials are handled securely by {providerName}.
                    </p>
                  </div>
                </div>
              </div>

              <button
                onClick={handleAuthorize}
                className="w-full flex items-center justify-center space-x-2 bg-gray-900 text-white px-6 py-3 rounded-xl hover:bg-gray-800 transition-colors font-medium shadow-lg hover:shadow-xl"
              >
                <ExternalLink className="w-5 h-5" />
                <span>Continue to {providerName}</span>
              </button>
            </div>
          )}

          {/* Authorizing State */}
          {step === 'authorizing' && (
            <div className="text-center py-8">
              <Loader2 className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Waiting for Authorization
              </h3>
              <p className="text-sm text-gray-600 mb-4">
                Please complete the authorization in the popup window.
              </p>
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                <p className="text-xs text-yellow-800">
                  <strong>Tip:</strong> If the popup was blocked, check your browser settings 
                  or allow popups for this site.
                </p>
              </div>
            </div>
          )}

          {/* Success State */}
          {step === 'success' && (
            <div className="text-center py-8">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="w-8 h-8 text-green-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Connection Successful!
              </h3>
              <p className="text-sm text-gray-600">
                {providerName} has been successfully connected to MemoHub.
              </p>
            </div>
          )}

          {/* Error State */}
          {step === 'error' && (
            <div className="text-center py-8">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <AlertCircle className="w-8 h-8 text-red-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Connection Failed
              </h3>
              <p className="text-sm text-gray-600 mb-6">
                {error || 'An error occurred during authorization. Please try again.'}
              </p>
              <div className="flex items-center space-x-3">
                <button
                  onClick={() => {
                    setStep('loading')
                    setError(null)
                    // Re-fetch auth URL
                    window.location.reload()
                  }}
                  className="flex-1 px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors"
                >
                  Try Again
                </button>
                <button
                  onClick={onClose}
                  className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        {step !== 'authorizing' && step !== 'success' && (
          <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
            <p className="text-xs text-gray-500 text-center">
              By connecting, you authorize MemoHub to access your {providerName} data. 
              <br />
              You can disconnect at any time in Settings.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}