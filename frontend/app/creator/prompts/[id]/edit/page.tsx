'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { usePrompt, useUpdatePrompt } from '@/hooks/usePrompts'
import { PromptTemplate } from '@/hooks/usePrompts'
import { useAuthGuard } from '@/hooks/useAuthGuard'
import { UserRole } from '@/lib/types'
import toast from 'react-hot-toast'
import MarkdownEditor from '@/components/MarkdownEditor'
import PromptVariableTester from '@/components/PromptVariableTester'

interface PromptFormData {
  name: string
  description: string
  content: string
  category: 'TRADING' | 'ANALYSIS' | 'RISK_MANAGEMENT'
  is_default: boolean
  is_active: boolean
}

export default function EditPromptPage() {
  const router = useRouter()
  const params = useParams()
  const promptId = params.id as string

  const { user, loading } = useAuthGuard({ 
    requireAuth: true, 
    requiredRole: UserRole.DEVELOPER 
  })

  const { data: prompt, isLoading: promptLoading } = usePrompt(parseInt(promptId))
  const updateMutation = useUpdatePrompt()

  const [formData, setFormData] = useState<PromptFormData>({
    name: '',
    description: '',
    content: '',
    category: 'TRADING',
    is_default: false,
    is_active: true
  })

  const [isSubmitting, setIsSubmitting] = useState(false)
  const [showVariableTester, setShowVariableTester] = useState(false)

  // Populate form when prompt data loads
  useEffect(() => {
    if (prompt) {
      console.log('📥 Loading prompt data:', prompt)
      setFormData({
        name: prompt.name || '',
        description: prompt.description || '',
        content: prompt.content || '',
        category: prompt.category || 'TRADING',
        is_default: prompt.is_default || false,
        is_active: prompt.is_active || true
      })
    }
  }, [prompt])

  const handleInputChange = (field: keyof PromptFormData, value: string | boolean) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (isSubmitting) return

    console.log('📝 Form data being submitted:', formData)
    setIsSubmitting(true)
    try {
      await updateMutation.mutateAsync({
        promptId: parseInt(promptId),
        data: {
          name: formData.name,
          description: formData.description,
          content: formData.content,
          category: formData.category,
          is_default: formData.is_default,
          is_active: formData.is_active
        }
      })
      
      toast.success('Prompt updated successfully!')
      // Small delay to ensure cache is updated
      setTimeout(() => {
        router.push('/creator/prompts')
      }, 500)
    } catch (error) {
      console.error('Error updating prompt:', error)
      toast.error('Failed to update prompt. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleCancel = () => {
    router.push('/creator/prompts')
  }

  if (loading || promptLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center neural-grid">
        <div className="card-quantum p-8 text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-quantum-500 mx-auto mb-4"></div>
          <p className="text-gray-300">Loading prompt...</p>
        </div>
      </div>
    )
  }

  if (!prompt) {
    return (
      <div className="min-h-screen flex items-center justify-center neural-grid">
        <div className="card-quantum p-8 text-center">
          <h1 className="text-2xl font-bold text-gray-200 mb-4">Prompt Not Found</h1>
          <p className="text-gray-400 mb-6">The requested prompt template could not be found.</p>
          <button
            onClick={() => router.push('/creator/prompts')}
            className="btn btn-primary px-6 py-2"
          >
            Back to Prompts
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-dark-900 neural-grid">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 via-blue-600 to-cyan-600 bg-clip-text text-transparent">
                Edit Prompt
              </h1>
              <p className="text-gray-400 mt-2">
                Modify the AI prompt template
              </p>
            </div>
            <button
              onClick={handleCancel}
              className="btn btn-secondary px-4 py-2"
            >
              ← Back to Prompts
            </button>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="card-quantum p-6">
            {/* Basic Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Name *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  className="w-full px-3 py-2 bg-dark-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-quantum-500"
                  placeholder="Enter prompt name"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Category *
                </label>
                <select
                  value={formData.category}
                  onChange={(e) => handleInputChange('category', e.target.value as any)}
                  className="w-full px-3 py-2 bg-dark-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-quantum-500"
                >
                  <option value="TRADING">Trading</option>
                  <option value="ANALYSIS">Analysis</option>
                  <option value="RISK_MANAGEMENT">Risk Management</option>
                </select>
              </div>
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Description *
              </label>
              <input
                type="text"
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                className="w-full px-3 py-2 bg-dark-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-quantum-500"
                placeholder="Brief description of this prompt template"
                required
              />
            </div>

            {/* Content Editor */}
            <div className="mb-6">
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-300">
                  Content *
                </label>
                <span className="text-xs text-gray-500">
                  Professional Markdown editor
                </span>
              </div>

              <MarkdownEditor
                content={formData.content}
                onChange={(content) => handleInputChange('content', content)}
                placeholder="Enter your prompt template here... Use Markdown for formatting!"
                className="w-full"
              />
            </div>

            {/* Editor Tips */}
            <div className="mb-6 p-4 bg-dark-800 border border-gray-600 rounded-md">
              <div className="flex items-start space-x-2">
                <span className="text-yellow-400">💡</span>
                <div className="text-sm text-gray-300">
                  <p className="font-medium mb-2">Editor Tips:</p>
                  <p>Use <code className="bg-dark-700 px-1 rounded">**bold**</code>, <code className="bg-dark-700 px-1 rounded">*italic*</code>, <code className="bg-dark-700 px-1 rounded">`code`</code>, <code className="bg-dark-700 px-1 rounded">```blocks```</code>, <code className="bg-dark-700 px-1 rounded"># Headers</code>, <code className="bg-dark-700 px-1 rounded">- Lists</code>, <code className="bg-dark-700 px-1 rounded">&gt; Quotes</code>. Press F11 for fullscreen mode.</p>
                </div>
              </div>
            </div>

            {/* Settings */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              <div className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  id="is_default"
                  checked={formData.is_default}
                  onChange={(e) => handleInputChange('is_default', e.target.checked)}
                  className="w-4 h-4 text-quantum-500 bg-dark-700 border-gray-600 rounded focus:ring-quantum-500"
                />
                <label htmlFor="is_default" className="text-sm text-gray-300">
                  Set as default template
                </label>
              </div>

              <div className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={formData.is_active}
                  onChange={(e) => handleInputChange('is_active', e.target.checked)}
                  className="w-4 h-4 text-quantum-500 bg-dark-700 border-gray-600 rounded focus:ring-quantum-500"
                />
                <label htmlFor="is_active" className="text-sm text-gray-300">
                  Active
                </label>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-end space-x-4">
              <button
                type="button"
                onClick={handleCancel}
                className="btn btn-secondary px-6 py-2"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting || !formData.name || !formData.content}
                className="btn btn-primary px-6 py-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Updating...' : 'Update Prompt'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}
