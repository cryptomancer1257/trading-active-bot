'use client'

import { useState } from 'react'
import { InformationCircleIcon } from '@heroicons/react/24/outline'

interface HistoricalLearningConfig {
  enabled: boolean
  transaction_limit: 10 | 25 | 50
  include_failed_trades: boolean
  learning_mode: 'recent' | 'best_performance' | 'mixed'
}

interface HistoricalLearningStats {
  total_trades: number
  win_count: number
  loss_count: number
  win_rate: number
  avg_win: number
  avg_loss: number
  risk_reward_ratio: number
  total_pnl: number
}

interface HistoricalLearningConfigProps {
  botId: number
  value: HistoricalLearningConfig
  onChange: (config: HistoricalLearningConfig) => void
  stats?: HistoricalLearningStats | null
  onSave?: () => void
}

export default function HistoricalLearningConfig({ 
  botId, 
  value, 
  onChange,
  stats,
  onSave
}: HistoricalLearningConfigProps) {
  const [showAdvanced, setShowAdvanced] = useState(false)
  
  const transactionOptions = [
    { 
      value: 10, 
      label: 'Minimal', 
      desc: '~2K tokens · High-frequency trading', 
      emoji: '🟢',
      cost: '$0.04/call'
    },
    { 
      value: 25, 
      label: 'Balanced', 
      desc: '~5K tokens · Daily signals', 
      emoji: '🟡', 
      recommended: true,
      cost: '$0.10/call'
    },
    { 
      value: 50, 
      label: 'Comprehensive', 
      desc: '~10K tokens · Swing trading', 
      emoji: '🔴',
      cost: '$0.20/call'
    },
  ]
  
  return (
    <div className="space-y-6">
      {/* Info Banner */}
      <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-6">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <InformationCircleIcon className="h-6 w-6 text-purple-600" />
          </div>
          <div className="ml-3">
            <h3 className="text-lg font-medium text-purple-900">
              🧠 Historical Learning
            </h3>
            <div className="mt-2 text-sm text-purple-700">
              <p>
                Enable LLM to learn from your bot's past transactions and avoid repeating mistakes.
                The AI will analyze patterns from winning and losing trades to improve decision-making.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Enable Toggle */}
      <div className="flex items-center justify-between p-4 bg-white border border-gray-200 rounded-lg">
        <div>
          <label className="text-sm font-medium text-gray-900">
            Enable Historical Learning
          </label>
          <p className="text-sm text-gray-500">
            LLM will analyze past transactions to improve decisions
          </p>
        </div>
        <button
          type="button"
          onClick={() => onChange({ ...value, enabled: !value.enabled })}
          className={`${
            value.enabled ? 'bg-purple-600' : 'bg-gray-200'
          } relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2`}
        >
          <span
            className={`${
              value.enabled ? 'translate-x-5' : 'translate-x-0'
            } pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out`}
          />
        </button>
      </div>

      {value.enabled && (
        <>
          {/* Transaction Limit Selector */}
          <div className="space-y-3">
            <label className="text-sm font-medium text-gray-900">
              Number of Transactions to Analyze
            </label>
            
            <div className="space-y-2">
              {transactionOptions.map((option) => (
                <div
                  key={option.value}
                  onClick={() => onChange({ ...value, transaction_limit: option.value as 10 | 25 | 50 })}
                  className={`relative flex cursor-pointer rounded-lg border p-4 focus:outline-none ${
                    value.transaction_limit === option.value
                      ? 'border-purple-500 bg-purple-50 ring-2 ring-purple-500'
                      : 'border-gray-300 bg-white hover:border-purple-300'
                  }`}
                >
                  <div className="flex flex-1">
                    <div className="flex items-center">
                      <input
                        type="radio"
                        checked={value.transaction_limit === option.value}
                        onChange={() => onChange({ ...value, transaction_limit: option.value as 10 | 25 | 50 })}
                        className="h-4 w-4 border-gray-300 text-purple-600 focus:ring-purple-500"
                      />
                    </div>
                    <div className="ml-3 flex flex-col">
                      <span className="text-sm font-medium text-gray-900">
                        {option.emoji} {option.label} ({option.value} transactions)
                        {option.recommended && (
                          <span className="ml-2 inline-flex items-center rounded-full bg-purple-100 px-2.5 py-0.5 text-xs font-medium text-purple-800">
                            ⭐ Recommended
                          </span>
                        )}
                      </span>
                      <span className="text-sm text-gray-500">{option.desc}</span>
                      <span className="text-xs text-gray-400 mt-1">Est. cost: {option.cost}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Performance Summary */}
          {stats && stats.total_trades > 0 && (
            <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
              <h4 className="text-sm font-medium text-gray-900 mb-3">
                📊 Recent Performance (Last {stats.total_trades} trades)
              </h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Win Rate</p>
                  <p className={`text-lg font-semibold ${
                    stats.win_rate >= 50 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {stats.win_rate}%
                  </p>
                  <p className="text-xs text-gray-400">
                    {stats.win_count}W / {stats.loss_count}L
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Total P&L</p>
                  <p className={`text-lg font-semibold ${
                    stats.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {stats.total_pnl >= 0 ? '+' : ''}{stats.total_pnl.toFixed(2)}%
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Avg Win</p>
                  <p className="text-lg font-semibold text-green-600">
                    +{stats.avg_win.toFixed(2)}%
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Avg Loss</p>
                  <p className="text-lg font-semibold text-red-600">
                    {stats.avg_loss.toFixed(2)}%
                  </p>
                </div>
                {stats.risk_reward_ratio > 0 && (
                  <div className="col-span-2">
                    <p className="text-sm text-gray-500">Risk/Reward Ratio</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {stats.risk_reward_ratio.toFixed(2)}:1
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Advanced Options */}
          <div>
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="text-sm text-purple-600 hover:text-purple-700 font-medium flex items-center"
            >
              <span className="mr-1">{showAdvanced ? '▼' : '▶'}</span>
              Advanced Options
            </button>

            {showAdvanced && (
              <div className="mt-3 space-y-3 pl-4 border-l-2 border-purple-200">
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id={`include-failed-${botId}`}
                    checked={value.include_failed_trades}
                    onChange={(e) => onChange({ ...value, include_failed_trades: e.target.checked })}
                    className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                  />
                  <label htmlFor={`include-failed-${botId}`} className="ml-2 text-sm text-gray-700">
                    Include failed trades for learning
                  </label>
                </div>
                
                <div>
                  <label className="text-sm font-medium text-gray-700 block mb-2">
                    Learning Mode
                  </label>
                  <div className="space-y-2">
                    {[
                      { value: 'recent', label: 'Recent (time-ordered, most recent first)' },
                      { value: 'best_performance', label: 'Best Performance (sorted by profit)' },
                      { value: 'mixed', label: 'Mixed (recent + top performers)' },
                    ].map((mode) => (
                      <label key={mode.value} className="flex items-center">
                        <input
                          type="radio"
                          checked={value.learning_mode === mode.value}
                          onChange={() => onChange({ ...value, learning_mode: mode.value as any })}
                          className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300"
                        />
                        <span className="ml-2 text-sm text-gray-600">{mode.label}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Save Button */}
          {onSave && (
            <div className="flex justify-end pt-4 border-t border-gray-200">
              <button
                type="button"
                onClick={onSave}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
              >
                💾 Save Configuration
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export type { HistoricalLearningConfig, HistoricalLearningStats }

