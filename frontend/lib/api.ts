import axios from 'axios'
import { config } from './config'

export const api = axios.create({
  baseURL: config.apiUrl,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Helper to refresh access token
let isRefreshing = false
let refreshSubscribers: ((token: string) => void)[] = []

function subscribeTokenRefresh(cb: (token: string) => void) {
  refreshSubscribers.push(cb)
}

function onRefreshed(token: string) {
  refreshSubscribers.forEach(cb => cb(token))
  refreshSubscribers = []
}

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = localStorage.getItem('refresh_token')
  if (!refreshToken) {
    return null
  }

  try {
    console.log('🔄 Refreshing access token...')
    const response = await axios.post(`${config.apiUrl}/auth/refresh`, {
      refresh_token: refreshToken
    })
    
    const { access_token, refresh_token: new_refresh_token } = response.data
    
    // Save new tokens
    localStorage.setItem('access_token', access_token)
    localStorage.setItem('refresh_token', new_refresh_token)
    
    console.log('✅ Token refreshed successfully')
    return access_token
  } catch (error) {
    console.error('❌ Failed to refresh token:', error)
    // Clear tokens on refresh failure
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    return null
  }
}

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
  async (error) => {
    if (error.code === 'ERR_NETWORK') {
      console.error('🔥 Network Error: Backend server not reachable at', api.defaults.baseURL)
      console.error('💡 Make sure backend is running')
      return Promise.reject(error)
    }
    
    console.error('❌ API Error:', error.config?.url, error.response?.status, error.response?.data)
    
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
    
    // Handle 401 - Try to refresh token
    if (error.response?.status === 401) {
      const originalRequest = error.config
      
      // Don't retry auth endpoints or refresh endpoint
      const authPaths = ['/auth/token', '/auth/register', '/auth/refresh']
      const isAuthRequest = authPaths.some(path => originalRequest?.url?.includes(path))
      
      if (isAuthRequest || originalRequest._retry) {
        // Auth request failed or already retried - clear tokens and redirect
        console.log('🔴 Authentication failed - clearing tokens')
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        
        const currentPath = window.location.pathname
        const isOnAuthPage = currentPath.includes('/auth/')
        
        if (!isOnAuthPage) {
          console.log('Redirecting to login')
          window.location.href = '/auth/login'
        }
        return Promise.reject(error)
      }
      
      // Try to refresh token
      if (!isRefreshing) {
        isRefreshing = true
        
        try {
          const newToken = await refreshAccessToken()
          
          if (newToken) {
            isRefreshing = false
            onRefreshed(newToken)
            
            // Retry original request with new token
            if (originalRequest) {
              originalRequest._retry = true
              originalRequest.headers.Authorization = `Bearer ${newToken}`
              return api(originalRequest)
            }
          } else {
            // Refresh failed
            isRefreshing = false
            throw new Error('Token refresh failed')
          }
        } catch (refreshError) {
          isRefreshing = false
          console.error('❌ Token refresh failed:', refreshError)
          
          // Clear tokens and redirect
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          
          const currentPath = window.location.pathname
          const isOnAuthPage = currentPath.includes('/auth/')
          
          if (!isOnAuthPage) {
            window.location.href = '/auth/login'
          }
          
          return Promise.reject(error)
        }
      }
      
      // If already refreshing, queue this request
      return new Promise((resolve) => {
        subscribeTokenRefresh((token: string) => {
          if (originalRequest) {
            originalRequest.headers.Authorization = `Bearer ${token}`
            resolve(api(originalRequest))
          }
        })
      })
    }
    
    return Promise.reject(error)
  }
)

export default api

