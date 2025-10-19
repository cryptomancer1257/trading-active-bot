'use client'

import { useState } from 'react'
import { usePlan } from '@/hooks/usePlan'
import UpgradeModal from './UpgradeModal'

export default function UpgradeBanner() {
  const { isFree, limits } = usePlan()
  const [showUpgradeModal, setShowUpgradeModal] = useState(false)

  if (!isFree || !limits) return null

  // Show banner if approaching limits or trying mainnet
  const shouldShowBanner = 
    !limits.usage.can_create_bot || 
    !limits.usage.can_publish_marketplace ||
    limits.plan.allowed_environment === 'testnet'

  if (!shouldShowBanner) return null

  return (
    <>
      <div className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-4 py-3 shadow-lg">
        <div className="max-w-7xl mx-auto flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <div className="text-2xl">🚀</div>
            <div>
              <div className="font-bold text-lg">Upgrade to Pro to unlock all features</div>
              <div className="text-sm text-purple-100">
                {!limits.usage.can_create_bot && `You've reached the bot limit (${limits.usage.total_bots}/${limits.plan.max_bots})`}
                {!limits.usage.can_publish_marketplace && "Get mainnet access & publish to marketplace"}
                {limits.plan.allowed_environment === 'testnet' && "Deploy on mainnet & earn 90% revenue share"}
              </div>
            </div>
          </div>
          
          <button
            onClick={() => setShowUpgradeModal(true)}
            className="px-6 py-2.5 bg-white text-purple-600 font-bold rounded-lg hover:bg-purple-50 transition-all shadow-lg hover:scale-105"
          >
            Upgrade to Pro - $60/month
          </button>
        </div>
      </div>

      <UpgradeModal 
        isOpen={showUpgradeModal}
        onClose={() => setShowUpgradeModal(false)}
      />
    </>
  )
}

