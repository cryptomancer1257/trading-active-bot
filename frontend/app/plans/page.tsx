'use client'

import { useState, useEffect } from 'react'
import { usePlan } from '@/hooks/usePlan'
import PlanBadge from '@/components/PlanBadge'
import UpgradeModal from '@/components/UpgradeModal'
import { api } from '@/lib/api'

interface PlanPricing {
  plan_name: string
  original_price_usd: number
  discount_percentage: number
  current_price_usd: number
  campaign_name: string | null
  campaign_active: boolean
}

export default function PlansPage() {
  const { currentPlan, planConfigs, limits, isLoadingPlan, isPro, cancelPlan } = usePlan()
  const [showUpgradeModal, setShowUpgradeModal] = useState(false)
  const [targetPlan, setTargetPlan] = useState<'pro' | 'ultra'>('pro')
  const [showCancelConfirm, setShowCancelConfirm] = useState(false)
  const [pricings, setPricings] = useState<Record<string, PlanPricing>>({})
  const [isLoadingPricing, setIsLoadingPricing] = useState(true)
  
  // Check if user is logged in
  const isLoggedIn = typeof window !== 'undefined' && !!localStorage.getItem('access_token')
  
  useEffect(() => {
    fetchPricings()
  }, [])
  
  const fetchPricings = async () => {
    setIsLoadingPricing(true)
    try {
      const plans = ['free', 'pro', 'ultra']
      const results: Record<string, PlanPricing> = {}
      
      for (const planName of plans) {
        try {
          const response = await api.get(`/admin/plan-pricing/${planName}`)
          const data = response.data
          // Convert string prices to numbers
          results[planName] = {
            ...data,
            original_price_usd: parseFloat(data.original_price_usd) || 0,
            discount_percentage: parseFloat(data.discount_percentage) || 0,
            current_price_usd: parseFloat(data.current_price_usd) || 0
          }
        } catch (err) {
          console.error(`Failed to fetch pricing for ${planName}:`, err)
          // Set default values if fetch fails
          results[planName] = {
            plan_name: planName,
            original_price_usd: planName === 'pro' ? 60 : planName === 'ultra' ? 500 : 0,
            discount_percentage: 0,
            current_price_usd: planName === 'pro' ? 60 : planName === 'ultra' ? 500 : 0,
            campaign_name: null,
            campaign_active: false
          }
        }
      }
      
      setPricings(results)
    } catch (error) {
      console.error('Failed to fetch pricing:', error)
    } finally {
      setIsLoadingPricing(false)
    }
  }

  const handleCancelPlan = async () => {
    try {
      await cancelPlan.mutateAsync()
      setShowCancelConfirm(false)
    } catch (err) {
      console.error('Failed to cancel plan:', err)
    }
  }

  // Only show loading if user is logged in AND we're loading their plan
  if (isLoggedIn && isLoadingPlan) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
      </div>
    )
  }
  
  // Show basic loading for pricing data
  if (isLoadingPricing && Object.keys(pricings).length === 0) {
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
            {isLoggedIn && <PlanBadge />}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Current Usage Stats - Only show if logged in */}
        {isLoggedIn && limits && (
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
                  <p className="text-sm text-orange-600 mt-1">Earn 100% with Pro plan</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Plan Comparison - 3 Tiers */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          {/* Free Plan */}
          <div className={`bg-white rounded-2xl shadow-lg p-6 ${!isPro ? 'ring-2 ring-blue-500' : ''}`}>
            <div className="text-center mb-4">
              <div className="inline-flex items-center justify-center w-12 h-12 bg-gray-100 rounded-full mb-3">
                <span className="text-2xl">🆓</span>
              </div>
              <h2 className="text-xl font-bold text-gray-900">Free</h2>
              <div className="text-3xl font-bold text-gray-900 my-3">$0</div>
              <p className="text-sm text-gray-600">forever</p>
            </div>

            <ul className="space-y-3 mb-6 text-sm">
              <li className="flex items-start">
                <span className="text-green-500 mr-2 mt-0.5">✓</span>
                <span className="text-gray-700"><strong>{planConfigs?.free.max_bots}</strong> bots</span>
              </li>
              <li className="flex items-start">
                <span className="text-green-500 mr-2 mt-0.5">✓</span>
                <span className="text-gray-700"><strong>{planConfigs?.free.max_subscriptions_per_bot}</strong> max subscriptions</span>
              </li>
              <li className="flex items-start">
                <span className="text-green-500 mr-2 mt-0.5">✓</span>
                <span className="text-gray-700"><strong>Testnet Only</strong></span>
              </li>
              <li className="flex items-start">
                <span className="text-green-500 mr-2 mt-0.5">✓</span>
                <span className="text-gray-700"><strong>∞ Unlimited/month</strong> (low quality)</span>
              </li>
              <li className="flex items-start">
                <span className="text-green-500 mr-2 mt-0.5">✓</span>
                <span className="text-gray-700"><strong>5 Strategies</strong> template</span>
              </li>
              <li className="flex items-start">
                <span className="text-gray-400 mr-2 mt-0.5">✗</span>
                <span className="text-gray-400">Publish to marketplace</span>
              </li>
            </ul>

            {!isPro && (
              <div className="text-center text-sm text-gray-600 font-medium">
                Current Plan
              </div>
            )}
          </div>

          {/* Pro Plan */}
          <div className={`bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl shadow-xl p-6 relative ${isPro ? 'ring-2 ring-purple-500' : ''}`}>
            <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-gradient-to-r from-purple-500 to-pink-500 text-white px-3 py-1 rounded-full text-xs font-bold shadow-lg">
              ⚡ RECOMMENDED
            </div>
            
            {pricings.pro?.discount_percentage > 0 && pricings.pro?.campaign_active && (
              <div className="absolute -top-3 -right-3 bg-gradient-to-r from-yellow-400 to-orange-500 text-white px-4 py-2 rounded-full text-sm font-bold shadow-lg transform rotate-12 animate-pulse">
                {pricings.pro.discount_percentage}% OFF
              </div>
            )}

            <div className="text-center mb-4 pt-2">
              <div className="inline-flex items-center justify-center w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full mb-3">
                <span className="text-2xl">⚡</span>
              </div>
              <h2 className="text-xl font-bold text-gray-900">Pro</h2>
              
              {pricings.pro?.campaign_active && pricings.pro?.campaign_name && (
                <div className="text-xs text-orange-600 font-semibold mb-2">
                  🎉 {pricings.pro.campaign_name}
                </div>
              )}
              
              {pricings.pro?.discount_percentage > 0 ? (
                <div>
                  <div className="text-lg text-gray-400 line-through mb-1">
                    ${pricings.pro.original_price_usd.toFixed(2)}
                  </div>
                  <div className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent my-2">
                    ${pricings.pro.current_price_usd.toFixed(2)}
                  </div>
                </div>
              ) : (
                <div className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent my-3">
                  ${pricings.pro?.current_price_usd?.toFixed(2) || '60'}
                </div>
              )}
              <p className="text-sm text-gray-600">per month</p>
            </div>

            <ul className="space-y-3 mb-6 text-sm">
              <li className="flex items-start">
                <span className="text-purple-600 mr-2 mt-0.5">✓</span>
                <span className="text-gray-900"><strong>{planConfigs?.pro.max_bots || 20}</strong> bots</span>
              </li>
              <li className="flex items-start">
                <span className="text-purple-600 mr-2 mt-0.5">✓</span>
                <span className="text-gray-900"><strong>{planConfigs?.pro.max_subscriptions_per_bot || 20}</strong> subscriptions</span>
              </li>
              <li className="flex items-start">
                <span className="text-purple-600 mr-2 mt-0.5">✓</span>
                <span className="text-gray-900"><strong>Testnet + Mainnet</strong></span>
              </li>
              <li className="flex items-start">
                <span className="text-purple-600 mr-2 mt-0.5">✓</span>
                <span className="text-gray-900"><strong>720 trades/month</strong></span>
              </li>
              <li className="flex items-start">
                <span className="text-purple-600 mr-2 mt-0.5">✓</span>
                <span className="text-gray-900"><strong>Full Access</strong> strategies template</span>
              </li>
              <li className="flex items-start">
                <span className="text-purple-600 mr-2 mt-0.5">✓</span>
                <span className="text-gray-900"><strong>✅ Full Access</strong> marketplace</span>
              </li>
              <li className="flex items-start">
                <span className="text-purple-600 mr-2 mt-0.5">✓</span>
                <span className="text-gray-900"><strong>24/7 Support</strong></span>
              </li>
            </ul>

            {isPro ? (
              <div className="space-y-2">
                <div className="text-center text-xs text-purple-600 font-medium">
                  ✓ Current Plan
                </div>
                {currentPlan?.expiry_date && (
                  <p className="text-center text-xs text-gray-600">
                    Renews {new Date(currentPlan.expiry_date).toLocaleDateString()}
                  </p>
                )}
                <button
                  onClick={() => setShowCancelConfirm(true)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 font-medium hover:bg-gray-50"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <button
                onClick={() => {
                  if (!isLoggedIn) {
                    window.location.href = '/login?redirect=/plans'
                    return
                  }
                  setTargetPlan('pro')
                  setShowUpgradeModal(true)
                }}
                className="w-full px-4 py-2.5 bg-gradient-to-r from-purple-600 to-pink-600 text-white text-sm font-bold rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all shadow-lg hover:shadow-xl"
              >
                {isLoggedIn ? 'Upgrade to Pro' : 'Sign in to Upgrade'}
              </button>
            )}
          </div>

          {/* Ultra Plan */}
          <div className="bg-gradient-to-br from-yellow-50 to-orange-50 rounded-2xl shadow-xl p-6 border-2 border-yellow-400/50 relative">
            {pricings.ultra?.discount_percentage > 0 && pricings.ultra?.campaign_active && (
              <div className="absolute -top-3 -right-3 bg-gradient-to-r from-red-500 to-pink-500 text-white px-4 py-2 rounded-full text-sm font-bold shadow-lg transform rotate-12 animate-pulse">
                {pricings.ultra.discount_percentage}% OFF
              </div>
            )}
            
            <div className="text-center mb-4">
              <div className="inline-flex items-center justify-center w-12 h-12 bg-gradient-to-r from-yellow-400 to-orange-500 rounded-full mb-3">
                <span className="text-2xl">💎</span>
              </div>
              <h2 className="text-xl font-bold text-gray-900">Ultra</h2>
              
              {pricings.ultra?.campaign_active && pricings.ultra?.campaign_name && (
                <div className="text-xs text-orange-600 font-semibold mb-2">
                  🎉 {pricings.ultra.campaign_name}
                </div>
              )}
              
              {pricings.ultra?.discount_percentage > 0 ? (
                <div>
                  <div className="text-lg text-gray-400 line-through mb-1">
                    ${pricings.ultra.original_price_usd.toFixed(2)}
                  </div>
                  <div className="text-3xl font-bold bg-gradient-to-r from-yellow-600 to-orange-600 bg-clip-text text-transparent my-2">
                    ${pricings.ultra.current_price_usd.toFixed(2)}
                  </div>
                </div>
              ) : (
                <div className="text-3xl font-bold bg-gradient-to-r from-yellow-600 to-orange-600 bg-clip-text text-transparent my-3">
                  ${pricings.ultra?.current_price_usd?.toFixed(2) || '500'}
                </div>
              )}
              <p className="text-sm text-gray-600">per month</p>
            </div>

            <ul className="space-y-3 mb-6 text-sm">
              <li className="flex items-start">
                <span className="text-yellow-600 mr-2 mt-0.5">✓</span>
                <span className="text-gray-900"><strong>∞ Unlimited</strong> bots</span>
              </li>
              <li className="flex items-start">
                <span className="text-yellow-600 mr-2 mt-0.5">✓</span>
                <span className="text-gray-900"><strong>∞ Unlimited</strong> subscriptions</span>
              </li>
              <li className="flex items-start">
                <span className="text-yellow-600 mr-2 mt-0.5">✓</span>
                <span className="text-gray-900"><strong>Testnet + Mainnet</strong></span>
              </li>
              <li className="flex items-start">
                <span className="text-yellow-600 mr-2 mt-0.5">✓</span>
                <span className="text-gray-900"><strong>7,200 trades/month</strong></span>
              </li>
              <li className="flex items-start">
                <span className="text-yellow-600 mr-2 mt-0.5">✓</span>
                <span className="text-gray-900"><strong>Full Access</strong> strategies template</span>
              </li>
              <li className="flex items-start">
                <span className="text-yellow-600 mr-2 mt-0.5">✓</span>
                <span className="text-gray-900"><strong>✅ Full Access</strong> marketplace</span>
              </li>
              <li className="flex items-start">
                <span className="text-yellow-600 mr-2 mt-0.5">✓</span>
                <span className="text-gray-900"><strong>24/7 Dedicated</strong> support</span>
              </li>
            </ul>

            <button
              onClick={() => {
                if (!isLoggedIn) {
                  window.location.href = '/login?redirect=/plans'
                  return
                }
                setTargetPlan('ultra')
                setShowUpgradeModal(true)
              }}
              className="w-full px-4 py-2.5 bg-gradient-to-r from-yellow-500 to-orange-500 text-white text-sm font-bold rounded-lg hover:from-yellow-600 hover:to-orange-600 transition-all shadow-lg hover:shadow-xl"
            >
              {isLoggedIn ? 'Upgrade to Ultra' : 'Sign in to Upgrade'}
            </button>
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
                How does the revenue share work?
                <span className="ml-2 text-gray-500 group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <p className="mt-2 text-gray-600 p-4">
                As a Pro user, you keep 100% of all subscription revenue from your marketplace bots. No platform fees - you earn everything your bots generate!
              </p>
            </details>
          </div>
        </div>
      </div>

      {/* Upgrade Modal */}
      <UpgradeModal 
        isOpen={showUpgradeModal}
        onClose={() => setShowUpgradeModal(false)}
        targetPlan={targetPlan}
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

