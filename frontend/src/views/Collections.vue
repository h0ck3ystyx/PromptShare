<template>
  <div>
    <h1 class="text-3xl font-bold mb-6">Collections</h1>
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div
        v-for="collection in collections"
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
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { collectionsAPI } from '../services/api'

const collections = ref([])

onMounted(async () => {
  try {
    const response = await collectionsAPI.list()
    collections.value = response.data.collections
  } catch (error) {
    console.error('Failed to load collections:', error)
  }
})
</script>

