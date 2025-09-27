'use client'

import { useState } from 'react'
import { 
  PlusIcon, 
  TrashIcon, 
  PencilIcon, 
  SparklesIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  LightBulbIcon
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface BotPromptsTabProps {
  botId: number
}

export default function BotPromptsTab({ botId }: BotPromptsTabProps) {
  const [showAttachModal, setShowAttachModal] = useState(false)
  const [selectedPrompt, setSelectedPrompt] = useState<any>(null)
  const [priority, setPriority] = useState(0)
  const [customOverride, setCustomOverride] = useState('')

  // Mock data for testing
  const attachedPrompts = [
    {
      id: 1,
      prompt_template: {
        name: "Advanced Trading Analysis",
        description: "Comprehensive market analysis with technical indicators",
        category: "TRADING"
      },
      priority: 2,
      is_active: true,
      custom_override: null
    }
  ]

  const suggestedPrompts = [
    {
      id: 2,
      name: "Risk Management & Capital Allocation",
      description: "AI-driven risk assessment and position sizing",
      category: "RISK_MANAGEMENT"
    },
    {
      id: 3,
      name: "Market Analysis Engine",
      description: "Real-time market sentiment and trend analysis",
      category: "ANALYSIS"
    }
  ]

  const allPrompts = [
    {
      id: 4,
      name: "News Sentiment Analysis",
      description: "Analyze market sentiment from news sources",
      category: "ANALYSIS"
    },
    {
      id: 5,
      name: "Comprehensive Market Analysis",
      description: "Complete market overview with multiple indicators",
      category: "TRADING"
    }
  ]

  const handleAttachPrompt = (promptId: number) => {
    toast.success(`Prompt ${promptId} attached successfully!`)
    setShowAttachModal(false)
    setSelectedPrompt(null)
  }

  const handleDetachPrompt = (promptId: number) => {
    toast.success(`Prompt ${promptId} detached successfully!`)
  }

  const handleUpdatePrompt = (promptId: number) => {
    toast.success(`Prompt ${promptId} updated successfully!`)
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

  return (
    <div className="p-6 space-y-8">
      {/* Attached Prompts */}
      <div>
        <h3 className="text-xl font-semibold text-gray-200 mb-4 flex items-center">
          Attached Prompts ({attachedPrompts.length})
          <span className="ml-2 text-sm text-gray-500 font-normal">
            (Prompts currently linked to this bot)
          </span>
        </h3>
        {attachedPrompts.length > 0 ? (
          <ul className="space-y-4">
            {attachedPrompts.map((bp) => (
              <li key={bp.id} className="bg-gray-800 p-4 rounded-lg shadow-md border border-gray-700">
                <div className="flex justify-between items-center">
                  <div>
                    <h4 className="text-lg font-medium text-white">{bp.prompt_template.name}</h4>
                    <p className="text-sm text-gray-400">{bp.prompt_template.description}</p>
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
                      onClick={() => handleUpdatePrompt(bp.id)}
                      className="p-2 rounded-full text-blue-400 hover:bg-blue-500/20 hover:text-blue-300 transition-colors"
                      title="Edit Prompt Settings"
                    >
                      <PencilIcon className="h-5 w-5" />
                    </button>
                    <button
                      onClick={() => handleDetachPrompt(bp.id)}
                      className="p-2 rounded-full text-red-400 hover:bg-red-500/20 hover:text-red-300 transition-colors"
                      title="Detach Prompt"
                    >
                      <TrashIcon className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-gray-400">No prompts attached to this bot yet.</p>
        )}
      </div>

      {/* Suggested Prompts */}
      <div>
        <h3 className="text-xl font-semibold text-gray-200 mb-4 flex items-center">
          <LightBulbIcon className="h-6 w-6 text-yellow-400 mr-2" />
          Suggested Prompts ({suggestedPrompts.length})
          <span className="ml-2 text-sm text-gray-500 font-normal">
            (Based on bot type and category)
          </span>
        </h3>
        {suggestedPrompts.length > 0 ? (
          <ul className="space-y-3">
            {suggestedPrompts.map((prompt) => (
              <li key={prompt.id} className="bg-gray-800 p-3 rounded-lg shadow-md border border-gray-700 flex justify-between items-center">
                <div>
                  <h4 className="text-lg font-medium text-white">{prompt.name}</h4>
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

      {/* All Available Prompts */}
      <div>
        <h3 className="text-xl font-semibold text-gray-200 mb-4 flex items-center">
          All Available Prompts ({allPrompts.length})
          <span className="ml-2 text-sm text-gray-500 font-normal">
            (Manually attach any prompt)
          </span>
        </h3>
        {allPrompts.length > 0 ? (
          <ul className="space-y-3">
            {allPrompts.map((prompt) => (
              <li key={prompt.id} className="bg-gray-800 p-3 rounded-lg shadow-md border border-gray-700 flex justify-between items-center">
                <div>
                  <h4 className="text-lg font-medium text-white">{prompt.name}</h4>
                  <p className="text-sm text-gray-400">{prompt.description}</p>
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
          <p className="text-gray-400">No more prompts to attach.</p>
        )}
      </div>

      {/* Attach Prompt Modal */}
      {showAttachModal && selectedPrompt && (
        <div className="fixed inset-0 bg-gray-900 bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-gray-800 p-6 rounded-lg shadow-xl max-w-md w-full border border-gray-700">
            <h3 className="text-xl font-semibold text-white mb-4">Attach Prompt: {selectedPrompt.name}</h3>
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
                  placeholder="Enter bot-specific prompt modifications (e.g., 'Always use a bullish bias'). This will override the default prompt content for this bot."
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
                  Attach Prompt
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}