'use client'

import { useState, useRef } from 'react'
import { api } from '@/lib/api'
import { PhotoIcon, XMarkIcon } from '@heroicons/react/24/outline'

interface ImageUploadProps {
  value?: string
  onChange: (url: string) => void
  className?: string
  disabled?: boolean
}

export default function ImageUpload({ value, onChange, className = '', disabled = false }: ImageUploadProps) {
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp']
    if (!allowedTypes.includes(file.type)) {
      setError('Chỉ hỗ trợ định dạng JPEG, PNG, WebP')
      return
    }

    // Validate file size (5MB max)
    const maxSize = 5 * 1024 * 1024 // 5MB
    if (file.size > maxSize) {
      setError('Kích thước file không được vượt quá 5MB')
      return
    }

    setIsUploading(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await api.post('/bots/upload-image', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      if (response.data.success) {
        onChange(response.data.url)
      } else {
        setError('Upload thất bại')
      }
    } catch (err: any) {
      console.error('Upload error:', err)
      setError(err.response?.data?.detail || 'Upload thất bại')
    } finally {
      setIsUploading(false)
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const handleRemove = () => {
    onChange('')
    setError(null)
  }

  const handleClick = () => {
    if (!disabled && !isUploading) {
      fileInputRef.current?.click()
    }
  }

  return (
    <div className={`space-y-3 ${className}`}>
      {/* Upload Area */}
      <div
        onClick={handleClick}
        className={`
          relative border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors
          ${disabled || isUploading 
            ? 'border-gray-400 bg-gray-100 cursor-not-allowed' 
            : 'border-gray-300 hover:border-purple-400 hover:bg-purple-50'
          }
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          onChange={handleFileSelect}
          className="hidden"
          disabled={disabled || isUploading}
        />

        {value ? (
          // Show uploaded image
          <div className="relative">
            <img
              src={value}
              alt="Bot preview"
              className="mx-auto h-32 w-32 object-cover rounded-lg"
            />
            {!disabled && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation()
                  handleRemove()
                }}
                className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 hover:bg-red-600"
              >
                <XMarkIcon className="h-4 w-4" />
              </button>
            )}
          </div>
        ) : (
          // Show upload prompt
          <div>
            <PhotoIcon className="mx-auto h-12 w-12 text-gray-400" />
            <div className="mt-2">
              <p className="text-sm text-gray-600">
                {isUploading ? 'Đang upload...' : 'Click để upload hình ảnh'}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                JPEG, PNG, WebP (tối đa 5MB)
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <p className="text-sm text-red-600">{error}</p>
      )}

      {/* Upload Progress */}
      {isUploading && (
        <div className="flex items-center space-x-2">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-purple-500"></div>
          <span className="text-sm text-gray-600">Đang upload...</span>
        </div>
      )}
    </div>
  )
}
