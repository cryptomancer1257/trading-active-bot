'use client'

import { useState, useEffect } from 'react'
import api from '@/lib/api'

export default function BackendStatus() {
  const [status, setStatus] = useState<'checking' | 'online' | 'offline'>('checking')
  const [lastCheck, setLastCheck] = useState<Date | null>(null)

  const checkBackend = async () => {
    setStatus('checking')
    try {
      await api.get('/health')
      setStatus('online')
      setLastCheck(new Date())
    } catch (error) {
      setStatus('offline')
      setLastCheck(new Date())
    }
  }

  useEffect(() => {
    checkBackend()
    const interval = setInterval(checkBackend, 60000) // Check every 60 seconds (less frequent)
    return () => clearInterval(interval)
  }, [])

  const getStatusColor = () => {
    switch (status) {
      case 'online': return 'text-neural-400 bg-neural-500/10'
      case 'offline': return 'text-danger-400 bg-danger-500/10'
      case 'checking': return 'text-yellow-400 bg-yellow-500/10'
      default: return 'text-gray-400 bg-gray-500/10'
    }
  }

  const getStatusIcon = () => {
    switch (status) {
      case 'online': return '🟢'
      case 'offline': return '🔴'
      case 'checking': return '🟡'
      default: return '⚫'
    }
  }

  return (
    <div className="fixed bottom-4 right-4 z-50">
      <div className={`px-3 py-2 rounded-full text-xs font-medium ${getStatusColor()} backdrop-blur-sm border border-current/20`}>
        <div className="flex items-center space-x-2">
          <span>{getStatusIcon()}</span>
          <span>Backend: {status}</span>
          <button 
            onClick={checkBackend}
            className="ml-2 hover:opacity-70 transition-opacity"
            title="Refresh status"
          >
            🔄
          </button>
        </div>
        {lastCheck && (
          <div className="text-xs opacity-60 mt-1">
            Last check: {lastCheck.toLocaleTimeString()}
          </div>
        )}
      </div>
    </div>
  )
}
