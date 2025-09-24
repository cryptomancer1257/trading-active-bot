import BotList from '@/components/bots/BotList'

export default function MarketplacePage() {
  return (
    <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Bot Marketplace</h1>
        <p className="mt-2 text-gray-600">
          Khám phá và sử dụng các bot trading AI được phát triển bởi cộng đồng
        </p>
      </div>
      
      <BotList />
    </div>
  )
}

