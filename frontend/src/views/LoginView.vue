<template>
  <div style="max-width: 400px; margin: 4rem auto;">
    <h2>Login</h2>
    <form @submit.prevent="handleSubmit">
      <div style="margin-bottom: 1rem;">
        <label>Email</label><br />
        <input v-model="email" type="email" required style="width: 100%; padding: 0.5rem;" />
      </div>
      <div style="margin-bottom: 1rem;">
        <label>Password</label><br />
        <input v-model="password" type="password" required style="width: 100%; padding: 0.5rem;" />
      </div>
      <p v-if="error" style="color: red;">{{ error }}</p>
      <button type="submit" :disabled="loading">{{ loading ? 'Logging in…' : 'Login' }}</button>
    </form>
    <p style="margin-top: 1rem;">
      Don't have an account? <RouterLink to="/signup">Sign up</RouterLink>
    </p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute, RouterLink } from 'vue-router'
import { login } from '../services/api'

const router = useRouter()
const route = useRoute()
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleSubmit() {
  error.value = ''
  loading.value = true
  try {
    const res = await login(email.value, password.value)
    if (!res.data.profile_complete) {
      router.push('/profile')
    } else {
      const next = route.query.next
      router.push(next && next !== '/login' ? next : '/people')
    }
  } catch (e) {
    error.value = e.response?.data?.error || 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>
