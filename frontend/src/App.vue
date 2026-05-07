<template>
  <div>
    <nav v-if="isAuthenticated" style="padding: 1rem; background: #2c5f2e; color: white; display: flex; gap: 1rem; align-items: center;">
      <strong>🎾 Tennis Tournaments</strong>
      <RouterLink to="/people" style="color: white;">People</RouterLink>
      <RouterLink to="/sorting" style="color: white;">Sorting</RouterLink>
      <button @click="handleLogout" style="margin-left: auto; cursor: pointer;">Logout</button>
    </nav>
    <main style="padding: 1rem;">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute, useRouter, RouterLink, RouterView } from 'vue-router'
import { logout, getMe } from './services/api'

const route = useRoute()
const router = useRouter()
const isAuthenticated = ref(false)

watch(
  () => route.path,
  async () => {
    try {
      await getMe()
      isAuthenticated.value = true
    } catch {
      isAuthenticated.value = false
    }
  },
  { immediate: true }
)

async function handleLogout() {
  await logout()
  isAuthenticated.value = false
  router.push('/login')
}
</script>
