'use client'

import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { CheckCircle, XCircle, Loader2 } from 'lucide-react'

export default function GoogleDriveCallbackPage() {
  const searchParams = useSearchParams()
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [message, setMessage] = useState('Processing authorization...')

  useEffect(() => {
    const handleCallback = () => {
      try {
        const code = searchParams.get('code')
        const state = searchParams.get('state')
        const error = searchParams.get('error')

        if (error) {
          setStatus('error')
          setMessage(`Authorization failed: ${error}`)
          // Notify parent window
          if (window.opener) {
            window.opener.postMessage({
              type: 'oauth-error',
              error: `Authorization failed: ${error}`
            }, window.location.origin)
          }
          setTimeout(() => {
            window.close()
          }, 3000)
          return
        }

        if (!code || !state) {
          setStatus('error')
          setMessage('Missing required authorization parameters')
          // Notify parent window
          if (window.opener) {
            window.opener.postMessage({
              type: 'oauth-error',
              error: 'Missing required authorization parameters'
            }, window.location.origin)
          }
          setTimeout(() => {
            window.close()
          }, 3000)
          return
        }

        // Send code and state to parent window, let parent window handle connection
        // This allows using parent window's auth token
        setStatus('success')
        setMessage('Authorization successful, connecting...')

        // Extract complete redirect_uri (current page's full URL, excluding query parameters)
        const currentRedirectUri = `${window.location.origin}${window.location.pathname}`
        console.log(`🔍 Callback page detected redirect_uri: ${currentRedirectUri}`)

        // Immediately notify parent window to handle connection, including redirect_uri
        if (window.opener) {
          window.opener.postMessage({
            type: 'oauth-success',
            code,
            state,
            redirect_uri: currentRedirectUri  // Pass redirect_uri to parent window
          }, window.location.origin)
          
          // Wait a moment before closing window
          setTimeout(() => {
            window.close()
          }, 1000)
        } else {
          // If no parent window (opened directly), show error
          setStatus('error')
          setMessage('Cannot connect to parent window, please open through app page')
        }
      } catch (err) {
        console.error('Google Drive callback error:', err)
        setStatus('error')
        const errorMessage = err instanceof Error ? err.message : 'Connection failed'
        setMessage(errorMessage)
        // Notify parent window
        if (window.opener) {
          window.opener.postMessage({
            type: 'oauth-error',
            error: errorMessage
          }, window.location.origin)
        }
        setTimeout(() => {
          window.close()
        }, 5000)
      }
    }

    handleCallback()
  }, [searchParams])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white rounded-2xl shadow-lg p-8 max-w-md w-full text-center">
        {status === 'loading' && (
          <>
            <Loader2 className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Processing...</h2>
            <p className="text-gray-600">{message}</p>
          </>
        )}
        {status === 'success' && (
          <>
            <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Connection Successful!</h2>
            <p className="text-gray-600">{message}</p>
            <p className="text-sm text-gray-500 mt-2">Window will close automatically...</p>
          </>
        )}
        {status === 'error' && (
          <>
            <XCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Connection Failed</h2>
            <p className="text-gray-600">{message}</p>
            <p className="text-sm text-gray-500 mt-2">Window will close automatically...</p>
          </>
        )}
      </div>
    </div>
  )
}