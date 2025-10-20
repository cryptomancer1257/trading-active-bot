'use client'

import { Suspense, useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { api } from '@/lib/api'

/**
 * PayPal success page content component
 */
function QuotaSuccessContent() {
  const searchParams = useSearchParams()
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [message, setMessage] = useState('')

  // Wrap useSearchParams usage in effect guarded by Suspense detection
  useEffect(() => {
    // In case this page is statically generated, guard against undefined
    const token = searchParams?.get('token')
    const payerId = searchParams?.get('PayerID')

    if (token && payerId) {
      completePurchase(token, payerId)
    } else {
      setStatus('error')
      setMessage('Invalid payment parameters. Please try again.')
    }
  }, [searchParams])

  const completePurchase = async (token: string, payerId: string) => {
    try {
      console.log('🔄 Completing purchase...')
      
      // Call backend API to complete purchase
      // The backend will verify PayPal payment and add quota
      const response = await api.post('/quota-topups/complete-paypal-purchase', {
        token,
        payer_id: payerId
      })
      
      console.log('✅ Purchase completed:', response.data)
      
      setStatus('success')
      setMessage('Payment completed successfully! Your quota has been added.')
      
      // Redirect to dashboard after 3 seconds
      setTimeout(() => {
        window.location.href = '/dashboard'
      }, 3000)
    } catch (error: any) {
      console.error('❌ Purchase completion failed:', error)
      setStatus('error')
      setMessage(error.response?.data?.detail || 'Failed to complete purchase. Please contact support.')
    }
  }

  return (
    <div className="min-h-screen bg-dark-900 flex items-center justify-center">
      <div className="max-w-md mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-dark-800/60 rounded-xl p-8 text-center">
          {status === 'loading' && (
            <>
              <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-600 mx-auto mb-4"></div>
              <h1 className="text-2xl font-bold text-white mb-2">Processing Payment...</h1>
              <p className="text-gray-400">Please wait while we verify your payment</p>
            </>
          )}
          
          {status === 'success' && (
            <>
              <div className="text-6xl mb-4">🎉</div>
              <h1 className="text-2xl font-bold text-green-400 mb-2">Payment Successful!</h1>
              <p className="text-gray-300 mb-4">{message}</p>
              <div className="bg-green-900/20 border border-green-500/30 rounded-lg p-4 mb-4">
                <p className="text-green-300 text-sm">
                  ✅ Your LLM quota has been added to your account
                </p>
                <p className="text-green-300 text-sm">
                  🔄 Redirecting to dashboard in 3 seconds...
                </p>
              </div>
            </>
          )}
          
          {status === 'error' && (
            <>
              <div className="text-6xl mb-4">❌</div>
              <h1 className="text-2xl font-bold text-red-400 mb-2">Payment Error</h1>
              <p className="text-gray-300 mb-4">{message}</p>
              <div className="flex space-x-3">
                <button
                  onClick={() => window.location.href = '/dashboard'}
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg"
                >
                  Go to Dashboard
                </button>
                <button
                  onClick={() => window.location.href = '/dashboard#quota'}
                  className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg"
                >
                  Try Again
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

/**
 * PayPal success page
 * Access at: /quota-success?token=...&PayerID=...
 */
export default function QuotaSuccessPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-dark-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-600"></div>
      </div>
    }>
      <QuotaSuccessContent />
    </Suspense>
  )
}
