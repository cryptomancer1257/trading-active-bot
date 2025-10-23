'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useMyPrompts, useDeletePrompt, PromptTemplate } from '@/hooks/usePrompts'
import { useAuthGuard } from '@/hooks/useAuthGuard'
import { UserRole } from '@/lib/types'
import toast from 'react-hot-toast'
import { PlusIcon, PencilIcon, TrashIcon, EyeIcon, DocumentTextIcon } from '@heroicons/react/24/outline'

export default function PromptsPage() {
  const router = useRouter()
  const { user, loading } = useAuthGuard({ 
    requireAuth: true, 
    requiredRole: UserRole.DEVELOPER 
  })

  const [viewingPrompt, setViewingPrompt] = useState<PromptTemplate | null>(null)

  const { data: myPrompts, isLoading: myLoading } = useMyPrompts({
    limit: 100
  })

  const deleteMutation = useDeletePrompt()

  if (loading || myLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center neural-grid">
        <div className="card-quantum p-8 text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-quantum-500 mx-auto mb-4"></div>
          <p className="text-gray-300">Loading prompts...</p>
        </div>
      </div>
    )
  }

  const handleCreate = () => {
    router.push('/creator/prompts/new')
  }

  const handleEdit = (prompt: PromptTemplate) => {
    router.push(`/creator/prompts/${prompt.id}/edit`)
  }

  const handleView = (prompt: PromptTemplate) => {
    setViewingPrompt(prompt)
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this strategy template?')) return

    try {
      await deleteMutation.mutateAsync(id)
      toast.success('Strategy template deleted successfully')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to delete strategy template')
    }
  }

  return (
    <div className="min-h-screen neural-grid">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3 mb-4">
                <DocumentTextIcon className="h-8 w-8 text-quantum-400" />
                <h1 className="text-4xl font-bold bg-gradient-to-r from-quantum-400 to-emerald-400 bg-clip-text text-transparent">
                  My Strategies
                </h1>
              </div>
              <p className="text-gray-300 text-lg">
                Manage your AI strategy templates for trading analysis and bot strategies
              </p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => router.push('/creator/strategy-library')}
                className="btn btn-secondary flex items-center gap-2"
              >
                <DocumentTextIcon className="h-5 w-5" />
                Strategy Library
              </button>
              <button
                onClick={handleCreate}
                className="btn-quantum flex items-center gap-2"
              >
                <PlusIcon className="h-5 w-5" />
                Create New Strategy
              </button>
            </div>
          </div>
        </div>

        {/* Strategies Grid */}
        {myPrompts && myPrompts.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {myPrompts.map((prompt) => (
              <div key={prompt.id} className="card-quantum p-6 hover:border-quantum-400/50 transition-colors">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-xl font-semibold text-white mb-2">{prompt.name}</h3>
                    <p className="text-gray-400 text-sm mb-3">{prompt.description || 'No description'}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-1 text-xs rounded ${
                      prompt.category === 'TRADING' ? 'bg-blue-500/20 text-blue-400' :
                      prompt.category === 'ANALYSIS' ? 'bg-purple-500/20 text-purple-400' :
                      'bg-orange-500/20 text-orange-400'
                    }`}>
                      {prompt.category}
                    </span>
                  </div>
                </div>

                <div className="mb-4">
                  <div className="text-gray-300 text-sm line-clamp-3 font-mono">
                    <pre className="whitespace-pre-wrap text-xs leading-relaxed">
                      {prompt.content ? prompt.content.substring(0, 200) + '...' : 'No content available'}
                    </pre>
                  </div>
                  <div className="mt-2 text-xs text-gray-500">
                    {prompt.content && prompt.content.length > 200 ? `${prompt.content.length} characters` : 'Short strategy'}
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleView(prompt)}
                      className="p-2 text-gray-400 hover:text-quantum-400 transition-colors"
                      title="View"
                    >
                      <EyeIcon className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleEdit(prompt)}
                      className="p-2 text-gray-400 hover:text-quantum-400 transition-colors"
                      title="Edit"
                    >
                      <PencilIcon className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(prompt.id)}
                      className="p-2 text-gray-400 hover:text-red-400 transition-colors"
                      title="Delete"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                  <div className="text-xs text-gray-500">
                    {new Date(prompt.created_at).toLocaleDateString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="card-quantum p-12 text-center">
            <DocumentTextIcon className="h-16 w-16 text-gray-500 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-300 mb-2">No Strategies Found</h3>
            <p className="text-gray-500 mb-6">
              You haven't created any strategy templates yet.
            </p>
            <button
              onClick={handleCreate}
              className="btn-quantum"
            >
              Create Your First Strategy
            </button>
          </div>
        )}

        {/* View Modal */}
        {viewingPrompt && (
          <ViewPromptModal
            prompt={viewingPrompt}
            onClose={() => setViewingPrompt(null)}
          />
        )}
      </div>
    </div>
  )
}

// View Strategy Modal Component
function ViewPromptModal({ prompt, onClose }: {
  prompt: PromptTemplate
  onClose: () => void
}) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="card-quantum p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-white">{prompt.name}</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            ✕
          </button>
        </div>

        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-semibold text-white mb-2">Description</h3>
            <p className="text-gray-300">{prompt.description || 'No description provided'}</p>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">Category</h3>
            <span className={`px-3 py-1 rounded text-sm ${
              prompt.category === 'TRADING' ? 'bg-blue-500/20 text-blue-400' :
              prompt.category === 'ANALYSIS' ? 'bg-purple-500/20 text-purple-400' :
              'bg-orange-500/20 text-orange-400'
            }`}>
              {prompt.category}
            </span>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">Content</h3>
            <div className="bg-gray-800 p-4 rounded-lg">
              <div className="text-gray-300 text-sm prose prose-invert max-w-none">
                <pre className="whitespace-pre-wrap font-mono text-sm leading-relaxed">
                  {prompt.content || 'No content available'}
                </pre>
              </div>
            </div>
            <div className="mt-2 text-xs text-gray-400">
              📝 <strong>Format:</strong> This strategy supports Markdown formatting for better readability
            </div>
          </div>

          <div className="flex items-center gap-4">
            <span className={`px-2 py-1 rounded text-xs ${
              prompt.is_active ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
            }`}>
              {prompt.is_active ? 'Active' : 'Inactive'}
            </span>
          </div>

          <div className="text-sm text-gray-500">
            Created: {new Date(prompt.created_at).toLocaleString()}
            {prompt.updated_at !== prompt.created_at && (
              <span> • Updated: {new Date(prompt.updated_at).toLocaleString()}</span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}