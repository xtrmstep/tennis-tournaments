<template>
  <div style="max-width: 400px; margin: 4rem auto;">
    <h2>Sign Up</h2>
    <form @submit.prevent="handleSubmit">
      <div style="margin-bottom: 1rem;">
        <label>Email</label><br />
        <input v-model="email" type="email" required style="width: 100%; padding: 0.5rem;" />
      </div>
      <div style="margin-bottom: 1rem;">
        <label>Password (min 6 chars)</label><br />
        <input v-model="password" type="password" required style="width: 100%; padding: 0.5rem;" />
      </div>
      <p v-if="error" style="color: red;">{{ error }}</p>
      <button type="submit" :disabled="loading">{{ loading ? 'Creating account…' : 'Sign Up' }}</button>
    </form>
    <p style="margin-top: 1rem;">
      Already have an account? <RouterLink to="/login">Login</RouterLink>
    </p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { signup } from '../services/api'

const router = useRouter()
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleSubmit() {
  error.value = ''
  loading.value = true
  try {
    await signup(email.value, password.value)
    router.push('/profile')
  } catch (e) {
    error.value = e.response?.data?.error || 'Sign up failed'
  } finally {
    loading.value = false
  }
}
</script>
