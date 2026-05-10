<template>
  <div>
    <!-- Header -->
    <div style="display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; margin-bottom: 1rem;">
      <RouterLink to="/competitions" style="color: #2c5f2e; text-decoration: none;">← Competitions</RouterLink>
      <h2 style="margin: 0;">{{ competition.name }}</h2>
      <span :style="statusStyle(competition.status)">{{ competition.status }}</span>
      <span style="color: #666; font-size: 0.9rem; text-transform: capitalize;">{{ competition.event_type }}</span>
      <button
        v-if="canManage && competition.id"
        @click="doDelete"
        style="margin-left: auto; padding: 0.35rem 0.9rem; background: #a00; color: white; border: none; cursor: pointer; border-radius: 4px; font-size: 0.9rem;"
      >Delete competition</button>
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

      <!-- Pending-pairs save bar (shown here so participants see it immediately after staging) -->
      <div v-if="isDirty && competition.event_type === 'doubles' && ['grouping', 'draw'].includes(competition.status)" style="display: flex; gap: 0.75rem; align-items: center; margin-bottom: 0.75rem; padding: 0.5rem 1rem; background: #fff8e1; border: 1px solid #f0c040; border-radius: 4px;">
        <span style="font-size: 0.9rem; color: #7a5000; flex: 1;">Unsaved pair changes</span>
        <button
          @click="doSave"
          style="padding: 0.35rem 1rem; background: #2c5f2e; color: white; border: none; cursor: pointer; border-radius: 4px; font-size: 0.9rem;"
        >Save</button>
        <button
          @click="discardChanges"
          style="padding: 0.35rem 0.8rem; background: #888; color: white; border: none; cursor: pointer; border-radius: 4px; font-size: 0.9rem;"
        >Discard</button>
      </div>

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
            <th v-if="competition.event_type === 'doubles' && ['grouping', 'draw', 'match', 'finished'].includes(competition.status)" style="text-align: left; padding: 0.4rem; border-bottom: 1px solid #ccc;">Partner</th>
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
            <td v-if="competition.event_type === 'doubles' && ['grouping', 'draw', 'match', 'finished'].includes(competition.status)" style="padding: 0.4rem;">
              <!-- Pending add: this player is in a staged new pair -->
              <span v-if="pendingAddFor(p.id)" style="display: flex; gap: 0.3rem; align-items: center; flex-wrap: wrap; color: #1a6ea0;">
                → {{ pendingPartnerNameFor(p.id) }} <em style="font-size: 0.8rem;">(pending)</em>
                <button
                  @click="cancelPendingAdd(p.id)"
                  style="padding: 0.1rem 0.4rem; background: #888; color: white; border: none; cursor: pointer; border-radius: 3px; font-size: 0.8rem;"
                >×</button>
              </span>
              <!-- Committed pair staged for removal -->
              <span v-else-if="allPairMap[p.id] && !effectivePairMap[p.id]" style="display: flex; gap: 0.3rem; align-items: center; color: #aaa; text-decoration: line-through;">
                {{ partnerNameOf(p, allPairMap) }}
                <button
                  v-if="canManage"
                  @click="cancelPendingRemove(allPairMap[p.id].id)"
                  style="text-decoration: none; padding: 0.1rem 0.4rem; background: #888; color: white; border: none; cursor: pointer; border-radius: 3px; font-size: 0.8rem;"
                >undo</button>
              </span>
              <!-- Active committed pair -->
              <span v-else-if="effectivePairMap[p.id]" style="display: flex; gap: 0.3rem; align-items: center; flex-wrap: wrap;">
                {{ partnerNameOf(p) }}
                <button
                  v-if="canManage && ['grouping', 'draw'].includes(competition.status)"
                  @click="stagePairRemove(effectivePairMap[p.id].id)"
                  style="padding: 0.1rem 0.4rem; background: #a00; color: white; border: none; cursor: pointer; border-radius: 3px; font-size: 0.8rem;"
                >✕</button>
              </span>
              <!-- Unpaired, can stage add -->
              <span v-else-if="canPairRow(p)" style="display: flex; gap: 0.3rem; align-items: center; flex-wrap: wrap;">
                <select v-model="pendingPartner[p.id]" style="padding: 0.3rem; font-size: 0.85rem;">
                  <option value="">Select partner…</option>
                  <option v-for="u in unpairedPlayers.filter(u => u.id !== p.id)" :key="u.id" :value="u.id">
                    {{ u.full_name || u.username || u.user_id }}
                  </option>
                </select>
                <button
                  @click="stagePairAdd(p.id, pendingPartner[p.id])"
                  :disabled="!pendingPartner[p.id]"
                  style="padding: 0.2rem 0.6rem; background: #1a5fa0; color: white; border: none; cursor: pointer; border-radius: 3px; font-size: 0.85rem;"
                >Add</button>
              </span>
              <span v-else style="color: #aaa;">—</span>
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

    <!-- Grouping section (doubles, grouping state and beyond) -->
    <section v-if="competition.event_type === 'doubles' && ['grouping', 'draw', 'match', 'finished'].includes(competition.status)" style="margin-bottom: 2rem;">
      <h3 style="margin-bottom: 0.5rem;">Pairs</h3>

      <!-- Save / Discard bar -->
      <div v-if="isDirty" style="display: flex; gap: 0.75rem; align-items: center; margin-bottom: 0.75rem; padding: 0.5rem 1rem; background: #fff8e1; border: 1px solid #f0c040; border-radius: 4px;">
        <span style="font-size: 0.9rem; color: #7a5000; flex: 1;">Unsaved changes</span>
        <button
          @click="doSave"
          style="padding: 0.35rem 1rem; background: #2c5f2e; color: white; border: none; cursor: pointer; border-radius: 4px; font-size: 0.9rem;"
        >Save</button>
        <button
          @click="discardChanges"
          style="padding: 0.35rem 0.8rem; background: #888; color: white; border: none; cursor: pointer; border-radius: 4px; font-size: 0.9rem;"
        >Discard</button>
      </div>

      <p v-if="pairError" style="color: red; margin-top: 0.4rem;">{{ pairError }}</p>
      <table v-if="pairs.length || pendingAdds.length" style="width: 100%; border-collapse: collapse;">
        <thead>
          <tr>
            <th style="text-align: left; padding: 0.4rem; border-bottom: 1px solid #ccc;">Team</th>
            <th style="text-align: left; padding: 0.4rem; border-bottom: 1px solid #ccc;">Player A</th>
            <th style="text-align: left; padding: 0.4rem; border-bottom: 1px solid #ccc;">Player B</th>
            <th v-if="['grouping', 'draw'].includes(competition.status)" style="padding: 0.4rem; border-bottom: 1px solid #ccc;"></th>
          </tr>
        </thead>
        <tbody>
          <!-- DB pairs -->
          <tr v-for="pair in pairs" :key="pair.id" :style="pendingRemoveIds.includes(pair.id) ? 'opacity: 0.45;' : ''">
            <!-- Edit mode -->
            <template v-if="pendingEdits[pair.id]">
              <td style="padding: 0.4rem; font-weight: 600; color: #666; font-style: italic;">{{ pair.team_name }}</td>
              <td style="padding: 0.4rem;">
                <select v-if="canEditSlot(pair, 'a')" v-model="pendingEdits[pair.id].playerAId" style="padding: 0.25rem; font-size: 0.85rem; max-width: 140px;">
                  <option v-for="u in editablePlayersForSlot(pair.id, pendingEdits[pair.id].playerBId)" :key="u.id" :value="u.id">
                    {{ u.full_name || u.username || `#${u.id}` }}
                  </option>
                </select>
                <span v-else>{{ playerName(pendingEdits[pair.id].playerAId) }}</span>
              </td>
              <td style="padding: 0.4rem;">
                <select v-if="canEditSlot(pair, 'b')" v-model="pendingEdits[pair.id].playerBId" style="padding: 0.25rem; font-size: 0.85rem; max-width: 140px;">
                  <option v-for="u in editablePlayersForSlot(pair.id, pendingEdits[pair.id].playerAId)" :key="u.id" :value="u.id">
                    {{ u.full_name || u.username || `#${u.id}` }}
                  </option>
                </select>
                <span v-else>{{ playerName(pendingEdits[pair.id].playerBId) }}</span>
              </td>
              <td style="padding: 0.4rem;">
                <button
                  @click="cancelEditPair(pair.id)"
                  style="padding: 0.2rem 0.6rem; background: #888; color: white; border: none; cursor: pointer; border-radius: 3px; font-size: 0.85rem;"
                >Cancel edit</button>
              </td>
            </template>
            <!-- View mode -->
            <template v-else>
              <td style="padding: 0.4rem; font-weight: 600;">
                {{ pair.team_name }}
                <em v-if="pendingRemoveIds.includes(pair.id)" style="font-weight: normal; font-size: 0.8rem; color: #a00;">(removing)</em>
              </td>
              <td style="padding: 0.4rem;">{{ pair.player_a_name }}</td>
              <td style="padding: 0.4rem;">{{ pair.player_b_name }}</td>
              <td v-if="['grouping', 'draw'].includes(competition.status)" style="padding: 0.4rem; white-space: nowrap;">
                <span style="display: flex; gap: 0.25rem;">
                  <button
                    v-if="canEditPair(pair) && !pendingRemoveIds.includes(pair.id)"
                    @click="startEditPair(pair)"
                    style="padding: 0.2rem 0.6rem; background: #1a6ea0; color: white; border: none; cursor: pointer; border-radius: 3px; font-size: 0.85rem;"
                  >Edit</button>
                  <button
                    v-if="canManage && !pendingRemoveIds.includes(pair.id)"
                    @click="stagePairRemove(pair.id)"
                    style="padding: 0.2rem 0.6rem; background: #a00; color: white; border: none; cursor: pointer; border-radius: 3px; font-size: 0.85rem;"
                  >Remove</button>
                  <button
                    v-if="canManage && pendingRemoveIds.includes(pair.id)"
                    @click="cancelPendingRemove(pair.id)"
                    style="padding: 0.2rem 0.6rem; background: #888; color: white; border: none; cursor: pointer; border-radius: 3px; font-size: 0.85rem;"
                  >Undo</button>
                </span>
              </td>
            </template>
          </tr>
          <!-- Pending adds -->
          <tr v-for="(add, idx) in pendingAdds" :key="'padd-' + idx" style="background: #e8f4e8;">
            <td style="padding: 0.4rem; font-weight: 600; color: #2c5f2e; font-style: italic;">(pending)</td>
            <td style="padding: 0.4rem;">{{ playerName(add.playerAId) }}</td>
            <td style="padding: 0.4rem;">{{ playerName(add.playerBId) }}</td>
            <td v-if="['grouping', 'draw'].includes(competition.status)" style="padding: 0.4rem;">
              <button
                @click="cancelPendingAdd(add.playerAId)"
                style="padding: 0.2rem 0.6rem; background: #888; color: white; border: none; cursor: pointer; border-radius: 3px; font-size: 0.85rem;"
              >Cancel</button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else style="color: #888;">No pairs yet.</p>
    </section>

    <!-- Matches section (draw / match / finished) -->
    <section v-if="['draw', 'match', 'finished'].includes(competition.status)">
      <h3 style="margin-bottom: 0.5rem;">Matches</h3>

      <!-- Generate bracket panel (admin/mod, draw state) -->
      <div v-if="canManage && competition.status === 'draw'" style="background: #f5f5f5; padding: 1rem; border-radius: 4px; margin-bottom: 1rem;">
        <strong>Generate Bracket</strong>
        <div style="display: flex; gap: 0.5rem; align-items: flex-end; margin-top: 0.5rem; flex-wrap: wrap;">
          <div>
            <label style="display: block; font-size: 0.85rem;">Number of courts</label>
            <input
              v-model.number="numCourts"
              type="number"
              min="1"
              style="padding: 0.4rem; width: 80px;"
            />
          </div>
          <button
            @click="doGenerateDraw"
            style="padding: 0.4rem 1rem; background: #1a6ea0; color: white; border: none; cursor: pointer; border-radius: 4px;"
          >Generate</button>
        </div>
        <p v-if="drawError" style="color: red; margin-top: 0.4rem;">{{ drawError }}</p>
      </div>

      <!-- Bracket table -->
      <div v-if="draw" style="margin-bottom: 1.5rem;">
        <h4 style="margin-bottom: 0.4rem;">Bracket ({{ draw.num_courts }} court{{ draw.num_courts === 1 ? '' : 's' }})</h4>
        <table style="width: 100%; border-collapse: collapse;">
          <thead>
            <tr>
              <th style="text-align: left; padding: 0.4rem; border-bottom: 1px solid #ccc;">Match</th>
              <th style="text-align: left; padding: 0.4rem; border-bottom: 1px solid #ccc;">Round</th>
              <th style="text-align: left; padding: 0.4rem; border-bottom: 1px solid #ccc;">Court</th>
              <th style="text-align: left; padding: 0.4rem; border-bottom: 1px solid #ccc;">Slot</th>
              <th style="text-align: left; padding: 0.4rem; border-bottom: 1px solid #ccc;">Side A</th>
              <th style="text-align: left; padding: 0.4rem; border-bottom: 1px solid #ccc;">Side B</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="slot in draw.slots" :key="slot.match_id">
              <td style="padding: 0.4rem; font-weight: 600;">{{ slot.match_id }}</td>
              <td style="padding: 0.4rem;">{{ slot.round }}</td>
              <td style="padding: 0.4rem;">{{ slot.court }}</td>
              <td style="padding: 0.4rem;">{{ slot.time_slot }}</td>
              <td style="padding: 0.4rem;">{{ slot.label_a }}</td>
              <td style="padding: 0.4rem;">{{ slot.label_b }}</td>
            </tr>
          </tbody>
        </table>
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
import { ref, computed, reactive, onMounted } from 'vue'
import { useRoute, RouterLink, useRouter } from 'vue-router'
import {
  getMe,
  getCompetition,
  updateCompetition,
  deleteCompetition,
  transitionCompetition,
  getCompetitionPlayers,
  applyToCompetition,
  withdrawFromCompetition,
  updatePlayerStatus,
  removePlayer,
  getCompetitionMatches,
  createMatch,
  setMatchScore,
  getCompetitionPairs,
  createPair,
  deletePair,
  generateCompetitionDraw,
  getCompetitionDraw,
} from '../services/api'

