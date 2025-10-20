'use client'

import { useAuthGuard } from '@/hooks/useAuthGuard'
import { UserRole } from '@/lib/types'
import {
  ChartBarIcon,
  UserGroupIcon,
  CpuChipIcon,
  FlagIcon,
  ArrowTrendingUpIcon,
  ClockIcon,
} from '@heroicons/react/24/outline'
import Link from 'next/link'

export default function AdminDashboardPage() {
  const { user, loading } = useAuthGuard({ 
    requireAuth: true, 
    requiredRole: UserRole.ADMIN 
  })

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyber-400"></div>
      </div>
    )
  }

  const stats = [
    {
      name: 'Total Users',
      value: '1,234',
      change: '+12%',
      changeType: 'positive',
      icon: UserGroupIcon,
      href: '/admin/users',
    },
    {
      name: 'Active Bots',
      value: '567',
      change: '+8%',
      changeType: 'positive',
      icon: CpuChipIcon,
      href: '/admin/bots',
    },
    {
      name: 'Feature Flags',
      value: '5',
      change: '2 enabled',
      changeType: 'neutral',
      icon: FlagIcon,
      href: '/admin/feature-flags',
    },
    {
      name: 'System Health',
      value: '98%',
      change: 'Operational',
      changeType: 'positive',
      icon: ChartBarIcon,
      href: '/admin/analytics',
    },
  ]

  const quickActions = [
    {
      name: 'Manage Feature Flags',
      description: 'Control feature visibility across platform',
      icon: FlagIcon,
      href: '/admin/feature-flags',
      color: 'from-cyber-500 to-quantum-500',
    },
    {
      name: 'LLM Providers',
      description: 'Configure AI model providers',
      icon: CpuChipIcon,
      href: '/admin/llm-providers',
      color: 'from-purple-500 to-pink-500',
    },
    {
      name: 'User Management',
      description: 'View and manage user accounts',
      icon: UserGroupIcon,
      href: '/admin/users',
      color: 'from-green-500 to-emerald-500',
    },
  ]

  const recentActivity = [
    {
      action: 'Feature flag toggled',
      detail: 'marketplace_publish_bot enabled',
      time: '5 minutes ago',
      user: 'Admin',
    },
    {
      action: 'New user registered',
      detail: 'john.doe@example.com',
      time: '15 minutes ago',
      user: 'System',
    },
    {
      action: 'Bot approved',
      detail: 'Universal Futures Bot v2.0',
      time: '1 hour ago',
      user: 'Admin',
    },
  ]

  return (
    <div className="p-8 neural-grid">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold cyber-text mb-2">
            Admin Dashboard
          </h1>
          <p className="text-gray-400">
            Welcome back, {user?.username || 'Admin'}
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {stats.map((stat) => {
            const Icon = stat.icon
            return (
              <Link
                key={stat.name}
                href={stat.href}
                className="card-cyber p-6 hover:scale-105 transition-transform"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="p-3 bg-gradient-to-br from-cyber-500/20 to-quantum-500/20 rounded-lg">
                    <Icon className="h-6 w-6 text-cyber-400" />
                  </div>
                  <span
                    className={`text-sm font-medium ${
                      stat.changeType === 'positive'
                        ? 'text-green-400'
                        : stat.changeType === 'negative'
                        ? 'text-red-400'
                        : 'text-gray-400'
                    }`}
                  >
                    {stat.change}
                  </span>
                </div>
                <div>
                  <p className="text-sm text-gray-400 mb-1">{stat.name}</p>
                  <p className="text-2xl font-bold text-white">{stat.value}</p>
                </div>
              </Link>
            )
          })}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Quick Actions */}
          <div className="card-cyber p-6">
            <h2 className="text-xl font-bold text-white mb-4 flex items-center">
              <ArrowTrendingUpIcon className="h-6 w-6 mr-2 text-cyber-400" />
              Quick Actions
            </h2>
            <div className="space-y-3">
              {quickActions.map((action) => {
                const Icon = action.icon
                return (
                  <Link
                    key={action.name}
                    href={action.href}
                    className="block p-4 bg-dark-700 rounded-lg hover:bg-dark-600 transition-colors"
                  >
                    <div className="flex items-start gap-4">
                      <div className={`p-3 bg-gradient-to-br ${action.color} rounded-lg`}>
                        <Icon className="h-6 w-6 text-white" />
                      </div>
                      <div className="flex-1">
                        <h3 className="font-semibold text-white mb-1">
                          {action.name}
                        </h3>
                        <p className="text-sm text-gray-400">
                          {action.description}
                        </p>
                      </div>
                    </div>
                  </Link>
                )
              })}
            </div>
          </div>

          {/* Recent Activity */}
          <div className="card-cyber p-6">
            <h2 className="text-xl font-bold text-white mb-4 flex items-center">
              <ClockIcon className="h-6 w-6 mr-2 text-cyber-400" />
              Recent Activity
            </h2>
            <div className="space-y-4">
              {recentActivity.map((activity, index) => (
                <div
                  key={index}
                  className="flex items-start gap-4 pb-4 border-b border-gray-700 last:border-0 last:pb-0"
                >
                  <div className="p-2 bg-dark-700 rounded-lg">
                    <ClockIcon className="h-5 w-5 text-gray-400" />
                  </div>
                  <div className="flex-1">
                    <p className="text-white font-medium">{activity.action}</p>
                    <p className="text-sm text-gray-400">{activity.detail}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-gray-500">
                        {activity.time}
                      </span>
                      <span className="text-xs text-gray-600">•</span>
                      <span className="text-xs text-gray-500">
                        by {activity.user}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* System Status */}
        <div className="mt-6 card-cyber p-6">
          <h2 className="text-xl font-bold text-white mb-4">System Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-dark-700 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-400">Database</span>
                <span className="px-2 py-1 text-xs bg-green-900/20 text-green-400 rounded-full">
                  Healthy
                </span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-white">98%</span>
                <span className="text-sm text-gray-500">uptime</span>
              </div>
            </div>

            <div className="p-4 bg-dark-700 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-400">API Response</span>
                <span className="px-2 py-1 text-xs bg-green-900/20 text-green-400 rounded-full">
                  Fast
                </span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-white">125ms</span>
                <span className="text-sm text-gray-500">avg</span>
              </div>
            </div>

            <div className="p-4 bg-dark-700 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-400">Background Jobs</span>
                <span className="px-2 py-1 text-xs bg-green-900/20 text-green-400 rounded-full">
                  Running
                </span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-white">12</span>
                <span className="text-sm text-gray-500">active</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

