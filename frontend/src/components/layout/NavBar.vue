<template>
  <nav class="bg-white shadow-md">
    <div class="container mx-auto px-4">
      <div class="flex justify-between items-center h-16">
        <div class="flex items-center space-x-8">
          <router-link to="/" class="text-xl font-bold text-blue-600">
            PromptShare
          </router-link>
          <div class="hidden md:flex space-x-4">
            <router-link
              to="/prompts"
              class="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium"
            >
              Prompts
            </router-link>
            <router-link
              to="/search"
              class="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium"
            >
              Search
            </router-link>
            <router-link
              to="/collections"
              class="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium"
            >
              Collections
            </router-link>
            <router-link
              to="/onboarding"
              class="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium"
            >
              Getting Started
            </router-link>
          </div>
        </div>
        <div class="flex items-center space-x-4">
          <template v-if="authStore.isAuthenticated">
            <router-link
              to="/notifications"
              class="relative text-gray-700 hover:text-blue-600"
            >
              <svg
                class="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                />
              </svg>
            </router-link>
            <router-link
              to="/prompts/create"
              class="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700"
            >
              Create Prompt
            </router-link>
            <div class="relative">
              <button
                @click="showMenu = !showMenu"
                class="flex items-center space-x-2 text-gray-700 hover:text-blue-600"
              >
                <span>{{ authStore.user?.username || 'User' }}</span>
                <svg
                  class="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M19 9l-7 7-7-7"
                  />
                </svg>
              </button>
              <div
                v-if="showMenu"
                class="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-10"
              >
                <router-link
                  to="/profile"
                  class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  Profile
                </router-link>
                <router-link
                  v-if="authStore.isAdmin"
                  to="/admin"
                  class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  Admin Dashboard
                </router-link>
                <button
                  @click="handleLogout"
                  class="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  Logout
                </button>
              </div>
            </div>
          </template>
          <template v-else>
            <router-link
              to="/login"
              class="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium"
            >
              Login
            </router-link>
          </template>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const authStore = useAuthStore()
const router = useRouter()
const showMenu = ref(false)

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}
</script>

