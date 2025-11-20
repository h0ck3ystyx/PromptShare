<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-3xl font-bold">Prompts</h1>
      <router-link
        v-if="authStore.isAuthenticated"
        to="/prompts/create"
        class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
      >
        Create Prompt
      </router-link>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-lg shadow p-4 mb-6">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Search</label>
          <input
            v-model="filters.q"
            type="text"
            placeholder="Search prompts..."
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            @input="debouncedSearch"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Platform</label>
          <select
            v-model="filters.platform_tag"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            @change="applyFilters"
          >
            <option value="">All Platforms</option>
            <option value="github_copilot">GitHub Copilot</option>
            <option value="o365_copilot">O365 Copilot</option>
            <option value="cursor">Cursor</option>
            <option value="claude">Claude</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Category</label>
          <select
            v-model="filters.category_id"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            @change="applyFilters"
          >
            <option value="">All Categories</option>
            <option v-for="cat in categories" :key="cat.id" :value="cat.id">
              {{ cat.name }}
            </option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Sort By</label>
          <select
            v-model="filters.sort_by"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            @change="applyFilters"
          >
            <option value="newest">Newest</option>
            <option value="oldest">Oldest</option>
            <option value="most_viewed">Most Viewed</option>
            <option value="highest_rated">Highest Rated</option>
          </select>
        </div>
      </div>
      <div class="mt-4 flex items-center space-x-4">
        <label class="flex items-center">
          <input
            v-model="filters.featured_only"
            type="checkbox"
            class="mr-2"
            @change="applyFilters"
          />
          <span class="text-sm text-gray-700">Featured Only</span>
        </label>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="promptsStore.loading" class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>

    <!-- Error State -->
    <div v-else-if="promptsStore.error" class="bg-red-50 border border-red-200 rounded-md p-4">
      <p class="text-red-800">{{ promptsStore.error }}</p>
    </div>

    <!-- Prompts Grid -->
    <div v-else-if="promptsStore.prompts.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div
        v-for="prompt in promptsStore.prompts"
        :key="prompt.id"
        class="bg-white rounded-lg shadow hover:shadow-lg transition p-6"
      >
        <div class="flex justify-between items-start mb-2">
          <h3 class="text-xl font-semibold text-gray-900">
            <router-link
              :to="`/prompts/${prompt.id}`"
              class="hover:text-blue-600"
            >
              {{ prompt.title }}
            </router-link>
          </h3>
          <span
            v-if="prompt.is_featured"
            class="bg-yellow-100 text-yellow-800 text-xs font-semibold px-2 py-1 rounded"
          >
            Featured
          </span>
        </div>
        <p class="text-gray-600 text-sm mb-4 line-clamp-2">{{ prompt.description }}</p>
        <div class="flex flex-wrap gap-2 mb-4">
          <span
            v-for="platform in prompt.platform_tags"
            :key="platform"
            class="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded"
          >
            {{ platform.replace('_', ' ').toUpperCase() }}
          </span>
        </div>
        <div class="flex justify-between items-center text-sm text-gray-500">
          <span>{{ prompt.view_count }} views</span>
          <span>{{ new Date(prompt.created_at).toLocaleDateString() }}</span>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="text-center py-12">
      <p class="text-gray-600">No prompts found. Try adjusting your filters.</p>
    </div>

    <!-- Pagination -->
    <div
      v-if="promptsStore.pagination.total > 0"
      class="mt-8 flex justify-center items-center space-x-2"
    >
      <button
        @click="changePage(promptsStore.pagination.page - 1)"
        :disabled="promptsStore.pagination.page === 1"
        class="px-4 py-2 border rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Previous
      </button>
      <span class="text-gray-700">
        Page {{ promptsStore.pagination.page }} of
        {{ Math.ceil(promptsStore.pagination.total / promptsStore.pagination.page_size) }}
      </span>
      <button
        @click="changePage(promptsStore.pagination.page + 1)"
        :disabled="
          promptsStore.pagination.page >=
          Math.ceil(promptsStore.pagination.total / promptsStore.pagination.page_size)
        "
        class="px-4 py-2 border rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Next
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { usePromptsStore } from '../stores/prompts'
import { useAuthStore } from '../stores/auth'
import { categoriesAPI } from '../services/api'

const promptsStore = usePromptsStore()
const authStore = useAuthStore()

const filters = ref({
  q: '',
  platform_tag: '',
  category_id: '',
  sort_by: 'newest',
  featured_only: false,
})

const categories = ref([])
let searchTimeout = null

onMounted(async () => {
  await loadCategories()
  await promptsStore.fetchPrompts(filters.value)
})

async function loadCategories() {
  try {
    const response = await categoriesAPI.list()
    categories.value = response.data.items
  } catch (error) {
    console.error('Failed to load categories:', error)
  }
}

function debouncedSearch() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    applyFilters()
  }, 500)
}

async function applyFilters() {
  promptsStore.pagination.page = 1
  await promptsStore.fetchPrompts(filters.value)
}

async function changePage(page) {
  promptsStore.pagination.page = page
  await promptsStore.fetchPrompts(filters.value)
}
</script>

