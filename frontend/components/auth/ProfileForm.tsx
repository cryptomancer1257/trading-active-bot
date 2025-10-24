'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useAuth } from '@/contexts/AuthContext'
import { UserRole } from '@/lib/types'
import { UserIcon, CogIcon } from '@heroicons/react/24/outline'

const profileSchema = z.object({
  developer_name: z.string().optional(),
  developer_bio: z.string().optional(),
  developer_website: z.string().url('Invalid website URL').optional().or(z.literal('')),
  telegram_username: z.string().optional(),
  discord_username: z.string().optional(),
})

type ProfileFormData = z.infer<typeof profileSchema>

export default function ProfileForm() {
  const [isLoading, setIsLoading] = useState(false)
  const { user, updateProfile } = useAuth()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      developer_name: user?.developer_name || '',
      developer_bio: user?.developer_bio || '',
      developer_website: user?.developer_website || '',
      telegram_username: user?.telegram_username || '',
      discord_username: user?.discord_username || '',
    },
  })

  const onSubmit = async (data: ProfileFormData) => {
    setIsLoading(true)
    try {
      await updateProfile(data)
    } finally {
      setIsLoading(false)
    }
  }

  if (!user) return null

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="flex items-center space-x-3 mb-6">
            <UserIcon className="h-8 w-8 text-gray-400" />
            <div>
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                Personal Information
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                Update your profile information
              </p>
            </div>
          </div>

          {/* User Basic Info */}
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 mb-8">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Email
              </label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <input
                  type="email"
                  value={user.email}
                  disabled
                  className="block w-full pr-10 border-gray-300 bg-gray-50 text-gray-500 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Role
              </label>
              <div className="mt-1">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  user.role === UserRole.ADMIN 
                    ? 'bg-red-100 text-red-800'
                    : user.role === UserRole.DEVELOPER
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {user.role === UserRole.ADMIN && 'Administrator'}
                  {user.role === UserRole.DEVELOPER && 'Developer'}
                  {user.role === UserRole.USER && 'User'}
                </span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Join Date
              </label>
              <div className="mt-1 text-sm text-gray-900">
                {new Date(user.created_at).toLocaleDateString('en-US')}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Status
              </label>
              <div className="mt-1">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {user.is_active ? 'Active' : 'Suspended'}
                </span>
              </div>
            </div>
          </div>

          {/* Developer Profile Form */}
          {(user.role === UserRole.DEVELOPER || user.role === UserRole.ADMIN) && (
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              <div className="border-t border-gray-200 pt-6">
                <div className="flex items-center space-x-3 mb-4">
                  <CogIcon className="h-6 w-6 text-gray-400" />
                  <h4 className="text-base font-medium text-gray-900">
                    Developer Information
                  </h4>
                </div>

                <div className="grid grid-cols-1 gap-6">
                  <div>
                    <label htmlFor="developer_name" className="form-label">
                      Display Name
                    </label>
                    <input
                      {...register('developer_name')}
                      type="text"
                      id="developer_name"
                      className="form-input"
                      placeholder="Enter your display name"
                    />
                    {errors.developer_name && (
                      <p className="form-error">{errors.developer_name.message}</p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="developer_bio" className="form-label">
                      About Yourself
                    </label>
                    <textarea
                      {...register('developer_bio')}
                      id="developer_bio"
                      rows={4}
                      className="form-input"
                      placeholder="Describe yourself, your experience and expertise..."
                    />
                    {errors.developer_bio && (
                      <p className="form-error">{errors.developer_bio.message}</p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="developer_website" className="form-label">
                      Website
                    </label>
                    <input
                      {...register('developer_website')}
                      type="url"
                      id="developer_website"
                      className="form-input"
                      placeholder="https://example.com"
                    />
                    {errors.developer_website && (
                      <p className="form-error">{errors.developer_website.message}</p>
                    )}
                  </div>

                  <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                    <div>
                      <label htmlFor="telegram_username" className="form-label">
                        Telegram Username
                      </label>
                      <div className="mt-1 flex rounded-md shadow-sm">
                        <span className="inline-flex items-center px-3 rounded-l-md border border-r-0 border-gray-300 bg-gray-50 text-gray-500 text-sm">
                          @
                        </span>
                        <input
                          {...register('telegram_username')}
                          type="text"
                          id="telegram_username"
                          className="form-input rounded-l-none"
                          placeholder="username"
                        />
                      </div>
                      <p className="mt-1 text-sm text-gray-500">
                        To receive notifications from bot (exclude @)
                      </p>
                      {errors.telegram_username && (
                        <p className="form-error">{errors.telegram_username.message}</p>
                      )}
                    </div>

                    <div>
                      <label htmlFor="discord_username" className="form-label">
                        Discord Username
                      </label>
                      <input
                        {...register('discord_username')}
                        type="text"
                        id="discord_username"
                        className="form-input"
                        placeholder="username#1234"
                      />
                      <p className="mt-1 text-sm text-gray-500">
                        To receive notifications from bot
                      </p>
                      {errors.discord_username && (
                        <p className="form-error">{errors.discord_username.message}</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={isLoading}
                  className="btn btn-primary px-6 py-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Saving...
                    </>
                  ) : (
                    'Save Changes'
                  )}
                </button>
              </div>
            </form>
          )}

          {/* Statistics for developers */}
          {user.role === UserRole.DEVELOPER && (
            <div className="border-t border-gray-200 pt-6 mt-8">
              <h4 className="text-base font-medium text-gray-900 mb-4">
                Statistics
              </h4>
              <div className="grid grid-cols-2 gap-6 sm:grid-cols-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-primary-600">
                    {user.total_developed_bots || 0}
                  </div>
                  <div className="text-sm text-gray-500">Bots Created</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-success-600">
                    {user.approved_bots || 0}
                  </div>
                  <div className="text-sm text-gray-500">Bots Approved</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {user.total_subscriptions || 0}
                  </div>
                  <div className="text-sm text-gray-500">Total Subscriptions</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {user.active_subscriptions || 0}
                  </div>
                  <div className="text-sm text-gray-500">Active</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

