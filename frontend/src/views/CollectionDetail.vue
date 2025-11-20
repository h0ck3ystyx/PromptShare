<template>
  <div>
    <h1 class="text-3xl font-bold mb-6">{{ collection?.name }}</h1>
    <p class="text-gray-600 mb-6">{{ collection?.description }}</p>
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div
        v-for="prompt in collection?.prompts"
        :key="prompt.id"
        class="bg-white rounded-lg shadow p-6"
      >
        <h3 class="text-xl font-semibold mb-2">
          <router-link :to="`/prompts/${prompt.id}`" class="hover:text-blue-600">
            {{ prompt.title }}
          </router-link>
        </h3>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { collectionsAPI } from '../services/api'

const route = useRoute()
const collection = ref(null)

onMounted(async () => {
  try {
    const response = await collectionsAPI.get(route.params.id)
    collection.value = response.data
  } catch (error) {
    console.error('Failed to load collection:', error)
  }
})
</script>

