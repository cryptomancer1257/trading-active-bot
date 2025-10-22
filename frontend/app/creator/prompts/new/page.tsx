'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useCreatePrompt, useTradingStrategyTemplates, usePromptCategories, TradingStrategyTemplate } from '@/hooks/usePrompts'
import { useAuthGuard } from '@/hooks/useAuthGuard'
import { UserRole } from '@/lib/types'
import toast from 'react-hot-toast'
import MarkdownEditor from '@/components/MarkdownEditor'
import { DocumentTextIcon, SparklesIcon, LockClosedIcon } from '@heroicons/react/24/outline'
import { usePlan } from '@/hooks/usePlan'
import UpgradeModal from '@/components/UpgradeModal'

interface PromptFormData {
  name: string
  description: string
  content: string
  category: string  // Can be full category name from DB or form value (TRADING/ANALYSIS/RISK_MANAGEMENT)
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
    category: 'TRADING',  // Default, will be overridden by first category from DB
    is_default: false,
    is_active: true
  })

  const [isSubmitting, setIsSubmitting] = useState(false)
  const [showTemplates, setShowTemplates] = useState(false)
  const [activeCategory, setActiveCategory] = useState<string>('all')  // Default to "All" filter
  const [showUpgradeModal, setShowUpgradeModal] = useState(false)

  const createMutation = useCreatePrompt()
  const { isFree, isPro } = usePlan()
  
  // Free plan can only access first 5 templates
  const FREE_TEMPLATE_LIMIT = 5
  
  // Get trading strategy templates from library (17+ pre-seeded strategies)
  const { data: templatePrompts, isLoading: templatesLoading } = useTradingStrategyTemplates({
    limit: 100
  })
  
  // Get prompt categories from database
  const { data: promptCategories, isLoading: categoriesLoading } = usePromptCategories()
  
  // Filter templates by active category (exact match)
  const filteredTemplates = templatePrompts?.filter(template => 
    activeCategory === 'all' || template.category === activeCategory
  ) || []
  
  // Helper function to map category name to form value (for backend submission)
  const mapCategoryToFormValue = (categoryName: string): 'TRADING' | 'ANALYSIS' | 'RISK_MANAGEMENT' => {
    const normalized = categoryName.toUpperCase().replace(/\s+/g, '_')
    if (normalized.includes('RISK') || normalized.includes('MANAGEMENT')) return 'RISK_MANAGEMENT'
    if (normalized.includes('ANALYSIS')) return 'ANALYSIS'
    return 'TRADING'
  }
  
  // Prepare categories for dropdown - group by parent category
  const categoriesForDropdown = promptCategories?.map(cat => ({
    value: cat.category_name,  // Use full category name as value
    label: cat.category_name,
    count: cat.template_count,
    parent: cat.parent_category,
    formValue: mapCategoryToFormValue(cat.category_name)
  })).sort((a, b) => {
    // Sort by parent, then by label
    if (a.parent !== b.parent) {
      return (a.parent || '').localeCompare(b.parent || '')
    }
    return a.label.localeCompare(b.label)
  })
  
  // Update default category when categories load
  useEffect(() => {
    if (categoriesForDropdown && categoriesForDropdown.length > 0) {
      // Set to first category from DB on initial load
      const firstCategory = categoriesForDropdown[0].value
      setFormData(prev => {
        // Only update if still using default TRADING value
        if (prev.category === 'TRADING' && firstCategory !== 'TRADING') {
          return { ...prev, category: firstCategory }
        }
        return prev
      })
    }
  }, [categoriesForDropdown])

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

  const handleUseTemplate = (strategy: TradingStrategyTemplate) => {
    console.log('Using template:', strategy)
    console.log('Template prompt:', strategy.prompt)
    
    setFormData(prev => ({
      ...prev,
      name: strategy.title,
      description: `${strategy.category} | ${strategy.timeframe || 'Any'} | Win Rate: ${strategy.win_rate_estimate || 'N/A'}`,
      content: strategy.prompt,
      category: strategy.category  // Keep the full category name from template
    }))
    setShowTemplates(false)
    toast.success(`Template "${strategy.title}" applied!`)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (isSubmitting) return

    setIsSubmitting(true)
    try {
      // Map category to backend form value (TRADING/ANALYSIS/RISK_MANAGEMENT)
      const backendCategory = mapCategoryToFormValue(formData.category)
      
      await createMutation.mutateAsync({
        name: formData.name,
        description: formData.description,
        content: formData.content,
        category: backendCategory,  // Use mapped form value for backend
        is_default: formData.is_default,
        is_active: formData.is_active
      })
      
      toast.success('Strategy created successfully!')
      router.push('/creator/prompts')
    } catch (error) {
      console.error('Error creating strategy:', error)
      toast.error('Failed to create strategy. Please try again.')
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
                Create New Strategy
              </h1>
              <p className="text-gray-400 mt-2">
                Create a new AI strategy template for trading analysis
              </p>
            </div>
            <button
              onClick={handleCancel}
              className="btn btn-secondary px-4 py-2"
            >
              ← Back to Strategies
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
            {showTemplates ? 'Hide' : 'Show'} Template Strategies
          </button>
          
          {showTemplates && (
            <div className="mt-4 bg-gray-800 rounded-lg p-4 border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                <DocumentTextIcon className="h-5 w-5 mr-2" />
                Choose from Template Strategies
              </h3>
              
              {/* Category Tabs - Trading vs Risk Management */}
              {!templatesLoading && templatePrompts && templatePrompts.length > 0 && (
                <div className="mb-4 flex flex-wrap gap-2">
                  <button
                    onClick={() => setActiveCategory('all')}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      activeCategory === 'all'
                        ? 'bg-purple-600 text-white'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    🌟 All ({templatePrompts.length})
                  </button>
                  
                  <button
                    onClick={() => setActiveCategory('Trading')}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      activeCategory === 'Trading'
                        ? 'bg-purple-600 text-white'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    📈 Trading Strategies ({templatePrompts.filter(t => t.category === 'Trading').length})
                  </button>
                  
                  <button
                    onClick={() => setActiveCategory('Risk Management')}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      activeCategory === 'Risk Management'
                        ? 'bg-purple-600 text-white'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    🛡️ Risk Management ({templatePrompts.filter(t => t.category === 'Risk Management').length})
                  </button>
                </div>
              )}
              
              {templatesLoading ? (
                <div className="text-center py-4">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-500 mx-auto"></div>
                  <p className="text-gray-400 mt-2">Loading templates...</p>
                </div>
              ) : filteredTemplates.length > 0 ? (
                <>
                  <div className="mb-4 flex items-center justify-between">
                    <div className="text-sm text-gray-400">
                      Showing {filteredTemplates.length} template{filteredTemplates.length !== 1 ? 's' : ''}
                      {isFree && filteredTemplates.length > FREE_TEMPLATE_LIMIT && (
                        <span className="ml-2 text-yellow-400">
                          (Free plan: {FREE_TEMPLATE_LIMIT} unlocked, {filteredTemplates.length - FREE_TEMPLATE_LIMIT} locked)
                        </span>
                      )}
                    </div>
                    {isFree && filteredTemplates.length > FREE_TEMPLATE_LIMIT && (
                      <button
                        type="button"
                        onClick={() => setShowUpgradeModal(true)}
                        className="text-xs px-3 py-1.5 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-semibold rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all"
                      >
                        Unlock All Templates
                      </button>
                    )}
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {filteredTemplates.map((template, index) => {
                      const isLocked = isFree && index >= FREE_TEMPLATE_LIMIT
                      
                      return (
                        <div 
                          key={template.id} 
                          className={`relative bg-gray-700 p-4 rounded-lg border transition-colors ${
                            isLocked 
                              ? 'border-gray-600 opacity-50' 
                              : 'border-gray-600 hover:border-purple-500'
                          }`}
                        >
                          {/* Locked Overlay */}
                          {isLocked && (
                            <div className="absolute inset-0 bg-dark-900/70 backdrop-blur-[2px] rounded-lg flex flex-col items-center justify-center z-10">
                              <LockClosedIcon className="h-8 w-8 text-yellow-400 mb-2" />
                              <p className="text-white font-semibold mb-2">Premium Template</p>
                              <button
                                type="button"
                                onClick={() => setShowUpgradeModal(true)}
                                className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white text-sm font-semibold rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all shadow-lg"
                              >
                                Unlock Now
                              </button>
                            </div>
                          )}
                          
                          <h4 className="text-white font-medium mb-2">{template.title}</h4>
                          <p className="text-gray-300 text-sm mb-3 line-clamp-2">
                            {template.best_for || 'Advanced trading strategy'}
                          </p>
                          
                          {/* Tags: Category, Timeframe, Win Rate */}
                          <div className="flex items-center gap-2 mb-3 flex-wrap">
                            <span className="text-xs text-purple-400 bg-purple-500/20 px-2 py-1 rounded font-medium">
                              📊 {template.category}
                            </span>
                            {template.timeframe && (
                              <span className="text-xs text-blue-400 bg-blue-500/20 px-2 py-1 rounded font-medium">
                                ⏱️ {template.timeframe}
                              </span>
                            )}
                            {template.win_rate_estimate && (
                              <span className="text-xs text-green-400 bg-green-500/20 px-2 py-1 rounded font-medium">
                                📈 {template.win_rate_estimate}
                              </span>
                            )}
                          </div>
                          
                          <div className="flex items-center justify-end">
                            {!isLocked && (
                              <button
                                type="button"
                                onClick={() => handleUseTemplate(template)}
                                className="text-purple-400 hover:text-purple-300 text-sm font-medium"
                              >
                                Use Template →
                              </button>
                            )}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </>
              ) : templatePrompts && templatePrompts.length > 0 ? (
                <p className="text-gray-400 text-center py-4">
                  No templates found in "{activeCategory}" category.
                </p>
              ) : (
                <p className="text-gray-400 text-center py-4">No template strategies available.</p>
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
                  placeholder="Enter strategy name"
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
                  disabled={categoriesLoading}
                >
                  {categoriesLoading ? (
                    <option>Loading categories...</option>
                  ) : categoriesForDropdown && categoriesForDropdown.length > 0 ? (
                    categoriesForDropdown.map((cat, idx) => (
                      <option key={idx} value={cat.value}>
                        {cat.label} {cat.count > 0 ? `(${cat.count} templates)` : ''}
                      </option>
                    ))
                  ) : (
                    <>
                      <option value="TRADING">Trading</option>
                      <option value="ANALYSIS">Analysis</option>
                      <option value="RISK_MANAGEMENT">Risk Management</option>
                    </>
                  )}
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
                placeholder="Brief description of this strategy template"
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
                placeholder="Enter your strategy template here... Use Markdown for formatting!"
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
                {isSubmitting ? 'Creating...' : 'Create Strategy'}
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Upgrade Modal */}
      <UpgradeModal 
        isOpen={showUpgradeModal}
        onClose={() => setShowUpgradeModal(false)}
        targetPlan="pro"
      />
    </div>
  )
}
