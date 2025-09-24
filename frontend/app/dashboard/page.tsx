'use client'

import { useAuthGuard } from '@/hooks/useAuthGuard'
import { UserRole } from '@/lib/types'
import Link from 'next/link'
import { 
  ChartBarIcon, 
  CpuChipIcon, 
  UserGroupIcon, 
  PlusIcon,
  CogIcon,
  ShieldCheckIcon
} from '@heroicons/react/24/outline'

export default function DashboardPage() {
  const { user, loading } = useAuthGuard({ requireAuth: true })

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center neural-grid">
        <div className="card-quantum p-8 text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-quantum-500 mx-auto mb-4"></div>
          <p className="text-gray-300">Initializing Neural Interface...</p>
        </div>
      </div>
    )
  }

  if (!user) {
    return null
  }

  const quickActions = [
    {
      name: '🔍 Scan Arsenal',
      description: 'Analyze existing AI entities and their capabilities',
      href: '/arsenal',
      icon: ChartBarIcon,
      gradient: 'from-cyber-500 to-blue-600',
    },
    {
      name: '⚙️ Neural Profile',
      description: 'Configure your neural interface settings',
      href: '/profile',
      icon: CogIcon,
      gradient: 'from-dark-600 to-gray-600',
    },
  ]

  const creatorActions = [
    {
      name: '🧠 Forge Entity',
      description: 'Create a new autonomous trading AI',
      href: '/creator/forge',
      icon: PlusIcon,
      gradient: 'from-neural-500 to-green-600',
    },
    {
      name: '⚡ My AI Entities',
      description: 'Command your AI army',
      href: '/creator/entities',
      icon: CpuChipIcon,
      gradient: 'from-quantum-500 to-purple-600',
    },
  ]

  const adminActions = [
    {
      name: '🔐 System Override',
      description: 'Control all AI entities in the network',
      href: '/admin/override',
      icon: ShieldCheckIcon,
      gradient: 'from-danger-500 to-red-600',
    },
    {
      name: '👥 User Matrix',
      description: 'Manage neural network participants',
      href: '/admin/matrix',
      icon: UserGroupIcon,
      gradient: 'from-yellow-500 to-orange-600',
    },
  ]

  const getActionsForUser = () => {
    let actions = [...quickActions]
    
    if (user.role === UserRole.DEVELOPER || user.role === UserRole.ADMIN) {
      actions = [...actions, ...creatorActions]
    }
    
    if (user.role === UserRole.ADMIN) {
      actions = [...actions, ...adminActions]
    }
    
    return actions
  }

  const actions = getActionsForUser()

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      {/* Welcome Section */}
      <div className="card-quantum mb-8 animate-fade-in">
        <div className="px-4 py-5 sm:p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="h-12 w-12 rounded-full bg-gradient-to-r from-quantum-600 to-cyber-600 flex items-center justify-center animate-neural-pulse">
                <span className="text-white font-bold text-lg">
                  {(user.developer_name || user.email).charAt(0).toUpperCase()}
                </span>
              </div>
            </div>
            <div className="ml-4">
              <h1 className="text-2xl font-bold cyber-text">
                Neural Link Active: {user.developer_name || user.email}
              </h1>
              <p className="text-gray-400 flex items-center">
                {user.role === UserRole.ADMIN && '🔐 System Architect - Full Access Granted'}
                {user.role === UserRole.DEVELOPER && '⚡ Bot Creator - Neural Forge Enabled'}
                {user.role === UserRole.USER && '🎯 Operator - Standard Interface Active'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Neural Statistics */}
      {(user.role === UserRole.DEVELOPER || user.role === UserRole.ADMIN) && (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
          <div className="card-cyber overflow-hidden animate-fade-in" style={{ animationDelay: '0.1s' }}>
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="p-2 rounded-lg bg-gradient-to-r from-quantum-500 to-purple-600">
                    <CpuChipIcon className="h-6 w-6 text-white" />
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-400 truncate">
                      🧠 AI Entities Forged
                    </dt>
                    <dd className="text-2xl font-bold cyber-text animate-neural-pulse">
                      {user.total_developed_bots || 0}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="card-cyber overflow-hidden animate-fade-in" style={{ animationDelay: '0.2s' }}>
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="p-2 rounded-lg bg-gradient-to-r from-neural-500 to-green-600">
                    <ShieldCheckIcon className="h-6 w-6 text-white" />
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-400 truncate">
                      ✅ Neural Network Approved
                    </dt>
                    <dd className="text-2xl font-bold text-neural-400 animate-neural-pulse">
                      {user.approved_bots || 0}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="card-cyber overflow-hidden animate-fade-in" style={{ animationDelay: '0.3s' }}>
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="p-2 rounded-lg bg-gradient-to-r from-cyber-500 to-blue-600">
                    <UserGroupIcon className="h-6 w-6 text-white" />
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-400 truncate">
                      👥 Neural Connections
                    </dt>
                    <dd className="text-2xl font-bold text-cyber-400 animate-neural-pulse">
                      {user.total_subscriptions || 0}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="card-cyber overflow-hidden animate-fade-in" style={{ animationDelay: '0.4s' }}>
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="p-2 rounded-lg bg-gradient-to-r from-yellow-500 to-orange-600">
                    <ChartBarIcon className="h-6 w-6 text-white" />
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-400 truncate">
                      ⚡ Active Neural Links
                    </dt>
                    <dd className="text-2xl font-bold text-yellow-400 animate-neural-pulse">
                      {user.active_subscriptions || 0}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Neural Command Center */}
      <div className="card-quantum animate-fade-in" style={{ animationDelay: '0.5s' }}>
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium cyber-text mb-6 flex items-center">
            ⚡ Neural Command Center
            <span className="ml-2 w-2 h-2 bg-neural-500 rounded-full animate-neural-pulse"></span>
          </h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {actions.map((action, index) => (
              <Link
                key={action.name}
                href={action.href}
                className="relative group card-cyber p-6 focus-within:ring-2 focus-within:ring-inset focus-within:ring-quantum-500 hover:shadow-2xl hover:shadow-quantum-500/20 transition-all duration-300 transform hover:-translate-y-1 animate-fade-in"
                style={{ animationDelay: `${0.6 + index * 0.1}s` }}
              >
                <div>
                  <span className={`rounded-lg inline-flex p-3 bg-gradient-to-r ${action.gradient} text-white shadow-lg`}>
                    <action.icon className="h-6 w-6" aria-hidden="true" />
                  </span>
                </div>
                <div className="mt-4">
                  <h3 className="text-lg font-medium text-gray-200">
                    <span className="absolute inset-0" aria-hidden="true" />
                    {action.name}
                  </h3>
                  <p className="mt-2 text-sm text-gray-400">
                    {action.description}
                  </p>
                </div>
                <span
                  className="pointer-events-none absolute top-6 right-6 text-gray-500 group-hover:text-quantum-400 transition-colors duration-300"
                  aria-hidden="true"
                >
                  <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                    <path d="m11.293 17.293 1.414 1.414L19.414 12l-6.707-6.707-1.414 1.414L15.586 11H6v2h9.586l-4.293 4.293z" />
                  </svg>
                </span>
              </Link>
            ))}
          </div>
        </div>
      </div>

      {/* Neural Activity Monitor */}
      <div className="card-cyber mt-8 animate-fade-in" style={{ animationDelay: '1s' }}>
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium cyber-text mb-6 flex items-center">
            📊 Neural Activity Monitor
            <span className="ml-2 w-2 h-2 bg-cyber-500 rounded-full animate-neural-pulse" style={{ animationDelay: '1s' }}></span>
          </h3>
          <div className="text-center py-12 text-gray-400">
            <div className="relative mx-auto h-16 w-16 mb-4">
              <ChartBarIcon className="h-16 w-16 text-gray-600 animate-neural-pulse" />
              <div className="absolute inset-0 bg-gradient-to-r from-quantum-500/20 to-cyber-500/20 rounded-full blur-xl"></div>
            </div>
            <p className="text-gray-300 font-medium">Neural Network Initializing...</p>
            <p className="text-sm mt-1 text-gray-500">Begin by forging your first AI entity or scanning the arsenal</p>
            <div className="mt-6 flex justify-center space-x-4">
              <Link 
                href="/creator/forge" 
                className="btn btn-primary px-6 py-2 text-sm"
              >
                🧠 Forge Entity
              </Link>
              <Link 
                href="/arsenal" 
                className="btn btn-secondary px-6 py-2 text-sm"
              >
                🔍 Scan Arsenal
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

