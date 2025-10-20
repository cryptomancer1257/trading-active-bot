'use client'

import { useState } from 'react'
import Link from 'next/link'
import { CpuChipIcon, ShieldCheckIcon, RocketLaunchIcon, BoltIcon } from '@heroicons/react/24/outline'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { usePlan } from '@/hooks/usePlan'
import { useFeatureFlags } from '@/hooks/useFeatureFlags'
import PlanBadge from '@/components/PlanBadge'
import UpgradeModal from '@/components/UpgradeModal'
import QuotaUsageCard from '@/components/QuotaUsageCard'

const features = [
  {
    name: 'Neural Architecture',
    description: 'Advanced AI algorithms that learn, adapt, and evolve. Create autonomous entities capable of making split-second financial decisions.',
    icon: CpuChipIcon,
    gradient: 'from-quantum-500 to-purple-600',
  },
  {
    name: 'Quantum Security',
    description: 'Military-grade encryption and quantum-resistant security protocols. Your AI entities operate in complete stealth mode.',
    icon: ShieldCheckIcon,
    gradient: 'from-cyber-500 to-blue-600',
  },
  {
    name: 'Market Domination',
    description: 'Deploy your AI entities across global markets. Watch as they execute complex strategies with inhuman precision.',
    icon: RocketLaunchIcon,
    gradient: 'from-neural-500 to-green-600',
  },
  {
    name: 'Real-time Control',
    description: 'Command center interface for monitoring and controlling your AI army. Override decisions in real-time when needed.',
    icon: BoltIcon,
    gradient: 'from-yellow-500 to-orange-600',
  }
];

