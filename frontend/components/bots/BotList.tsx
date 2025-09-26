'use client'

import { useState } from 'react'
import { usePublicBots } from '@/hooks/useBots'
import { Bot, BotStatus, BotType } from '@/lib/types'
import { MagnifyingGlassIcon, FunnelIcon, StarIcon } from '@heroicons/react/24/outline'
import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/20/solid'
import Link from 'next/link'
import clsx from 'clsx'

interface BotListProps {
  showFilters?: boolean
  showPagination?: boolean
}

export default function BotList({ showFilters = true, showPagination = true }: BotListProps) {
  const [filters, setFilters] = useState({
    search: '',
    category_id: undefined as number | undefined,
    sort_by: 'created_at',
    order: 'desc',
    skip: 0,
    limit: 12,
  })

  const { data: botsData, isLoading, error } = usePublicBots()
  const categories: any[] = [] // Removed useBotCategories

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setFilters(prev => ({ ...prev, skip: 0 }))
  }

  const handleFilterChange = (key: string, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value, skip: 0 }))
  }

  const handlePageChange = (newSkip: number) => {
    setFilters(prev => ({ ...prev, skip: newSkip }))
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
      {/* Filters */}
      {showFilters && (
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex flex-col sm:flex-row gap-4">
            {/* Search */}
            <form onSubmit={handleSearch} className="flex-1">
              <div className="relative">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Tìm kiếm bot..."
                  value={filters.search}
                  onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                  className="pl-10 form-input"
                />
              </div>
            </form>

            {/* Category Filter */}
            <select
              value={filters.category_id || ''}
              onChange={(e) => handleFilterChange('category_id', e.target.value ? parseInt(e.target.value) : undefined)}
              className="form-input w-full sm:w-48"
            >
              <option value="">Tất cả danh mục</option>
              {categories?.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>

            {/* Sort */}
            <select
              value={`${filters.sort_by}-${filters.order}`}
              onChange={(e) => {
                const [sort_by, order] = e.target.value.split('-')
                handleFilterChange('sort_by', sort_by)
                handleFilterChange('order', order)
              }}
              className="form-input w-full sm:w-48"
            >
              <option value="created_at-desc">Mới nhất</option>
              <option value="created_at-asc">Cũ nhất</option>
              <option value="total_subscribers-desc">Phổ biến nhất</option>
              <option value="average_rating-desc">Đánh giá cao</option>
              <option value="name-asc">Tên A-Z</option>
            </select>
          </div>
        </div>
      )}

      {/* Bot Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="bg-white rounded-lg shadow-sm border animate-pulse">
              <div className="h-48 bg-gray-200 rounded-t-lg"></div>
              <div className="p-4 space-y-3">
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                <div className="h-3 bg-gray-200 rounded w-full"></div>
                <div className="h-3 bg-gray-200 rounded w-2/3"></div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {botsData?.map((bot) => (
            <Link key={bot.id} href={`/marketplace/${bot.id}`}>
              <div className="bg-white rounded-lg shadow-sm border hover:shadow-md transition-shadow cursor-pointer">
                {/* Bot Image */}
                <div className="h-48 bg-gradient-to-br from-primary-100 to-primary-200 rounded-t-lg flex items-center justify-center">
                  {bot.image_url ? (
                    <img
                      src={bot.image_url}
                      alt={bot.name}
                      className="w-full h-full object-cover rounded-t-lg"
                    />
                  ) : (
                    <div className="text-primary-600 text-6xl font-bold">
                      {bot.name.charAt(0).toUpperCase()}
                    </div>
                  )}
                </div>

                <div className="p-4">
                  {/* Bot Type Badge */}
                  <div className="mb-2">
                    <span className={clsx(
                      'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                      getBotTypeColor(bot.bot_type as BotType)
                    )}>
                      {getBotTypeName(bot.bot_type as BotType)}
                    </span>
                  </div>

                  {/* Bot Name */}
                  <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-1">
                    {bot.name}
                  </h3>

                  {/* Bot Description */}
                  <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                    {bot.description}
                  </p>

                  {/* Stats */}
                  <div className="flex items-center justify-between text-sm text-gray-500">
                    <div className="flex items-center">
                      <StarIcon className="h-4 w-4 text-yellow-400 mr-1" />
                      <span>{(bot as any).average_rating?.toFixed(1) || '0.0'}</span>
                      <span className="ml-1">({(bot as any).total_reviews || 0})</span>
                    </div>
                    <div>
                      {(bot as any).total_subscribers || 0} người dùng
                    </div>
                  </div>

                  {/* Price */}
                  <div className="mt-3 pt-3 border-t">
                    {(bot as any).is_free ? (
                      <span className="text-lg font-bold text-success-600">Miễn phí</span>
                    ) : (
                      <span className="text-lg font-bold text-gray-900">
                        ${(bot as any).price_per_month || 0}/tháng
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && botsData?.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-500 text-lg">Không tìm thấy bot nào</div>
          <p className="text-gray-400 mt-2">Thử thay đổi bộ lọc hoặc từ khóa tìm kiếm</p>
        </div>
      )}

      {/* Pagination */}
      {showPagination && botsData && botsData.length >= filters.limit && (
        <div className="flex items-center justify-between border-t border-gray-200 bg-white px-4 py-3 sm:px-6 rounded-lg">
          <div className="flex flex-1 justify-between sm:hidden">
            <button
              onClick={() => handlePageChange(Math.max(0, filters.skip - filters.limit))}
              disabled={filters.skip === 0}
              className="relative inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              Trước
            </button>
            <button
              onClick={() => handlePageChange(filters.skip + filters.limit)}
              disabled={botsData.length < filters.limit}
              className="relative ml-3 inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              Sau
            </button>
          </div>
          <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
            <div>
              <p className="text-sm text-gray-700">
                Hiển thị{' '}
                <span className="font-medium">{filters.skip + 1}</span> đến{' '}
                <span className="font-medium">
                  {Math.min(filters.skip + filters.limit, botsData.length)}
                </span>{' '}
                trong tổng số <span className="font-medium">{botsData.length}+</span> kết quả
              </p>
            </div>
            <div>
              <nav className="isolate inline-flex -space-x-px rounded-md shadow-sm" aria-label="Pagination">
                <button
                  onClick={() => handlePageChange(Math.max(0, filters.skip - filters.limit))}
                  disabled={filters.skip === 0}
                  className="relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50"
                >
                  <ChevronLeftIcon className="h-5 w-5" aria-hidden="true" />
                </button>
                <button
                  onClick={() => handlePageChange(filters.skip + filters.limit)}
                  disabled={botsData.length < filters.limit}
                  className="relative inline-flex items-center rounded-r-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50"
                >
                  <ChevronRightIcon className="h-5 w-5" aria-hidden="true" />
                </button>
              </nav>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

