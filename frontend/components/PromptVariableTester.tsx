'use client'

import { useState } from 'react'
import { injectVariables, getDefaultVariables, validateVariables, AVAILABLE_VARIABLES } from '@/utils/promptVariables'

interface PromptVariableTesterProps {
  promptTemplate: string
  onClose: () => void
}

export default function PromptVariableTester({ promptTemplate, onClose }: PromptVariableTesterProps) {
  const [variables, setVariables] = useState(getDefaultVariables())
  const [injectedPrompt, setInjectedPrompt] = useState('')
  const [validation, setValidation] = useState<{ valid: boolean; errors: string[] }>({ valid: true, errors: [] })

  const handleVariableChange = (key: string, value: string) => {
    const newVariables = { ...variables, [key]: value }
    setVariables(newVariables)
    
    // Auto-inject variables
    const injected = injectVariables(promptTemplate, newVariables)
    setInjectedPrompt(injected)
    
    // Validate
    const validationResult = validateVariables(promptTemplate)
    setValidation(validationResult)
  }

  const handleTestInjection = () => {
    const injected = injectVariables(promptTemplate, variables)
    setInjectedPrompt(injected)
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-white">Test Variable Injection</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white"
          >
            ✕
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Variables Panel */}
          <div className="space-y-4">
            <h4 className="text-md font-medium text-gray-300">Variables</h4>
            <div className="space-y-3">
              {Object.entries(AVAILABLE_VARIABLES).map(([key, variable]) => (
                <div key={key} className="bg-gray-700 p-3 rounded">
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    {key}
                  </label>
                  <p className="text-xs text-gray-400 mb-2">{variable.description}</p>
                  <input
                    type={variable.type === 'number' ? 'number' : 'text'}
                    value={variables[key] || ''}
                    onChange={(e) => handleVariableChange(key, e.target.value)}
                    className="w-full px-3 py-2 bg-gray-600 text-white rounded text-sm"
                    placeholder={`Enter ${variable.type} value`}
                  />
                </div>
              ))}
            </div>
            
            {!validation.valid && (
              <div className="bg-red-900 border border-red-700 p-3 rounded">
                <h5 className="text-red-300 font-medium mb-2">Validation Errors:</h5>
                <ul className="text-red-200 text-sm space-y-1">
                  {validation.errors.map((error, index) => (
                    <li key={index}>• {error}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Results Panel */}
          <div className="space-y-4">
            <h4 className="text-md font-medium text-gray-300">Results</h4>
            
            {/* Original Template */}
            <div>
              <h5 className="text-sm font-medium text-gray-400 mb-2">Original Template:</h5>
              <div className="bg-gray-900 p-3 rounded text-sm text-gray-300 whitespace-pre-wrap max-h-32 overflow-y-auto">
                {promptTemplate}
              </div>
            </div>

            {/* Injected Template */}
            <div>
              <h5 className="text-sm font-medium text-gray-400 mb-2">Injected Template:</h5>
              <div className="bg-gray-900 p-3 rounded text-sm text-gray-300 whitespace-pre-wrap max-h-32 overflow-y-auto">
                {injectedPrompt || 'Click "Test Injection" to see results'}
              </div>
            </div>

            <button
              onClick={handleTestInjection}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded transition-colors"
            >
              Test Injection
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
