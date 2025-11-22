<template>
  <div class="max-w-4xl mx-auto mt-8 p-6">
    <h1 class="text-3xl font-bold mb-6">Security Dashboard</h1>
    
    <div v-if="loading" class="text-center py-8">Loading...</div>
    
    <div v-else-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
      {{ error }}
    </div>
    
    <div v-else class="space-y-6">
      <!-- Security Status -->
      <div class="bg-white rounded-lg shadow-md p-6">
        <h2 class="text-xl font-semibold mb-4">Security Status</h2>
        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <span>MFA Enabled:</span>
            <span :class="securityData.mfa_enabled ? 'text-green-600' : 'text-red-600'">
              {{ securityData.mfa_enabled ? 'Yes' : 'No' }}
            </span>
          </div>
          <div class="flex items-center justify-between">
            <span>Email Verified:</span>
            <span :class="securityData.email_verified ? 'text-green-600' : 'text-red-600'">
              {{ securityData.email_verified ? 'Yes' : 'No' }}
            </span>
          </div>
        </div>
        <div class="mt-4">
          <button
            v-if="!securityData.mfa_enabled"
            @click="showMFAEnroll = true"
            class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Enable MFA
          </button>
          <button
            v-else
            @click="showMFADisable = true"
            class="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
          >
            Disable MFA
          </button>
        </div>
      </div>

      <!-- Active Sessions -->
      <div class="bg-white rounded-lg shadow-md p-6">
        <h2 class="text-xl font-semibold mb-4">Active Sessions</h2>
        <div v-if="securityData.active_sessions.length === 0" class="text-gray-500">
          No active sessions
        </div>
        <div v-else class="space-y-3">
          <div
            v-for="session in securityData.active_sessions"
            :key="session.id"
            class="border rounded p-4 flex justify-between items-center"
          >
            <div>
              <div class="font-medium">{{ session.device_info || 'Unknown Device' }}</div>
              <div class="text-sm text-gray-600">{{ session.ip_address }}</div>
              <div class="text-sm text-gray-500">Last activity: {{ formatDate(session.last_activity) }}</div>
            </div>
            <button
              @click="revokeSession(session.id)"
              class="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
            >
              Revoke
            </button>
          </div>
        </div>
      </div>

      <!-- Trusted Devices -->
      <div class="bg-white rounded-lg shadow-md p-6">
        <h2 class="text-xl font-semibold mb-4">Trusted Devices</h2>
        <div v-if="securityData.trusted_devices.length === 0" class="text-gray-500">
          No trusted devices
        </div>
        <div v-else class="space-y-3">
          <div
            v-for="device in securityData.trusted_devices"
            :key="device.id"
            class="border rounded p-4 flex justify-between items-center"
          >
            <div>
              <div class="font-medium">{{ device.device_name }}</div>
              <div class="text-sm text-gray-600">{{ device.ip_address }}</div>
              <div class="text-sm text-gray-500">Last used: {{ formatDate(device.last_used) }}</div>
            </div>
            <button
              @click="removeDevice(device.id)"
              class="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
            >
              Remove
            </button>
          </div>
        </div>
      </div>

      <!-- Recent Auth Events -->
      <div class="bg-white rounded-lg shadow-md p-6">
        <h2 class="text-xl font-semibold mb-4">Recent Authentication Events</h2>
        <div v-if="securityData.recent_auth_events.length === 0" class="text-gray-500">
          No recent events
        </div>
        <div v-else class="space-y-2">
          <div
            v-for="(event, index) in securityData.recent_auth_events"
            :key="index"
            class="border-b pb-2"
          >
            <div class="font-medium">{{ event.event_type }}</div>
            <div class="text-sm text-gray-600">{{ event.ip_address }}</div>
            <div class="text-sm text-gray-500">{{ formatDate(event.created_at) }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- MFA Enrollment Modal -->
    <MFAEnrollModal v-if="showMFAEnroll" @close="showMFAEnroll = false" @success="loadSecurityData" />
    
    <!-- MFA Disable Modal -->
    <MFADisableModal v-if="showMFADisable" @close="showMFADisable = false" @success="loadSecurityData" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { authAPI } from '../services/api'
import MFAEnrollModal from '../components/auth/MFAEnrollModal.vue'
import MFADisableModal from '../components/auth/MFADisableModal.vue'

const authStore = useAuthStore()
const securityData = ref({
  mfa_enabled: false,
  email_verified: false,
  active_sessions: [],
  trusted_devices: [],
  recent_auth_events: []
})
const loading = ref(true)
const error = ref('')
const showMFAEnroll = ref(false)
const showMFADisable = ref(false)

function formatDate(dateString) {
  return new Date(dateString).toLocaleString()
}

async function loadSecurityData() {
  loading.value = true
  error.value = ''
  
  const result = await authStore.getSecurityDashboard()
  
  if (result.success) {
    securityData.value = result.data
  } else {
    error.value = result.error || 'Failed to load security data'
  }
  
  loading.value = false
}

async function revokeSession(sessionId) {
  try {
    await authAPI.revokeSession(sessionId)
    await loadSecurityData()
  } catch (err) {
    error.value = 'Failed to revoke session'
  }
}

async function removeDevice(deviceId) {
  try {
    await authAPI.removeTrustedDevice(deviceId)
    await loadSecurityData()
  } catch (err) {
    error.value = 'Failed to remove device'
  }
}

onMounted(() => {
  loadSecurityData()
})
</script>

