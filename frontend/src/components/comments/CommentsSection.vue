<template>
  <div class="bg-white rounded-lg shadow p-6">
    <h2 class="text-xl font-semibold mb-4">Comments</h2>
    
    <!-- Add Comment Form -->
    <div v-if="authStore.isAuthenticated" class="mb-6">
      <textarea
        v-model="newComment"
        placeholder="Add a comment..."
        rows="3"
        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 mb-2"
      ></textarea>
      <button
        @click="submitComment"
        :disabled="loading || !newComment.trim()"
        class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
      >
        Post Comment
      </button>
    </div>
    <div v-else class="mb-6 text-sm text-gray-600">
      <router-link to="/login" class="text-blue-600 hover:text-blue-800">
        Login
      </router-link>
      to post a comment
    </div>

    <!-- Comments List -->
    <div v-if="loading" class="text-center py-4">
      <div class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
    </div>
    <div v-else-if="comments.length === 0" class="text-gray-600 text-center py-4">
      No comments yet. Be the first to comment!
    </div>
    <div v-else class="space-y-4">
      <div
        v-for="comment in comments"
        :key="comment.id"
        class="border-b border-gray-200 pb-4 last:border-0"
      >
        <div class="flex justify-between items-start mb-2">
          <div>
            <span class="font-semibold text-gray-900">{{ comment.author?.username || 'Unknown' }}</span>
            <span class="text-sm text-gray-500 ml-2">
              {{ new Date(comment.created_at).toLocaleDateString() }}
            </span>
          </div>
          <button
            v-if="canDelete(comment)"
            @click="deleteComment(comment.id)"
            class="text-red-600 hover:text-red-800 text-sm"
          >
            Delete
          </button>
        </div>
        <p class="text-gray-700 whitespace-pre-wrap">{{ comment.content }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../../stores/auth'
import { commentsAPI } from '../../services/api'

const props = defineProps({
  promptId: {
    type: String,
    required: true,
  },
})

const authStore = useAuthStore()
const comments = ref([])
const newComment = ref('')
const loading = ref(false)

onMounted(async () => {
  await loadComments()
})

async function loadComments() {
  loading.value = true
  try {
    const response = await commentsAPI.list(props.promptId)
    comments.value = response.data.items || []
  } catch (error) {
    console.error('Failed to load comments:', error)
  } finally {
    loading.value = false
  }
}

async function submitComment() {
  if (!newComment.value.trim()) return

  loading.value = true
  try {
    await commentsAPI.create(props.promptId, { content: newComment.value })
    newComment.value = ''
    await loadComments()
  } catch (error) {
    console.error('Failed to submit comment:', error)
  } finally {
    loading.value = false
  }
}

function canDelete(comment) {
  if (!authStore.isAuthenticated) return false
  if (authStore.isAdmin || authStore.isModerator) return true
  return comment.author_id === authStore.user?.id
}

async function deleteComment(commentId) {
  if (!confirm('Are you sure you want to delete this comment?')) return

  try {
    await commentsAPI.delete(props.promptId, commentId)
    await loadComments()
  } catch (error) {
    console.error('Failed to delete comment:', error)
  }
}
</script>

