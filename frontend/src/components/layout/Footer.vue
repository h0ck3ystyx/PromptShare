<template>
  <footer class="bg-white border-t mt-12">
    <div class="container mx-auto px-4 py-8">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div>
          <h3 class="text-lg font-semibold mb-4">PromptShare</h3>
          <p class="text-gray-600 text-sm">
            An internal platform for sharing and discovering effective prompts for AI tools.
          </p>
        </div>
        <div>
          <h3 class="text-lg font-semibold mb-4">Quick Links</h3>
          <ul class="space-y-2 text-sm">
            <li>
              <router-link to="/prompts" class="text-gray-600 hover:text-blue-600">
                Browse Prompts
              </router-link>
            </li>
            <li>
              <router-link to="/onboarding" class="text-gray-600 hover:text-blue-600">
                Getting Started
              </router-link>
            </li>
            <li>
              <router-link to="/collections" class="text-gray-600 hover:text-blue-600">
                Collections
              </router-link>
            </li>
          </ul>
        </div>
        <div>
          <h3 class="text-lg font-semibold mb-4">Support</h3>
          <ul class="space-y-2 text-sm">
            <li>
              <router-link to="/onboarding" class="text-gray-600 hover:text-blue-600">
                Documentation
              </router-link>
            </li>
            <li>
              <a
                :href="`${apiBaseUrl}/docs`"
                target="_blank"
                class="text-gray-600 hover:text-blue-600"
              >
                API Documentation
              </a>
            </li>
          </ul>
        </div>
      </div>
      <div class="mt-8 pt-8 border-t text-center text-sm text-gray-600">
        <p>&copy; {{ new Date().getFullYear() }} PromptShare. Internal use only.</p>
      </div>
    </div>
  </footer>
</template>

<script setup>
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:7999/api'
</script>