export default function HomePage() {
  const [showUpgradeModal, setShowUpgradeModal] = useState(false)
  const [targetPlan, setTargetPlan] = useState<'pro' | 'ultra'>('pro')
  const { currentPlan, limits, isPro, isFree } = usePlan()
  // Check if plan package is enabled via feature flags
  const { isPlanPackageEnabled, planPackageStatus, isLoadingPlanPackage, planPackageError } = useFeatureFlags()
  
  // Debug logging
  console.log('Feature Flag Debug:', {
    isPlanPackageEnabled,
    planPackageStatus,
    isLoadingPlanPackage,
    planPackageError
  })
  
  // Always show plan UI for now (remove feature flag dependency)
  const shouldShowPlanUI = true
  
  // Fetch real-time stats from API
  const { data: statsData, isLoading } = useQuery({
    queryKey: ['public-stats'],
    queryFn: async () => {
      const response = await api.get('/bots/stats')
      return response.data
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  // Format stats for display
  const stats = [
    { 
      name: 'AI Entities Created', 
      value: isLoading ? '...' : statsData?.total_bots?.toLocaleString() || '0', 
      suffix: '+' 
    },
    { 
      name: 'Active Deployments', 
      value: isLoading ? '...' : statsData?.total_subscriptions?.toLocaleString() || '0', 
      suffix: '' 
    },
    { 
      name: 'Average Rating', 
      value: isLoading ? '...' : statsData?.avg_rating || '0', 
      suffix: '/5 ⭐' 
    },
    { 
      name: 'Neural Architects', 
      value: isLoading ? '...' : statsData?.total_developers?.toLocaleString() || '∞', 
      suffix: '' 
    }
  ];

  return (
    <div className="relative">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-quantum-900/20 via-dark-900/50 to-cyber-900/20"></div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
          <div className="text-center">
            <div className="mb-8">
              <span className="inline-flex items-center px-4 py-2 rounded-full text-sm font-medium bg-gradient-to-r from-quantum-500/20 to-cyber-500/20 text-quantum-300 border border-quantum-500/30 backdrop-blur-sm">
                ⚡ Neural Network Active
              </span>
            </div>
            
            <h1 className="text-5xl md:text-7xl font-extrabold mb-6">
              <span className="block cyber-text glitch-effect" data-text="FORGE THE FUTURE">
                FORGE THE FUTURE
              </span>
              <span className="block text-gray-300 text-3xl md:text-5xl mt-4">
                of Autonomous Trading
              </span>
            </h1>
            
            <p className="mt-6 text-xl text-gray-400 max-w-3xl mx-auto leading-8">
              Enter the QuantumForge - where artificial intelligence transcends human limitations. 
              Create AI entities that don't just trade markets, they <span className="text-quantum-400 font-semibold">dominate</span> them.
            </p>
            
            <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href="/auth/register"
                className="btn btn-cyber px-8 py-4 text-lg font-semibold rounded-lg transform hover:scale-105 transition-all duration-300"
              >
                🧠 Initialize Neural Link
              </Link>
              <Link
                href="/arsenal"
                className="btn btn-secondary px-8 py-4 text-lg font-semibold rounded-lg border border-quantum-500/30 hover:border-quantum-400 transition-all duration-300"
              >
                🔍 Analyze Entities
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Plan Status Card - Only show if user is logged in AND plan package is enabled */}
      {currentPlan && limits && shouldShowPlanUI && (
        <div className="py-8 bg-dark-800/30">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className={`relative rounded-xl overflow-hidden ${
              isPro 
                ? 'bg-gradient-to-r from-purple-900/40 to-pink-900/40' 
                : limits.usage.can_create_bot
                ? 'bg-dark-800/60'
                : 'bg-gradient-to-r from-yellow-900/30 to-red-900/30'
            }`}>
              {/* Glowing border effect */}
              <div className={`absolute inset-0 rounded-xl border ${
                isPro 
                  ? 'border-purple-500/30' 
                  : limits.usage.can_create_bot 
                  ? 'border-quantum-500/20' 
                  : 'border-yellow-500/40'
              }`}></div>
              
              <div className="relative p-6">
                <div className="flex items-start justify-between gap-4">
                  {/* Left: Plan Badge + Info */}
                  <div className="flex items-start gap-4 flex-1 min-w-0">
                    <div className={`w-12 h-12 rounded-lg flex items-center justify-center flex-shrink-0 ${
                      isPro 
                        ? 'bg-gradient-to-br from-purple-500 to-pink-500' 
                        : limits.usage.can_create_bot
                        ? 'bg-dark-700/80'
                        : 'bg-yellow-600/80'
                    }`}>
                      <span className="text-2xl">
                        {isPro ? '⚡' : limits.usage.can_create_bot ? '🆓' : '⚠️'}
                      </span>
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="text-lg font-bold text-white">
                          {isPro ? 'Pro Plan' : 'Free Plan'}
                        </h3>
                        <PlanBadge />
                      </div>
                      
                      {/* Usage stats - separate row (only show if not at limit) */}
                      {!isPro && limits.usage.can_create_bot && (
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-gray-400 text-sm font-medium">
                            {limits.usage.total_bots}/{limits.plan.max_bots} Entities
                          </span>
                          <div className="w-32 bg-dark-700 rounded-full h-2">
                            <div 
                              className="h-2 rounded-full transition-all bg-quantum-500"
                              style={{ width: `${(limits.usage.total_bots / limits.plan.max_bots) * 100}%` }}
                            ></div>
                          </div>
                        </div>
                      )}
                      
                      {/* Features - only show for Pro plan */}
                      {isPro && (
                        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
                          <span className="text-green-400 flex items-center gap-1">
                            <span className="text-green-400">✓</span> Unlimited Entities
                          </span>
                          <span className="text-green-400 flex items-center gap-1">
                            <span className="text-green-400">✓</span> Mainnet
                          </span>
                          <span className="text-green-400 flex items-center gap-1">
                            <span className="text-green-400">✓</span> Unlimited Subscriptions
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Right: CTA Button */}
                  <div className="flex-shrink-0">
                    {isFree ? (
                      <button
                        onClick={() => {
                          setTargetPlan('pro')
                          setShowUpgradeModal(true)
                        }}
                        className="px-6 py-2.5 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold text-sm rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all shadow-lg hover:shadow-purple-500/50 transform hover:scale-105 whitespace-nowrap"
                      >
                        {limits.usage.can_create_bot ? 'Upgrade to Pro - $60/mo' : '⚡ Upgrade Now - $60/mo'}
                      </button>
                    ) : (
                      <Link
                        href="/plans"
                        className="px-6 py-2.5 border border-purple-400/60 text-purple-300 font-semibold text-sm rounded-lg hover:bg-purple-500/20 hover:border-purple-400 transition-all whitespace-nowrap"
                      >
                        Manage Plan
                      </Link>
                    )}
                  </div>
                </div>

                {/* Warning text for at-limit users */}
                {isFree && !limits.usage.can_create_bot && (
                  <div className="mt-3 pt-3 border-t border-yellow-500/20">
                    <p className="text-sm text-yellow-300/90 flex items-center gap-2">
                      <span>⚠️</span>
                      <span>Entity limit reached. Upgrade to Pro for unlimited entities and mainnet access.</span>
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Quota Usage Section - Only show for authenticated users */}
      {currentPlan && (
        <div className="py-8 bg-dark-800/20 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Quota Usage Card */}
              <div className="lg:col-span-1">
                <QuotaUsageCard />
              </div>
              
              {/* Additional Info Cards */}
              <div className="lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Plan Benefits */}
                <div className="bg-dark-800/60 rounded-xl p-6">
                  <div className="flex items-center mb-4">
                    <span className="text-2xl mr-3">💎</span>
                    <h3 className="text-white font-bold text-lg">Plan Benefits</h3>
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center text-gray-300">
                      <span className="mr-2">✓</span>
                      <span>Unlimited AI Entities</span>
                    </div>
                    <div className="flex items-center text-gray-300">
                      <span className="mr-2">✓</span>
                      <span>Mainnet Trading</span>
                    </div>
                    <div className="flex items-center text-gray-300">
                      <span className="mr-2">✓</span>
                      <span>Advanced Analytics</span>
                    </div>
                    <div className="flex items-center text-gray-300">
                      <span className="mr-2">✓</span>
                      <span>Priority Support</span>
                    </div>
                  </div>
                </div>

                {/* Usage Tips */}
                <div className="bg-dark-800/60 rounded-xl p-6">
                  <div className="flex items-center mb-4">
                    <span className="text-2xl mr-3">💡</span>
                    <h3 className="text-white font-bold text-lg">Usage Tips</h3>
                  </div>
                  <div className="space-y-2 text-sm text-gray-300">
                    <p>• Use signals bots for lower quota consumption</p>
                    <p>• Optimize bot frequency to reduce API calls</p>
                    <p>• Monitor quota usage regularly</p>
                    <p>• Purchase top-ups when needed</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Stats Section */}
      <div className="py-16 bg-dark-800/30 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
            {stats.map((stat) => (
              <div key={stat.name} className="text-center">
                <div className="text-4xl font-bold cyber-text animate-neural-pulse">
                  {stat.value}{stat.suffix}
                </div>
                <div className="text-sm text-gray-400 mt-2">{stat.name}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Plan Comparison Table - Only show if plan package is enabled */}
      {shouldShowPlanUI && (
      <div className="py-20 bg-gradient-to-b from-dark-900 to-dark-800">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Section Header */}
          <div className="text-center mb-12">
            <h2 className="text-4xl font-extrabold mb-4">
              <span className="cyber-text bg-clip-text text-transparent bg-gradient-to-r from-quantum-400 to-cyber-400">
                Choose Your Power Level
              </span>
            </h2>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto">
              From testing to domination. Pick the plan that matches your ambition.
            </p>
          </div>

          {/* Comparison Table */}
          <div className="overflow-hidden rounded-2xl border border-quantum-500/20 bg-dark-800/50 backdrop-blur-sm">
            <table className="w-full">
              <thead>
                <tr className="border-b border-quantum-500/20">
                  <th className="py-6 px-6 text-left">
                    <span className="text-lg font-bold text-gray-400">Features</span>
                  </th>
                  <th className="py-6 px-6 text-center bg-dark-700/30">
                    <div className="flex flex-col items-center">
                      <span className="text-2xl mb-2">🆓</span>
                      <span className="text-xl font-bold text-white mb-1">Free</span>
                      <span className="text-3xl font-extrabold cyber-text">$0</span>
                      <span className="text-xs text-gray-500 mt-1">forever</span>
                    </div>
                  </th>
                  <th className="py-6 px-6 text-center bg-gradient-to-br from-purple-900/30 to-pink-900/30 relative">
                    <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-gradient-to-r from-purple-500 to-pink-500 text-white px-3 py-1 rounded-full text-xs font-bold shadow-lg z-10">
                      ⚡ RECOMMENDED
                    </div>
                    <div className="flex flex-col items-center">
                      <span className="text-2xl mb-2">⚡</span>
                      <span className="text-xl font-bold text-white mb-1">Pro</span>
                      <span className="text-3xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-400">$60</span>
                      <span className="text-xs text-gray-400 mt-1">per month</span>
                    </div>
                  </th>
                  <th className="py-6 px-6 text-center bg-gradient-to-br from-yellow-900/30 to-orange-900/30 relative">
                    <div className="flex flex-col items-center">
                      <span className="text-2xl mb-2">💎</span>
                      <span className="text-xl font-bold text-white mb-1">Ultra</span>
                      <span className="text-3xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-yellow-400 to-orange-400">$500</span>
                      <span className="text-xs text-gray-400 mt-1">per month</span>
                    </div>
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-quantum-500/10">
                {/* 1️⃣ Core Limits Section */}
                <tr className="bg-dark-700/30">
                  <td colSpan={4} className="py-3 px-6">
                    <h3 className="text-lg font-bold text-cyber-400 flex items-center">
                      <span className="mr-2">1️⃣</span>
                      Core Limits
                    </h3>
                  </td>
                </tr>

                {/* Bot Limit */}
                <tr className="hover:bg-dark-700/20 transition-colors">
                  <td className="py-4 px-6 text-gray-300 font-medium">Maximum Entities</td>
                  <td className="py-4 px-6 text-center bg-dark-700/20">
                    <span className="text-gray-400">5 bots</span>
                  </td>
                  <td className="py-4 px-6 text-center bg-gradient-to-br from-purple-900/10 to-pink-900/10">
                    <span className="text-purple-400 font-semibold">20 bots</span>
                  </td>
                  <td className="py-4 px-6 text-center bg-gradient-to-br from-yellow-900/10 to-orange-900/10">
                    <span className="text-yellow-400 font-semibold">♾️ Unlimited</span>
                  </td>
                </tr>

                {/* Subscriptions per Bot */}
                <tr className="hover:bg-dark-700/20 transition-colors">
                  <td className="py-4 px-6 text-gray-300 font-medium">Subscriptions per Bot</td>
                  <td className="py-4 px-6 text-center bg-dark-700/20">
                    <span className="text-gray-400">5 max</span>
                  </td>
                  <td className="py-4 px-6 text-center bg-gradient-to-br from-purple-900/10 to-pink-900/10">
                    <span className="text-purple-400 font-semibold">20 max</span>
                  </td>
                  <td className="py-4 px-6 text-center bg-gradient-to-br from-yellow-900/10 to-orange-900/10">
                    <span className="text-yellow-400 font-semibold">♾️ Unlimited</span>
                  </td>
                </tr>

                {/* Environment */}
                <tr className="hover:bg-dark-700/20 transition-colors">
                  <td className="py-4 px-6 text-gray-300 font-medium">Trading Environment</td>
                  <td className="py-4 px-6 text-center bg-dark-700/20">
                    <span className="text-yellow-400">Testnet Only</span>
                  </td>
                  <td className="py-4 px-6 text-center bg-gradient-to-br from-purple-900/10 to-pink-900/10">
                    <span className="text-purple-400 font-semibold">Testnet + Mainnet</span>
                  </td>
                  <td className="py-4 px-6 text-center bg-gradient-to-br from-yellow-900/10 to-orange-900/10">
                    <span className="text-yellow-400 font-semibold">Testnet + Mainnet</span>
                  </td>
                </tr>

                {/* Compute Quota */}
                <tr className="hover:bg-dark-700/20 transition-colors">
                  <td className="py-4 px-6 text-gray-300 font-medium">
                    <div>Compute Quota</div>
                    <div className="text-xs text-gray-500">Bot trades per month</div>
                  </td>
                  <td className="py-4 px-6 text-center bg-dark-700/20">
                    <span className="text-yellow-400">∞ Unlimited (Low Quality)</span>
                  </td>
                  <td className="py-4 px-6 text-center bg-gradient-to-br from-purple-900/10 to-pink-900/10">
                    <span className="text-purple-400 font-semibold">720 trades</span>
                  </td>
                  <td className="py-4 px-6 text-center bg-gradient-to-br from-yellow-900/10 to-orange-900/10">
                    <span className="text-yellow-400 font-semibold">7,200 trades</span>
                  </td>
                </tr>

                {/* LLM Provider Quality */}
                <tr className="hover:bg-dark-700/20 transition-colors">
                  <td className="py-4 px-6 text-gray-300 font-medium">LLM Provider Quality</td>
                  <td className="py-4 px-6 text-center bg-dark-700/20">
                    <span className="text-yellow-400">Low Quality</span>
                  </td>
                  <td className="py-4 px-6 text-center bg-gradient-to-br from-purple-900/10 to-pink-900/10">
                    <span className="text-purple-400 font-semibold">High Quality</span>
                  </td>
                  <td className="py-4 px-6 text-center bg-gradient-to-br from-yellow-900/10 to-orange-900/10">
                    <span className="text-yellow-400 font-semibold">High Quality</span>
                  </td>
                </tr>

                {/* Duration */}
                <tr className="hover:bg-dark-700/20 transition-colors">
                  <td className="py-4 px-6 text-gray-300 font-medium">Bot Subscription Duration</td>
                  <td className="py-4 px-6 text-center bg-dark-700/20">
                    <span className="text-gray-400">3-day trial</span>
                  </td>
                  <td className="py-4 px-6 text-center bg-gradient-to-br from-purple-900/10 to-pink-900/10">
                    <span className="text-purple-400 font-semibold">30 days</span>
                  </td>
                  <td className="py-4 px-6 text-center bg-gradient-to-br from-yellow-900/10 to-orange-900/10">
                    <span className="text-yellow-400 font-semibold">30 days</span>
                  </td>
                </tr>

                {/* Strategies Template */}
                <tr className="hover:bg-dark-700/20 transition-colors">
                  <td className="py-4 px-6 text-gray-300 font-medium">Strategies Template Access</td>
                  <td className="py-4 px-6 text-center bg-dark-700/20">
                    <span className="text-yellow-400">5 templates</span>
                  </td>
                  <td className="py-4 px-6 text-center bg-gradient-to-br from-purple-900/10 to-pink-900/10">
                    <span className="text-purple-400 font-semibold">✓ Full Access</span>
                  </td>
                  <td className="py-4 px-6 text-center bg-gradient-to-br from-yellow-900/10 to-orange-900/10">
                    <span className="text-yellow-400 font-semibold">✓ Full Access</span>
                  </td>
                </tr>

                {/* 2️⃣ Trading & Performance Section */}
                <tr className="bg-dark-700/30">
                  <td colSpan={4} className="py-3 px-6">
                    <h3 className="text-lg font-bold text-cyber-400 flex items-center">
                      <span className="mr-2">2️⃣</span>
                      Trading & Performance
                    </h3>
                  </td>
                </tr>

                {/* Trading Type */}
                <tr className="hover:bg-dark-700/20 transition-colors">
                  <td className="py-4 px-6 text-gray-300 font-medium">Trading Type</td>
                  <td className="py-4 px-6 text-center bg-dark-700/20">
                    <span className="text-green-400">✓ SPOT, FUTURES</span>
                  </td>
                  <td className="py-4 px-6 text-center bg-gradient-to-br from-purple-900/10 to-pink-900/10">
                    <span className="text-purple-400 font-semibold">✓ SPOT, FUTURES</span>
                  </td>
                  <td className="py-4 px-6 text-center bg-gradient-to-br from-yellow-900/10 to-orange-900/10">
                    <span className="text-yellow-400 font-semibold">✓ SPOT, FUTURES</span>
                  </td>
                </tr>

                {/* Exchange Support */}
                <tr className="hover:bg-dark-700/20 transition-colors">
                  <td className="py-4 px-6 text-gray-300 font-medium">Exchange Support</td>
                  <td className="py-4 px-6 text-center bg-dark-700/20">
                    <span className="text-green-400">✓ Multiple</span>
                  </td>
                  <td className="py-4 px-6 text-center bg-gradient-to-br from-purple-900/10 to-pink-900/10">
                    <span className="text-purple-400 font-semibold">✓ Multiple</span>
                  </td>
                  <td className="py-4 px-6 text-center bg-gradient-to-br from-yellow-900/10 to-orange-900/10">
                    <span className="text-yellow-400 font-semibold">✓ Multiple</span>
                  </td>
                </tr>

                {/* Risk Management */}
                <tr className="hover:bg-dark-700/20 transition-colors">
                  <td className="py-4 px-6 text-gray-300 font-medium">Risk Management</td>
                  <td className="py-4 px-6 text-center bg-dark-700/20">
                    <span className="text-green-400">✓</span>
                  </td>
                  <td className="py-4 px-6 text-center bg-gradient-to-br from-purple-900/10 to-pink-900/10">
                    <span className="text-purple-400 font-semibold">✓</span>
                  </td>
                  <td className="py-4 px-6 text-center bg-gradient-to-br from-yellow-900/10 to-orange-900/10">
                    <span className="text-yellow-400 font-semibold">✓</span>
                  </td>
                </tr>

                {/* Capital Management */}
                <tr className="hover:bg-dark-700/20 transition-colors">
                  <td className="py-4 px-6 text-gray-300 font-medium">Capital Management</td>
                  <td className="py-4 px-6 text-center bg-dark-700/20">
                    <span className="text-green-400">✓</span>
                  </td>
                  <td className="py-4 px-6 text-center bg-gradient-to-br from-purple-900/10 to-pink-900/10">
                    <span className="text-purple-400 font-semibold">✓</span>
                  </td>
                  <td className="py-4 px-6 text-center bg-gradient-to-br from-yellow-900/10 to-orange-900/10">
                    <span className="text-yellow-400 font-semibold">✓</span>
                  </td>
                </tr>

                {/* Strategies Library */}
                <tr className="hover:bg-dark-700/20 transition-colors">
                  <td className="py-4 px-6 text-gray-300 font-medium">Strategies Library</td>
                  <td className="py-4 px-6 text-center bg-dark-700/20">
                    <span className="text-green-400">✓</span>
                  </td>
                  <td className="py-4 px-6 text-center bg-gradient-to-br from-purple-900/10 to-pink-900/10">
                    <span className="text-purple-400 font-semibold">✓</span>
                  </td>
                  <td className="py-4 px-6 text-center bg-gradient-to-br from-yellow-900/10 to-orange-900/10">
                    <span className="text-yellow-400 font-semibold">✓</span>
                  </td>
                </tr>

                {/* Bot Template */}
                <tr className="hover:bg-dark-700/20 transition-colors">
                  <td className="py-4 px-6 text-gray-300 font-medium">Bot Template</td>
                  <td className="py-4 px-6 text-center bg-dark-700/20">
                    <span className="text-green-400">✓</span>
                  </td>
                  <td className="py-4 px-6 text-center bg-gradient-to-br from-purple-900/10 to-pink-900/10">
                    <span className="text-purple-400 font-semibold">✓</span>
                  </td>
                  <td className="py-4 px-6 text-center bg-gradient-to-br from-yellow-900/10 to-orange-900/10">
                    <span className="text-yellow-400 font-semibold">✓</span>
                  </td>
                </tr>

                {/* Execution Log Monitoring */}
                <tr className="hover:bg-dark-700/20 transition-colors">
                  <td className="py-4 px-6 text-gray-300 font-medium">Execution Log Monitoring</td>
                  <td className="py-4 px-6 text-center bg-dark-700/20">
                    <span className="text-green-400">✓</span>
                  </td>
                  <td className="py-4 px-6 text-center bg-gradient-to-br from-purple-900/10 to-pink-900/10">
                    <span className="text-purple-400 font-semibold">✓</span>
                  </td>
                  <td className="py-4 px-6 text-center bg-gradient-to-br from-yellow-900/10 to-orange-900/10">
                    <span className="text-yellow-400 font-semibold">✓</span>
                  </td>
                </tr>

                {/* 3️⃣ Communication & Support Section */}
                <tr className="bg-dark-700/30">
                  <td colSpan={4} className="py-3 px-6">
                    <h3 className="text-lg font-bold text-cyber-400 flex items-center">
                      <span className="mr-2">3️⃣</span>
                      Communication & Support
                    </h3>
                  </td>
                </tr>

                {/* Telegram/Discord Notification */}
                <tr className="hover:bg-dark-700/20 transition-colors">
                  <td className="py-4 px-6 text-gray-300 font-medium">Telegram/Discord Notification</td>
                  <td className="py-4 px-6 text-center bg-dark-700/20">
                    <span className="text-green-400">✓</span>
                  </td>
                  <td className="py-4 px-6 text-center bg-gradient-to-br from-purple-900/10 to-pink-900/10">
                    <span className="text-purple-400 font-semibold">✓</span>
                  </td>
                  <td className="py-4 px-6 text-center bg-gradient-to-br from-yellow-900/10 to-orange-900/10">
                    <span className="text-yellow-400 font-semibold">✓</span>
                  </td>
                </tr>

                {/* Analytic Dashboard */}
                <tr className="hover:bg-dark-700/20 transition-colors">
                  <td className="py-4 px-6 text-gray-300 font-medium">Analytic Dashboard</td>
                  <td className="py-4 px-6 text-center bg-dark-700/20">
                    <span className="text-green-400">✓</span>
                  </td>
                  <td className="py-4 px-6 text-center bg-gradient-to-br from-purple-900/10 to-pink-900/10">
                    <span className="text-purple-400 font-semibold">✓</span>
                  </td>
                  <td className="py-4 px-6 text-center bg-gradient-to-br from-yellow-900/10 to-orange-900/10">
                    <span className="text-yellow-400 font-semibold">✓</span>
                  </td>
                </tr>

                {/* Subscription Management */}
                <tr className="hover:bg-dark-700/20 transition-colors">
                  <td className="py-4 px-6 text-gray-300 font-medium">Subscription Management</td>
                  <td className="py-4 px-6 text-center bg-dark-700/20">
                    <span className="text-green-400">✓</span>
                  </td>
                  <td className="py-4 px-6 text-center bg-gradient-to-br from-purple-900/10 to-pink-900/10">
                    <span className="text-purple-400 font-semibold">✓</span>
                  </td>
                  <td className="py-4 px-6 text-center bg-gradient-to-br from-yellow-900/10 to-orange-900/10">
                    <span className="text-yellow-400 font-semibold">✓</span>
                  </td>
                </tr>

                {/* Support */}
                <tr className="hover:bg-dark-700/20 transition-colors">
                  <td className="py-4 px-6 text-gray-300 font-medium">Priority Support</td>
                  <td className="py-4 px-6 text-center bg-dark-700/20">
                    <span className="text-gray-400">Community Only</span>
                  </td>
                  <td className="py-4 px-6 text-center bg-gradient-to-br from-purple-900/10 to-pink-900/10">
                    <span className="text-purple-400 font-semibold">✓ 24/7 Support</span>
                  </td>
                  <td className="py-4 px-6 text-center bg-gradient-to-br from-yellow-900/10 to-orange-900/10">
                    <span className="text-yellow-400 font-semibold">✓ 24/7 Dedicated</span>
                  </td>
                </tr>

                {/* 4️⃣ Marketplace Access Section */}
                <tr className="bg-dark-700/30">
                  <td colSpan={4} className="py-3 px-6">
                    <h3 className="text-lg font-bold text-cyber-400 flex items-center">
                      <span className="mr-2">4️⃣</span>
                      Marketplace Access
                    </h3>
                  </td>
                </tr>

                {/* Marketplace */}
                <tr className="hover:bg-dark-700/20 transition-colors">
                  <td className="py-4 px-6 text-gray-300 font-medium">Publish to Marketplace</td>
                  <td className="py-4 px-6 text-center bg-dark-700/20">
                    <span className="text-red-400">✗ Not Allowed</span>
                  </td>
                  <td className="py-4 px-6 text-center bg-gradient-to-br from-purple-900/10 to-pink-900/10">
                    <span className="text-purple-400 font-semibold">✓ Full Access</span>
                  </td>
                  <td className="py-4 px-6 text-center bg-gradient-to-br from-yellow-900/10 to-orange-900/10">
                    <span className="text-yellow-400 font-semibold">✓ Full Access</span>
                  </td>
                </tr>
              </tbody>
            </table>

            {/* CTA Row */}
            <div className="grid grid-cols-3 gap-0 border-t border-quantum-500/20">
              <div className="py-6 px-4 text-center bg-dark-700/20">
                <Link
                  href="/auth/register"
                  className="inline-block px-6 py-3 border border-quantum-500/30 text-quantum-300 font-semibold rounded-lg hover:bg-quantum-500/10 transition-all text-sm"
                >
                  Start Free
                </Link>
              </div>
              <div className="py-6 px-4 text-center bg-gradient-to-br from-purple-900/10 to-pink-900/10">
                <button
                  onClick={() => {
                    setTargetPlan('pro')
                    setShowUpgradeModal(true)
                  }}
                  className="inline-block px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all shadow-lg hover:shadow-purple-500/50 transform hover:scale-105 text-sm"
                >
                  Upgrade to Pro
                </button>
              </div>
              <div className="py-6 px-4 text-center bg-gradient-to-br from-yellow-900/10 to-orange-900/10">
                <button
                  onClick={() => {
                    setTargetPlan('ultra')
                    setShowUpgradeModal(true)
                  }}
                  className="inline-block px-6 py-3 bg-gradient-to-r from-yellow-500 to-orange-500 text-white font-bold rounded-lg hover:from-yellow-600 hover:to-orange-600 transition-all shadow-lg hover:shadow-yellow-500/50 transform hover:scale-105 text-sm"
                >
                  Upgrade to Ultra
                </button>
              </div>
            </div>
          </div>

          {/* Additional Info */}
          <div className="mt-8 text-center">
            <p className="text-sm text-gray-500">
              All plans include secure authentication, encrypted data, and quantum-resistant security protocols.
            </p>
          </div>
        </div>
      </div>
      )}
      <div className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-extrabold cyber-text mb-4">
              Neural Capabilities
            </h2>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto">
              Harness the power of quantum computing and artificial intelligence to create 
              trading entities that operate beyond human comprehension.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {features.map((feature, index) => (
              <div
                key={feature.name}
                className="card-quantum p-8 hover:shadow-2xl transition-all duration-500 transform hover:-translate-y-2 animate-fade-in"
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                <div className="flex items-center mb-6">
                  <div className={`p-3 rounded-lg bg-gradient-to-r ${feature.gradient} shadow-lg`}>
                    <feature.icon className="h-8 w-8 text-white" />
                  </div>
                  <h3 className="ml-4 text-xl font-bold text-gray-200">{feature.name}</h3>
                </div>
                <p className="text-gray-400 leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="py-20 bg-gradient-to-r from-quantum-900/30 via-dark-800/50 to-cyber-900/30 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-4xl font-extrabold mb-6">
            <span className="cyber-text">Ready to Transcend</span>
            <span className="block text-gray-300 text-2xl mt-2">Human Trading Limitations?</span>
          </h2>
          
          <p className="text-xl text-gray-400 mb-10 max-w-2xl mx-auto">
            Join the elite circle of AI architects. Create, deploy, and command 
            an army of autonomous trading entities.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-6 justify-center">
            <Link
              href="/auth/register"
              className="btn btn-primary px-10 py-4 text-lg font-bold rounded-lg transform hover:scale-105 transition-all duration-300 shadow-2xl"
            >
              🚀 Begin Neural Synthesis
            </Link>
            <Link
              href="/creator/forge"
              className="btn btn-cyber px-10 py-4 text-lg font-bold rounded-lg transform hover:scale-105 transition-all duration-300"
            >
              ⚡ Enter the Forge
            </Link>
          </div>
          
          <div className="mt-8 text-sm text-gray-500">
            <span className="inline-flex items-center">
              🔒 Quantum-encrypted • 🧠 AI-powered • ⚡ Neural-enhanced
            </span>
          </div>
        </div>
      </div>

      {/* Floating Elements */}
      <div className="fixed top-20 left-10 w-2 h-2 bg-quantum-500 rounded-full animate-neural-pulse opacity-60"></div>
      <div className="fixed top-40 right-20 w-1 h-1 bg-cyber-400 rounded-full animate-neural-pulse opacity-40" style={{ animationDelay: '1s' }}></div>
      <div className="fixed bottom-40 left-20 w-1.5 h-1.5 bg-neural-500 rounded-full animate-neural-pulse opacity-50" style={{ animationDelay: '2s' }}></div>
      <div className="fixed bottom-20 right-10 w-2 h-2 bg-quantum-400 rounded-full animate-neural-pulse opacity-30" style={{ animationDelay: '3s' }}></div>

      {/* Upgrade Modal */}
      <UpgradeModal 
        isOpen={showUpgradeModal}
        onClose={() => setShowUpgradeModal(false)}
        targetPlan={targetPlan}
      />
    </div>
  )
}