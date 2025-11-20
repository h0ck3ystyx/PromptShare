<template>
  <div class="max-w-3xl mx-auto">
    <h1 class="text-3xl font-bold mb-6">Edit Prompt</h1>
    
    <div v-if="promptsStore.loading" class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>

    <form
      v-else-if="promptsStore.currentPrompt"
      @submit.prevent="handleSubmit"
      class="bg-white rounded-lg shadow p-6 space-y-6"
    >
      <!-- Same form fields as CreatePrompt -->
      <div>
        <label for="title" class="block text-sm font-medium text-gray-700 mb-1">
          Title <span class="text-red-500">*</span>
        </label>
        <input
          id="title"
          v-model="form.title"
          type="text"
          required
          maxlength="255"
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label for="content" class="block text-sm font-medium text-gray-700 mb-1">
          Prompt Content <span class="text-red-500">*</span>
        </label>
        <textarea
          id="content"
          v-model="form.content"
          required
          rows="10"
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
        ></textarea>
      </div>

      <!-- Add other fields similar to CreatePrompt -->

      <div v-if="error" class="bg-red-50 border border-red-200 rounded-md p-4">
        <p class="text-red-800">{{ error }}</p>
      </div>

      <div class="flex justify-end space-x-4">
        <router-link
          :to="`/prompts/${route.params.id}`"
          class="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
        >
          Cancel
        </router-link>
        <button
          type="submit"
          :disabled="loading"
          class="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {{ loading ? 'Updating...' : 'Update Prompt' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePromptsStore } from '../stores/prompts'

const route = useRoute()
const router = useRouter()
const promptsStore = usePromptsStore()

const form = ref({
  title: '',
  description: '',
  content: '',
  platform_tags: [],
  category_ids: [],
  use_cases: [],
  usage_tips: '',
  status: 'draft',
})

const loading = ref(false)
const error = ref(null)

onMounted(async () => {
  await promptsStore.fetchPrompt(route.params.id)
  if (promptsStore.currentPrompt) {
    form.value = {
      title: promptsStore.currentPrompt.title,
      description: promptsStore.currentPrompt.description || '',
      content: promptsStore.currentPrompt.content,
      platform_tags: promptsStore.currentPrompt.platform_tags || [],
      category_ids: promptsStore.currentPrompt.category_ids || [],
      use_cases: promptsStore.currentPrompt.use_cases || [],
      usage_tips: promptsStore.currentPrompt.usage_tips || '',
      status: promptsStore.currentPrompt.status,
    }
  }
})

async function handleSubmit() {
  loading.value = true
  error.value = null

  const result = await promptsStore.updatePrompt(route.params.id, form.value)

  if (result.success) {
    router.push(`/prompts/${route.params.id}`)
  } else {
    error.value = result.error
    loading.value = false
  }
}
</script>

