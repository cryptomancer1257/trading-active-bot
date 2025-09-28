'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { 
  ArrowLeftIcon, 
  PencilIcon, 
  TrashIcon,
  EyeIcon,
  DocumentTextIcon,
  TagIcon,
  CalendarIcon,
  UserIcon
} from '@heroicons/react/24/outline'
import { usePrompt, useDeletePrompt } from '@/hooks/usePrompts'
import { useAuthGuard } from '@/hooks/useAuthGuard'
import toast from 'react-hot-toast'
import MarkdownEditor from '@/components/MarkdownEditor'

interface PromptDetailPageProps {
  params: {
    id: string
  }
}

export default function PromptDetailPage({ params }: PromptDetailPageProps) {
  const router = useRouter()
  const { id } = params
  const { user, loading: authLoading } = useAuthGuard()
  
  const { data: prompt, isLoading: promptLoading, error: promptError } = usePrompt(parseInt(id))
  const deletePrompt = useDeletePrompt()
  
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  // Redirect if not authenticated
  if (!authLoading && !user) {
    router.push('/login')
    return null
  }

  // Loading state
  if (authLoading || promptLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    )
  }

  // Error state
  if (promptError || !prompt) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-white mb-4">Prompt Not Found</h1>
          <p className="text-gray-400 mb-6">The prompt you're looking for doesn't exist or you don't have permission to view it.</p>
          <button
            onClick={() => router.push('/creator/prompts')}
            className="btn btn-primary"
          >
            Back to Prompts
          </button>
        </div>
      </div>
    )
  }

  const handleEdit = () => {
    router.push(`/creator/prompts/${id}/edit`)
  }

  const handleDelete = async () => {
    if (!prompt) return
    
    setIsDeleting(true)
    try {
      await deletePrompt.mutateAsync(prompt.id)
      toast.success('Prompt deleted successfully!')
      router.push('/creator/prompts')
    } catch (error) {
      console.error('Error deleting prompt:', error)
      toast.error('Failed to delete prompt. Please try again.')
    } finally {
      setIsDeleting(false)
      setShowDeleteModal(false)
    }
  }

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'TRADING':
        return 'bg-green-500/20 text-green-400'
      case 'ANALYSIS':
        return 'bg-blue-500/20 text-blue-400'
      case 'RISK_MANAGEMENT':
        return 'bg-red-500/20 text-red-400'
      default:
        return 'bg-gray-500/20 text-gray-400'
    }
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <button
              onClick={() => router.push('/creator/prompts')}
              className="flex items-center text-gray-400 hover:text-white transition-colors"
            >
              <ArrowLeftIcon className="h-5 w-5 mr-2" />
              Back to Prompts
            </button>
            
            <div className="flex items-center space-x-3">
              <button
                onClick={handleEdit}
                className="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
              >
                <PencilIcon className="h-4 w-4 mr-2" />
                Edit
              </button>
              <button
                onClick={() => setShowDeleteModal(true)}
                className="flex items-center px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors"
              >
                <TrashIcon className="h-4 w-4 mr-2" />
                Delete
              </button>
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h1 className="text-3xl font-bold text-white mb-2">{prompt.name}</h1>
                <p className="text-gray-400 text-lg">{prompt.description}</p>
              </div>
              <div className="flex items-center space-x-2">
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getCategoryColor(prompt.category)}`}>
                  {prompt.category}
                </span>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  prompt.is_active ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                }`}>
                  {prompt.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
            </div>

            {/* Metadata */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-400">
              <div className="flex items-center">
                <UserIcon className="h-4 w-4 mr-2" />
                <span>Created by: {prompt.created_by ? `User ${prompt.created_by}` : 'System'}</span>
              </div>
              <div className="flex items-center">
                <CalendarIcon className="h-4 w-4 mr-2" />
                <span>Created: {new Date(prompt.created_at).toLocaleDateString()}</span>
              </div>
              <div className="flex items-center">
                <CalendarIcon className="h-4 w-4 mr-2" />
                <span>Updated: {new Date(prompt.updated_at).toLocaleDateString()}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="bg-gray-800 rounded-lg border border-gray-700">
          <div className="p-6 border-b border-gray-700">
            <div className="flex items-center">
              <DocumentTextIcon className="h-6 w-6 text-blue-400 mr-2" />
              <h2 className="text-xl font-semibold text-white">Prompt Content</h2>
            </div>
          </div>
          
          <div className="p-6">
            <div className="bg-gray-900 rounded-lg p-4 border border-gray-600">
              <MarkdownEditor
                content={prompt.content || ''}
                onChange={() => {}} // Read-only mode
                placeholder="No content available"
                readOnly={true}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-gray-900 bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-gray-800 p-6 rounded-lg shadow-xl max-w-md w-full border border-gray-700">
            <h3 className="text-xl font-semibold text-white mb-4">Delete Prompt</h3>
            <p className="text-gray-400 mb-6">
              Are you sure you want to delete "{prompt.name}"? This action cannot be undone.
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowDeleteModal(false)}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md transition-colors"
                disabled={isDeleting}
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors"
                disabled={isDeleting}
              >
                {isDeleting ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
