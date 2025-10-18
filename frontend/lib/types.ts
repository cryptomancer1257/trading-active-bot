// User Types
export enum UserRole {
  USER = "USER",
  DEVELOPER = "DEVELOPER",
  ADMIN = "ADMIN"
}

export interface User {
  id: number
  email: string
  role: UserRole
  is_active: boolean
  created_at: string
  updated_at: string
  developer_name?: string
  developer_bio?: string
  developer_website?: string
  telegram_username?: string
  discord_username?: string
  total_subscriptions?: number
  active_subscriptions?: number
  total_developed_bots?: number
  approved_bots?: number
}

export interface UserCreate {
  email: string
  password: string
  role?: UserRole
  developer_name?: string
  developer_bio?: string
  developer_website?: string
}

export interface UserUpdate {
  developer_name?: string
  developer_bio?: string
  developer_website?: string
  telegram_username?: string
  discord_username?: string
}

// Auth Types
export interface LoginRequest {
  username: string
  password: string
}

export interface Token {
  access_token: string
  token_type: string
}

// Bot Types
export enum BotStatus {
  PENDING = "PENDING",
  APPROVED = "APPROVED",
  REJECTED = "REJECTED",
  ARCHIVED = "ARCHIVED"
}

export enum BotType {
  TECHNICAL = "TECHNICAL",
  ML = "ML",
  DL = "DL",
  LLM = "LLM",
  SPOT = "SPOT",
  FUTURES = "FUTURES",
  FUTURES_RPA = "FUTURES_RPA",
  FUTURES_API = "FUTURES_API"
}

export enum ExchangeType {
  BINANCE = "BINANCE",
  COINBASE = "COINBASE",
  KRAKEN = "KRAKEN",
  BYBIT = "BYBIT",
  HUOBI = "HUOBI"
}

export interface Bot {
  id: number
  name: string
  description: string
  developer_id: number
  category_id?: number
  status: BotStatus
  version: string
  bot_type: BotType
  price_per_month: number
  is_free: boolean
  total_subscribers: number
  average_rating: number
  total_reviews: number
  created_at: string
  updated_at: string
  approved_at?: string
  approved_by?: number
  code_path?: string
  model_path?: string
  config_schema?: any
  default_config?: any
  model_metadata?: any
  timeframes?: string[]
  timeframe?: string
  exchange_type?: ExchangeType
  trading_pair?: string
  strategy_config?: any
  image_url?: string
}

export interface BotCreate {
  name: string
  description: string
  category_id?: number
  version?: string
  bot_type?: BotType
  price_per_month?: number
  is_free?: boolean
  config_schema?: any
  default_config?: any
  model_metadata?: any
  timeframes?: string[]
  timeframe?: string
  exchange_type?: ExchangeType
  trading_pair?: string
  strategy_config?: any
  image_url?: string
}

export interface BotUpdate {
  name?: string
  description?: string
  category_id?: number
  version?: string
  bot_type?: BotType
  price_per_month?: number
  is_free?: boolean
  config_schema?: any
  default_config?: any
  model_metadata?: any
  timeframes?: string[]
  trading_pair?: string
  strategy_config?: string[]
}

export interface BotWithDeveloper extends Bot {
  developer: User
}

export interface BotListResponse {
  bots: Bot[]
  total: number
  page: number
  per_page: number
}

// Bot Category Types
export interface BotCategory {
  id: number
  name: string
  description?: string
}

export interface BotCategoryCreate {
  name: string
  description?: string
}

// Exchange Credentials Types
export interface ExchangeCredentials {
  id: number
  exchange: ExchangeType
  is_testnet: boolean
  is_active: boolean
  validation_status: string
  last_validated?: string
  api_key_preview: string
}

export interface ExchangeCredentialsCreate {
  exchange: ExchangeType
  api_key: string
  api_secret: string
  api_passphrase?: string
  is_testnet?: boolean
}

export interface ExchangeCredentialsUpdate {
  api_key?: string
  api_secret?: string
  api_passphrase?: string
  is_testnet?: boolean
  is_active?: boolean
}

// Admin Types
export interface AdminStats {
  total_users: number
  total_developers: number
  total_bots: number
  approved_bots: number
  pending_bots: number
  total_subscriptions: number
  active_subscriptions: number
  total_trades: number
  total_revenue: number
}

// LLM Provider Types
export enum LLMProviderType {
  OPENAI = "OPENAI",
  ANTHROPIC = "ANTHROPIC", 
  GEMINI = "GEMINI",
  GROQ = "GROQ",
  COHERE = "COHERE"
}

export interface LLMProvider {
  id: number
  user_id: number
  provider_type: LLMProviderType
  name: string
  api_key: string
  base_url?: string
  is_active: boolean
  is_default: boolean
  models: LLMModel[]
  created_at: string
  updated_at: string
}

export interface LLMModel {
  id: number
  provider_id: number
  model_name: string
  display_name: string
  is_active: boolean
  max_tokens?: number
  cost_per_1k_tokens?: number
  created_at: string
  updated_at: string
}

export interface LLMProviderCreate {
  provider_type: LLMProviderType
  name: string
  api_key: string
  base_url?: string
  is_active?: boolean
  is_default?: boolean
  models?: LLMModelCreate[]
}

export interface LLMProviderUpdate {
  name?: string
  api_key?: string
  base_url?: string
  is_active?: boolean
  is_default?: boolean
}

export interface LLMModelCreate {
  model_name: string
  display_name: string
  is_active?: boolean
  max_tokens?: number
  cost_per_1k_tokens?: number
}

export interface LLMModelUpdate {
  display_name?: string
  is_active?: boolean
  max_tokens?: number
  cost_per_1k_tokens?: number
}

// API Response Types
export interface ApiResponse<T> {
  data: T
  message?: string
  success: boolean
}

export interface ApiError {
  error: string
  message: string
  details?: any
}

