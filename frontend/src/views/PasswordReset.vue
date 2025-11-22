<template>
  <div class="max-w-md mx-auto mt-12">
    <div class="bg-white rounded-lg shadow-md p-8">
      <h1 class="text-2xl font-bold text-center mb-6">Reset Password</h1>
      <div v-if="!token" class="space-y-4">
        <p class="text-sm text-gray-600 text-center mb-6">
          Enter your email address and we'll send you a link to reset your password.
        </p>
        <form @submit.prevent="handleRequestReset" class="space-y-4">
          <div>
            <label for="email" class="block text-sm font-medium text-gray-700 mb-1">
              Email
            </label>
            <input
              id="email"
              v-model="form.email"
              type="email"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="your.email@example.com"
            />
          </div>
          <div v-if="error" class="text-red-600 text-sm">{{ error }}</div>
          <div v-if="success" class="text-green-600 text-sm">
            If an account exists with that email, a password reset link has been sent.
          </div>
          <button
            type="submit"
            :disabled="loading"
            class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ loading ? 'Sending...' : 'Send Reset Link' }}
          </button>
          <div class="text-center text-sm">
            <router-link to="/login" class="text-blue-600 hover:underline">
              Back to Login
            </router-link>
          </div>
        </form>
      </div>
      <div v-else class="space-y-4">
        <p class="text-sm text-gray-600 text-center mb-6">
          Enter your new password below.
        </p>
        <form @submit.prevent="handleReset" class="space-y-4">
          <div>
            <label for="newPassword" class="block text-sm font-medium text-gray-700 mb-1">
              New Password
            </label>
            <input
              id="newPassword"
              v-model="form.newPassword"
              type="password"
              required
              minlength="8"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Minimum 8 characters"
            />
          </div>
          <div>
            <label for="confirmPassword" class="block text-sm font-medium text-gray-700 mb-1">
              Confirm Password
            </label>
            <input
              id="confirmPassword"
              v-model="form.confirmPassword"
              type="password"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Re-enter your password"
            />
            <div v-if="form.newPassword && form.confirmPassword && form.newPassword !== form.confirmPassword" class="text-red-600 text-sm mt-1">
              Passwords do not match
            </div>
          </div>
          <div v-if="error" class="text-red-600 text-sm">{{ error }}</div>
          <button
            type="submit"
            :disabled="loading || form.newPassword !== form.confirmPassword"
            class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ loading ? 'Resetting...' : 'Reset Password' }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const token = ref(null)
const form = ref({
  email: '',
  newPassword: '',
  confirmPassword: ''
})
const loading = ref(false)
const error = ref('')
const success = ref(false)

onMounted(() => {
  token.value = route.query.token || null
})

async function handleRequestReset() {
  loading.value = true
  error.value = ''
  success.value = false

  const result = await authStore.requestPasswordReset(form.value.email)

  if (result.success) {
    success.value = true
  } else {
    error.value = result.error || 'Failed to send reset link'
  }

  loading.value = false
}

async function handleReset() {
  if (form.value.newPassword !== form.value.confirmPassword) {
    error.value = 'Passwords do not match'
    return
  }

  loading.value = true
  error.value = ''

  const result = await authStore.resetPassword(token.value, form.value.newPassword)

  if (result.success) {
    success.value = true
    setTimeout(() => {
      router.push('/login')
    }, 2000)
  } else {
    error.value = result.error || 'Password reset failed'
  }

  loading.value = false
}
</script>

