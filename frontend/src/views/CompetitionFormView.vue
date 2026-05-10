<template>
  <div style="max-width: 500px;">
    <h2>New Competition</h2>
    <p v-if="error" style="color: red;">{{ error }}</p>

    <form @submit.prevent="submit">
      <div style="margin-bottom: 1rem;">
        <label style="display: block; margin-bottom: 0.25rem;">Name *</label>
        <input v-model="form.name" type="text" required style="width: 100%; padding: 0.5rem; box-sizing: border-box;" />
      </div>

      <div style="margin-bottom: 1rem;">
        <label style="display: block; margin-bottom: 0.25rem;">Description</label>
        <textarea v-model="form.description" rows="3" style="width: 100%; padding: 0.5rem; box-sizing: border-box;" />
      </div>

      <div style="margin-bottom: 1.5rem;">
        <label style="display: block; margin-bottom: 0.25rem;">Event Type *</label>
        <select v-model="form.event_type" style="width: 100%; padding: 0.5rem;">
          <option value="singles">Singles</option>
          <option value="doubles">Doubles</option>
        </select>
      </div>

      <div style="display: flex; gap: 1rem;">
        <button
          type="submit"
          :disabled="submitting"
          style="padding: 0.5rem 1.5rem; background: #2c5f2e; color: white; border: none; cursor: pointer; border-radius: 4px;"
        >{{ submitting ? 'Creating…' : 'Create Competition' }}</button>
        <RouterLink to="/competitions" style="padding: 0.5rem 1rem; text-decoration: none; color: #555;">Cancel</RouterLink>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { createCompetition } from '../services/api'

const router = useRouter()
const error = ref('')
const submitting = ref(false)

const form = ref({ name: '', description: '', event_type: 'singles' })

async function submit() {
  error.value = ''
  submitting.value = true
  try {
    const res = await createCompetition(form.value)
    router.push(`/competitions/${res.data.id}`)
  } catch (e) {
    error.value = e.response?.data?.error || 'Failed to create competition'
  } finally {
    submitting.value = false
  }
}
</script>
