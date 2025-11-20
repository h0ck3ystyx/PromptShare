/**
 * API service layer using Axios.
 */

import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:7999/api'

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle errors
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Unauthorized - try to refresh token first if we have one
      const token = localStorage.getItem('auth_token')
      if (token) {
        try {
          // Try to refresh by fetching current user
          const { useAuthStore } = await import('../stores/auth')
          const authStore = useAuthStore()
          const result = await authStore.fetchCurrentUser()
          
          if (result.success) {
            // Token refreshed, retry the original request
            const originalRequest = error.config
            originalRequest.headers.Authorization = `Bearer ${authStore.token}`
            return apiClient(originalRequest)
          }
        } catch (refreshError) {
          // Refresh failed, proceed with logout
          console.error('Token refresh failed:', refreshError)
        }
      }
      
      // Clear token and redirect to login
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user')
      localStorage.removeItem('token_expiry_time')
      
      // Only redirect if we're not already on the login page
      if (window.location.pathname !== '/login') {
        // Store current route for redirect after login
        const redirectPath = window.location.pathname + window.location.search
        window.location.href = `/login?redirect=${encodeURIComponent(redirectPath)}`
      }
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  // Login (supports both LDAP and local auth)
  login: (username, password) => {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)
    return apiClient.post('/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  logout: () => apiClient.post('/auth/logout'),
  getCurrentUser: () => apiClient.get('/auth/me'),
  
  // Registration and local auth
  register: (data) => apiClient.post('/auth/register', data),
  verifyEmail: (token) => apiClient.post('/auth/verify-email', { token }),
  verifyEmailGet: (token) => apiClient.get(`/auth/verify-email?token=${token}`),
  
  // Password management
  requestPasswordReset: (email) => apiClient.post('/auth/password-reset-request', { email }),
  resetPassword: (token, newPassword) => apiClient.post('/auth/password-reset', { token, new_password: newPassword }),
  changePassword: (currentPassword, newPassword) => apiClient.post('/auth/change-password', {
    current_password: currentPassword,
    new_password: newPassword
  }),
  validatePassword: (password) => apiClient.post('/auth/validate-password', null, { params: { password } }),
  
  // MFA
  mfaEnroll: (password) => apiClient.post('/auth/mfa/enroll', { password }),
  mfaVerify: (pendingToken, code, rememberDevice = false, deviceFingerprint = null, deviceName = null) =>
    apiClient.post('/auth/mfa/verify', {
      pending_token: pendingToken,
      code,
      remember_device: rememberDevice,
      device_fingerprint: deviceFingerprint,
      device_name: deviceName
    }),
  mfaDisable: (password, code = null) => apiClient.post('/auth/mfa/disable', { password, code }),
  mfaStatus: () => apiClient.get('/auth/mfa/status'),
  
  // Security dashboard
  getSecurityDashboard: () => apiClient.get('/auth/security'),
  listSessions: () => apiClient.get('/auth/sessions'),
  revokeSession: (sessionId) => apiClient.delete(`/auth/sessions/${sessionId}`),
  listTrustedDevices: () => apiClient.get('/auth/devices'),
  removeTrustedDevice: (deviceId) => apiClient.delete(`/auth/devices/${deviceId}`),
}

// Prompts API
export const promptsAPI = {
  list: (params) => apiClient.get('/prompts', { params }),
  get: (id) => apiClient.get(`/prompts/${id}`),
  create: (data) => apiClient.post('/prompts', data),
  update: (id, data) => apiClient.put(`/prompts/${id}`, data),
  delete: (id) => apiClient.delete(`/prompts/${id}`),
  trackCopy: (id) => apiClient.post(`/prompts/${id}/copy`),
}

// Search API
export const searchAPI = {
  search: (params) => apiClient.get('/search', { params }),
}

// Categories API
export const categoriesAPI = {
  list: () => apiClient.get('/categories'),
  get: (id) => apiClient.get(`/categories/${id}`),
}

// Collections API
export const collectionsAPI = {
  list: (params) => apiClient.get('/collections', { params }),
  get: (id) => apiClient.get(`/collections/${id}`),
  create: (data) => apiClient.post('/collections', data),
  update: (id, data) => apiClient.put(`/collections/${id}`, data),
  delete: (id) => apiClient.delete(`/collections/${id}`),
}

// Comments API
export const commentsAPI = {
  list: (promptId, params) => apiClient.get(`/prompts/${promptId}/comments`, { params }),
  create: (promptId, data) => apiClient.post(`/prompts/${promptId}/comments`, data),
  update: (promptId, commentId, data) => apiClient.put(`/prompts/${promptId}/comments/${commentId}`, data),
  delete: (promptId, commentId) => apiClient.delete(`/prompts/${promptId}/comments/${commentId}`),
}

// Ratings API
export const ratingsAPI = {
  rate: (promptId, rating) => apiClient.post(`/prompts/${promptId}/ratings`, { rating }),
  getSummary: (promptId) => apiClient.get(`/prompts/${promptId}/ratings/summary`),
  getMyRating: (promptId) => apiClient.get(`/prompts/${promptId}/ratings/me`),
  updateRating: (promptId, rating) => apiClient.put(`/prompts/${promptId}/ratings/me`, { rating }),
  deleteRating: (promptId) => apiClient.delete(`/prompts/${promptId}/ratings/me`),
}

// Upvotes API
export const upvotesAPI = {
  upvote: (promptId) => apiClient.post(`/prompts/${promptId}/upvote`),
  removeUpvote: (promptId) => apiClient.delete(`/prompts/${promptId}/upvote`),
  getSummary: (promptId) => apiClient.get(`/prompts/${promptId}/upvotes/summary`),
}

// Notifications API
export const notificationsAPI = {
  list: (params) => apiClient.get('/notifications', { params }),
  markAsRead: (id) => apiClient.patch(`/notifications/${id}/read`),
  markAllAsRead: () => apiClient.post('/notifications/mark-all-read'),
  getUnreadCount: () => apiClient.get('/notifications/unread-count'),
  delete: (id) => apiClient.delete(`/notifications/${id}`),
}

// Follows API
export const followsAPI = {
  followCategory: (categoryId) => apiClient.post(`/follows/categories/${categoryId}`),
  unfollowCategory: (categoryId) => apiClient.delete(`/follows/categories/${categoryId}`),
  list: () => apiClient.get('/follows/categories'),
  check: (categoryId) => apiClient.get(`/follows/categories/${categoryId}/check`),
}

// Onboarding API
export const onboardingAPI = {
  getMaterials: () => apiClient.get('/onboarding'),
  getBestPractices: () => apiClient.get('/onboarding/best-practices'),
}

// FAQs API
export const faqsAPI = {
  list: (params) => apiClient.get('/faqs', { params }),
  get: (id) => apiClient.get(`/faqs/${id}`),
}

// Analytics API (admin only)
export const analyticsAPI = {
  getPromptAnalytics: (promptId, params) =>
    apiClient.get(`/analytics/prompts/${promptId}`, { params }),
  getOverview: (params) => apiClient.get('/analytics/overview', { params }),
}

// Users API
export const usersAPI = {
  list: (params) => apiClient.get('/users', { params }),
  get: (id) => apiClient.get(`/users/${id}`),
  updateRole: (id, role) => apiClient.put(`/users/${id}/role`, { role }),
}

export default apiClient

