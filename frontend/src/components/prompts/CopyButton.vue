<template>
  <button
    @click="handleCopy"
    :disabled="copied"
    class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:bg-green-600 disabled:cursor-not-allowed flex items-center space-x-2"
  >
    <svg
      v-if="!copied"
      class="w-5 h-5"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        stroke-linecap="round"
        stroke-linejoin="round"
        stroke-width="2"
        d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
      />
    </svg>
    <svg
      v-else
      class="w-5 h-5"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        stroke-linecap="round"
        stroke-linejoin="round"
        stroke-width="2"
        d="M5 13l4 4L19 7"
      />
    </svg>
    <span>{{ copied ? 'Copied!' : 'Copy Prompt' }}</span>
  </button>
</template>

<script setup>
import { ref } from 'vue'
import { usePromptsStore } from '../../stores/prompts'

const props = defineProps({
  text: {
    type: String,
    required: true,
  },
  promptId: {
    type: String,
    required: true,
  },
})

const promptsStore = usePromptsStore()
const copied = ref(false)

async function handleCopy() {
  try {
    await navigator.clipboard.writeText(props.text)
    copied.value = true
    
    // Track copy event
    await promptsStore.trackCopy(props.promptId)
    
    // Reset after 2 seconds
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (error) {
    console.error('Failed to copy:', error)
    // Fallback for older browsers
    const textArea = document.createElement('textarea')
    textArea.value = props.text
    document.body.appendChild(textArea)
    textArea.select()
    document.execCommand('copy')
    document.body.removeChild(textArea)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  }
}
</script>

