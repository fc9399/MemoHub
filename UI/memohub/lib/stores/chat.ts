import { create } from 'zustand'
import { agentApi } from '../api'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations?: {
    memoryId: string
    snippet: string
    fileName: string
    similarity: number
  }[]
  createdAt: string
  conversationId?: string
}

interface ChatState {
  messages: ChatMessage[]
  currentConversationId: string | null
  isLoading: boolean
  error: string | null
  sendMessage: (content: string) => Promise<void>
  clearMessages: () => void
  loadConversation: (conversationId: string) => Promise<void>
  clearError: () => void
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  currentConversationId: null,
  isLoading: false,
  error: null,
  
  sendMessage: async (content: string) => {
    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content,
      createdAt: new Date().toISOString(),
      conversationId: get().currentConversationId || undefined
    }
    
    set((state) => ({
      messages: [...state.messages, userMessage],
      isLoading: true,
      error: null
    }))
    
    try {
      // Call the real AI Agent API
      const response = await agentApi.chat(
        content,
        get().currentConversationId || undefined,
        true // use_memory
      )
      
      // Update conversation ID
      if (!get().currentConversationId) {
        set({ currentConversationId: response.conversation_id })
      }
      
      // Convert relevant memories to citation format
      const citations = response.relevant_memories?.map((mem: any) => ({
        memoryId: mem.memory?.id || '',
        snippet: mem.memory?.summary || mem.memory?.content?.substring(0, 200) || '',
        fileName: mem.memory?.metadata?.original_filename || mem.memory?.source || 'Memory',
        similarity: mem.similarity_score || 0
      })) || []
      
      const assistantMessage: ChatMessage = {
        id: `msg_${Date.now() + 1}`,
        role: 'assistant',
        content: response.response,
        citations: citations.length > 0 ? citations : undefined,
        createdAt: response.timestamp,
        conversationId: response.conversation_id
      }
      
      set((state) => ({
        messages: [...state.messages, assistantMessage],
        isLoading: false,
        currentConversationId: response.conversation_id
      }))
    } catch (error: any) {
      console.error('Chat failed:', error)
      
      const errorMessage: ChatMessage = {
        id: `msg_${Date.now() + 1}`,
        role: 'assistant',
        content: `Sorry, I encountered an issue: ${error.message || 'Unable to connect to AI service'}`,
        createdAt: new Date().toISOString(),
        conversationId: get().currentConversationId || undefined
      }
      
      set((state) => ({
        messages: [...state.messages, errorMessage],
        isLoading: false,
        error: error.message || 'AI conversation failed'
      }))
    }
  },
  
  loadConversation: async (conversationId: string) => {
    set({ isLoading: true, error: null })
    try {
      const response = await agentApi.getConversationHistory(conversationId)
      
      // Convert conversation history to message format
      const messages: ChatMessage[] = []
      response.history.forEach((turn) => {
        messages.push({
          id: `msg_${Date.now()}_user`,
          role: 'user',
          content: turn.user_input,
          createdAt: turn.timestamp,
          conversationId: conversationId
        })
        messages.push({
          id: `msg_${Date.now()}_assistant`,
          role: 'assistant',
          content: turn.response,
          createdAt: turn.timestamp,
          conversationId: conversationId
        })
      })
      
      set({
        messages,
        currentConversationId: conversationId,
        isLoading: false
      })
    } catch (error: any) {
      console.error('Failed to load conversation:', error)
      set({
        error: error.message || 'Failed to load conversation history',
        isLoading: false
      })
    }
  },
  
  clearMessages: async () => {
    const conversationId = get().currentConversationId
    if (conversationId) {
      try {
        await agentApi.clearConversation(conversationId)
      } catch (error) {
        console.error('Failed to clear conversation:', error)
      }
    }
    set({
      messages: [],
      currentConversationId: null,
      error: null
    })
  },
  
  clearError: () => {
    set({ error: null })
  }
}))