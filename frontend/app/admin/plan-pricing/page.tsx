'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { UserRole } from '@/lib/types'
import { useAuthGuard } from '@/hooks/useAuthGuard'
import config from '@/lib/config'
import toast from 'react-hot-toast'
import { 
  CurrencyDollarIcon, 
  SparklesIcon, 
  PencilIcon, 
  CheckIcon,
  XMarkIcon 
} from '@heroicons/react/24/outline'

interface PlanPricing {
  id: number
  plan_name: string
  original_price_usd: number
  discount_percentage: number
  current_price_usd: number
  campaign_name: string | null
  campaign_active: boolean
  campaign_start_date: string | null
  campaign_end_date: string | null
  created_at: string
  updated_at: string
}

export default function AdminPlanPricingPage() {
  const { user, loading: authLoading } = useAuthGuard({ 
    requireAuth: true,
    requiredRole: UserRole.ADMIN 
  })
  
  const [pricings, setPricings] = useState<PlanPricing[]>([])
  const [loading, setLoading] = useState(true)
  const [editingPlan, setEditingPlan] = useState<string | null>(null)
  const [editForm, setEditForm] = useState<{
    original_price_usd: number
    discount_percentage: number
    campaign_name: string
    campaign_active: boolean
  }>({
    original_price_usd: 0,
    discount_percentage: 0,
    campaign_name: '',
    campaign_active: true
  })

  useEffect(() => {
    if (user) {
      fetchPricings()
    }
  }, [user])

  const fetchPricings = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('access_token')
      console.log('🔵 Fetching plan pricing with token:', token ? 'EXISTS' : 'MISSING')
      
      const response = await fetch(`${config.studioBaseUrl}/admin/plan-pricing/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      console.log('🔵 Response status:', response.status)

      if (response.ok) {
        const data = await response.json()
        console.log('✅ Plan pricing data:', data)
        
        // Convert price strings to numbers
        const normalizedData = data.map((p: any) => ({
          ...p,
          original_price_usd: parseFloat(p.original_price_usd) || 0,
          discount_percentage: parseFloat(p.discount_percentage) || 0,
          current_price_usd: parseFloat(p.current_price_usd) || 0
        }))
        
        setPricings(normalizedData)
        toast.success(`Loaded ${data.length} plan pricing templates`)
      } else {
        const error = await response.json()
        console.error('❌ Error response:', error)
        toast.error(error.detail || 'Failed to load plan pricing')
      }
    } catch (error) {
      console.error('❌ Error fetching pricings:', error)
      toast.error('Failed to load plan pricing: ' + (error instanceof Error ? error.message : 'Unknown error'))
    } finally {
      setLoading(false)
    }
  }

  const handleEdit = (pricing: PlanPricing) => {
    setEditingPlan(pricing.plan_name)
    setEditForm({
      original_price_usd: parseFloat(pricing.original_price_usd.toString()) || 0,
      discount_percentage: parseFloat(pricing.discount_percentage.toString()) || 0,
      campaign_name: pricing.campaign_name || '',
      campaign_active: pricing.campaign_active
    })
  }

  const handleSave = async (planName: string) => {
    try {
      const token = localStorage.getItem('access_token')
      
      // Ensure numbers are sent as numbers
      const payload = {
        original_price_usd: parseFloat(editForm.original_price_usd.toString()),
        discount_percentage: parseFloat(editForm.discount_percentage.toString()),
        campaign_name: editForm.campaign_name || null,
        campaign_active: editForm.campaign_active
      }
      
      console.log('💾 Saving pricing:', payload)
      
      const response = await fetch(`${config.studioBaseUrl}/admin/plan-pricing/${planName}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      })

      if (response.ok) {
        toast.success('Plan pricing updated successfully')
        setEditingPlan(null)
        fetchPricings()
      } else {
        const error = await response.json()
        toast.error(error.detail || 'Failed to update pricing')
      }
    } catch (error) {
      console.error('Error updating pricing:', error)
      toast.error('Failed to update pricing')
    }
  }

  const handleCancel = () => {
    setEditingPlan(null)
  }

  const getPlanDisplayName = (planName: string) => {
    const names: Record<string, string> = {
      'free': 'Free Plan',
      'pro': 'Pro Plan',
      'ultra': 'Ultra Plan'
    }
    return names[planName] || planName
  }

  const getPlanColor = (planName: string) => {
    const colors: Record<string, string> = {
      'free': 'from-gray-500 to-gray-600',
      'pro': 'from-blue-500 to-purple-600',
      'ultra': 'from-purple-500 to-pink-600'
    }
    return colors[planName] || 'from-gray-500 to-gray-600'
  }

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-400">Authenticating...</p>
        </div>
      </div>
    )
  }
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-600 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading plan pricing...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <CurrencyDollarIcon className="h-10 w-10 text-yellow-500" />
          <h1 className="text-4xl font-extrabold text-white">
            Plan Pricing Management
          </h1>
        </div>
        <p className="text-xl text-gray-400">
          Manage pricing and discounts for all subscription plans
        </p>
      </div>

      {/* Pricing Cards */}
      {pricings.length === 0 ? (
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-12 text-center">
          <div className="text-gray-500 mb-4">
            <CurrencyDollarIcon className="h-16 w-16 mx-auto mb-4 opacity-50" />
            <p className="text-lg">No pricing templates found</p>
            <p className="text-sm mt-2">Data will appear here once loaded from the database</p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {pricings.map((pricing) => (
          <div 
            key={pricing.id} 
            className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden hover:border-blue-500 transition-all"
          >
            {/* Plan Header */}
            <div className={`bg-gradient-to-r ${getPlanColor(pricing.plan_name)} p-6`}>
              <h3 className="text-2xl font-bold text-white mb-1">
                {getPlanDisplayName(pricing.plan_name)}
              </h3>
              {pricing.campaign_name && pricing.campaign_active && (
                <div className="flex items-center gap-1 text-yellow-300 text-sm">
                  <SparklesIcon className="h-4 w-4" />
                  <span>{pricing.campaign_name}</span>
                </div>
              )}
            </div>

            {/* Pricing Content */}
            <div className="p-6">
              {editingPlan === pricing.plan_name ? (
                // Edit Mode
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">
                      Original Price (USD)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={editForm.original_price_usd}
                      onChange={(e) => setEditForm({ ...editForm, original_price_usd: parseFloat(e.target.value) })}
                      className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">
                      Discount (%)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      max="100"
                      value={editForm.discount_percentage}
                      onChange={(e) => setEditForm({ ...editForm, discount_percentage: parseFloat(e.target.value) })}
                      className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">
                      Campaign Name
                    </label>
                    <input
                      type="text"
                      value={editForm.campaign_name}
                      onChange={(e) => setEditForm({ ...editForm, campaign_name: e.target.value })}
                      className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
                      placeholder="e.g., Quantum Launch Campaign"
                    />
                  </div>

                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id={`active-${pricing.plan_name}`}
                      checked={editForm.campaign_active}
                      onChange={(e) => setEditForm({ ...editForm, campaign_active: e.target.checked })}
                      className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500"
                    />
                    <label htmlFor={`active-${pricing.plan_name}`} className="text-sm text-gray-300">
                      Campaign Active
                    </label>
                  </div>

                  {/* Preview Current Price */}
                  <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-3">
                    <div className="text-xs text-gray-400 mb-1">Preview Price:</div>
                    <div className="text-2xl font-bold text-green-400">
                      ${(editForm.original_price_usd * (1 - editForm.discount_percentage / 100)).toFixed(2)}
                      <span className="text-sm text-gray-400"> /month</span>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-2 pt-2">
                    <button
                      onClick={() => handleSave(pricing.plan_name)}
                      className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors flex items-center justify-center gap-2"
                    >
                      <CheckIcon className="h-5 w-5" />
                      Save
                    </button>
                    <button
                      onClick={handleCancel}
                      className="flex-1 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors flex items-center justify-center gap-2"
                    >
                      <XMarkIcon className="h-5 w-5" />
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                // View Mode
                <div className="space-y-4">
                  {/* Current Price */}
                  <div>
                    <div className="text-sm text-gray-400 mb-1">Current Price</div>
                    <div className="text-4xl font-bold text-green-400">
                      ${pricing.current_price_usd.toFixed(2)}
                      <span className="text-lg text-gray-400"> /month</span>
                    </div>
                  </div>

                  {/* Original Price & Discount */}
                  {pricing.discount_percentage > 0 && (
                    <div className="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-3">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-gray-400">Original Price:</span>
                        <span className="text-lg text-gray-400 line-through">
                          ${pricing.original_price_usd.toFixed(2)}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-400">Discount:</span>
                        <span className="text-xl font-bold text-yellow-400">
                          {pricing.discount_percentage}% OFF
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Edit Button */}
                  <button
                    onClick={() => handleEdit(pricing)}
                    className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center justify-center gap-2"
                  >
                    <PencilIcon className="h-5 w-5" />
                    Edit Pricing
                  </button>
                </div>
              )}
            </div>

            {/* Footer Info */}
            <div className="px-6 py-3 bg-gray-900/50 border-t border-gray-700">
              <div className="text-xs text-gray-500">
                Last updated: {new Date(pricing.updated_at).toLocaleDateString()}
              </div>
            </div>
          </div>
        ))}
        </div>
      )}
    </div>
  )
}

