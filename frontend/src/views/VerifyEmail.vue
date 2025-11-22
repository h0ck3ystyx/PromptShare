<template>
  <div class="max-w-md mx-auto mt-12">
    <div class="bg-white rounded-lg shadow-md p-8 text-center">
      <div class="mb-4">
        <h1 class="text-2xl font-bold mb-2">Email Verification</h1>
        <p class="text-gray-600" v-if="status === 'loading'">Verifying your email address...</p>
        <p class="text-green-600" v-else-if="status === 'success'">{{ message }}</p>
        <p class="text-red-600" v-else>{{ message }}</p>
      </div>
      <div class="space-y-2">
        <router-link
          v-if="status === 'success'"
          to="/login"
          class="inline-block bg-blue-600 text-white px-4 py-2 rounded-md"
        >
          Continue to Login
        </router-link>
        <router-link
          v-else
          to="/register"
          class="inline-block text-blue-600 hover:underline"
        >
          Back to Registration
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { authAPI } from '../services/api'

const route = useRoute()
const status = ref('loading')
const message = ref('Verifying your email address...')

onMounted(async () => {
  const token = route.query.token
  if (!token) {
    status.value = 'error'
    message.value = 'Verification token is missing. Please use the link sent to your email.'
    return
  }

  try {
    await authAPI.verifyEmail(token)
    status.value = 'success'
    message.value = 'Your email has been verified successfully! You can now log in.'
  } catch (error) {
    status.value = 'error'
    if (error.response?.data?.detail) {
      message.value = error.response.data.detail
    } else {
      message.value = 'We could not verify your email. The link may be invalid or expired.'
    }
  }
})
</script>
