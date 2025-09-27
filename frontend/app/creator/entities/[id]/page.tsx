'use client'

import { useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { 
  ArrowLeftIcon,
  PencilIcon,
  Cog6ToothIcon,
  SparklesIcon,
  ChartBarIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'
import { CheckCircleIcon, ClockIcon, XCircleIcon, ArchiveBoxIcon } from '@heroicons/react/24/solid'
import Link from 'next/link'
import BotPromptsTab from '@/components/BotPromptsTab'

type TabType = 'overview' | 'prompts' | 'settings' | 'analytics'

export default function BotDetailPage() {
  const router = useRouter()
  const params = useParams()
  const botId = params?.id as string

  const [activeTab, setActiveTab] = useState<TabType>('overview')

  // Mock bot data for testing
  const bot = {
    id: parseInt(botId || '48'),
    name: '🚀 Futures Quantum Entity',
    description: 'Advanced futures trading with LLM AI analysis, leverage, and quantum risk management',
    bot_type: 'FUTURES',
    version: '1.0.0',
    status: 'APPROVED',
    exchange_type: 'BINANCE',
    trading_pair: 'BTC/USDT',
    timeframe: '1h',
    leverage: 10,
    created_at: '2025-09-27T08:39:45'
  }

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-white">{bot.name}</h2>
            <p className="text-gray-300">{bot.description}</p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-gray-800 p-4 rounded-lg shadow-md border border-gray-700">
                <h3 className="text-lg font-semibold text-purple-400 mb-2">Basic Info</h3>
                <p className="text-gray-300"><strong>Type:</strong> {bot.bot_type}</p>
                <p className="text-gray-300"><strong>Version:</strong> {bot.version}</p>
                <p className="text-gray-300"><strong>Status:</strong> {bot.status}</p>
                <p className="text-gray-300"><strong>Created:</strong> {new Date(bot.created_at).toLocaleDateString()}</p>
              </div>

              <div className="bg-gray-800 p-4 rounded-lg shadow-md border border-gray-700">
                <h3 className="text-lg font-semibold text-purple-400 mb-2">Trading Parameters</h3>
                <p className="text-gray-300"><strong>Exchange:</strong> {bot.exchange_type}</p>
                <p className="text-gray-300"><strong>Pair:</strong> {bot.trading_pair}</p>
                <p className="text-gray-300"><strong>Timeframe:</strong> {bot.timeframe}</p>
                <p className="text-gray-300"><strong>Leverage:</strong> {bot.leverage}x</p>
              </div>
            </div>
          </div>
        )
      case 'settings':
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-white">Bot Settings</h2>
            <p className="text-gray-300">Manage advanced configurations for your bot.</p>
            <Link href={`/creator/entities/${bot.id}/edit`} className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500">
              <Cog6ToothIcon className="-ml-1 mr-2 h-5 w-5" />
              Edit Bot Configuration
            </Link>
          </div>
        )
      case 'prompts':
        return <BotPromptsTab botId={bot.id} />
      case 'analytics':
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-white">Analytics</h2>
            <p className="text-gray-300">Bot performance metrics and analytics.</p>
            <div className="bg-gray-800 p-6 rounded-lg">
              <p className="text-gray-400">Analytics coming soon...</p>
            </div>
          </div>
        )
      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <Link href="/creator/entities" className="inline-flex items-center text-purple-400 hover:text-purple-300">
            <ArrowLeftIcon className="h-5 w-5 mr-2" />
            Back to My Entities
          </Link>
          <h1 className="text-3xl font-extrabold text-white">{bot.name}</h1>
          <div className="w-10"></div> {/* Spacer */}
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-700 mb-6">
          <nav className="-mb-px flex space-x-8" aria-label="Tabs">
            <button
              onClick={() => setActiveTab('overview')}
              className={`whitespace-nowrap py-3 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'overview'
                  ? 'border-purple-500 text-purple-400'
                  : 'border-transparent text-gray-400 hover:text-gray-200 hover:border-gray-300'
              }`}
            >
              <SparklesIcon className="h-5 w-5 inline-block mr-2" />
              Overview
            </button>
            <button
              onClick={() => setActiveTab('prompts')}
              className={`whitespace-nowrap py-3 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'prompts'
                  ? 'border-purple-500 text-purple-400'
                  : 'border-transparent text-gray-400 hover:text-gray-200 hover:border-gray-300'
              }`}
            >
              <DocumentTextIcon className="h-5 w-5 inline-block mr-2" />
              Prompts
            </button>
            <button
              onClick={() => setActiveTab('settings')}
              className={`whitespace-nowrap py-3 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'settings'
                  ? 'border-purple-500 text-purple-400'
                  : 'border-transparent text-gray-400 hover:text-gray-200 hover:border-gray-300'
              }`}
            >
              <Cog6ToothIcon className="h-5 w-5 inline-block mr-2" />
              Settings
            </button>
            <button
              onClick={() => setActiveTab('analytics')}
              className={`whitespace-nowrap py-3 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'analytics'
                  ? 'border-purple-500 text-purple-400'
                  : 'border-transparent text-gray-400 hover:text-gray-200 hover:border-gray-300'
              }`}
            >
              <ChartBarIcon className="h-5 w-5 inline-block mr-2" />
              Analytics
            </button>
          </nav>
        </div>

        {/* Content based on active tab */}
        {renderContent()}
      </div>
    </div>
  )
}