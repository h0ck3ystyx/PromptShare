<template>
  <div class="max-w-md mx-auto mt-12">
    <div class="bg-white rounded-lg shadow-md p-8">
      <h1 class="text-2xl font-bold text-center mb-6">Login to PromptShare</h1>
      <MFAVerification
        v-if="showMFA"
        @success="handleMFASuccess"
        @cancel="showMFA = false"
      />
      <form v-else @submit.prevent="handleLogin" class="space-y-4">
        <div>
          <label for="username" class="block text-sm font-medium text-gray-700 mb-1">
            Username or Email
          </label>
          <input
            id="username"
            v-model="form.username"
            type="text"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Enter your username or email"
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
        <div v-if="mfaMessage" class="text-blue-600 text-sm">{{ mfaMessage }}</div>
        <button
          type="submit"
          :disabled="loading"
          class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ loading ? 'Logging in...' : 'Login' }}
        </button>
        <div class="text-center text-sm space-y-2">
          <div>
            <router-link to="/password-reset" class="text-blue-600 hover:underline">
              Forgot password?
            </router-link>
          </div>
          <div>
            <router-link to="/register" class="text-blue-600 hover:underline">
              Don't have an account? Register
            </router-link>
          </div>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import MFAVerification from '../components/auth/MFAVerification.vue'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const form = ref({
  username: '',
  password: '',
})
const loading = ref(false)
const error = ref('')
const showMFA = ref(false)
const mfaMessage = ref('')

onMounted(() => {
  // Redirect if already authenticated
  if (authStore.isAuthenticated) {
    router.push(route.query.redirect || '/')
  }
})

async function handleLogin() {
  loading.value = true
  error.value = ''
  mfaMessage.value = ''

  const result = await authStore.login(form.value.username, form.value.password)

  if (result.success) {
    router.push(route.query.redirect || '/')
  } else if (result.mfaRequired) {
    showMFA.value = true
    mfaMessage.value = result.message || 'MFA code sent to your email'
  } else {
    error.value = result.error || 'Login failed'
  }

  loading.value = false
}

async function handleMFASuccess() {
  const redirect = route.query.redirect || '/'
  router.push(redirect)
}
</script>
