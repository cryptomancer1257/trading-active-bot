'use client'

import { useState } from 'react'
import Link from 'next/link'
import QuotaTopUpModal from './QuotaTopUpModal'

interface QuotaExhaustedCardProps {
  className?: string
  quotaUsed?: number
  quotaTotal?: number
  planName?: string
  resetDate?: string
}

export default function QuotaExhaustedCard({ 
  className = '',
  quotaUsed = 0,
  quotaTotal = 0,
  planName = 'PRO',
  resetDate
}: QuotaExhaustedCardProps) {
  const [showTopUpModal, setShowTopUpModal] = useState(false)
  const isFree = planName?.toLowerCase() === 'free'

  return (
    <>
      <div className={`bg-gradient-to-br from-red-900/20 to-orange-900/20 border border-red-500/30 rounded-xl p-6 ${className}`}>
        <div className="text-center">
          <div className="text-4xl mb-2 animate-pulse">🚨</div>
          <h3 className="text-red-300 font-bold mb-2 text-lg">Quota Exhausted</h3>
          <p className="text-red-200 text-sm mb-4">
            Your LLM quota has been completely used up
          </p>
          
          {/* Quota Stats */}
          <div className="bg-red-900/30 rounded-lg p-4 mb-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-red-300">Used</p>
                <p className="text-white font-bold">{quotaUsed.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-red-300">Total</p>
                <p className="text-white font-bold">{quotaTotal.toLocaleString()}</p>
              </div>
            </div>
            <div className="mt-3 pt-3 border-t border-red-700">
              <p className="text-red-300 text-xs">Plan: {planName}</p>
              {resetDate && (
                <p className="text-red-300 text-xs">Resets: {new Date(resetDate).toLocaleDateString()}</p>
              )}
            </div>
          </div>
          
          {/* Warning Message */}
          <div className="bg-red-800/30 border border-red-600/50 rounded-lg p-3 mb-4">
            <p className="text-red-200 text-sm">
              ⚠️ Your bots using LLM features are currently paused. 
              {isFree ? ' Upgrade to Pro to continue trading.' : ' Purchase more quota to continue trading.'}
            </p>
          </div>
          
          {/* Action Button - Different for FREE vs PRO/ULTRA */}
          {isFree ? (
            <>
              <Link
                href="/plans"
                className="block w-full px-4 py-3 bg-gradient-to-r from-red-500 to-orange-500 hover:from-red-600 hover:to-orange-600 text-white rounded-lg font-semibold text-sm transition-all transform hover:scale-105 shadow-lg hover:shadow-red-500/25"
              >
                ⚡ Upgrade to Pro
              </Link>
              
              <p className="text-red-400 text-xs mt-3">
                Get access to advanced features and higher quotas
              </p>
            </>
          ) : (
            <>
              <button
                onClick={() => setShowTopUpModal(true)}
                className="w-full px-4 py-3 bg-gradient-to-r from-red-500 to-orange-500 hover:from-red-600 hover:to-orange-600 text-white rounded-lg font-semibold text-sm transition-all transform hover:scale-105 shadow-lg hover:shadow-red-500/25"
              >
                🚨 Purchase Quota Now
              </button>
              
              <p className="text-red-400 text-xs mt-3">
                Get instant access to continue your AI trading
              </p>
            </>
          )}
        </div>
      </div>

      {/* Top-up Modal - Only for non-FREE users */}
      {!isFree && (
        <QuotaTopUpModal 
          isOpen={showTopUpModal}
          onClose={() => setShowTopUpModal(false)}
        />
      )}
    </>
  )
}
