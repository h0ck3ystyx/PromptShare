<template>
  <div class="max-w-3xl mx-auto">
    <h1 class="text-3xl font-bold mb-6">Create New Prompt</h1>
    
    <form @submit.prevent="handleSubmit" class="bg-white rounded-lg shadow p-6 space-y-6">
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
          placeholder="Enter prompt title"
        />
      </div>

      <div>
        <label for="description" class="block text-sm font-medium text-gray-700 mb-1">
          Description
        </label>
        <textarea
          id="description"
          v-model="form.description"
          rows="3"
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Brief description of what this prompt does"
        ></textarea>
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
          placeholder="Enter the actual prompt text"
        ></textarea>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">
          Platform Tags <span class="text-red-500">*</span>
        </label>
        <div class="flex flex-wrap gap-2">
          <label
            v-for="platform in platforms"
            :key="platform.value"
            class="flex items-center space-x-2 cursor-pointer"
          >
            <input
              v-model="form.platform_tags"
              type="checkbox"
              :value="platform.value"
              class="rounded"
            />
            <span>{{ platform.label }}</span>
          </label>
        </div>
      </div>

      <div>
        <label for="categories" class="block text-sm font-medium text-gray-700 mb-2">
          Categories
        </label>
        <div class="flex flex-wrap gap-2">
          <label
            v-for="category in categories"
            :key="category.id"
            class="flex items-center space-x-2 cursor-pointer"
          >
            <input
              v-model="form.category_ids"
              type="checkbox"
              :value="category.id"
              class="rounded"
            />
            <span>{{ category.name }}</span>
          </label>
        </div>
      </div>

      <div>
        <label for="use_cases" class="block text-sm font-medium text-gray-700 mb-1">
          Use Cases (one per line)
        </label>
        <textarea
          id="use_cases"
          v-model="useCasesText"
          rows="4"
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Enter use cases, one per line"
        ></textarea>
      </div>

      <div>
        <label for="usage_tips" class="block text-sm font-medium text-gray-700 mb-1">
          Usage Tips
        </label>
        <textarea
          id="usage_tips"
          v-model="form.usage_tips"
          rows="3"
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Tips for using this prompt effectively"
        ></textarea>
      </div>

      <div>
        <label for="status" class="block text-sm font-medium text-gray-700 mb-1">
          Status
        </label>
        <select
          id="status"
          v-model="form.status"
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="draft">Draft</option>
          <option value="published">Published</option>
        </select>
      </div>

      <div v-if="error" class="bg-red-50 border border-red-200 rounded-md p-4">
        <p class="text-red-800">{{ error }}</p>
      </div>

      <div class="flex justify-end space-x-4">
        <router-link
          to="/prompts"
          class="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
        >
          Cancel
        </router-link>
        <button
          type="submit"
          :disabled="loading"
          class="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {{ loading ? 'Creating...' : 'Create Prompt' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePromptsStore } from '../stores/prompts'
import { categoriesAPI } from '../services/api'

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

const useCasesText = ref('')
const categories = ref([])
const loading = ref(false)
const error = ref(null)

const platforms = [
  { value: 'github_copilot', label: 'GitHub Copilot' },
  { value: 'o365_copilot', label: 'O365 Copilot' },
  { value: 'cursor', label: 'Cursor' },
  { value: 'claude', label: 'Claude' },
]

onMounted(async () => {
  await loadCategories()
})

async function loadCategories() {
  try {
    const response = await categoriesAPI.list()
    categories.value = response.data.items
  } catch (err) {
    console.error('Failed to load categories:', err)
  }
}

async function handleSubmit() {
  if (form.value.platform_tags.length === 0) {
    error.value = 'Please select at least one platform tag'
    return
  }

  loading.value = true
  error.value = null

  // Convert use cases text to array
  const useCases = useCasesText.value
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line.length > 0)

  const result = await promptsStore.createPrompt({
    ...form.value,
    use_cases: useCases,
  })

  if (result.success) {
    router.push(`/prompts/${result.data.id}`)
  } else {
    error.value = result.error
    loading.value = false
  }
}
</script>

