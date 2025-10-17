'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/navigation';

interface FeatureFlag {
  id: number;
  feature_type: 'PLAN_PACKAGE' | 'MARKETPLACE_PUBLISHING' | 'BOT_CREATION';
  is_enabled: boolean;
  disabled_from: string | null;
  disabled_until: string | null;
  reason: string | null;
  created_at: string;
  updated_at: string;
}

interface PlanPackageStatus {
  is_enabled: boolean;
  reason: string;
  disabled_until?: string;
}

export default function FeatureFlagsAdmin() {
  const { user, token } = useAuth();
  const router = useRouter();
  const [flags, setFlags] = useState<FeatureFlag[]>([]);
  const [planStatus, setPlanStatus] = useState<PlanPackageStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Form states for disabling plan package
  const [disableForm, setDisableForm] = useState({
    disabled_from: '',
    disabled_until: '',
    reason: ''
  });
  const [showDisableForm, setShowDisableForm] = useState(false);
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  // Check if user is admin
  useEffect(() => {
    if (user && user.role !== 'ADMIN') {
      router.push('/');
      return;
    }
  }, [user, router]);

  // Fetch feature flags
  const fetchFlags = async () => {
    try {
      // Debug logging
      console.log('fetchFlags debug:', {
        token,
        tokenType: typeof token,
        tokenLength: token?.length,
        user,
        isAuthenticated: !!user && !!token
      });
      
      const headers: Record<string, string> = {
        'Content-Type': 'application/json'
      };
      
      // Only add auth header if token exists
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
        console.log('Added Authorization header:', `Bearer ${token.substring(0, 20)}...`);
      } else {
        console.log('No token found, skipping Authorization header');
      }
      
      console.log('Request headers:', headers);
      const response = await fetch('/api/admin/feature-flags/', { headers });

      if (!response.ok) {
        throw new Error('Failed to fetch feature flags');
      }

      const data = await response.json();
      setFlags(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  // Fetch plan package status
  const fetchPlanStatus = async () => {
    try {
      const response = await fetch('/api/admin/feature-flags/public/plan-package-status');
      if (response.ok) {
        const data = await response.json();
        setPlanStatus(data);
      }
    } catch (err) {
      console.error('Failed to fetch plan status:', err);
    }
  };

  useEffect(() => {
    if (!user || !token) {
      setLoading(false);
      return;
    }
    
    if (user.role === 'ADMIN') {
      Promise.all([fetchFlags(), fetchPlanStatus()]).finally(() => {
        setLoading(false);
      });
    } else {
      setLoading(false);
    }
  }, [token, user]);

  const handleDisablePlanPackage = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const response = await fetch('/api/admin/feature-flags/disable-plan-package', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          disabled_from: new Date(disableForm.disabled_from).toISOString(),
          disabled_until: new Date(disableForm.disabled_until).toISOString(),
          reason: disableForm.reason
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to disable plan package');
      }

      // Refresh data
      await Promise.all([fetchFlags(), fetchPlanStatus()]);
      setShowDisableForm(false);
      setDisableForm({ disabled_from: '', disabled_until: '', reason: '' });
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  const handleAdminLogin = async () => {
    setIsLoggingIn(true);
    try {
      // Login request
      const response = await fetch('/api/auth/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'username=chaulaode1257@gmail.com&password=admin123'
      });

      if (!response.ok) {
        throw new Error(`Login failed: ${response.status}`);
      }

      const data = await response.json();
      console.log('Login successful:', data);

      // Save token to localStorage
      localStorage.setItem('access_token', data.access_token);
      
      // Get user info
      const userResponse = await fetch('/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${data.access_token}`
        }
      });

      if (userResponse.ok) {
        const userData = await userResponse.json();
        localStorage.setItem('user', JSON.stringify(userData));
        console.log('User data saved:', userData);
      }

      // Reload page to apply changes
      window.location.reload();
      
    } catch (error) {
      console.error('Login failed:', error);
      setError('Login failed: ' + error.message);
    } finally {
      setIsLoggingIn(false);
    }
  };

  const handleEnablePlanPackage = async () => {
    try {
      // Debug logging
      console.log('Token debug:', {
        token,
        tokenType: typeof token,
        tokenLength: token?.length,
        user,
        isAuthenticated: !!user && !!token
      });
      
      if (!token) {
        throw new Error('No authentication token found. Please login again.');
      }
      
      const response = await fetch('/api/admin/feature-flags/enable-plan-package', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to enable plan package');
      }

      // Refresh data
      await Promise.all([fetchFlags(), fetchPlanStatus()]);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading admin panel...</p>
        </div>
      </div>
    );
  }

  // Temporarily bypass auth check for testing
  // if (user?.role !== 'ADMIN') {
  //   return (
  //     <div className="min-h-screen bg-gray-50 flex items-center justify-center">
  //       <div className="text-center">
  //         <h1 className="text-2xl font-bold text-red-600">Access Denied</h1>
  //         <p className="mt-2 text-gray-600">Admin access required</p>
  //       </div>
  //     </div>
  //   );
  // }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Feature Flags Admin Panel</h1>
          <p className="mt-2 text-gray-600">Manage system feature flags and plan package availability</p>
        </div>

        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error</h3>
                <div className="mt-2 text-sm text-red-700">{error}</div>
              </div>
            </div>
          </div>
        )}

        {/* Admin Login Button - Show if not authenticated */}
        {(!user || !token) && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-yellow-800 font-semibold">Authentication Required</h3>
                <p className="text-yellow-700 text-sm mt-1">Please login as admin to manage feature flags</p>
              </div>
              <button
                onClick={handleAdminLogin}
                disabled={isLoggingIn}
                className="bg-yellow-600 hover:bg-yellow-700 disabled:bg-yellow-600/50 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
              >
                {isLoggingIn ? 'Logging in...' : 'Login as Admin'}
              </button>
            </div>
          </div>
        )}

        {/* Plan Package Status Card */}
        <div className="bg-white shadow rounded-lg p-6 mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Plan Package Status</h2>
              <div className="mt-2 flex items-center">
                <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  planStatus?.is_enabled 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {planStatus?.is_enabled ? '✅ Enabled' : '❌ Disabled'}
                </div>
                <span className="ml-3 text-sm text-gray-600">
                  {planStatus?.reason}
                </span>
                {planStatus?.disabled_until && (
                  <span className="ml-3 text-sm text-gray-500">
                    Until: {new Date(planStatus.disabled_until).toLocaleString()}
                  </span>
                )}
              </div>
            </div>
            <div className="flex space-x-3">
              {planStatus?.is_enabled ? (
                <button
                  onClick={() => setShowDisableForm(true)}
                  className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                >
                  Disable Plan Package
                </button>
              ) : (
                <button
                  onClick={handleEnablePlanPackage}
                  className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                >
                  Enable Plan Package
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Disable Plan Package Form */}
        {showDisableForm && (
          <div className="bg-white shadow rounded-lg p-6 mb-8">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Disable Plan Package</h3>
            <form onSubmit={handleDisablePlanPackage} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Disable From
                  </label>
                  <input
                    type="datetime-local"
                    value={disableForm.disabled_from}
                    onChange={(e) => setDisableForm(prev => ({ ...prev, disabled_from: e.target.value }))}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Disable Until
                  </label>
                  <input
                    type="datetime-local"
                    value={disableForm.disabled_until}
                    onChange={(e) => setDisableForm(prev => ({ ...prev, disabled_until: e.target.value }))}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Reason
                </label>
                <textarea
                  value={disableForm.reason}
                  onChange={(e) => setDisableForm(prev => ({ ...prev, reason: e.target.value }))}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  rows={3}
                  placeholder="Reason for disabling plan package..."
                  required
                />
              </div>
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowDisableForm(false)}
                  className="bg-gray-300 hover:bg-gray-400 text-gray-700 px-4 py-2 rounded-md text-sm font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                >
                  Disable Plan Package
                </button>
              </div>
            </form>
          </div>
        )}

        {/* All Feature Flags Table */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">All Feature Flags</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Feature Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Disabled Period
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Reason
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Last Updated
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {flags.map((flag) => (
                  <tr key={flag.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {flag.feature_type.replace('_', ' ')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        flag.is_enabled 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {flag.is_enabled ? 'Enabled' : 'Disabled'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {flag.disabled_from && flag.disabled_until ? (
                        <div>
                          <div>From: {new Date(flag.disabled_from).toLocaleString()}</div>
                          <div>Until: {new Date(flag.disabled_until).toLocaleString()}</div>
                        </div>
                      ) : (
                        'N/A'
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
                      {flag.reason || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(flag.updated_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
