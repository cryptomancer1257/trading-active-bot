'use client'

import { useState } from 'react'
import { useQuotaPackages, useCreatePayPalOrder, usePurchaseQuota } from '@/hooks/useQuota'
import QuotaPackagesFallback from './QuotaPackagesFallback'

interface QuotaTopUpModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function QuotaTopUpModal({ isOpen, onClose }: QuotaTopUpModalProps) {
  const [selectedPackage, setSelectedPackage] = useState<string>('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  
  const { data: packages, isLoading: packagesLoading, error: packagesError } = useQuotaPackages()
  const createPayPalOrder = useCreatePayPalOrder()
  const purchaseQuota = usePurchaseQuota()

  if (!isOpen) return null

  const handlePackageSelect = (packageKey: string) => {
    console.log('📦 Package selected:', packageKey)
    setSelectedPackage(packageKey)
    setError(null)
  }

  const handlePurchase = async () => {
    if (!selectedPackage) {
      setError('Please select a package')
      return
    }

    setIsProcessing(true)
    setError(null)

    try {
      console.log('🛒 Starting purchase process for package:', selectedPackage)
      
      // Check if we're in demo mode (no authentication)
      const isDemoMode = !localStorage.getItem('token') || localStorage.getItem('token') === 'null'
      
      if (isDemoMode) {
        console.log('🎭 Demo mode: Simulating purchase')
        
        // Simulate demo purchase
        setTimeout(() => {
          setSuccess(true)
          setTimeout(() => {
            onClose()
            setSuccess(false)
            setSelectedPackage('')
          }, 2000)
          setIsProcessing(false)
        }, 2000)
        
        return
      }

      // Real PayPal flow
      console.log('💳 Creating PayPal order...')
      const orderResult = await createPayPalOrder.mutateAsync({
        package: selectedPackage
      })

      console.log('✅ PayPal order created:', orderResult)
      
      // Redirect to PayPal (works on all browsers including Safari)
      if (orderResult.approve_url) {
        console.log('🔄 Redirecting to PayPal...')
        // Store selected package for when user returns
        localStorage.setItem('pending_quota_package', selectedPackage)
        localStorage.setItem('pending_quota_order_id', orderResult.order_id)
        
        // Redirect to PayPal (instead of popup - works better on Safari)
        window.location.href = orderResult.approve_url
      } else {
        throw new Error('No PayPal approval URL received')
      }

    } catch (err: any) {
      console.error('❌ Purchase failed:', err)
      setError(err.message || 'Failed to create PayPal order')
      setIsProcessing(false)
    }
  }

  const getPackageIcon = (packageKey: string) => {
    const icons: Record<string, string> = {
      small: '📦',
      medium: '📦📦',
      large: '📦📦📦'
    }
    return icons[packageKey] || '📦'
  }

  const getPackageColor = (packageKey: string) => {
    const colors: Record<string, string> = {
      small: 'from-blue-500 to-blue-600',
      medium: 'from-purple-500 to-purple-600',
      large: 'from-orange-500 to-orange-600'
    }
    return colors[packageKey] || 'from-gray-500 to-gray-600'
  }

  if (success) {
    return (
      <div className="fixed inset-0 z-50 overflow-y-auto">
        <div className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"></div>
        <div className="flex min-h-full items-center justify-center p-4">
          <div className="relative bg-white rounded-2xl shadow-2xl max-w-md w-full p-8 text-center">
            <div className="text-6xl mb-4">🎉</div>
            <h3 className="text-2xl font-bold text-green-600 mb-2">Purchase Successful!</h3>
            <p className="text-gray-600">Your quota has been added to your account</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      ></div>

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[95vh] overflow-y-auto">
          {/* Header */}
          <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 rounded-t-2xl">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Buy Additional Trades Quota</h2>
                <p className="text-gray-600">Choose a package to get more Trade times</p>
              </div>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 text-2xl"
              >
                ×
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="p-6">
            {packagesLoading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto"></div>
                <p className="mt-2 text-gray-600">Loading packages...</p>
              </div>
            ) : packages ? (
              <>
                {/* Package Selection */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  {Object.entries(packages.packages).map(([key, pkg]) => (
                    <div
                      key={key}
                      className={`relative border-2 rounded-xl p-6 cursor-pointer transition-all ${
                        selectedPackage === key
                          ? 'border-purple-500 bg-purple-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                      onClick={() => handlePackageSelect(key)}
                    >
                      {selectedPackage === key && (
                        <div className="absolute top-2 right-2">
                          <div className="w-6 h-6 bg-purple-500 rounded-full flex items-center justify-center">
                            <span className="text-white text-sm">✓</span>
                          </div>
                        </div>
                      )}
                      
                      <div className="text-center">
                        <div className="text-4xl mb-3">{pkg.icon}</div>
                        <h3 className="text-xl font-bold text-gray-900 mb-2">{pkg.name}</h3>
                        <div className={`inline-block px-4 py-2 rounded-full text-white font-bold text-lg bg-gradient-to-r ${getPackageColor(key)}`}>
                          ${pkg.price}
                        </div>
                        <p className="text-gray-600 mt-2">{pkg.description}</p>
                        <div className="mt-3 text-sm text-gray-500">
                          +{pkg.quota} Trade times
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Error Message */}
                {error && (
                  <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
                    {error}
                  </div>
                )}

                {/* Purchase Button */}
                <div className="flex justify-center">
                  <button
                    onClick={handlePurchase}
                    disabled={!selectedPackage || isProcessing}
                    className={`px-8 py-3 rounded-lg font-bold text-white transition-all ${
                      selectedPackage && !isProcessing
                        ? 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 shadow-lg hover:shadow-purple-500/50 transform hover:scale-105'
                        : 'bg-gray-400 cursor-not-allowed'
                    }`}
                  >
                    {isProcessing ? (
                      <div className="flex items-center">
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                        Processing...
                      </div>
                    ) : (
                      `Purchase ${selectedPackage ? packages.packages[selectedPackage]?.name : 'Package'}`
                    )}
                  </button>
                </div>

                {/* Info */}
                <div className="mt-6 text-center text-sm text-gray-500">
                  <p>💳 Secure payment via PayPal</p>
                  <p>⚡ Quota added instantly after payment</p>
                  <p>🔄 Can be purchased multiple times</p>
                  
                  {/* Debug Info */}
                  <div className="mt-4 p-3 bg-gray-100 rounded-lg text-xs">
                    <p className="text-gray-600">
                      🔧 Debug: {!localStorage.getItem('access_token') || localStorage.getItem('access_token') === 'null' ? 'Demo Mode' : 'Authenticated'}
                    </p>
                    <p className="text-gray-600">
                      📦 Selected: {selectedPackage || 'None'}
                    </p>
                    {(!localStorage.getItem('access_token') || localStorage.getItem('access_token') === 'null') && (
                      <p className="text-yellow-600 font-semibold">
                        🎭 Demo Mode: Will open fake PayPal URL
                      </p>
                    )}
                  </div>
                </div>
              </>
            ) : packagesError ? (
              <div className="text-center py-8">
                <div className="text-4xl mb-4">⚠️</div>
                <h3 className="text-lg font-bold text-yellow-600 mb-2">Using Offline Packages</h3>
                <p className="text-gray-600 mb-4">
                  API temporarily unavailable. Using cached packages.
                </p>
                
                {/* Use fallback packages */}
                <QuotaPackagesFallback
                  onPackageSelect={handlePackageSelect}
                  selectedPackage={selectedPackage}
                  onPurchase={handlePurchase}
                  isProcessing={isProcessing}
                />
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="text-4xl mb-4">❓</div>
                <p className="text-gray-600">No packages available</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
