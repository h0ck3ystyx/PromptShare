/**
 * Pinia store for authentication state.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authAPI } from '../services/api'

// Token expiration time (30 minutes default, matching backend)
const TOKEN_EXPIRY_MINUTES = 30
// Idle timeout (15 minutes of inactivity)
const IDLE_TIMEOUT_MINUTES = 15
// Refresh token before expiration (5 minutes before)
const TOKEN_REFRESH_BUFFER_MINUTES = 5

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('auth_token') || null)
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const tokenExpiryTime = ref(localStorage.getItem('token_expiry_time') ? new Date(localStorage.getItem('token_expiry_time')) : null)
  const lastActivityTime = ref(Date.now())
  
  let tokenRefreshTimer = null
  let idleTimeoutTimer = null
  let activityCheckInterval = null

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isModerator = computed(() => user.value?.role === 'moderator' || isAdmin.value)
  
  // Check if token is expired or will expire soon
  const isTokenExpiringSoon = computed(() => {
    if (!tokenExpiryTime.value) return false
    const now = new Date()
    const refreshTime = new Date(tokenExpiryTime.value.getTime() - TOKEN_REFRESH_BUFFER_MINUTES * 60 * 1000)
    return now >= refreshTime
  })
  
  // Check if user is idle
  const isIdle = computed(() => {
    const idleThreshold = IDLE_TIMEOUT_MINUTES * 60 * 1000
    return Date.now() - lastActivityTime.value > idleThreshold
  })

  function updateActivityTime() {
    lastActivityTime.value = Date.now()
  }

  function setTokenExpiry() {
    const expiryTime = new Date()
    expiryTime.setMinutes(expiryTime.getMinutes() + TOKEN_EXPIRY_MINUTES)
    tokenExpiryTime.value = expiryTime
    localStorage.setItem('token_expiry_time', expiryTime.toISOString())
  }

  function setupTokenRefresh() {
    if (tokenRefreshTimer) {
      clearTimeout(tokenRefreshTimer)
    }
    
    if (!token.value || !tokenExpiryTime.value) return
    
    const now = new Date()
    const refreshTime = new Date(tokenExpiryTime.value.getTime() - TOKEN_REFRESH_BUFFER_MINUTES * 60 * 1000)
    const timeUntilRefresh = refreshTime.getTime() - now.getTime()
    
    if (timeUntilRefresh > 0) {
      tokenRefreshTimer = setTimeout(() => {
        refreshToken()
      }, timeUntilRefresh)
    } else {
      // Token is already expiring soon, refresh immediately
      refreshToken()
    }
  }

  function setupIdleTimeout() {
    if (idleTimeoutTimer) {
      clearTimeout(idleTimeoutTimer)
    }
    
    if (!token.value) return
    
    idleTimeoutTimer = setTimeout(() => {
      if (isIdle.value) {
        handleIdleTimeout()
      }
    }, IDLE_TIMEOUT_MINUTES * 60 * 1000)
  }

  function setupActivityTracking() {
    // Track user activity
    const events = ['mousedown', 'keydown', 'scroll', 'touchstart']
    const updateActivity = () => {
      updateActivityTime()
      setupIdleTimeout()
    }
    
    events.forEach(event => {
      window.addEventListener(event, updateActivity, { passive: true })
    })
    
    // Check activity periodically
    activityCheckInterval = setInterval(() => {
      if (isIdle.value && token.value) {
        handleIdleTimeout()
      }
    }, 60000) // Check every minute
    
    return () => {
      events.forEach(event => {
        window.removeEventListener(event, updateActivity)
      })
      if (activityCheckInterval) {
        clearInterval(activityCheckInterval)
      }
    }
  }

  async function refreshToken() {
    if (!token.value) return
    
    try {
      // Try to refresh by fetching current user (validates token)
      const result = await fetchCurrentUser()
      if (result.success) {
        // Token is still valid, update expiry
        setTokenExpiry()
        setupTokenRefresh()
      } else {
        // Token is invalid, logout
        await logout()
      }
    } catch (error) {
      console.error('Token refresh failed:', error)
      await logout()
    }
  }

  function handleIdleTimeout() {
    // Prompt user before logging out
    if (confirm('You have been idle for a while. Would you like to stay logged in?')) {
      updateActivityTime()
      setupIdleTimeout()
    } else {
      logout()
    }
  }

  async function login(username, password) {
    try {
      const response = await authAPI.login(username, password)
      token.value = response.data.access_token
      user.value = response.data.user

      localStorage.setItem('auth_token', token.value)
      localStorage.setItem('user', JSON.stringify(user.value))
      setTokenExpiry()
      updateActivityTime()
      
      // Setup token refresh and idle timeout
      setupTokenRefresh()
      setupIdleTimeout()
      setupActivityTracking()

      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Login failed',
      }
    }
  }

  async function logout() {
    // Clear timers
    if (tokenRefreshTimer) {
      clearTimeout(tokenRefreshTimer)
      tokenRefreshTimer = null
    }
    if (idleTimeoutTimer) {
      clearTimeout(idleTimeoutTimer)
      idleTimeoutTimer = null
    }
    if (activityCheckInterval) {
      clearInterval(activityCheckInterval)
      activityCheckInterval = null
    }
    
    try {
      await authAPI.logout()
    } catch (error) {
      // Continue with logout even if API call fails
      console.error('Logout API error:', error)
    } finally {
      token.value = null
      user.value = null
      tokenExpiryTime.value = null
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user')
      localStorage.removeItem('token_expiry_time')
    }
  }

  async function fetchCurrentUser() {
    try {
      const response = await authAPI.getCurrentUser()
      user.value = response.data
      localStorage.setItem('user', JSON.stringify(user.value))
      // Update token expiry on successful fetch
      if (token.value) {
        setTokenExpiry()
        setupTokenRefresh()
      }
      return { success: true }
    } catch (error) {
      // If fetch fails, clear auth state
      token.value = null
      user.value = null
      tokenExpiryTime.value = null
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user')
      localStorage.removeItem('token_expiry_time')
      return { success: false, error: error.response?.data?.detail || 'Failed to fetch user' }
    }
  }

  // Initialize on store creation if token exists
  function initialize() {
    if (token.value) {
      const storedExpiry = localStorage.getItem('token_expiry_time')
      if (storedExpiry) {
        tokenExpiryTime.value = new Date(storedExpiry)
        // Check if token is already expired
        if (new Date() >= tokenExpiryTime.value) {
          logout()
          return
        }
      } else {
        // No expiry stored, set one now
        setTokenExpiry()
      }
      setupTokenRefresh()
      setupIdleTimeout()
      setupActivityTracking()
    }
  }

  // Initialize on store creation
  initialize()

  return {
    token,
    user,
    isAuthenticated,
    isAdmin,
    isModerator,
    isTokenExpiringSoon,
    isIdle,
    login,
    logout,
    fetchCurrentUser,
    updateActivityTime,
    refreshToken,
  }
})

