<template>
  <div>
    <!-- Header -->
    <div style="display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; margin-bottom: 1rem;">
      <RouterLink to="/competitions" style="color: #2c5f2e; text-decoration: none;">← Competitions</RouterLink>
      <h2 style="margin: 0;">{{ competition.name }}</h2>
      <span :style="statusStyle(competition.status)">{{ competition.status }}</span>
      <span style="color: #666; font-size: 0.9rem; text-transform: capitalize;">{{ competition.event_type }}</span>
    </div>

    <p v-if="loadError" style="color: red;">{{ loadError }}</p>

    <p v-if="competition.description" style="color: #444; margin-bottom: 1rem;">{{ competition.description }}</p>

    <!-- Inline edit form (admin/mod, draft only) -->
    <div v-if="canManage && competition.status === 'draft'" style="background: #f5f5f5; padding: 1rem; border-radius: 4px; margin-bottom: 1rem;">
      <strong>Edit</strong>
      <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 0.5rem; align-items: flex-end;">
        <div>
          <label style="display: block; font-size: 0.85rem;">Name</label>
          <input v-model="edit.name" type="text" style="padding: 0.4rem;" />
        </div>
        <div>
          <label style="display: block; font-size: 0.85rem;">Type</label>
          <select v-model="edit.event_type" style="padding: 0.4rem;">
            <option value="singles">Singles</option>
            <option value="doubles">Doubles</option>
          </select>
        </div>
        <div style="flex: 1; min-width: 200px;">
          <label style="display: block; font-size: 0.85rem;">Description</label>
          <input v-model="edit.description" type="text" style="padding: 0.4rem; width: 100%; box-sizing: border-box;" />
        </div>
        <button @click="saveEdit" style="padding: 0.4rem 1rem; background: #2c5f2e; color: white; border: none; cursor: pointer; border-radius: 4px;">Save</button>
      </div>
      <p v-if="editError" style="color: red; margin-top: 0.5rem;">{{ editError }}</p>
    </div>

    <!-- Lifecycle transition (admin/mod) -->
    <div v-if="canManage && nextStatus" style="margin-bottom: 1.5rem;">
      <button
        @click="doTransition"
        :disabled="transitioning"
        style="padding: 0.5rem 1.2rem; background: #1a6ea0; color: white; border: none; cursor: pointer; border-radius: 4px;"
      >{{ transitioning ? '…' : `Move to "${nextStatus}"` }}</button>
      <p v-if="transitionError" style="color: red; margin-top: 0.5rem;">{{ transitionError }}</p>
    </div>

    <!-- Players section -->
    <section style="margin-bottom: 2rem;">
      <h3 style="margin-bottom: 0.5rem;">
        Players
        <span style="font-weight: normal; font-size: 0.9rem; color: #666;">
          ({{ confirmedPlayers.length }} confirmed, {{ candidates.length }} candidates)
        </span>
      </h3>

      <!-- Apply / Withdraw (regular user, published state) -->
      <div v-if="!canManage && competition.status === 'published'" style="margin-bottom: 0.75rem;">
        <button
          v-if="!myPlayerEntry"
          @click="apply"
          style="padding: 0.4rem 1rem; background: #2c5f2e; color: white; border: none; cursor: pointer; border-radius: 4px;"
        >Apply to compete</button>
        <div v-else>
          <span style="color: #2c5f2e; margin-right: 1rem;">
            ✓ Applied ({{ myPlayerEntry.status }})
          </span>
          <button
            v-if="myPlayerEntry.status === 'candidate'"
            @click="withdraw"
            style="padding: 0.4rem 1rem; background: #a00; color: white; border: none; cursor: pointer; border-radius: 4px;"
          >Withdraw</button>
        </div>
        <p v-if="applyError" style="color: red; margin-top: 0.4rem;">{{ applyError }}</p>
      </div>

      <table v-if="players.length" style="width: 100%; border-collapse: collapse;">
        <thead>
          <tr>
            <th style="text-align: left; padding: 0.4rem; border-bottom: 1px solid #ccc;">Name</th>
            <th style="text-align: left; padding: 0.4rem; border-bottom: 1px solid #ccc;">Username</th>
            <th style="text-align: left; padding: 0.4rem; border-bottom: 1px solid #ccc;">Status</th>
            <th v-if="canManage" style="padding: 0.4rem; border-bottom: 1px solid #ccc;"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in players" :key="p.id">
            <td style="padding: 0.4rem;">{{ p.full_name || '—' }}</td>
            <td style="padding: 0.4rem;">{{ p.username || '—' }}</td>
            <td style="padding: 0.4rem;">
              <span :style="playerStatusStyle(p.status)">{{ p.status }}</span>
            </td>
            <td v-if="canManage" style="padding: 0.4rem; white-space: nowrap;">
              <button
                v-if="p.status === 'candidate'"
                @click="confirmPlayer(p.id)"
                style="padding: 0.25rem 0.6rem; background: #2c5f2e; color: white; border: none; cursor: pointer; border-radius: 3px; margin-right: 0.25rem; font-size: 0.85rem;"
              >Confirm</button>
              <button
                v-if="p.status === 'player'"
                @click="demotePlayer(p.id)"
                style="padding: 0.25rem 0.6rem; background: #888; color: white; border: none; cursor: pointer; border-radius: 3px; margin-right: 0.25rem; font-size: 0.85rem;"
              >Demote</button>
              <button
                @click="deletePlayer(p.id)"
                style="padding: 0.25rem 0.6rem; background: #a00; color: white; border: none; cursor: pointer; border-radius: 3px; font-size: 0.85rem;"
              >Remove</button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else style="color: #888;">No participants yet.</p>
    </section>

    <!-- Matches section (draw / match / finished) -->
    <section v-if="['draw', 'match', 'finished'].includes(competition.status)">
      <h3 style="margin-bottom: 0.5rem;">Matches</h3>

      <!-- Create match form (admin/mod, draw state) -->
      <div v-if="canManage && competition.status === 'draw'" style="background: #f5f5f5; padding: 1rem; border-radius: 4px; margin-bottom: 1rem;">
        <strong>Create Match</strong>
        <div style="display: flex; gap: 0.5rem; align-items: flex-end; margin-top: 0.5rem; flex-wrap: wrap;">
          <div>
            <label style="display: block; font-size: 0.85rem;">Player A</label>
            <select v-model="newMatch.playerA" style="padding: 0.4rem;">
              <option value="">Select…</option>
              <option v-for="p in confirmedPlayers" :key="p.id" :value="p.id">
                {{ p.full_name || p.username || p.user_id }}
              </option>
            </select>
          </div>
          <div>
            <label style="display: block; font-size: 0.85rem;">Player B</label>
            <select v-model="newMatch.playerB" style="padding: 0.4rem;">
              <option value="">Select…</option>
              <option v-for="p in confirmedPlayers" :key="p.id" :value="p.id">
                {{ p.full_name || p.username || p.user_id }}
              </option>
            </select>
          </div>
          <button
            @click="addMatch"
            style="padding: 0.4rem 1rem; background: #2c5f2e; color: white; border: none; cursor: pointer; border-radius: 4px;"
          >Add Match</button>
        </div>
        <p v-if="matchError" style="color: red; margin-top: 0.4rem;">{{ matchError }}</p>
      </div>

      <table v-if="matches.length" style="width: 100%; border-collapse: collapse;">
        <thead>
          <tr>
            <th style="text-align: left; padding: 0.4rem; border-bottom: 1px solid #ccc;">#</th>
            <th style="text-align: left; padding: 0.4rem; border-bottom: 1px solid #ccc;">Player A</th>
            <th style="text-align: left; padding: 0.4rem; border-bottom: 1px solid #ccc;">Player B</th>
            <th style="text-align: left; padding: 0.4rem; border-bottom: 1px solid #ccc;">Score</th>
            <th v-if="competition.status === 'match'" style="padding: 0.4rem; border-bottom: 1px solid #ccc;"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(m, idx) in matches" :key="m.id">
            <td style="padding: 0.4rem;">{{ idx + 1 }}</td>
            <td style="padding: 0.4rem;">{{ m.player_a_name }}</td>
            <td style="padding: 0.4rem;">{{ m.player_b_name }}</td>
            <td style="padding: 0.4rem;">
              <span v-if="m.score_a !== null && m.score_b !== null">
                {{ m.score_a }} – {{ m.score_b }}
              </span>
              <span v-else style="color: #aaa;">—</span>
            </td>
            <td v-if="competition.status === 'match'" style="padding: 0.4rem;">
              <div v-if="canScoreMatch(m)" style="display: flex; gap: 0.3rem; align-items: center;">
                <input
                  v-model.number="scoreInputs[m.id].a"
                  type="number"
                  min="0"
                  style="width: 50px; padding: 0.2rem;"
                  placeholder="A"
                />
                <span>–</span>
                <input
                  v-model.number="scoreInputs[m.id].b"
                  type="number"
                  min="0"
                  style="width: 50px; padding: 0.2rem;"
                  placeholder="B"
                />
                <button
                  @click="submitScore(m.id)"
                  style="padding: 0.2rem 0.6rem; background: #1a6ea0; color: white; border: none; cursor: pointer; border-radius: 3px; font-size: 0.85rem;"
                >Save</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else style="color: #888;">No matches yet.</p>
      <p v-if="scoreError" style="color: red; margin-top: 0.4rem;">{{ scoreError }}</p>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import {
  getMe,
  getCompetition,
  updateCompetition,
  transitionCompetition,
  getCompetitionPlayers,
  applyToCompetition,
  withdrawFromCompetition,
  updatePlayerStatus,
  removePlayer,
  getCompetitionMatches,
  createMatch,
  setMatchScore,
} from '../services/api'

