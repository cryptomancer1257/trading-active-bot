'use client'

import { useEffect, useState } from 'react'
import QuotaTopUpModal from './QuotaTopUpModal'
import { toast } from 'react-hot-toast'

/**
 * Global handler for quota exceeded events
 * Listens to 'quota-exceeded' events dispatched by API interceptor
 * and shows top-up modal automatically
 */
export default function GlobalQuotaHandler() {
  const [showTopUpModal, setShowTopUpModal] = useState(false)

  useEffect(() => {
    const handleQuotaExceeded = (event: any) => {
      const { message, endpoint } = event.detail || {}
      
      console.warn('🚨 Global Quota Exceeded Handler triggered', { message, endpoint })
      
      // Show toast notification
      toast.error(
        message || 'LLM quota exceeded. Please purchase more quota to continue.',
        {
          duration: 5000,
          icon: '🚨',
        }
      )
      
      // Open top-up modal
      setShowTopUpModal(true)
    }

    // Listen for quota-exceeded events
    window.addEventListener('quota-exceeded', handleQuotaExceeded)

    return () => {
      window.removeEventListener('quota-exceeded', handleQuotaExceeded)
    }
  }, [])

  return (
    <QuotaTopUpModal 
      isOpen={showTopUpModal}
      onClose={() => setShowTopUpModal(false)}
    />
  )
}

