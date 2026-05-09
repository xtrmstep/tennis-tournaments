<template>
  <div>
    <h2>People</h2>

    <div style="margin-bottom: 1rem;">
      <input
        v-model="search"
        type="search"
        placeholder="Search by name or username…"
        style="width: 100%; max-width: 360px; padding: 0.5rem; box-sizing: border-box;"
      />
    </div>

    <p v-if="loading">Loading…</p>
    <p v-if="error" style="color: red;">{{ error }}</p>

    <table v-if="!loading && filtered.length" style="width: 100%; border-collapse: collapse; margin-top: 0.5rem;">
      <thead>
        <tr>
          <th style="text-align: left; padding: 0.5rem; border-bottom: 1px solid #ccc;">Photo</th>
          <th style="text-align: left; padding: 0.5rem; border-bottom: 1px solid #ccc;">Username</th>
          <th style="text-align: left; padding: 0.5rem; border-bottom: 1px solid #ccc;">Full Name</th>
          <th style="text-align: left; padding: 0.5rem; border-bottom: 1px solid #ccc;">Skill Level</th>
          <th style="text-align: left; padding: 0.5rem; border-bottom: 1px solid #ccc;">Gender</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="user in filtered" :key="user.id">
          <td style="padding: 0.5rem;">
            <img
              v-if="user.photo_url"
              :src="user.photo_url"
              alt="photo"
              style="width: 40px; height: 40px; object-fit: cover; border-radius: 50%;"
            />
            <div
              v-else
              style="width: 40px; height: 40px; border-radius: 50%; background: #ccc; display: flex; align-items: center; justify-content: center; font-size: 1.1rem; color: #666;"
            >{{ initials(user) }}</div>
          </td>
          <td style="padding: 0.5rem;">{{ user.username || '—' }}</td>
          <td style="padding: 0.5rem;">{{ user.full_name || '—' }}</td>
          <td style="padding: 0.5rem;">{{ user.skill_level ?? '—' }}</td>
          <td style="padding: 0.5rem;">{{ user.gender || '—' }}</td>
        </tr>
      </tbody>
    </table>
    <p v-else-if="!loading && !filtered.length && search">No people match your search.</p>
    <p v-else-if="!loading">No people yet.</p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getUsers } from '../services/api'

const users = ref([])
const loading = ref(false)
const error = ref('')
const search = ref('')

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return users.value
  return users.value.filter(u =>
    (u.full_name || '').toLowerCase().includes(q) ||
    (u.username || '').toLowerCase().includes(q)
  )
})

function initials(user) {
  const name = user.full_name || user.username || ''
  return name.split(' ').map(w => w[0] || '').join('').slice(0, 2).toUpperCase() || '?'
}

onMounted(async () => {
  loading.value = true
  try {
    const res = await getUsers()
    users.value = res.data
  } catch {
    error.value = 'Failed to load people'
  } finally {
    loading.value = false
  }
})
</script>
