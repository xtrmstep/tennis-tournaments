<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <h2>People</h2>
      <RouterLink to="/people/new">
        <button>Add Person</button>
      </RouterLink>
    </div>

    <p v-if="loading">Loading…</p>
    <p v-if="error" style="color: red;">{{ error }}</p>

    <table v-if="!loading && people.length" style="width: 100%; border-collapse: collapse; margin-top: 1rem;">
      <thead>
        <tr>
          <th style="text-align: left; padding: 0.5rem; border-bottom: 1px solid #ccc;">Name</th>
          <th style="text-align: left; padding: 0.5rem; border-bottom: 1px solid #ccc;">Skill</th>
          <th style="text-align: left; padding: 0.5rem; border-bottom: 1px solid #ccc;">Rating (1-10)</th>
          <th style="text-align: left; padding: 0.5rem; border-bottom: 1px solid #ccc;">Photo</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="person in people" :key="person.id">
          <td style="padding: 0.5rem;">{{ person.name }}</td>
          <td style="padding: 0.5rem;">{{ person.skill || '—' }}</td>
          <td style="padding: 0.5rem;">
            <input
              type="number"
              min="1"
              max="10"
              :value="person.rating"
              :aria-label="`Rating for ${person.name}`"
              style="width: 60px;"
              @blur="onRatingChange(person, $event)"
              @keydown.enter="onRatingChange(person, $event)"
            />
          </td>
          <td style="padding: 0.5rem;">
            <img
              v-if="person.photo_url"
              :src="person.photo_url"
              alt="photo"
              style="width: 48px; height: 48px; object-fit: cover; border-radius: 4px;"
            />
            <span v-else>—</span>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else-if="!loading">No people yet. Add one!</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { getPeople, updateRating } from '../services/api'

const people = ref([])
const loading = ref(false)
const error = ref('')

onMounted(async () => {
  loading.value = true
  try {
    const res = await getPeople()
    people.value = res.data
  } catch {
    error.value = 'Failed to load people'
  } finally {
    loading.value = false
  }
})

async function onRatingChange(person, event) {
  const val = parseInt(event.target.value, 10)
  if (isNaN(val) || val < 1 || val > 10) {
    error.value = 'Rating must be a number between 1 and 10'
    event.target.value = person.rating ?? ''
    return
  }
  error.value = ''
  try {
    const res = await updateRating(person.id, val)
    person.rating = res.data.rating
  } catch {
    error.value = 'Failed to update rating'
    event.target.value = person.rating ?? ''
  }
}
</script>
