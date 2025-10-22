'use client'

import { useState } from 'react'
import Link from 'next/link'
import QuotaTopUpModal from './QuotaTopUpModal'

interface QuotaUnavailableCardProps {
  className?: string
  title?: string
  message?: string
  showTopUpButton?: boolean
  planName?: string  // NEW: Plan name to determine button text
}

export default function QuotaUnavailableCard({ 
  className = '',
  title = "Quota Unavailable",
  message = "Unable to load quota information",
  showTopUpButton = true,
  planName = 'free'  // NEW: Default to free
}: QuotaUnavailableCardProps) {
  const [showTopUpModal, setShowTopUpModal] = useState(false)
  const isFree = planName?.toLowerCase() === 'free'

  return (
    <>
      <div className={`bg-dark-800/60 rounded-xl p-6 ${className}`}>
        <div className="text-center">
          <div className="text-4xl mb-2">❌</div>
          <h3 className="text-white font-bold mb-2">{title}</h3>
          <p className="text-gray-400 text-sm mb-4">{message}</p>
          
          {showTopUpButton && (
            <>
              {/* Action Button - Different for FREE vs PRO/ULTRA */}
              {isFree ? (
                <>
                  <Link
                    href="/plans"
                    className="block w-full px-4 py-3 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white rounded-lg font-semibold text-sm transition-all transform hover:scale-105 shadow-lg hover:shadow-purple-500/25"
                  >
                    ⚡ Upgrade to Pro
                  </Link>
                  
                  <p className="text-gray-500 text-xs mt-3">
                    Get access to advanced features and higher quotas
                  </p>
                </>
              ) : (
                <>
                  <button
                    onClick={() => setShowTopUpModal(true)}
                    className="w-full px-4 py-3 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white rounded-lg font-semibold text-sm transition-all transform hover:scale-105 shadow-lg hover:shadow-purple-500/25"
                  >
                    💎 Purchase Quota Now
                  </button>
                  
                  <p className="text-gray-500 text-xs mt-3">
                    Get instant access to LLM features
                  </p>
                </>
              )}
            </>
          )}
        </div>
      </div>

      {/* Top-up Modal - Only for non-FREE users */}
      {showTopUpButton && !isFree && (
        <QuotaTopUpModal 
          isOpen={showTopUpModal}
          onClose={() => setShowTopUpModal(false)}
        />
      )}
    </>
  )
}
