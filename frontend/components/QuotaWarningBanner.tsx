'use client'

import { useQuotaUsage } from '@/hooks/useQuota'
import { useState } from 'react'
import QuotaTopUpModal from './QuotaTopUpModal'

export default function QuotaWarningBanner() {
  // TEMPORARY: Hide quota warning banner
  return null
  
  /*
  const [showTopUpModal, setShowTopUpModal] = useState(false)
  const [isDismissed, setIsDismissed] = useState(false)
  const { data: quotaUsage } = useQuotaUsage()

  // Don't show if dismissed or no quota data
  if (isDismissed || !quotaUsage) return null

  // Don't show if quota is OK (> 100 remaining)
  if (quotaUsage.remaining > 100) return null

  // Determine warning level
  const isExhausted = quotaUsage.remaining === 0
  const isCritical = quotaUsage.remaining < 50 && quotaUsage.remaining > 0
  const isLow = quotaUsage.remaining < 100 && quotaUsage.remaining >= 50

  return (
    <>
      {isExhausted && (
        <div className="bg-gradient-to-r from-red-900/90 to-orange-900/90 border-b border-red-500/50 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <div className="flex-shrink-0 text-2xl">
                  🚨
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-white mb-0.5">
                    LLM Quota Exhausted
                  </p>
                  <p className="text-xs text-red-200">
                    You've used {quotaUsage.used} of {quotaUsage.total} daily quota. Top up now to continue using AI features.
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                <button
                  onClick={() => setShowTopUpModal(true)}
                  className="px-4 py-2 bg-white text-red-900 rounded-lg text-sm font-medium hover:bg-red-50 transition-colors"
                >
                  ⚡ Top Up Now
                </button>
                <button
                  onClick={() => setIsDismissed(true)}
                  className="p-2 text-red-200 hover:text-white hover:bg-red-800/50 rounded-lg transition-colors"
                  aria-label="Dismiss"
                >
                  ✕
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {isCritical && (
        <div className="bg-gradient-to-r from-orange-900/90 to-yellow-900/90 border-b border-orange-500/50 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2.5">
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <div className="flex-shrink-0 text-xl">
                  ⚠️
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white">
                    Critical: Only {quotaUsage.remaining} LLM calls remaining today
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                <button
                  onClick={() => setShowTopUpModal(true)}
                  className="px-3 py-1.5 bg-white text-orange-900 rounded-lg text-xs font-medium hover:bg-orange-50 transition-colors"
                >
                  Top Up
                </button>
                <button
                  onClick={() => setIsDismissed(true)}
                  className="p-1.5 text-orange-200 hover:text-white hover:bg-orange-800/50 rounded-lg transition-colors"
                  aria-label="Dismiss"
                >
                  ✕
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {isLow && (
        <div className="bg-gradient-to-r from-yellow-900/90 to-amber-900/90 border-b border-yellow-500/50 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2">
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <div className="flex-shrink-0 text-lg">
                  💡
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-white">
                    Low quota: {quotaUsage.remaining} of {quotaUsage.total} LLM calls remaining today
                    <span className="ml-1 text-yellow-200">
                      ({Math.round((quotaUsage.remaining / quotaUsage.total) * 100)}% left)
                    </span>
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                <button
                  onClick={() => setShowTopUpModal(true)}
                  className="px-3 py-1 bg-white text-yellow-900 rounded text-xs font-medium hover:bg-yellow-50 transition-colors"
                >
                  Top Up
                </button>
                <button
                  onClick={() => setIsDismissed(true)}
                  className="p-1 text-yellow-200 hover:text-white hover:bg-yellow-800/50 rounded transition-colors"
                  aria-label="Dismiss"
                >
                  ✕
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <QuotaTopUpModal 
        isOpen={showTopUpModal}
        onClose={() => setShowTopUpModal(false)}
      />
    </>
  )
  */
}
