<template>
  <div v-if="promptsStore.currentPrompt">
    <!-- Header -->
    <div class="bg-white rounded-lg shadow p-6 mb-6">
      <div class="flex justify-between items-start mb-4">
        <div class="flex-1">
          <div class="flex items-center space-x-2 mb-2">
            <h1 class="text-3xl font-bold">{{ promptsStore.currentPrompt.title }}</h1>
            <span
              v-if="promptsStore.currentPrompt.is_featured"
              class="bg-yellow-100 text-yellow-800 text-xs font-semibold px-2 py-1 rounded"
            >
              Featured
            </span>
          </div>
          <p class="text-gray-600 mb-4">{{ promptsStore.currentPrompt.description }}</p>
          <div class="flex flex-wrap gap-2 mb-4">
            <span
              v-for="platform in promptsStore.currentPrompt.platform_tags"
              :key="platform"
              class="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded"
            >
              {{ platform.replace('_', ' ').toUpperCase() }}
            </span>
          </div>
          <div class="flex items-center space-x-4 text-sm text-gray-500">
            <span>By {{ promptsStore.currentPrompt.author?.username || 'Unknown' }}</span>
            <span>{{ promptsStore.currentPrompt.view_count }} views</span>
            <span>{{ new Date(promptsStore.currentPrompt.created_at).toLocaleDateString() }}</span>
          </div>
        </div>
        <div v-if="canEdit" class="ml-4">
          <router-link
            :to="`/prompts/${promptsStore.currentPrompt.id}/edit`"
            class="bg-gray-200 text-gray-800 px-4 py-2 rounded-md hover:bg-gray-300 text-sm"
          >
            Edit
          </router-link>
        </div>
      </div>
    </div>

    <!-- Prompt Content -->
    <div class="bg-white rounded-lg shadow p-6 mb-6">
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-xl font-semibold">Prompt Content</h2>
        <CopyButton
          :text="promptsStore.currentPrompt.content"
          :prompt-id="promptsStore.currentPrompt.id"
        />
      </div>
      <pre
        class="bg-gray-50 p-4 rounded border overflow-x-auto whitespace-pre-wrap"
      >{{ promptsStore.currentPrompt.content }}</pre>
    </div>

    <!-- Usage Tips -->
    <div v-if="promptsStore.currentPrompt.usage_tips" class="bg-blue-50 rounded-lg shadow p-6 mb-6">
      <h2 class="text-xl font-semibold mb-2">Usage Tips</h2>
      <p class="text-gray-700">{{ promptsStore.currentPrompt.usage_tips }}</p>
    </div>

    <!-- Use Cases -->
    <div v-if="promptsStore.currentPrompt.use_cases?.length > 0" class="bg-white rounded-lg shadow p-6 mb-6">
      <h2 class="text-xl font-semibold mb-4">Use Cases</h2>
      <ul class="list-disc list-inside space-y-2">
        <li v-for="(useCase, index) in promptsStore.currentPrompt.use_cases" :key="index">
          {{ useCase }}
        </li>
      </ul>
    </div>

    <!-- Actions (Rating, Upvote) -->
    <div class="bg-white rounded-lg shadow p-6 mb-6">
      <div class="flex items-center space-x-6">
        <RatingComponent :prompt-id="promptsStore.currentPrompt.id" />
        <UpvoteComponent :prompt-id="promptsStore.currentPrompt.id" />
      </div>
    </div>

    <!-- Comments -->
    <CommentsSection :prompt-id="promptsStore.currentPrompt.id" />
  </div>
  <div v-else-if="promptsStore.loading" class="text-center py-12">
    <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
  </div>
  <div v-else class="text-center py-12">
    <p class="text-gray-600">Prompt not found</p>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { usePromptsStore } from '../stores/prompts'
import { useAuthStore } from '../stores/auth'
import CopyButton from '../components/prompts/CopyButton.vue'
import RatingComponent from '../components/prompts/RatingComponent.vue'
import UpvoteComponent from '../components/prompts/UpvoteComponent.vue'
import CommentsSection from '../components/comments/CommentsSection.vue'

const route = useRoute()
const promptsStore = usePromptsStore()
const authStore = useAuthStore()

const canEdit = computed(() => {
  if (!authStore.isAuthenticated) return false
  if (authStore.isAdmin || authStore.isModerator) return true
  return promptsStore.currentPrompt?.author_id === authStore.user?.id
})

onMounted(async () => {
  await promptsStore.fetchPrompt(route.params.id)
})
</script>