const route = useRoute()
const id = route.params.id

const competition = ref({ name: '', status: '', event_type: '', description: '' })
const players = ref([])
const matches = ref([])
const currentUser = ref(null)
const loadError = ref('')

const canManage = computed(() =>
  currentUser.value && (currentUser.value.is_admin || currentUser.value.is_moderator)
)
const confirmedPlayers = computed(() => players.value.filter(p => p.status === 'player'))
const candidates = computed(() => players.value.filter(p => p.status === 'candidate'))
const myPlayerEntry = computed(() =>
  currentUser.value
    ? players.value.find(p => p.user_id === currentUser.value.id) || null
    : null
)
const nextStatus = computed(() => {
  const map = { draft: 'published', published: 'draw', draw: 'match', match: 'finished' }
  return map[competition.value.status] || null
})

// Score inputs keyed by match id
const scoreInputs = ref({})

// Edit form
const edit = ref({ name: '', description: '', event_type: 'singles' })
const editError = ref('')

// Transition
const transitioning = ref(false)
const transitionError = ref('')

// Apply/withdraw
const applyError = ref('')

// New match
const newMatch = ref({ playerA: '', playerB: '' })
const matchError = ref('')

// Score
const scoreError = ref('')

const STATUS_COLORS = {
  draft: '#888',
  published: '#2c5f2e',
  draw: '#1a6ea0',
  match: '#c07000',
  finished: '#555',
}

