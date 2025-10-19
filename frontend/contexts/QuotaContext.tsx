'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useQuotaUsage } from '@/hooks/useQuota'

interface QuotaContextType {
  remaining: number
  total: number
  used: number
  percentage: number
  isExhausted: boolean
  isLow: boolean // < 100 remaining
  isCritical: boolean // < 50 remaining
  canPurchase: boolean
  showTopUpModal: boolean
  setShowTopUpModal: (show: boolean) => void
  checkQuota: () => boolean // Returns false if quota exhausted
}

const QuotaContext = createContext<QuotaContextType | undefined>(undefined)

export function QuotaProvider({ children }: { children: ReactNode }) {
  const { data: quotaUsage, refetch } = useQuotaUsage()
  const [showTopUpModal, setShowTopUpModal] = useState(false)

  const remaining = quotaUsage?.remaining || 0
  const total = quotaUsage?.total || 0
  const used = quotaUsage?.used || 0
  const percentage = quotaUsage?.percentage || 0
  const canPurchase = quotaUsage?.can_purchase || false

  const isExhausted = remaining === 0
  const isLow = remaining < 100 && remaining > 0
  const isCritical = remaining < 50 && remaining > 0

  // Auto-trigger popup when quota is exhausted
  useEffect(() => {
    if (isExhausted && canPurchase) {
      setShowTopUpModal(true)
    }
  }, [isExhausted, canPurchase])

  const checkQuota = (): boolean => {
    if (isExhausted) {
      setShowTopUpModal(true)
      return false
    }
    return true
  }

  return (
    <QuotaContext.Provider
      value={{
        remaining,
        total,
        used,
        percentage,
        isExhausted,
        isLow,
        isCritical,
        canPurchase,
        showTopUpModal,
        setShowTopUpModal,
        checkQuota
      }}
    >
      {children}
    </QuotaContext.Provider>
  )
}

export function useQuotaContext() {
  const context = useContext(QuotaContext)
  if (context === undefined) {
    throw new Error('useQuotaContext must be used within a QuotaProvider')
  }
  return context
}

