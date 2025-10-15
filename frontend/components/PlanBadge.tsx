import { usePlan } from '@/hooks/usePlan'

export default function PlanBadge() {
  const { currentPlan, isLoadingPlan } = usePlan()

  if (isLoadingPlan) {
    return (
      <div className="inline-flex items-center px-3 py-1 rounded-full bg-gray-100 text-gray-400 text-sm">
        <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-gray-400 mr-2"></div>
        Loading...
      </div>
    )
  }

  if (!currentPlan) return null

  const isPro = currentPlan.plan_name === 'pro'

  return (
    <div className={`inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium ${
      isPro 
        ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg shadow-purple-500/50' 
        : 'bg-gray-100 text-gray-700 border border-gray-300'
    }`}>
      {isPro ? (
        <>
          <span className="mr-1.5">⚡</span>
          <span className="font-bold">PRO</span>
        </>
      ) : (
        <>
          <span className="mr-1.5">🆓</span>
          <span>Free</span>
        </>
      )}
    </div>
  )
}

