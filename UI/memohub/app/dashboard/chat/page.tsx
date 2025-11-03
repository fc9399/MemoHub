'use client'

import { ChatPanel } from '@/components/chat-panel'

export default function ChatPage() {
  // TODO: AI Chat feature is connected to backend /api/agent/chat endpoint
  // This feature uses real NVIDIA NIM LLM service and memory retrieval
  // MCP (Model Context Protocol) feature not yet implemented

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-gray-900">AI Chat</h1>
        <p className="text-gray-500 mt-1">
          Chat with your memory library for intelligent answers
        </p>
      </div>
      
      <div className="bg-white rounded-2xl shadow-brand overflow-hidden" style={{ height: 'calc(100vh - 280px)', minHeight: '600px' }}>
        <ChatPanel />
      </div>
    </div>
  )
}