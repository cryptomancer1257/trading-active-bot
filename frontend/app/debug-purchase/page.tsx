'use client'

import { useState } from 'react'
import QuotaTopUpModal from '@/components/QuotaTopUpModal'

/**
 * Debug page for purchase flow
 * Access at: /debug-purchase
 */
export default function DebugPurchasePage() {
  const [showModal, setShowModal] = useState(false)
  const [debugInfo, setDebugInfo] = useState<any>({})

  const checkAuthStatus = () => {
    const token = localStorage.getItem('token')
    const user = localStorage.getItem('user')
    
    setDebugInfo({
      hasToken: !!token,
      tokenValue: token ? `${token.substring(0, 20)}...` : 'null',
      hasUser: !!user,
      userValue: user ? JSON.parse(user) : null,
      isDemoMode: !token || token === 'null'
    })
  }

  const simulateLogin = () => {
    localStorage.setItem('token', 'fake-jwt-token-for-testing')
    localStorage.setItem('user', JSON.stringify({
      id: 1,
      email: 'test@example.com',
      role: 'DEVELOPER'
    }))
    checkAuthStatus()
  }

  const simulateLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    checkAuthStatus()
  }

  return (
    <div className="min-h-screen bg-dark-900 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-white mb-4">
            🐛 Purchase Debug Page
          </h1>
          <p className="text-gray-400">
            Debug the purchase flow and authentication
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Auth Status */}
          <div className="bg-dark-800/60 rounded-xl p-6">
            <h2 className="text-2xl font-bold text-white mb-4">Authentication Status</h2>
            
            <div className="space-y-4">
              <div className="p-4 bg-gray-800 rounded-lg">
                <h3 className="text-white font-semibold mb-2">Current Status:</h3>
                <div className="space-y-2 text-sm">
                  <p className="text-gray-300">
                    Token: {debugInfo.hasToken ? '✅ Present' : '❌ Missing'}
                  </p>
                  <p className="text-gray-300">
                    User: {debugInfo.hasUser ? '✅ Present' : '❌ Missing'}
                  </p>
                  <p className="text-gray-300">
                    Mode: {debugInfo.isDemoMode ? '🎭 Demo' : '🔐 Authenticated'}
                  </p>
                </div>
              </div>

              <div className="flex space-x-3">
                <button
                  onClick={checkAuthStatus}
                  className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm"
                >
                  🔍 Check Status
                </button>
                
                <button
                  onClick={simulateLogin}
                  className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg text-sm"
                >
                  🔐 Simulate Login
                </button>
                
                <button
                  onClick={simulateLogout}
                  className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg text-sm"
                >
                  🚪 Simulate Logout
                </button>
              </div>
            </div>
          </div>

          {/* Purchase Test */}
          <div className="bg-dark-800/60 rounded-xl p-6">
            <h2 className="text-2xl font-bold text-white mb-4">Purchase Test</h2>
            
            <div className="space-y-4">
              <p className="text-gray-400 text-sm">
                Test the purchase flow with different authentication states
              </p>
              
              <button
                onClick={() => setShowModal(true)}
                className="w-full px-4 py-3 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white rounded-lg font-semibold text-sm transition-all transform hover:scale-105"
              >
                💎 Test Purchase Modal
              </button>
            </div>
          </div>
        </div>

        {/* Debug Info */}
        {Object.keys(debugInfo).length > 0 && (
          <div className="mt-8">
            <h2 className="text-2xl font-bold text-white mb-4">Debug Information</h2>
            <div className="bg-dark-800/60 rounded-xl p-6">
              <pre className="text-green-400 text-sm overflow-auto">
                {JSON.stringify(debugInfo, null, 2)}
              </pre>
            </div>
          </div>
        )}

        {/* Instructions */}
        <div className="mt-8">
          <h2 className="text-2xl font-bold text-white mb-4">Debug Instructions</h2>
          <div className="bg-dark-800/60 rounded-xl p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-white font-semibold mb-2">🔧 Testing Steps</h3>
                <div className="space-y-2 text-sm text-gray-300">
                  <p>1. <strong>Check Status:</strong> See current auth state</p>
                  <p>2. <strong>Simulate Login:</strong> Set fake token for testing</p>
                  <p>3. <strong>Test Purchase:</strong> Open modal and try purchase</p>
                  <p>4. <strong>Check Console:</strong> Look for debug logs</p>
                </div>
              </div>
              
              <div>
                <h3 className="text-white font-semibold mb-2">🎯 Expected Behavior</h3>
                <div className="space-y-2 text-sm text-gray-300">
                  <p>✅ <strong>Demo Mode:</strong> Simulates purchase in 2s</p>
                  <p>✅ <strong>Auth Mode:</strong> Calls real PayPal API</p>
                  <p>✅ <strong>Console Logs:</strong> Shows debug information</p>
                  <p>✅ <strong>Error Handling:</strong> Shows clear error messages</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Modal */}
      <QuotaTopUpModal 
        isOpen={showModal}
        onClose={() => setShowModal(false)}
      />
    </div>
  )
}
