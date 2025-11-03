'use client'

import { useState, useEffect } from 'react'
import { X, ExternalLink, Loader2, CheckCircle, AlertCircle } from 'lucide-react'

interface OAuthModalProps {
  isOpen: boolean
  onClose: () => void
  provider: 'google-drive' | 'notion'
  providerName: string
  onSuccess: () => void
}

export function OAuthModal({ isOpen, onClose, provider, providerName, onSuccess }: OAuthModalProps) {
  const [step, setStep] = useState<'info' | 'redirecting' | 'authorizing' | 'success' | 'error'>('info')
  const [authUrl, setAuthUrl] = useState('')
  const [error, setError] = useState<string | null>(null)

  // Generate authorization URL (replace with actual backend API endpoint)
  const generateAuthUrl = async () => {
    try {
      // Should call backend API to get OAuth authorization URL
      // const response = await fetch(`/api/integrations/${provider}/auth-url`)
      // const data = await response.json()
      
      // Simulate generating authorization URL
      const mockAuthUrls = {
        'google-drive': 'https://accounts.google.com/o/oauth2/v2/auth?client_id=YOUR_CLIENT_ID&redirect_uri=YOUR_REDIRECT_URI&response_type=code&scope=https://www.googleapis.com/auth/drive.readonly&access_type=offline&prompt=consent',
        'notion': 'https://api.notion.com/v1/oauth/authorize?client_id=YOUR_CLIENT_ID&redirect_uri=YOUR_REDIRECT_URI&response_type=code&owner=user'
      }
      
      setAuthUrl(mockAuthUrls[provider])
      setStep('redirecting')
    } catch (err) {
      setError('Failed to generate authorization URL')
      setStep('error')
    }
  }

  useEffect(() => {
    if (isOpen && step === 'info') {
      generateAuthUrl()
    }
    // Reset state when modal closes
    if (!isOpen) {
      setStep('info')
      setError(null)
      setAuthUrl('')
    }
  }, [isOpen])

  const handleAuthorize = () => {
    setStep('authorizing')
    // Open authorization page in new window
    const authWindow = window.open(
      authUrl,
      `${providerName} Authorization`,
      'width=600,height=700,scrollbars=yes,resizable=yes'
    )

    // Monitor authorization window closure
    const checkClosed = setInterval(() => {
      if (authWindow?.closed) {
        clearInterval(checkClosed)
        // Should check if authorization was successful
        // In actual implementation, after successful authorization there will be a callback, then call backend API to verify
        setTimeout(() => {
          setStep('success')
          setTimeout(() => {
            onSuccess()
            onClose()
            setStep('info')
          }, 1500)
        }, 1000)
      }
    }, 500)
  }

  const handleCopyLink = () => {
    navigator.clipboard.writeText(authUrl)
    // Can add a brief notification
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative bg-white rounded-2xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              Connect {providerName}
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              Authorize MemoHub to access your {providerName} account
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {step === 'info' && (
            <div className="text-center">
              <Loader2 className="w-8 h-8 text-gray-400 animate-spin mx-auto mb-4" />
              <p className="text-gray-600">Preparing authorization...</p>
            </div>
          )}

          {step === 'redirecting' && (
            <div className="space-y-4">
              <div className="text-center">
                <ExternalLink className="w-12 h-12 text-blue-500 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Ready to Authorize
                </h3>
                <p className="text-sm text-gray-600 mb-6">
                  Click the button below to open the authorization page in a new window. 
                  After granting permissions, the window will close automatically.
                </p>
              </div>

              {/* Authorization Link Display */}
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs font-medium text-gray-700">
                    Authorization URL:
                  </label>
                  <button
                    onClick={handleCopyLink}
                    className="text-xs text-blue-600 hover:text-blue-700"
                  >
                    Copy Link
                  </button>
                </div>
                <div className="text-xs text-gray-600 font-mono break-all bg-white p-2 rounded border border-gray-200">
                  {authUrl}
                </div>
              </div>

              <button
                onClick={handleAuthorize}
                className="w-full flex items-center justify-center space-x-2 bg-gray-900 text-white px-6 py-3 rounded-lg hover:bg-gray-800 transition-colors font-medium"
              >
                <ExternalLink className="w-5 h-5" />
                <span>Open Authorization Page</span>
              </button>
            </div>
          )}

          {step === 'authorizing' && (
            <div className="text-center space-y-4">
              <Loader2 className="w-12 h-12 text-blue-500 animate-spin mx-auto" />
              <h3 className="text-lg font-semibold text-gray-900">
                Waiting for Authorization
              </h3>
              <p className="text-sm text-gray-600">
                Please complete the authorization in the popup window...
              </p>
              <p className="text-xs text-gray-500">
                If the popup was blocked, check your browser settings or use the link above.
              </p>
            </div>
          )}

          {step === 'success' && (
            <div className="text-center space-y-4">
              <CheckCircle className="w-16 h-16 text-green-500 mx-auto" />
              <h3 className="text-lg font-semibold text-gray-900">
                Connection Successful!
              </h3>
              <p className="text-sm text-gray-600">
                {providerName} has been successfully connected to MemoHub.
              </p>
            </div>
          )}

          {step === 'error' && (
            <div className="text-center space-y-4">
              <AlertCircle className="w-16 h-16 text-red-500 mx-auto" />
              <h3 className="text-lg font-semibold text-gray-900">
                Connection Failed
              </h3>
              <p className="text-sm text-gray-600">
                {error || 'An error occurred during authorization. Please try again.'}
              </p>
              <button
                onClick={() => {
                  setStep('info')
                  setError(null)
                  generateAuthUrl()
                }}
                className="mt-4 px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors"
              >
                Try Again
              </button>
            </div>
          )}
        </div>

        {/* Footer */}
        {step !== 'authorizing' && step !== 'success' && (
          <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
            <p className="text-xs text-gray-500 text-center">
              By connecting, you authorize MemoHub to access your {providerName} data. 
              You can disconnect at any time.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}