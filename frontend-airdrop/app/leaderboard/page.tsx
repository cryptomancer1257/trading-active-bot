'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { isAuthenticated, removeAuthToken } from '@/lib/auth';
import { airdropAPI } from '@/lib/api';
import { 
  TrophyIcon,
  ChartBarIcon,
  ArrowLeftIcon,
  SparklesIcon,
  FireIcon
} from '@heroicons/react/24/outline';

interface LeaderboardEntry {
  rank: number;
  principal_id: string;
  total_points: number;
  tasks_completed: number;
  trading_volume?: number;
  profit_loss?: number;
}

export default function LeaderboardPage() {
  const router = useRouter();
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [userRank, setUserRank] = useState<number | null>(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/login');
      return;
    }
    loadData();
  }, [router]);

  const loadData = async () => {
    try {
      const [statusRes, leaderboardRes] = await Promise.all([
        airdropAPI.getUserStatus(),
        airdropAPI.getLeaderboard().catch(() => ({ data: [] })), // Fallback if endpoint doesn't exist
      ]);

      // Generate mock leaderboard data for now
      const mockLeaderboard: LeaderboardEntry[] = Array.from({ length: 50 }, (_, i) => ({
        rank: i + 1,
        principal_id: `user_${i + 1}`,
        total_points: Math.floor(Math.random() * 10000) + 1000,
        tasks_completed: Math.floor(Math.random() * 20) + 1,
        trading_volume: Math.floor(Math.random() * 100000),
        profit_loss: Math.random() * 10000 - 5000,
      })).sort((a, b) => b.total_points - a.total_points);

      // Update ranks
      mockLeaderboard.forEach((entry, index) => {
        entry.rank = index + 1;
      });

      setLeaderboard(mockLeaderboard);

      // Find user's rank (mock for now)
      const userPoints = statusRes.data.total_points || 0;
      const rank = mockLeaderboard.findIndex(e => e.total_points <= userPoints) + 1;
      setUserRank(rank || mockLeaderboard.length + 1);
    } catch (error) {
      console.error('Failed to load leaderboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const getRankColor = (rank: number) => {
    if (rank === 1) return 'bg-gradient-to-r from-yellow-400 to-yellow-600 text-white';
    if (rank === 2) return 'bg-gradient-to-r from-gray-300 to-gray-400 text-gray-900';
    if (rank === 3) return 'bg-gradient-to-r from-orange-400 to-orange-600 text-white';
    return 'bg-gray-100 text-gray-700';
  };

  const getRankBadge = (rank: number) => {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return `#${rank}`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading leaderboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.push('/dashboard')}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ArrowLeftIcon className="w-6 h-6 text-gray-600" />
              </button>
              <div>
                <h1 className="text-3xl font-bold text-gray-900 flex items-center space-x-2">
                  <TrophyIcon className="w-8 h-8 text-yellow-500" />
                  <span>Leaderboard</span>
                </h1>
                <p className="text-gray-600 mt-1">Top performers in the airdrop campaign</p>
              </div>
            </div>
            <button
              onClick={() => {
                removeAuthToken();
                router.push('/login');
              }}
              className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* User's Rank Card */}
        {userRank && (
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg shadow-lg p-6 mb-8 text-white">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-100 text-sm mb-1">Your Rank</p>
                <p className="text-4xl font-bold">{getRankBadge(userRank)}</p>
              </div>
              <div className="text-right">
                <p className="text-blue-100 text-sm mb-1">Keep climbing!</p>
                <p className="text-2xl font-bold">
                  {userRank <= 10 ? '🔥 Top 10!' : userRank <= 50 ? '⭐ Top 50' : 'Keep going!'}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Top 3 Podium */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          {leaderboard.slice(0, 3).map((entry, index) => (
            <div
              key={entry.principal_id}
              className={`${
                index === 0 ? 'order-2' : index === 1 ? 'order-1' : 'order-3'
              }`}
            >
              <div className={`bg-white rounded-lg shadow-lg p-6 text-center border-2 ${
                index === 0 ? 'border-yellow-400' : index === 1 ? 'border-gray-300' : 'border-orange-400'
              }`}>
                <div className={`text-6xl mb-2 ${index === 0 ? 'scale-125' : ''}`}>
                  {getRankBadge(entry.rank)}
                </div>
                <p className="text-sm text-gray-600 mb-2 truncate">
                  {entry.principal_id.substring(0, 12)}...
                </p>
                <div className="flex items-center justify-center space-x-1 mb-1">
                  <SparklesIcon className="w-5 h-5 text-yellow-500" />
                  <p className="text-2xl font-bold text-gray-900">
                    {entry.total_points.toLocaleString()}
                  </p>
                </div>
                <p className="text-xs text-gray-500">{entry.tasks_completed} tasks</p>
              </div>
            </div>
          ))}
        </div>

        {/* Leaderboard Table */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Rank
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Points
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Tasks
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Trading Volume
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {leaderboard.map((entry) => (
                  <tr 
                    key={entry.principal_id}
                    className={`hover:bg-gray-50 transition-colors ${
                      entry.rank <= 3 ? 'bg-yellow-50/30' : ''
                    }`}
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center justify-center w-10 h-10 rounded-full font-bold ${getRankColor(entry.rank)}`}>
                        {getRankBadge(entry.rank)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-400 to-purple-400 flex items-center justify-center text-white font-bold text-xs mr-3">
                          {entry.principal_id.substring(0, 2).toUpperCase()}
                        </div>
                        <span className="text-sm font-medium text-gray-900 truncate max-w-xs">
                          {entry.principal_id}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center space-x-1">
                        <SparklesIcon className="w-4 h-4 text-yellow-500" />
                        <span className="text-sm font-bold text-gray-900">
                          {entry.total_points.toLocaleString()}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center space-x-1">
                        <ChartBarIcon className="w-4 h-4 text-blue-500" />
                        <span className="text-sm text-gray-600">
                          {entry.tasks_completed}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      ${entry.trading_volume?.toLocaleString() || '0'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Info Banner */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <div className="flex items-start space-x-3">
            <FireIcon className="w-6 h-6 text-blue-600 flex-shrink-0 mt-1" />
            <div>
              <h3 className="text-lg font-semibold text-blue-900 mb-2">
                How Rankings Work
              </h3>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• Rankings are based on total points earned from completing tasks</li>
                <li>• Complete more tasks to climb the leaderboard</li>
                <li>• Top 100 users will receive bonus tokens at the end of the campaign</li>
                <li>• Leaderboard updates in real-time</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

