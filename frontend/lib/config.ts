/**
 * Frontend Configuration
 * Manages environment variables and API endpoints
 */

export const config = {
  // API Configuration
  apiUrl: process.env.NEXT_PUBLIC_API_URL || (typeof window !== 'undefined' ? window.location.origin : 'https://quantumforge.cryptomancer.ai'),
  studioBaseUrl: process.env.NEXT_PUBLIC_STUDIO_BASE_URL || (typeof window !== 'undefined' ? window.location.origin : 'https://quantumforge.cryptomancer.ai'),
  marketplaceApiKey: process.env.NEXT_PUBLIC_MARKETPLACE_API_KEY || 'marketplace_dev_api_key_12345',
  
  // API Endpoints
  endpoints: {
    marketplaceSubscription: '/marketplace/subscription',
    auth: '/auth',
    bots: '/bots',
    subscriptions: '/subscriptions'
  },
  
  // Trial Configuration
  trial: {
    durationHours: 24,
    defaultTradingPair: 'BTC/USDT',
    defaultNetwork: 'TESTNET'
  }
} as const

export default config
