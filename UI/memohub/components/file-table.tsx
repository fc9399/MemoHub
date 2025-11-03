'use client'

import { useUploadStore, FileItem } from '@/lib/stores/upload'
import { 
  FileText, 
  Image, 
  Music, 
  Tag, 
  MoreVertical,
  CheckCircle,
  AlertCircle,
  X,
  Trash2,
  Upload,
  Loader2
} from 'lucide-react'
import { useState } from 'react'

const fileTypeIcons: Record<string, any> = {
  pdf: FileText,
  docx: FileText,
  txt: FileText,
  image: Image,
  audio: Music,
  document: FileText,
  text: FileText,
}

const statusConfig: Record<string, { label: string; color: string; icon: any }> = {
  ready: { label: 'Ready', color: 'text-green-600', icon: CheckCircle },
  fail: { label: 'Fail', color: 'text-red-600', icon: AlertCircle },
  uploading: { label: 'Uploading', color: 'text-blue-600', icon: Upload },
  processing: { label: 'Processing', color: 'text-yellow-600', icon: Loader2 },
}

export function FileTable() {
  const { items, deleteFile, addTag, removeTag } = useUploadStore()
  const [newTag, setNewTag] = useState<Record<string, string>>({})

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const handleAddTag = (fileId: string) => {
    const tag = newTag[fileId]?.trim()
    if (tag) {
      addTag(fileId, tag)
      setNewTag(prev => ({ ...prev, [fileId]: '' }))
    }
  }

  return (
    <div className="bg-white rounded-2xl shadow-brand">
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900">File List</h2>
      </div>
      
      <div className="overflow-x-hidden">
        <table className="w-full table-fixed">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                File
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Type
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Size
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Tags
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {items.map((file) => {
              const IconComponent = fileTypeIcons[file.type] || FileText
              const statusInfo = statusConfig[file.status] || statusConfig.fail
              const StatusComponent = statusInfo.icon
              
              return (
                <tr key={file.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="flex items-center min-w-0">
                      <IconComponent className="w-5 h-5 text-gray-400 mr-3 flex-shrink-0" />
                      <div className="min-w-0 flex-1">
                        <div className="text-sm font-medium text-gray-900 truncate" title={file.name}>
                          {file.name}
                        </div>
                        <div className="text-sm text-gray-500">
                          {new Date(file.updatedAt).toLocaleDateString()}
                        </div>
                      </div>
                    </div>
                  </td>
                  
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                      {file.type.toUpperCase()}
                    </span>
                  </td>
                  
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatFileSize(file.size)}
                  </td>
                  
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <StatusComponent className={`w-4 h-4 mr-2 ${statusInfo.color} ${file.status === 'processing' ? 'animate-spin' : ''}`} />
                      <span className={`text-sm font-medium ${statusInfo.color}`}>
                        {statusInfo.label}
                      </span>
                    </div>
                  </td>
                  
                  <td className="px-6 py-4">
                    <div className="flex flex-wrap gap-1 mb-2">
                      {file.tags?.map((tag, index) => (
                        <span
                          key={index}
                          className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                        >
                          {tag}
                          <button
                            onClick={() => removeTag(file.id, tag)}
                            className="ml-1 hover:text-blue-600"
                          >
                            <X className="w-3 h-3" />
                          </button>
                        </span>
                      ))}
                    </div>
                    <div className="flex items-center space-x-2">
                      <input
                        type="text"
                        placeholder="Add tag"
                        value={newTag[file.id] || ''}
                        onChange={(e) => setNewTag(prev => ({ ...prev, [file.id]: e.target.value }))}
                        className="text-xs border border-gray-300 rounded px-2 py-1 w-24"
                        onKeyPress={(e) => e.key === 'Enter' && handleAddTag(file.id)}
                      />
                      <button
                        onClick={() => handleAddTag(file.id)}
                        className="text-xs bg-blue-500 text-white px-2 py-1 rounded hover:bg-blue-600"
                      >
                        Add
                      </button>
                    </div>
                  </td>
                  
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => deleteFile(file.id)}
                        className="p-2 rounded-lg transition-colors bg-red-100 text-red-600 hover:bg-red-200"
                        title="Delete file"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
        
        {items.length === 0 && (
          <div className="text-center py-12">
            <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">No files yet, please upload files first</p>
          </div>
        )}
      </div>
    </div>
  )
}
