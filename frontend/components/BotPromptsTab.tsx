'use client'

import { useState } from 'react'
import Link from 'next/link'
import { 
  PlusIcon, 
  TrashIcon, 
  PencilIcon, 
  SparklesIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  LightBulbIcon,
  EyeIcon
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'
import { useBotPrompts, useAttachPrompt, useDetachPrompt, useUpdateBotPrompt } from '@/hooks/useBotPrompts'
import { useMyPrompts } from '@/hooks/usePrompts'

interface BotPromptsTabProps {
  botId: number
}

export default function BotPromptsTab({ botId }: BotPromptsTabProps) {
  const [showAttachModal, setShowAttachModal] = useState(false)
  const [selectedPrompt, setSelectedPrompt] = useState<any>(null)
  const [priority, setPriority] = useState(0)
  const [customOverride, setCustomOverride] = useState('')

  // Use real data hooks
  const { data: botPrompts, isLoading: botPromptsLoading, error: botPromptsError } = useBotPrompts(botId)
  const { data: myPrompts, isLoading: myPromptsLoading } = useMyPrompts()
  const attachPromptMutation = useAttachPrompt()
  const detachPromptMutation = useDetachPrompt()
  const updatePromptMutation = useUpdateBotPrompt()

  // Filter prompts for trading only (exclude risk management)
  const tradingPrompts = myPrompts?.filter(prompt => 
    prompt.category === 'TRADING'
  ) || []

  // Get attached trading prompts
  const attachedPrompts = botPrompts?.filter(bp => 
    bp.is_active && bp.prompt_template?.category === 'TRADING'
  ) || []

  // Get suggested trading prompts (not yet attached)
  const attachedPromptIds = attachedPrompts.map(ap => ap.prompt_template?.id).filter(Boolean)
  const suggestedPrompts = tradingPrompts.filter(p => !attachedPromptIds.includes(p.id))

  // All available prompts (trading prompts only)
  const allPrompts = tradingPrompts
  
  // Debug logs
  console.log('🔍 BotPromptsTab Debug:', {
    botId,
    botPrompts: botPrompts?.length || 0,
    myPrompts: myPrompts?.length || 0,
    tradingPrompts: tradingPrompts.length,
    attachedPrompts: attachedPrompts.length,
    suggestedPrompts: suggestedPrompts.length,
    allPrompts: allPrompts.length
  })

  const handleAttachPrompt = async (promptId: number) => {
    try {
      await attachPromptMutation.mutateAsync({
        botId,
        promptId,
        data: {
          priority,
          custom_override: customOverride || undefined
        }
      })
      toast.success('Strategy attached successfully!')
      setShowAttachModal(false)
      setSelectedPrompt(null)
    } catch (error) {
      console.error('Error attaching prompt:', error)
      toast.error('Failed to attach strategy')
    }
  }

  const handleDetachPrompt = async (botPromptId: number) => {
    try {
      // Find the prompt template ID from the bot prompt
      const botPrompt = attachedPrompts.find(bp => bp.id === botPromptId)
      if (!botPrompt) {
        toast.error('Strategy not found')
        return
      }
      
      await detachPromptMutation.mutateAsync({
        botId,
        promptId: botPrompt.prompt_template.id
      })
      toast.success('Strategy detached successfully!')
    } catch (error) {
      console.error('Error detaching prompt:', error)
      toast.error('Failed to detach strategy')
    }
  }

  const handleUpdatePrompt = async (botPromptId: number, updateData: any) => {
    try {
      // Find the prompt template ID from the bot prompt
      const botPrompt = attachedPrompts.find(bp => bp.id === botPromptId)
      if (!botPrompt) {
        toast.error('Strategy not found')
        return
      }
      
      await updatePromptMutation.mutateAsync({
        botId,
        promptId: botPrompt.prompt_template.id,
        data: updateData
      })
      toast.success('Strategy updated successfully!')
    } catch (error) {
      console.error('Error updating prompt:', error)
      toast.error('Failed to update strategy')
    }
  }

  const getPriorityColor = (priority: number) => {
    switch (priority) {
      case 3: return 'bg-red-500/20 text-red-400'
      case 2: return 'bg-yellow-500/20 text-yellow-400'
      case 1: return 'bg-blue-500/20 text-blue-400'
      default: return 'bg-gray-500/20 text-gray-400'
    }
  }

  const getPriorityLabel = (priority: number) => {
    switch (priority) {
      case 3: return 'High'
      case 2: return 'Medium'
      case 1: return 'Low'
      default: return 'Default'
    }
  }

  // Loading state
  if (botPromptsLoading || myPromptsLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <span className="ml-2 text-gray-400">Loading strategies...</span>
      </div>
    )
  }

  // Error state
  if (botPromptsError) {
    return (
      <div className="bg-red-900/30 border border-red-700 text-red-300 p-4 rounded-md">
        <div className="flex items-center">
          <ExclamationTriangleIcon className="h-5 w-5 mr-2" />
          <span>Error loading strategies: {botPromptsError.message}</span>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-8">
      {/* Attached Strategies */}
      <div>
        <h3 className="text-xl font-semibold text-gray-200 mb-4 flex items-center">
          Attached Strategies ({attachedPrompts.length})
          <span className="ml-2 text-sm text-gray-500 font-normal">
            (Strategies currently linked to this bot)
          </span>
        </h3>
        {attachedPrompts.length > 0 ? (
          <ul className="space-y-4">
            {attachedPrompts.map((bp) => (
              <li key={bp.id} className="bg-gray-800 p-4 rounded-lg shadow-md border border-gray-700">
                <div className="flex justify-between items-center">
                  <div>
                    <div className="flex items-center space-x-2">
                      <Link 
                        href={`/creator/prompts/${bp.prompt_template?.id}`}
                        className="text-lg font-medium text-white hover:text-blue-400 transition-colors cursor-pointer"
                      >
                        {bp.prompt_template?.name || 'Unknown Strategy'}
                      </Link>
                      <Link 
                        href={`/creator/prompts/${bp.prompt_template?.id}`}
                        className="p-1 rounded text-gray-400 hover:text-blue-400 hover:bg-blue-500/20 transition-colors"
                        title="View Strategy Details"
                      >
                        <EyeIcon className="h-4 w-4" />
                      </Link>
                    </div>
                    <p className="text-sm text-gray-400">{bp.prompt_template?.description || 'No description available'}</p>
                    <div className="mt-2 flex items-center space-x-3 text-sm">
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${getPriorityColor(bp.priority)}`}>
                        Priority: {getPriorityLabel(bp.priority)}
                      </span>
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        bp.is_active ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                      }`}>
                        {bp.is_active ? 'Active' : 'Inactive'}
                      </span>
                      {bp.custom_override && (
                        <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-500/20 text-blue-400">
                          Customized
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleUpdatePrompt(bp.id, {})}
                      className="p-2 rounded-full text-blue-400 hover:bg-blue-500/20 hover:text-blue-300 transition-colors"
                      title="Edit Strategy Settings"
                      disabled={updatePromptMutation.isPending}
                    >
                      <PencilIcon className="h-5 w-5" />
                    </button>
                    <button
                      onClick={() => handleDetachPrompt(bp.id)}
                      className="p-2 rounded-full text-red-400 hover:bg-red-500/20 hover:text-red-300 transition-colors"
                      title="Detach Strategy"
                      disabled={detachPromptMutation.isPending}
                    >
                      <TrashIcon className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-gray-400">No strategies attached to this bot yet.</p>
        )}
      </div>

      {/* Suggested Strategies */}
      <div>
        <h3 className="text-xl font-semibold text-gray-200 mb-4 flex items-center">
          <LightBulbIcon className="h-6 w-6 text-yellow-400 mr-2" />
          Suggested Strategies ({suggestedPrompts.length})
          <span className="ml-2 text-sm text-gray-500 font-normal">
            (Based on bot type and category)
          </span>
        </h3>
        {suggestedPrompts.length > 0 ? (
          <ul className="space-y-3">
            {suggestedPrompts.map((prompt) => (
              <li key={prompt.id} className="bg-gray-800 p-3 rounded-lg shadow-md border border-gray-700 flex justify-between items-center">
                <div>
                  <div className="flex items-center space-x-2">
                    <Link 
                      href={`/creator/prompts/${prompt.id}`}
                      className="text-lg font-medium text-white hover:text-blue-400 transition-colors cursor-pointer"
                    >
                      {prompt.name}
                    </Link>
                    <Link 
                      href={`/creator/prompts/${prompt.id}`}
                      className="p-1 rounded text-gray-400 hover:text-blue-400 hover:bg-blue-500/20 transition-colors"
                      title="View Prompt Details"
                    >
                      <EyeIcon className="h-4 w-4" />
                    </Link>
                  </div>
                  <p className="text-sm text-gray-400">{prompt.description}</p>
                </div>
                <button
                  onClick={() => {
                    setSelectedPrompt(prompt)
                    setShowAttachModal(true)
                  }}
                  className="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                >
                  <PlusIcon className="-ml-0.5 mr-2 h-4 w-4" />
                  Attach
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-gray-400">No suggestions at the moment.</p>
        )}
      </div>

      {/* All Available Strategies */}
      <div>
        <h3 className="text-xl font-semibold text-gray-200 mb-4 flex items-center">
          All Available Strategies ({allPrompts.length})
          <span className="ml-2 text-sm text-gray-500 font-normal">
            (Manually attach any strategy)
          </span>
        </h3>
        {allPrompts.length > 0 ? (
          <ul className="space-y-3">
            {allPrompts.map((prompt) => (
              <li key={prompt.id} className="bg-gray-800 p-3 rounded-lg shadow-md border border-gray-700 flex justify-between items-center">
                <div>
                  <div className="flex items-center space-x-2">
                    <Link 
                      href={`/creator/prompts/${prompt.id}`}
                      className="text-lg font-medium text-white hover:text-blue-400 transition-colors cursor-pointer"
                    >
                      {prompt.name || 'Unknown Strategy'}
                    </Link>
                    <Link 
                      href={`/creator/prompts/${prompt.id}`}
                      className="p-1 rounded text-gray-400 hover:text-blue-400 hover:bg-blue-500/20 transition-colors"
                      title="View Prompt Details"
                    >
                      <EyeIcon className="h-4 w-4" />
                    </Link>
                  </div>
                  <p className="text-sm text-gray-400">{prompt.description || 'No description available'}</p>
                  <span className="text-xs text-gray-500">Category: {prompt.category || 'Unknown'}</span>
                </div>
                <button
                  onClick={() => {
                    setSelectedPrompt(prompt)
                    setShowAttachModal(true)
                  }}
                  className="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
                >
                  <PlusIcon className="-ml-0.5 mr-2 h-4 w-4" />
                  Attach
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <div className="bg-gradient-to-r from-yellow-900/20 to-orange-900/20 border border-yellow-700/50 rounded-lg p-6">
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0">
                <SparklesIcon className="h-12 w-12 text-yellow-400" />
              </div>
              <div className="flex-1">
                <h4 className="text-lg font-semibold text-yellow-300 mb-2">
                  No Strategies Found
                </h4>
                <p className="text-gray-300 mb-4">
                  You haven't created any strategy templates yet. Strategy templates help guide your bot's AI analysis and decision-making process.
                </p>
                
                <div className="bg-gray-800/50 rounded-lg p-4 mb-4">
                  <h5 className="text-white font-medium mb-3">How to create strategies:</h5>
                  <ol className="space-y-2 text-sm text-gray-300">
                    <li className="flex items-start">
                      <span className="flex-shrink-0 w-6 h-6 rounded-full bg-purple-500/20 text-purple-400 flex items-center justify-center mr-2 text-xs font-bold">1</span>
                      <span>Visit the Strategy Management page</span>
                    </li>
                    <li className="flex items-start">
                      <span className="flex-shrink-0 w-6 h-6 rounded-full bg-purple-500/20 text-purple-400 flex items-center justify-center mr-2 text-xs font-bold">2</span>
                      <span>Click "Create New Strategy Template"</span>
                    </li>
                    <li className="flex items-start">
                      <span className="flex-shrink-0 w-6 h-6 rounded-full bg-purple-500/20 text-purple-400 flex items-center justify-center mr-2 text-xs font-bold">3</span>
                      <span>Configure your strategy with trading strategies</span>
                    </li>
                    <li className="flex items-start">
                      <span className="flex-shrink-0 w-6 h-6 rounded-full bg-purple-500/20 text-purple-400 flex items-center justify-center mr-2 text-xs font-bold">4</span>
                      <span>Return here to attach it to your bot</span>
                    </li>
                  </ol>
                </div>
                
                <Link 
                  href="/creator/prompts"
                  className="inline-flex items-center px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-md shadow-sm transition-colors"
                >
                  <SparklesIcon className="h-5 w-5 mr-2" />
                  Go to Strategy Management
                </Link>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Attach Strategy Modal */}
      {showAttachModal && selectedPrompt && (
        <div className="fixed inset-0 bg-gray-900 bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-gray-800 p-6 rounded-lg shadow-xl max-w-md w-full border border-gray-700">
            <h3 className="text-xl font-semibold text-white mb-4">Attach Strategy: {selectedPrompt.name}</h3>
            <div className="space-y-4">
              <div>
                <label htmlFor="priority" className="block text-sm font-medium text-gray-400">Priority</label>
                <select
                  id="priority"
                  value={priority}
                  onChange={(e) => setPriority(parseInt(e.target.value))}
                  className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-600 focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm rounded-md bg-gray-700 text-white"
                >
                  <option value={0}>Default</option>
                  <option value={1}>Low</option>
                  <option value={2}>Medium</option>
                  <option value={3}>High</option>
                </select>
              </div>
              <div>
                <label htmlFor="custom-override" className="block text-sm font-medium text-gray-400">Custom Override (Optional)</label>
                <textarea
                  id="custom-override"
                  value={customOverride}
                  onChange={(e) => setCustomOverride(e.target.value)}
                  rows={4}
                  className="mt-1 block w-full border border-gray-600 rounded-md shadow-sm p-2 bg-gray-700 text-white focus:ring-purple-500 focus:border-purple-500 sm:text-sm"
                  placeholder="Enter bot-specific strategy modifications (e.g., 'Always use a bullish bias'). This will override the default strategy content for this bot."
                />
              </div>
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => setShowAttachModal(false)}
                  className="py-2 px-4 border border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-300 bg-gray-700 hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleAttachPrompt(selectedPrompt.id)}
                  className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
                >
                  Attach Strategy
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}