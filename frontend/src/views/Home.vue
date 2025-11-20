<template>
  <div>
    <!-- Hero Section -->
    <div class="text-center py-12">
      <h1 class="text-4xl font-bold text-gray-900 mb-4">
        Welcome to PromptShare
      </h1>
      <p class="text-xl text-gray-600 mb-8">
        Discover, share, and collaborate on effective prompts for AI tools
      </p>
      <div class="flex justify-center space-x-4">
        <router-link
          to="/prompts"
          class="bg-blue-600 text-white px-6 py-3 rounded-md font-medium hover:bg-blue-700"
        >
          Browse Prompts
        </router-link>
        <router-link
          to="/search"
          class="bg-gray-200 text-gray-800 px-6 py-3 rounded-md font-medium hover:bg-gray-300"
        >
          Search
        </router-link>
      </div>
    </div>

    <!-- Featured Collections -->
    <div v-if="featuredCollections.length > 0" class="mt-12">
      <h2 class="text-2xl font-bold mb-6">Featured Collections</h2>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div
          v-for="collection in featuredCollections"
          :key="collection.id"
          class="bg-white rounded-lg shadow p-6 hover:shadow-lg transition"
        >
          <h3 class="text-xl font-semibold mb-2">{{ collection.name }}</h3>
          <p class="text-gray-600 text-sm mb-4">{{ collection.description }}</p>
          <router-link
            :to="`/collections/${collection.id}`"
            class="text-blue-600 hover:text-blue-800 font-medium"
          >
            View Collection →
          </router-link>
        </div>
      </div>
    </div>

    <!-- Quick Stats -->
    <div class="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
      <div class="bg-white rounded-lg shadow p-6 text-center">
        <div class="text-3xl font-bold text-blue-600">{{ stats.totalPrompts }}</div>
        <div class="text-gray-600 mt-2">Total Prompts</div>
      </div>
      <div class="bg-white rounded-lg shadow p-6 text-center">
        <div class="text-3xl font-bold text-blue-600">{{ stats.totalUsers }}</div>
        <div class="text-gray-600 mt-2">Active Users</div>
      </div>
      <div class="bg-white rounded-lg shadow p-6 text-center">
        <div class="text-3xl font-bold text-blue-600">{{ stats.totalViews }}</div>
        <div class="text-gray-600 mt-2">Total Views</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { collectionsAPI } from '../services/api'

const featuredCollections = ref([])
const stats = ref({
  totalPrompts: 0,
  totalUsers: 0,
  totalViews: 0,
})

onMounted(async () => {
  try {
    const response = await collectionsAPI.list({ featured_only: true, page_size: 3 })
    featuredCollections.value = response.data.collections
  } catch (error) {
    console.error('Failed to fetch featured collections:', error)
  }
})
</script>

