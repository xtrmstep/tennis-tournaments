<template>
  <div style="max-width: 700px;">
    <h2>Sorting</h2>

    <div style="margin-bottom: 1rem;">
      <label style="margin-right: 1rem;">
        <input type="radio" v-model="mode" value="singles" /> Singles
      </label>
      <label>
        <input type="radio" v-model="mode" value="doubles" /> Doubles
      </label>
    </div>

    <button @click="handleRun" :disabled="loading">
      {{ loading ? 'Running…' : 'Run Sorting' }}
    </button>

    <p v-if="error" style="color: red; margin-top: 1rem;">{{ error }}</p>

    <div v-if="result" style="margin-top: 2rem;">
      <h3>Result — {{ result.mode }} ({{ result.generated_at }})</h3>

      <!-- Singles result -->
      <ol v-if="result.mode === 'singles'">
        <li v-for="person in result.items" :key="person.id" style="margin-bottom: 0.5rem;">
          <strong>{{ person.name }}</strong>
          — Rating: {{ person.rating ?? '—' }}
          <span v-if="person.skill"> | Skill: {{ person.skill }}</span>
        </li>
      </ol>

      <!-- Doubles result -->
      <table v-else style="width: 100%; border-collapse: collapse; margin-top: 1rem;">
        <thead>
          <tr>
            <th style="text-align: left; padding: 0.5rem; border-bottom: 1px solid #ccc;">Team</th>
            <th style="text-align: left; padding: 0.5rem; border-bottom: 1px solid #ccc;">Player 1</th>
            <th style="text-align: left; padding: 0.5rem; border-bottom: 1px solid #ccc;">Player 2</th>
            <th style="text-align: left; padding: 0.5rem; border-bottom: 1px solid #ccc;">Pair Strength</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="team in result.items" :key="team.team_id">
            <td style="padding: 0.5rem;">{{ team.team_id }}</td>
            <td style="padding: 0.5rem;">{{ team.player1.name }} ({{ team.player1.rating ?? '—' }})</td>
            <td style="padding: 0.5rem;">{{ team.player2.name }} ({{ team.player2.rating ?? '—' }})</td>
            <td style="padding: 0.5rem;">{{ team.pair_strength }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { runSorting } from '../services/api'

const mode = ref('singles')
const loading = ref(false)
const error = ref('')
const result = ref(null)

async function handleRun() {
  error.value = ''
  result.value = null
  loading.value = true
  try {
    const res = await runSorting(mode.value)
    result.value = res.data
  } catch (e) {
    error.value = e.response?.data?.error || 'Sorting failed'
  } finally {
    loading.value = false
  }
}
</script>
