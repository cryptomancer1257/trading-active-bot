'use client'

import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'

/**
 * PayPal cancel page
 * Access at: /quota-cancel?token=...
 */
export default function QuotaCancelPage() {
  const searchParams = useSearchParams()
  const [token, setToken] = useState<string | null>(null)

  useEffect(() => {
    const paymentToken = searchParams.get('token')
    setToken(paymentToken)
    
    console.log('❌ PayPal Cancel Page')
    console.log('Token:', paymentToken)
  }, [searchParams])

  return (
    <div className="min-h-screen bg-dark-900 flex items-center justify-center">
      <div className="max-w-md mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-dark-800/60 rounded-xl p-8 text-center">
          <div className="text-6xl mb-4">🚫</div>
          <h1 className="text-2xl font-bold text-yellow-400 mb-2">Payment Cancelled</h1>
          <p className="text-gray-300 mb-4">
            You cancelled the payment process. No charges have been made.
          </p>
          
          {token && (
            <div className="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-4 mb-4">
              <p className="text-yellow-300 text-sm">
                Payment Token: {token}
              </p>
            </div>
          )}
          
          <div className="space-y-3">
            <button
              onClick={() => window.location.href = '/dashboard#quota'}
              className="w-full px-4 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-semibold"
            >
              💎 Try Purchase Again
            </button>
            
            <button
              onClick={() => window.location.href = '/dashboard'}
              className="w-full px-4 py-3 bg-gray-600 hover:bg-gray-700 text-white rounded-lg"
            >
              🏠 Go to Dashboard
            </button>
          </div>
          
          <div className="mt-6 text-sm text-gray-500">
            <p>💡 You can purchase quota anytime from your dashboard</p>
          </div>
        </div>
      </div>
    </div>
  )
}
