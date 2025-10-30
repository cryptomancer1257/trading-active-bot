'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { isAuthenticated, removeAuthToken } from '@/lib/auth';
import { airdropAPI } from '@/lib/api';
import { 
  GiftIcon, 
  CheckCircleIcon, 
  ChartBarIcon,
  UserGroupIcon,
  ArrowRightIcon,
  ArrowLeftOnRectangleIcon
} from '@heroicons/react/24/outline';

interface Task {
  id: number;
  name: string;
  description: string;
  points: number;
  category: string;
  is_active: boolean;
  is_completed?: boolean;
}

interface UserStatus {
  total_points: number;
  total_tokens: number;
  total_claims: number;
  pending_claims: number;
}

export default function DashboardPage() {
  const router = useRouter();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [userStatus, setUserStatus] = useState<UserStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState<number | null>(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/login');
      return;
    }
    loadData();
  }, [router]);

  const loadData = async () => {
    try {
      const [tasksRes, statusRes] = await Promise.all([
        airdropAPI.getTasks(),
        airdropAPI.getUserStatus()
      ]);
      
      setTasks(tasksRes.data);
      setUserStatus(statusRes.data);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (taskId: number, taskName: string) => {
    setVerifying(taskId);
    try {
      let response;
      if (taskName.toLowerCase().includes('bot creation')) {
        response = await airdropAPI.verifyBotCreation();
      } else if (taskName.toLowerCase().includes('first trade')) {
        response = await airdropAPI.verifyFirstTrade();
      } else if (taskName.toLowerCase().includes('volume')) {
        response = await airdropAPI.verifyTradingVolume();
      }
      
      if (response?.data.verified) {
        alert(`✅ Verified! You earned ${response.data.points} points`);
        loadData();
      } else {
        alert(`❌ Not verified yet. ${response?.data.message || 'Requirements not met'}`);
      }
    } catch (error: any) {
      alert(`❌ Verification failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setVerifying(null);
    }
  };

  const handleLogout = () => {
    removeAuthToken();
    router.push('/');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center">
              <GiftIcon className="w-8 h-8 text-blue-600 mr-2" />
              <h1 className="text-2xl font-bold text-gray-900">BOT Airdrop</h1>
            </div>
            <button
              onClick={handleLogout}
              className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
            >
              <ArrowLeftOnRectangleIcon className="w-5 h-5 mr-2" />
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Stats Cards */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg shadow-lg p-6 text-white">
            <div className="text-3xl font-bold">{userStatus?.total_points || 0}</div>
            <div className="text-sm opacity-90">Total Points</div>
          </div>
          <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-lg shadow-lg p-6 text-white">
            <div className="text-3xl font-bold">{userStatus?.total_tokens || 0}</div>
            <div className="text-sm opacity-90">BOT Tokens</div>
          </div>
          <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg shadow-lg p-6 text-white">
            <div className="text-3xl font-bold">{userStatus?.total_claims || 0}</div>
            <div className="text-sm opacity-90">Completed Tasks</div>
          </div>
          <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-lg shadow-lg p-6 text-white">
            <div className="text-3xl font-bold">{userStatus?.pending_claims || 0}</div>
            <div className="text-sm opacity-90">Pending</div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <button
            onClick={() => router.push('/tasks')}
            className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow"
          >
            <ChartBarIcon className="w-8 h-8 text-blue-600 mb-2" />
            <h3 className="text-lg font-semibold text-gray-900 mb-1">View All Tasks</h3>
            <p className="text-sm text-gray-600">Complete tasks to earn points</p>
          </button>
          
          <button
            onClick={() => router.push('/leaderboard')}
            className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow"
          >
            <UserGroupIcon className="w-8 h-8 text-purple-600 mb-2" />
            <h3 className="text-lg font-semibold text-gray-900 mb-1">Leaderboard</h3>
            <p className="text-sm text-gray-600">See top performers</p>
          </button>
          
          <button
            onClick={() => airdropAPI.claimTokens()}
            className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg shadow p-6 hover:shadow-lg transition-shadow text-white"
          >
            <GiftIcon className="w-8 h-8 mb-2" />
            <h3 className="text-lg font-semibold mb-1">Claim Tokens</h3>
            <p className="text-sm opacity-90">Convert points to BOT</p>
          </button>
        </div>

        {/* Recent Tasks */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">Available Tasks</h2>
          </div>
          
          <div className="divide-y divide-gray-200">
            {tasks.slice(0, 5).map((task) => (
              <div key={task.id} className="px-6 py-4 flex items-center justify-between hover:bg-gray-50">
                <div className="flex-1">
                  <div className="flex items-center">
                    <h3 className="text-lg font-medium text-gray-900">{task.name}</h3>
                    <span className="ml-3 px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                      {task.points} points
                    </span>
                    {task.is_completed && (
                      <CheckCircleIcon className="ml-2 w-5 h-5 text-green-500" />
                    )}
                  </div>
                  <p className="mt-1 text-sm text-gray-600">{task.description}</p>
                </div>
                
                <div className="ml-4">
                  {task.is_completed ? (
                    <span className="text-sm text-green-600 font-medium">Completed</span>
                  ) : (
                    <button
                      onClick={() => handleVerify(task.id, task.name)}
                      disabled={verifying === task.id}
                      className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                    >
                      {verifying === task.id ? 'Verifying...' : 'Verify'}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
          
          <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
            <button
              onClick={() => router.push('/tasks')}
              className="flex items-center text-sm font-medium text-blue-600 hover:text-blue-800"
            >
              View all {tasks.length} tasks
              <ArrowRightIcon className="ml-2 w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

