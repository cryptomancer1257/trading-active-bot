'use client'

import { useAuthGuard } from '@/hooks/useAuthGuard'
import { UserRole } from '@/lib/types'
import { ChartBarIcon, CpuChipIcon } from '@heroicons/react/24/outline'

export default function AnalyticsPage() {
  const { user, loading } = useAuthGuard({ 
    requireAuth: true,
    requiredRole: UserRole.DEVELOPER 
  })

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center neural-grid">
        <div className="card-quantum p-8 text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-quantum-500 mx-auto mb-4"></div>
          <p className="text-gray-300">Loading Neural Analytics...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-extrabold cyber-text mb-4">
          📊 Neural Analytics
        </h1>
        <p className="text-xl text-gray-400">
          Deep analysis of your AI entities' performance and behavior patterns
        </p>
      </div>

      <div className="card-quantum p-12 text-center">
        <ChartBarIcon className="h-24 w-24 text-quantum-500 mx-auto mb-6 animate-neural-pulse" />
        <h2 className="text-2xl font-bold cyber-text mb-4">
          Analytics Matrix Initializing...
        </h2>
        <p className="text-gray-400 mb-6">
          Advanced neural analytics dashboard coming soon. Monitor your AI entities' 
          learning progress, trading patterns, and quantum performance metrics.
        </p>
        <div className="text-sm text-gray-500">
          🧠 Neural Pattern Analysis • 📈 Performance Metrics • ⚡ Real-time Monitoring
        </div>
      </div>
    </div>
  )
}
