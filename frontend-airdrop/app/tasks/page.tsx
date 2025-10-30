'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { isAuthenticated, removeAuthToken } from '@/lib/auth';
import { airdropAPI } from '@/lib/api';
import { 
  GiftIcon, 
  CheckCircleIcon, 
  XCircleIcon,
  ChartBarIcon,
  UserGroupIcon,
  CogIcon,
  CodeBracketIcon,
  ArrowLeftIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';

interface Task {
  id: number;
  name: string;
  description: string;
  points: number;
  category: string;
  is_active: boolean;
  verification_method: string;
}

interface UserClaim {
  task_id: number;
  verification_status: string;
}

export default function TasksPage() {
  const router = useRouter();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [userClaims, setUserClaims] = useState<UserClaim[]>([]);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState<number | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

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
        airdropAPI.getUserStatus(),
      ]);
      setTasks(tasksRes.data);
      setUserClaims(statusRes.data.claims || []);
    } catch (error) {
      console.error('Failed to load tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (taskId: number) => {
    setVerifying(taskId);
    try {
      // Call appropriate verification endpoint based on task
      const task = tasks.find(t => t.id === taskId);
      if (!task) return;

      let response;
      switch (task.verification_method) {
        case 'API_CHECK':
          response = await airdropAPI.verifyBotCreation();
          break;
        case 'TRANSACTION_CHECK':
          response = await airdropAPI.verifyFirstTrade();
          break;
        default:
          alert('Verification method not implemented yet');
          return;
      }

      if (response.data.verified) {
        alert(`✅ Task verified! You earned ${response.data.points} points.`);
        await loadData();
      } else {
        alert(`❌ ${response.data.error || 'Task not completed yet'}`);
      }
    } catch (error: any) {
      alert(`❌ Verification failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setVerifying(null);
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'platform_usage':
        return <ChartBarIcon className="w-6 h-6" />;
      case 'community':
        return <UserGroupIcon className="w-6 h-6" />;
      case 'sns':
        return <CogIcon className="w-6 h-6" />;
      case 'trader_contributions':
        return <CodeBracketIcon className="w-6 h-6" />;
      default:
        return <GiftIcon className="w-6 h-6" />;
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'platform_usage':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'community':
        return 'bg-purple-100 text-purple-800 border-purple-300';
      case 'sns':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'trader_contributions':
        return 'bg-orange-100 text-orange-800 border-orange-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const isTaskCompleted = (taskId: number) => {
    return userClaims.some(
      claim => claim.task_id === taskId && claim.verification_status === 'VERIFIED'
    );
  };

  const categories = [
    { id: 'all', name: 'All Tasks', icon: SparklesIcon },
    { id: 'platform_usage', name: 'Platform Usage', icon: ChartBarIcon },
    { id: 'community', name: 'Community', icon: UserGroupIcon },
    { id: 'sns', name: 'SNS Participation', icon: CogIcon },
    { id: 'trader_contributions', name: 'Trader Contributions', icon: CodeBracketIcon },
  ];

  const filteredTasks = selectedCategory === 'all' 
    ? tasks 
    : tasks.filter(t => t.category === selectedCategory);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading tasks...</p>
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
                <h1 className="text-3xl font-bold text-gray-900">Airdrop Tasks</h1>
                <p className="text-gray-600 mt-1">Complete tasks to earn BOT tokens</p>
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
        {/* Category Filter */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-8">
          <div className="flex flex-wrap gap-2">
            {categories.map((category) => {
              const Icon = category.icon;
              return (
                <button
                  key={category.id}
                  onClick={() => setSelectedCategory(category.id)}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                    selectedCategory === category.id
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span>{category.name}</span>
                  <span className="px-2 py-0.5 text-xs rounded-full bg-white/20">
                    {category.id === 'all' 
                      ? tasks.length 
                      : tasks.filter(t => t.category === category.id).length}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Tasks Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredTasks.map((task) => {
            const completed = isTaskCompleted(task.id);
            return (
              <div
                key={task.id}
                className={`bg-white rounded-lg shadow-sm border-2 transition-all hover:shadow-md ${
                  completed ? 'border-green-300' : 'border-gray-200'
                }`}
              >
                <div className="p-6">
                  {/* Category Badge */}
                  <div className="flex items-center justify-between mb-4">
                    <div className={`flex items-center space-x-2 px-3 py-1 rounded-full border ${getCategoryColor(task.category)}`}>
                      {getCategoryIcon(task.category)}
                      <span className="text-xs font-medium capitalize">
                        {task.category.replace('_', ' ')}
                      </span>
                    </div>
                    {completed && (
                      <CheckCircleIcon className="w-6 h-6 text-green-500" />
                    )}
                  </div>

                  {/* Task Info */}
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {task.name}
                  </h3>
                  <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                    {task.description}
                  </p>

                  {/* Points */}
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-2">
                      <SparklesIcon className="w-5 h-5 text-yellow-500" />
                      <span className="text-lg font-bold text-gray-900">
                        {task.points.toLocaleString()}
                      </span>
                      <span className="text-sm text-gray-600">points</span>
                    </div>
                  </div>

                  {/* Action Button */}
                  {completed ? (
                    <button
                      disabled
                      className="w-full py-3 bg-green-100 text-green-700 rounded-lg font-medium flex items-center justify-center space-x-2"
                    >
                      <CheckCircleIcon className="w-5 h-5" />
                      <span>Completed</span>
                    </button>
                  ) : (
                    <button
                      onClick={() => handleVerify(task.id)}
                      disabled={verifying === task.id || !task.is_active}
                      className={`w-full py-3 rounded-lg font-medium transition-colors ${
                        verifying === task.id
                          ? 'bg-gray-100 text-gray-500 cursor-wait'
                          : task.is_active
                          ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:from-blue-700 hover:to-purple-700'
                          : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                      }`}
                    >
                      {verifying === task.id ? 'Verifying...' : task.is_active ? 'Verify Task' : 'Coming Soon'}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Empty State */}
        {filteredTasks.length === 0 && (
          <div className="text-center py-12">
            <XCircleIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No tasks found</h3>
            <p className="text-gray-600">Try selecting a different category</p>
          </div>
        )}
      </div>
    </div>
  );
}

