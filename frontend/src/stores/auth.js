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
  let activityTrackingCleanup = null

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
    // Clean up existing listeners before setting up new ones
    if (activityTrackingCleanup) {
      activityTrackingCleanup()
      activityTrackingCleanup = null
    }
    
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
    
    // Store cleanup function
    activityTrackingCleanup = () => {
      events.forEach(event => {
        window.removeEventListener(event, updateActivity)
      })
      if (activityCheckInterval) {
        clearInterval(activityCheckInterval)
        activityCheckInterval = null
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

  // MFA state
  const mfaRequired = ref(false)
  const pendingMfaToken = ref(null)

  async function login(username, password) {
    try {
      const response = await authAPI.login(username, password)
      
      // Check if MFA is required
      if (response.data.mfa_required) {
        mfaRequired.value = true
        pendingMfaToken.value = response.data.access_token
        return {
          success: false,
          mfaRequired: true,
          pendingToken: response.data.access_token,
          message: 'MFA code sent to your email'
        }
      }
      
      // Normal login success
      token.value = response.data.access_token
      mfaRequired.value = false
      pendingMfaToken.value = null

      // Fetch user info
      const userResponse = await authAPI.getCurrentUser()
      user.value = userResponse.data

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

  async function verifyMFA(code, rememberDevice = false) {
    if (!pendingMfaToken.value) {
      return { success: false, error: 'No pending MFA verification' }
    }

    try {
      // Generate device fingerprint (simple implementation)
      const deviceFingerprint = generateDeviceFingerprint()
      const deviceName = `${navigator.platform} - ${navigator.userAgent.substring(0, 50)}`

      const response = await authAPI.mfaVerify(
        pendingMfaToken.value,
        code,
        rememberDevice,
        deviceFingerprint,
        deviceName
      )

      // MFA verified, complete login
      token.value = response.data.access_token
      mfaRequired.value = false
      pendingMfaToken.value = null

      // Fetch user info
      const userResponse = await authAPI.getCurrentUser()
      user.value = userResponse.data

      localStorage.setItem('auth_token', token.value)
      localStorage.setItem('user', JSON.stringify(user.value))
      setTokenExpiry()
      updateActivityTime()
      
      setupTokenRefresh()
      setupIdleTimeout()
      setupActivityTracking()

      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'MFA verification failed',
      }
    }
  }

  function generateDeviceFingerprint() {
    // Simple device fingerprint based on available properties
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    ctx.textBaseline = 'top'
    ctx.font = '14px Arial'
    ctx.fillText('Device fingerprint', 2, 2)
    const canvasFingerprint = canvas.toDataURL()
    
    const fingerprint = [
      navigator.userAgent,
      navigator.language,
      screen.width + 'x' + screen.height,
      new Date().getTimezoneOffset(),
      canvasFingerprint.substring(0, 50)
    ].join('|')
    
    // Simple hash
    let hash = 0
    for (let i = 0; i < fingerprint.length; i++) {
      const char = fingerprint.charCodeAt(i)
      hash = ((hash << 5) - hash) + char
      hash = hash & hash // Convert to 32bit integer
    }
    return Math.abs(hash).toString(36)
  }

  async function register(userData) {
    try {
      const response = await authAPI.register(userData)
      user.value = response.data
      return { success: true, data: response.data }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Registration failed',
      }
    }
  }

  async function requestPasswordReset(email) {
    try {
      await authAPI.requestPasswordReset(email)
      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Password reset request failed',
      }
    }
  }

  async function resetPassword(token, newPassword) {
    try {
      await authAPI.resetPassword(token, newPassword)
      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Password reset failed',
      }
    }
  }

  async function changePassword(currentPassword, newPassword) {
    try {
      await authAPI.changePassword(currentPassword, newPassword)
      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Password change failed',
      }
    }
  }

  async function enrollMFA(password) {
    try {
      await authAPI.mfaEnroll(password)
      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'MFA enrollment failed',
      }
    }
  }

  async function disableMFA(password, code = null) {
    try {
      await authAPI.mfaDisable(password, code)
      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'MFA disable failed',
      }
    }
  }

  async function getSecurityDashboard() {
    try {
      const response = await authAPI.getSecurityDashboard()
      return { success: true, data: response.data }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to load security dashboard',
      }
    }
  }

  async function logout() {
    // Clear activity tracking listeners first
    if (activityTrackingCleanup) {
      activityTrackingCleanup()
      activityTrackingCleanup = null
    }
    
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
    mfaRequired,
    pendingMfaToken,
    login,
    logout,
    verifyMFA,
    register,
    requestPasswordReset,
    resetPassword,
    changePassword,
    enrollMFA,
    disableMFA,
    getSecurityDashboard,
    fetchCurrentUser,
    updateActivityTime,
    refreshToken,
  }
})

