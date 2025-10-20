'use client'

import { useState, useEffect } from 'react'
import { useQuotaUsage } from '@/hooks/useQuota'
import QuotaTopUpModal from './QuotaTopUpModal'
import QuotaUnavailableCard from './QuotaUnavailableCard'
import QuotaExhaustedCard from './QuotaExhaustedCard'

interface QuotaUsageCardProps {
  className?: string
  autoTriggerOnExhausted?: boolean // Auto-open popup when quota exhausted
}

export default function QuotaUsageCard({ className = '', autoTriggerOnExhausted = true }: QuotaUsageCardProps) {
  const [showTopUpModal, setShowTopUpModal] = useState(false)
  const { data: quotaUsage, isLoading, error } = useQuotaUsage()

  // Auto-trigger popup when quota is exhausted
  useEffect(() => {
    if (autoTriggerOnExhausted && quotaUsage && quotaUsage.remaining === 0 && quotaUsage.can_purchase) {
      setShowTopUpModal(true)
    }
  }, [quotaUsage?.remaining, quotaUsage?.can_purchase, autoTriggerOnExhausted])

  if (isLoading) {
    return (
      <div className={`bg-dark-800/60 rounded-xl p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-700 rounded mb-4"></div>
          <div className="h-4 bg-gray-700 rounded mb-2"></div>
          <div className="h-2 bg-gray-700 rounded"></div>
        </div>
      </div>
    )
  }

  if (error || !quotaUsage) {
    return <QuotaUnavailableCard className={className} />
  }

  // Free Plan - Show special message
  if (quotaUsage.plan_name.toUpperCase() === 'FREE' || !quotaUsage.can_purchase) {
    return (
      <div className={`bg-gradient-to-br from-gray-800/80 to-gray-900/80 rounded-xl p-6 border border-gray-700 ${className}`}>
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <span className="text-2xl mr-3">🆓</span>
            <div>
              <h3 className="text-white font-bold text-lg">Trades Quota</h3>
              <p className="text-gray-400 text-sm">FREE Plan</p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-2xl">∞</div>
            <div className="text-xs font-semibold text-yellow-400">
              Unlimited
            </div>
          </div>
        </div>

        {/* Free Plan Info */}
        <div className="mb-4 p-4 bg-yellow-900/20 border border-yellow-500/30 rounded-lg">
          <div className="flex items-start">
            <span className="mr-3 text-yellow-400 text-xl">⚠️</span>
            <div className="flex-1">
              <p className="text-yellow-300 font-semibold text-sm mb-2">
                Free Plan Limitations
              </p>
              <ul className="text-yellow-200/80 text-xs space-y-1">
                <li>• Unlimited trades with <strong>low quality AI models</strong></li>
                <li>• Slower response times and lower analysis accuracy</li>
                <li>• Testnet trading only</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Upgrade CTA */}
        <div className="space-y-3">
          <p className="text-gray-300 text-sm text-center mb-3">
            Unlock faster trading speeds, advanced models (GPT-4o, Claude 3.7 Sonnet), and higher accuracy
          </p>
          
          <a
            href="/plans"
            className="block w-full px-4 py-3 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-bold text-sm rounded-lg transition-all shadow-lg hover:shadow-purple-500/50 transform hover:scale-105 text-center"
          >
            ⚡ Upgrade to Pro Plan - $60/mo
          </a>
          
          <a
            href="/plans"
            className="block w-full px-4 py-2 bg-gradient-to-r from-yellow-500/20 to-orange-500/20 hover:from-yellow-500/30 hover:to-orange-500/30 text-yellow-300 font-semibold text-sm rounded-lg transition-all border border-yellow-500/30 text-center"
          >
            💎 View Ultra Plan - $500/mo
          </a>
        </div>
      </div>
    )
  }

  // Show exhausted state if quota is completely used up
  if (quotaUsage.remaining === 0) {
    return (
      <QuotaExhaustedCard 
        className={className}
        quotaUsed={quotaUsage.used}
        quotaTotal={quotaUsage.total}
        planName={quotaUsage.plan_name}
        resetDate={quotaUsage.reset_at}
      />
    )
  }

  const getProgressColor = (percentage: number) => {
    if (percentage >= 90) return 'bg-red-500'
    if (percentage >= 70) return 'bg-yellow-500'
    return 'bg-green-500'
  }

  const getStatusIcon = (percentage: number) => {
    if (percentage >= 90) return '🚨'
    if (percentage >= 70) return '⚠️'
    return '✅'
  }

  const getStatusText = (percentage: number) => {
    if (percentage >= 90) return 'Critical'
    if (percentage >= 70) return 'Low'
    return 'Good'
  }

  return (
    <>
      <div className={`bg-dark-800/60 rounded-xl p-6 ${className}`}>
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <span className="text-2xl mr-3">🤖</span>
            <div>
              <h3 className="text-white font-bold text-lg">Trades Quota</h3>
              <p className="text-gray-400 text-sm">
                {quotaUsage.plan_name.toUpperCase()} Plan
              </p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-2xl">{getStatusIcon(quotaUsage.percentage)}</div>
            <div className={`text-xs font-semibold ${
              quotaUsage.percentage >= 90 ? 'text-red-400' :
              quotaUsage.percentage >= 70 ? 'text-yellow-400' : 'text-green-400'
            }`}>
              {getStatusText(quotaUsage.percentage)}
            </div>
          </div>
        </div>

        {/* Usage Stats */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-400 text-sm">Used</span>
            <span className="text-white font-bold">
              {quotaUsage.used.toLocaleString()} / {quotaUsage.total.toLocaleString()}
            </span>
          </div>
          
          {/* Progress Bar */}
          <div className="w-full bg-gray-700 rounded-full h-2 mb-2">
            <div 
              className={`h-2 rounded-full transition-all duration-300 ${getProgressColor(quotaUsage.percentage)}`}
              style={{ width: `${Math.min(quotaUsage.percentage, 100)}%` }}
            />
          </div>
          
          <div className="flex justify-between text-xs text-gray-400">
            <span>{quotaUsage.percentage.toFixed(1)}% used</span>
            <span>{quotaUsage.remaining.toLocaleString()} remaining</span>
          </div>
        </div>

        {/* Reset Info */}
        {quotaUsage.reset_at && (
          <div className="mb-4 p-3 bg-gray-800/50 rounded-lg">
            <div className="flex items-center text-sm text-gray-400">
              <span className="mr-2">🔄</span>
              <span>Resets on {new Date(quotaUsage.reset_at).toLocaleDateString()}</span>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="space-y-2">
          {quotaUsage.can_purchase && (
            <button
              onClick={() => setShowTopUpModal(true)}
              className={`w-full px-4 py-2 rounded-lg font-semibold text-sm transition-all ${
                quotaUsage.remaining < 100
                  ? 'bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white'
                  : 'bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white'
              }`}
            >
              {quotaUsage.remaining < 100 ? '🚨 Buy More Quota' : '💎 Buy Additional Quota'}
            </button>
          )}
          
          {!quotaUsage.can_purchase && (
            <div className="w-full px-4 py-2 rounded-lg bg-gray-700 text-gray-400 text-sm text-center">
              <span className="mr-2">🔒</span>
              Upgrade to PRO or ULTRA to buy quota
            </div>
          )}
        </div>

        {/* Low Quota Warning */}
        {quotaUsage.remaining < 50 && quotaUsage.remaining > 0 && (
          <div className="mt-4 p-3 bg-yellow-900/20 border border-yellow-500/30 rounded-lg">
            <div className="flex items-center text-yellow-300 text-sm">
              <span className="mr-2">⚠️</span>
              <span>Low quota warning: {quotaUsage.remaining} trades remaining</span>
            </div>
          </div>
        )}

        {/* Critical Quota Warning */}
        {quotaUsage.remaining === 0 && (
          <div className="mt-4 p-3 bg-red-900/20 border border-red-500/30 rounded-lg">
            <div className="flex items-center text-red-300 text-sm">
              <span className="mr-2">🚨</span>
              <span>Quota exhausted! Purchase more to continue trading.</span>
            </div>
          </div>
        )}
      </div>

      {/* Top-up Modal */}
      <QuotaTopUpModal 
        isOpen={showTopUpModal}
        onClose={() => setShowTopUpModal(false)}
      />
    </>
  )
}
