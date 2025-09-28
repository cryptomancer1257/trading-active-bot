'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useCreatePrompt, usePrompts } from '@/hooks/usePrompts'
import { PromptTemplate } from '@/hooks/usePrompts'
import { useAuthGuard } from '@/hooks/useAuthGuard'
import { UserRole } from '@/lib/types'
import toast from 'react-hot-toast'
import MarkdownEditor from '@/components/MarkdownEditor'
import { DocumentTextIcon, SparklesIcon } from '@heroicons/react/24/outline'

interface PromptFormData {
  name: string
  description: string
  content: string
  category: 'TRADING' | 'ANALYSIS' | 'RISK_MANAGEMENT'
  is_default: boolean
  is_active: boolean
}

export default function NewPromptPage() {
  const router = useRouter()
  const { user, loading } = useAuthGuard({ 
    requireAuth: true, 
    requiredRole: UserRole.DEVELOPER 
  })

  const [formData, setFormData] = useState<PromptFormData>({
    name: '',
    description: '',
    content: '',
    category: 'TRADING',
    is_default: false,
    is_active: true
  })

  const [isSubmitting, setIsSubmitting] = useState(false)
  const [showTemplates, setShowTemplates] = useState(false)

  const createMutation = useCreatePrompt()
  
  // Get template prompts (default prompts)
  const { data: templatePrompts, isLoading: templatesLoading } = usePrompts({
    limit: 100
  })

  const handleInputChange = (field: keyof PromptFormData, value: string | boolean) => {
    console.log('Input change:', field, value)
    setFormData(prev => {
      const newData = {
        ...prev,
        [field]: value
      }
      console.log('New form data:', newData)
      return newData
    })
  }

  const handleUseTemplate = (template: PromptTemplate) => {
    console.log('Using template:', template)
    console.log('Template content:', template.content)
    setFormData(prev => ({
      ...prev,
      name: template.name,
      description: template.description || '',
      content: template.content,
      category: template.category as 'TRADING' | 'ANALYSIS' | 'RISK_MANAGEMENT'
    }))
    setShowTemplates(false)
    toast.success(`Template "${template.name}" applied!`)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (isSubmitting) return

    setIsSubmitting(true)
    try {
      await createMutation.mutateAsync({
        name: formData.name,
        description: formData.description,
        content: formData.content,
        category: formData.category,
        is_default: formData.is_default,
        is_active: formData.is_active
      })
      
      toast.success('Prompt created successfully!')
      router.push('/creator/prompts')
    } catch (error) {
      console.error('Error creating prompt:', error)
      toast.error('Failed to create prompt. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleCancel = () => {
    router.push('/creator/prompts')
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center neural-grid">
        <div className="card-quantum p-8 text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-quantum-500 mx-auto mb-4"></div>
          <p className="text-gray-300">Loading...</p>
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
                Create New Prompt
              </h1>
              <p className="text-gray-400 mt-2">
                Create a new AI prompt template for trading analysis
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

        {/* Template Prompts Section */}
        <div className="mb-6">
          <button
            type="button"
            onClick={() => setShowTemplates(!showTemplates)}
            className="inline-flex items-center px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
          >
            <SparklesIcon className="h-5 w-5 mr-2" />
            {showTemplates ? 'Hide' : 'Show'} Template Prompts
          </button>
          
          {showTemplates && (
            <div className="mt-4 bg-gray-800 rounded-lg p-4 border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                <DocumentTextIcon className="h-5 w-5 mr-2" />
                Choose from Template Prompts
              </h3>
              {templatesLoading ? (
                <div className="text-center py-4">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-500 mx-auto"></div>
                  <p className="text-gray-400 mt-2">Loading templates...</p>
                </div>
              ) : templatePrompts && templatePrompts.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {templatePrompts.map((template) => (
                    <div key={template.id} className="bg-gray-700 p-4 rounded-lg border border-gray-600 hover:border-purple-500 transition-colors">
                      <h4 className="text-white font-medium mb-2">{template.name}</h4>
                      <p className="text-gray-300 text-sm mb-3 line-clamp-2">{template.description}</p>
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-purple-400 bg-purple-500/20 px-2 py-1 rounded">
                          {template.category}
                        </span>
                        <button
                          type="button"
                          onClick={() => handleUseTemplate(template)}
                          className="text-purple-400 hover:text-purple-300 text-sm font-medium"
                        >
                          Use Template →
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-400 text-center py-4">No template prompts available.</p>
              )}
            </div>
          )}
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
                  GitLab Flavored Markdown editor
                </span>
              </div>

              <MarkdownEditor
                content={formData.content}
                onChange={(content) => handleInputChange('content', content)}
                placeholder="Enter your prompt template here... Use GitLab Flavored Markdown for formatting!"
                className="w-full"
              />
            </div>

            {/* Markdown Tips */}
            <div className="mb-6 p-4 bg-dark-800 border border-gray-600 rounded-md">
              <div className="flex items-start space-x-2">
                <span className="text-yellow-400">💡</span>
                <div className="text-sm text-gray-300">
                  <p className="font-medium mb-2">Markdown Tips:</p>
                  <p>Use <code className="bg-dark-700 px-1 rounded">**bold**</code>, <code className="bg-dark-700 px-1 rounded">*italic*</code>, <code className="bg-dark-700 px-1 rounded">`code`</code>, <code className="bg-dark-700 px-1 rounded">```blocks```</code>, <code className="bg-dark-700 px-1 rounded"># Headers</code>, <code className="bg-dark-700 px-1 rounded">- Lists</code>, <code className="bg-dark-700 px-1 rounded">&gt; Quotes</code></p>
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
                {isSubmitting ? 'Creating...' : 'Create Prompt'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}
