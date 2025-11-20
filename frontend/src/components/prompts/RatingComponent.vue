<template>
  <div>
    <label class="block text-sm font-medium text-gray-700 mb-2">Rate this prompt</label>
    <div class="flex items-center space-x-1">
      <button
        v-for="star in 5"
        :key="star"
        @click="ratePrompt(star)"
        :disabled="loading"
        class="text-2xl focus:outline-none disabled:opacity-50"
        :class="star <= (userRating || 0) ? 'text-yellow-400' : 'text-gray-300'"
      >
        ★
      </button>
      <span v-if="averageRating" class="ml-2 text-sm text-gray-600">
        ({{ averageRating.toFixed(1) }} avg)
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../../stores/auth'
import { ratingsAPI } from '../../services/api'

const props = defineProps({
  promptId: {
    type: String,
    required: true,
  },
})

const authStore = useAuthStore()
const userRating = ref(0)
const averageRating = ref(0)
const loading = ref(false)

onMounted(async () => {
  await loadRating()
})

async function loadRating() {
  try {
    // Get user's rating (only if authenticated)
    if (authStore.isAuthenticated) {
      try {
        const myRatingResponse = await ratingsAPI.getMyRating(props.promptId)
        if (myRatingResponse.data) {
          userRating.value = myRatingResponse.data.rating || 0
        }
      } catch (error) {
        // If no rating exists (404) or unauthorized (401), that's OK for guests
        if (error.response?.status !== 404 && error.response?.status !== 401) {
          console.error('Failed to load user rating:', error)
        }
      }
    }
    
    // Get summary for average (available to all users)
    const summaryResponse = await ratingsAPI.getSummary(props.promptId)
    if (summaryResponse.data) {
      averageRating.value = summaryResponse.data.average_rating || 0
    }
  } catch (error) {
    console.error('Failed to load rating:', error)
  }
}

async function ratePrompt(rating) {
  loading.value = true
  try {
    if (userRating.value > 0) {
      // Update existing rating
      await ratingsAPI.updateRating(props.promptId, rating)
    } else {
      // Create new rating
      await ratingsAPI.rate(props.promptId, rating)
    }
    userRating.value = rating
    // Reload to get updated average
    const summaryResponse = await ratingsAPI.getSummary(props.promptId)
    if (summaryResponse.data) {
      averageRating.value = summaryResponse.data.average_rating || 0
    }
  } catch (error) {
    console.error('Failed to rate prompt:', error)
  } finally {
    loading.value = false
  }
}
</script>

