<template>
  <div>
    <h1 class="text-3xl font-bold mb-6">Search Prompts</h1>
    
    <div class="bg-white rounded-lg shadow p-6 mb-6">
      <div class="flex space-x-4">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search prompts..."
          class="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          @keyup.enter="performSearch"
        />
        <button
          @click="performSearch"
          class="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700"
        >
          Search
        </button>
      </div>
    </div>

    <!-- Results similar to PromptsList -->
    <div v-if="results.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div
        v-for="prompt in results"
        :key="prompt.id"
        class="bg-white rounded-lg shadow hover:shadow-lg transition p-6"
      >
        <h3 class="text-xl font-semibold mb-2">
          <router-link :to="`/prompts/${prompt.id}`" class="hover:text-blue-600">
            {{ prompt.title }}
          </router-link>
        </h3>
        <p class="text-gray-600 text-sm mb-4">{{ prompt.description }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { searchAPI } from '../services/api'

const searchQuery = ref('')
const results = ref([])
const loading = ref(false)

async function performSearch() {
  if (!searchQuery.value.trim()) return

  loading.value = true
  try {
    const response = await searchAPI.search({ q: searchQuery.value })
    results.value = response.data.items || []
  } catch (error) {
    console.error('Search failed:', error)
  } finally {
    loading.value = false
  }
}
</script>

