/**
 * Vue Router configuration.
 */

import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue'),
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { requiresGuest: true },
  },
  {
    path: '/prompts',
    name: 'Prompts',
    component: () => import('../views/PromptsList.vue'),
  },
  {
    path: '/prompts/:id',
    name: 'PromptDetail',
    component: () => import('../views/PromptDetail.vue'),
  },
  {
    path: '/prompts/create',
    name: 'CreatePrompt',
    component: () => import('../views/CreatePrompt.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/prompts/:id/edit',
    name: 'EditPrompt',
    component: () => import('../views/EditPrompt.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/search',
    name: 'Search',
    component: () => import('../views/Search.vue'),
  },
  {
    path: '/collections',
    name: 'Collections',
    component: () => import('../views/Collections.vue'),
  },
  {
    path: '/collections/:id',
    name: 'CollectionDetail',
    component: () => import('../views/CollectionDetail.vue'),
  },
  {
    path: '/notifications',
    name: 'Notifications',
    component: () => import('../views/Notifications.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/onboarding',
    name: 'Onboarding',
    component: () => import('../views/Onboarding.vue'),
  },
  {
    path: '/admin',
    name: 'AdminDashboard',
    component: () => import('../views/AdminDashboard.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../views/NotFound.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Navigation guards
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  // Check if route requires authentication
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }

  // Check if route requires admin
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    next({ name: 'Home' })
    return
  }

  // Redirect authenticated users away from login page
  if (to.meta.requiresGuest && authStore.isAuthenticated) {
    next({ name: 'Home' })
    return
  }

  next()
})

export default router

