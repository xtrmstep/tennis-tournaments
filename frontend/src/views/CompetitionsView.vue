<template>
  <div>
    <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
      <h2>Competitions</h2>
      <RouterLink
        v-if="canManage"
        to="/competitions/new"
        style="padding: 0.4rem 0.9rem; background: #2c5f2e; color: white; text-decoration: none; border-radius: 4px;"
      >+ New Competition</RouterLink>
    </div>

    <p v-if="loading">Loading…</p>
    <p v-if="error" style="color: red;">{{ error }}</p>

    <table v-if="!loading && competitions.length" style="width: 100%; border-collapse: collapse;">
      <thead>
        <tr>
          <th style="text-align: left; padding: 0.5rem; border-bottom: 1px solid #ccc;">Name</th>
          <th style="text-align: left; padding: 0.5rem; border-bottom: 1px solid #ccc;">Type</th>
          <th style="text-align: left; padding: 0.5rem; border-bottom: 1px solid #ccc;">Status</th>
          <th style="text-align: left; padding: 0.5rem; border-bottom: 1px solid #ccc;">Players</th>
          <th style="text-align: left; padding: 0.5rem; border-bottom: 1px solid #ccc;">Candidates</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="c in competitions"
          :key="c.id"
          style="cursor: pointer;"
          @click="$router.push(`/competitions/${c.id}`)"
        >
          <td style="padding: 0.5rem;">{{ c.name }}</td>
          <td style="padding: 0.5rem; text-transform: capitalize;">{{ c.event_type }}</td>
          <td style="padding: 0.5rem;">
            <span :style="statusStyle(c.status)">{{ c.status }}</span>
          </td>
          <td style="padding: 0.5rem;">{{ c.player_count }}</td>
          <td style="padding: 0.5rem;">{{ c.candidate_count }}</td>
        </tr>
      </tbody>
    </table>
    <p v-else-if="!loading">No competitions yet.</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { getMe, getCompetitions } from '../services/api'

const router = useRouter()
const competitions = ref([])
const loading = ref(false)
const error = ref('')
const canManage = ref(false)

const STATUS_COLORS = {
  draft: '#888',
  published: '#2c5f2e',
  draw: '#1a6ea0',
  match: '#c07000',
  finished: '#555',
}

function statusStyle(status) {
  const color = STATUS_COLORS[status] || '#333'
  return `background:${color};color:white;padding:0.15rem 0.5rem;border-radius:3px;font-size:0.8rem;`
}

onMounted(async () => {
  loading.value = true
  try {
    const [meRes, compRes] = await Promise.all([getMe(), getCompetitions()])
    canManage.value = meRes.data.is_admin || meRes.data.is_moderator
    competitions.value = compRes.data
  } catch {
    error.value = 'Failed to load competitions'
  } finally {
    loading.value = false
  }
})
</script>
