import axios from 'axios';
import { getAuthToken } from './auth';

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
});

// Add JWT token to all requests
apiClient.interceptors.request.use((config) => {
  const token = getAuthToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 errors (token expired)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const airdropAPI = {
  // Configuration
  getConfig: () => apiClient.get('/api/airdrop/config'),
  getStats: () => apiClient.get('/api/airdrop/stats'),
  
  // Tasks
  getTasks: () => apiClient.get('/api/airdrop/tasks'),
  getUserStatus: () => apiClient.get('/api/airdrop/status'),
  
  // Platform Usage Verification
  verifyBotCreation: () => apiClient.post('/api/airdrop/verify-bot-creation'),
  verifyFirstTrade: () => apiClient.post('/api/airdrop/verify-first-trade'),
  verifyTradingVolume: () => apiClient.post('/api/airdrop/verify-trading-volume'),
  
  // Community Verification
  verifyDiscord: (discordId: string) => 
    apiClient.post('/api/airdrop/verify-discord', { discord_id: discordId }),
  verifyTelegram: (code: string) => 
    apiClient.post('/api/airdrop/verify-telegram', { code }),
  
  // Referrals
  getReferralCode: () => apiClient.get('/api/airdrop/referral-code'),
  useReferralCode: (code: string) => 
    apiClient.post('/api/airdrop/use-referral', { referral_code: code }),
  
  // Claim
  claimTokens: () => apiClient.post('/api/airdrop/claim'),
  
  // Trader Contributions
  getLeaderboard: () => 
    apiClient.get('/api/trader-contributions/leaderboard/monthly-performance'),
  submitStrategy: (data: any) => 
    apiClient.post('/api/trader-contributions/submit-strategy-template', data),
  getStrategyTemplates: () => 
    apiClient.get('/api/trader-contributions/strategy-templates'),
  createBotFromTemplate: (templateId: number, name: string, capital: number) => 
    apiClient.post('/api/trader-contributions/create-bot-from-template', {
      template_id: templateId,
      name,
      initial_capital: capital
    }),
};

export default apiClient;

