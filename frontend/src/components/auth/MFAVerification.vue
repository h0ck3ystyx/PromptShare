<template>
  <div class="max-w-md mx-auto mt-12">
    <div class="bg-white rounded-lg shadow-md p-8">
      <h1 class="text-2xl font-bold text-center mb-6">MFA Verification</h1>
      <p class="text-sm text-gray-600 text-center mb-6">
        We've sent a 6-digit code to your email. Please enter it below.
      </p>
      <form @submit.prevent="handleVerify" class="space-y-4">
        <div>
          <label for="code" class="block text-sm font-medium text-gray-700 mb-1">
            Verification Code
          </label>
          <input
            id="code"
            v-model="form.code"
            type="text"
            maxlength="6"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-center text-2xl tracking-widest"
            placeholder="000000"
            @input="form.code = form.code.replace(/\D/g, '')"
          />
        </div>
        <div class="flex items-center">
          <input
            id="rememberDevice"
            v-model="form.rememberDevice"
            type="checkbox"
            class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label for="rememberDevice" class="ml-2 block text-sm text-gray-700">
            Remember this device for 30 days
          </label>
        </div>
        <div v-if="error" class="text-red-600 text-sm">{{ error }}</div>
        <button
          type="submit"
          :disabled="loading || form.code.length !== 6"
          class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ loading ? 'Verifying...' : 'Verify' }}
        </button>
        <button
          type="button"
          @click="$emit('cancel')"
          class="w-full bg-gray-200 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-300"
        >
          Cancel
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../../stores/auth'

const emit = defineEmits(['success', 'cancel'])

const authStore = useAuthStore()
const form = ref({
  code: '',
  rememberDevice: false
})
const loading = ref(false)
const error = ref('')

async function handleVerify() {
  if (form.value.code.length !== 6) {
    error.value = 'Please enter a 6-digit code'
    return
  }

  loading.value = true
  error.value = ''

  const result = await authStore.verifyMFA(form.value.code, form.value.rememberDevice)

  if (result.success) {
    emit('success')
  } else {
    error.value = result.error || 'Verification failed'
  }

  loading.value = false
}
</script>

