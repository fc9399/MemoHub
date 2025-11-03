// ⚠️ This file is for development and testing purposes only
// The actual application is already connected to the real backend API (http://localhost:8012)
// 
// Mock data and simulated API calls - Deprecated, kept for testing reference
export const mockData = {
  files: [
    {
      id: '1',
      name: 'Important Document.pdf',
      type: 'pdf' as const,
      size: 1024000,
      status: 'ready' as const,
      tags: ['work', 'important'],
      pinned: true,
      updatedAt: '2024-01-20T10:30:00Z'
    },
    {
      id: '2',
      name: 'Technical Manual.docx',
      type: 'docx' as const,
      size: 512000,
      status: 'ready' as const,
      tags: ['technical'],
      pinned: false,
      updatedAt: '2024-01-20T09:15:00Z'
    },
    {
      id: '3',
      name: 'Meeting Recording.mp3',
      type: 'audio' as const,
      size: 2048000,
      status: 'fail' as const,
      tags: ['meeting'],
      pinned: false,
      updatedAt: '2024-01-20T08:45:00Z'
    }
  ],

  chatMessages: [
    {
      id: '1',
      role: 'user' as const,
      content: 'Please help me summarize yesterday\'s meeting content',
      createdAt: '2024-01-20T10:30:00Z'
    },
    {
      id: '2',
      role: 'assistant' as const,
      content: 'Based on your memory hub, I found relevant information about yesterday\'s meeting:\n\nMeeting Topic: Product Planning Discussion\nMain Topics:\n1. New feature development plan\n2. User experience optimization\n3. Technical architecture adjustments\n\nMeeting Conclusions:\n- Determined next quarter\'s development priorities\n- Assigned specific tasks to each team\n- Established milestone timeline',
      citations: [
        {
          fileId: '3',
          snippet: 'Meeting recording minute 15: Product planning discussion begins...',
          fileName: 'Meeting Recording.mp3'
        }
      ],
      createdAt: '2024-01-20T10:31:00Z'
    }
  ],

  apiKeys: [
    {
      id: '1',
      keyMasked: 'memo_****_abc123',
      createdAt: '2024-01-15T10:30:00Z',
      lastUsed: '2024-01-20T14:22:00Z',
      isActive: true
    }
  ],

  integrations: [
    {
      provider: 'google-drive' as const,
      connected: false
    },
    {
      provider: 'notion' as const,
      connected: false
    }
  ]
}

// Simulate delay
export const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

// Simulate API calls
export const mockApi = {
  // Simulate login
  login: async (email: string, password: string) => {
    await delay(1000)
    return {
      token: 'mock-jwt-token-' + Date.now(),
      user: {
        id: '1',
        email,
        name: email.split('@')[0]
      }
    }
  },

  // Simulate registration
  register: async (email: string, password: string, name: string) => {
    await delay(1200)
    return {
      token: 'mock-jwt-token-' + Date.now(),
      user: {
        id: '1',
        email,
        name
      }
    }
  },

  // Simulate file upload
  uploadFile: async (file: File) => {
    await delay(500)
    return {
      id: Date.now().toString(),
      status: 'ready'
    }
  },

  // Simulate query
  query: async (query: string) => {
    await delay(2000)
    return {
      answer: `Based on your memory hub, I found relevant information:\n\n${query} related content can be found in the following documents:\n\n1. Document A page 3 mentions this concept\n2. Document B page 7 has detailed explanation\n3. Document C page 1 has relevant definition`,
      citations: [
        {
          fileId: '1',
          snippet: 'Definition and explanation of related concept...',
          fileName: 'Important Document.pdf'
        },
        {
          fileId: '2',
          snippet: 'Detailed technical explanation and examples...',
          fileName: 'Technical Manual.docx'
        }
      ]
    }
  },

  // Simulate create API Key
  createApiKey: async () => {
    await delay(800)
    return {
      id: Date.now().toString(),
      keyMasked: `memo_${Math.random().toString(36).substr(2, 8)}_${Math.random().toString(36).substr(2, 6)}`,
      createdAt: new Date().toISOString(),
      isActive: true
    }
  },

  // Simulate connect integration
  connectIntegration: async (provider: string) => {
    await delay(1500)
    return {
      provider,
      connected: true,
      account: `${provider}@example.com`,
      lastSync: new Date().toISOString()
    }
  }
}