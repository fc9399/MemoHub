'use client'

import { useState, useCallback } from 'react'
import { useUploadStore } from '@/lib/stores/upload'
import { Upload, File, X } from 'lucide-react'

export function UploadPanel() {
  const [isDragOver, setIsDragOver] = useState(false)
  const { addFile } = useUploadStore()

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    
    const files = Array.from(e.dataTransfer.files)
    files.forEach(file => {
      addFile(file)
    })
  }, [addFile])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    files.forEach(file => {
      addFile(file)
    })
  }, [addFile])

  return (
    <div className="bg-white rounded-2xl shadow-brand p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Upload Files</h2>
      
      <div
        className={`border-2 border-dashed rounded-2xl p-8 text-center transition-colors ${
          isDragOver
            ? 'border-blue-400 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
      >
        <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <p className="text-lg font-medium text-gray-700 mb-2">
          Drag files here or click to select files
        </p>
        <p className="text-sm text-gray-500 mb-4">
          Supports PDF, DOCX, images, and audio files
        </p>
        
        <input
          type="file"
          multiple
          accept=".pdf,.docx,.doc,.jpg,.jpeg,.png,.gif,.webp,.mp3,.wav,.m4a,.aac"
          onChange={handleFileSelect}
          className="hidden"
          id="file-upload"
        />
        <label
          htmlFor="file-upload"
          className="inline-flex items-center px-4 py-2 bg-gray-900 text-white rounded-2xl font-medium hover:bg-gray-800 transition-colors cursor-pointer"
        >
          <File className="w-4 h-4 mr-2" />
          Select Files
        </label>
      </div>
    </div>
  )
}
