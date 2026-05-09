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
          <td style="padding: 0.5rem;">
            <template v-if="isAdmin">
              <input
                type="number"
                min="0"
                max="10"
                :value="pendingSkill[user.id] ?? user.skill_level ?? ''"
                @input="pendingSkill[user.id] = $event.target.valueAsNumber"
                @blur="saveSkill(user)"
                @keyup.enter="$event.target.blur()"
                style="width: 64px; padding: 0.2rem;"
              />
              <span v-if="skillError[user.id]" style="color: red; font-size: 0.8rem; margin-left: 0.3rem;">{{ skillError[user.id] }}</span>
            </template>
            <template v-else>{{ user.skill_level ?? '—' }}</template>
          </td>
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
import { getUsers, getMe, adminUpdateUserSkill } from '../services/api'

const users = ref([])
const loading = ref(false)
const error = ref('')
const search = ref('')
const isAdmin = ref(false)
const pendingSkill = ref({})
const skillError = ref({})

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

async function saveSkill(user) {
  const raw = pendingSkill.value[user.id]
  if (raw === undefined || raw === user.skill_level) return

  if (!Number.isInteger(raw) || raw < 0 || raw > 10) {
    skillError.value[user.id] = '0–10'
    return
  }

  try {
    const res = await adminUpdateUserSkill(user.id, raw)
    user.skill_level = res.data.skill_level
    delete pendingSkill.value[user.id]
    delete skillError.value[user.id]
  } catch {
    skillError.value[user.id] = 'Failed'
  }
}

onMounted(async () => {
  loading.value = true
  try {
    const [meRes, usersRes] = await Promise.all([getMe(), getUsers()])
    isAdmin.value = meRes.data.is_admin === true
    users.value = usersRes.data
  } catch {
    error.value = 'Failed to load people'
  } finally {
    loading.value = false
  }
})
</script>
