<template>
  <div class="max-w-md mx-auto mt-12">
    <div class="bg-white rounded-lg shadow-md p-8">
      <h1 class="text-2xl font-bold text-center mb-6">Login to PromptShare</h1>
      <form @submit.prevent="handleLogin" class="space-y-4">
        <div>
          <label for="username" class="block text-sm font-medium text-gray-700 mb-1">
            Username
          </label>
          <input
            id="username"
            v-model="form.username"
            type="text"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Enter your username"
          />
        </div>
        <div>
          <label for="password" class="block text-sm font-medium text-gray-700 mb-1">
            Password
          </label>
          <input
            id="password"
            v-model="form.password"
            type="password"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Enter your password"
          />
        </div>
        <div v-if="error" class="text-red-600 text-sm">{{ error }}</div>
        <button
          type="submit"
          :disabled="loading"
          class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ loading ? 'Logging in...' : 'Login' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const form = ref({
  username: '',
  password: '',
})
const loading = ref(false)
const error = ref(null)

onMounted(() => {
  // Redirect if already authenticated
  if (authStore.isAuthenticated) {
    router.push(route.query.redirect || '/')
  }
})

async function handleLogin() {
  loading.value = true
  error.value = null

  const result = await authStore.login(form.value.username, form.value.password)

  if (result.success) {
    router.push(route.query.redirect || '/')
  } else {
    error.value = result.error
  }

  loading.value = false
}
</script>

