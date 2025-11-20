<template>
  <div>
    <h1 class="text-3xl font-bold mb-6">Notifications</h1>
    <div class="space-y-4">
      <div
        v-for="notification in notifications"
        :key="notification.id"
        class="bg-white rounded-lg shadow p-4"
        :class="{ 'bg-blue-50': !notification.is_read }"
      >
        <p>{{ notification.message }}</p>
        <span class="text-sm text-gray-500">
          {{ new Date(notification.created_at).toLocaleDateString() }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { notificationsAPI } from '../services/api'

const notifications = ref([])

onMounted(async () => {
  try {
    const response = await notificationsAPI.list()
    notifications.value = response.data.items || []
  } catch (error) {
    console.error('Failed to load notifications:', error)
  }
})
</script>

