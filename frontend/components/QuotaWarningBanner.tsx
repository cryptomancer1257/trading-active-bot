'use client'

import { useQuotaUsage } from '@/hooks/useQuota'
import { useState } from 'react'
import QuotaTopUpModal from './QuotaTopUpModal'

export default function QuotaWarningBanner() {
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
      {/* Exhausted Banner - Red */}
      {isExhausted && (
        <div className="bg-gradient-to-r from-red-900/90 to-orange-900/90 border-b border-red-500/50 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <span className="text-2xl animate-pulse">🚨</span>
                <div>
                  <p className="text-white font-bold text-sm">
                    LLM Quota Exhausted!
                  </p>
                  <p className="text-red-200 text-xs">
                    Your bots cannot use LLM features. Purchase more quota to continue.
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                {quotaUsage.can_purchase && (
                  <button
                    onClick={() => setShowTopUpModal(true)}
                    className="px-4 py-2 bg-white text-red-900 rounded-lg font-semibold text-sm hover:bg-gray-100 transition-colors"
                  >
                    Buy Quota Now
                  </button>
                )}
                <button
                  onClick={() => setIsDismissed(true)}
                  className="p-2 text-white hover:text-gray-200 transition-colors"
                  aria-label="Dismiss"
                >
                  ✕
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Critical Banner - Orange */}
      {isCritical && (
        <div className="bg-gradient-to-r from-orange-900/80 to-yellow-900/80 border-b border-orange-500/50 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <span className="text-xl">⚠️</span>
                <div>
                  <p className="text-white font-bold text-sm">
                    Critical: Only {quotaUsage.remaining} LLM calls remaining
                  </p>
                  <p className="text-orange-200 text-xs">
                    Purchase additional quota to avoid service interruption.
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                {quotaUsage.can_purchase && (
                  <button
                    onClick={() => setShowTopUpModal(true)}
                    className="px-4 py-2 bg-white text-orange-900 rounded-lg font-semibold text-sm hover:bg-gray-100 transition-colors"
                  >
                    Buy More Quota
                  </button>
                )}
                <button
                  onClick={() => setIsDismissed(true)}
                  className="p-2 text-white hover:text-gray-200 transition-colors"
                  aria-label="Dismiss"
                >
                  ✕
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Low Quota Banner - Yellow */}
      {isLow && (
        <div className="bg-gradient-to-r from-yellow-900/70 to-yellow-800/70 border-b border-yellow-500/50 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <span className="text-lg">💡</span>
                <div>
                  <p className="text-white font-semibold text-sm">
                    Low LLM Quota: {quotaUsage.remaining} calls remaining
                  </p>
                  {quotaUsage.reset_at && (
                    <p className="text-yellow-200 text-xs">
                      Resets on {new Date(quotaUsage.reset_at as string).toLocaleDateString()}
                    </p>
                  )}
                </div>
              </div>
              <div className="flex items-center space-x-2">
                {quotaUsage.can_purchase && (
                  <button
                    onClick={() => setShowTopUpModal(true)}
                    className="px-3 py-1.5 bg-white text-yellow-900 rounded-lg font-semibold text-xs hover:bg-gray-100 transition-colors"
                  >
                    Buy Quota
                  </button>
                )}
                <button
                  onClick={() => setIsDismissed(true)}
                  className="p-1 text-white hover:text-gray-200 transition-colors text-sm"
                  aria-label="Dismiss"
                >
                  ✕
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Top-up Modal */}
      <QuotaTopUpModal 
        isOpen={showTopUpModal}
        onClose={() => setShowTopUpModal(false)}
      />
    </>
  )
}

