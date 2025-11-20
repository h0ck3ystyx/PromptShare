<template>
  <div>
    <h1 class="text-3xl font-bold mb-6">Admin Dashboard</h1>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <div class="bg-white rounded-lg shadow p-6">
        <h3 class="text-lg font-semibold mb-2">Total Views</h3>
        <p class="text-3xl font-bold text-blue-600">{{ analytics.total_views || 0 }}</p>
        <p class="text-sm text-gray-500 mt-1">Last {{ analytics.period_days || 30 }} days</p>
      </div>
      <div class="bg-white rounded-lg shadow p-6">
        <h3 class="text-lg font-semibold mb-2">Total Copies</h3>
        <p class="text-3xl font-bold text-blue-600">{{ analytics.total_copies || 0 }}</p>
        <p class="text-sm text-gray-500 mt-1">Last {{ analytics.period_days || 30 }} days</p>
      </div>
      <div class="bg-white rounded-lg shadow p-6">
        <h3 class="text-lg font-semibold mb-2">Total Searches</h3>
        <p class="text-3xl font-bold text-blue-600">{{ analytics.total_searches || 0 }}</p>
        <p class="text-sm text-gray-500 mt-1">Last {{ analytics.period_days || 30 }} days</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { analyticsAPI } from '../services/api'

const analytics = ref({})

onMounted(async () => {
  try {
    const response = await analyticsAPI.getOverview()
    analytics.value = response.data
  } catch (error) {
    console.error('Failed to load analytics:', error)
  }
})
</script>

