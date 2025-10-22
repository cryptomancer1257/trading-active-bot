'use client'

import { useState } from 'react'

interface QuotaPackage {
  name: string
  quota: number
  price: number
  description: string
  icon: string
}

interface QuotaPackagesFallbackProps {
  onPackageSelect: (packageKey: string) => void
  selectedPackage: string
  onPurchase: () => void
  isProcessing: boolean
}

// Fallback packages when API fails
const FALLBACK_PACKAGES: Record<string, QuotaPackage> = {
  small: {
    name: "Small Pack",
    quota: 500,
    price: 20.00,
    description: "500 additional Trade times",
    icon: "📦"
  },
  medium: {
    name: "Medium Pack", 
    quota: 1300,
    price: 50.00,
    description: "1300 additional Trade times",
    icon: "📦📦"
  },
  large: {
    name: "Large Pack",
    quota: 2800,
    price: 100.00,
    description: "2800 additional Trade times", 
    icon: "📦📦📦"
  }
}

export default function QuotaPackagesFallback({ 
  onPackageSelect, 
  selectedPackage, 
  onPurchase, 
  isProcessing 
}: QuotaPackagesFallbackProps) {
  const getPackageColor = (packageKey: string) => {
    const colors: Record<string, string> = {
      small: 'from-blue-500 to-blue-600',
      medium: 'from-purple-500 to-purple-600',
      large: 'from-orange-500 to-orange-600'
    }
    return colors[packageKey] || 'from-gray-500 to-gray-600'
  }

  return (
    <>
      {/* Package Selection */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {Object.entries(FALLBACK_PACKAGES).map(([key, pkg]) => (
          <div
            key={key}
            className={`relative border-2 rounded-xl p-6 cursor-pointer transition-all ${
              selectedPackage === key
                ? 'border-purple-500 bg-purple-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
            onClick={() => onPackageSelect(key)}
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

      {/* Purchase Button */}
      <div className="flex justify-center">
        <button
          onClick={onPurchase}
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
            `Purchase ${selectedPackage ? FALLBACK_PACKAGES[selectedPackage]?.name : 'Package'}`
          )}
        </button>
      </div>

      {/* Info */}
      <div className="mt-6 text-center text-sm text-gray-500">
        <p>💳 Secure payment via PayPal</p>
        <p>⚡ Quota added instantly after payment</p>
        <p>🔄 Can be purchased multiple times</p>
      </div>
    </>
  )
}
