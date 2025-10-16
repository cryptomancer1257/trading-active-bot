'use client'

import { useState } from 'react'
import { usePlan } from '@/hooks/usePlan'
import PlanBadge from '@/components/PlanBadge'
import UpgradeModal from '@/components/UpgradeModal'

export default function PlansPage() {
  const { currentPlan, planConfigs, limits, isLoadingPlan, isPro, cancelPlan } = usePlan()
  const [showUpgradeModal, setShowUpgradeModal] = useState(false)
  const [showCancelConfirm, setShowCancelConfirm] = useState(false)

  const handleCancelPlan = async () => {
    try {
      await cancelPlan.mutateAsync()
      setShowCancelConfirm(false)
    } catch (err) {
      console.error('Failed to cancel plan:', err)
    }
  }

  if (isLoadingPlan) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Subscription Plans</h1>
              <p className="text-gray-600 mt-1">Choose the perfect plan for your trading bot business</p>
            </div>
            <PlanBadge />
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Current Usage Stats */}
        {limits && (
          <div className="bg-white rounded-xl shadow-sm p-6 mb-8">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Current Usage</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <div className="text-sm text-gray-600 mb-2">Bots</div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-2xl font-bold text-gray-900">
                    {limits.usage.total_bots} / {limits.plan.max_bots === 999999 ? '∞' : limits.plan.max_bots}
                  </span>
                  <span className={`text-sm font-medium ${limits.usage.can_create_bot ? 'text-green-600' : 'text-red-600'}`}>
                    {limits.usage.bots_remaining} remaining
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full ${limits.usage.can_create_bot ? 'bg-green-500' : 'bg-red-500'}`}
                    style={{ width: `${(limits.usage.total_bots / limits.plan.max_bots) * 100}%` }}
                  ></div>
                </div>
              </div>

              <div>
                <div className="text-sm text-gray-600 mb-2">Environment</div>
                <div className="text-2xl font-bold text-gray-900">
                  {limits.plan.allowed_environment === 'mainnet' ? '🌐 Mainnet' : '🧪 Testnet'}
                </div>
                {limits.plan.allowed_environment === 'testnet' && !isPro && (
                  <p className="text-sm text-orange-600 mt-1">Upgrade to Pro for mainnet access</p>
                )}
              </div>

              <div>
                <div className="text-sm text-gray-600 mb-2">Revenue Share</div>
                <div className="text-2xl font-bold text-gray-900">
                  {limits.plan.revenue_share_percentage}%
                </div>
                {!isPro && (
                  <p className="text-sm text-orange-600 mt-1">Earn 90% with Pro plan</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Plan Comparison */}
        <div className="grid md:grid-cols-2 gap-8 mb-8">
          {/* Free Plan */}
          <div className={`bg-white rounded-2xl shadow-lg p-8 ${!isPro ? 'ring-2 ring-blue-500' : ''}`}>
            <div className="text-center mb-6">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-100 rounded-full mb-4">
                <span className="text-3xl">🆓</span>
              </div>
              <h2 className="text-2xl font-bold text-gray-900">Free Plan</h2>
              <div className="text-4xl font-bold text-gray-900 my-4">$0</div>
              <p className="text-gray-600">Perfect for testing and learning</p>
            </div>

            <ul className="space-y-4 mb-8">
              <li className="flex items-start">
                <span className="text-green-500 mr-3 mt-1">✓</span>
                <span className="text-gray-700"><strong>{planConfigs?.free.max_bots}</strong> trading bots maximum</span>
              </li>
              <li className="flex items-start">
                <span className="text-green-500 mr-3 mt-1">✓</span>
                <span className="text-gray-700"><strong>{planConfigs?.free.max_subscriptions_per_bot}</strong> subscriptions per bot</span>
              </li>
              <li className="flex items-start">
                <span className="text-green-500 mr-3 mt-1">✓</span>
                <span className="text-gray-700"><strong>Testnet</strong> environment only</span>
              </li>
              <li className="flex items-start">
                <span className="text-green-500 mr-3 mt-1">✓</span>
                <span className="text-gray-700"><strong>{planConfigs?.free.subscription_expiry_days}-day</strong> free trial subscriptions</span>
              </li>
              <li className="flex items-start">
                <span className="text-gray-400 mr-3 mt-1">✗</span>
                <span className="text-gray-400 line-through">Publish to marketplace</span>
              </li>
              <li className="flex items-start">
                <span className="text-gray-400 mr-3 mt-1">✗</span>
                <span className="text-gray-400 line-through">Revenue sharing</span>
              </li>
            </ul>

            {!isPro && (
              <div className="text-center text-sm text-gray-600 font-medium">
                Current Plan
              </div>
            )}
          </div>

          {/* Pro Plan */}
          <div className={`bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl shadow-xl p-8 relative ${isPro ? 'ring-2 ring-purple-500' : ''}`}>
            <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 bg-gradient-to-r from-purple-500 to-pink-500 text-white px-4 py-2 rounded-full text-sm font-bold shadow-lg">
              ⚡ RECOMMENDED
            </div>

            <div className="text-center mb-6 pt-4">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full mb-4">
                <span className="text-3xl">⚡</span>
              </div>
              <h2 className="text-2xl font-bold text-gray-900">Pro Plan</h2>
              <div className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent my-4">
                $10
              </div>
              <p className="text-gray-600">per month • Cancel anytime</p>
            </div>

            <ul className="space-y-4 mb-8">
              <li className="flex items-start">
                <span className="text-purple-600 mr-3 mt-1">✓</span>
                <span className="text-gray-900 font-medium"><strong>Unlimited</strong> trading bots</span>
              </li>
              <li className="flex items-start">
                <span className="text-purple-600 mr-3 mt-1">✓</span>
                <span className="text-gray-900 font-medium"><strong>Unlimited</strong> subscriptions per bot</span>
              </li>
              <li className="flex items-start">
                <span className="text-purple-600 mr-3 mt-1">✓</span>
                <span className="text-gray-900 font-medium"><strong>Mainnet</strong> environment access</span>
              </li>
              <li className="flex items-start">
                <span className="text-purple-600 mr-3 mt-1">✓</span>
                <span className="text-gray-900 font-medium"><strong>Unlimited</strong> subscription duration</span>
              </li>
              <li className="flex items-start">
                <span className="text-purple-600 mr-3 mt-1">✓</span>
                <span className="text-gray-900 font-medium"><strong>Publish</strong> to marketplace</span>
              </li>
              <li className="flex items-start">
                <span className="text-purple-600 mr-3 mt-1">✓</span>
                <span className="text-gray-900 font-medium"><strong>90%</strong> revenue share</span>
              </li>
            </ul>

            {isPro ? (
              <div className="space-y-3">
                <div className="text-center text-sm text-purple-600 font-medium mb-4">
                  ✓ Current Plan
                </div>
                {currentPlan?.expiry_date && (
                  <p className="text-center text-sm text-gray-600">
                    Renews on {new Date(currentPlan.expiry_date).toLocaleDateString()}
                  </p>
                )}
                <button
                  onClick={() => setShowCancelConfirm(true)}
                  className="w-full px-6 py-3 border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50 transition-colors"
                >
                  Cancel Subscription
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowUpgradeModal(true)}
                className="w-full px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all shadow-lg hover:shadow-xl transform hover:scale-105"
              >
                Upgrade to Pro Now
              </button>
            )}
          </div>
        </div>

        {/* FAQ */}
        <div className="bg-white rounded-xl shadow-sm p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Frequently Asked Questions</h2>
          <div className="space-y-4">
            <details className="group">
              <summary className="flex items-center justify-between cursor-pointer font-medium text-gray-900 p-4 bg-gray-50 rounded-lg">
                Can I cancel my Pro subscription anytime?
                <span className="ml-2 text-gray-500 group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <p className="mt-2 text-gray-600 p-4">
                Yes! You can cancel your Pro subscription at any time. You'll continue to have Pro access until the end of your billing period.
              </p>
            </details>

            <details className="group">
              <summary className="flex items-center justify-between cursor-pointer font-medium text-gray-900 p-4 bg-gray-50 rounded-lg">
                What happens to my bots if I downgrade to Free?
                <span className="ml-2 text-gray-500 group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <p className="mt-2 text-gray-600 p-4">
                Your existing bots will remain, but you won't be able to create new bots beyond the Free plan limit (5 bots). Marketplace bots will be unpublished.
              </p>
            </details>

            <details className="group">
              <summary className="flex items-center justify-between cursor-pointer font-medium text-gray-900 p-4 bg-gray-50 rounded-lg">
                How does the 90% revenue share work?
                <span className="ml-2 text-gray-500 group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <p className="mt-2 text-gray-600 p-4">
                As a Pro user, you keep 90% of all subscription revenue from your marketplace bots. We only take 10% as a platform fee.
              </p>
            </details>
          </div>
        </div>
      </div>

      {/* Upgrade Modal */}
      <UpgradeModal 
        isOpen={showUpgradeModal}
        onClose={() => setShowUpgradeModal(false)}
      />

      {/* Cancel Confirmation Modal */}
      {showCancelConfirm && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="fixed inset-0 bg-black bg-opacity-50" onClick={() => setShowCancelConfirm(false)}></div>
          <div className="flex min-h-full items-center justify-center p-4">
            <div className="relative bg-white rounded-xl shadow-2xl max-w-md w-full p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4">Cancel Pro Subscription?</h3>
              <p className="text-gray-600 mb-6">
                You'll lose access to Pro features at the end of your billing period. Are you sure you want to cancel?
              </p>
              <div className="flex gap-3">
                <button
                  onClick={() => setShowCancelConfirm(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50"
                >
                  Keep Pro
                </button>
                <button
                  onClick={handleCancelPlan}
                  disabled={cancelPlan.isPending}
                  className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 disabled:opacity-50"
                >
                  {cancelPlan.isPending ? 'Cancelling...' : 'Yes, Cancel'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