function statusStyle(status) {
  const color = STATUS_COLORS[status] || '#333'
  return `background:${color};color:white;padding:0.15rem 0.6rem;border-radius:3px;font-size:0.85rem;`
}

function playerStatusStyle(status) {
  return status === 'player'
    ? 'background:#2c5f2e;color:white;padding:0.1rem 0.4rem;border-radius:3px;font-size:0.8rem;'
    : 'background:#888;color:white;padding:0.1rem 0.4rem;border-radius:3px;font-size:0.8rem;'
}

function canScoreMatch(m) {
  if (!currentUser.value) return false
  if (canManage.value) return true
  return m.player_a_user_id === currentUser.value.id || m.player_b_user_id === currentUser.value.id
}

function initScoreInputs() {
  matches.value.forEach(m => {
    if (!scoreInputs.value[m.id]) {
      scoreInputs.value[m.id] = { a: m.score_a ?? '', b: m.score_b ?? '' }
    }
  })
}

async function load() {
  try {
    const [meRes, compRes, playersRes] = await Promise.all([
      getMe(),
      getCompetition(id),
      getCompetitionPlayers(id),
    ])
    currentUser.value = meRes.data
    competition.value = compRes.data
    players.value = playersRes.data
    edit.value = {
      name: compRes.data.name,
      description: compRes.data.description || '',
      event_type: compRes.data.event_type,
    }

    if (['draw', 'match', 'finished'].includes(compRes.data.status)) {
      const matchRes = await getCompetitionMatches(id)
      matches.value = matchRes.data
      initScoreInputs()
    }
  } catch {
    loadError.value = 'Failed to load competition.'
  }
}

