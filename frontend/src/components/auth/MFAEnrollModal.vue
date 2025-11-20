<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white rounded-lg shadow-xl p-8 max-w-md w-full mx-4">
      <h2 class="text-2xl font-bold mb-4">Enable MFA</h2>
      <p class="text-sm text-gray-600 mb-6">
        Enter your password to enable multi-factor authentication.
      </p>
      <form @submit.prevent="handleEnroll" class="space-y-4">
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
          />
        </div>
        <div v-if="error" class="text-red-600 text-sm">{{ error }}</div>
        <div class="flex space-x-3">
          <button
            type="submit"
            :disabled="loading"
            class="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {{ loading ? 'Enabling...' : 'Enable MFA' }}
          </button>
          <button
            type="button"
            @click="$emit('close')"
            class="flex-1 bg-gray-200 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-300"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../../stores/auth'

const emit = defineEmits(['close', 'success'])

const authStore = useAuthStore()
const form = ref({ password: '' })
const loading = ref(false)
const error = ref('')

async function handleEnroll() {
  loading.value = true
  error.value = ''

  const result = await authStore.enrollMFA(form.value.password)

  if (result.success) {
    emit('success')
    emit('close')
  } else {
    error.value = result.error || 'Failed to enable MFA'
  }

  loading.value = false
}
</script>

