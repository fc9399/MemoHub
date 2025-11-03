import { useAuthStore } from './stores/auth'

// API base configuration - Connect to backend FastAPI service
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8012'

// Get authentication headers
function getAuthHeaders(includeContentType: boolean = true) {
  const token = useAuthStore.getState().token
  const headers: Record<string, string> = {}
  
  if (includeContentType) {
    headers['Content-Type'] = 'application/json'
  }
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  
  return headers
}

// Generic fetch wrapper
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`
  const isFormData = options.body instanceof FormData
  
  const response = await fetch(url, {
    ...options,
    headers: {
      ...getAuthHeaders(!isFormData),
      ...options.headers
    }
  })

  if (!response.ok) {
    const errorText = await response.text()
    let errorMessage = `API Error: ${response.status}`
    try {
      const errorJson = JSON.parse(errorText)
      errorMessage = errorJson.detail || errorMessage
    } catch {
      errorMessage = errorText || errorMessage
    }
    throw new Error(errorMessage)
  }

  return response.json()
}

// Authentication related API - Connect to backend /api/auth endpoints
export const authApi = {
  // Backend uses username instead of email
  login: (username: string, password: string) =>
    apiRequest<{ access_token: string; refresh_token: string; token_type: string; expires_in: number }>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    }),

  register: (username: string, email: string, password: string, full_name?: string) =>
    apiRequest<{ id: string; username: string; email: string; full_name?: string; is_active: boolean; created_at: string; updated_at: string }>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, email, password, full_name })
    }),

  // Get current user information
  getMe: () =>
    apiRequest<{ id: string; username: string; email: string; full_name?: string; is_active: boolean; created_at: string; updated_at: string }>('/api/auth/me'),

  // Refresh token
  refreshToken: (refresh_token: string) => {
    // Backend may require as Query parameter or Body, trying Body first
    return apiRequest<{ access_token: string; refresh_token: string; token_type: string; expires_in: number }>('/api/auth/refresh', {
      method: 'POST',
      body: JSON.stringify(refresh_token) // FastAPI may need {"refresh_token": "..."} format, adjust if needed
    })
  },

  // Logout
  logout: () =>
    apiRequest<{ message: string }>('/api/auth/logout', {
      method: 'POST'
    })
}

// File upload related API - Connect to backend /api/upload endpoints
export const uploadApi = {
  // Upload file - Connect to /api/upload
  upload: (file: File, parse_and_store: boolean = true) => {
    const formData = new FormData()
    formData.append('file', file)
    
    return apiRequest<{
      success: boolean
      message: string
      data: {
        original_filename: string
        s3_key: string
        file_url: string
        file_size: number
        file_extension: string
        upload_time: string
      }
      memory?: {
        memory_id: string
        parsed_content: any
        embedding_dimension: number
      }
    }>('/api/upload', {
      method: 'POST',
      body: formData,
      headers: {} // Let browser set Content-Type with boundary
    })
  },

  // Upload text - Connect to /api/upload/text
  uploadText: (text: string, source?: string) =>
    apiRequest<{
      success: boolean
      message: string
      memory_id: string
      content: string
      embedding_dimension: number
    }>(`/api/upload/text?text=${encodeURIComponent(text)}${source ? `&source=${encodeURIComponent(source)}` : ''}`, {
      method: 'POST'
    }),

  // Get supported file types
  getSupportedTypes: () =>
    apiRequest<{
      supported_types: string[]
      total: number
    }>('/api/upload/supported-types')
}

// Memory/Search related API - Connect to backend /api/search endpoints
export const searchApi = {
  // Semantic search - Connect to /api/search/semantic
  semanticSearch: (query: string, limit: number = 10, threshold: number = 0.2) =>
    apiRequest<{
      query: string
      results: Array<{
        memory: {
          id: string
          content: string
          memory_type: string
          metadata: any
          created_at: string
          updated_at: string
          source?: string
          summary?: string
          tags: string[]
        }
        similarity_score: number
        search_time: number
      }>
      total: number
      search_time: number
    }>('/api/search/semantic', {
      method: 'POST',
      body: JSON.stringify({ query, limit, threshold })
    }),

  // Get memory list - Connect to /api/search/memories
  getMemories: (params?: {
    limit?: number
    offset?: number
    memory_type?: string
    start_date?: string
    end_date?: string
  }) => {
    const query = new URLSearchParams()
    if (params?.limit) query.append('limit', params.limit.toString())
    if (params?.offset) query.append('offset', params.offset.toString())
    if (params?.memory_type) query.append('memory_type', params.memory_type)
    if (params?.start_date) query.append('start_date', params.start_date)
    if (params?.end_date) query.append('end_date', params.end_date)
    
    const url = `/api/search/memories${query.toString() ? '?' + query.toString() : ''}`
    return apiRequest<{
      memories: Array<{
        id: string
        content: string
        memory_type: string
        metadata: any
        created_at: string
        updated_at: string
        source?: string
        summary?: string
        tags: string[]
        user_id: string
      }>
      total: number
      limit: number
      offset: number
    }>(url)
  },

  // Get specific memory
  getMemory: (memoryId: string) =>
    apiRequest<{
      id: string
      content: string
      memory_type: string
      metadata: any
      created_at: string
      updated_at: string
      source?: string
      summary?: string
      tags: string[]
      user_id: string
    }>(`/api/search/memories/${memoryId}`),

  // Get related memories
  getRelatedMemories: (memoryId: string, limit: number = 5) =>
    apiRequest<{
      memory_id: string
      related_memories: Array<{
        memory: any
        similarity_score: number
        search_time: number
      }>
      count: number
    }>(`/api/search/memories/${memoryId}/related?limit=${limit}`, {
      method: 'POST'
    }),

  // Delete memory
  deleteMemory: (memoryId: string) =>
    apiRequest<{
      success: boolean
      message: string
    }>(`/api/search/memories/${memoryId}`, {
      method: 'DELETE'
    })
}

// AI Agent related API - Connect to backend /api/agent endpoints
export const agentApi = {
  // AI chat - Connect to /api/agent/chat
  chat: (message: string, conversation_id?: string, use_memory: boolean = true) =>
    apiRequest<{
      response: string
      conversation_id: string
      relevant_memories: Array<{
        memory: any
        similarity_score: number
      }>
      context_used: number
      timestamp: string
    }>('/api/agent/chat', {
      method: 'POST',
      body: JSON.stringify({ message, conversation_id, use_memory })
    }),

  // Get conversation list
  getConversations: () =>
    apiRequest<{
      conversations: Array<{
        conversation_id: string
        turn_count: number
        last_activity: string | null
      }>
      total: number
    }>('/api/agent/conversations'),

  // Get conversation history
  getConversationHistory: (conversationId: string) =>
    apiRequest<{
      conversation_id: string
      history: Array<{
        user_input: string
        response: string
        timestamp: string
      }>
      total_turns: number
    }>(`/api/agent/conversations/${conversationId}/history`),

  // Clear conversation history
  clearConversation: (conversationId?: string) =>
    apiRequest<{
      success: boolean
      message: string
    }>(conversationId ? `/api/agent/conversations/${conversationId}` : '/api/agent/conversations', {
      method: 'DELETE'
    })
}

// Embedding related API - Connect to backend /api/embeddings endpoints (optional)
export const embeddingApi = {
  generate: (text: string, input_type: 'passage' | 'query' = 'passage') =>
    apiRequest<{
      embedding: number[]
      dimension: number
      model: string
    }>('/api/embeddings/generate', {
      method: 'POST',
      body: JSON.stringify({ text, input_type })
    }),

  batchGenerate: (texts: string[], input_type: 'passage' | 'query' = 'passage') =>
    apiRequest<{
      embeddings: number[][]
      count: number
      dimension: number
    }>('/api/embeddings/batch', {
      method: 'POST',
      body: JSON.stringify({ texts, input_type })
    })
}

// Integrations related API - Connect to backend /api/integrations endpoints
export const integrationsApi = {
  // Get OAuth authorization URL
  getAuthUrl: (provider: 'google-drive' | 'notion', redirect_uri?: string) => {
    const query = redirect_uri ? `?redirect_uri=${encodeURIComponent(redirect_uri)}` : ''
    return apiRequest<{
      auth_url: string
      state: string
    }>(`/api/integrations/${provider}/auth-url${query}`)
  },

  // Connect integration service
  connect: (provider: 'google-drive' | 'notion', code: string, state: string, redirectUri?: string) =>
    apiRequest<{
      success: boolean
      integration: {
        id: string
        provider: string
        account?: string
        connected: boolean
        last_sync?: string
        user_id: string
        created_at: string
        updated_at: string
      }
      message: string
    }>(`/api/integrations/${provider}/connect`, {
      method: 'POST',
      body: JSON.stringify({ code, state, redirect_uri: redirectUri })
    }),

  // Disconnect integration
  disconnect: (provider: 'google-drive' | 'notion') =>
    apiRequest<{
      success: boolean
      message: string
    }>(`/api/integrations/${provider}/disconnect`, {
      method: 'DELETE'
    }),

  // Sync integration data
  sync: (provider: 'google-drive' | 'notion') =>
    apiRequest<{
      success: boolean
      message: string
      synced_items: number
      last_sync: string
    }>(`/api/integrations/${provider}/sync`, {
      method: 'POST'
    }),

  // Get all user integrations
  list: () =>
    apiRequest<{
      integrations: Array<{
        id: string
        provider: string
        account?: string
        connected: boolean
        last_sync?: string
        user_id: string
        created_at: string
        updated_at: string
      }>
      total: number
    }>('/api/integrations')
}

// API Keys related API - Connect to backend /api/api-keys endpoints
export const apiKeysApi = {
  // Create API key
  create: (name?: string, expiresAt?: string) =>
    apiRequest<{
      id: string
      name?: string
      key: string  // Full key, only returned once at creation
      key_prefix: string
      created_at: string
      last_used?: string
      expires_at?: string  // Expiration time
      is_active: boolean
    }>('/api/api-keys', {
      method: 'POST',
      body: JSON.stringify({ 
        name,
        expires_at: expiresAt ? new Date(expiresAt).toISOString() : undefined
      })
    }),

  // Get API key list
  list: () =>
    apiRequest<{
      keys: Array<{
        id: string
        name?: string
        user_id: string
        key_prefix: string
        created_at: string
        last_used?: string
        expires_at?: string  // Expiration time
        is_active: boolean
      }>
      total: number
    }>('/api/api-keys'),

  // Revoke API key
  revoke: (apiKeyId: string) =>
    apiRequest<{ success: boolean; message?: string }>(`/api/api-keys/${apiKeyId}`, {
      method: 'DELETE'
    })
}