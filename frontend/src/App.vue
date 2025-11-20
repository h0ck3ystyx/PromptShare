<template>
  <div class="min-h-screen bg-gray-50">
    <NavBar />
    <main class="container mx-auto px-4 py-8">
      <router-view />
    </main>
    <Footer />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'
import NavBar from './components/layout/NavBar.vue'
import Footer from './components/layout/Footer.vue'

const authStore = useAuthStore()

onMounted(async () => {
  // Fetch current user if token exists
  if (authStore.isAuthenticated) {
    await authStore.fetchCurrentUser()
  }
})
</script>
