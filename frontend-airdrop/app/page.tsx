'use client';

import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { GiftIcon, CheckCircleIcon, UserGroupIcon, ChartBarIcon } from '@heroicons/react/24/outline';
import { isAuthenticated } from '@/lib/auth';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated()) {
      router.push('/dashboard');
    }
  }, [router]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
          <div className="text-center">
            <GiftIcon className="w-20 h-20 mx-auto mb-6 text-blue-600" />
            <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
              BOT Token Airdrop
            </h1>
            <p className="text-xl md:text-2xl text-gray-600 mb-8 max-w-3xl mx-auto">
              Complete tasks, earn points, and claim up to <span className="text-blue-600 font-bold">50M BOT tokens</span>
            </p>
            
            <button
              onClick={() => router.push('/login')}
              className="inline-flex items-center px-8 py-4 text-lg font-semibold text-white bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all transform hover:scale-105 shadow-lg"
            >
              Get Started - Sign In
            </button>
          </div>
        </div>
      </div>

      {/* Stats Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="bg-white rounded-xl shadow-lg p-8 text-center">
            <div className="text-4xl font-bold text-blue-600 mb-2">50M</div>
            <div className="text-gray-600">BOT Tokens Available</div>
          </div>
          <div className="bg-white rounded-xl shadow-lg p-8 text-center">
            <div className="text-4xl font-bold text-purple-600 mb-2">21</div>
            <div className="text-gray-600">Different Tasks</div>
          </div>
          <div className="bg-white rounded-xl shadow-lg p-8 text-center">
            <div className="text-4xl font-bold text-green-600 mb-2">10</div>
            <div className="text-gray-600">BOT per Point</div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
          How to Earn BOT Tokens
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {[
            {
              icon: <ChartBarIcon className="w-8 h-8" />,
              title: 'Platform Usage',
              description: 'Create bots, execute trades, reach volume milestones',
              percentage: '40%'
            },
            {
              icon: <UserGroupIcon className="w-8 h-8" />,
              title: 'Community',
              description: 'Join Discord, Telegram, Twitter, refer friends',
              percentage: '30%'
            },
            {
              icon: <CheckCircleIcon className="w-8 h-8" />,
              title: 'Trader Contributions',
              description: 'Submit strategies, compete in leaderboard',
              percentage: '10%'
            },
            {
              icon: <GiftIcon className="w-8 h-8" />,
              title: 'SNS Participation',
              description: 'Participate in SNS, vote on governance',
              percentage: '20%'
            }
          ].map((feature, idx) => (
            <div key={idx} className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
              <div className="text-blue-600 mb-4">{feature.icon}</div>
              <div className="text-sm font-semibold text-purple-600 mb-2">{feature.percentage}</div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">{feature.title}</h3>
              <p className="text-gray-600 text-sm">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* CTA Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl shadow-2xl p-12 text-center text-white">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Ready to Start Earning?
          </h2>
          <p className="text-xl mb-8 opacity-90">
            Sign in now and complete your first task to earn BOT tokens
          </p>
          <button
            onClick={() => router.push('/login')}
            className="inline-flex items-center px-8 py-4 text-lg font-semibold text-blue-600 bg-white rounded-lg hover:bg-gray-100 transition-all transform hover:scale-105 shadow-lg"
          >
            Get Started Now
          </button>
        </div>
      </div>

      {/* Footer */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 text-center text-gray-600">
        <p>© 2025 AI Trading Bot Marketplace. All rights reserved.</p>
      </div>
    </div>
  );
}
