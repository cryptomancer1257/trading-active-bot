'use client'

import { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { 
  BellIcon, 
  GlobeAltIcon, 
  ShieldCheckIcon, 
  PaintBrushIcon,
  MoonIcon,
  SunIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

export default function SettingsPage() {
  const { user } = useAuth()
  
  // Notification settings
  const [emailNotifications, setEmailNotifications] = useState(true)
  const [tradeAlerts, setTradeAlerts] = useState(true)
  const [botStatusAlerts, setBotStatusAlerts] = useState(true)
  const [weeklyReports, setWeeklyReports] = useState(false)
  
  // Display settings
  const [theme, setTheme] = useState<'dark' | 'light'>('dark')
  const [language, setLanguage] = useState('en')
  const [timezone, setTimezone] = useState('UTC')
  
  // Privacy settings
  const [profileVisibility, setProfileVisibility] = useState<'public' | 'private'>('public')
  const [showStats, setShowStats] = useState(true)
  
  const [saving, setSaving] = useState(false)

  const handleSaveSettings = async () => {
    setSaving(true)
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      const settings = {
        notifications: {
          email: emailNotifications,
          trade_alerts: tradeAlerts,
          bot_status: botStatusAlerts,
          weekly_reports: weeklyReports
        },
        display: {
          theme,
          language,
          timezone
        },
        privacy: {
          profile_visibility: profileVisibility,
          show_stats: showStats
        }
      }
      
      // Here you would make an API call to save settings
      console.log('Saving settings:', settings)
      
      toast.success('✅ Settings saved successfully!')
    } catch (error) {
      console.error('Error saving settings:', error)
      toast.error('❌ Failed to save settings')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-dark-900 via-dark-800 to-dark-900 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2 flex items-center">
            <ShieldCheckIcon className="h-8 w-8 mr-3 text-quantum-500" />
            Settings
          </h1>
          <p className="text-gray-400">Customize your QuantumForge experience</p>
        </div>

        {/* User Info */}
        <div className="bg-dark-800/50 backdrop-blur-md border border-quantum-500/20 rounded-lg p-6 mb-6 shadow-xl">
          <div className="flex items-center">
            <div className="h-16 w-16 rounded-full bg-gradient-to-r from-quantum-600 to-cyber-600 flex items-center justify-center">
              <span className="text-2xl font-bold text-white">
                {user?.developer_name?.charAt(0).toUpperCase() || user?.email?.charAt(0).toUpperCase()}
              </span>
            </div>
            <div className="ml-4">
              <h2 className="text-xl font-semibold text-white">{user?.developer_name || user?.email}</h2>
              <p className="text-gray-400">{user?.email}</p>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-quantum-500/20 text-quantum-400 mt-2">
                {user?.role}
              </span>
            </div>
          </div>
        </div>

        {/* Notification Settings */}
        <div className="bg-dark-800/50 backdrop-blur-md border border-quantum-500/20 rounded-lg p-6 mb-6 shadow-xl">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <BellIcon className="h-5 w-5 mr-2 text-quantum-500" />
            Notification Preferences
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-300">Email Notifications</label>
                <p className="text-xs text-gray-500">Receive updates via email</p>
              </div>
              <button
                onClick={() => setEmailNotifications(!emailNotifications)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  emailNotifications ? 'bg-quantum-600' : 'bg-gray-600'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    emailNotifications ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-300">Trade Alerts</label>
                <p className="text-xs text-gray-500">Get notified about trade executions</p>
              </div>
              <button
                onClick={() => setTradeAlerts(!tradeAlerts)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  tradeAlerts ? 'bg-quantum-600' : 'bg-gray-600'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    tradeAlerts ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-300">Bot Status Alerts</label>
                <p className="text-xs text-gray-500">Monitor bot health and errors</p>
              </div>
              <button
                onClick={() => setBotStatusAlerts(!botStatusAlerts)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  botStatusAlerts ? 'bg-quantum-600' : 'bg-gray-600'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    botStatusAlerts ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-300">Weekly Reports</label>
                <p className="text-xs text-gray-500">Receive performance summaries</p>
              </div>
              <button
                onClick={() => setWeeklyReports(!weeklyReports)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  weeklyReports ? 'bg-quantum-600' : 'bg-gray-600'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    weeklyReports ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>
        </div>

        {/* Display Settings */}
        <div className="bg-dark-800/50 backdrop-blur-md border border-quantum-500/20 rounded-lg p-6 mb-6 shadow-xl">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <PaintBrushIcon className="h-5 w-5 mr-2 text-quantum-500" />
            Display & Language
          </h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Theme</label>
              <div className="flex gap-3">
                <button
                  onClick={() => setTheme('dark')}
                  className={`flex-1 flex items-center justify-center px-4 py-3 rounded-lg border-2 transition-all ${
                    theme === 'dark'
                      ? 'border-quantum-500 bg-quantum-500/20 text-white'
                      : 'border-gray-600 bg-dark-700 text-gray-400 hover:border-gray-500'
                  }`}
                >
                  <MoonIcon className="h-5 w-5 mr-2" />
                  Dark
                  {theme === 'dark' && <CheckCircleIcon className="h-5 w-5 ml-2" />}
                </button>
                <button
                  onClick={() => setTheme('light')}
                  className={`flex-1 flex items-center justify-center px-4 py-3 rounded-lg border-2 transition-all ${
                    theme === 'light'
                      ? 'border-quantum-500 bg-quantum-500/20 text-white'
                      : 'border-gray-600 bg-dark-700 text-gray-400 hover:border-gray-500'
                  }`}
                >
                  <SunIcon className="h-5 w-5 mr-2" />
                  Light
                  {theme === 'light' && <CheckCircleIcon className="h-5 w-5 ml-2" />}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Language</label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full px-4 py-2 bg-dark-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-quantum-500"
              >
                <option value="en">English</option>
                <option value="vi">Tiếng Việt</option>
                <option value="zh">中文</option>
                <option value="ja">日本語</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Timezone</label>
              <select
                value={timezone}
                onChange={(e) => setTimezone(e.target.value)}
                className="w-full px-4 py-2 bg-dark-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-quantum-500"
              >
                <option value="UTC">UTC</option>
                <option value="Asia/Ho_Chi_Minh">Asia/Ho Chi Minh (UTC+7)</option>
                <option value="America/New_York">America/New York (EST)</option>
                <option value="Europe/London">Europe/London (GMT)</option>
                <option value="Asia/Tokyo">Asia/Tokyo (JST)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Privacy Settings */}
        <div className="bg-dark-800/50 backdrop-blur-md border border-quantum-500/20 rounded-lg p-6 mb-6 shadow-xl">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <ShieldCheckIcon className="h-5 w-5 mr-2 text-quantum-500" />
            Privacy & Security
          </h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Profile Visibility</label>
              <select
                value={profileVisibility}
                onChange={(e) => setProfileVisibility(e.target.value as 'public' | 'private')}
                className="w-full px-4 py-2 bg-dark-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-quantum-500"
              >
                <option value="public">Public - Anyone can see your profile</option>
                <option value="private">Private - Only you can see your profile</option>
              </select>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-300">Show Statistics</label>
                <p className="text-xs text-gray-500">Display your trading stats on profile</p>
              </div>
              <button
                onClick={() => setShowStats(!showStats)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  showStats ? 'bg-quantum-600' : 'bg-gray-600'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    showStats ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end">
          <button
            onClick={handleSaveSettings}
            disabled={saving}
            className="px-6 py-3 bg-gradient-to-r from-quantum-600 to-cyber-600 hover:from-quantum-700 hover:to-cyber-700 disabled:from-gray-600 disabled:to-gray-700 text-white font-semibold rounded-lg transition-all duration-200 transform hover:scale-105 disabled:scale-100 disabled:cursor-not-allowed shadow-lg"
          >
            {saving ? (
              <>
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Saving...
              </>
            ) : (
              'Save Settings'
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

