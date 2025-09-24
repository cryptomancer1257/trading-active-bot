'use client'

import { useState, useEffect } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Bot, BotCreate, BotUpdate, BotType, ExchangeType } from '@/lib/types'
import { useBotCategories, useCreateBot, useUpdateBot, useUploadBotFile } from '@/hooks/useBots'
import { DocumentArrowUpIcon, XMarkIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

const botSchema = z.object({
  name: z.string().min(1, 'Tên bot là bắt buộc').max(255, 'Tên bot quá dài'),
  description: z.string().min(10, 'Mô tả phải có ít nhất 10 ký tự'),
  category_id: z.number().optional(),
  version: z.string().default('1.0.0'),
  bot_type: z.nativeEnum(BotType),
  price_per_month: z.number().min(0, 'Giá không được âm'),
  is_free: z.boolean(),
  exchange_type: z.nativeEnum(ExchangeType).optional(),
  trading_pair: z.string().optional(),
  timeframe: z.string().optional(),
  timeframes: z.array(z.string()).optional(),
  image_url: z.string().url().optional().or(z.literal('')),
})

type BotFormData = z.infer<typeof botSchema>

interface BotFormProps {
  bot?: Bot
  onSuccess?: () => void
  onCancel?: () => void
}

const timeframeOptions = [
  { value: '1m', label: '1 phút' },
  { value: '5m', label: '5 phút' },
  { value: '15m', label: '15 phút' },
  { value: '1h', label: '1 giờ' },
  { value: '2h', label: '2 giờ' },
  { value: '4h', label: '4 giờ' },
  { value: '6h', label: '6 giờ' },
  { value: '8h', label: '8 giờ' },
  { value: '12h', label: '12 giờ' },
  { value: '1d', label: '1 ngày' },
  { value: '1w', label: '1 tuần' },
]

export default function BotForm({ bot, onSuccess, onCancel }: BotFormProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  
  const { data: categories } = useBotCategories()
  const createBot = useCreateBot()
  const updateBot = useUpdateBot()
  const uploadFile = useUploadBotFile()

  const {
    register,
    handleSubmit,
    control,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<BotFormData>({
    resolver: zodResolver(botSchema),
    defaultValues: bot ? {
      name: bot.name,
      description: bot.description,
      category_id: bot.category_id || undefined,
      version: bot.version,
      bot_type: bot.bot_type,
      price_per_month: bot.price_per_month,
      is_free: bot.is_free,
      exchange_type: bot.exchange_type || ExchangeType.BINANCE,
      trading_pair: bot.trading_pair || '',
      timeframe: bot.timeframe || '1h',
      timeframes: bot.timeframes || [],
      image_url: bot.image_url || '',
    } : {
      version: '1.0.0',
      bot_type: BotType.TECHNICAL,
      price_per_month: 0,
      is_free: true,
      exchange_type: ExchangeType.BINANCE,
      trading_pair: 'BTC/USDT',
      timeframe: '1h',
      timeframes: [],
      image_url: '',
    }
  })

  const watchIsFree = watch('is_free')
  const watchTimeframes = watch('timeframes')

  useEffect(() => {
    if (watchIsFree) {
      setValue('price_per_month', 0)
    }
  }, [watchIsFree, setValue])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      // Validate file type
      if (!file.name.endsWith('.py')) {
        toast.error('Chỉ chấp nhận file Python (.py)')
        return
      }
      
      // Validate file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        toast.error('File quá lớn (tối đa 10MB)')
        return
      }
      
      setSelectedFile(file)
    }
  }

  const handleTimeframeToggle = (timeframe: string) => {
    const currentTimeframes = watchTimeframes || []
    const newTimeframes = currentTimeframes.includes(timeframe)
      ? currentTimeframes.filter(t => t !== timeframe)
      : [...currentTimeframes, timeframe]
    
    setValue('timeframes', newTimeframes)
  }

  const onSubmit = async (data: BotFormData) => {
    try {
      let savedBot: Bot

      if (bot) {
        // Update existing bot
        savedBot = await updateBot.mutateAsync({
          botId: bot.id,
          botData: data as BotUpdate
        })
      } else {
        // Create new bot
        savedBot = await createBot.mutateAsync(data as BotCreate)
      }

      // Upload file if selected
      if (selectedFile) {
        setIsUploading(true)
        try {
          await uploadFile.mutateAsync({
            botId: savedBot.id,
            file: selectedFile,
            fileType: 'CODE'
          })
        } catch (error) {
          console.error('File upload failed:', error)
        } finally {
          setIsUploading(false)
        }
      }

      onSuccess?.()
    } catch (error) {
      console.error('Bot save failed:', error)
    }
  }

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="mb-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              {bot ? 'Chỉnh sửa Bot' : 'Tạo Bot mới'}
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              {bot ? 'Cập nhật thông tin bot của bạn' : 'Tạo bot trading mới và chia sẻ với cộng đồng'}
            </p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* Basic Information */}
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
              <div className="sm:col-span-2">
                <label htmlFor="name" className="form-label">
                  Tên Bot *
                </label>
                <input
                  {...register('name')}
                  type="text"
                  id="name"
                  className="form-input"
                  placeholder="Nhập tên bot của bạn"
                />
                {errors.name && (
                  <p className="form-error">{errors.name.message}</p>
                )}
              </div>

              <div className="sm:col-span-2">
                <label htmlFor="description" className="form-label">
                  Mô tả *
                </label>
                <textarea
                  {...register('description')}
                  id="description"
                  rows={4}
                  className="form-input"
                  placeholder="Mô tả chi tiết về bot, chiến lược trading và tính năng..."
                />
                {errors.description && (
                  <p className="form-error">{errors.description.message}</p>
                )}
              </div>

              <div>
                <label htmlFor="category_id" className="form-label">
                  Danh mục
                </label>
                <select
                  {...register('category_id', { valueAsNumber: true })}
                  id="category_id"
                  className="form-input"
                >
                  <option value="">Chọn danh mục</option>
                  {categories?.map((category) => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label htmlFor="version" className="form-label">
                  Phiên bản
                </label>
                <input
                  {...register('version')}
                  type="text"
                  id="version"
                  className="form-input"
                  placeholder="1.0.0"
                />
              </div>

              <div>
                <label htmlFor="bot_type" className="form-label">
                  Loại Bot *
                </label>
                <select
                  {...register('bot_type')}
                  id="bot_type"
                  className="form-input"
                >
                  <option value={BotType.TECHNICAL}>Phân tích kỹ thuật</option>
                  <option value={BotType.ML}>Machine Learning</option>
                  <option value={BotType.DL}>Deep Learning</option>
                  <option value={BotType.LLM}>AI Language Model</option>
                  <option value={BotType.FUTURES}>Futures Trading</option>
                  <option value={BotType.SPOT}>Spot Trading</option>
                </select>
              </div>

              <div>
                <label htmlFor="exchange_type" className="form-label">
                  Sàn giao dịch
                </label>
                <select
                  {...register('exchange_type')}
                  id="exchange_type"
                  className="form-input"
                >
                  <option value={ExchangeType.BINANCE}>Binance</option>
                  <option value={ExchangeType.COINBASE}>Coinbase</option>
                  <option value={ExchangeType.KRAKEN}>Kraken</option>
                  <option value={ExchangeType.BYBIT}>Bybit</option>
                  <option value={ExchangeType.HUOBI}>Huobi</option>
                </select>
              </div>

              <div>
                <label htmlFor="trading_pair" className="form-label">
                  Cặp giao dịch
                </label>
                <input
                  {...register('trading_pair')}
                  type="text"
                  id="trading_pair"
                  className="form-input"
                  placeholder="BTC/USDT"
                />
              </div>

              <div>
                <label htmlFor="timeframe" className="form-label">
                  Khung thời gian chính
                </label>
                <select
                  {...register('timeframe')}
                  id="timeframe"
                  className="form-input"
                >
                  {timeframeOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Timeframes */}
            <div>
              <label className="form-label">
                Khung thời gian hỗ trợ
              </label>
              <div className="mt-2 grid grid-cols-3 gap-2 sm:grid-cols-6">
                {timeframeOptions.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => handleTimeframeToggle(option.value)}
                    className={`px-3 py-2 text-sm rounded-md border ${
                      watchTimeframes?.includes(option.value)
                        ? 'bg-primary-100 border-primary-500 text-primary-700'
                        : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Pricing */}
            <div className="space-y-4">
              <div className="flex items-center">
                <input
                  {...register('is_free')}
                  id="is_free"
                  type="checkbox"
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <label htmlFor="is_free" className="ml-2 block text-sm text-gray-900">
                  Bot miễn phí
                </label>
              </div>

              {!watchIsFree && (
                <div>
                  <label htmlFor="price_per_month" className="form-label">
                    Giá thuê tháng (USD)
                  </label>
                  <input
                    {...register('price_per_month', { valueAsNumber: true })}
                    type="number"
                    id="price_per_month"
                    step="0.01"
                    min="0"
                    className="form-input"
                    placeholder="0.00"
                  />
                  {errors.price_per_month && (
                    <p className="form-error">{errors.price_per_month.message}</p>
                  )}
                </div>
              )}
            </div>

            {/* Image URL */}
            <div>
              <label htmlFor="image_url" className="form-label">
                URL hình ảnh
              </label>
              <input
                {...register('image_url')}
                type="url"
                id="image_url"
                className="form-input"
                placeholder="https://example.com/bot-image.jpg"
              />
              {errors.image_url && (
                <p className="form-error">{errors.image_url.message}</p>
              )}
            </div>

            {/* File Upload */}
            <div>
              <label className="form-label">
                File code Bot (Python)
              </label>
              <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
                <div className="space-y-1 text-center">
                  <DocumentArrowUpIcon className="mx-auto h-12 w-12 text-gray-400" />
                  <div className="flex text-sm text-gray-600">
                    <label
                      htmlFor="file-upload"
                      className="relative cursor-pointer bg-white rounded-md font-medium text-primary-600 hover:text-primary-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-primary-500"
                    >
                      <span>Upload file</span>
                      <input
                        id="file-upload"
                        name="file-upload"
                        type="file"
                        className="sr-only"
                        accept=".py"
                        onChange={handleFileChange}
                      />
                    </label>
                    <p className="pl-1">hoặc kéo thả file vào đây</p>
                  </div>
                  <p className="text-xs text-gray-500">Chỉ chấp nhận file .py (tối đa 10MB)</p>
                </div>
              </div>
              
              {selectedFile && (
                <div className="mt-2 flex items-center justify-between bg-gray-50 px-3 py-2 rounded-md">
                  <span className="text-sm text-gray-700">{selectedFile.name}</span>
                  <button
                    type="button"
                    onClick={() => setSelectedFile(null)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <XMarkIcon className="h-5 w-5" />
                  </button>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex justify-end space-x-3">
              {onCancel && (
                <button
                  type="button"
                  onClick={onCancel}
                  className="btn btn-secondary px-6 py-2"
                >
                  Hủy
                </button>
              )}
              <button
                type="submit"
                disabled={isSubmitting || isUploading}
                className="btn btn-primary px-6 py-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting || isUploading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    {isUploading ? 'Đang upload...' : 'Đang lưu...'}
                  </>
                ) : (
                  bot ? 'Cập nhật Bot' : 'Tạo Bot'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