const route = useRoute()
const router = useRouter()
const id = route.params.id

const competition = ref({ name: '', status: '', event_type: '', description: '' })
const players = ref([])
const matches = ref([])
const pairs = ref([])
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
  const isDoubles = competition.value.event_type === 'doubles'
  const singles = { draft: 'published', published: 'draw', draw: 'match', match: 'finished' }
  const doubles = { draft: 'published', published: 'grouping', grouping: 'draw', draw: 'match', match: 'finished' }
  return (isDoubles ? doubles : singles)[competition.value.status] || null
})
const pairedPlayerIds = computed(() => {
  const ids = new Set()
  pairs.value.forEach(p => {
    if (pendingRemoveIds.value.includes(p.id)) return
    const edit = pendingEdits[p.id]
    if (edit) {
      ids.add(edit.playerAId)
      ids.add(edit.playerBId)
    } else {
      ids.add(p.player_a_id)
      ids.add(p.player_b_id)
    }
  })
  pendingAdds.value.forEach(a => { ids.add(a.playerAId); ids.add(a.playerBId) })
  return ids
})
const unpairedPlayers = computed(() =>
  confirmedPlayers.value.filter(p => !pairedPlayerIds.value.has(p.id))
)
const isMyselfUnpaired = computed(() =>
  !!myPlayerEntry.value && !pairedPlayerIds.value.has(myPlayerEntry.value.id)
)
const partnerCandidates = computed(() =>
  unpairedPlayers.value.filter(p => p.id !== myPlayerEntry.value?.id)
)
// allPairMap: all DB pairs (including those staged for removal)
const allPairMap = computed(() => {
  const map = {}
  pairs.value.forEach(pair => {
    map[pair.player_a_id] = pair
    map[pair.player_b_id] = pair
  })
  return map
})
// effectivePairMap: DB pairs minus those staged for removal
const effectivePairMap = computed(() => {
  const map = {}
  pairs.value.forEach(pair => {
    if (!pendingRemoveIds.value.includes(pair.id)) {
      map[pair.player_a_id] = pair
      map[pair.player_b_id] = pair
    }
  })
  return map
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

// Inline partner selection (keyed by competition_player id)
const pendingPartner = reactive({})
const pairError = ref('')

// Pair staging
const pendingAdds = ref([])       // [{playerAId, playerBId}]
const pendingRemoveIds = ref([])  // pair IDs staged for deletion
const pendingEdits = reactive({}) // pairId -> {playerAId, playerBId}
const isDirty = computed(() => pendingAdds.value.length > 0 || pendingRemoveIds.value.length > 0 || Object.keys(pendingEdits).length > 0)

// Draw generation
const draw = ref(null)
const numCourts = ref(2)
const drawError = ref('')

// Score
const scoreError = ref('')

const STATUS_COLORS = {
  draft: '#888',
  published: '#2c5f2e',
  grouping: '#7a3db0',
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

    if (['grouping', 'draw', 'match', 'finished'].includes(compRes.data.status) && compRes.data.event_type === 'doubles') {
      const pairsRes = await getCompetitionPairs(id)
      pairs.value = pairsRes.data
    }
    if (['draw', 'match', 'finished'].includes(compRes.data.status)) {
      const matchRes = await getCompetitionMatches(id)
      matches.value = matchRes.data
      initScoreInputs()
      try {
        const drawRes = await getCompetitionDraw(id)
        draw.value = drawRes.data
      } catch { /* no draw yet */ }
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
    if (['grouping', 'draw', 'match', 'finished'].includes(res.data.status) && res.data.event_type === 'doubles') {
      const pairsRes = await getCompetitionPairs(id)
      pairs.value = pairsRes.data
    }
    if (['draw', 'match', 'finished'].includes(res.data.status)) {
      const matchRes = await getCompetitionMatches(id)
      matches.value = matchRes.data
      initScoreInputs()
      try {
        const drawRes = await getCompetitionDraw(id)
        draw.value = drawRes.data
      } catch { /* no draw yet */ }
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

function playerName(playerId) {
  const p = players.value.find(p => p.id === playerId)
  return p ? (p.full_name || p.username || `#${playerId}`) : `#${playerId}`
}

function partnerNameOf(player, map) {
  const m = map ?? effectivePairMap.value
  const pair = m[player.id]
  if (!pair) return ''
  const partnerId = pair.player_a_id === player.id ? pair.player_b_id : pair.player_a_id
  const partner = players.value.find(p => p.id === partnerId)
  return partner ? (partner.full_name || partner.username || `#${partnerId}`) : `#${partnerId}`
}

function pendingAddFor(playerId) {
  return pendingAdds.value.find(a => a.playerAId === playerId || a.playerBId === playerId) || null
}

function pendingPartnerNameFor(playerId) {
  const add = pendingAddFor(playerId)
  if (!add) return ''
  const partnerId = add.playerAId === playerId ? add.playerBId : add.playerAId
  return playerName(partnerId)
}

function canPairRow(player) {
  if (competition.value.status !== 'grouping') return false
  if (player.status !== 'player') return false
  if (pairedPlayerIds.value.has(player.id)) return false
  if (canManage.value) return true
  return myPlayerEntry.value?.id === player.id
}

function stagePairAdd(playerAId, playerBId) {
  if (!playerBId) return
  pendingAdds.value = [...pendingAdds.value, { playerAId, playerBId }]
  pendingPartner[playerAId] = ''
}

function stagePairRemove(pairId) {
  if (!pendingRemoveIds.value.includes(pairId)) {
    pendingRemoveIds.value = [...pendingRemoveIds.value, pairId]
  }
}

function cancelPendingAdd(playerId) {
  pendingAdds.value = pendingAdds.value.filter(
    a => a.playerAId !== playerId && a.playerBId !== playerId
  )
}

function cancelPendingRemove(pairId) {
  pendingRemoveIds.value = pendingRemoveIds.value.filter(id => id !== pairId)
}

function discardChanges() {
  pendingAdds.value = []
  pendingRemoveIds.value = []
  for (const key of Object.keys(pendingEdits)) delete pendingEdits[key]
}

function canEditPair(pair) {
  if (!['grouping', 'draw'].includes(competition.value.status)) return false
  if (canManage.value) return true
  if (!myPlayerEntry.value) return false
  return pair.player_a_id === myPlayerEntry.value.id || pair.player_b_id === myPlayerEntry.value.id
}

function mySlotInPair(pair) {
  if (!myPlayerEntry.value) return null
  if (pair.player_a_id === myPlayerEntry.value.id) return 'a'
  if (pair.player_b_id === myPlayerEntry.value.id) return 'b'
  return null
}

function canEditSlot(pair, slot) {
  if (canManage.value) return true
  const mySlot = mySlotInPair(pair)
  return mySlot !== null && mySlot !== slot
}

function startEditPair(pair) {
  pendingEdits[pair.id] = { playerAId: pair.player_a_id, playerBId: pair.player_b_id }
}

function cancelEditPair(pairId) {
  delete pendingEdits[pairId]
}

function editablePlayersForSlot(pairId, otherSlotPlayerId) {
  const occupiedIds = new Set()
  pairs.value.forEach(p => {
    if (p.id === pairId) return
    if (pendingRemoveIds.value.includes(p.id)) return
    const edit = pendingEdits[p.id]
    if (edit) {
      occupiedIds.add(edit.playerAId)
      occupiedIds.add(edit.playerBId)
    } else {
      occupiedIds.add(p.player_a_id)
      occupiedIds.add(p.player_b_id)
    }
  })
  pendingAdds.value.forEach(a => { occupiedIds.add(a.playerAId); occupiedIds.add(a.playerBId) })
  if (otherSlotPlayerId) occupiedIds.add(otherSlotPlayerId)
  return confirmedPlayers.value.filter(p => !occupiedIds.has(p.id))
}

async function doSave() {
  pairError.value = ''
  try {
    for (const pairId of pendingRemoveIds.value) {
      await deletePair(id, pairId)
    }
    for (const [pairId, edit] of Object.entries(pendingEdits)) {
      await deletePair(id, Number(pairId))
      await createPair(id, edit.playerAId, edit.playerBId)
    }
    for (const { playerAId, playerBId } of pendingAdds.value) {
      await createPair(id, playerAId, playerBId)
    }
    const res = await getCompetitionPairs(id)
    pairs.value = res.data
    pendingAdds.value = []
    pendingRemoveIds.value = []
    for (const key of Object.keys(pendingEdits)) delete pendingEdits[key]
  } catch (e) {
    pairError.value = e.response?.data?.error || 'Failed to save pairs.'
  }
}

async function doGenerateDraw() {
  drawError.value = ''
  try {
    const res = await generateCompetitionDraw(id, numCourts.value)
    draw.value = res.data
    if (competition.value.event_type === 'doubles') {
      const pairsRes = await getCompetitionPairs(id)
      pairs.value = pairsRes.data
    }
  } catch (e) {
    drawError.value = e.response?.data?.error || 'Failed to generate draw.'
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

async function doDelete() {
  if (!confirm(`Delete "${competition.value.name}"? This cannot be undone.`)) return
  try {
    await deleteCompetition(id)
    router.push('/competitions')
  } catch (e) {
    loadError.value = e.response?.data?.error || 'Failed to delete competition.'
  }
}

onMounted(load)
</script>
