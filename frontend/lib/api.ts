import axios from 'axios'
import { config } from './config'

export const api = axios.create({
  baseURL: config.apiUrl,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add token to requests if available
api.interceptors.request.use((config) => {
  console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${api.defaults.baseURL}${config.url}`)
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
    console.log('🔐 Added token:', token.substring(0, 20) + '...')
  } else {
    console.log('⚠️ No auth token found')
  }
  return config
})

// Handle token expiry and quota exceeded errors
api.interceptors.response.use(
  (response) => {
    console.log('✅ API Success:', response.config.url, response.status)
    
    // Check for quota_exceeded in successful responses (some endpoints return this as success)
    if (response.data && response.data.error === 'quota_exceeded') {
      console.warn('⚠️ LLM Quota Exceeded:', response.data.message)
      // Trigger quota exceeded event
      window.dispatchEvent(new CustomEvent('quota-exceeded', {
        detail: {
          message: response.data.message,
          endpoint: response.config.url
        }
      }))
    }
    
    return response
  },
  (error) => {
    if (error.code === 'ERR_NETWORK') {
      console.error('🔥 Network Error: Backend server not reachable at', api.defaults.baseURL)
      console.error('💡 Make sure backend is running')
    } else {
      console.error('❌ API Error:', error.config?.url, error.response?.status, error.response?.data)
    }
    
    // Check for quota_exceeded in error responses
    if (error.response?.data?.error === 'quota_exceeded') {
      console.warn('⚠️ LLM Quota Exceeded:', error.response.data.message)
      // Trigger quota exceeded event
      window.dispatchEvent(new CustomEvent('quota-exceeded', {
        detail: {
          message: error.response.data.message,
          endpoint: error.config?.url
        }
      }))
    }
    
    if (error.response?.status === 401) {
      console.log('401 error - token expired or invalid')
      
      // Don't redirect during login/register process
      const authPaths = ['/auth/token', '/auth/register']
      const isAuthRequest = authPaths.some(path => error.config?.url?.includes(path))
      
      if (!isAuthRequest) {
        console.log('Removing expired token')
        localStorage.removeItem('access_token')
        
        // Only redirect if we're not already on an auth page
        const currentPath = window.location.pathname
        const isOnAuthPage = currentPath.includes('/auth/')
        
        if (!isOnAuthPage) {
          console.log('Redirecting to login due to expired session')
          window.location.href = '/auth/login'
        }
      }
    }
    return Promise.reject(error)
  }
)

export default api

