'use client'

import { useState } from 'react'
import { EyeIcon, PencilIcon, TrashIcon, PlusIcon } from '@heroicons/react/24/outline'
import { useBotPrompts, useAttachPrompt, useDetachPrompt, useUpdateBotPrompt } from '@/hooks/useBotPrompts'
import { useMyPrompts } from '@/hooks/usePrompts'
import Link from 'next/link'
import toast from 'react-hot-toast'

interface RiskManagementTabProps {
  botId: number
}

export default function RiskManagementTab({ botId }: RiskManagementTabProps) {
  const [showAttachModal, setShowAttachModal] = useState(false)
  const [selectedPrompt, setSelectedPrompt] = useState<any>(null)
  const [priority, setPriority] = useState(0)
  const [customOverride, setCustomOverride] = useState('')

  // Use real data hooks
  const { data: botPrompts, isLoading: botPromptsLoading, error: botPromptsError } = useBotPrompts(botId)
  const { data: allPrompts, isLoading: allPromptsLoading } = useMyPrompts()
  const attachPromptMutation = useAttachPrompt()
  const detachPromptMutation = useDetachPrompt()
  const updatePromptMutation = useUpdateBotPrompt()

  // Filter prompts for risk management
  const riskManagementPrompts = allPrompts?.filter(prompt => 
    prompt.category === 'RISK_MANAGEMENT'
  ) || []

  // Get attached risk management prompts
  const attachedRiskPrompts = botPrompts?.filter(bp => 
    bp.is_active && bp.prompt_template?.category === 'RISK_MANAGEMENT'
  ) || []

  // Get suggested risk management prompts (not yet attached)
  const attachedRiskPromptIds = attachedRiskPrompts.map(ap => ap.prompt_template?.id).filter(Boolean)
  const suggestedRiskPrompts = riskManagementPrompts.filter(p => 
    !attachedRiskPromptIds.includes(p.id)
  )

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
      toast.success('Risk management prompt attached successfully!')
      setShowAttachModal(false)
      setSelectedPrompt(null)
    } catch (error) {
      console.error('Error attaching risk management prompt:', error)
      toast.error('Failed to attach risk management prompt')
    }
  }

  const handleDetachPrompt = async (botPromptId: number) => {
    try {
      const botPrompt = attachedRiskPrompts.find(bp => bp.id === botPromptId)
      if (!botPrompt) {
        toast.error('Risk management prompt not found')
        return
      }

      await detachPromptMutation.mutateAsync({
        botId,
        promptId: botPrompt.prompt_template.id
      })
      toast.success('Risk management prompt detached successfully!')
    } catch (error) {
      console.error('Error detaching risk management prompt:', error)
      toast.error('Failed to detach risk management prompt')
    }
  }

  const handleUpdatePrompt = async (botPromptId: number, updateData: any) => {
    try {
      const botPrompt = attachedRiskPrompts.find(bp => bp.id === botPromptId)
      if (!botPrompt) {
        toast.error('Risk management prompt not found')
        return
      }

      await updatePromptMutation.mutateAsync({
        botId,
        promptId: botPrompt.prompt_template.id,
        data: updateData
      })
      toast.success('Risk management prompt updated successfully!')
    } catch (error) {
      console.error('Error updating risk management prompt:', error)
      toast.error('Failed to update risk management prompt')
    }
  }

  const openAttachModal = (prompt: any) => {
    setSelectedPrompt(prompt)
    setShowAttachModal(true)
  }

  // Loading state
  if (botPromptsLoading || allPromptsLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <span className="ml-2 text-gray-400">Loading risk management prompts...</span>
      </div>
    )
  }

  // Error state
  if (botPromptsError) {
    return (
      <div className="bg-red-900/30 border border-red-700 text-red-300 p-4 rounded-md">
        <div className="flex items-center">
          <span className="text-red-400 mr-2">⚠️</span>
          <span>Error loading risk management prompts: {botPromptsError.message}</span>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Attached Risk Management Prompts */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-2">
          Attached Risk Management Prompts ({attachedRiskPrompts.length})
        </h3>
        <p className="text-sm text-gray-400 mb-4">
          (Risk management prompts currently linked to this bot)
        </p>
        
        {attachedRiskPrompts.length === 0 ? (
          <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-6 text-center">
            <div className="text-gray-400 mb-2">🛡️</div>
            <p className="text-gray-400">No risk management prompts attached</p>
            <p className="text-sm text-gray-500">Attach prompts below to get started</p>
          </div>
        ) : (
          <div className="space-y-3">
            {attachedRiskPrompts.map((bp) => (
              <div key={bp.id} className="bg-gray-800/50 border border-gray-700 rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <Link href={`/creator/prompts/${bp.prompt_template.id}`}>
                        <h4 className="text-lg font-medium text-white hover:text-blue-400 transition-colors cursor-pointer">
                          {bp.prompt_template?.name || 'Unknown Risk Management Prompt'}
                        </h4>
                      </Link>
                      <Link href={`/creator/prompts/${bp.prompt_template.id}`}>
                        <EyeIcon className="h-4 w-4 text-gray-400 hover:text-blue-400 transition-colors cursor-pointer" />
                      </Link>
                    </div>
                    <p className="text-sm text-gray-400 mb-2">
                      {bp.prompt_template?.description || 'No description available'}
                    </p>
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 rounded text-xs ${
                        bp.priority >= 8 ? 'bg-red-900/30 text-red-300' :
                        bp.priority >= 5 ? 'bg-yellow-900/30 text-yellow-300' :
                        'bg-green-900/30 text-green-300'
                      }`}>
                        Priority: {bp.priority >= 8 ? 'High' : bp.priority >= 5 ? 'Medium' : 'Low'}
                      </span>
                      <span className={`px-2 py-1 rounded text-xs ${
                        bp.is_active ? 'bg-green-900/30 text-green-300' : 'bg-gray-900/30 text-gray-300'
                      }`}>
                        {bp.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2 ml-4">
                    <button
                      onClick={() => handleDetachPrompt(bp.id)}
                      className="p-2 text-red-400 hover:text-red-300 hover:bg-red-900/20 rounded-md transition-colors"
                      title="Detach Risk Management Prompt"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Suggested Risk Management Prompts */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-2">
          Suggested Risk Management Prompts ({suggestedRiskPrompts.length})
        </h3>
        <p className="text-sm text-gray-400 mb-4">
          (Based on bot type and risk management needs)
        </p>
        
        {suggestedRiskPrompts.length === 0 ? (
          <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-6 text-center">
            <div className="text-gray-400 mb-2">💡</div>
            <p className="text-gray-400">No suggested risk management prompts available</p>
            <p className="text-sm text-gray-500">Create risk management prompts in Prompt Management</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {suggestedRiskPrompts.map((prompt) => (
              <div key={prompt.id} className="bg-gray-800/50 border border-gray-700 rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <Link href={`/creator/prompts/${prompt.id}`}>
                        <h4 className="text-lg font-medium text-white hover:text-blue-400 transition-colors cursor-pointer">
                          {prompt.name || 'Unknown Risk Management Prompt'}
                        </h4>
                      </Link>
                      <Link href={`/creator/prompts/${prompt.id}`}>
                        <EyeIcon className="h-4 w-4 text-gray-400 hover:text-blue-400 transition-colors cursor-pointer" />
                      </Link>
                    </div>
                    <p className="text-sm text-gray-400 mb-2">
                      {prompt.description || 'No description available'}
                    </p>
                    <span className="text-xs text-gray-500">Category: {prompt.category || 'RISK_MANAGEMENT'}</span>
                  </div>
                  <button
                    onClick={() => openAttachModal(prompt)}
                    className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm transition-colors ml-4"
                  >
                    + Attach
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* All Available Risk Management Prompts */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-2">
          All Available Risk Management Prompts ({riskManagementPrompts.length})
        </h3>
        <p className="text-sm text-gray-400 mb-4">
          (Manually attach any risk management prompt)
        </p>
        
        {riskManagementPrompts.length === 0 ? (
          <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-6 text-center">
            <div className="text-gray-400 mb-2">🛡️</div>
            <p className="text-gray-400">No risk management prompts available</p>
            <p className="text-sm text-gray-500">Create risk management prompts in Prompt Management</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {riskManagementPrompts.map((prompt) => (
              <div key={prompt.id} className="bg-gray-800/50 border border-gray-700 rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <Link href={`/creator/prompts/${prompt.id}`}>
                        <h4 className="text-lg font-medium text-white hover:text-blue-400 transition-colors cursor-pointer">
                          {prompt.name || 'Unknown Risk Management Prompt'}
                        </h4>
                      </Link>
                      <Link href={`/creator/prompts/${prompt.id}`}>
                        <EyeIcon className="h-4 w-4 text-gray-400 hover:text-blue-400 transition-colors cursor-pointer" />
                      </Link>
                    </div>
                    <p className="text-sm text-gray-400 mb-2">
                      {prompt.description || 'No description available'}
                    </p>
                    <span className="text-xs text-gray-500">Category: {prompt.category || 'RISK_MANAGEMENT'}</span>
                  </div>
                  <button
                    onClick={() => openAttachModal(prompt)}
                    className="bg-purple-600 hover:bg-purple-700 text-white px-3 py-1 rounded text-sm transition-colors ml-4"
                  >
                    + Attach
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Attach Modal */}
      {showAttachModal && selectedPrompt && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4 border border-gray-700">
            <div className="p-6">
              <h3 className="text-lg font-semibold text-white mb-4">
                Attach Risk Management Prompt
              </h3>
              
              <div className="mb-4">
                <h4 className="text-white font-medium mb-2">{selectedPrompt.name}</h4>
                <p className="text-gray-400 text-sm">{selectedPrompt.description}</p>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Priority Level
                  </label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(parseInt(e.target.value))}
                    className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value={0}>Low (0)</option>
                    <option value={5}>Medium (5)</option>
                    <option value={8}>High (8)</option>
                    <option value={10}>Critical (10)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Custom Override (Optional)
                  </label>
                  <textarea
                    value={customOverride}
                    onChange={(e) => setCustomOverride(e.target.value)}
                    placeholder="Bot-specific risk management customization..."
                    className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:ring-blue-500 focus:border-blue-500 h-20 resize-none"
                  />
                </div>
              </div>

              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => setShowAttachModal(false)}
                  className="px-4 py-2 border border-gray-600 rounded-md text-white hover:bg-gray-700 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleAttachPrompt(selectedPrompt.id)}
                  disabled={attachPromptMutation.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
                >
                  {attachPromptMutation.isPending ? 'Attaching...' : 'Attach Risk Management Prompt'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
