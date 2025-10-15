export interface UserPlan {
  id: number
  user_id: number
  plan_name: 'free' | 'pro'
  price_usd: number
  max_bots: number
  max_subscriptions_per_bot: number
  allowed_environment: 'testnet' | 'mainnet'
  publish_marketplace: boolean
  subscription_expiry_days: number
  compute_quota_per_day: number
  revenue_share_percentage: number
  status: 'active' | 'paused' | 'expired'
  expiry_date: string | null
  auto_renew: boolean
  payment_method: 'paypal' | 'stripe' | 'crypto' | null
  created_at: string
  updated_at: string
}

export interface PlanConfig {
  plan_name: string
  price_usd: number
  max_bots: number
  max_subscriptions_per_bot: number
  allowed_environment: string
  publish_marketplace: boolean
  subscription_expiry_days: number
  compute_quota_per_day: number
  revenue_share_percentage: number
}

export interface PlanLimits {
  plan: {
    name: string
    max_bots: number
    max_subscriptions_per_bot: number
    allowed_environment: string
    publish_marketplace: boolean
    compute_quota_per_day: number
    revenue_share_percentage: number
  }
  usage: {
    total_bots: number
    total_subscriptions: number
    bots_remaining: number
    can_create_bot: boolean
    can_publish_marketplace: boolean
  }
  status: {
    is_pro: boolean
    is_active: boolean
    expiry_date: string | null
    auto_renew: boolean
  }
}

