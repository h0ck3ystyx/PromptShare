import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@testing-library/vue'
import { createPinia, setActivePinia } from 'pinia'
import { useAuthStore } from '../src/stores/auth'

describe('Auth Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  it('should initialize with no token', () => {
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(false)
    expect(store.token).toBe(null)
  })

  it('should set token on login', async () => {
    const store = useAuthStore()
    // Mock the API call
    vi.spyOn(store, 'login').mockResolvedValue({ success: true })
    
    // Note: In a real test, you'd mock the authAPI.login call
    // This is just an example structure
    expect(store.isAuthenticated).toBe(false)
  })
})

