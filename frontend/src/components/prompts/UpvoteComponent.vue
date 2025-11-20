<template>
  <div>
    <button
      @click="toggleUpvote"
      :disabled="loading"
      class="flex items-center space-x-2 px-4 py-2 rounded-md border hover:bg-gray-50 disabled:opacity-50"
      :class="hasUpvoted ? 'border-blue-500 bg-blue-50' : 'border-gray-300'"
    >
      <svg
        class="w-5 h-5"
        :class="hasUpvoted ? 'text-blue-600' : 'text-gray-600'"
        fill="currentColor"
        viewBox="0 0 20 20"
      >
        <path
          fill-rule="evenodd"
          d="M3.293 9.707a1 1 0 010-1.414l6-6a1 1 0 011.414 0l6 6a1 1 0 01-1.414 1.414L11 5.414V17a1 1 0 11-2 0V5.414L4.707 9.707a1 1 0 01-1.414 0z"
          clip-rule="evenodd"
        />
      </svg>
      <span :class="hasUpvoted ? 'text-blue-600 font-semibold' : 'text-gray-700'">
        {{ upvoteCount }}
      </span>
    </button>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { upvotesAPI } from '../../services/api'

const props = defineProps({
  promptId: {
    type: String,
    required: true,
  },
})

const hasUpvoted = ref(false)
const upvoteCount = ref(0)
const loading = ref(false)

onMounted(async () => {
  await loadUpvoteStatus()
})

async function loadUpvoteStatus() {
  try {
    const response = await upvotesAPI.getSummary(props.promptId)
    upvoteCount.value = response.data.count || 0
    hasUpvoted.value = response.data.has_upvoted || false
  } catch (error) {
    console.error('Failed to load upvote status:', error)
  }
}

async function toggleUpvote() {
  loading.value = true
  try {
    if (hasUpvoted.value) {
      await upvotesAPI.removeUpvote(props.promptId)
      hasUpvoted.value = false
      upvoteCount.value--
    } else {
      await upvotesAPI.upvote(props.promptId)
      hasUpvoted.value = true
      upvoteCount.value++
    }
  } catch (error) {
    console.error('Failed to toggle upvote:', error)
  } finally {
    loading.value = false
  }
}
</script>

