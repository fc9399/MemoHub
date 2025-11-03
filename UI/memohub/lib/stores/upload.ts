import { create } from 'zustand'
import { uploadApi, searchApi } from '../api'

export interface FileItem {
  id: string
  name: string
  type: 'pdf' | 'docx' | 'txt' | 'image' | 'audio' | 'document' | 'text'
  size: number
  status: 'ready' | 'fail' | 'uploading' | 'processing'
  tags?: string[]
  s3_key?: string
  s3_url?: string
  memory_id?: string
  updatedAt: string
  created_at?: string
}

interface UploadState {
  items: FileItem[]
  progress: Record<string, number>
  isLoading: boolean
  error: string | null
  addFile: (file: File) => Promise<void>
  uploadText: (text: string, source?: string) => Promise<void>
  loadMemories: () => Promise<void>
  updateStatus: (id: string, status: FileItem['status']) => void
  updateProgress: (id: string, progress: number) => void
  deleteFile: (id: string) => Promise<void>
  clearError: () => void
}

export const useUploadStore = create<UploadState>((set, get) => ({
  items: [],
  progress: {},
  isLoading: false,
  error: null,
  
  addFile: async (file: File) => {
    const id = `upload_${Date.now()}`
    const fileType = getFileType(file.name)
    
    // Add file to list with uploading status
    const newFile: FileItem = {
      id,
      name: file.name,
      type: fileType,
      size: file.size,
      status: 'uploading',
      updatedAt: new Date().toISOString()
    }
    
    set((state) => ({
      items: [...state.items, newFile],
      progress: { ...state.progress, [id]: 0 },
      isLoading: true,
      error: null
    }))
    
    try {
      get().updateProgress(id, 50)
      
      // Call real API to upload
      const response = await uploadApi.upload(file, true)
      
      // Update file status
      get().updateStatus(id, 'ready')
      get().updateProgress(id, 100)
      
      // Update file information
      set((state) => ({
        items: state.items.map(item => 
          item.id === id 
            ? {
                ...item,
                s3_key: response.data.s3_key,
                s3_url: response.data.file_url,
                memory_id: response.memory?.memory_id,
                status: 'ready',
                updatedAt: response.data.upload_time
              }
            : item
        ),
        isLoading: false
      }))
      
      // Reload memory list
      await get().loadMemories()
    } catch (error: any) {
      console.error('Upload failed:', error)
      get().updateStatus(id, 'fail')
      get().updateProgress(id, 0)
      set({
        error: error.message || 'File upload failed',
        isLoading: false
      })
    }
  },
  
  uploadText: async (text: string, source?: string) => {
    set({ isLoading: true, error: null })
    try {
      const response = await uploadApi.uploadText(text, source)
      
      // Reload memory list
      await get().loadMemories()
      set({ isLoading: false })
    } catch (error: any) {
      console.error('Text upload failed:', error)
      set({
        error: error.message || 'Text upload failed',
        isLoading: false
      })
    }
  },
  
  loadMemories: async () => {
    set({ isLoading: true, error: null })
    try {
      const response = await searchApi.getMemories({ limit: 100 })
      
      // Convert memories to file item format
      const fileItems: FileItem[] = response.memories.map((memory) => ({
        id: memory.id,
        name: memory.metadata?.original_filename || memory.source || `Memory ${memory.id.slice(0, 8)}`,
        type: memory.memory_type as FileItem['type'],
        size: memory.metadata?.file_size || 0,
        status: 'ready' as const,
        tags: memory.tags || [],
        s3_key: memory.metadata?.s3_key,
        s3_url: memory.source,
        memory_id: memory.id,
        updatedAt: memory.updated_at,
        created_at: memory.created_at
      }))
      
      set({
        items: fileItems,
        isLoading: false
      })
    } catch (error: any) {
      console.error('Failed to load memories:', error)
      set({
        error: error.message || 'Failed to load memory list',
        isLoading: false
      })
    }
  },
  
  updateStatus: (id: string, status: FileItem['status']) => {
    set((state) => ({
      items: state.items.map(item => 
        item.id === id ? { ...item, status } : item
      )
    }))
  },
  
  updateProgress: (id: string, progress: number) => {
    set((state) => ({
      progress: { ...state.progress, [id]: progress }
    }))
  },
  
  deleteFile: async (id: string) => {
    try {
      // Try to delete memory
      await searchApi.deleteMemory(id)
      
      // Remove from list
      set((state) => ({
        items: state.items.filter(item => item.id !== id),
        progress: Object.fromEntries(
          Object.entries(state.progress).filter(([key]) => key !== id)
        )
      }))
    } catch (error: any) {
      console.error('Failed to delete file:', error)
      // Remove from local list even if deletion fails
      set((state) => ({
        items: state.items.filter(item => item.id !== id),
        progress: Object.fromEntries(
          Object.entries(state.progress).filter(([key]) => key !== id)
        )
      }))
    }
  },
  
  clearError: () => {
    set({ error: null })
  }
}))

function getFileType(filename: string): FileItem['type'] {
  const ext = filename.toLowerCase().split('.').pop()
  if (['pdf'].includes(ext || '')) return 'pdf'
  if (['docx', 'doc'].includes(ext || '')) return 'docx'
  if (['txt', 'md'].includes(ext || '')) return 'txt'
  if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext || '')) return 'image'
  if (['mp3', 'wav', 'm4a', 'aac'].includes(ext || '')) return 'audio'
  return 'document' // default
}


