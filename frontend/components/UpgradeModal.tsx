'use client'

import { useState } from 'react'
import { usePlan } from '@/hooks/usePlan'
import { PayPalButtons, PayPalScriptProvider } from '@paypal/react-paypal-js'

interface UpgradeModalProps {
  isOpen: boolean
  onClose: () => void
  targetPlan?: 'pro' | 'ultra' // Default to 'pro' for backward compatibility
}

export default function UpgradeModal({ isOpen, onClose, targetPlan = 'pro' }: UpgradeModalProps) {
  const { planConfigs, upgradeToPro } = usePlan()
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  if (!isOpen) return null

  // Plan configuration
  const isPro = targetPlan === 'pro'
  const planPrice = isPro ? 60 : 500
  const planName = isPro ? 'Pro' : 'Ultra'
  const planIcon = isPro ? '⚡' : '💎'
  const planGradient = isPro 
    ? 'from-purple-500 to-pink-500' 
    : 'from-yellow-500 to-orange-500'
  const planBgGradient = isPro
    ? 'from-purple-50 to-pink-50'
    : 'from-yellow-50 to-orange-50'
  const planBorder = isPro ? 'border-purple-200' : 'border-yellow-200'

  const handlePayPalApprove = async (data: any) => {
    setIsProcessing(true)
    setError(null)

    try {
      await upgradeToPro.mutateAsync(data.orderID)
      setSuccess(true)
      
      setTimeout(() => {
        onClose()
      }, 2000)
    } catch (err: any) {
      setError(err.message || 'Failed to upgrade plan')
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      ></div>

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-2 sm:p-4">
        <div className="relative bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[95vh] overflow-y-auto p-4 sm:p-6 md:p-8">
          {/* Close button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 text-2xl"
          >
            ×
          </button>

          {success ? (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">🎉</div>
              <h3 className="text-2xl font-bold text-green-600 mb-2">Welcome to {planName}!</h3>
              <p className="text-gray-600">Your plan has been upgraded successfully</p>
            </div>
          ) : (
            <>
              {/* Header */}
              <div className="text-center mb-4">
                <div className={`inline-flex items-center justify-center w-14 h-14 bg-gradient-to-r ${planGradient} rounded-full mb-3`}>
                  <span className="text-2xl">{planIcon}</span>
                </div>
                <h2 className="text-xl md:text-2xl font-bold text-gray-900 mb-1">Upgrade to {planName} - ${planPrice}/month</h2>
                <p className="text-xs md:text-sm text-gray-600">Unlock {isPro ? 'unlimited' : 'ultimate'} potential</p>
              </div>

              {/* Benefits (Dynamic based on plan) */}
              <div className={`bg-gradient-to-br ${planBgGradient} border-2 ${planBorder} rounded-lg p-4 mb-4`}>
                <div className="flex flex-col gap-2 text-xs md:text-sm">
                  <div className="flex items-center text-gray-900 font-medium">
                    <span className="mr-2 text-green-500">✓</span>
                    {isPro ? '20 bots' : '♾️ Unlimited bots'}
                  </div>
                  <div className="flex items-center text-gray-900 font-medium">
                    <span className="mr-2 text-green-500">✓</span>
                    Mainnet access
                  </div>
                  <div className="flex items-center text-gray-900 font-medium">
                    <span className="mr-2 text-green-500">✓</span>
                    Publish to marketplace
                  </div>
                  {!isPro && (
                    <>
                      <div className="flex items-center text-gray-900 font-medium">
                        <span className="mr-2 text-green-500">✓</span>
                        2,400 API calls per day
                      </div>
                      <div className="flex items-center text-gray-900 font-medium">
                        <span className="mr-2 text-green-500">✓</span>
                        24/7 Dedicated support
                      </div>
                    </>
                  )}
                </div>
              </div>

              {/* Error */}
              {error && (
                <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
                  {error}
                </div>
              )}

              {/* PayPal Payment */}
              <div className="border-t pt-3">
                <h3 className="font-semibold text-gray-900 mb-2 text-center text-sm">Complete Payment</h3>
                
                {isProcessing ? (
                  <div className="flex items-center justify-center py-4">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-500 mr-2"></div>
                    <span className="text-xs text-gray-600">Processing...</span>
                  </div>
                ) : (
                  <PayPalScriptProvider
                    options={{
                      clientId: process.env.NEXT_PUBLIC_PAYPAL_CLIENT_ID || 'test',
                      currency: 'USD'
                    }}
                  >
                    <PayPalButtons
                      createOrder={(data, actions) => {
                        return actions.order.create({
                          purchase_units: [{
                            amount: {
                              value: '10.00',
                              currency_code: 'USD'
                            },
                            description: 'QuantumForge Pro Plan - Monthly Subscription'
                          }]
                        })
                      }}
                      onApprove={handlePayPalApprove}
                      onError={(err) => {
                        console.error('PayPal error:', err)
                        setError('Payment failed. Please try again.')
                      }}
                      style={{
                        layout: 'vertical',
                        color: 'gold',
                        shape: 'rect',
                        label: 'paypal',
                        height: 40
                      }}
                    />
                  </PayPalScriptProvider>
                )}
              </div>

              {/* Note */}
              <p className="text-center text-xs text-gray-500 mt-3">
                Cancel anytime • Secure payment via PayPal
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

