import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add token to requests if available
api.interceptors.request.use((config) => {
  console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${API_BASE_URL}${config.url}`)
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
    console.log('🔐 Added token:', token.substring(0, 20) + '...')
  } else {
    console.log('⚠️ No auth token found')
  }
  return config
})

// Handle token expiry
api.interceptors.response.use(
  (response) => {
    console.log('✅ API Success:', response.config.url, response.status)
    return response
  },
  (error) => {
    if (error.code === 'ERR_NETWORK') {
      console.error('🔥 Network Error: Backend server not reachable at', API_BASE_URL)
      console.error('💡 Make sure backend is running on port 8000')
    } else {
      console.error('❌ API Error:', error.config?.url, error.response?.status, error.response?.data)
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

