<template>
  <div style="max-width: 500px; margin: 4rem auto;">
    <h2>Profile</h2>
    <div style="margin-bottom: 1.5rem; color: #555;">
      <label>Email</label><br />
      <span>{{ email }}</span>
    </div>
    <form @submit.prevent="handleSubmit">
      <div style="margin-bottom: 1rem;">
        <label>Full Name</label><br />
        <input v-model="fullName" type="text" required style="width: 100%; padding: 0.5rem;" />
      </div>
      <div style="margin-bottom: 1rem;">
        <label>Username</label><br />
        <input v-model="username" type="text" required style="width: 100%; padding: 0.5rem;" />
      </div>
      <div style="margin-bottom: 1rem;">
        <label>Skill Level (0–10)</label><br />
        <input v-model.number="skillLevel" type="number" min="0" max="10" required style="width: 100%; padding: 0.5rem;" />
      </div>
      <div style="margin-bottom: 1rem;">
        <label>Gender</label><br />
        <select v-model="gender" required style="width: 100%; padding: 0.5rem;">
          <option value="" disabled>Select gender</option>
          <option value="male">Male</option>
          <option value="female">Female</option>
        </select>
      </div>
      <p v-if="error" style="color: red;">{{ error }}</p>
      <button type="submit" :disabled="loading">{{ loading ? 'Saving…' : 'Save Profile' }}</button>
    </form>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getMe, updateProfile } from '../services/api'

const router = useRouter()
const email = ref('')
const fullName = ref('')
const username = ref('')
const skillLevel = ref(5)
const gender = ref('')
const error = ref('')
const loading = ref(false)

onMounted(async () => {
  try {
    const res = await getMe()
    email.value = res.data.email ?? ''
    fullName.value = res.data.full_name ?? ''
    username.value = res.data.username ?? ''
    skillLevel.value = res.data.skill_level ?? 5
    gender.value = res.data.gender ?? ''
  } catch {
    // unauthenticated — router guard will redirect
  }
})

async function handleSubmit() {
  error.value = ''
  loading.value = true
  try {
    await updateProfile({
      full_name: fullName.value,
      username: username.value,
      skill_level: skillLevel.value,
      gender: gender.value,
    })
    router.push('/people')
  } catch (e) {
    error.value = e.response?.data?.error || 'Failed to save profile'
  } finally {
    loading.value = false
  }
}
</script>
