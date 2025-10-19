'use client'

import React, { useState, useEffect } from 'react'
import { useCredentials, useDefaultCredentials } from '@/hooks/useCredentials'
import { Bot } from '@/lib/types'
import config from '@/lib/config'

interface PreTrialValidationModalProps {
  isOpen: boolean
  onClose: () => void
  onProceed: () => void
  bot: Bot
  networkType: 'TESTNET' | 'MAINNET'
}

interface ValidationResult {
  hasExchangeCredentials: boolean
  hasPrompt: boolean
  missingCredentials: boolean
  missingPrompt: boolean
  exchangeType: string
  credentialType: string
  networkType: string
  promptCount: number
}
// Note: LLM Provider validation removed - platform now manages LLM providers centrally

export default function PreTrialValidationModal({
  isOpen,
  onClose,
  onProceed,
  bot,
  networkType
}: PreTrialValidationModalProps) {
  const [validation, setValidation] = useState<ValidationResult | null>(null)
  const [isValidating, setIsValidating] = useState(false)

  // Fetch exchange credentials
  const { data: credentials, isLoading: isLoadingCredentials } = useCredentials()

  // Determine exchange and credential type from bot
  const exchangeType = bot.exchange_type || 'BINANCE'
  const credentialType = bot.bot_type === 'SPOT' ? 'SPOT' : 'FUTURES'

  // Check for default credentials for this specific exchange/type/network
  const { data: defaultCredentials } = useDefaultCredentials(
    exchangeType,
    credentialType,
    networkType,
    !isLoadingCredentials
  )

  useEffect(() => {
    if (isOpen && !isLoadingCredentials) {
      validateConfiguration()
    }
  }, [isOpen, isLoadingCredentials, credentials, bot, networkType])

  const validateConfiguration = async () => {
    setIsValidating(true)

    try {
      // Check if bot is passive signals bot (skip exchange credentials check)
      const isPassiveBot = (bot as any).bot_mode === 'PASSIVE'
      
      // Check exchange credentials (skip for passive bots)
      const hasMatchingCredentials = isPassiveBot ? true : (
        credentials?.some(cred => 
          cred.exchange_type === exchangeType &&
          cred.credential_type === credentialType &&
          cred.network_type === networkType &&
          cred.is_active
        ) || !!defaultCredentials
      )

      // Check prompts
      let hasPrompts = false
      let promptCount = 0
      
      const token = localStorage.getItem('access_token')
      if (token) {
        try {
          const response = await fetch(`${config.studioBaseUrl}/bot-prompts/bots/${bot.id}/prompts`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          })

          if (response.ok) {
            const prompts = await response.json()
            hasPrompts = Array.isArray(prompts) && prompts.length > 0
            promptCount = hasPrompts ? prompts.length : 0
          }
        } catch (error) {
          console.error('Error fetching prompts:', error)
        }
      }

      const validationResult: ValidationResult = {
        hasExchangeCredentials: hasMatchingCredentials,
        hasPrompt: hasPrompts,
        missingCredentials: !hasMatchingCredentials && !isPassiveBot, // Only show as missing if not passive
        missingPrompt: !hasPrompts,
        exchangeType,
        credentialType,
        networkType,
        promptCount
      }

      setValidation(validationResult)
    } catch (error) {
      console.error('Error validating configuration:', error)
    } finally {
      setIsValidating(false)
    }
  }

  const handleProceed = () => {
    if (validation?.hasExchangeCredentials && validation?.hasPrompt) {
      onProceed()
    }
  }

  const openCredentialsPage = () => {
    window.open('/creator/credentials', '_blank')
  }

  const openPromptsTab = () => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('bot-detail-tab', 'prompts')
      window.location.reload()
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 rounded-xl border border-gray-700 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-gray-700">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-white flex items-center">
              <span className="mr-3">🔍</span>
              Pre-Trial Configuration Check
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <p className="text-gray-400 mt-2">
            Before starting your free trial, we need to verify your configuration
          </p>
        </div>

        {/* Content */}
        <div className="p-6">
          {isValidating || isLoadingCredentials ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
              <span className="ml-3 text-gray-300">Validating configuration...</span>
            </div>
          ) : validation ? (
            <div className="space-y-6">
              {/* Bot Info */}
              <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                <h3 className="text-lg font-semibold text-white mb-2">Bot Configuration</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-400">Bot:</span>
                    <span className="ml-2 text-white">{bot.name}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Exchange:</span>
                    <span className="ml-2 text-white">{exchangeType}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Type:</span>
                    <span className="ml-2 text-white">{credentialType}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Network:</span>
                    <span className="ml-2 text-white">{networkType}</span>
                  </div>
                </div>
              </div>

              {/* LLM Provider - Platform Managed */}
              <div className="rounded-lg p-4 border bg-green-900/30 border-green-500/30">
                <div className="flex items-center">
                  <span className="text-2xl mr-3">✅</span>
                  <div>
                    <h4 className="text-lg font-semibold text-white">
                      LLM Provider Configuration
                    </h4>
                    <p className="text-sm text-gray-300">
                      Platform-managed LLM providers are automatically configured
                    </p>
                  </div>
                </div>
              </div>

              {/* Exchange Credentials Check */}
              {(bot as any).bot_mode !== 'PASSIVE' && (
                <div className={`rounded-lg p-4 border ${
                  validation.hasExchangeCredentials 
                    ? 'bg-green-900/30 border-green-500/30' 
                    : 'bg-red-900/30 border-red-500/30'
                }`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <span className="text-2xl mr-3">
                        {validation.hasExchangeCredentials ? '✅' : '❌'}
                      </span>
                      <div>
                        <h4 className="text-lg font-semibold text-white">
                          Exchange API Credentials
                        </h4>
                        <p className="text-sm text-gray-300">
                          {validation.hasExchangeCredentials 
                            ? `${exchangeType} ${credentialType} credentials configured for ${networkType}`
                            : `No ${exchangeType} ${credentialType} credentials found for ${networkType}`
                          }
                        </p>
                      </div>
                    </div>
                    {validation.missingCredentials && (
                      <button
                        onClick={openCredentialsPage}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-sm"
                      >
                        Configure API
                      </button>
                    )}
                  </div>
                  {validation.missingCredentials && (
                    <div className="mt-3 p-3 bg-red-900/20 border border-red-500/20 rounded text-sm text-red-300">
                      <p className="font-medium mb-1">⚠️ Exchange API Credentials Required</p>
                      <p>This bot needs {exchangeType} {credentialType} API credentials for {networkType} to execute trades.</p>
                    </div>
                  )}
                </div>
              )}
              
              {/* Passive Bot Info */}
              {(bot as any).bot_mode === 'PASSIVE' && (
                <div className="rounded-lg p-4 border bg-blue-900/30 border-blue-500/30">
                  <div className="flex items-center">
                    <span className="text-2xl mr-3">ℹ️</span>
                    <div>
                      <h4 className="text-lg font-semibold text-white">
                        Signals Bot (Passive Mode)
                      </h4>
                      <p className="text-sm text-gray-300">
                        This is a passive signals bot. It will send trading signals without executing trades, so exchange API credentials are not required.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Prompt Check */}
              <div className={`rounded-lg p-4 border ${
                validation.hasPrompt 
                  ? 'bg-green-900/30 border-green-500/30' 
                  : 'bg-red-900/30 border-red-500/30'
              }`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <span className="text-2xl mr-3">
                      {validation.hasPrompt ? '✅' : '❌'}
                    </span>
                    <div>
                      <h4 className="text-lg font-semibold text-white">
                        Bot Prompt Configuration
                      </h4>
                      <p className="text-sm text-gray-300">
                        {validation.hasPrompt 
                          ? `Found ${validation.promptCount} attached prompt(s)`
                          : 'No prompts attached to this bot'
                        }
                      </p>
                    </div>
                  </div>
                  {validation.missingPrompt && (
                    <button
                      onClick={openPromptsTab}
                      className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors text-sm"
                    >
                      Attach Prompt
                    </button>
                  )}
                </div>
                {validation.missingPrompt && (
                  <div className="mt-3 p-3 bg-red-900/20 border border-red-500/20 rounded text-sm text-red-300">
                    <p className="font-medium mb-1">⚠️ Prompt Required</p>
                    <p>This bot requires at least one prompt to guide its trading strategy and decision-making.</p>
                  </div>
                )}
              </div>

              {/* Summary */}
              <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                <h4 className="text-lg font-semibold text-white mb-3">Configuration Status</h4>
                {validation.hasExchangeCredentials && validation.hasPrompt ? (
                  <div className="text-green-400 flex items-center">
                    <span className="mr-2">🎉</span>
                    <span>All configurations are ready! You can start your {networkType === 'TESTNET' ? 'free trial' : 'trade'}.</span>
                  </div>
                ) : (
                  <div className="text-red-400 flex items-center">
                    <span className="mr-2">⚠️</span>
                    <span>Please configure the missing items above before starting.</span>
                  </div>
                )}
              </div>
            </div>
          ) : null}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-700 flex justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleProceed}
            disabled={!validation?.hasExchangeCredentials || !validation?.hasPrompt}
            className={`px-6 py-2 rounded-lg font-medium transition-colors ${
              validation?.hasExchangeCredentials && validation?.hasPrompt
                ? 'bg-green-600 hover:bg-green-700 text-white'
                : 'bg-gray-700 text-gray-400 cursor-not-allowed'
            }`}
          >
            {validation?.hasExchangeCredentials && validation?.hasPrompt
              ? 'Start Free Trial' 
              : 'Configure Missing Items'
            }
          </button>
        </div>
      </div>
    </div>
  )
}
