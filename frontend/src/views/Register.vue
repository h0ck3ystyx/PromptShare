<template>
  <div class="max-w-md mx-auto mt-12">
    <div class="bg-white rounded-lg shadow-md p-8">
      <h1 class="text-2xl font-bold text-center mb-6">Create Account</h1>
      <form @submit.prevent="handleRegister" class="space-y-4">
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
        <div>
          <label for="username" class="block text-sm font-medium text-gray-700 mb-1">
            Username
          </label>
          <input
            id="username"
            v-model="form.username"
            type="text"
            required
            minlength="3"
            maxlength="100"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Choose a username"
          />
        </div>
        <div>
          <label for="fullName" class="block text-sm font-medium text-gray-700 mb-1">
            Full Name
          </label>
          <input
            id="fullName"
            v-model="form.fullName"
            type="text"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Your full name"
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
            minlength="8"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Minimum 8 characters"
            @input="validatePassword"
          />
          <div v-if="passwordValidation" class="mt-2 text-sm">
            <div v-if="passwordValidation.valid" class="text-green-600">
              ✓ Password strength: {{ passwordValidation.score }}/4
            </div>
            <div v-else class="text-red-600">
              <div v-for="feedback in passwordValidation.feedback" :key="feedback">
                • {{ feedback }}
              </div>
            </div>
          </div>
        </div>
        <div class="flex items-center">
          <input
            id="rememberMe"
            v-model="form.rememberMe"
            type="checkbox"
            class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label for="rememberMe" class="ml-2 block text-sm text-gray-700">
            Remember me
          </label>
        </div>
        <div v-if="error" class="text-red-600 text-sm">{{ error }}</div>
        <div v-if="success" class="text-green-600 text-sm">
          Registration successful! Please check your email to verify your account.
        </div>
        <button
          type="submit"
          :disabled="loading || !passwordValid"
          class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ loading ? 'Registering...' : 'Register' }}
        </button>
        <div class="text-center text-sm">
          <router-link to="/login" class="text-blue-600 hover:underline">
            Already have an account? Login
          </router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { authAPI } from '../services/api'

const router = useRouter()
const authStore = useAuthStore()

const form = ref({
  email: '',
  username: '',
  fullName: '',
  password: '',
  rememberMe: false
})
const loading = ref(false)
const error = ref('')
const success = ref(false)
const passwordValidation = ref(null)
const passwordValid = computed(() => passwordValidation.value?.valid || false)

async function validatePassword() {
  if (form.value.password.length < 8) {
    passwordValidation.value = null
    return
  }

  try {
    const response = await authAPI.validatePassword(form.value.password)
    passwordValidation.value = response.data
  } catch (err) {
    passwordValidation.value = null
  }
}

async function handleRegister() {
  loading.value = true
  error.value = ''
  success.value = false

  const result = await authStore.register({
    email: form.value.email,
    username: form.value.username,
    full_name: form.value.fullName,
    password: form.value.password,
    remember_me: form.value.rememberMe
  })

  if (result.success) {
    success.value = true
    setTimeout(() => {
      router.push('/login')
    }, 3000)
  } else {
    error.value = result.error || 'Registration failed'
  }

  loading.value = false
}
</script>

