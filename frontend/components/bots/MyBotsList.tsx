'use client'

import { useState } from 'react'
import { useMyBots, useDeleteBot } from '@/hooks/useBots'
import { Bot, BotStatus, BotType } from '@/lib/types'
import { 
  PencilIcon, 
  TrashIcon, 
  EyeIcon,
  PlusIcon,
  ChartBarIcon,
  UserGroupIcon,
  StarIcon 
} from '@heroicons/react/24/outline'
import { CheckCircleIcon, ClockIcon, XCircleIcon, ArchiveBoxIcon } from '@heroicons/react/24/solid'
import Link from 'next/link'
import clsx from 'clsx'
import { format } from 'date-fns'

export default function MyBotsList() {
  const [selectedBot, setSelectedBot] = useState<Bot | null>(null)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  
  const { data: bots, isLoading, error } = useMyBots()
  const deleteBot = useDeleteBot()

  const handleDelete = async () => {
    if (selectedBot) {
      try {
        await deleteBot.mutateAsync(selectedBot.id)
        setShowDeleteModal(false)
        setSelectedBot(null)
      } catch (error) {
        console.error('Delete failed:', error)
      }
    }
  }

  const getStatusBadge = (status: BotStatus) => {
    switch (status) {
      case BotStatus.APPROVED:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
            <CheckCircleIcon className="w-4 h-4 mr-1" />
            Đã duyệt
          </span>
        )
      case BotStatus.PENDING:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
            <ClockIcon className="w-4 h-4 mr-1" />
            Chờ duyệt
          </span>
        )
      case BotStatus.REJECTED:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
            <XCircleIcon className="w-4 h-4 mr-1" />
            Bị từ chối
          </span>
        )
      case BotStatus.ARCHIVED:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
            <ArchiveBoxIcon className="w-4 h-4 mr-1" />
            Đã lưu trữ
          </span>
        )
      default:
        return null
    }
  }

  const getBotTypeColor = (botType: BotType) => {
    switch (botType) {
      case BotType.TECHNICAL: return 'bg-blue-100 text-blue-800'
      case BotType.ML: return 'bg-green-100 text-green-800'
      case BotType.DL: return 'bg-purple-100 text-purple-800'
      case BotType.LLM: return 'bg-pink-100 text-pink-800'
      case BotType.FUTURES: return 'bg-orange-100 text-orange-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getBotTypeName = (botType: BotType) => {
    switch (botType) {
      case BotType.TECHNICAL: return 'Phân tích kỹ thuật'
      case BotType.ML: return 'Machine Learning'
      case BotType.DL: return 'Deep Learning'
      case BotType.LLM: return 'AI Language Model'
      case BotType.FUTURES: return 'Futures Trading'
      default: return botType
    }
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600">Có lỗi xảy ra khi tải danh sách bot</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Bot của tôi</h1>
          <p className="text-gray-600">Quản lý và theo dõi các bot trading của bạn</p>
        </div>
        <Link href="/developer/create-bot">
          <button className="btn btn-primary flex items-center px-4 py-2">
            <PlusIcon className="h-5 w-5 mr-2" />
            Tạo Bot mới
          </button>
        </Link>
      </div>

      {/* Stats Cards */}
      {bots && bots.length > 0 && (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <ChartBarIcon className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Tổng bot
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {bots.length}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <CheckCircleIcon className="h-6 w-6 text-green-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Đã duyệt
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {bots.filter(bot => bot.status === BotStatus.APPROVED).length}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <UserGroupIcon className="h-6 w-6 text-blue-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Tổng người dùng
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {bots.reduce((sum, bot) => sum + bot.total_subscribers, 0)}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <StarIcon className="h-6 w-6 text-yellow-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Đánh giá TB
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {bots.length > 0 
                        ? (bots.reduce((sum, bot) => sum + bot.average_rating, 0) / bots.length).toFixed(1)
                        : '0.0'
                      }
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Bots List */}
      {isLoading ? (
        <div className="grid grid-cols-1 gap-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="bg-white shadow rounded-lg animate-pulse">
              <div className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="h-4 bg-gray-200 rounded w-1/4 mb-2"></div>
                    <div className="h-3 bg-gray-200 rounded w-3/4"></div>
                  </div>
                  <div className="ml-4">
                    <div className="h-8 bg-gray-200 rounded w-20"></div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : bots && bots.length > 0 ? (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul className="divide-y divide-gray-200">
            {bots.map((bot) => (
              <li key={bot.id}>
                <div className="px-4 py-4 sm:px-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center min-w-0 flex-1">
                      {/* Bot Image/Icon */}
                      <div className="flex-shrink-0 mr-4">
                        {bot.image_url ? (
                          <img
                            className="h-12 w-12 rounded-lg object-cover"
                            src={bot.image_url}
                            alt={bot.name}
                          />
                        ) : (
                          <div className="h-12 w-12 rounded-lg bg-gradient-to-br from-primary-100 to-primary-200 flex items-center justify-center">
                            <span className="text-primary-600 font-bold text-lg">
                              {bot.name.charAt(0).toUpperCase()}
                            </span>
                          </div>
                        )}
                      </div>

                      <div className="min-w-0 flex-1">
                        <div className="flex items-center space-x-2 mb-1">
                          <h3 className="text-lg font-medium text-gray-900 truncate">
                            {bot.name}
                          </h3>
                          <span className={clsx(
                            'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                            getBotTypeColor(bot.bot_type as BotType)
                          )}>
                            {getBotTypeName(bot.bot_type as BotType)}
                          </span>
                          {getStatusBadge(bot.status as BotStatus)}
                        </div>

                        <p className="text-sm text-gray-600 mb-2 line-clamp-2">
                          {bot.description}
                        </p>

                        <div className="flex items-center text-xs text-gray-500 space-x-4">
                          <span>v{bot.version}</span>
                          <span>{(bot as any).total_subscribers || 0} người dùng</span>
                          <span className="flex items-center">
                            <StarIcon className="h-3 w-3 text-yellow-400 mr-1" />
                            {(bot as any).average_rating?.toFixed(1) || '0.0'} ({(bot as any).total_reviews || 0} đánh giá)
                          </span>
                          <span>
                            Tạo {format(new Date(bot.created_at), 'dd/MM/yyyy')}
                          </span>
                          {(bot as any).is_free ? (
                            <span className="text-green-600 font-medium">Miễn phí</span>
                          ) : (
                            <span className="text-gray-900 font-medium">
                              ${(bot as any).price_per_month || 0}/tháng
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center space-x-2 ml-4">
                      <Link href={`/creator/entities/${bot.id}`}>
                        <button className="p-2 text-gray-400 hover:text-gray-600 rounded-md hover:bg-gray-100" title="View Details">
                          <EyeIcon className="h-5 w-5" />
                        </button>
                      </Link>
                      
                      <Link href={`/creator/entities/${bot.id}/edit`}>
                        <button className="p-2 text-blue-400 hover:text-blue-600 rounded-md hover:bg-blue-50" title="Edit Bot">
                          <PencilIcon className="h-5 w-5" />
                        </button>
                      </Link>

                      <button
                        onClick={() => {
                          setSelectedBot(bot as any)
                          setShowDeleteModal(true)
                        }}
                        className="p-2 text-red-400 hover:text-red-600 rounded-md hover:bg-red-50"
                        title="Delete Bot"
                      >
                        <TrashIcon className="h-5 w-5" />
                      </button>
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <div className="text-center py-12">
          <div className="mx-auto h-12 w-12 text-gray-400">
            <ChartBarIcon />
          </div>
          <h3 className="mt-2 text-sm font-medium text-gray-900">Chưa có bot nào</h3>
          <p className="mt-1 text-sm text-gray-500">
            Bắt đầu bằng cách tạo bot trading đầu tiên của bạn.
          </p>
          <div className="mt-6">
            <Link href="/developer/create-bot">
              <button className="btn btn-primary flex items-center px-4 py-2">
                <PlusIcon className="h-5 w-5 mr-2" />
                Tạo Bot mới
              </button>
            </Link>
          </div>
        </div>
      )}

      {/* Delete Modal */}
      {showDeleteModal && selectedBot && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3 text-center">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
                <TrashIcon className="h-6 w-6 text-red-600" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mt-2">Xóa Bot</h3>
              <div className="mt-2 px-7 py-3">
                <p className="text-sm text-gray-500">
                  Bạn có chắc chắn muốn xóa bot "{selectedBot.name}"? 
                  Hành động này không thể hoàn tác.
                </p>
              </div>
              <div className="items-center px-4 py-3">
                <button
                  onClick={handleDelete}
                  disabled={deleteBot.isPending}
                  className="px-4 py-2 bg-red-500 text-white text-base font-medium rounded-md shadow-sm hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-red-300 mr-3 disabled:opacity-50"
                >
                  {deleteBot.isPending ? 'Đang xóa...' : 'Xóa'}
                </button>
                <button
                  onClick={() => {
                    setShowDeleteModal(false)
                    setSelectedBot(null)
                  }}
                  className="px-4 py-2 bg-gray-500 text-white text-base font-medium rounded-md shadow-sm hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-300"
                >
                  Hủy
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

