<template>
  <div>
    <h1 class="text-3xl font-bold mb-6">Getting Started</h1>
    <div class="space-y-8">
      <div v-for="section in onboarding.getting_started" :key="section.order">
        <h2 class="text-2xl font-semibold mb-2">{{ section.title }}</h2>
        <p class="text-gray-700">{{ section.content }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { onboardingAPI } from '../services/api'

const onboarding = ref({ getting_started: [] })

onMounted(async () => {
  try {
    const response = await onboardingAPI.getMaterials()
    onboarding.value = response.data
  } catch (error) {
    console.error('Failed to load onboarding:', error)
  }
})
</script>

