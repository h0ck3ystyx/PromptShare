/**
 * Pinia store for prompts state.
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import { promptsAPI } from '../services/api'

export const usePromptsStore = defineStore('prompts', () => {
  const prompts = ref([])
  const currentPrompt = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const pagination = ref({
    page: 1,
    page_size: 20,
    total: 0,
  })

  async function fetchPrompts(params = {}) {
    loading.value = true
    error.value = null
    try {
      const response = await promptsAPI.list({
        ...params,
        page: params.page || pagination.value.page,
        page_size: params.page_size || pagination.value.page_size,
      })
      prompts.value = response.data.items
      pagination.value = {
        page: response.data.page,
        page_size: response.data.page_size,
        total: response.data.total,
      }
      return { success: true }
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch prompts'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  async function fetchPrompt(id) {
    loading.value = true
    error.value = null
    try {
      const response = await promptsAPI.get(id)
      currentPrompt.value = response.data
      return { success: true }
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch prompt'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  async function createPrompt(data) {
    loading.value = true
    error.value = null
    try {
      const response = await promptsAPI.create(data)
      prompts.value.unshift(response.data)
      return { success: true, data: response.data }
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to create prompt'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  async function updatePrompt(id, data) {
    loading.value = true
    error.value = null
    try {
      const response = await promptsAPI.update(id, data)
      const index = prompts.value.findIndex((p) => p.id === id)
      if (index !== -1) {
        prompts.value[index] = response.data
      }
      if (currentPrompt.value?.id === id) {
        currentPrompt.value = response.data
      }
      return { success: true, data: response.data }
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to update prompt'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  async function deletePrompt(id) {
    loading.value = true
    error.value = null
    try {
      await promptsAPI.delete(id)
      prompts.value = prompts.value.filter((p) => p.id !== id)
      if (currentPrompt.value?.id === id) {
        currentPrompt.value = null
      }
      return { success: true }
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to delete prompt'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  async function trackCopy(id) {
    try {
      await promptsAPI.trackCopy(id)
      return { success: true }
    } catch (err) {
      // Don't show error for copy tracking failures
      console.error('Failed to track copy:', err)
      return { success: false }
    }
  }

  function clearCurrentPrompt() {
    currentPrompt.value = null
  }

  return {
    prompts,
    currentPrompt,
    loading,
    error,
    pagination,
    fetchPrompts,
    fetchPrompt,
    createPrompt,
    updatePrompt,
    deletePrompt,
    trackCopy,
    clearCurrentPrompt,
  }
})