async function saveEdit() {
  editError.value = ''
  try {
    const res = await updateCompetition(id, edit.value)
    competition.value = res.data
  } catch (e) {
    editError.value = e.response?.data?.error || 'Update failed.'
  }
}

async function doTransition() {
  transitionError.value = ''
  transitioning.value = true
  try {
    const res = await transitionCompetition(id, nextStatus.value)
    competition.value = res.data
    if (['draw', 'match', 'finished'].includes(res.data.status)) {
      const matchRes = await getCompetitionMatches(id)
      matches.value = matchRes.data
      initScoreInputs()
    }
  } catch (e) {
    transitionError.value = e.response?.data?.error || 'Transition failed.'
  } finally {
    transitioning.value = false
  }
}

async function apply() {
  applyError.value = ''
  try {
    await applyToCompetition(id)
    const res = await getCompetitionPlayers(id)
    players.value = res.data
  } catch (e) {
    applyError.value = e.response?.data?.error || 'Failed to apply.'
  }
}

async function withdraw() {
  applyError.value = ''
  try {
    await withdrawFromCompetition(id)
    const res = await getCompetitionPlayers(id)
    players.value = res.data
  } catch (e) {
    applyError.value = e.response?.data?.error || 'Failed to withdraw.'
  }
}

async function confirmPlayer(playerId) {
  try {
    await updatePlayerStatus(id, playerId, 'player')
    const res = await getCompetitionPlayers(id)
    players.value = res.data
  } catch (e) {
    loadError.value = e.response?.data?.error || 'Failed to confirm player.'
  }
}

async function demotePlayer(playerId) {
  try {
    await updatePlayerStatus(id, playerId, 'candidate')
    const res = await getCompetitionPlayers(id)
    players.value = res.data
  } catch (e) {
    loadError.value = e.response?.data?.error || 'Failed to demote player.'
  }
}

async function deletePlayer(playerId) {
  if (!confirm('Remove this player from the competition?')) return
  try {
    await removePlayer(id, playerId)
    const res = await getCompetitionPlayers(id)
    players.value = res.data
  } catch (e) {
    loadError.value = e.response?.data?.error || 'Failed to remove player.'
  }
}

async function addMatch() {
  matchError.value = ''
  if (!newMatch.value.playerA || !newMatch.value.playerB) {
    matchError.value = 'Select both players.'
    return
  }
  try {
    await createMatch(id, newMatch.value.playerA, newMatch.value.playerB)
    newMatch.value = { playerA: '', playerB: '' }
    const res = await getCompetitionMatches(id)
    matches.value = res.data
    initScoreInputs()
  } catch (e) {
    matchError.value = e.response?.data?.error || 'Failed to create match.'
  }
}

async function submitScore(matchId) {
  scoreError.value = ''
  const inp = scoreInputs.value[matchId]
  if (inp.a === '' || inp.b === '') {
    scoreError.value = 'Enter both scores.'
    return
  }
  try {
    await setMatchScore(id, matchId, inp.a, inp.b)
    const res = await getCompetitionMatches(id)
    matches.value = res.data
    initScoreInputs()
  } catch (e) {
    scoreError.value = e.response?.data?.error || 'Failed to save score.'
  }
}

onMounted(load)
</script>
