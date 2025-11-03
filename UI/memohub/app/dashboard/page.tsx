'use client'

import { useEffect } from 'react'
import { UploadPanel } from '@/components/upload-panel'
import { FileTable } from '@/components/file-table'
import { useUploadStore } from '@/lib/stores/upload'

export default function DashboardPage() {
  const { loadMemories } = useUploadStore()
  
  useEffect(() => {
    // Load memory list when page loads
    loadMemories()
    
    // Listen for integration sync success event, automatically refresh memory list
    const handleMemoriesUpdated = () => {
      console.log('🔄 Detected memory update, refreshing list...')
      loadMemories()
    }
    
    window.addEventListener('memories-updated', handleMemoriesUpdated)
    
    return () => {
      window.removeEventListener('memories-updated', handleMemoriesUpdated)
    }
  }, [loadMemories])
  
  return (
    <div className="space-y-8 overflow-x-hidden max-w-full">
      {/* Upload Section */}
      <UploadPanel />
      
      {/* Files Table */}
      <FileTable />
    </div>
  )
}


